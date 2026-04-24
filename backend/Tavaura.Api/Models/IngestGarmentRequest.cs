namespace Tavaura.Api.Models;

public class IngestGarmentRequest
{
    public string ExternalProductId { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Category { get; set; } = string.Empty;

    public string Layer { get; set; } = string.Empty;

    public string SourceImageUrl { get; set; } = string.Empty;
}

