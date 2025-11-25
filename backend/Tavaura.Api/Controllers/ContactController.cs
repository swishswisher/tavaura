using Microsoft.AspNetCore.Mvc;
using Tavaura.Api.Contact;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
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

        if (string.IsNullOrWhiteSpace(request.Email))
        {
            return BadRequest(new ContactResponseDto
            {
                Accepted = false,
                Message = "Email is required."
            });
        }

        if (string.IsNullOrWhiteSpace(request.Message))
        {
            return BadRequest(new ContactResponseDto
            {
                Accepted = false,
                Message = "Message is required."
            });
        }

        _logger.LogInformation(
            "New contact request from {Email}. Name: {Name}, Company: {Company}, Context: {Context}, Message: {Message}",
            request.Email,
            request.Name ?? "(none)",
            request.CompanyOrBrand ?? "(none)",
            request.Context ?? "(none)",
            request.Message
        );

        var response = new ContactResponseDto
        {
            Accepted = true,
            Message = "Contact request accepted."
        };

        return Accepted(response);
    }
}
