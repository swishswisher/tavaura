using System;

namespace Tavaura.Api.Domain.Entities;

public class MerchantAdminSettings
{
    public Guid Id { get; set; }

    public Guid TenantId { get; set; }

    public string SupportEmail { get; set; } = string.Empty;

    public string WebsiteUrl { get; set; } = string.Empty;

    public string? LogoUrl { get; set; }

    public string ApiKeyHash { get; set; } = string.Empty;

    public string ApiKeyPrefix { get; set; } = string.Empty;

    public string ApiKeyLastFour { get; set; } = string.Empty;

    public string ApiKeyScopes { get; set; } = string.Empty;

    public DateTime? ApiKeyCreatedAt { get; set; }

    public string WebhookUrl { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}
