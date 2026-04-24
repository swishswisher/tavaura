using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Models.Admin;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/admin/dashboard")]
[Authorize(Roles = AuthRoles.MerchantOrPlatform)]
public class AdminDashboardController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public AdminDashboardController(TavauraDbContext dbContext, ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpGet]
    public async Task<ActionResult<AdminDashboardResponse>> GetAsync(
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var now = DateTime.UtcNow;
        var recentWindowStart = now.AddDays(-7);

        var allGarmentLookup = await _dbContext.Garments
            .AsNoTracking()
            .Where(g => g.TenantId == tenantId)
            .Select(g => new
            {
                g.Id,
                g.Name,
                g.ExternalProductId
            })
            .ToListAsync(cancellationToken);

        var activeGarments = await _dbContext.Garments
            .AsNoTracking()
            .Where(g => g.TenantId == tenantId && g.IsActive)
            .Select(g => new
            {
                g.Id,
                g.Name,
                g.ExternalProductId,
                g.CreatedAt
            })
            .ToListAsync(cancellationToken);

        var activeGarmentIds = activeGarments
            .Select(g => g.Id)
            .ToHashSet();
        var activeExternalProductIds = activeGarments
            .Select(g => g.ExternalProductId)
            .ToHashSet(StringComparer.Ordinal);

        var latestAssetByGarmentId = new Dictionary<Guid, bool>();
        if (activeGarmentIds.Count > 0)
        {
            var garmentAssets = await _dbContext.GarmentAssets
                .AsNoTracking()
                .Where(ga => ga.TenantId == tenantId && activeGarmentIds.Contains(ga.GarmentId))
                .OrderByDescending(ga => ga.CreatedAt)
                .Select(ga => new
                {
                    ga.GarmentId,
                    ga.ProcessedMaskUrl,
                    ga.ProcessedTextureUrl
                })
                .ToListAsync(cancellationToken);

            latestAssetByGarmentId = garmentAssets
                .GroupBy(ga => ga.GarmentId)
                .ToDictionary(
                    group => group.Key,
                    group =>
                    {
                        var latest = group.First();
                        return !string.IsNullOrWhiteSpace(latest.ProcessedMaskUrl) &&
                               !string.IsNullOrWhiteSpace(latest.ProcessedTextureUrl);
                    });
        }

        var latestIngestionByExternalProductId = new Dictionary<string, string>(StringComparer.Ordinal);
        if (activeExternalProductIds.Count > 0)
        {
            var ingestionJobs = await _dbContext.IngestionJobs
                .AsNoTracking()
                .Where(ij => ij.TenantId == tenantId && activeExternalProductIds.Contains(ij.ExternalProductId))
                .OrderByDescending(ij => ij.CreatedAt)
                .Select(ij => new
                {
                    ij.ExternalProductId,
                    ij.Status
                })
                .ToListAsync(cancellationToken);

            latestIngestionByExternalProductId = ingestionJobs
                .GroupBy(ij => ij.ExternalProductId, StringComparer.Ordinal)
                .ToDictionary(group => group.Key, group => group.First().Status, StringComparer.Ordinal);
        }

        var readyGarments = 0;
        var processingGarments = 0;
        var failedGarments = 0;

        foreach (var garment in activeGarments)
        {
            latestAssetByGarmentId.TryGetValue(garment.Id, out var hasProcessedAsset);
            latestIngestionByExternalProductId.TryGetValue(garment.ExternalProductId, out var latestIngestionStatus);
            var garmentStatus = ResolveGarmentStatus(hasProcessedAsset, latestIngestionStatus);
            if (string.Equals(garmentStatus, "ready", StringComparison.Ordinal))
            {
                readyGarments++;
                continue;
            }

            if (string.Equals(garmentStatus, "processing", StringComparison.Ordinal))
            {
                processingGarments++;
                continue;
            }

            if (string.Equals(garmentStatus, "failed", StringComparison.Ordinal))
            {
                failedGarments++;
            }
        }

        var totalRenders = await _dbContext.RenderJobs
            .AsNoTracking()
            .CountAsync(rj => rj.TenantId == tenantId, cancellationToken);

        var recentResults = await _dbContext.RenderResults
            .AsNoTracking()
            .Join(
                _dbContext.RenderJobs.AsNoTracking().Where(rj => rj.TenantId == tenantId),
                rr => rr.RenderJobId,
                rj => rj.Id,
                (rr, _) => rr)
            .CountAsync(rr => rr.CreatedAt >= recentWindowStart, cancellationToken);

        var externalProductLookup = allGarmentLookup
            .GroupBy(g => g.ExternalProductId, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.Ordinal);

        var garmentCreatedEvents = activeGarments
            .Select(g => new AdminDashboardActivityItem
            {
                EventType = "garment_created",
                EventLabel = "Garment created",
                RelatedName = g.Name,
                RelatedPath = $"/admin/garments/{g.Id}",
                Status = "created",
                Timestamp = g.CreatedAt
            })
            .OrderByDescending(item => item.Timestamp)
            .Take(20)
            .ToList();

        var ingestionEventRows = await _dbContext.IngestionJobs
            .AsNoTracking()
            .Where(ij =>
                ij.TenantId == tenantId &&
                (ij.Status == "completed" || ij.Status == "failed"))
            .OrderByDescending(ij => ij.CompletedAt ?? ij.UpdatedAt)
            .Take(20)
            .Select(ij => new
            {
                ij.ExternalProductId,
                ij.Status,
                Timestamp = ij.CompletedAt ?? ij.UpdatedAt
            })
            .ToListAsync(cancellationToken);

        var ingestionEvents = ingestionEventRows
            .Select(ij =>
            {
                externalProductLookup.TryGetValue(ij.ExternalProductId, out var garment);
                var isCompleted = string.Equals(ij.Status, "completed", StringComparison.OrdinalIgnoreCase);

                return new AdminDashboardActivityItem
                {
                    EventType = isCompleted ? "ingestion_completed" : "ingestion_failed",
                    EventLabel = isCompleted ? "Ingestion completed" : "Ingestion failed",
                    RelatedName = garment?.Name ?? ij.ExternalProductId,
                    RelatedPath = garment is not null ? $"/admin/garments/{garment.Id}" : null,
                    Status = ij.Status,
                    Timestamp = ij.Timestamp
                };
            })
            .ToList();

        var renderEventRows = await _dbContext.RenderJobs
            .AsNoTracking()
            .Where(rj =>
                rj.TenantId == tenantId &&
                (rj.Status == "completed" || rj.Status == "failed"))
            .Join(
                _dbContext.GarmentAssets.AsNoTracking().Where(ga => ga.TenantId == tenantId),
                rj => rj.GarmentAssetId,
                ga => ga.Id,
                (rj, ga) => new
                {
                    rj.Id,
                    rj.Status,
                    Timestamp = rj.CompletedAt ?? rj.UpdatedAt,
                    ga.GarmentId
                })
            .Join(
                _dbContext.Garments.AsNoTracking().Where(g => g.TenantId == tenantId),
                x => x.GarmentId,
                g => g.Id,
                (x, g) => new
                {
                    x.Id,
                    x.Status,
                    x.Timestamp,
                    GarmentName = g.Name
                })
            .OrderByDescending(x => x.Timestamp)
            .Take(20)
            .ToListAsync(cancellationToken);

        var renderEvents = renderEventRows
            .Select(rj =>
            {
                var isCompleted = string.Equals(rj.Status, "completed", StringComparison.OrdinalIgnoreCase);
                return new AdminDashboardActivityItem
                {
                    EventType = isCompleted ? "render_completed" : "render_failed",
                    EventLabel = isCompleted ? "Render completed" : "Render failed",
                    RelatedName = rj.GarmentName,
                    RelatedPath = $"/admin/render-results/{rj.Id}",
                    Status = rj.Status,
                    Timestamp = rj.Timestamp
                };
            })
            .ToList();

        var recentActivity = garmentCreatedEvents
            .Concat(ingestionEvents)
            .Concat(renderEvents)
            .OrderByDescending(item => item.Timestamp)
            .Take(20)
            .ToList();

        var latestIngestionJob = await _dbContext.IngestionJobs
            .AsNoTracking()
            .Where(ij => ij.TenantId == tenantId)
            .OrderByDescending(ij => ij.UpdatedAt)
            .Select(ij => new
            {
                ij.Status,
                ij.UpdatedAt
            })
            .FirstOrDefaultAsync(cancellationToken);

        var latestRenderJob = await _dbContext.RenderJobs
            .AsNoTracking()
            .Where(rj => rj.TenantId == tenantId)
            .OrderByDescending(rj => rj.UpdatedAt)
            .Select(rj => new
            {
                rj.Status,
                rj.UpdatedAt
            })
            .FirstOrDefaultAsync(cancellationToken);

        var response = new AdminDashboardResponse
        {
            Metrics = new AdminDashboardMetrics
            {
                TotalGarments = activeGarments.Count,
                ReadyGarments = readyGarments,
                ProcessingGarments = processingGarments,
                FailedGarments = failedGarments,
                TotalRenders = totalRenders,
                RecentResults = recentResults
            },
            RecentActivity = recentActivity,
            WorkspaceHealth = new[]
            {
                new AdminDashboardHealthSignal
                {
                    Key = "api_auth",
                    Label = "API auth",
                    Status = "ready",
                    Detail = "Authenticated session is valid."
                },
                new AdminDashboardHealthSignal
                {
                    Key = "tenant_resolution",
                    Label = "Tenant resolution",
                    Status = "ready",
                    Detail = "Tenant context resolved from authenticated identity."
                },
                BuildPipelineHealthSignal(
                    key: "worker_pipeline",
                    label: "Worker pipeline",
                    latestStatus: latestIngestionJob?.Status,
                    lastUpdatedAt: latestIngestionJob?.UpdatedAt),
                BuildPipelineHealthSignal(
                    key: "render_pipeline",
                    label: "Render pipeline",
                    latestStatus: latestRenderJob?.Status,
                    lastUpdatedAt: latestRenderJob?.UpdatedAt)
            }
        };

        return Ok(response);
    }

    private static AdminDashboardHealthSignal BuildPipelineHealthSignal(
        string key,
        string label,
        string? latestStatus,
        DateTime? lastUpdatedAt)
    {
        if (string.IsNullOrWhiteSpace(latestStatus))
        {
            return new AdminDashboardHealthSignal
            {
                Key = key,
                Label = label,
                Status = "unknown",
                Detail = "No jobs have run yet.",
                LastUpdatedAt = null
            };
        }

        if (string.Equals(latestStatus, "failed", StringComparison.OrdinalIgnoreCase))
        {
            return new AdminDashboardHealthSignal
            {
                Key = key,
                Label = label,
                Status = "degraded",
                Detail = "Last job failed and needs attention.",
                LastUpdatedAt = lastUpdatedAt
            };
        }

        if (string.Equals(latestStatus, "pending", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(latestStatus, "processing", StringComparison.OrdinalIgnoreCase))
        {
            return new AdminDashboardHealthSignal
            {
                Key = key,
                Label = label,
                Status = "active",
                Detail = "Jobs are currently processing.",
                LastUpdatedAt = lastUpdatedAt
            };
        }

        if (string.Equals(latestStatus, "completed", StringComparison.OrdinalIgnoreCase))
        {
            return new AdminDashboardHealthSignal
            {
                Key = key,
                Label = label,
                Status = "ready",
                Detail = "Recent jobs completed successfully.",
                LastUpdatedAt = lastUpdatedAt
            };
        }

        return new AdminDashboardHealthSignal
        {
            Key = key,
            Label = label,
            Status = "unknown",
            Detail = $"Latest status: {latestStatus}.",
            LastUpdatedAt = lastUpdatedAt
        };
    }

    private static string ResolveGarmentStatus(bool hasProcessedAsset, string? latestIngestionStatus)
    {
        if (hasProcessedAsset)
        {
            return "ready";
        }

        var normalizedStatus = latestIngestionStatus?.Trim().ToLowerInvariant();
        if (string.IsNullOrWhiteSpace(normalizedStatus))
        {
            return "pending";
        }

        if (IsFailedStatus(normalizedStatus))
        {
            return "failed";
        }

        if (IsActiveStatus(normalizedStatus))
        {
            return "processing";
        }

        if (IsCompletedStatus(normalizedStatus))
        {
            // Completed without assets should surface as failed consistency.
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
