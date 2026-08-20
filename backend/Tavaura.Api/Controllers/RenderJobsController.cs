using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Jobs;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/render-jobs")]
[Authorize(Roles = AuthRoles.CustomerMerchantOrPlatform)]
public class RenderJobsController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public RenderJobsController(TavauraDbContext dbContext, ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpPost]
    [HttpPost("/api/admin/render-jobs")]
    public async Task<ActionResult<RenderJobResponse>> CreateAsync(
        [FromBody] CreateRenderJobRequest request,
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        if (request.GarmentId == Guid.Empty)
        {
            return BadRequest(new { message = "GarmentId is required." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var avatar = request.AvatarId == Guid.Empty
            ? await GetOrCreateDefaultAvatarAsync(request.AvatarImageUrl, tenantId, cancellationToken)
            : await _dbContext.Avatars.FirstOrDefaultAsync(a => a.Id == request.AvatarId, cancellationToken);
        if (avatar is null)
        {
            return BadRequest(new { message = "Avatar does not exist." });
        }

        if (avatar.TenantId != tenantId)
        {
            return BadRequest(new { message = "Avatar does not belong to this tenant." });
        }

        if (User.IsInRole(AuthRoles.CustomerUser) &&
            !string.Equals(
                User.FindFirstValue(ClaimTypes.NameIdentifier),
                avatar.UserId.ToString(),
                StringComparison.OrdinalIgnoreCase))
        {
            return Forbid();
        }

        var garment = await _dbContext.Garments.FirstOrDefaultAsync(
            g => g.Id == request.GarmentId && g.TenantId == tenantId && g.IsActive && !g.IsDeleted,
            cancellationToken);
        if (garment is null)
        {
            return BadRequest(new { message = "Garment does not exist for this tenant." });
        }

        var garmentAsset = await _dbContext.GarmentAssets
            .Where(ga => ga.TenantId == tenantId && ga.GarmentId == garment.Id)
            .OrderByDescending(ga => ga.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken);
        if (garmentAsset is null)
        {
            return BadRequest(new { message = "Garment has no processed asset. Queue and complete ingestion first." });
        }

        if (string.IsNullOrWhiteSpace(garmentAsset.ProcessedImageUrl))
        {
            return BadRequest(new { message = "Garment asset is missing processed image output. Queue and complete ingestion first." });
        }

        if (string.IsNullOrWhiteSpace(garmentAsset.ProcessedMaskUrl) ||
            string.IsNullOrWhiteSpace(garmentAsset.ProcessedTextureUrl))
        {
            return BadRequest(new { message = "Garment asset is missing processed output URLs. Queue and complete ingestion first." });
        }

        var assetVersion = await _dbContext.AssetVersions
            .Where(av => av.GarmentAssetId == garmentAsset.Id)
            .OrderByDescending(av => av.VersionNumber)
            .FirstOrDefaultAsync(cancellationToken);
        if (assetVersion is null)
        {
            return BadRequest(new { message = "Garment asset has no asset version. Queue and complete ingestion first." });
        }

        var now = DateTime.UtcNow;
        var renderJob = new RenderJob
        {
            Id = Guid.NewGuid(),
            TenantId = tenantId,
            AvatarId = avatar.Id,
            GarmentAssetId = garmentAsset.Id,
            AssetVersionId = assetVersion.Id,
            Status = "pending",
            AttemptCount = 0,
            IsDeleted = false,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.RenderJobs.Add(renderJob);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var response = ToRenderJobResponse(renderJob, garment.Id);
        return Created($"/api/render-jobs/{renderJob.Id}", response);
    }

    private async Task<Avatar?> GetOrCreateDefaultAvatarAsync(
        string? avatarImageUrl,
        Guid tenantId,
        CancellationToken cancellationToken)
    {
        var userIdValue = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(userIdValue, out var userId))
        {
            return null;
        }

        var source = string.IsNullOrWhiteSpace(avatarImageUrl)
            ? "tavaura-default-avatar"
            : avatarImageUrl.Trim();

        var existingAvatar = await _dbContext.Avatars
            .Where(a => a.UserId == userId && a.TenantId == tenantId && a.Source == source)
            .OrderByDescending(a => a.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken);
        if (existingAvatar is not null)
        {
            return existingAvatar;
        }

        var now = DateTime.UtcNow;
        var avatar = new Avatar
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            TenantId = tenantId,
            Source = source,
            HeightCm = 172,
            WeightKg = 70,
            Age = 30,
            Gender = "unspecified",
            IsPregnant = false,
            SkinTone = "neutral",
            SmplParametersJson = "{}",
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.Avatars.Add(avatar);
        await _dbContext.SaveChangesAsync(cancellationToken);
        return avatar;
    }

    private static RenderJobResponse ToRenderJobResponse(RenderJob renderJob, Guid garmentId)
    {
        return new RenderJobResponse
        {
            Id = renderJob.Id,
            TenantId = renderJob.TenantId,
            AvatarId = renderJob.AvatarId,
            GarmentId = garmentId,
            GarmentAssetId = renderJob.GarmentAssetId,
            AssetVersionId = renderJob.AssetVersionId,
            Status = renderJob.Status,
            AttemptCount = renderJob.AttemptCount,
            ErrorMessage = renderJob.ErrorMessage,
            StartedAt = renderJob.StartedAt,
            CompletedAt = renderJob.CompletedAt,
            CreatedAt = renderJob.CreatedAt,
            UpdatedAt = renderJob.UpdatedAt
        };
    }
}
