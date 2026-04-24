using System.Net.Mail;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Auth;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private const int MinimumPasswordLength = 8;

    private readonly TavauraDbContext _dbContext;
    private readonly PasswordHasher _passwordHasher;
    private readonly JwtTokenService _jwtTokenService;
    private readonly IConfiguration _configuration;

    public AuthController(
        TavauraDbContext dbContext,
        PasswordHasher passwordHasher,
        JwtTokenService jwtTokenService,
        IConfiguration configuration)
    {
        _dbContext = dbContext;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _configuration = configuration;
    }

    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new { status = "ok", area = "auth" });
    }

    [HttpPost("login")]
    public async Task<ActionResult<LoginResponse>> Login(
        [FromBody] LoginRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        var normalizedEmail = NormalizeEmail(request.Email);
        if (string.IsNullOrWhiteSpace(normalizedEmail) || string.IsNullOrWhiteSpace(request.Password))
        {
            return BadRequest(new { message = "Email and password are required." });
        }

        var users = await _dbContext.Users
            .Where(u => u.Email.ToLower() == normalizedEmail)
            .ToListAsync(cancellationToken);
        if (users.Count != 1)
        {
            return Unauthorized(new { message = "Invalid email or password." });
        }

        var user = users[0];
        if (!_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
        {
            return Unauthorized(new { message = "Invalid email or password." });
        }

        return Ok(_jwtTokenService.CreateLoginResponse(user));
    }

    [HttpPost("register-merchant")]
    public Task<ActionResult<LoginResponse>> RegisterMerchant(
        [FromBody] RegisterMerchantRequest request,
        CancellationToken cancellationToken)
    {
        return RegisterTenantUserAsync(
            request?.TenantId ?? Guid.Empty,
            request?.Email,
            request?.Password,
            request?.DisplayName,
            AuthRoles.MerchantAdmin,
            cancellationToken);
    }

    [HttpPost("register-customer")]
    public Task<ActionResult<LoginResponse>> RegisterCustomer(
        [FromBody] RegisterCustomerRequest request,
        CancellationToken cancellationToken)
    {
        return RegisterTenantUserAsync(
            request?.TenantId ?? Guid.Empty,
            request?.Email,
            request?.Password,
            request?.DisplayName,
            AuthRoles.CustomerUser,
            cancellationToken);
    }

    [HttpPost("register-platform-admin")]
    public async Task<ActionResult<LoginResponse>> RegisterPlatformAdmin(
        [FromBody] RegisterPlatformAdminRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        var expectedSecret = _configuration["Auth:PlatformAdminBootstrapSecret"];
        if (string.IsNullOrWhiteSpace(expectedSecret))
        {
            return StatusCode(
                StatusCodes.Status403Forbidden,
                new { message = "Platform admin bootstrap registration is not enabled." });
        }

        if (!string.Equals(request.BootstrapSecret, expectedSecret, StringComparison.Ordinal))
        {
            return StatusCode(StatusCodes.Status403Forbidden, new { message = "Invalid bootstrap secret." });
        }

        return await RegisterUserAsync(
            tenantId: null,
            email: request.Email,
            password: request.Password,
            displayName: request.DisplayName,
            role: AuthRoles.PlatformAdmin,
            cancellationToken);
    }

    private async Task<ActionResult<LoginResponse>> RegisterTenantUserAsync(
        Guid tenantId,
        string? email,
        string? password,
        string? displayName,
        string role,
        CancellationToken cancellationToken)
    {
        if (tenantId == Guid.Empty)
        {
            return BadRequest(new { message = "TenantId is required." });
        }

        var tenantExists = await _dbContext.Tenants.AnyAsync(t => t.Id == tenantId, cancellationToken);
        if (!tenantExists)
        {
            return BadRequest(new { message = "Tenant does not exist." });
        }

        return await RegisterUserAsync(tenantId, email, password, displayName, role, cancellationToken);
    }

    private async Task<ActionResult<LoginResponse>> RegisterUserAsync(
        Guid? tenantId,
        string? email,
        string? password,
        string? displayName,
        string role,
        CancellationToken cancellationToken)
    {
        var normalizedEmail = NormalizeEmail(email);
        if (string.IsNullOrWhiteSpace(normalizedEmail) || !IsValidEmail(normalizedEmail))
        {
            return BadRequest(new { message = "A valid email is required." });
        }

        if (string.IsNullOrWhiteSpace(password) || password.Length < MinimumPasswordLength)
        {
            return BadRequest(new { message = $"Password must be at least {MinimumPasswordLength} characters." });
        }

        var emailInUse = await _dbContext.Users
            .AnyAsync(u => u.Email.ToLower() == normalizedEmail, cancellationToken);
        if (emailInUse)
        {
            return Conflict(new { message = "A user with this email already exists." });
        }

        var now = DateTime.UtcNow;
        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = normalizedEmail,
            DisplayName = string.IsNullOrWhiteSpace(displayName) ? null : displayName.Trim(),
            PasswordHash = _passwordHasher.HashPassword(password),
            Role = role,
            TenantId = tenantId,
            TokenVersion = 0,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.Users.Add(user);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var response = _jwtTokenService.CreateLoginResponse(user);
        return Created($"/api/auth/users/{user.Id}", response);
    }

    private static string NormalizeEmail(string? email)
    {
        return email?.Trim().ToLowerInvariant() ?? string.Empty;
    }

    private static bool IsValidEmail(string email)
    {
        try
        {
            var parsed = new MailAddress(email);
            return string.Equals(parsed.Address, email, StringComparison.OrdinalIgnoreCase);
        }
        catch (FormatException)
        {
            return false;
        }
    }
}
