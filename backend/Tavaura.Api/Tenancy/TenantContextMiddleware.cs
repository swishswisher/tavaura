using System;
using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Tavaura.Api.Auth;

namespace Tavaura.Api.Tenancy;

/// <summary>
/// Resolves tenant context from authenticated JWT claims, falling back to development headers for legacy flows.
/// </summary>
public class TenantContextMiddleware
{
    private const string TenantHeader = "X-Tavaura-Tenant";
    private const string PlatformHeader = "X-Tavaura-Platform";
    private const string DomainHeader = "X-Tavaura-Domain";

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

        if (isAuthenticated && Guid.TryParse(tenantClaim, out var authenticatedTenantId))
        {
            tenantContext.TenantId = authenticatedTenantId;
        }
        else if ((!isAuthenticated || role == AuthRoles.PlatformAdmin) &&
                 context.Request.Headers.TryGetValue(TenantHeader, out var tenantHeader) &&
                 Guid.TryParse(tenantHeader, out var headerTenantId))
        {
            tenantContext.TenantId = headerTenantId;
        }

        if (context.Request.Headers.TryGetValue(PlatformHeader, out var platformHeader))
        {
            tenantContext.Platform = platformHeader.ToString();
        }

        if (context.Request.Headers.TryGetValue(DomainHeader, out var domainHeader))
        {
            tenantContext.Domain = domainHeader.ToString();
        }

        await _next(context);
    }
}
