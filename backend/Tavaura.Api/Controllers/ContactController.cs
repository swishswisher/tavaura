using Microsoft.AspNetCore.Mvc;
using Tavaura.Api.Contact;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Microsoft.AspNetCore.Authorization.AllowAnonymous]
[Microsoft.AspNetCore.RateLimiting.EnableRateLimiting("public-write")]
[RequestSizeLimit(8 * 1024)]
public class ContactController : ControllerBase
{
    private readonly ILogger<ContactController> _logger;

    public ContactController(ILogger<ContactController> logger)
    {
        _logger = logger;
    }

    [HttpPost]
    public IActionResult Post([FromBody] ContactRequestDto request)
    {
        if (request == null)
        {
            return BadRequest(new ContactResponseDto
            {
                Accepted = false,
                Message = "Request body is required."
            });
        }

        if (string.IsNullOrWhiteSpace(request.Email) || request.Email.Length > 320)
        {
            return BadRequest(new ContactResponseDto
            {
                Accepted = false,
                Message = "Email is required."
            });
        }

        if (string.IsNullOrWhiteSpace(request.Message) || request.Message.Length > 5000)
        {
            return BadRequest(new ContactResponseDto
            {
                Accepted = false,
                Message = "Message is required."
            });
        }

        _logger.LogInformation(
            "Accepted contact request {RequestId} with context {Context}",
            HttpContext.TraceIdentifier,
            request.Context ?? "unspecified"
        );

        var response = new ContactResponseDto
        {
            Accepted = true,
            Message = "Contact request accepted."
        };

        return Accepted(response);
    }
}
