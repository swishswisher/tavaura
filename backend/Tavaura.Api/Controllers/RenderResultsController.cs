using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Models.Jobs;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/render-results")]
[Authorize(Roles = AuthRoles.CustomerMerchantOrPlatform)]
public class RenderResultsController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public RenderResultsController(TavauraDbContext dbContext, ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<RenderResultListItemResponse>>> ListAsync(
        [FromQuery] int limit = 50,
        CancellationToken cancellationToken = default)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var safeLimit = Math.Clamp(limit, 1, 200);

        var renderJobsQuery = _dbContext.RenderJobs
            .AsNoTracking()
            .Where(rj => rj.TenantId == tenantId);

        if (User.IsInRole(AuthRoles.CustomerUser))
        {
            if (!Guid.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out var currentUserId))
            {
                return Forbid();
            }

            renderJobsQuery = renderJobsQuery.Where(rj =>
                _dbContext.Avatars.Any(a => a.Id == rj.AvatarId && a.UserId == currentUserId));
        }

        var rows = await renderJobsQuery
            .Join(
                _dbContext.GarmentAssets.AsNoTracking(),
                rj => rj.GarmentAssetId,
                ga => ga.Id,
                (rj, ga) => new { RenderJob = rj, GarmentAsset = ga })
            .Join(
                _dbContext.Garments.AsNoTracking(),
                x => x.GarmentAsset.GarmentId,
                g => g.Id,
                (x, g) => new
                {
                    x.RenderJob,
                    GarmentName = g.Name,
                    LatestResult = _dbContext.RenderResults
                        .Where(rr => rr.RenderJobId == x.RenderJob.Id)
                        .OrderByDescending(rr => rr.CreatedAt)
                        .Select(rr => new
                        {
                            rr.Id,
                            rr.OutputImageUrl,
                            rr.PreviewImageUrl,
                            rr.CreatedAt
                        })
                        .FirstOrDefault()
                })
            .OrderByDescending(x => x.RenderJob.CreatedAt)
            .Take(safeLimit)
            .ToListAsync(cancellationToken);

        var response = rows.Select(row => new RenderResultListItemResponse
        {
            RenderJobId = row.RenderJob.Id,
            RenderResultId = row.LatestResult?.Id,
            GarmentName = row.GarmentName,
            Status = row.RenderJob.Status,
            ErrorMessage = row.RenderJob.ErrorMessage,
            OutputImageUrl = row.LatestResult?.OutputImageUrl,
            PreviewImageUrl = row.LatestResult?.PreviewImageUrl,
            CreatedAt = row.LatestResult?.CreatedAt ?? row.RenderJob.CreatedAt
        }).ToList();

        return Ok(response);
    }

    [HttpGet("{jobId:guid}")]
    public async Task<ActionResult<RenderResultResponse>> GetLatestAsync(
        Guid jobId,
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var renderJob = await _dbContext.RenderJobs.FirstOrDefaultAsync(
            rj => rj.Id == jobId && rj.TenantId == tenantId,
            cancellationToken);
        if (renderJob is null)
        {
            return NotFound(new { message = "Render job was not found for this tenant." });
        }

        if (User.IsInRole(AuthRoles.CustomerUser))
        {
            var avatar = await _dbContext.Avatars.FirstOrDefaultAsync(
                a => a.Id == renderJob.AvatarId,
                cancellationToken);
            if (avatar is null ||
                !string.Equals(
                    User.FindFirstValue(ClaimTypes.NameIdentifier),
                    avatar.UserId.ToString(),
                    StringComparison.OrdinalIgnoreCase))
            {
                return Forbid();
            }
        }

        var renderResult = await _dbContext.RenderResults
            .Where(rr => rr.RenderJobId == renderJob.Id)
            .OrderByDescending(rr => rr.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken);
        if (renderResult is null)
        {
            return NotFound(new
            {
                message = "Render result is not available yet.",
                renderJobId = renderJob.Id,
                status = renderJob.Status,
                errorMessage = renderJob.ErrorMessage
            });
        }

        return Ok(new RenderResultResponse
        {
            RenderJobId = renderJob.Id,
            Status = renderJob.Status,
            ErrorMessage = renderJob.ErrorMessage,
            StartedAt = renderJob.StartedAt,
            CompletedAt = renderJob.CompletedAt,
            RenderResultId = renderResult.Id,
            OutputImageUrl = renderResult.OutputImageUrl,
            PreviewImageUrl = renderResult.PreviewImageUrl,
            CreatedAt = renderResult.CreatedAt
        });
    }
}
