namespace Tavaura.Api.Models.Auth;

public class AcceptInvitationRequest
{
    public string Token { get; set; } = string.Empty;

    public string Password { get; set; } = string.Empty;

    public string? DisplayName { get; set; }
}
