using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Worker;

public class WorkerIngestionClient : IWorkerIngestionClient
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    private readonly HttpClient _httpClient;
    private readonly ILogger<WorkerIngestionClient> _logger;

    public WorkerIngestionClient(HttpClient httpClient, ILogger<WorkerIngestionClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task IngestAsync(
        Guid tenantId,
        Guid garmentId,
        string imageUrl,
        string? externalProductId,
        CancellationToken cancellationToken)
    {
        await RunMockIngestionAsync(
            new WorkerIngestionMockRequest
            {
                JobId = garmentId.ToString(),
                TenantId = tenantId.ToString(),
                GarmentId = garmentId.ToString(),
                SourceType = "catalog_import",
                SourceImageUrls = new List<string> { imageUrl },
                ExternalProductId = externalProductId
            },
            cancellationToken);
    }

    public async Task<WorkerIngestionMockResponse> RunMockIngestionAsync(
        WorkerIngestionMockRequest request,
        CancellationToken cancellationToken)
    {
        var payloadJson = JsonSerializer.Serialize(request, JsonOptions);
        HttpResponseMessage response;

        try
        {
            using var content = new StringContent(payloadJson, Encoding.UTF8, "application/json");
            response = await _httpClient.PostAsync("/jobs/ingestion/mock", content, cancellationToken);
        }
        catch (Exception ex)
        {
            throw new WorkerClientException("Worker ingestion endpoint is unavailable.", innerException: ex);
        }

        if (!response.IsSuccessStatusCode)
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            _logger.LogError(
                "Worker ingestion call failed. StatusCode={StatusCode}; RequestPayload={RequestPayload}; ResponseBody={ResponseBody}",
                (int)response.StatusCode,
                payloadJson,
                content);
            throw new WorkerClientException(
                $"Worker ingestion call failed with {(int)response.StatusCode}: {content}",
                response.StatusCode);
        }

        var payload = await response.Content.ReadFromJsonAsync<WorkerIngestionMockResponse>(cancellationToken: cancellationToken);
        if (payload is null)
        {
            throw new WorkerClientException("Worker ingestion returned an empty response payload.");
        }

        return payload;
    }
}
