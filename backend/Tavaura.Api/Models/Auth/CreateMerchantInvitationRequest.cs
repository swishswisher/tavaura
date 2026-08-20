namespace Tavaura.Api.Models.Auth;

public class CreateMerchantInvitationRequest
{
    public Guid TenantId { get; set; }

    public string Email { get; set; } = string.Empty;

    public int ExpiresInHours { get; set; } = 24;
}
