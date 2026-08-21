using System.Net;
using System.Net.Http.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc.Controllers;
using Microsoft.AspNetCore.Routing;
using Microsoft.AspNetCore.Routing.Patterns;
using Microsoft.Extensions.DependencyInjection;
using Tavaura.Api.Models.Auth;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

[Collection(PostgresCollection.Name)]
public sealed partial class RouteAuthorizationIntegrationTests
{
    private readonly PostgresFixture _fixture;

    public RouteAuthorizationIntegrationTests(PostgresFixture fixture)
    {
        _fixture = fixture;
    }

    [PostgresFact]
    public async Task EveryPrivilegedControllerRouteRejectsAnonymousRequests()
    {
        using var client = _fixture.Factory.CreateSecureClient();
        var endpoints = ControllerEndpoints(_fixture.Factory.Services)
            .Where(endpoint => endpoint.Metadata.GetMetadata<IAllowAnonymous>() is null)
            .ToList();
        Assert.NotEmpty(endpoints);

        foreach (var endpoint in endpoints)
        {
            var methods = endpoint.Metadata.GetMetadata<IHttpMethodMetadata>()?.HttpMethods ?? ["GET"];
            foreach (var method in methods)
            {
                using var request = CreateAnonymousRequest(method, endpoint.RoutePattern);
                var response = await client.SendAsync(request);
                Assert.True(
                    response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden,
                    $"{method} {request.RequestUri} returned {(int)response.StatusCode} instead of 401/403.");
            }
        }
    }

    [PostgresFact]
    public void AnonymousControllerRouteInventoryIsExplicitAndMinimal()
    {
        using var client = _fixture.Factory.CreateSecureClient();
        var actual = ControllerEndpoints(_fixture.Factory.Services)
            .Where(endpoint => endpoint.Metadata.GetMetadata<IAllowAnonymous>() is not null)
            .SelectMany(endpoint =>
                (endpoint.Metadata.GetMetadata<IHttpMethodMetadata>()?.HttpMethods ?? ["GET"])
                .Select(method => $"{method.ToUpperInvariant()} {NormalizeRoute(endpoint.RoutePattern.RawText)}"))
            .OrderBy(value => value, StringComparer.Ordinal)
            .ToArray();
        var expected = new[]
        {
            "GET /api/auth/health",
            "GET /health",
            "POST /api/auth/login",
            "POST /api/auth/merchant-invitations/accept",
            "POST /api/auth/register-platform-admin",
            "POST /api/contact"
        };

        Assert.Equal(expected.OrderBy(value => value, StringComparer.Ordinal), actual);
    }

    [PostgresFact]
    public async Task DevelopmentBootstrapEndpointIsUnavailableInProduction()
    {
        using var client = _fixture.Factory.CreateSecureClient();
        var response = await client.PostAsJsonAsync(
            "/api/auth/register-platform-admin",
            new RegisterPlatformAdminRequest
            {
                Email = "should-not-exist@example.com",
                Password = TestWorkspace.Password,
                BootstrapSecret = "any-value"
            });

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    private static IReadOnlyList<RouteEndpoint> ControllerEndpoints(IServiceProvider services)
    {
        return services.GetServices<EndpointDataSource>()
            .SelectMany(source => source.Endpoints)
            .OfType<RouteEndpoint>()
            .Where(endpoint => endpoint.Metadata.GetMetadata<ControllerActionDescriptor>() is not null)
            .ToList();
    }

    private static HttpRequestMessage CreateAnonymousRequest(string method, RoutePattern pattern)
    {
        var route = ConcreteRoute().Replace(
            NormalizeRoute(pattern.RawText),
            Guid.Empty.ToString());
        var request = new HttpRequestMessage(new HttpMethod(method), route);
        if (method is "POST" or "PUT" or "PATCH")
        {
            request.Content = JsonContent.Create(new { });
        }

        return request;
    }

    private static string NormalizeRoute(string? route)
    {
        return "/" + (route ?? string.Empty).TrimStart('/').ToLowerInvariant();
    }

    [GeneratedRegex("\\{[^}]+\\}", RegexOptions.CultureInvariant)]
    private static partial Regex ConcreteRoute();
}
