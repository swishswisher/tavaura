using System;

namespace Tavaura.Api.Domain.Entities;

/// <summary>
/// Represents an individual account that can act on behalf of a tenant or as a global Tavaura administrator.
/// The Role field differentiates permissions (e.g., user, merchant_admin, tavaura_admin) and TenantId may be null for global admins.
/// </summary>
public class User
{
    public Guid Id { get; set; }

    public string Email { get; set; } = string.Empty;

    public string? DisplayName { get; set; }

    public string Role { get; set; } = string.Empty;

    public Guid? TenantId { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}

