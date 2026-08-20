using System.Security.Claims;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Tenancy;
using Xunit;

namespace Tavaura.Api.Tests;

public class TenantContextMiddlewareTests
{
    [Fact]
    public async Task AnonymousTenantHeaderCannotSelectATenant()
    {
        var requestedTenant = Guid.NewGuid();
        var tenantContext = new TenantContext();
        await using var scope = await CreateScopeAsync(tenantContext, requestedTenant);
        var httpContext = new DefaultHttpContext { RequestServices = scope.ServiceProvider };
        httpContext.Request.Headers["X-Tavaura-Tenant"] = requestedTenant.ToString();
        var nextCalled = false;
        var middleware = new TenantContextMiddleware(_ =>
        {
            nextCalled = true;
            return Task.CompletedTask;
        });

        await middleware.InvokeAsync(httpContext);

        Assert.True(nextCalled);
        Assert.Null(tenantContext.TenantId);
    }

    [Fact]
    public async Task MerchantClaimWinsOverAConflictingHeader()
    {
        var claimedTenant = Guid.NewGuid();
        var headerTenant = Guid.NewGuid();
        var tenantContext = new TenantContext();
        await using var scope = await CreateScopeAsync(tenantContext, claimedTenant, headerTenant);
        var httpContext = AuthenticatedContext(scope, AuthRoles.MerchantAdmin, claimedTenant);
        httpContext.Request.Headers["X-Tavaura-Tenant"] = headerTenant.ToString();
        var middleware = new TenantContextMiddleware(_ => Task.CompletedTask);

        await middleware.InvokeAsync(httpContext);

        Assert.Equal(claimedTenant, tenantContext.TenantId);
    }

    [Fact]
    public async Task PlatformAdministratorCanSelectAnExistingTenant()
    {
        var requestedTenant = Guid.NewGuid();
        var tenantContext = new TenantContext();
        await using var scope = await CreateScopeAsync(tenantContext, requestedTenant);
        var httpContext = AuthenticatedContext(scope, AuthRoles.PlatformAdmin, null);
        httpContext.Request.Headers["X-Tavaura-Tenant"] = requestedTenant.ToString();
        var middleware = new TenantContextMiddleware(_ => Task.CompletedTask);

        await middleware.InvokeAsync(httpContext);

        Assert.Equal(requestedTenant, tenantContext.TenantId);
        Assert.Equal("shopify", tenantContext.Platform);
    }

    private static DefaultHttpContext AuthenticatedContext(
        AsyncServiceScope scope,
        string role,
        Guid? tenantId)
    {
        var claims = new List<Claim> { new(ClaimTypes.Role, role) };
        if (tenantId.HasValue)
        {
            claims.Add(new Claim(AuthClaimTypes.TenantId, tenantId.Value.ToString()));
        }

        return new DefaultHttpContext
        {
            RequestServices = scope.ServiceProvider,
            User = new ClaimsPrincipal(new ClaimsIdentity(claims, "test"))
        };
    }

    private static async Task<AsyncServiceScope> CreateScopeAsync(
        TenantContext tenantContext,
        params Guid[] tenantIds)
    {
        var services = new ServiceCollection();
        services.AddSingleton<ITenantContext>(tenantContext);
        services.AddDbContext<TavauraDbContext>(options =>
            options.UseInMemoryDatabase(Guid.NewGuid().ToString()));
        var provider = services.BuildServiceProvider();
        var scope = provider.CreateAsyncScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<TavauraDbContext>();
        foreach (var tenantId in tenantIds)
        {
            dbContext.Tenants.Add(new Tenant
            {
                Id = tenantId,
                Name = tenantId.ToString(),
                Platform = "shopify",
                Status = "active"
            });
        }

        await dbContext.SaveChangesAsync();
        return scope;
    }
}
