using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

namespace Tavaura.Api.Tenancy;

/// <summary>
/// Simple header-based tenant resolution middleware used during early development. Future versions may also inspect
/// domains, API keys, or session cookies to hydrate the tenant context.
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

        if (context.Request.Headers.TryGetValue(TenantHeader, out var tenantHeader) &&
            Guid.TryParse(tenantHeader, out var tenantId))
        {
            tenantContext.TenantId = tenantId;
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

