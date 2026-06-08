using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Png;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Processing;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Render;
using Tavaura.Api.Worker;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/render")]
public class RenderController : ControllerBase
{
    private static readonly HttpClient ImageHttpClient = new();
    private static readonly PngEncoder PngEncoder = new();
    private const int DefaultAvatarWidth = 768;
    private const int DefaultAvatarHeight = 1024;

    private readonly TavauraDbContext _dbContext;
    private readonly IWorkerRenderClient _workerRenderClient;
    private readonly ILogger<RenderController> _logger;

    public RenderController(
        TavauraDbContext dbContext,
        IWorkerRenderClient workerRenderClient,
        ILogger<RenderController> logger)
    {
        _dbContext = dbContext;
        _workerRenderClient = workerRenderClient;
        _logger = logger;
    }

    [HttpGet("/render")]
    public async Task<IActionResult> RenderGarmentPreviewAsync(
        [FromQuery] Guid garmentId,
        CancellationToken cancellationToken)
    {
        if (garmentId == Guid.Empty)
        {
            return BadRequest(new { message = "garmentId is required." });
        }

        var garmentAsset = await (
            from garment in _dbContext.Garments.AsNoTracking()
            join asset in _dbContext.GarmentAssets.AsNoTracking()
                on garment.Id equals asset.GarmentId
            where garment.Id == garmentId && garment.IsActive && !garment.IsDeleted
            orderby asset.CreatedAt descending
            select new
            {
                garment.Name,
                asset.ProcessedImageUrl
            })
            .FirstOrDefaultAsync(cancellationToken);

        if (garmentAsset is null)
        {
            return NotFound(new { message = "Garment was not found." });
        }

        if (string.IsNullOrWhiteSpace(garmentAsset.ProcessedImageUrl))
        {
            return Conflict(new
            {
                message = "Garment does not have a processed transparent image yet. Complete ingestion first."
            });
        }

        byte[] garmentImageBytes;
        try
        {
            garmentImageBytes = await DownloadImageBytesAsync(
                garmentAsset.ProcessedImageUrl,
                cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Failed to download processed garment image for garment {GarmentId} from {ImageUrl}",
                garmentId,
                garmentAsset.ProcessedImageUrl);

            return StatusCode(StatusCodes.Status502BadGateway, new
            {
                message = "Unable to fetch the processed garment image."
            });
        }

        try
        {
            using var avatarImage = CreateDefaultAvatarImage();
            using var garmentImage = Image.Load<Rgba32>(garmentImageBytes);

            ResizeGarmentForAvatar(garmentImage, avatarImage);

            var overlayX = (avatarImage.Width - garmentImage.Width) / 2;
            var overlayY = (int)(avatarImage.Height * 0.25f);

            avatarImage.Mutate(ctx => ctx.DrawImage(garmentImage, new Point(overlayX, overlayY), 1f));

            using var output = new MemoryStream();
            await avatarImage.SaveAsPngAsync(output, PngEncoder, cancellationToken);

            Response.Headers.CacheControl = "no-store";
            return File(output.ToArray(), "image/png");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to compose render preview for garment {GarmentId}", garmentId);
            return StatusCode(StatusCodes.Status500InternalServerError, new
            {
                message = "Unable to generate render preview."
            });
        }
    }

    [HttpPost("mock-run")]
    public async Task<ActionResult<MockRunRenderResponse>> RunMockRenderAsync(
        [FromBody] MockRunRenderRequest request,
        CancellationToken cancellationToken)
    {
        if (request.TenantId == Guid.Empty)
        {
            return BadRequest("TenantId is required.");
        }

        if (request.AvatarId == Guid.Empty || request.GarmentAssetId == Guid.Empty || request.AssetVersionId == Guid.Empty)
        {
            return BadRequest("AvatarId, GarmentAssetId, and AssetVersionId are required.");
        }

        var tenantExists = await _dbContext.Tenants.AnyAsync(t => t.Id == request.TenantId, cancellationToken);
        if (!tenantExists)
        {
            return BadRequest("Tenant does not exist.");
        }

        var avatar = await _dbContext.Avatars.FirstOrDefaultAsync(a => a.Id == request.AvatarId, cancellationToken);
        if (avatar is null)
        {
            return BadRequest("Avatar does not exist.");
        }

        if (avatar.TenantId.HasValue && avatar.TenantId.Value != request.TenantId)
        {
            return BadRequest("Avatar does not belong to the provided tenant.");
        }

        var garmentAsset = await _dbContext.GarmentAssets
            .FirstOrDefaultAsync(ga => ga.Id == request.GarmentAssetId, cancellationToken);
        if (garmentAsset is null)
        {
            return BadRequest("Garment asset does not exist.");
        }

        if (garmentAsset.TenantId != request.TenantId)
        {
            return BadRequest("Garment asset does not belong to the provided tenant.");
        }

        var assetVersion = await _dbContext.AssetVersions
            .FirstOrDefaultAsync(av => av.Id == request.AssetVersionId, cancellationToken);
        if (assetVersion is null)
        {
            return BadRequest("Asset version does not exist.");
        }

        if (assetVersion.GarmentAssetId != request.GarmentAssetId)
        {
            return BadRequest("Asset version is not linked to the provided garment asset.");
        }

        var now = DateTime.UtcNow;
        var renderJob = new RenderJob
        {
            Id = Guid.NewGuid(),
            TenantId = request.TenantId,
            AvatarId = request.AvatarId,
            GarmentAssetId = request.GarmentAssetId,
            AssetVersionId = request.AssetVersionId,
            Status = "pending",
            AttemptCount = 0,
            IsDeleted = false,
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.RenderJobs.Add(renderJob);
        await _dbContext.SaveChangesAsync(cancellationToken);

        renderJob.Status = "processing";
        renderJob.AttemptCount += 1;
        renderJob.StartedAt = DateTime.UtcNow;
        renderJob.UpdatedAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        try
        {
            var workerResponse = await _workerRenderClient.RunMockRenderAsync(
                new WorkerRenderMockRequest
                {
                    JobId = renderJob.Id.ToString(),
                    TenantId = request.TenantId.ToString(),
                    Mode = request.Mode,
                    AvatarId = request.AvatarId.ToString(),
                    PhotoInputUrl = request.PhotoInputUrl,
                    GarmentAssetId = request.GarmentAssetId.ToString(),
                    AssetVersionId = request.AssetVersionId.ToString()
                },
                cancellationToken);

            renderJob.Status = workerResponse.Status;
            renderJob.CompletedAt = workerResponse.CompletedAt;
            renderJob.UpdatedAt = DateTime.UtcNow;
            renderJob.ErrorMessage = null;

            var renderResult = new RenderResult
            {
                Id = Guid.NewGuid(),
                RenderJobId = renderJob.Id,
                OutputImageUrl = workerResponse.RenderOutputUrl,
                PreviewImageUrl = workerResponse.PreviewOutputUrl,
                IsDeleted = false,
                CreatedAt = DateTime.UtcNow
            };

            _dbContext.RenderResults.Add(renderResult);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Mock render completed for job {JobId}. Output={OutputUrl}, Preview={PreviewUrl}",
                renderJob.Id,
                renderResult.OutputImageUrl,
                renderResult.PreviewImageUrl);

            return Ok(new MockRunRenderResponse
            {
                RenderJobId = renderJob.Id,
                RenderResultId = renderResult.Id,
                Status = renderJob.Status,
                StartedAt = workerResponse.StartedAt,
                CompletedAt = workerResponse.CompletedAt,
                OutputImageUrl = renderResult.OutputImageUrl,
                PreviewImageUrl = renderResult.PreviewImageUrl
            });
        }
        catch (WorkerClientException ex)
        {
            _logger.LogError(ex, "Mock render worker call failed for job {JobId}", renderJob.Id);

            renderJob.Status = "failed";
            renderJob.ErrorMessage = ex.Message;
            renderJob.CompletedAt = DateTime.UtcNow;
            renderJob.UpdatedAt = DateTime.UtcNow;
            await _dbContext.SaveChangesAsync(cancellationToken);

            return StatusCode(StatusCodes.Status503ServiceUnavailable, new
            {
                message = "Worker render endpoint unavailable.",
                renderJobId = renderJob.Id
            });
        }
    }

    private static async Task<byte[]> DownloadImageBytesAsync(
        string imageUrl,
        CancellationToken cancellationToken)
    {
        using var response = await ImageHttpClient.GetAsync(
            imageUrl,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken);

        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsByteArrayAsync(cancellationToken);
    }

    private static void ResizeGarmentForAvatar(Image<Rgba32> garmentImage, Image<Rgba32> avatarImage)
    {
        var maxWidth = (int)(avatarImage.Width * 0.52f);
        var maxHeight = (int)(avatarImage.Height * 0.46f);
        var widthScale = maxWidth / (float)garmentImage.Width;
        var heightScale = maxHeight / (float)garmentImage.Height;
        var scale = Math.Min(widthScale, heightScale);

        if (scale >= 1f)
        {
            return;
        }

        var resizedWidth = Math.Max(1, (int)MathF.Round(garmentImage.Width * scale));
        var resizedHeight = Math.Max(1, (int)MathF.Round(garmentImage.Height * scale));
        garmentImage.Mutate(ctx => ctx.Resize(resizedWidth, resizedHeight));
    }

    private static Image<Rgba32> CreateDefaultAvatarImage()
    {
        var image = new Image<Rgba32>(
            DefaultAvatarWidth,
            DefaultAvatarHeight,
            new Rgba32(248, 250, 252, 255));

        FillEllipse(image, 384, 975, 170, 26, new Rgba32(15, 23, 42, 28));
        FillEllipse(image, 384, 180, 88, 104, new Rgba32(237, 202, 177, 255));
        FillRectangle(image, 345, 255, 78, 74, new Rgba32(237, 202, 177, 255));
        FillEllipse(image, 384, 480, 178, 240, new Rgba32(214, 220, 229, 255));
        FillRectangle(image, 220, 360, 328, 360, new Rgba32(214, 220, 229, 255));
        FillEllipse(image, 256, 480, 54, 156, new Rgba32(237, 202, 177, 255));
        FillEllipse(image, 512, 480, 54, 156, new Rgba32(237, 202, 177, 255));
        FillRectangle(image, 286, 690, 82, 220, new Rgba32(100, 116, 139, 255));
        FillRectangle(image, 400, 690, 82, 220, new Rgba32(100, 116, 139, 255));
        FillEllipse(image, 327, 925, 72, 26, new Rgba32(51, 65, 85, 255));
        FillEllipse(image, 441, 925, 72, 26, new Rgba32(51, 65, 85, 255));

        return image;
    }

    private static void FillRectangle(
        Image<Rgba32> image,
        int x,
        int y,
        int width,
        int height,
        Rgba32 color)
    {
        var startX = Math.Max(0, x);
        var startY = Math.Max(0, y);
        var endX = Math.Min(image.Width, x + width);
        var endY = Math.Min(image.Height, y + height);

        for (var px = startX; px < endX; px++)
        {
            for (var py = startY; py < endY; py++)
            {
                image[px, py] = color;
            }
        }
    }

    private static void FillEllipse(
        Image<Rgba32> image,
        int centerX,
        int centerY,
        int radiusX,
        int radiusY,
        Rgba32 color)
    {
        var startX = Math.Max(0, centerX - radiusX);
        var endX = Math.Min(image.Width - 1, centerX + radiusX);
        var startY = Math.Max(0, centerY - radiusY);
        var endY = Math.Min(image.Height - 1, centerY + radiusY);

        var radiusXSquared = radiusX * radiusX;
        var radiusYSquared = radiusY * radiusY;

        for (var px = startX; px <= endX; px++)
        {
            for (var py = startY; py <= endY; py++)
            {
                var dx = px - centerX;
                var dy = py - centerY;
                var ellipseValue =
                    (dx * dx) / (double)radiusXSquared +
                    (dy * dy) / (double)radiusYSquared;

                if (ellipseValue <= 1d)
                {
                    image[px, py] = color;
                }
            }
        }
    }
}
