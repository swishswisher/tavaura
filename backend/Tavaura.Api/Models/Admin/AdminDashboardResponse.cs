namespace Tavaura.Api.Models.Admin;

public class AdminDashboardResponse
{
    public AdminDashboardMetrics Metrics { get; set; } = new();

    public IReadOnlyList<AdminDashboardActivityItem> RecentActivity { get; set; } =
        Array.Empty<AdminDashboardActivityItem>();

    public IReadOnlyList<AdminDashboardHealthSignal> WorkspaceHealth { get; set; } =
        Array.Empty<AdminDashboardHealthSignal>();
}

public class AdminDashboardMetrics
{
    public int TotalGarments { get; set; }

    public int ReadyGarments { get; set; }

    public int ProcessingGarments { get; set; }

    public int FailedGarments { get; set; }

    public int TotalRenders { get; set; }

    public int RecentResults { get; set; }
}

public class AdminDashboardActivityItem
{
    public string EventType { get; set; } = string.Empty;

    public string EventLabel { get; set; } = string.Empty;

    public string? RelatedName { get; set; }

    public string? RelatedPath { get; set; }

    public string? Status { get; set; }

    public DateTime Timestamp { get; set; }
}

public class AdminDashboardHealthSignal
{
    public string Key { get; set; } = string.Empty;

    public string Label { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string Detail { get; set; } = string.Empty;

    public DateTime? LastUpdatedAt { get; set; }
}
