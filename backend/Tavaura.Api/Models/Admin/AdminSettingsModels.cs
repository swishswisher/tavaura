namespace Tavaura.Api.Models.Admin;

public class AdminSettingsResponse
{
    public AdminBrandProfileResponse BrandProfile { get; set; } = new();

    public AdminIntegrationSettingsResponse Integration { get; set; } = new();

    public AdminUsagePlanResponse Usage { get; set; } = new();
}

public class AdminBrandProfileResponse
{
    public string BrandName { get; set; } = string.Empty;

    public string SupportEmail { get; set; } = string.Empty;

    public string WebsiteUrl { get; set; } = string.Empty;

    public string? LogoUrl { get; set; }
}

public class AdminIntegrationSettingsResponse
{
    public string ApiKeyPrefix { get; set; } = string.Empty;

    public string ApiKeyLastFour { get; set; } = string.Empty;

    public string ApiKeyScopes { get; set; } = string.Empty;

    public DateTime? ApiKeyCreatedAt { get; set; }

    public string WebhookUrl { get; set; } = string.Empty;
}

public class ApiKeyRegenerationResponse
{
    public string ApiKey { get; set; } = string.Empty;

    public AdminSettingsResponse Settings { get; set; } = new();
}

public class AdminUsagePlanResponse
{
    public int GarmentsProcessedThisMonth { get; set; }

    public int RendersThisMonth { get; set; }

    public string CurrentPlan { get; set; } = string.Empty;

    public int UsageRemaining { get; set; }
}

public class UpdateAdminBrandSettingsRequest
{
    public string BrandName { get; set; } = string.Empty;

    public string SupportEmail { get; set; } = string.Empty;

    public string WebsiteUrl { get; set; } = string.Empty;
}

public class UpdateAdminWebhookRequest
{
    public string WebhookUrl { get; set; } = string.Empty;
}

public class ChangeAdminPasswordRequest
{
    public string CurrentPassword { get; set; } = string.Empty;

    public string NewPassword { get; set; } = string.Empty;
}

public class WorkspaceDeletionRequestResponse
{
    public string Message { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;
}
