using System;

namespace Tavaura.Api.Domain.Entities;

/// <summary>
/// Represents an individual account that can act on behalf of a tenant or as a global Tavaura administrator.
/// The Role field differentiates permissions and TenantId may be null for global admins.
/// </summary>
public class User
{
    public Guid Id { get; set; }

    public string Email { get; set; } = string.Empty;

    public string NormalizedEmail { get; set; } = string.Empty;

    public string? DisplayName { get; set; }

    public string PasswordHash { get; set; } = string.Empty;

    public string Role { get; set; } = string.Empty;

    public Guid? TenantId { get; set; }

    public int TokenVersion { get; set; }

    public int FailedLoginCount { get; set; }

    public DateTime? LockoutEnd { get; set; }

    public DateTime? LastLoginAt { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

