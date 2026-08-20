namespace Tavaura.Api.Domain.Entities;

public class UserInvitation
{
    public Guid Id { get; set; }

    public string TokenHash { get; set; } = string.Empty;

    public string Email { get; set; } = string.Empty;

    public string NormalizedEmail { get; set; } = string.Empty;

    public string Role { get; set; } = string.Empty;

    public Guid TenantId { get; set; }

    public Guid CreatedByUserId { get; set; }

    public DateTime ExpiresAt { get; set; }

    public DateTime? AcceptedAt { get; set; }

    public DateTime CreatedAt { get; set; }
}
