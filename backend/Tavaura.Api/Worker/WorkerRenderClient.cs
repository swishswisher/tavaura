using System.Net.Http.Json;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Worker;

public class WorkerRenderClient : IWorkerRenderClient
{
    private readonly HttpClient _httpClient;

    public WorkerRenderClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<WorkerRenderMockResponse> RunMockRenderAsync(
        WorkerRenderMockRequest request,
        CancellationToken cancellationToken)
    {
        HttpResponseMessage response;

        try
        {
            response = await _httpClient.PostAsJsonAsync("/jobs/render/mock", request, cancellationToken);
        }
        catch (Exception ex)
        {
            throw new WorkerClientException("Worker render endpoint is unavailable.", innerException: ex);
        }

        if (!response.IsSuccessStatusCode)
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new WorkerClientException(
                $"Worker render call failed with {(int)response.StatusCode}: {content}",
                response.StatusCode);
        }

        var payload = await response.Content.ReadFromJsonAsync<WorkerRenderMockResponse>(cancellationToken: cancellationToken);
        if (payload is null)
        {
            throw new WorkerClientException("Worker render returned an empty response payload.");
        }

        return payload;
    }
}

