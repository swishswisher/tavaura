using Microsoft.AspNetCore.Mvc;
using Tavaura.Api.Models.Tenants;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

/// <summary>
/// Temporary read-only endpoints exposing sample tenants until the database-backed implementation is ready.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class TenantsController : ControllerBase
{
    private readonly ITenantContext _tenantContext;

    public TenantsController(ITenantContext tenantContext)
    {
        _tenantContext = tenantContext;
    }

    /// <summary>
    /// Returns the tenant context inferred from headers for debugging purposes during early development.
    /// </summary>
    [HttpGet("current-context")]
    public ActionResult<TenantContextDto> GetCurrentContext()
    {
        var dto = new TenantContextDto
        {
            TenantId = _tenantContext.TenantId,
            Platform = _tenantContext.Platform,
            Domain = _tenantContext.Domain,
            HasTenant = _tenantContext.HasTenant
        };

        return Ok(dto);
    }

    [HttpGet("sample")]
    public ActionResult<IEnumerable<TenantSummaryDto>> GetSampleTenants()
    {
        var tenants = new List<TenantSummaryDto>
        {
            new()
            {
                Id = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                Name = "Demo Fashion",
                Domain = "demo-fashion.example",
                Platform = "shopify",
                Status = "trial",
                Plan = "starter"
            },
            new()
            {
                Id = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                Name = "Glow Cosmetics",
                Domain = "glow-cosmetics.example",
                Platform = "woocommerce",
                Status = "active",
                Plan = "growth"
            }
        };

        return Ok(tenants);
    }
}

