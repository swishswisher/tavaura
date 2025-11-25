using Microsoft.AspNetCore.Mvc;
using Tavaura.Api.Models.Auth;

namespace Tavaura.Api.Controllers;

/// <summary>
/// Temporary authentication endpoints used during early development before real email/SSO auth is implemented.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new { status = "ok", area = "auth" });
    }

    [HttpPost("mock-login")]
    public IActionResult MockLogin([FromBody] LoginRequest request)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Email))
        {
            return BadRequest("Email is required.");
        }

        var response = new LoginResponse
        {
            AccessToken = $"mock-token-for-{request.Email}",
            Role = "user",
            TenantId = null
        };

        return Ok(response);
    }
}

