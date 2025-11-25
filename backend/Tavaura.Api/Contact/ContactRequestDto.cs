namespace Tavaura.Api.Contact;

public class ContactRequestDto
{
    public string? Name { get; set; }
    public string Email { get; set; } = string.Empty;
    public string? CompanyOrBrand { get; set; }
    public string Message { get; set; } = string.Empty;
    public string? Context { get; set; }
}
