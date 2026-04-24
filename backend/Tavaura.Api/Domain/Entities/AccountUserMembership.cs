using System;

namespace Tavaura.Api.Domain.Entities;

public class AccountUserMembership
{
    public Guid Id { get; set; }

    public Guid AccountId { get; set; }

    public Guid UserId { get; set; }

    public string Role { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }
}

