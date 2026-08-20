namespace Tavaura.Api.Models.Auth;

public class MerchantWorkspaceResponse
{
    public Guid AccountId { get; set; }

    public Guid StoreId { get; set; }

    public Guid TenantId { get; set; }

    public MerchantInvitationResponse Invitation { get; set; } = new();
}
