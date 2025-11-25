using System;

namespace Tavaura.Api.Domain.Entities;

/// <summary>
/// Represents a saved avatar configuration for a user, including anthropometric data and rendering presets.
/// </summary>
public class Avatar
{
    public Guid Id { get; set; }

    public Guid UserId { get; set; }

    public Guid? TenantId { get; set; }

    public string Source { get; set; } = string.Empty;

    public double HeightCm { get; set; }

    public double WeightKg { get; set; }

    public int Age { get; set; }

    public string Gender { get; set; } = string.Empty;

    public bool IsPregnant { get; set; }

    public string SkinTone { get; set; } = string.Empty;

    public string? FacePreset { get; set; }

    public string? HairStyleId { get; set; }

    public string SmplParametersJson { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

