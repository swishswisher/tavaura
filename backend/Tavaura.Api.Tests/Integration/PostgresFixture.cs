using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.Extensions.Options;
using Npgsql;
using Tavaura.Api.Auth;
using Tavaura.Api.Configuration;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Tenancy;
using Xunit;

namespace Tavaura.Api.Tests.Integration;

public sealed class PostgresFixture : IAsyncLifetime
{
    public const string AdminConnectionEnvironmentVariable = "TAVAURA_TEST_ADMIN_CONNECTION";
    private const string RuntimeRole = "tavaura_phase1_app";
    private const string RuntimePassword = "phase1-test-app-password";

    private readonly string? _configuredAdminConnection =
        Environment.GetEnvironmentVariable(AdminConnectionEnvironmentVariable);

    public string AdminConnectionString => _configuredAdminConnection ??
        throw new InvalidOperationException($"{AdminConnectionEnvironmentVariable} is not configured.");

    public string AppConnectionString { get; private set; } = string.Empty;

    public TavauraApiFactory Factory { get; private set; } = null!;

    public bool IsEnabled => !string.IsNullOrWhiteSpace(_configuredAdminConnection);

    public async Task InitializeAsync()
    {
        if (!IsEnabled)
        {
            if (string.Equals(Environment.GetEnvironmentVariable("CI"), "true", StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    $"CI must provide {AdminConnectionEnvironmentVariable}; PostgreSQL tests may not be skipped in CI.");
            }

            return;
        }

        await ResetSchemaAsync();
        await ApplyMigrationsAsync(AdminConnectionString);
        AppConnectionString = await ConfigureRuntimeRoleAsync();
        Factory = new TavauraApiFactory(AppConnectionString);
    }

    public async Task DisposeAsync()
    {
        if (IsEnabled)
        {
            await Factory.DisposeAsync();
            NpgsqlConnection.ClearAllPools();
        }
    }

    public TavauraDbContext CreateAdminDbContext(Guid? tenantId = null)
    {
        var options = new DbContextOptionsBuilder<TavauraDbContext>()
            .UseNpgsql(AdminConnectionString)
            .Options;
        return new TavauraDbContext(
            options,
            new TenantContext { TenantId = tenantId });
    }

    public TavauraApiFactory CreateFactory(
        int authPermitLimit = 100,
        int publicWritePermitLimit = 100)
    {
        return new TavauraApiFactory(
            AppConnectionString,
            authPermitLimit,
            publicWritePermitLimit);
    }

    public async Task<User> SeedPlatformAdministratorAsync(string label)
    {
        await using var dbContext = CreateAdminDbContext();
        var now = DateTime.UtcNow;
        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = $"platform-{label}@example.com".ToLowerInvariant(),
            NormalizedEmail = $"PLATFORM-{label}@EXAMPLE.COM".ToUpperInvariant(),
            DisplayName = $"Platform {label}",
            Role = AuthRoles.PlatformAdmin,
            CreatedAt = now,
            UpdatedAt = now
        };
        user.PasswordHash = new PasswordHasher().HashPassword(user, TestWorkspace.Password);
        dbContext.Users.Add(user);
        await dbContext.SaveChangesAsync();
        return user;
    }

    public async Task<TestWorkspace> SeedWorkspaceAsync(string label)
    {
        var slug = $"test-{label}-{Guid.NewGuid():N}".ToLowerInvariant();
        var now = DateTime.UtcNow;
        var tenant = new Tenant
        {
            Id = Guid.NewGuid(),
            Name = $"Store {label}",
            Domain = $"{slug}.example.com",
            Platform = "shopify",
            Status = "active",
            Plan = "starter",
            CreatedAt = now,
            UpdatedAt = now
        };
        var account = new Account
        {
            Id = Guid.NewGuid(),
            Name = $"Account {label}",
            Slug = slug,
            BillingEmail = $"billing-{slug}@example.com",
            Status = "active",
            CreatedAt = now,
            UpdatedAt = now
        };
        var store = new Store
        {
            Id = Guid.NewGuid(),
            AccountId = account.Id,
            TenantId = tenant.Id,
            Name = tenant.Name,
            Slug = slug,
            Platform = tenant.Platform,
            Domain = tenant.Domain,
            Status = "active",
            CreatedAt = now,
            UpdatedAt = now
        };
        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = $"merchant-{slug}@example.com",
            NormalizedEmail = $"MERCHANT-{slug}@EXAMPLE.COM".ToUpperInvariant(),
            DisplayName = $"Merchant {label}",
            Role = AuthRoles.MerchantAdmin,
            TenantId = tenant.Id,
            CreatedAt = now,
            UpdatedAt = now
        };
        user.PasswordHash = new PasswordHasher().HashPassword(user, TestWorkspace.Password);
        var membership = new AccountUserMembership
        {
            Id = Guid.NewGuid(),
            AccountId = account.Id,
            UserId = user.Id,
            Role = AuthRoles.MerchantAdmin,
            Status = "active",
            CreatedAt = now
        };

        await using var dbContext = CreateAdminDbContext(tenant.Id);
        dbContext.AddRange(tenant, account, store, user, membership);
        await dbContext.SaveChangesAsync();
        return new TestWorkspace(tenant, account, store, user, IssueToken(user));
    }

    public static string IssueToken(User user)
    {
        var service = new JwtTokenService(Options.Create(new JwtOptions
        {
            Issuer = TavauraApiFactory.JwtIssuer,
            Audience = TavauraApiFactory.JwtAudience,
            SigningKey = TavauraApiFactory.JwtSigningKey,
            ExpiresMinutes = 30
        }));
        return service.CreateLoginResponse(user).AccessToken;
    }

    public static string HashSecret(string secret)
    {
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(secret)));
    }

    public static void Authorize(HttpRequestMessage request, string token)
    {
        request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
    }

    private async Task ResetSchemaAsync()
    {
        await using var connection = new NpgsqlConnection(AdminConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            DROP SCHEMA IF EXISTS public CASCADE;
            CREATE SCHEMA public;
            """;
        await command.ExecuteNonQueryAsync();
    }

    public static async Task ApplyMigrationsAsync(string connectionString, string? targetMigration = null)
    {
        var options = new DbContextOptionsBuilder<TavauraDbContext>()
            .UseNpgsql(connectionString)
            .Options;
        await using var dbContext = new TavauraDbContext(options, new TenantContext());
        if (targetMigration is null)
        {
            await dbContext.Database.MigrateAsync();
            return;
        }

        var migrator = dbContext.Database.GetService<Microsoft.EntityFrameworkCore.Migrations.IMigrator>();
        await migrator.MigrateAsync(targetMigration);
    }

    private async Task<string> ConfigureRuntimeRoleAsync()
    {
        var adminBuilder = new NpgsqlConnectionStringBuilder(AdminConnectionString);
        await using var connection = new NpgsqlConnection(AdminConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText =
            $$"""
            DO $role$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{{RuntimeRole}}') THEN
                    CREATE ROLE {{RuntimeRole}} LOGIN PASSWORD '{{RuntimePassword}}';
                ELSE
                    ALTER ROLE {{RuntimeRole}} LOGIN PASSWORD '{{RuntimePassword}}';
                END IF;
            END
            $role$;
            ALTER ROLE {{RuntimeRole}} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
            GRANT CONNECT ON DATABASE "{{adminBuilder.Database}}" TO {{RuntimeRole}};
            GRANT USAGE ON SCHEMA public TO {{RuntimeRole}};
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {{RuntimeRole}};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {{RuntimeRole}};
            """;
        await command.ExecuteNonQueryAsync();

        var appBuilder = new NpgsqlConnectionStringBuilder(AdminConnectionString)
        {
            Username = RuntimeRole,
            Password = RuntimePassword,
            ApplicationName = "tavaura-phase1-integration-tests"
        };
        return appBuilder.ConnectionString;
    }
}

public sealed record TestWorkspace(
    Tenant Tenant,
    Account Account,
    Store Store,
    User User,
    string AccessToken)
{
    public const string Password = "Correct-Phase1-Password!";
}

[CollectionDefinition(Name, DisableParallelization = true)]
public sealed class PostgresCollection : ICollectionFixture<PostgresFixture>
{
    public const string Name = "PostgreSQL integration";
}
