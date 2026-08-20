using Microsoft.AspNetCore.Mvc;
using Tavaura.Api.Models.Tenants;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

/// <summary>
/// Temporary read-only endpoints exposing sample tenants until the database-backed implementation is ready.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Microsoft.AspNetCore.Authorization.Authorize]
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

}

