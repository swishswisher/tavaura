namespace Tavaura.Api.Auth;

public static class AuthRoles
{
    public const string PlatformAdmin = "platform_admin";
    public const string MerchantAdmin = "merchant_admin";
    public const string CustomerUser = "customer_user";

    public const string MerchantOrPlatform = MerchantAdmin + "," + PlatformAdmin;
    public const string CustomerMerchantOrPlatform = CustomerUser + "," + MerchantAdmin + "," + PlatformAdmin;
}
