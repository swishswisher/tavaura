using System;

namespace Tavaura.Api.Tenancy;

public interface ITenantContext
{
    Guid? TenantId { get; set; }

    string? Platform { get; set; }

    string? Domain { get; set; }

    bool HasTenant { get; }
}

