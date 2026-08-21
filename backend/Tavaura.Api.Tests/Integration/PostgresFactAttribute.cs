using Xunit;

namespace Tavaura.Api.Tests.Integration;

public sealed class PostgresFactAttribute : FactAttribute
{
    public PostgresFactAttribute()
    {
        if (string.IsNullOrWhiteSpace(
                Environment.GetEnvironmentVariable(PostgresFixture.AdminConnectionEnvironmentVariable)))
        {
            Skip = $"Set {PostgresFixture.AdminConnectionEnvironmentVariable} to run PostgreSQL integration tests.";
        }
    }
}
