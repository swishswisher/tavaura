"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type {
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
} from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock3,
  PackageCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  getAdminDashboard,
  type DashboardActivityItem,
  type DashboardHealthSignal,
  type DashboardMetrics,
} from "@/lib/admin/dashboard";

type MetricCardConfig = {
  key: keyof DashboardMetrics;
  label: string;
  helper: string;
  icon: LucideIcon;
  href: string;
};

const METRIC_CARDS: MetricCardConfig[] = [
  {
    key: "totalGarments",
    label: "Total Garments",
    helper: "Active catalog items",
    icon: PackageCheck,
    href: "/admin/garments",
  },
  {
    key: "readyGarments",
    label: "Ready Garments",
    helper: "Prepared for render jobs",
    icon: CheckCircle2,
    href: "/admin/garments?status=ready",
  },
  {
    key: "processingGarments",
    label: "Processing Garments",
    helper: "Currently in ingestion flow",
    icon: Clock3,
    href: "/admin/ingestion-jobs?status=processing",
  },
  {
    key: "failedGarments",
    label: "Failed Garments",
    helper: "Need ingestion attention",
    icon: TriangleAlert,
    href: "/admin/ingestion-jobs?status=failed",
  },
  {
    key: "totalRenders",
    label: "Total Renders",
    helper: "Render jobs submitted",
    icon: Sparkles,
    href: "/admin/render-results",
  },
  {
    key: "recentResults",
    label: "Recent Results",
    helper: "Render results in last 7 days",
    icon: Activity,
    href: "/admin/render-results?range=7d",
  },
];

const HEALTH_ROUTES: Record<string, string> = {
  worker_pipeline: "/admin/ingestion-jobs",
  render_pipeline: "/admin/render-results",
  api_auth: "/admin/settings",
  tenant_resolution: "/admin/settings",
};

const DEFAULT_METRICS: DashboardMetrics = {
  totalGarments: 0,
  readyGarments: 0,
  processingGarments: 0,
  failedGarments: 0,
  totalRenders: 0,
  recentResults: 0,
};

function formatEventTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function getActivityStatusLabel(status: string | null) {
  if (!status) {
    return null;
  }

  const normalized = status.toLowerCase();

  if (normalized === "completed") return "Completed";
  if (normalized === "failed") return "Failed";
  if (normalized === "created") return "Created";
  if (normalized === "processing") return "Processing";
  if (normalized === "pending") return "Pending";

  return status;
}

function getActivityStatusClasses(status: string | null) {
  const normalized = status?.toLowerCase();

  if (normalized === "completed") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200/80";
  }

  if (normalized === "failed") {
    return "bg-rose-50 text-rose-700 ring-rose-200/80";
  }

  if (normalized === "processing" || normalized === "pending") {
    return "bg-amber-50 text-amber-700 ring-amber-200/80";
  }

  return "bg-slate-100 text-slate-600 ring-slate-200/80";
}

function getHealthChipClasses(status: string) {
  const normalized = status.toLowerCase();

  if (normalized === "ready") {
    return "bg-emerald-50 text-emerald-700";
  }

  if (normalized === "active") {
    return "bg-amber-50 text-amber-700";
  }

  if (normalized === "degraded") {
    return "bg-rose-50 text-rose-700";
  }

  return "bg-slate-100 text-slate-600";
}

function getHealthLabel(status: string) {
  const normalized = status.toLowerCase();

  if (normalized === "ready") return "Ready";
  if (normalized === "active") return "Active";
  if (normalized === "degraded") return "Attention";

  return "Unknown";
}

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof Element)) {
    return false;
  }

  return Boolean(
    target.closest('a, button, input, select, textarea, [role="button"], [role="link"]')
  );
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<DashboardMetrics>(DEFAULT_METRICS);
  const [recentActivity, setRecentActivity] = useState<DashboardActivityItem[]>([]);
  const [workspaceHealth, setWorkspaceHealth] = useState<DashboardHealthSignal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getAdminDashboard();
        if (!isMounted) {
          return;
        }

        setMetrics(data.metrics);
        setRecentActivity(data.recentActivity);
        setWorkspaceHealth(data.workspaceHealth);
      } catch (err) {
        if (!isMounted) {
          return;
        }

        setError(err instanceof Error ? err.message : "Unable to load dashboard data.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  const metricCards = useMemo(
    () =>
      METRIC_CARDS.map((card) => ({
        ...card,
        value: metrics[card.key].toLocaleString(),
      })),
    [metrics]
  );

  const readySummary =
    metrics.totalGarments > 0
      ? `${metrics.readyGarments} of ${metrics.totalGarments} garments are ready.`
      : "No garments are available yet.";

  const openRelatedActivity = (item: DashboardActivityItem) => {
    if (!item.relatedPath) {
      return;
    }

    router.push(item.relatedPath);
  };

  const handleActivityClick = (
    event: ReactMouseEvent<HTMLElement>,
    item: DashboardActivityItem
  ) => {
    if (!item.relatedPath || isInteractiveTarget(event.target)) {
      return;
    }

    openRelatedActivity(item);
  };

  const handleActivityKeyDown = (
    event: ReactKeyboardEvent<HTMLElement>,
    item: DashboardActivityItem
  ) => {
    if (!item.relatedPath || event.target !== event.currentTarget) {
      return;
    }

    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openRelatedActivity(item);
  };

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/80 shadow-tavaura backdrop-blur-xl">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-center">
          <div className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
              Dashboard
            </p>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold tracking-tight text-tavaura-ink sm:text-4xl">
                Live merchant operations overview.
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-tavaura-ink/70 sm:text-base">
                Track catalog readiness, render throughput, and operational activity in real time.
              </p>
            </div>
          </div>

          <div className="rounded-3xl bg-tavaura-ink p-5 text-white shadow-2xl shadow-tavaura-ink/20">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
              Workspace summary
            </p>
            <h2 className="mt-3 text-xl font-semibold">{readySummary}</h2>
            <p className="mt-2 text-sm leading-6 text-white/70">
              {metrics.totalRenders.toLocaleString()} total renders processed for this tenant.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                href="/admin/garments"
                className="inline-flex cursor-pointer items-center rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-tavaura-ink transition hover:bg-white/90"
              >
                Open Garments
              </Link>
              <Link
                href="/admin/render-results"
                className="inline-flex cursor-pointer items-center rounded-full border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/15"
              >
                Open Renders
              </Link>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <div className="flex items-start gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {metricCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.label}
              href={card.href}
              className="cursor-pointer rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur transition hover:-translate-y-0.5 hover:shadow-tavaura focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/20"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-tavaura-ink/70">{card.label}</p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-tavaura-ink">
                    {isLoading ? "--" : card.value}
                  </p>
                </div>
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
                  <Icon size={20} />
                </div>
              </div>
              <p className="mt-4 text-xs leading-5 text-tavaura-ink/60">{card.helper}</p>
            </Link>
          );
        })}
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.72fr)]">
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-tavaura-sm backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-tavaura-ink">Recent activity</h2>
              <p className="text-sm text-tavaura-ink/60">Latest garment and render pipeline events.</p>
            </div>
          </div>

          {isLoading ? (
            <div className="mt-6 rounded-2xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-8 text-center text-sm font-medium text-tavaura-ink/65">
              Loading recent activity...
            </div>
          ) : recentActivity.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-8 text-center">
              <p className="text-sm font-medium text-tavaura-ink">No activity yet.</p>
              <p className="mt-2 text-xs text-tavaura-ink/60">
                New garment, ingestion, and render events will appear here.
              </p>
            </div>
          ) : (
            <div className="mt-5 space-y-3">
              {recentActivity.map((item, index) => {
                const statusLabel = getActivityStatusLabel(item.status);
                const isRowClickable = Boolean(item.relatedPath);

                return (
                  <article
                    key={`${item.eventType}-${item.timestamp}-${index}`}
                    role={isRowClickable ? "link" : undefined}
                    tabIndex={isRowClickable ? 0 : undefined}
                    aria-label={isRowClickable ? `Open details for ${item.eventLabel}` : undefined}
                    onClick={(event) => handleActivityClick(event, item)}
                    onKeyDown={(event) => handleActivityKeyDown(event, item)}
                    className={`rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 ${
                      isRowClickable
                        ? "cursor-pointer transition hover:-translate-y-0.5 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/20"
                        : ""
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-tavaura-ink">{item.eventLabel}</p>
                        {item.relatedName && (
                          <p className="mt-1 truncate text-xs text-tavaura-ink/65">
                            {item.relatedName}
                          </p>
                        )}
                        <p className="mt-1 text-xs text-tavaura-ink/55">
                          {formatEventTime(item.timestamp)}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center justify-end gap-2">
                        {statusLabel && (
                          <span
                            className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${getActivityStatusClasses(
                              item.status
                            )}`}
                          >
                            {statusLabel}
                          </span>
                        )}
                        {item.relatedPath && (
                          <Link
                            href={item.relatedPath}
                            onClick={(event) => event.stopPropagation()}
                            className="inline-flex cursor-pointer items-center rounded-full border border-tavaura-ink/12 bg-white px-3 py-1 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
                          >
                            Open
                          </Link>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-tavaura-sm backdrop-blur">
          <h2 className="text-lg font-semibold text-tavaura-ink">Workspace health</h2>
          <div className="mt-5 space-y-3">
            {workspaceHealth.length === 0 && isLoading ? (
              <div className="rounded-2xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-4 py-5 text-sm text-tavaura-ink/65">
                Loading workspace health...
              </div>
            ) : workspaceHealth.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-4 py-5 text-sm text-tavaura-ink/65">
                Health signals are not available yet.
              </div>
            ) : (
              workspaceHealth.map((signal) => {
                const targetHref = HEALTH_ROUTES[signal.key];
                const content = (
                  <>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-tavaura-ink">{signal.label}</span>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getHealthChipClasses(
                          signal.status
                        )}`}
                      >
                        {getHealthLabel(signal.status)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-tavaura-ink/60">{signal.detail}</p>
                    {signal.lastUpdatedAt && (
                      <p className="mt-1 text-[11px] text-tavaura-ink/50">
                        Updated {formatEventTime(signal.lastUpdatedAt)}
                      </p>
                    )}
                  </>
                );

                if (targetHref) {
                  return (
                    <Link
                      key={signal.key}
                      href={targetHref}
                      className="block cursor-pointer rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 transition hover:-translate-y-0.5 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/20"
                    >
                      {content}
                    </Link>
                  );
                }

                return (
                  <div
                    key={signal.key}
                    className="rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3"
                  >
                    {content}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
