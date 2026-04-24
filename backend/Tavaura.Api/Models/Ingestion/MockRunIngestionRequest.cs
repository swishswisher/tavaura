using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Ingestion;

public class MockRunIngestionRequest
{
    [Required]
    public Guid TenantId { get; set; }

    [Required]
    public Guid GarmentId { get; set; }

    [Required]
    public string ExternalProductId { get; set; } = string.Empty;

    public string SourceType { get; set; } = "catalog_import";

    public List<string> SourceImageUrls { get; set; } = [];
}

