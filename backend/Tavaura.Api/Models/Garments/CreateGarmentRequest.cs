using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Garments;

public class CreateGarmentRequest
{
    [Required]
    public string ExternalProductId { get; set; } = string.Empty;

    [Required]
    public string Name { get; set; } = string.Empty;

    [Required]
    public string Category { get; set; } = string.Empty;

    [Required]
    public string Layer { get; set; } = string.Empty;

    [Required]
    public string SourceImageUrl { get; set; } = string.Empty;
}

