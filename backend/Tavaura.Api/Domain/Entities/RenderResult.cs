using System;

namespace Tavaura.Api.Domain.Entities;

public class RenderResult
{
    public Guid Id { get; set; }

    public Guid RenderJobId { get; set; }

    public string OutputImageUrl { get; set; } = string.Empty;

    public string PreviewImageUrl { get; set; } = string.Empty;

    public bool IsDeleted { get; set; }

    public DateTime? DeletedAt { get; set; }

    public DateTime CreatedAt { get; set; }
}
