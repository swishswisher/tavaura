using System;

namespace Tavaura.Api.Tenancy;

public class TenantContext : ITenantContext
{
    public Guid? TenantId { get; set; }

    public string? Platform { get; set; }

    public string? Domain { get; set; }

    public bool HasTenant => TenantId.HasValue;
}

