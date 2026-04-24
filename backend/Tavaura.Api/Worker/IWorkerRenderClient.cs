using System.Threading;
using System.Threading.Tasks;
using Tavaura.Api.Worker.Contracts;

namespace Tavaura.Api.Worker;

public interface IWorkerRenderClient
{
    Task<WorkerRenderMockResponse> RunMockRenderAsync(WorkerRenderMockRequest request, CancellationToken cancellationToken);
}

