using System;

namespace Tavaura.Api.Domain.Entities;

public class UserLook
{
    public Guid Id { get; set; }

    public Guid UserId { get; set; }

    public Guid? AvatarId { get; set; }

    public Guid TenantId { get; set; }

    public string Mode { get; set; } = string.Empty;

    public string SnapshotUrl { get; set; } = string.Empty;

    public string? MetadataJson { get; set; }

    public DateTime CreatedAt { get; set; }
}

