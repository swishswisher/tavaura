using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;

namespace Tavaura.Api.Tests.Integration;

public sealed class TavauraApiFactory : WebApplicationFactory<Program>
{
    public const string JwtIssuer = "Tavaura.Api.IntegrationTests";
    public const string JwtAudience = "Tavaura.Api.IntegrationClients";
    public const string JwtSigningKey =
        "integration-test-only-signing-key-at-least-thirty-two-bytes-2026";

    private readonly string _connectionString;
    private readonly int _authPermitLimit;
    private readonly int _publicWritePermitLimit;

    public TavauraApiFactory(
        string connectionString,
        int authPermitLimit = 100,
        int publicWritePermitLimit = 100)
    {
        _connectionString = connectionString;
        _authPermitLimit = authPermitLimit;
        _publicWritePermitLimit = publicWritePermitLimit;
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Production");
        builder.UseSetting("ConnectionStrings:DefaultConnection", _connectionString);
        builder.UseSetting("Jwt:Issuer", JwtIssuer);
        builder.UseSetting("Jwt:Audience", JwtAudience);
        builder.UseSetting("Jwt:SigningKey", JwtSigningKey);
        builder.UseSetting("Jwt:ExpiresMinutes", "30");
        builder.UseSetting("Cors:AllowedOrigins:0", "https://merchant.example");
        builder.UseSetting("RateLimiting:AuthPermitLimit", _authPermitLimit.ToString());
        builder.UseSetting("RateLimiting:AuthWindowSeconds", "60");
        builder.UseSetting("RateLimiting:PublicWritePermitLimit", _publicWritePermitLimit.ToString());
        builder.UseSetting("RateLimiting:PublicWriteWindowSeconds", "60");
        builder.ConfigureAppConfiguration((_, configuration) =>
        {
            configuration.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ConnectionStrings:DefaultConnection"] = _connectionString,
                ["Jwt:Issuer"] = JwtIssuer,
                ["Jwt:Audience"] = JwtAudience,
                ["Jwt:SigningKey"] = JwtSigningKey,
                ["Jwt:ExpiresMinutes"] = "30",
                ["Cors:AllowedOrigins:0"] = "https://merchant.example",
                ["RateLimiting:AuthPermitLimit"] = _authPermitLimit.ToString(),
                ["RateLimiting:AuthWindowSeconds"] = "60",
                ["RateLimiting:PublicWritePermitLimit"] = _publicWritePermitLimit.ToString(),
                ["RateLimiting:PublicWriteWindowSeconds"] = "60"
            });
        });
    }

    public HttpClient CreateSecureClient()
    {
        return CreateClient(new WebApplicationFactoryClientOptions
        {
            AllowAutoRedirect = false,
            BaseAddress = new Uri("https://localhost")
        });
    }
}
