using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Contact;
using Tavaura.Api.Models.Admin;
using Tavaura.Api.Models.Auth;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

[Collection(PostgresCollection.Name)]
public sealed class SecurityLifecycleIntegrationTests
{
    private readonly PostgresFixture _fixture;

    public SecurityLifecycleIntegrationTests(PostgresFixture fixture)
    {
        _fixture = fixture;
    }

    [PostgresFact]
    public async Task FiveFailedLoginsLockTheAccountEvenWithTheCorrectPassword()
    {
        var user = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        await using var factory = _fixture.CreateFactory(authPermitLimit: 100);
        using var client = factory.CreateSecureClient();

        for (var attempt = 0; attempt < 5; attempt += 1)
        {
            var response = await client.PostAsJsonAsync(
                "/api/auth/login",
                new LoginRequest { Email = user.Email, Password = "wrong-password-value" });
            Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
        }

        var lockedResponse = await client.PostAsJsonAsync(
            "/api/auth/login",
            new LoginRequest { Email = user.Email, Password = TestWorkspace.Password });
        Assert.Equal(HttpStatusCode.Unauthorized, lockedResponse.StatusCode);

        await using var dbContext = _fixture.CreateAdminDbContext();
        var stored = await dbContext.Users.SingleAsync(candidate => candidate.Id == user.Id);
        Assert.True(stored.LockoutEnd > DateTime.UtcNow);
        Assert.Equal(0, stored.FailedLoginCount);
        Assert.Equal(1, stored.TokenVersion);
    }

    [PostgresFact]
    public async Task AuthenticationAndPublicWritePoliciesReturn429AtTheirConfiguredLimits()
    {
        await using var authFactory = _fixture.CreateFactory(authPermitLimit: 5);
        using var authClient = authFactory.CreateSecureClient();
        for (var requestNumber = 1; requestNumber <= 6; requestNumber += 1)
        {
            var response = await authClient.PostAsJsonAsync(
                "/api/auth/login",
                new LoginRequest());
            Assert.Equal(
                requestNumber <= 5 ? HttpStatusCode.BadRequest : HttpStatusCode.TooManyRequests,
                response.StatusCode);
        }

        await using var publicFactory = _fixture.CreateFactory(publicWritePermitLimit: 10);
        using var publicClient = publicFactory.CreateSecureClient();
        for (var requestNumber = 1; requestNumber <= 11; requestNumber += 1)
        {
            var response = await publicClient.PostAsJsonAsync(
                "/api/contact",
                new ContactRequestDto
                {
                    Email = "rate-limit@example.com",
                    Message = "Phase 1 public write rate-limit verification."
                });
            Assert.Equal(
                requestNumber <= 10 ? HttpStatusCode.Accepted : HttpStatusCode.TooManyRequests,
                response.StatusCode);
        }
    }

    [PostgresFact]
    public async Task SessionRevocationRejectsOldTokenAndReturnsUsableReplacement()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("token-revocation");
        using var client = _fixture.Factory.CreateSecureClient();
        var loginResponse = await client.PostAsJsonAsync(
            "/api/auth/login",
            new LoginRequest
            {
                Email = workspace.User.Email,
                Password = TestWorkspace.Password
            });
        Assert.Equal(HttpStatusCode.OK, loginResponse.StatusCode);
        var initialLogin = (await loginResponse.Content.ReadFromJsonAsync<LoginResponse>())!;
        using var revokeRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "/api/admin/settings/sessions/sign-out-others");
        PostgresFixture.Authorize(revokeRequest, initialLogin.AccessToken);
        var revokeResponse = await client.SendAsync(revokeRequest);
        Assert.Equal(HttpStatusCode.OK, revokeResponse.StatusCode);
        var replacement = (await revokeResponse.Content.ReadFromJsonAsync<LoginResponse>())!;
        Assert.NotEqual(initialLogin.AccessToken, replacement.AccessToken);

        using var oldTokenRequest = new HttpRequestMessage(HttpMethod.Get, "/api/admin/settings");
        PostgresFixture.Authorize(oldTokenRequest, initialLogin.AccessToken);
        Assert.Equal(HttpStatusCode.Unauthorized, (await client.SendAsync(oldTokenRequest)).StatusCode);

        using var replacementRequest = new HttpRequestMessage(HttpMethod.Get, "/api/admin/settings");
        PostgresFixture.Authorize(replacementRequest, replacement.AccessToken);
        Assert.Equal(HttpStatusCode.OK, (await client.SendAsync(replacementRequest)).StatusCode);
    }

    [PostgresFact]
    public async Task ApiKeySecretIsReturnedOnceAndOnlyItsHashAndDescriptorAreStored()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("api-key");
        using var client = _fixture.Factory.CreateSecureClient();
        using var regenerateRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "/api/admin/settings/api-key/regenerate");
        PostgresFixture.Authorize(regenerateRequest, workspace.AccessToken);
        var regenerateResponse = await client.SendAsync(regenerateRequest);
        Assert.Equal(HttpStatusCode.OK, regenerateResponse.StatusCode);
        var generated = (await regenerateResponse.Content.ReadFromJsonAsync<ApiKeyRegenerationResponse>())!;
        Assert.StartsWith("tv_live_", generated.ApiKey, StringComparison.Ordinal);

        await using (var dbContext = _fixture.CreateAdminDbContext())
        {
            var stored = await dbContext.MerchantAdminSettings
                .IgnoreQueryFilters()
                .SingleAsync(settings => settings.TenantId == workspace.Tenant.Id);
            Assert.Equal(PostgresFixture.HashSecret(generated.ApiKey), stored.ApiKeyHash);
            Assert.DoesNotContain(generated.ApiKey, stored.ApiKeyHash, StringComparison.Ordinal);
            Assert.Equal(generated.ApiKey[..15], stored.ApiKeyPrefix);
            Assert.Equal(generated.ApiKey[^4..], stored.ApiKeyLastFour);
            Assert.Equal("storefront:session:create", stored.ApiKeyScopes);
        }

        using var getRequest = new HttpRequestMessage(HttpMethod.Get, "/api/admin/settings");
        PostgresFixture.Authorize(getRequest, workspace.AccessToken);
        var getResponse = await client.SendAsync(getRequest);
        Assert.Equal(HttpStatusCode.OK, getResponse.StatusCode);
        var responseJson = await getResponse.Content.ReadAsStringAsync();
        Assert.DoesNotContain(generated.ApiKey, responseJson, StringComparison.Ordinal);
        using var document = JsonDocument.Parse(responseJson);
        Assert.False(document.RootElement.TryGetProperty("apiKey", out _));
        Assert.False(document.RootElement.GetProperty("integration").TryGetProperty("apiKey", out _));
    }
}
