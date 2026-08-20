using System.Data.Common;
using System.Security.Claims;
using Microsoft.EntityFrameworkCore.Diagnostics;
using Npgsql;
using Tavaura.Api.Auth;

namespace Tavaura.Api.Tenancy;

public sealed class TenantRlsConnectionInterceptor : DbConnectionInterceptor
{
    private readonly ITenantContext _tenantContext;
    private readonly IHttpContextAccessor _httpContextAccessor;

    public TenantRlsConnectionInterceptor(
        ITenantContext tenantContext,
        IHttpContextAccessor httpContextAccessor)
    {
        _tenantContext = tenantContext;
        _httpContextAccessor = httpContextAccessor;
    }

    public override void ConnectionOpened(DbConnection connection, ConnectionEndEventData eventData)
    {
        ConfigureSessionAsync(connection, CancellationToken.None).GetAwaiter().GetResult();
        base.ConnectionOpened(connection, eventData);
    }

    public override async Task ConnectionOpenedAsync(
        DbConnection connection,
        ConnectionEndEventData eventData,
        CancellationToken cancellationToken = default)
    {
        await ConfigureSessionAsync(connection, cancellationToken);
        await base.ConnectionOpenedAsync(connection, eventData, cancellationToken);
    }

    private async Task ConfigureSessionAsync(DbConnection connection, CancellationToken cancellationToken)
    {
        if (connection is not NpgsqlConnection)
        {
            return;
        }

        var role = _httpContextAccessor.HttpContext?.User.FindFirstValue(ClaimTypes.Role);
        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT set_config('app.tenant_id', @tenant_id, false),
                   set_config('app.is_platform', @is_platform, false),
                   set_config('app.is_worker', 'false', false);
            """;
        var tenantParameter = command.CreateParameter();
        tenantParameter.ParameterName = "tenant_id";
        tenantParameter.Value = _tenantContext.TenantId?.ToString() ?? string.Empty;
        command.Parameters.Add(tenantParameter);
        var platformParameter = command.CreateParameter();
        platformParameter.ParameterName = "is_platform";
        platformParameter.Value = role == AuthRoles.PlatformAdmin ? "true" : "false";
        command.Parameters.Add(platformParameter);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }
}
