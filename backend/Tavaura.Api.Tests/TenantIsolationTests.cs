using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Tenancy;
using Xunit;

namespace Tavaura.Api.Tests;

public class TenantIsolationTests
{
    private static readonly Guid TenantA = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static readonly Guid TenantB = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");

    [Fact]
    public async Task TenantQueryFiltersExposeOnlyTheSelectedTenant()
    {
        var tenantContext = new TenantContext { TenantId = TenantA };
        await using var dbContext = CreateContext(tenantContext);
        await SeedTenantRowsAsync(dbContext);

        Assert.All(await dbContext.Garments.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.GarmentAssets.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.AssetVersions.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.IngestionJobs.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.RenderJobs.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.RenderResults.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));
        Assert.All(await dbContext.UserLooks.ToListAsync(), row => Assert.Equal(TenantA, row.TenantId));

        tenantContext.TenantId = TenantB;
        dbContext.ChangeTracker.Clear();

        Assert.All(await dbContext.Garments.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.GarmentAssets.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.AssetVersions.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.IngestionJobs.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.RenderJobs.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.RenderResults.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
        Assert.All(await dbContext.UserLooks.ToListAsync(), row => Assert.Equal(TenantB, row.TenantId));
    }

    [Fact]
    public async Task TenantQueryFiltersDefaultDenyWhenContextIsMissing()
    {
        var tenantContext = new TenantContext { TenantId = TenantA };
        await using var dbContext = CreateContext(tenantContext);
        await SeedTenantRowsAsync(dbContext);

        tenantContext.TenantId = null;
        dbContext.ChangeTracker.Clear();

        Assert.Empty(await dbContext.Garments.ToListAsync());
        Assert.Empty(await dbContext.GarmentAssets.ToListAsync());
        Assert.Empty(await dbContext.AssetVersions.ToListAsync());
        Assert.Empty(await dbContext.IngestionJobs.ToListAsync());
        Assert.Empty(await dbContext.RenderJobs.ToListAsync());
        Assert.Empty(await dbContext.RenderResults.ToListAsync());
        Assert.Empty(await dbContext.UserLooks.ToListAsync());
    }

    [Theory]
    [InlineData(typeof(GarmentAsset), "TenantId", "GarmentId")]
    [InlineData(typeof(AssetVersion), "TenantId", "GarmentAssetId")]
    [InlineData(typeof(RenderJob), "TenantId", "GarmentAssetId")]
    [InlineData(typeof(RenderJob), "TenantId", "AssetVersionId")]
    [InlineData(typeof(RenderJob), "TenantId", "AvatarId")]
    [InlineData(typeof(RenderResult), "TenantId", "RenderJobId")]
    public void PipelineRelationshipsCarryTenantInTheirForeignKey(
        Type entityType,
        params string[] expectedProperties)
    {
        var tenantContext = new TenantContext { TenantId = TenantA };
        using var dbContext = CreateContext(tenantContext);
        var entity = dbContext.Model.FindEntityType(entityType);

        Assert.NotNull(entity);
        Assert.Contains(
            entity.GetForeignKeys(),
            foreignKey => foreignKey.Properties
                .Select(property => property.Name)
                .SequenceEqual(expectedProperties));
    }

    private static TavauraDbContext CreateContext(TenantContext tenantContext)
    {
        var options = new DbContextOptionsBuilder<TavauraDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new TavauraDbContext(options, tenantContext);
    }

    private static async Task SeedTenantRowsAsync(TavauraDbContext dbContext)
    {
        foreach (var tenantId in new[] { TenantA, TenantB })
        {
            var garmentId = Guid.NewGuid();
            var garmentAssetId = Guid.NewGuid();
            var assetVersionId = Guid.NewGuid();
            var renderJobId = Guid.NewGuid();
            dbContext.Garments.Add(new Garment
            {
                Id = garmentId,
                TenantId = tenantId,
                ExternalProductId = $"product-{tenantId}",
                Name = "Test garment"
            });
            dbContext.GarmentAssets.Add(new GarmentAsset
            {
                Id = garmentAssetId,
                TenantId = tenantId,
                GarmentId = garmentId,
                AssetType = "front"
            });
            dbContext.AssetVersions.Add(new AssetVersion
            {
                Id = assetVersionId,
                TenantId = tenantId,
                GarmentAssetId = garmentAssetId,
                VersionNumber = 1
            });
            dbContext.IngestionJobs.Add(new IngestionJob
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                ExternalProductId = $"product-{tenantId}",
                Status = "pending"
            });
            dbContext.RenderJobs.Add(new RenderJob
            {
                Id = renderJobId,
                TenantId = tenantId,
                AvatarId = Guid.NewGuid(),
                GarmentAssetId = garmentAssetId,
                AssetVersionId = assetVersionId,
                Status = "pending"
            });
            dbContext.RenderResults.Add(new RenderResult
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                RenderJobId = renderJobId
            });
            dbContext.UserLooks.Add(new UserLook
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                UserId = Guid.NewGuid(),
                Mode = "test"
            });
        }

        await dbContext.SaveChangesAsync();
        dbContext.ChangeTracker.Clear();
    }
}
