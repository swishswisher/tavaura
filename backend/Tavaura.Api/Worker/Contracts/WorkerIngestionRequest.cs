using System;
using System.Text.Json.Serialization;

namespace Tavaura.Api.Worker.Contracts;

public class WorkerIngestionRequest
{
    [JsonPropertyName("garment_id")]
    public Guid GarmentId { get; set; }

    [JsonPropertyName("image_url")]
    public string ImageUrl { get; set; } = default!;
}
