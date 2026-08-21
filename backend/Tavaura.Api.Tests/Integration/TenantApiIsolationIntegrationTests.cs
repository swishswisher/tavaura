using System.Net;
using System.Net.Http.Json;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Admin;
using Tavaura.Api.Models.Garments;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

[Collection(PostgresCollection.Name)]
public sealed class TenantApiIsolationIntegrationTests
{
    private readonly PostgresFixture _fixture;

    public TenantApiIsolationIntegrationTests(PostgresFixture fixture)
    {
        _fixture = fixture;
    }

    [PostgresFact]
    public async Task TenantAListDetailCreateUpdateAndDeleteCannotAffectTenantB()
    {
        var tenantA = await _fixture.SeedWorkspaceAsync("api-a");
        var tenantB = await _fixture.SeedWorkspaceAsync("api-b");
        var garmentB = await SeedGarmentAsync(tenantB, "tenant-b-product");
        using var client = _fixture.Factory.CreateSecureClient();

        var createPayload = new CreateGarmentRequest
        {
            ExternalProductId = $"tenant-a-{Guid.NewGuid():N}",
            Name = "Tenant A T-shirt",
            Category = "top",
            Layer = "top",
            SourceImageUrl = "https://images.example.com/tenant-a.png"
        };
        using var createRequest = new HttpRequestMessage(HttpMethod.Post, "/api/garments")
        {
            Content = JsonContent.Create(createPayload)
        };
        PostgresFixture.Authorize(createRequest, tenantA.AccessToken);
        var createResponse = await client.SendAsync(createRequest);
        Assert.Equal(HttpStatusCode.Created, createResponse.StatusCode);
        var garmentA = (await createResponse.Content.ReadFromJsonAsync<GarmentResponse>())!;
        Assert.Equal(tenantA.Tenant.Id, garmentA.TenantId);

        using var listRequest = new HttpRequestMessage(HttpMethod.Get, "/api/garments");
        PostgresFixture.Authorize(listRequest, tenantA.AccessToken);
        var listResponse = await client.SendAsync(listRequest);
        Assert.Equal(HttpStatusCode.OK, listResponse.StatusCode);
        var listed = (await listResponse.Content.ReadFromJsonAsync<List<GarmentResponse>>())!;
        Assert.Contains(listed, garment => garment.Id == garmentA.Id);
        Assert.DoesNotContain(listed, garment => garment.Id == garmentB.Id);
        Assert.All(listed, garment => Assert.Equal(tenantA.Tenant.Id, garment.TenantId));

        using var foreignDetailRequest = new HttpRequestMessage(
            HttpMethod.Get,
            $"/api/garments/{garmentB.Id}");
        PostgresFixture.Authorize(foreignDetailRequest, tenantA.AccessToken);
        var foreignDetailResponse = await client.SendAsync(foreignDetailRequest);
        Assert.Equal(HttpStatusCode.NotFound, foreignDetailResponse.StatusCode);

        using var foreignDeleteRequest = new HttpRequestMessage(
            HttpMethod.Delete,
            $"/api/garments/{garmentB.Id}");
        PostgresFixture.Authorize(foreignDeleteRequest, tenantA.AccessToken);
        var foreignDeleteResponse = await client.SendAsync(foreignDeleteRequest);
        Assert.Equal(HttpStatusCode.NotFound, foreignDeleteResponse.StatusCode);

        using var updateRequest = new HttpRequestMessage(HttpMethod.Patch, "/api/admin/settings/brand")
        {
            Content = JsonContent.Create(new UpdateAdminBrandSettingsRequest
            {
                BrandName = "Tenant A Updated",
                SupportEmail = "support-a@example.com",
                WebsiteUrl = "https://tenant-a.example.com"
            })
        };
        PostgresFixture.Authorize(updateRequest, tenantA.AccessToken);
        updateRequest.Headers.Add("X-Tavaura-Tenant", tenantB.Tenant.Id.ToString());
        var updateResponse = await client.SendAsync(updateRequest);
        Assert.Equal(HttpStatusCode.OK, updateResponse.StatusCode);

        using var ownDeleteRequest = new HttpRequestMessage(
            HttpMethod.Delete,
            $"/api/garments/{garmentA.Id}");
        PostgresFixture.Authorize(ownDeleteRequest, tenantA.AccessToken);
        var ownDeleteResponse = await client.SendAsync(ownDeleteRequest);
        Assert.Equal(HttpStatusCode.NoContent, ownDeleteResponse.StatusCode);

        await using var verification = _fixture.CreateAdminDbContext();
        Assert.Equal(
            "Tenant A Updated",
            (await verification.Tenants.SingleAsync(tenant => tenant.Id == tenantA.Tenant.Id)).Name);
        Assert.Equal(
            tenantB.Tenant.Name,
            (await verification.Tenants.SingleAsync(tenant => tenant.Id == tenantB.Tenant.Id)).Name);
        Assert.True(
            (await verification.Garments
                .IgnoreQueryFilters()
                .SingleAsync(garment => garment.Id == garmentA.Id)).IsDeleted);
        Assert.False(
            (await verification.Garments
                .IgnoreQueryFilters()
                .SingleAsync(garment => garment.Id == garmentB.Id)).IsDeleted);
    }

    private async Task<Garment> SeedGarmentAsync(TestWorkspace workspace, string externalProductId)
    {
        var now = DateTime.UtcNow;
        var garment = new Garment
        {
            Id = Guid.NewGuid(),
            TenantId = workspace.Tenant.Id,
            ExternalProductId = $"{externalProductId}-{Guid.NewGuid():N}",
            Name = "Tenant B T-shirt",
            Category = "top",
            Layer = "top",
            SourceImageUrl = "https://images.example.com/tenant-b.png",
            IsActive = true,
            CreatedAt = now,
            UpdatedAt = now
        };
        await using var dbContext = _fixture.CreateAdminDbContext(workspace.Tenant.Id);
        dbContext.Garments.Add(garment);
        await dbContext.SaveChangesAsync();
        return garment;
    }
}
