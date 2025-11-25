using System;

namespace Tavaura.Api.Models.Auth;

public class LoginResponse
{
    public string AccessToken { get; set; } = string.Empty;

    public string Role { get; set; } = string.Empty;

    public Guid? TenantId { get; set; }
}

