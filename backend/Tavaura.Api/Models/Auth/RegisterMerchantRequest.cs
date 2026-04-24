using System;

namespace Tavaura.Api.Models.Auth;

public class RegisterMerchantRequest
{
    public Guid TenantId { get; set; }

    public string Email { get; set; } = string.Empty;

    public string Password { get; set; } = string.Empty;

    public string? DisplayName { get; set; }
}
