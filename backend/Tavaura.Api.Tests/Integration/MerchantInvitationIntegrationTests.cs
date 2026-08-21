using System.Net;
using System.Net.Http.Json;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Auth;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

[Collection(PostgresCollection.Name)]
public sealed class MerchantInvitationIntegrationTests
{
    private readonly PostgresFixture _fixture;

    public MerchantInvitationIntegrationTests(PostgresFixture fixture)
    {
        _fixture = fixture;
    }

    [PostgresFact]
    public async Task OnlyPlatformAdministratorCanCreateMerchantWorkspacesAndInvitations()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("invitation-auth");
        var platform = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        using var client = _fixture.Factory.CreateSecureClient();
        var payload = new CreateMerchantInvitationRequest
        {
            TenantId = workspace.Tenant.Id,
            Email = $"invite-{Guid.NewGuid():N}@example.com",
            ExpiresInHours = 24
        };

        var anonymousResponse = await client.PostAsJsonAsync("/api/auth/merchant-invitations", payload);
        Assert.Equal(HttpStatusCode.Unauthorized, anonymousResponse.StatusCode);

        using var merchantRequest = new HttpRequestMessage(HttpMethod.Post, "/api/auth/merchant-invitations")
        {
            Content = JsonContent.Create(payload)
        };
        PostgresFixture.Authorize(merchantRequest, workspace.AccessToken);
        var merchantResponse = await client.SendAsync(merchantRequest);
        Assert.Equal(HttpStatusCode.Forbidden, merchantResponse.StatusCode);

        using var platformRequest = new HttpRequestMessage(HttpMethod.Post, "/api/auth/merchant-invitations")
        {
            Content = JsonContent.Create(payload)
        };
        PostgresFixture.Authorize(platformRequest, PostgresFixture.IssueToken(platform));
        var platformResponse = await client.SendAsync(platformRequest);
        Assert.Equal(HttpStatusCode.Created, platformResponse.StatusCode);

        var workspaceSlug = $"workspace-{Guid.NewGuid():N}";
        var workspacePayload = new CreateMerchantWorkspaceRequest
        {
            AccountName = "Authorized account",
            AccountSlug = workspaceSlug,
            StoreName = "Authorized store",
            StoreSlug = workspaceSlug,
            Platform = "shopify",
            Domain = $"{workspaceSlug}.example.com",
            MerchantAdminEmail = $"workspace-{Guid.NewGuid():N}@example.com",
            InvitationExpiresInHours = 24
        };
        using var unauthorizedWorkspaceRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "/api/auth/merchant-workspaces")
        {
            Content = JsonContent.Create(workspacePayload)
        };
        PostgresFixture.Authorize(unauthorizedWorkspaceRequest, workspace.AccessToken);
        Assert.Equal(
            HttpStatusCode.Forbidden,
            (await client.SendAsync(unauthorizedWorkspaceRequest)).StatusCode);

        using var authorizedWorkspaceRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "/api/auth/merchant-workspaces")
        {
            Content = JsonContent.Create(workspacePayload)
        };
        PostgresFixture.Authorize(authorizedWorkspaceRequest, PostgresFixture.IssueToken(platform));
        var workspaceResponse = await client.SendAsync(authorizedWorkspaceRequest);
        Assert.Equal(HttpStatusCode.Created, workspaceResponse.StatusCode);
        var createdWorkspace =
            (await workspaceResponse.Content.ReadFromJsonAsync<MerchantWorkspaceResponse>())!;
        await using var verification = _fixture.CreateAdminDbContext();
        Assert.True(await verification.Accounts.AnyAsync(account => account.Id == createdWorkspace.AccountId));
        Assert.True(await verification.Stores.AnyAsync(store =>
            store.Id == createdWorkspace.StoreId &&
            store.AccountId == createdWorkspace.AccountId &&
            store.TenantId == createdWorkspace.TenantId));
    }

    [PostgresFact]
    public async Task ExpiredInvitationIsRejectedWithoutCreatingAUser()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("invitation-expired");
        var platform = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        var token = $"expired-{Guid.NewGuid():N}";
        var email = $"expired-{Guid.NewGuid():N}@example.com";
        await using (var dbContext = _fixture.CreateAdminDbContext())
        {
            dbContext.UserInvitations.Add(new UserInvitation
            {
                Id = Guid.NewGuid(),
                TokenHash = PostgresFixture.HashSecret(token),
                Email = email,
                NormalizedEmail = email.ToUpperInvariant(),
                Role = AuthRoles.MerchantAdmin,
                TenantId = workspace.Tenant.Id,
                CreatedByUserId = platform.Id,
                ExpiresAt = DateTime.UtcNow.AddMinutes(-1),
                CreatedAt = DateTime.UtcNow.AddHours(-1)
            });
            await dbContext.SaveChangesAsync();
        }

        using var client = _fixture.Factory.CreateSecureClient();
        var response = await client.PostAsJsonAsync(
            "/api/auth/merchant-invitations/accept",
            new AcceptInvitationRequest
            {
                Token = token,
                Email = email,
                Password = TestWorkspace.Password
            });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        await using var verification = _fixture.CreateAdminDbContext();
        Assert.False(await verification.Users.AnyAsync(user => user.NormalizedEmail == email.ToUpperInvariant()));
    }

    [PostgresFact]
    public async Task InvitationEmailMustMatchAndMismatchDoesNotConsumeToken()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("invitation-email");
        var platform = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        var invitation = await CreateInvitationAsync(workspace, platform);
        using var client = _fixture.Factory.CreateSecureClient();

        var mismatch = await client.PostAsJsonAsync(
            "/api/auth/merchant-invitations/accept",
            new AcceptInvitationRequest
            {
                Token = invitation.Token,
                Email = $"wrong-{Guid.NewGuid():N}@example.com",
                Password = TestWorkspace.Password
            });
        Assert.Equal(HttpStatusCode.BadRequest, mismatch.StatusCode);

        var accepted = await client.PostAsJsonAsync(
            "/api/auth/merchant-invitations/accept",
            new AcceptInvitationRequest
            {
                Token = invitation.Token,
                Email = invitation.Email.ToUpperInvariant(),
                Password = TestWorkspace.Password
            });
        Assert.Equal(HttpStatusCode.Created, accepted.StatusCode);
        var login = (await accepted.Content.ReadFromJsonAsync<LoginResponse>())!;
        using var settingsRequest = new HttpRequestMessage(HttpMethod.Get, "/api/admin/settings");
        PostgresFixture.Authorize(settingsRequest, login.AccessToken);
        Assert.Equal(HttpStatusCode.OK, (await client.SendAsync(settingsRequest)).StatusCode);
    }

    [PostgresFact]
    public async Task ConcurrentReplayCreatesExactlyOneUserAndMembership()
    {
        var workspace = await _fixture.SeedWorkspaceAsync("invitation-replay");
        var platform = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        var invitation = await CreateInvitationAsync(workspace, platform);
        using var client = _fixture.Factory.CreateSecureClient();
        var payload = new AcceptInvitationRequest
        {
            Token = invitation.Token,
            Email = invitation.Email,
            Password = TestWorkspace.Password
        };

        var responses = await Task.WhenAll(
            client.PostAsJsonAsync("/api/auth/merchant-invitations/accept", payload),
            client.PostAsJsonAsync("/api/auth/merchant-invitations/accept", payload));

        Assert.Single(responses, response => response.StatusCode == HttpStatusCode.Created);
        Assert.Single(responses, response => response.StatusCode == HttpStatusCode.BadRequest);

        await using var dbContext = _fixture.CreateAdminDbContext();
        var user = await dbContext.Users.SingleAsync(
            candidate => candidate.NormalizedEmail == invitation.Email.ToUpperInvariant());
        Assert.Equal(workspace.Tenant.Id, user.TenantId);
        Assert.Equal(
            1,
            await dbContext.AccountUserMemberships.CountAsync(
                membership => membership.UserId == user.Id &&
                              membership.AccountId == workspace.Account.Id &&
                              membership.Status == "active"));
        Assert.NotNull((await dbContext.UserInvitations.SingleAsync(i => i.Id == invitation.Id)).AcceptedAt);
    }

    [PostgresFact]
    public async Task FailedAcceptanceRollsBackInvitationConsumption()
    {
        var platform = await _fixture.SeedPlatformAdministratorAsync(Guid.NewGuid().ToString("N"));
        var now = DateTime.UtcNow;
        var tenant = new Tenant
        {
            Id = Guid.NewGuid(),
            Name = "Unmapped invitation tenant",
            Platform = "shopify",
            Status = "active",
            Plan = "starter",
            CreatedAt = now,
            UpdatedAt = now
        };
        var token = $"rollback-{Guid.NewGuid():N}";
        var email = $"rollback-{Guid.NewGuid():N}@example.com";
        var invitation = new UserInvitation
        {
            Id = Guid.NewGuid(),
            TokenHash = PostgresFixture.HashSecret(token),
            Email = email,
            NormalizedEmail = email.ToUpperInvariant(),
            Role = AuthRoles.MerchantAdmin,
            TenantId = tenant.Id,
            CreatedByUserId = platform.Id,
            ExpiresAt = now.AddHours(1),
            CreatedAt = now
        };
        await using (var dbContext = _fixture.CreateAdminDbContext())
        {
            dbContext.AddRange(tenant, invitation);
            await dbContext.SaveChangesAsync();
        }

        using var client = _fixture.Factory.CreateSecureClient();
        var response = await client.PostAsJsonAsync(
            "/api/auth/merchant-invitations/accept",
            new AcceptInvitationRequest
            {
                Token = token,
                Email = email,
                Password = TestWorkspace.Password
            });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        await using var verification = _fixture.CreateAdminDbContext();
        Assert.Null((await verification.UserInvitations.SingleAsync(i => i.Id == invitation.Id)).AcceptedAt);
        Assert.False(await verification.Users.AnyAsync(user => user.NormalizedEmail == email.ToUpperInvariant()));
    }

    private async Task<MerchantInvitationResponse> CreateInvitationAsync(
        TestWorkspace workspace,
        User platform)
    {
        using var client = _fixture.Factory.CreateSecureClient();
        using var request = new HttpRequestMessage(HttpMethod.Post, "/api/auth/merchant-invitations")
        {
            Content = JsonContent.Create(new CreateMerchantInvitationRequest
            {
                TenantId = workspace.Tenant.Id,
                Email = $"invite-{Guid.NewGuid():N}@example.com",
                ExpiresInHours = 24
            })
        };
        PostgresFixture.Authorize(request, PostgresFixture.IssueToken(platform));
        var response = await client.SendAsync(request);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        return (await response.Content.ReadFromJsonAsync<MerchantInvitationResponse>())!;
    }
}
