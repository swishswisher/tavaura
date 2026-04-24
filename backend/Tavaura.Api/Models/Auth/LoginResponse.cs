using System;

namespace Tavaura.Api.Models.Auth;

public class LoginResponse
{
    public Guid UserId { get; set; }

    public string Email { get; set; } = string.Empty;

    public string AccessToken { get; set; } = string.Empty;

    public string TokenType { get; set; } = "Bearer";

    public DateTime ExpiresAtUtc { get; set; }

    public string Role { get; set; } = string.Empty;

    public Guid? TenantId { get; set; }
}

