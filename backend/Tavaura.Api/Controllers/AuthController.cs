using System.Data;
using System.Net.Mail;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.WebUtilities;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Auth;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[RequestSizeLimit(16 * 1024)]
public class AuthController : ControllerBase
{
    private static readonly Regex SlugPattern = new(
        "^[a-z0-9]+(?:-[a-z0-9]+)*$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    private const int MinimumPasswordLength = 12;
    private const int MaximumFailedLogins = 5;
    private const int LockoutMinutes = 15;
    private const int MaximumInvitationHours = 72;

    private readonly TavauraDbContext _dbContext;
    private readonly PasswordHasher _passwordHasher;
    private readonly JwtTokenService _jwtTokenService;
    private readonly IConfiguration _configuration;
    private readonly IHostEnvironment _environment;

    public AuthController(
        TavauraDbContext dbContext,
        PasswordHasher passwordHasher,
        JwtTokenService jwtTokenService,
        IConfiguration configuration,
        IHostEnvironment environment)
    {
        _dbContext = dbContext;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _configuration = configuration;
        _environment = environment;
    }

    [AllowAnonymous]
    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new { status = "ok", area = "auth" });
    }

    [AllowAnonymous]
    [EnableRateLimiting("auth")]
    [HttpPost("login")]
    public async Task<ActionResult<LoginResponse>> Login(
        [FromBody] LoginRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        var normalizedEmail = NormalizeEmailKey(request.Email);
        if (string.IsNullOrWhiteSpace(normalizedEmail) || string.IsNullOrWhiteSpace(request.Password))
        {
            return BadRequest(new { message = "Email and password are required." });
        }

        var user = await _dbContext.Users
            .SingleOrDefaultAsync(u => u.NormalizedEmail == normalizedEmail, cancellationToken);
        if (user is null)
        {
            _passwordHasher.VerifyDummyPassword(request.Password);
            return Unauthorized(new { message = "Invalid email or password." });
        }

        var now = DateTime.UtcNow;
        if (user.LockoutEnd.HasValue && user.LockoutEnd.Value > now)
        {
            _passwordHasher.VerifyDummyPassword(request.Password);
            return Unauthorized(new { message = "Invalid email or password." });
        }

        var verificationResult = _passwordHasher.VerifyPassword(user, request.Password);
        if (verificationResult == PasswordVerificationResult.Failed)
        {
            user.FailedLoginCount += 1;
            if (user.FailedLoginCount >= MaximumFailedLogins)
            {
                user.LockoutEnd = now.AddMinutes(LockoutMinutes);
                user.FailedLoginCount = 0;
                user.TokenVersion += 1;
            }

            user.UpdatedAt = now;
            await _dbContext.SaveChangesAsync(cancellationToken);
            return Unauthorized(new { message = "Invalid email or password." });
        }

        if (verificationResult == PasswordVerificationResult.SuccessRehashNeeded)
        {
            user.PasswordHash = _passwordHasher.HashPassword(user, request.Password);
        }

        if (!await HasValidMerchantMembershipAsync(user, cancellationToken))
        {
            return Unauthorized(new { message = "Invalid email or password." });
        }

        user.FailedLoginCount = 0;
        user.LockoutEnd = null;
        user.LastLoginAt = now;
        user.UpdatedAt = now;
        await _dbContext.SaveChangesAsync(cancellationToken);

        return Ok(_jwtTokenService.CreateLoginResponse(user));
    }

    [Authorize(Roles = AuthRoles.PlatformAdmin)]
    [HttpPost("merchant-workspaces")]
    public async Task<ActionResult<MerchantWorkspaceResponse>> CreateMerchantWorkspace(
        [FromBody] CreateMerchantWorkspaceRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        var accountName = request.AccountName.Trim();
        var storeName = request.StoreName.Trim();
        var accountSlug = request.AccountSlug.Trim().ToLowerInvariant();
        var storeSlug = request.StoreSlug.Trim().ToLowerInvariant();
        var platform = request.Platform.Trim().ToLowerInvariant();
        var plan = request.Plan.Trim().ToLowerInvariant();
        var email = NormalizeEmail(request.MerchantAdminEmail);
        var normalizedEmail = NormalizeEmailKey(email);
        var domain = NormalizeDomain(request.Domain);

        if (string.IsNullOrWhiteSpace(accountName) || string.IsNullOrWhiteSpace(storeName) ||
            string.IsNullOrWhiteSpace(platform) || !SlugPattern.IsMatch(accountSlug) ||
            !SlugPattern.IsMatch(storeSlug))
        {
            return BadRequest(new { message = "Names, platform, and lowercase hyphenated slugs are required." });
        }

        if (string.IsNullOrWhiteSpace(email) || !IsValidEmail(email))
        {
            return BadRequest(new { message = "A valid merchant administrator email is required." });
        }

        if (request.InvitationExpiresInHours is < 1 or > MaximumInvitationHours)
        {
            return BadRequest(new { message = $"InvitationExpiresInHours must be between 1 and {MaximumInvitationHours}." });
        }

        if (!string.IsNullOrWhiteSpace(request.Domain) && domain is null)
        {
            return BadRequest(new { message = "Domain must be a valid HTTPS hostname or hostname." });
        }

        if (await _dbContext.Accounts.AnyAsync(a => a.Slug == accountSlug, cancellationToken) ||
            await _dbContext.Users.AnyAsync(u => u.NormalizedEmail == normalizedEmail, cancellationToken))
        {
            return Conflict(new { message = "Account slug or merchant email is already in use." });
        }

        var createdByValue = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(createdByValue, out var createdByUserId))
        {
            return Unauthorized(new { message = "Authenticated platform user is invalid." });
        }

        await using var transaction = await _dbContext.Database.BeginTransactionAsync(
            IsolationLevel.Serializable,
            cancellationToken);
        var now = DateTime.UtcNow;
        var tenant = new Tenant
        {
            Id = Guid.NewGuid(),
            Name = storeName,
            Domain = domain,
            Platform = platform,
            Status = "active",
            Plan = string.IsNullOrWhiteSpace(plan) ? "starter" : plan,
            CreatedAt = now,
            UpdatedAt = now
        };
        var account = new Account
        {
            Id = Guid.NewGuid(),
            Name = accountName,
            Slug = accountSlug,
            BillingEmail = email,
            Status = "active",
            CreatedAt = now,
            UpdatedAt = now
        };
        var store = new Store
        {
            Id = Guid.NewGuid(),
            AccountId = account.Id,
            TenantId = tenant.Id,
            Name = storeName,
            Slug = storeSlug,
            Platform = platform,
            Domain = domain,
            Status = "active",
            CreatedAt = now,
            UpdatedAt = now
        };
        var (invitation, token) = CreateInvitation(
            tenant.Id,
            createdByUserId,
            email,
            normalizedEmail,
            request.InvitationExpiresInHours,
            now);

        _dbContext.AddRange(tenant, account, store, invitation);
        await _dbContext.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return Created(
            $"/api/auth/merchant-workspaces/{account.Id}",
            new MerchantWorkspaceResponse
            {
                AccountId = account.Id,
                StoreId = store.Id,
                TenantId = tenant.Id,
                Invitation = BuildInvitationResponse(invitation, token)
            });
    }

    [Authorize(Roles = AuthRoles.PlatformAdmin)]
    [HttpPost("merchant-invitations")]
    public async Task<ActionResult<MerchantInvitationResponse>> CreateMerchantInvitation(
        [FromBody] CreateMerchantInvitationRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        if (request.TenantId == Guid.Empty)
        {
            return BadRequest(new { message = "TenantId is required." });
        }

        var email = NormalizeEmail(request.Email);
        var normalizedEmail = NormalizeEmailKey(email);
        if (string.IsNullOrWhiteSpace(email) || !IsValidEmail(email))
        {
            return BadRequest(new { message = "A valid email is required." });
        }

        if (request.ExpiresInHours is < 1 or > MaximumInvitationHours)
        {
            return BadRequest(new { message = $"ExpiresInHours must be between 1 and {MaximumInvitationHours}." });
        }

        var store = await _dbContext.Stores
            .AsNoTracking()
            .SingleOrDefaultAsync(s => s.TenantId == request.TenantId, cancellationToken);
        if (store is null)
        {
            return BadRequest(new { message = "Tenant is not mapped to a merchant account and store." });
        }

        var emailInUse = await _dbContext.Users
            .AnyAsync(u => u.NormalizedEmail == normalizedEmail, cancellationToken);
        if (emailInUse)
        {
            return Conflict(new { message = "A user with this email already exists." });
        }

        var createdByValue = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(createdByValue, out var createdByUserId))
        {
            return Unauthorized(new { message = "Authenticated platform user is invalid." });
        }

        var now = DateTime.UtcNow;
        var existingInvitations = await _dbContext.UserInvitations
            .Where(i => i.NormalizedEmail == normalizedEmail &&
                        i.TenantId == request.TenantId &&
                        i.AcceptedAt == null &&
                        i.ExpiresAt > now)
            .ToListAsync(cancellationToken);
        foreach (var existingInvitation in existingInvitations)
        {
            existingInvitation.ExpiresAt = now;
        }

        var (invitation, token) = CreateInvitation(
            request.TenantId,
            createdByUserId,
            email,
            normalizedEmail,
            request.ExpiresInHours,
            now);

        _dbContext.UserInvitations.Add(invitation);
        await _dbContext.SaveChangesAsync(cancellationToken);

        return Created(
            $"/api/auth/merchant-invitations/{invitation.Id}",
            BuildInvitationResponse(invitation, token));
    }

    [AllowAnonymous]
    [EnableRateLimiting("auth")]
    [HttpPost("merchant-invitations/accept")]
    public async Task<ActionResult<LoginResponse>> AcceptMerchantInvitation(
        [FromBody] AcceptInvitationRequest request,
        CancellationToken cancellationToken)
    {
        if (request is null || string.IsNullOrWhiteSpace(request.Token))
        {
            return BadRequest(new { message = "A valid invitation token is required." });
        }

        var normalizedEmail = NormalizeEmailKey(request.Email);
        if (string.IsNullOrWhiteSpace(normalizedEmail) || !IsValidEmail(NormalizeEmail(request.Email)))
        {
            return BadRequest(new { message = "A valid invitation email is required." });
        }

        if (string.IsNullOrWhiteSpace(request.Password) || request.Password.Length < MinimumPasswordLength)
        {
            return BadRequest(new { message = $"Password must be at least {MinimumPasswordLength} characters." });
        }

        await using var transaction = await _dbContext.Database.BeginTransactionAsync(
            IsolationLevel.ReadCommitted,
            cancellationToken);

        var now = DateTime.UtcNow;
        var tokenHash = HashInvitationToken(request.Token.Trim());
        var invitation = await _dbContext.UserInvitations
            .FromSqlInterpolated(
                $"""SELECT * FROM "UserInvitations" WHERE "TokenHash" = {tokenHash} FOR UPDATE""")
            .SingleOrDefaultAsync(cancellationToken);
        if (invitation is null || invitation.AcceptedAt.HasValue || invitation.ExpiresAt <= now)
        {
            return BadRequest(new { message = "Invitation is invalid or has expired." });
        }

        if (!string.Equals(invitation.NormalizedEmail, normalizedEmail, StringComparison.Ordinal))
        {
            return BadRequest(new { message = "Invitation is invalid or has expired." });
        }

        var emailInUse = await _dbContext.Users
            .AnyAsync(u => u.NormalizedEmail == invitation.NormalizedEmail, cancellationToken);
        if (emailInUse)
        {
            return Conflict(new { message = "A user with this email already exists." });
        }

        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = invitation.Email,
            NormalizedEmail = invitation.NormalizedEmail,
            DisplayName = NormalizeDisplayName(request.DisplayName),
            Role = invitation.Role,
            TenantId = invitation.TenantId,
            TokenVersion = 0,
            CreatedAt = now,
            UpdatedAt = now
        };
        user.PasswordHash = _passwordHasher.HashPassword(user, request.Password);
        invitation.AcceptedAt = now;

        var accountId = await _dbContext.Stores
            .Where(s => s.TenantId == invitation.TenantId && s.Status == "active")
            .Select(s => (Guid?)s.AccountId)
            .SingleOrDefaultAsync(cancellationToken);
        if (!accountId.HasValue)
        {
            return BadRequest(new { message = "Invitation workspace is not active." });
        }

        var membership = new AccountUserMembership
        {
            Id = Guid.NewGuid(),
            AccountId = accountId.Value,
            UserId = user.Id,
            Role = AuthRoles.MerchantAdmin,
            Status = "active",
            CreatedAt = now
        };

        _dbContext.AddRange(user, membership);
        await _dbContext.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return Created("/api/auth/login", _jwtTokenService.CreateLoginResponse(user));
    }

    [AllowAnonymous]
    [EnableRateLimiting("auth")]
    [HttpPost("register-platform-admin")]
    public async Task<ActionResult<LoginResponse>> RegisterPlatformAdmin(
        [FromBody] RegisterPlatformAdminRequest request,
        CancellationToken cancellationToken)
    {
        if (!_environment.IsDevelopment())
        {
            return NotFound();
        }

        if (request is null)
        {
            return BadRequest(new { message = "Request body is required." });
        }

        var expectedSecret = _configuration["Auth:PlatformAdminBootstrapSecret"];
        if (string.IsNullOrWhiteSpace(expectedSecret) || !SecretsMatch(request.BootstrapSecret, expectedSecret))
        {
            return StatusCode(StatusCodes.Status403Forbidden, new { message = "Invalid bootstrap secret." });
        }

        return await RegisterPlatformUserAsync(
            request.Email,
            request.Password,
            request.DisplayName,
            cancellationToken);
    }

    private async Task<ActionResult<LoginResponse>> RegisterPlatformUserAsync(
        string? email,
        string? password,
        string? displayName,
        CancellationToken cancellationToken)
    {
        var normalizedEmail = NormalizeEmailKey(email);
        var displayEmail = NormalizeEmail(email);
        if (string.IsNullOrWhiteSpace(displayEmail) || !IsValidEmail(displayEmail))
        {
            return BadRequest(new { message = "A valid email is required." });
        }

        if (string.IsNullOrWhiteSpace(password) || password.Length < MinimumPasswordLength)
        {
            return BadRequest(new { message = $"Password must be at least {MinimumPasswordLength} characters." });
        }

        var emailInUse = await _dbContext.Users
            .AnyAsync(u => u.NormalizedEmail == normalizedEmail, cancellationToken);
        if (emailInUse)
        {
            return Conflict(new { message = "A user with this email already exists." });
        }

        var now = DateTime.UtcNow;
        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = displayEmail,
            NormalizedEmail = normalizedEmail,
            DisplayName = NormalizeDisplayName(displayName),
            Role = AuthRoles.PlatformAdmin,
            TenantId = null,
            TokenVersion = 0,
            CreatedAt = now,
            UpdatedAt = now
        };
        user.PasswordHash = _passwordHasher.HashPassword(user, password);

        _dbContext.Users.Add(user);
        await _dbContext.SaveChangesAsync(cancellationToken);

        return Created("/api/auth/login", _jwtTokenService.CreateLoginResponse(user));
    }

    private static string NormalizeEmail(string? email)
    {
        return email?.Trim().ToLowerInvariant() ?? string.Empty;
    }

    private async Task<bool> HasValidMerchantMembershipAsync(
        User user,
        CancellationToken cancellationToken)
    {
        if (user.Role != AuthRoles.MerchantAdmin)
        {
            return true;
        }

        if (!user.TenantId.HasValue)
        {
            return false;
        }

        return await _dbContext.Stores
            .Where(s => s.TenantId == user.TenantId.Value && s.Status == "active")
            .Join(
                _dbContext.AccountUserMemberships.Where(m =>
                    m.UserId == user.Id && m.Status == "active"),
                s => s.AccountId,
                m => m.AccountId,
                (s, m) => new { Store = s, Membership = m })
            .Join(
                _dbContext.Accounts.Where(a => a.Status == "active"),
                x => x.Store.AccountId,
                a => a.Id,
                (_, _) => 1)
            .AnyAsync(cancellationToken);
    }

    private static (UserInvitation Invitation, string Token) CreateInvitation(
        Guid tenantId,
        Guid createdByUserId,
        string email,
        string normalizedEmail,
        int expiresInHours,
        DateTime now)
    {
        var token = WebEncoders.Base64UrlEncode(RandomNumberGenerator.GetBytes(32));
        return (new UserInvitation
        {
            Id = Guid.NewGuid(),
            TokenHash = HashInvitationToken(token),
            Email = email,
            NormalizedEmail = normalizedEmail,
            Role = AuthRoles.MerchantAdmin,
            TenantId = tenantId,
            CreatedByUserId = createdByUserId,
            ExpiresAt = now.AddHours(expiresInHours),
            CreatedAt = now
        }, token);
    }

    private static MerchantInvitationResponse BuildInvitationResponse(
        UserInvitation invitation,
        string token)
    {
        return new MerchantInvitationResponse
        {
            Id = invitation.Id,
            TenantId = invitation.TenantId,
            Email = invitation.Email,
            Role = invitation.Role,
            Token = token,
            ExpiresAt = invitation.ExpiresAt
        };
    }

    private static string? NormalizeDomain(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        var candidate = value.Trim();
        if (!candidate.Contains("://", StringComparison.Ordinal))
        {
            candidate = $"https://{candidate}";
        }

        return Uri.TryCreate(candidate, UriKind.Absolute, out var uri) &&
               uri.Scheme == Uri.UriSchemeHttps &&
               string.IsNullOrEmpty(uri.UserInfo) &&
               uri.Port == 443 &&
               uri.AbsolutePath == "/" &&
               string.IsNullOrEmpty(uri.Query) &&
               string.IsNullOrEmpty(uri.Fragment)
            ? uri.IdnHost.ToLowerInvariant()
            : null;
    }

    private static string NormalizeEmailKey(string? email)
    {
        return email?.Trim().ToUpperInvariant() ?? string.Empty;
    }

    private static string? NormalizeDisplayName(string? displayName)
    {
        return string.IsNullOrWhiteSpace(displayName) ? null : displayName.Trim();
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

    private static string HashInvitationToken(string token)
    {
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(token)));
    }

    private static bool SecretsMatch(string? suppliedSecret, string expectedSecret)
    {
        var suppliedHash = SHA256.HashData(Encoding.UTF8.GetBytes(suppliedSecret ?? string.Empty));
        var expectedHash = SHA256.HashData(Encoding.UTF8.GetBytes(expectedSecret));
        return CryptographicOperations.FixedTimeEquals(suppliedHash, expectedHash);
    }
}
