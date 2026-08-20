using System;
using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;

namespace Tavaura.Api.Tenancy;

/// <summary>
/// Resolves tenant context from verified identity. Platform administrators may explicitly select a tenant.
/// </summary>
public class TenantContextMiddleware
{
    private const string TenantHeader = "X-Tavaura-Tenant";
    private readonly RequestDelegate _next;

    public TenantContextMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var tenantContext = context.RequestServices.GetRequiredService<ITenantContext>();
        var isAuthenticated = context.User.Identity?.IsAuthenticated == true;
        var role = context.User.FindFirstValue(ClaimTypes.Role) ?? context.User.FindFirstValue("role");
        var tenantClaim = context.User.FindFirstValue(AuthClaimTypes.TenantId);
        Guid? requestedTenantId = null;

        if (isAuthenticated && Guid.TryParse(tenantClaim, out var authenticatedTenantId))
        {
            requestedTenantId = authenticatedTenantId;
        }
        else if (isAuthenticated && role == AuthRoles.PlatformAdmin &&
                 context.Request.Headers.TryGetValue(TenantHeader, out var tenantHeader))
        {
            if (!Guid.TryParse(tenantHeader, out var headerTenantId))
            {
                context.Response.StatusCode = StatusCodes.Status400BadRequest;
                await context.Response.WriteAsJsonAsync(new { message = "Tenant header is invalid." });
                return;
            }

            requestedTenantId = headerTenantId;
        }

        if (requestedTenantId.HasValue)
        {
            var dbContext = context.RequestServices.GetRequiredService<TavauraDbContext>();
            var tenant = await dbContext.Tenants
                .AsNoTracking()
                .SingleOrDefaultAsync(t => t.Id == requestedTenantId.Value, context.RequestAborted);
            if (tenant is null)
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                await context.Response.WriteAsJsonAsync(new { message = "Tenant context is not authorized." });
                return;
            }

            tenantContext.TenantId = tenant.Id;
            tenantContext.Platform = tenant.Platform;
            tenantContext.Domain = tenant.Domain;
        }

        await _next(context);
    }
}
