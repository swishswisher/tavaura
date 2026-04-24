using System.Threading;
using System.Threading.Tasks;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Worker;

public interface IWorkerIngestionClient
{
    Task IngestAsync(Guid tenantId, Guid garmentId, string imageUrl, string? externalProductId, CancellationToken cancellationToken);

    Task<WorkerIngestionMockResponse> RunMockIngestionAsync(WorkerIngestionMockRequest request, CancellationToken cancellationToken);
}
