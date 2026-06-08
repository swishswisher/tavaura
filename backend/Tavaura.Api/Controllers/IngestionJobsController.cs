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
[Route("api/ingestion-jobs")]
[Authorize(Roles = AuthRoles.MerchantOrPlatform)]
public class IngestionJobsController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public IngestionJobsController(TavauraDbContext dbContext, ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<IngestionJobListItemResponse>>> ListAsync(
        [FromQuery] string? status,
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var normalizedStatus = status?.Trim().ToLowerInvariant();

        var ingestionJobsQuery = _dbContext.IngestionJobs
            .AsNoTracking()
            .Where(ij => ij.TenantId == tenantId);

        if (!string.IsNullOrWhiteSpace(normalizedStatus) &&
            !string.Equals(normalizedStatus, "all", StringComparison.OrdinalIgnoreCase))
        {
            ingestionJobsQuery = ingestionJobsQuery
                .Where(ij => ij.Status == normalizedStatus);
        }

        var rows = await (
            from ingestionJob in ingestionJobsQuery
            join garment in _dbContext.Garments.AsNoTracking().Where(g => g.TenantId == tenantId && g.IsActive && !g.IsDeleted)
                on ingestionJob.ExternalProductId equals garment.ExternalProductId
            orderby ingestionJob.CreatedAt descending
            select new IngestionJobListItemResponse
            {
                Id = ingestionJob.Id,
                GarmentId = garment.Id,
                GarmentName = garment.Name,
                ExternalProductId = ingestionJob.ExternalProductId,
                Status = ingestionJob.Status,
                AttemptCount = ingestionJob.AttemptCount,
                ErrorMessage = ingestionJob.ErrorMessage,
                StartedAt = ingestionJob.StartedAt,
                CompletedAt = ingestionJob.CompletedAt,
                CreatedAt = ingestionJob.CreatedAt,
                UpdatedAt = ingestionJob.UpdatedAt
            })
            .ToListAsync(cancellationToken);

        return Ok(rows);
    }

    [HttpPost]
    public async Task<ActionResult<IngestionJobResponse>> CreateAsync(
        [FromBody] CreateIngestionJobRequest request,
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
        var garment = await _dbContext.Garments.FirstOrDefaultAsync(
            g => g.Id == request.GarmentId && g.TenantId == tenantId && g.IsActive && !g.IsDeleted,
            cancellationToken);
        if (garment is null)
        {
            return BadRequest(new { message = "Garment does not exist for this tenant." });
        }

        if (string.IsNullOrWhiteSpace(garment.SourceImageUrl))
        {
            return BadRequest(new { message = "Garment is missing SourceImageUrl." });
        }

        var now = DateTime.UtcNow;
        var ingestionJob = new IngestionJob
        {
            Id = Guid.NewGuid(),
            TenantId = tenantId,
            ExternalProductId = garment.ExternalProductId,
            Status = "pending",
            AttemptCount = 0,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.IngestionJobs.Add(ingestionJob);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var response = ToIngestionJobResponse(ingestionJob, garment.Id);
        return Created($"/api/ingestion-jobs/{ingestionJob.Id}", response);
    }

    private static IngestionJobResponse ToIngestionJobResponse(IngestionJob ingestionJob, Guid garmentId)
    {
        return new IngestionJobResponse
        {
            Id = ingestionJob.Id,
            TenantId = ingestionJob.TenantId,
            GarmentId = garmentId,
            ExternalProductId = ingestionJob.ExternalProductId,
            Status = ingestionJob.Status,
            AttemptCount = ingestionJob.AttemptCount,
            ErrorMessage = ingestionJob.ErrorMessage,
            StartedAt = ingestionJob.StartedAt,
            CompletedAt = ingestionJob.CompletedAt,
            CreatedAt = ingestionJob.CreatedAt,
            UpdatedAt = ingestionJob.UpdatedAt
        };
    }
}
