using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Garments;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/garments")]
[Authorize(Roles = AuthRoles.MerchantOrPlatform)]
public class GarmentsController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public GarmentsController(
        TavauraDbContext dbContext,
        ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<GarmentResponse>>> ListAsync(CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var garments = await _dbContext.Garments
            .Where(g => g.TenantId == tenantId && g.IsActive && !g.IsDeleted)
            .OrderByDescending(g => g.CreatedAt)
            .ToListAsync(cancellationToken);

        var responses = await BuildGarmentResponsesAsync(tenantId, garments, cancellationToken);
        return Ok(responses);
    }

    [HttpGet("{garmentId:guid}")]
    public async Task<ActionResult<GarmentResponse>> GetAsync(Guid garmentId, CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var garment = await _dbContext.Garments.FirstOrDefaultAsync(
            g => g.Id == garmentId && g.TenantId == tenantId && g.IsActive && !g.IsDeleted,
            cancellationToken);
        if (garment is null)
        {
            return NotFound(new { message = "Garment was not found for this tenant." });
        }

        var response = await BuildGarmentResponseAsync(tenantId, garment, cancellationToken);
        return Ok(response);
    }

    [HttpPost]
    public async Task<ActionResult<GarmentResponse>> CreateAsync(
        [FromBody] CreateGarmentRequest request,
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var tenantExists = await _dbContext.Tenants.AnyAsync(t => t.Id == tenantId, cancellationToken);
        if (!tenantExists)
        {
            return BadRequest(new { message = "Tenant does not exist." });
        }

        if (string.IsNullOrWhiteSpace(request.ExternalProductId))
        {
            return BadRequest(new { message = "ExternalProductId is required." });
        }

        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(new { message = "Name is required." });
        }

        if (string.IsNullOrWhiteSpace(request.Category))
        {
            return BadRequest(new { message = "Category is required." });
        }

        if (string.IsNullOrWhiteSpace(request.Layer))
        {
            return BadRequest(new { message = "Layer is required." });
        }

        if (string.IsNullOrWhiteSpace(request.SourceImageUrl))
        {
            return BadRequest(new { message = "SourceImageUrl is required." });
        }

        var normalizedExternalProductId = request.ExternalProductId.Trim();
        var alreadyExists = await _dbContext.Garments.AnyAsync(
            g => g.TenantId == tenantId && g.ExternalProductId == normalizedExternalProductId,
            cancellationToken);
        if (alreadyExists)
        {
            return Conflict(new { message = "A garment with this ExternalProductId already exists for the tenant." });
        }

        var now = DateTime.UtcNow;
        var garment = new Garment
        {
            Id = Guid.NewGuid(),
            TenantId = tenantId,
            ExternalProductId = normalizedExternalProductId,
            Name = request.Name.Trim(),
            Category = request.Category.Trim(),
            Layer = request.Layer.Trim(),
            SourceImageUrl = request.SourceImageUrl.Trim(),
            IsActive = true,
            IsDeleted = false,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.Garments.Add(garment);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var response = ToGarmentResponse(garment, latestAsset: null, latestJob: null);
        return Created($"/api/garments/{garment.Id}", response);
    }

    [HttpDelete("{garmentId:guid}")]
    public async Task<IActionResult> DeleteAsync(Guid garmentId, CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var garment = await _dbContext.Garments.FirstOrDefaultAsync(
            g => g.Id == garmentId && g.TenantId == tenantId && g.IsActive && !g.IsDeleted,
            cancellationToken);
        if (garment is null)
        {
            return NotFound(new { message = "Garment was not found for this tenant." });
        }

        var now = DateTime.UtcNow;
        garment.IsActive = false;
        garment.IsDeleted = true;
        garment.DeletedAt = now;
        garment.UpdatedAt = now;
        await _dbContext.SaveChangesAsync(cancellationToken);

        return NoContent();
    }

    private async Task<IReadOnlyList<GarmentResponse>> BuildGarmentResponsesAsync(
        Guid tenantId,
        IReadOnlyList<Garment> garments,
        CancellationToken cancellationToken)
    {
        if (garments.Count == 0)
        {
            return Array.Empty<GarmentResponse>();
        }

        var garmentIds = garments.Select(g => g.Id).ToHashSet();
        var externalProductIds = garments.Select(g => g.ExternalProductId).ToHashSet(StringComparer.Ordinal);

        var assets = await _dbContext.GarmentAssets
            .Where(ga => ga.TenantId == tenantId && garmentIds.Contains(ga.GarmentId))
            .OrderByDescending(ga => ga.CreatedAt)
            .ToListAsync(cancellationToken);
        var assetsByGarmentId = assets
            .GroupBy(ga => ga.GarmentId)
            .ToDictionary(group => group.Key, group => group.First());

        var ingestionJobs = await _dbContext.IngestionJobs
            .Where(ij => ij.TenantId == tenantId && externalProductIds.Contains(ij.ExternalProductId))
            .OrderByDescending(ij => ij.CreatedAt)
            .ToListAsync(cancellationToken);
        var jobsByExternalProductId = ingestionJobs
            .GroupBy(ij => ij.ExternalProductId)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.Ordinal);

        return garments
            .Select(garment =>
            {
                assetsByGarmentId.TryGetValue(garment.Id, out var latestAsset);
                jobsByExternalProductId.TryGetValue(garment.ExternalProductId, out var latestJob);
                return ToGarmentResponse(garment, latestAsset, latestJob);
            })
            .ToList();
    }

    private async Task<GarmentResponse> BuildGarmentResponseAsync(
        Guid tenantId,
        Garment garment,
        CancellationToken cancellationToken)
    {
        var latestAsset = await _dbContext.GarmentAssets
            .Where(ga => ga.TenantId == tenantId && ga.GarmentId == garment.Id)
            .OrderByDescending(ga => ga.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken);

        var latestJob = await _dbContext.IngestionJobs
            .Where(ij => ij.TenantId == tenantId && ij.ExternalProductId == garment.ExternalProductId)
            .OrderByDescending(ij => ij.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken);

        return ToGarmentResponse(garment, latestAsset, latestJob);
    }

    private static GarmentResponse ToGarmentResponse(
        Garment garment,
        GarmentAsset? latestAsset,
        IngestionJob? latestJob)
    {
        var hasProcessedAsset =
            latestAsset is not null &&
            !string.IsNullOrWhiteSpace(latestAsset.ProcessedMaskUrl) &&
            !string.IsNullOrWhiteSpace(latestAsset.ProcessedTextureUrl);

        return new GarmentResponse
        {
            Id = garment.Id,
            TenantId = garment.TenantId,
            ExternalProductId = garment.ExternalProductId,
            Name = garment.Name,
            Category = garment.Category,
            Layer = garment.Layer,
            SourceImageUrl = garment.SourceImageUrl,
            IsActive = garment.IsActive,
            Status = GetGarmentStatus(garment, hasProcessedAsset, latestJob),
            HasProcessedAsset = hasProcessedAsset,
            ProcessedImageUrl = latestAsset?.ProcessedImageUrl,
            ProcessedMaskUrl = latestAsset?.ProcessedMaskUrl,
            ProcessedTextureUrl = latestAsset?.ProcessedTextureUrl,
            LatestAssetCreatedAt = latestAsset?.CreatedAt,
            LatestIngestionStatus = latestJob?.Status,
            LatestIngestionErrorMessage = latestJob?.ErrorMessage,
            CreatedAt = garment.CreatedAt,
            UpdatedAt = garment.UpdatedAt
        };
    }

    private static string GetGarmentStatus(
        Garment garment,
        bool hasProcessedAsset,
        IngestionJob? latestJob)
    {
        if (garment.IsDeleted || !garment.IsActive)
        {
            return "deleted";
        }

        if (hasProcessedAsset)
        {
            return "ready";
        }

        var latestStatus = latestJob?.Status?.Trim().ToLowerInvariant();
        if (string.IsNullOrWhiteSpace(latestStatus))
        {
            return "pending";
        }

        if (IsFailedStatus(latestStatus))
        {
            return "failed";
        }

        if (IsActiveStatus(latestStatus))
        {
            return "processing";
        }

        if (IsCompletedStatus(latestStatus))
        {
            // Completed without processed assets is treated as failed consistency.
            return "failed";
        }

        return "pending";
    }

    private static bool IsActiveStatus(string status)
    {
        return status is "pending" or "queued" or "running" or "in_progress" or "processing";
    }

    private static bool IsCompletedStatus(string status)
    {
        return status is "completed" or "success";
    }

    private static bool IsFailedStatus(string status)
    {
        return status is "failed" or "error" or "needs_review";
    }
}
