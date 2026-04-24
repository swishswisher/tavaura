namespace Tavaura.Api.Models.Auth;

public class RegisterPlatformAdminRequest
{
    public string Email { get; set; } = string.Empty;

    public string Password { get; set; } = string.Empty;

    public string? DisplayName { get; set; }

    public string BootstrapSecret { get; set; } = string.Empty;
}
