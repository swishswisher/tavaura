using Microsoft.AspNetCore.Mvc;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("health")]
[Microsoft.AspNetCore.Authorization.AllowAnonymous]
public class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        var payload = new { status = "ok", service = "Tavaura.Api" };
        return Ok(payload);
    }
}

