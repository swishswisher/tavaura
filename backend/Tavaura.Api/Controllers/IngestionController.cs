using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Ingestion;
using Tavaura.Api.Worker;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/ingestion")]
public class IngestionController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly IWorkerIngestionClient _workerIngestionClient;
    private readonly ILogger<IngestionController> _logger;

    public IngestionController(
        TavauraDbContext dbContext,
        IWorkerIngestionClient workerIngestionClient,
        ILogger<IngestionController> logger)
    {
        _dbContext = dbContext;
        _workerIngestionClient = workerIngestionClient;
        _logger = logger;
    }

    [HttpPost("mock-run")]
    public async Task<ActionResult<MockRunIngestionResponse>> RunMockIngestionAsync(
        [FromBody] MockRunIngestionRequest request,
        CancellationToken cancellationToken)
    {
        if (request.TenantId == Guid.Empty)
        {
            return BadRequest("TenantId is required.");
        }

        if (request.GarmentId == Guid.Empty)
        {
            return BadRequest("GarmentId is required.");
        }

        if (string.IsNullOrWhiteSpace(request.ExternalProductId))
        {
            return BadRequest("ExternalProductId is required.");
        }

        var tenantExists = await _dbContext.Tenants.AnyAsync(t => t.Id == request.TenantId, cancellationToken);
        if (!tenantExists)
        {
            return BadRequest("Tenant does not exist.");
        }

        var now = DateTime.UtcNow;
        var ingestionJob = new IngestionJob
        {
            Id = Guid.NewGuid(),
            TenantId = request.TenantId,
            ExternalProductId = request.ExternalProductId,
            Status = "pending",
            AttemptCount = 0,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.IngestionJobs.Add(ingestionJob);
        await _dbContext.SaveChangesAsync(cancellationToken);

        ingestionJob.Status = "processing";
        ingestionJob.AttemptCount += 1;
        ingestionJob.StartedAt = DateTime.UtcNow;
        ingestionJob.UpdatedAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        try
        {
            var workerResponse = await _workerIngestionClient.RunMockIngestionAsync(
                new WorkerIngestionMockRequest
                {
                    JobId = ingestionJob.Id.ToString(),
                    TenantId = request.TenantId.ToString(),
                    GarmentId = request.GarmentId.ToString(),
                    SourceType = request.SourceType,
                    SourceImageUrls = request.SourceImageUrls,
                    ExternalProductId = request.ExternalProductId
                },
                cancellationToken);

            ingestionJob.Status = workerResponse.Status;
            ingestionJob.CompletedAt = workerResponse.CompletedAt;
            ingestionJob.UpdatedAt = DateTime.UtcNow;
            ingestionJob.ErrorMessage = null;

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Mock ingestion completed for job {JobId}. Classification={ClassificationHint}, CanonicalVersion={CanonicalVersion}, ReviewRequired={ReviewRequired}",
                ingestionJob.Id,
                workerResponse.ClassificationHint,
                workerResponse.CanonicalAssetVersion,
                workerResponse.ReviewRequired);

            return Ok(new MockRunIngestionResponse
            {
                IngestionJobId = ingestionJob.Id,
                Status = ingestionJob.Status,
                StartedAt = workerResponse.StartedAt,
                CompletedAt = workerResponse.CompletedAt,
                ClassificationHint = workerResponse.ClassificationHint,
                SegmentationMaskUrl = workerResponse.SegmentationMaskUrl,
                CanonicalAssetVersion = workerResponse.CanonicalAssetVersion,
                ReviewRequired = workerResponse.ReviewRequired
            });
        }
        catch (WorkerClientException ex)
        {
            _logger.LogError(ex, "Mock ingestion worker call failed for job {JobId}", ingestionJob.Id);

            ingestionJob.Status = "failed";
            ingestionJob.ErrorMessage = ex.Message;
            ingestionJob.CompletedAt = DateTime.UtcNow;
            ingestionJob.UpdatedAt = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync(cancellationToken);

            return StatusCode(StatusCodes.Status503ServiceUnavailable, new
            {
                message = "Worker ingestion endpoint unavailable.",
                ingestionJobId = ingestionJob.Id
            });
        }
    }
}
