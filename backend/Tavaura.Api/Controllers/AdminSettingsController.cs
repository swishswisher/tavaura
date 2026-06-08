using System.Net.Mail;
using System.Security.Claims;
using System.Security.Cryptography;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Admin;
using Tavaura.Api.Models.Auth;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/admin/settings")]
[Authorize(Roles = AuthRoles.MerchantOrPlatform)]
public class AdminSettingsController : ControllerBase
{
    private const int MinimumPasswordLength = 8;
    private const long MaxLogoBytes = 2 * 1024 * 1024;

    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;
    private readonly PasswordHasher _passwordHasher;
    private readonly JwtTokenService _jwtTokenService;

    public AdminSettingsController(
        TavauraDbContext dbContext,
        ITenantContext tenantContext,
        PasswordHasher passwordHasher,
        JwtTokenService jwtTokenService)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
    }

    [HttpGet]
    public async Task<ActionResult<AdminSettingsResponse>> GetAsync(CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        return Ok(await BuildResponseAsync(context.Value.Tenant, context.Value.Settings, cancellationToken));
    }

    [HttpPatch("brand")]
    public async Task<ActionResult<AdminSettingsResponse>> UpdateBrandAsync(
        [FromBody] UpdateAdminBrandSettingsRequest request,
        CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        var brandName = request.BrandName.Trim();
        var supportEmail = request.SupportEmail.Trim();
        var websiteUrl = request.WebsiteUrl.Trim();

        if (string.IsNullOrWhiteSpace(brandName))
        {
            return BadRequest(new { message = "Brand name is required." });
        }

        if (string.IsNullOrWhiteSpace(supportEmail) || !IsValidEmail(supportEmail))
        {
            return BadRequest(new { message = "A valid support email is required." });
        }

        if (string.IsNullOrWhiteSpace(websiteUrl) || !IsValidHttpUrl(websiteUrl))
        {
            return BadRequest(new { message = "A valid website URL is required." });
        }

        var now = DateTime.UtcNow;
        context.Value.Tenant.Name = brandName;
        context.Value.Tenant.Domain = websiteUrl;
        context.Value.Tenant.UpdatedAt = now;
        context.Value.Settings.SupportEmail = supportEmail;
        context.Value.Settings.WebsiteUrl = websiteUrl;
        context.Value.Settings.UpdatedAt = now;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(await BuildResponseAsync(context.Value.Tenant, context.Value.Settings, cancellationToken));
    }

    [HttpPost("logo")]
    [RequestSizeLimit(MaxLogoBytes + 1024)]
    public async Task<ActionResult<AdminSettingsResponse>> UploadLogoAsync(
        [FromForm] IFormFile logo,
        CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        if (logo is null || logo.Length == 0)
        {
            return BadRequest(new { message = "Logo file is required." });
        }

        if (logo.Length > MaxLogoBytes)
        {
            return BadRequest(new { message = "Logo file must be 2 MB or smaller." });
        }

        if (string.IsNullOrWhiteSpace(logo.ContentType) ||
            !logo.ContentType.StartsWith("image/", StringComparison.OrdinalIgnoreCase))
        {
            return BadRequest(new { message = "Logo must be an image file." });
        }

        await using var stream = logo.OpenReadStream();
        using var memory = new MemoryStream();
        await stream.CopyToAsync(memory, cancellationToken);

        context.Value.Settings.LogoUrl =
            $"data:{logo.ContentType};base64,{Convert.ToBase64String(memory.ToArray())}";
        context.Value.Settings.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(await BuildResponseAsync(context.Value.Tenant, context.Value.Settings, cancellationToken));
    }

    [HttpPut("webhook")]
    public async Task<ActionResult<AdminSettingsResponse>> UpdateWebhookAsync(
        [FromBody] UpdateAdminWebhookRequest request,
        CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        var webhookUrl = request.WebhookUrl.Trim();
        if (string.IsNullOrWhiteSpace(webhookUrl) || !IsValidHttpUrl(webhookUrl))
        {
            return BadRequest(new { message = "A valid webhook URL is required." });
        }

        context.Value.Settings.WebhookUrl = webhookUrl;
        context.Value.Settings.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(await BuildResponseAsync(context.Value.Tenant, context.Value.Settings, cancellationToken));
    }

    [HttpPost("api-key/regenerate")]
    public async Task<ActionResult<AdminSettingsResponse>> RegenerateApiKeyAsync(
        CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        context.Value.Settings.ApiKey = GenerateApiKey();
        context.Value.Settings.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(await BuildResponseAsync(context.Value.Tenant, context.Value.Settings, cancellationToken));
    }

    [HttpPost("password")]
    public async Task<ActionResult<LoginResponse>> ChangePasswordAsync(
        [FromBody] ChangeAdminPasswordRequest request,
        CancellationToken cancellationToken)
    {
        var user = await LoadCurrentUserAsync(cancellationToken);
        if (user is null)
        {
            return Unauthorized(new { message = "Authenticated user was not found." });
        }

        if (string.IsNullOrWhiteSpace(request.CurrentPassword) ||
            !_passwordHasher.VerifyPassword(request.CurrentPassword, user.PasswordHash))
        {
            return BadRequest(new { message = "Current password is incorrect." });
        }

        if (string.IsNullOrWhiteSpace(request.NewPassword) ||
            request.NewPassword.Length < MinimumPasswordLength)
        {
            return BadRequest(new { message = $"New password must be at least {MinimumPasswordLength} characters." });
        }

        user.PasswordHash = _passwordHasher.HashPassword(request.NewPassword);
        user.TokenVersion += 1;
        user.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(_jwtTokenService.CreateLoginResponse(user));
    }

    [HttpPost("sessions/sign-out-others")]
    public async Task<ActionResult<LoginResponse>> SignOutOtherSessionsAsync(CancellationToken cancellationToken)
    {
        var user = await LoadCurrentUserAsync(cancellationToken);
        if (user is null)
        {
            return Unauthorized(new { message = "Authenticated user was not found." });
        }

        user.TokenVersion += 1;
        user.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);
        return Ok(_jwtTokenService.CreateLoginResponse(user));
    }

    [HttpPost("workspace/delete-request")]
    public async Task<ActionResult<WorkspaceDeletionRequestResponse>> RequestWorkspaceDeletionAsync(
        CancellationToken cancellationToken)
    {
        var context = await LoadTenantSettingsContextAsync(cancellationToken);
        if (context.Result is not null)
        {
            return context.Result;
        }

        context.Value.Tenant.Status = "deletion_requested";
        context.Value.Tenant.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return Ok(new WorkspaceDeletionRequestResponse
        {
            Message = "Workspace deletion request recorded.",
            Status = context.Value.Tenant.Status
        });
    }

    private async Task<ActionResult<(Tenant Tenant, MerchantAdminSettings Settings)>> LoadTenantSettingsContextAsync(
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var tenant = await _dbContext.Tenants.FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);
        if (tenant is null)
        {
            return NotFound(new { message = "Tenant was not found." });
        }

        var user = await LoadCurrentUserAsync(cancellationToken);
        var settings = await _dbContext.MerchantAdminSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (settings is null)
        {
            var now = DateTime.UtcNow;
            settings = new MerchantAdminSettings
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                SupportEmail = user?.Email ?? string.Empty,
                WebsiteUrl = tenant.Domain ?? string.Empty,
                ApiKey = GenerateApiKey(),
                WebhookUrl = string.Empty,
                CreatedAt = now,
                UpdatedAt = now
            };

            _dbContext.MerchantAdminSettings.Add(settings);
            await _dbContext.SaveChangesAsync(cancellationToken);
        }

        return (tenant, settings);
    }

    private async Task<User?> LoadCurrentUserAsync(CancellationToken cancellationToken)
    {
        var userIdValue = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(userIdValue, out var userId))
        {
            return null;
        }

        return await _dbContext.Users.FirstOrDefaultAsync(u => u.Id == userId, cancellationToken);
    }

    private async Task<AdminSettingsResponse> BuildResponseAsync(
        Tenant tenant,
        MerchantAdminSettings settings,
        CancellationToken cancellationToken)
    {
        var now = DateTime.UtcNow;
        var monthStart = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc);
        var plan = string.IsNullOrWhiteSpace(tenant.Plan) ? "starter" : tenant.Plan;
        var renderLimit = GetMonthlyRenderLimit(plan);

        var garmentsProcessedThisMonth = await _dbContext.GarmentAssets
            .AsNoTracking()
            .Join(
                _dbContext.Garments.AsNoTracking().Where(g => g.TenantId == tenant.Id && g.IsActive && !g.IsDeleted),
                ga => ga.GarmentId,
                g => g.Id,
                (ga, _) => ga)
            .CountAsync(ga =>
                    ga.TenantId == tenant.Id &&
                    ga.CreatedAt >= monthStart &&
                    !string.IsNullOrWhiteSpace(ga.ProcessedMaskUrl) &&
                    !string.IsNullOrWhiteSpace(ga.ProcessedTextureUrl),
                cancellationToken);

        var visibleRenderJobs = _dbContext.RenderJobs
            .AsNoTracking()
            .Where(rj => rj.TenantId == tenant.Id && !rj.IsDeleted)
            .Join(
                _dbContext.GarmentAssets.AsNoTracking().Where(ga => ga.TenantId == tenant.Id),
                rj => rj.GarmentAssetId,
                ga => ga.Id,
                (rj, ga) => new { RenderJob = rj, ga.GarmentId })
            .Join(
                _dbContext.Garments.AsNoTracking().Where(g => g.TenantId == tenant.Id && g.IsActive && !g.IsDeleted),
                x => x.GarmentId,
                g => g.Id,
                (x, _) => x.RenderJob);

        var rendersThisMonth = await _dbContext.RenderResults
            .AsNoTracking()
            .Join(
                visibleRenderJobs,
                rr => rr.RenderJobId,
                rj => rj.Id,
                (rr, _) => rr)
            .CountAsync(rr => rr.CreatedAt >= monthStart && !rr.IsDeleted, cancellationToken);

        return new AdminSettingsResponse
        {
            BrandProfile = new AdminBrandProfileResponse
            {
                BrandName = tenant.Name,
                SupportEmail = settings.SupportEmail,
                WebsiteUrl = settings.WebsiteUrl,
                LogoUrl = settings.LogoUrl
            },
            Integration = new AdminIntegrationSettingsResponse
            {
                ApiKey = settings.ApiKey,
                WebhookUrl = settings.WebhookUrl
            },
            Usage = new AdminUsagePlanResponse
            {
                GarmentsProcessedThisMonth = garmentsProcessedThisMonth,
                RendersThisMonth = rendersThisMonth,
                CurrentPlan = plan,
                UsageRemaining = Math.Max(0, renderLimit - rendersThisMonth)
            }
        };
    }

    private static string GenerateApiKey()
    {
        return $"tv_live_{Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant()}";
    }

    private static int GetMonthlyRenderLimit(string plan)
    {
        return plan.Trim().ToLowerInvariant() switch
        {
            "growth" => 2000,
            "scale" => 10000,
            "enterprise" => 50000,
            _ => 500
        };
    }

    private static bool IsValidEmail(string value)
    {
        try
        {
            var parsed = new MailAddress(value);
            return string.Equals(parsed.Address, value, StringComparison.OrdinalIgnoreCase);
        }
        catch (FormatException)
        {
            return false;
        }
    }

    private static bool IsValidHttpUrl(string value)
    {
        return Uri.TryCreate(value, UriKind.Absolute, out var uri) &&
               (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps);
    }
}
