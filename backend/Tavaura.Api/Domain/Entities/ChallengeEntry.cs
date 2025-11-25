using System;

namespace Tavaura.Api.Domain.Entities;

public class ChallengeEntry
{
    public Guid Id { get; set; }

    public Guid ChallengeId { get; set; }

    public Guid UserId { get; set; }

    public Guid? UserLookId { get; set; }

    public string SnapshotUrl { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }
}

