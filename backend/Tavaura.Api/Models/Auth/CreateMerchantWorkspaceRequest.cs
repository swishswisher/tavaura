namespace Tavaura.Api.Models.Auth;

public class CreateMerchantWorkspaceRequest
{
    public string AccountName { get; set; } = string.Empty;

    public string AccountSlug { get; set; } = string.Empty;

    public string StoreName { get; set; } = string.Empty;

    public string StoreSlug { get; set; } = string.Empty;

    public string Platform { get; set; } = string.Empty;

    public string? Domain { get; set; }

    public string Plan { get; set; } = "starter";

    public string MerchantAdminEmail { get; set; } = string.Empty;

    public int InvitationExpiresInHours { get; set; } = 24;
}
