using Microsoft.EntityFrameworkCore;
using Npgsql;
using Tavaura.Api.Domain.Entities;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

[Collection(PostgresCollection.Name)]
public sealed class PostgresMigrationAndRlsIntegrationTests
{
    private const string PrePhase1Migration = "20260506153247_AddSoftDeleteForRenderResults";
    private readonly PostgresFixture _fixture;

    public PostgresMigrationAndRlsIntegrationTests(PostgresFixture fixture)
    {
        _fixture = fixture;
    }

    [PostgresFact]
    public async Task FreshMigrationChainProducesRequiredTenantSchema()
    {
        await using var connection = new NpgsqlConnection(_fixture.AdminConnectionString);
        await connection.OpenAsync();
        Assert.Equal(
            "20260820131648_RequireUserLookTenant",
            await ScalarAsync<string>(
                connection,
                """SELECT "MigrationId" FROM "__EFMigrationsHistory" ORDER BY "MigrationId" DESC LIMIT 1"""));

        await using var columns = connection.CreateCommand();
        columns.CommandText =
            """
            SELECT count(*)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('AssetVersions', 'Avatars', 'RenderResults', 'UserLooks')
              AND column_name = 'TenantId'
              AND is_nullable = 'NO'
            """;
        Assert.Equal(4L, (long)(await columns.ExecuteScalarAsync())!);

        await using var role = connection.CreateCommand();
        role.CommandText =
            """
            SELECT NOT rolsuper AND NOT rolbypassrls
            FROM pg_roles
            WHERE rolname = 'tavaura_phase1_app'
            """;
        Assert.True((bool)(await role.ExecuteScalarAsync())!);
    }

    [PostgresFact]
    public async Task RuntimeRoleEnforcesTenantDefaultDenyPlatformWorkerAndCompositeBoundaries()
    {
        var tenantA = await _fixture.SeedWorkspaceAsync("rls-a");
        var tenantB = await _fixture.SeedWorkspaceAsync("rls-b");
        var garmentA = await SeedGarmentAsync(tenantA, "rls-product-a");
        var garmentB = await SeedGarmentAsync(tenantB, "rls-product-b");
        await using var connection = new NpgsqlConnection(_fixture.AppConnectionString);
        await connection.OpenAsync();

        await SetSecurityContextAsync(connection, string.Empty, isPlatform: false, isWorker: false);
        Assert.Equal(0L, await CountGarmentsAsync(connection, garmentA.Id, garmentB.Id));

        await SetSecurityContextAsync(connection, tenantA.Tenant.Id.ToString(), false, false);
        Assert.Equal(1L, await CountGarmentsAsync(connection, garmentA.Id, garmentB.Id));
        Assert.Equal(garmentA.Id, await VisibleGarmentIdAsync(connection, garmentA.Id, garmentB.Id));

        await SetSecurityContextAsync(connection, tenantB.Tenant.Id.ToString(), false, false);
        Assert.Equal(1L, await CountGarmentsAsync(connection, garmentA.Id, garmentB.Id));
        Assert.Equal(garmentB.Id, await VisibleGarmentIdAsync(connection, garmentA.Id, garmentB.Id));

        await SetSecurityContextAsync(connection, string.Empty, isPlatform: true, isWorker: false);
        Assert.Equal(2L, await CountGarmentsAsync(connection, garmentA.Id, garmentB.Id));

        await SetSecurityContextAsync(connection, string.Empty, isPlatform: false, isWorker: true);
        Assert.Equal(2L, await CountGarmentsAsync(connection, garmentA.Id, garmentB.Id));

        await SetSecurityContextAsync(connection, tenantA.Tenant.Id.ToString(), false, false);
        var rlsViolation = await Assert.ThrowsAsync<PostgresException>(async () =>
        {
            await using var command = connection.CreateCommand();
            command.CommandText =
                """
                INSERT INTO "Garments"
                    ("Id", "TenantId", "ExternalProductId", "Name", "Category", "Layer",
                     "SourceImageUrl", "IsActive", "IsDeleted", "CreatedAt", "UpdatedAt")
                VALUES
                    (@id, @tenant, @external, 'Blocked', 'top', 'top',
                     'https://example.com/blocked.png', true, false, now(), now())
                """;
            command.Parameters.AddWithValue("id", Guid.NewGuid());
            command.Parameters.AddWithValue("tenant", tenantB.Tenant.Id);
            command.Parameters.AddWithValue("external", $"blocked-{Guid.NewGuid():N}");
            await command.ExecuteNonQueryAsync();
        });
        Assert.Equal(PostgresErrorCodes.InsufficientPrivilege, rlsViolation.SqlState);

        var foreignKeyViolation = await Assert.ThrowsAsync<PostgresException>(async () =>
        {
            await using var command = connection.CreateCommand();
            command.CommandText =
                """
                INSERT INTO "GarmentAssets"
                    ("Id", "TenantId", "GarmentId", "AssetType", "SourceImageUrl",
                     "ConfidenceScore", "CreatedAt")
                VALUES
                    (@id, @tenant, @garment, 'front', 'https://example.com/cross.png', 1, now())
                """;
            command.Parameters.AddWithValue("id", Guid.NewGuid());
            command.Parameters.AddWithValue("tenant", tenantA.Tenant.Id);
            command.Parameters.AddWithValue("garment", garmentB.Id);
            await command.ExecuteNonQueryAsync();
        });
        Assert.Equal(PostgresErrorCodes.ForeignKeyViolation, foreignKeyViolation.SqlState);
    }

    [PostgresFact]
    public async Task RepresentativeLegacyDatabaseUpgradesWithoutLosingOwnershipOrSecrets()
    {
        var databaseName = $"tavaura_legacy_{Guid.NewGuid():N}";
        var serverBuilder = new NpgsqlConnectionStringBuilder(_fixture.AdminConnectionString)
        {
            Database = "postgres",
            Pooling = false
        };
        var legacyBuilder = new NpgsqlConnectionStringBuilder(_fixture.AdminConnectionString)
        {
            Database = databaseName,
            Pooling = false
        };

        await ExecuteAsync(serverBuilder.ConnectionString, $"CREATE DATABASE \"{databaseName}\"");
        try
        {
            await PostgresFixture.ApplyMigrationsAsync(legacyBuilder.ConnectionString, PrePhase1Migration);
            var seedSql = await File.ReadAllTextAsync(
                Path.Combine(AppContext.BaseDirectory, "TestData", "legacy-upgrade-seed.sql"));
            await ExecuteAsync(legacyBuilder.ConnectionString, seedSql);
            await PostgresFixture.ApplyMigrationsAsync(legacyBuilder.ConnectionString);

            await using var connection = new NpgsqlConnection(legacyBuilder.ConnectionString);
            await connection.OpenAsync();
            Assert.Equal(
                "LEGACY.ADMIN@EXAMPLE.COM",
                await ScalarAsync<string>(
                    connection,
                    """SELECT "NormalizedEmail" FROM "Users" WHERE "Id" = 'c1000000-0000-0000-0000-000000000001'"""));
            foreach (var (table, id) in new[]
                     {
                         ("Stores", "c3000000-0000-0000-0000-000000000001"),
                         ("AssetVersions", "c6000000-0000-0000-0000-000000000001"),
                         ("Avatars", "c7000000-0000-0000-0000-000000000001"),
                         ("RenderResults", "c9000000-0000-0000-0000-000000000001"),
                         ("UserLooks", "cb000000-0000-0000-0000-000000000001")
                     })
            {
                Assert.Equal(
                    Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    await ScalarAsync<Guid>(
                        connection,
                        $"SELECT \"TenantId\" FROM \"{table}\" WHERE \"Id\" = '{id}'"));
            }

            Assert.Equal(
                1L,
                await ScalarAsync<long>(
                    connection,
                    """
                    SELECT count(*) FROM "AccountUserMemberships"
                    WHERE "AccountId" = 'c2000000-0000-0000-0000-000000000001'
                      AND "UserId" = 'c1000000-0000-0000-0000-000000000001'
                      AND "Status" = 'active'
                    """));
            Assert.Equal(
                0L,
                await ScalarAsync<long>(
                    connection,
                    """
                    SELECT count(*) FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'MerchantAdminSettings'
                      AND column_name = 'ApiKey'
                    """));
        }
        finally
        {
            NpgsqlConnection.ClearAllPools();
            await ExecuteAsync(
                serverBuilder.ConnectionString,
                $"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{databaseName}' AND pid <> pg_backend_pid();
                """);
            await ExecuteAsync(
                serverBuilder.ConnectionString,
                $"DROP DATABASE IF EXISTS \"{databaseName}\"");
        }
    }

    private async Task<Garment> SeedGarmentAsync(TestWorkspace workspace, string externalProductId)
    {
        var now = DateTime.UtcNow;
        var garment = new Garment
        {
            Id = Guid.NewGuid(),
            TenantId = workspace.Tenant.Id,
            ExternalProductId = $"{externalProductId}-{Guid.NewGuid():N}",
            Name = externalProductId,
            Category = "top",
            Layer = "top",
            SourceImageUrl = "https://example.com/source.png",
            IsActive = true,
            CreatedAt = now,
            UpdatedAt = now
        };
        await using var dbContext = _fixture.CreateAdminDbContext(workspace.Tenant.Id);
        dbContext.Garments.Add(garment);
        await dbContext.SaveChangesAsync();
        return garment;
    }

    private static async Task SetSecurityContextAsync(
        NpgsqlConnection connection,
        string tenantId,
        bool isPlatform,
        bool isWorker)
    {
        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT set_config('app.tenant_id', @tenant, false),
                   set_config('app.is_platform', @platform, false),
                   set_config('app.is_worker', @worker, false)
            """;
        command.Parameters.AddWithValue("tenant", tenantId);
        command.Parameters.AddWithValue("platform", isPlatform ? "true" : "false");
        command.Parameters.AddWithValue("worker", isWorker ? "true" : "false");
        await command.ExecuteNonQueryAsync();
    }

    private static async Task<long> CountGarmentsAsync(
        NpgsqlConnection connection,
        Guid garmentA,
        Guid garmentB)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = """SELECT count(*) FROM "Garments" WHERE "Id" IN (@a, @b)""";
        command.Parameters.AddWithValue("a", garmentA);
        command.Parameters.AddWithValue("b", garmentB);
        return (long)(await command.ExecuteScalarAsync())!;
    }

    private static async Task<Guid> VisibleGarmentIdAsync(
        NpgsqlConnection connection,
        Guid garmentA,
        Guid garmentB)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = """SELECT "Id" FROM "Garments" WHERE "Id" IN (@a, @b)""";
        command.Parameters.AddWithValue("a", garmentA);
        command.Parameters.AddWithValue("b", garmentB);
        return (Guid)(await command.ExecuteScalarAsync())!;
    }

    private static async Task<T> ScalarAsync<T>(NpgsqlConnection connection, string sql)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = sql;
        return (T)(await command.ExecuteScalarAsync())!;
    }

    private static async Task ExecuteAsync(string connectionString, string sql)
    {
        await using var connection = new NpgsqlConnection(connectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = sql;
        await command.ExecuteNonQueryAsync();
    }
}
