import { authenticatedFetch } from "@/lib/api";

export type DashboardMetrics = {
  totalGarments: number;
  readyGarments: number;
  processingGarments: number;
  failedGarments: number;
  totalRenders: number;
  recentResults: number;
};

export type DashboardActivityItem = {
  eventType: string;
  eventLabel: string;
  relatedName: string | null;
  relatedPath: string | null;
  status: string | null;
  timestamp: string;
};

export type DashboardHealthSignal = {
  key: string;
  label: string;
  status: string;
  detail: string;
  lastUpdatedAt: string | null;
};

export type DashboardResponse = {
  metrics: DashboardMetrics;
  recentActivity: DashboardActivityItem[];
  workspaceHealth: DashboardHealthSignal[];
};

export async function getAdminDashboard() {
  return authenticatedFetch<DashboardResponse>("/api/admin/dashboard");
}
