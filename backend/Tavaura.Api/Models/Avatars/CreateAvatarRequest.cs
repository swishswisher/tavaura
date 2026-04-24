using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Avatars;

public class CreateAvatarRequest
{
    [Required]
    public Guid UserId { get; set; }

    [Required]
    public string Source { get; set; } = string.Empty;

    [Required]
    public double HeightCm { get; set; }

    [Required]
    public double WeightKg { get; set; }

    [Required]
    public int Age { get; set; }

    [Required]
    public string Gender { get; set; } = string.Empty;

    public bool IsPregnant { get; set; }

    [Required]
    public string SkinTone { get; set; } = string.Empty;

    public string? FacePreset { get; set; }

    public string? HairStyleId { get; set; }

    public string? SmplParametersJson { get; set; }
}

