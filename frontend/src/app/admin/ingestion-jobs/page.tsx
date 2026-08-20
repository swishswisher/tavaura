"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
} from "react";
import { AlertCircle, PackagePlus, RefreshCw } from "lucide-react";
import {
  listGarments,
  retryGarmentIngestion,
  type Garment,
} from "@/lib/admin/garments";
import { listIngestionJobs, type IngestionJob } from "@/lib/admin/ingestion-jobs";

type StatusFilter = "all" | "pending" | "processing" | "completed" | "failed";
type IngestionJobRow = IngestionJob & { isSyntheticPending?: boolean };

const filterTabs: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
];

function getNormalizedStatusFilter(value: string | null): StatusFilter {
  if (value === "pending") {
    return "pending";
  }

  if (value === "processing") {
    return "processing";
  }

  if (value === "completed") {
    return "completed";
  }

  if (value === "failed") {
    return "failed";
  }

  return "all";
}

function getLookupKey(value: string | null | undefined) {
  return value?.trim().toLowerCase() ?? "";
}

function buildSyntheticPendingRows(
  garments: Garment[],
  jobs: IngestionJob[]
): IngestionJobRow[] {
  const garmentIdsWithJobs = new Set(
    jobs.map((job) => getLookupKey(job.garmentId)).filter(Boolean)
  );
  const productIdsWithJobs = new Set(
    jobs.map((job) => getLookupKey(job.externalProductId)).filter(Boolean)
  );

  return garments
    .filter((garment) => {
      if (getLookupKey(garment.status) !== "pending") {
        return false;
      }

      const garmentIdKey = getLookupKey(garment.id);
      const productIdKey = getLookupKey(garment.externalProductId);
      const hasGarmentJob = garmentIdKey ? garmentIdsWithJobs.has(garmentIdKey) : false;
      const hasProductJob = productIdKey ? productIdsWithJobs.has(productIdKey) : false;

      return !hasGarmentJob && !hasProductJob;
    })
    .map((garment) => ({
      id: `synthetic-pending-${garment.id}`,
      garmentId: garment.id,
      garmentName: garment.name,
      externalProductId: garment.externalProductId,
      status: "pending",
      attemptCount: 0,
      errorMessage: null,
      startedAt: null,
      completedAt: null,
      createdAt: garment.createdAt,
      updatedAt: garment.updatedAt,
      isSyntheticPending: true,
    }));
}

function getJobStatus(status: string | null | undefined): Exclude<StatusFilter, "all"> {
  const normalized = status?.trim().toLowerCase();

  if (!normalized || normalized === "unknown") {
    return "pending";
  }

  if (normalized === "pending") {
    return "pending";
  }

  if (normalized === "processing" || normalized === "running" || normalized === "in_progress") {
    return "processing";
  }

  if (normalized === "completed" || normalized === "success") {
    return "completed";
  }

  if (normalized === "failed" || normalized === "error" || normalized === "needs_review") {
    return "failed";
  }

  return "pending";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function getStatusLabel(status: string) {
  const normalizedStatus = getJobStatus(status);

  if (normalizedStatus === "processing") return "Processing";
  if (normalizedStatus === "completed") return "Completed";
  if (normalizedStatus === "failed") return "Failed";
  if (normalizedStatus === "pending") return "Pending";

  return "Pending";
}

function getStatusClasses(status: string) {
  const normalizedStatus = getJobStatus(status);

  if (normalizedStatus === "completed") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200/80";
  }

  if (normalizedStatus === "processing" || normalizedStatus === "pending") {
    return "bg-amber-50 text-amber-700 ring-amber-200/80";
  }

  if (normalizedStatus === "failed") {
    return "bg-rose-50 text-rose-700 ring-rose-200/80";
  }

  return "bg-slate-100 text-slate-600 ring-slate-200/80";
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${getStatusClasses(status)}`}
    >
      {getStatusLabel(status)}
    </span>
  );
}

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof Element)) {
    return false;
  }

  return Boolean(
    target.closest('a, button, input, select, textarea, [role="button"], [role="link"]')
  );
}

function getGarmentHref(garmentId: string) {
  return `/admin/garments/${garmentId}`;
}

export default function AdminIngestionJobsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [activeFilter, setActiveFilter] = useState<StatusFilter>(() =>
    getNormalizedStatusFilter(searchParams.get("status"))
  );

  const [jobs, setJobs] = useState<IngestionJobRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [retryingJobId, setRetryingJobId] = useState<string | null>(null);

  useEffect(() => {
    const nextFilter = getNormalizedStatusFilter(searchParams.get("status"));
    setActiveFilter((currentFilter) =>
      currentFilter === nextFilter ? currentFilter : nextFilter
    );
  }, [searchParams]);

  const handleFilterChange = useCallback((nextFilter: StatusFilter) => {
    setActiveFilter(nextFilter);

    if (typeof window === "undefined") {
      return;
    }

    const params = new URLSearchParams(window.location.search);

    if (nextFilter === "all") {
      params.delete("status");
    } else {
      params.set("status", nextFilter);
    }

    const nextSearch = params.toString();
    const nextUrl = nextSearch
      ? `${window.location.pathname}?${nextSearch}`
      : window.location.pathname;

    window.history.replaceState(window.history.state, "", nextUrl);
  }, []);

  const loadJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [jobsData, garmentsData] = await Promise.all([
        listIngestionJobs(),
        listGarments(),
      ]);
      const syntheticPendingRows = buildSyntheticPendingRows(garmentsData, jobsData);
      setJobs([...jobsData, ...syntheticPendingRows]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load ingestion jobs.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const filteredJobs = useMemo(() => {
    if (activeFilter === "all") {
      return jobs;
    }

    return jobs.filter((job) => getJobStatus(job.status) === activeFilter);
  }, [activeFilter, jobs]);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  const handleRetry = async (job: IngestionJobRow) => {
    if (!job.garmentId) {
      setError("Unable to retry this job because the garment reference is missing.");
      return;
    }

    setRetryingJobId(job.id);
    setError(null);
    setNotice(null);

    try {
      await retryGarmentIngestion(job.garmentId);
      setNotice(
        job.isSyntheticPending
          ? `Processing queued for ${job.garmentName}.`
          : `Rebuild queued for ${job.garmentName}.`
      );
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to retry ingestion.");
    } finally {
      setRetryingJobId(null);
    }
  };

  const handleRowClick = (
    event: ReactMouseEvent<HTMLElement>,
    job: IngestionJob
  ) => {
    if (!job.garmentId || isInteractiveTarget(event.target)) {
      return;
    }

    router.push(getGarmentHref(job.garmentId));
  };

  const handleRowKeyDown = (
    event: ReactKeyboardEvent<HTMLElement>,
    job: IngestionJob
  ) => {
    if (!job.garmentId || event.target !== event.currentTarget) {
      return;
    }

    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    router.push(getGarmentHref(job.garmentId));
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
            Pipeline
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink">
            Ingestion Jobs
          </h1>
          <p className="mt-2 text-sm text-tavaura-ink/70">
            Monitor garment processing jobs and quickly recover failed tasks.
          </p>
        </div>
        <Link
          href="/admin/garments"
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
        >
          <PackagePlus size={17} />
          Open Garments
        </Link>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-4 shadow-tavaura-sm backdrop-blur sm:p-5">
        <div className="flex flex-wrap gap-2">
          {filterTabs.map((tab) => {
            const isActive = activeFilter === tab.value;

            return (
              <button
                key={tab.value}
                type="button"
                onClick={() => handleFilterChange(tab.value)}
                className={`inline-flex cursor-pointer items-center rounded-full px-4 py-2 text-sm font-semibold transition ${
                  isActive
                    ? "bg-tavaura-ink text-white shadow-tavaura-sm"
                    : "border border-tavaura-ink/12 bg-white text-tavaura-ink hover:bg-tavaura-ink/5"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </section>

      {error && (
        <div className="flex items-start gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
          {notice}
        </div>
      )}

      <section className="rounded-[2rem] border border-white/70 bg-white/80 p-4 shadow-tavaura-sm backdrop-blur sm:p-5">
        {isLoading ? (
          <div className="py-14 text-center text-sm font-medium text-tavaura-ink/65">
            Loading ingestion jobs...
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-12 text-center">
            {jobs.length === 0 ? (
              <>
                <p className="text-sm font-semibold text-tavaura-ink">No ingestion jobs yet.</p>
                <p className="mt-2 text-xs text-tavaura-ink/60">
                  Queue garment processing to see job history here.
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold text-tavaura-ink">No matching jobs.</p>
                <p className="mt-2 text-xs text-tavaura-ink/60">
                  Try a different status filter.
                </p>
              </>
            )}
          </div>
        ) : (
          <>
            <div className="hidden rounded-3xl border border-tavaura-ink/8 bg-white lg:block">
              <table className="w-full table-fixed text-left text-sm">
                <colgroup>
                  <col className="w-[30%]" />
                  <col className="w-[12%]" />
                  <col className="w-[16%]" />
                  <col className="w-[16%]" />
                  <col className="w-[18%]" />
                  <col className="w-[8%]" />
                </colgroup>
                <thead className="bg-tavaura-bg/80 text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/55">
                  <tr>
                    <th className="rounded-tl-3xl px-4 py-3">Garment</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3">Updated</th>
                    <th className="px-4 py-3">Error</th>
                    <th className="rounded-tr-3xl px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-tavaura-ink/8">
                  {filteredJobs.map((job) => {
                    const isClickable = Boolean(job.garmentId);
                    const isFailed = getJobStatus(job.status) === "failed";
                    const canQueue = Boolean(job.isSyntheticPending && job.garmentId);
                    const isRetrying = retryingJobId === job.id;

                    return (
                      <tr
                        key={job.id}
                        role={isClickable ? "link" : undefined}
                        tabIndex={isClickable ? 0 : undefined}
                        aria-label={
                          isClickable ? `Open details for ${job.garmentName}` : undefined
                        }
                        onClick={(event) => handleRowClick(event, job)}
                        onKeyDown={(event) => handleRowKeyDown(event, job)}
                        className={
                          isClickable
                            ? "cursor-pointer transition hover:bg-tavaura-bg/50 focus-visible:bg-tavaura-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-tavaura-ink/15"
                            : undefined
                        }
                      >
                        <td className="px-4 py-3">
                          <div className="min-w-0">
                            {job.garmentId ? (
                              <Link
                                href={getGarmentHref(job.garmentId)}
                                onClick={(event) => event.stopPropagation()}
                                className="block cursor-pointer truncate font-semibold text-tavaura-ink transition hover:text-tavaura-cocoa focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                              >
                                {job.garmentName}
                              </Link>
                            ) : (
                              <p className="truncate font-semibold text-tavaura-ink">
                                {job.garmentName}
                              </p>
                            )}
                            <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                              Product ID: {job.externalProductId}
                            </p>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={job.status} />
                        </td>
                        <td className="truncate px-4 py-3 text-tavaura-ink/65">
                          {formatDate(job.createdAt)}
                        </td>
                        <td className="truncate px-4 py-3 text-tavaura-ink/65">
                          {formatDate(job.updatedAt)}
                        </td>
                        <td className="px-4 py-3 text-xs text-rose-700">
                          {isFailed && job.errorMessage ? job.errorMessage : "\u2014"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {(isFailed || canQueue) && job.garmentId ? (
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation();
                                void handleRetry(job);
                              }}
                              disabled={isRetrying}
                              className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-3 py-1.5 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              <RefreshCw size={14} />
                              {isRetrying ? "Queueing..." : canQueue ? "Queue" : "Rebuild"}
                            </button>
                          ) : (
                            <span className="text-xs text-tavaura-ink/35">\u2014</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="space-y-3 lg:hidden">
              {filteredJobs.map((job) => {
                const isClickable = Boolean(job.garmentId);
                const isFailed = getJobStatus(job.status) === "failed";
                const canQueue = Boolean(job.isSyntheticPending && job.garmentId);
                const isRetrying = retryingJobId === job.id;

                return (
                  <article
                    key={job.id}
                    role={isClickable ? "link" : undefined}
                    tabIndex={isClickable ? 0 : undefined}
                    aria-label={isClickable ? `Open details for ${job.garmentName}` : undefined}
                    onClick={(event) => handleRowClick(event, job)}
                    onKeyDown={(event) => handleRowKeyDown(event, job)}
                    className={`rounded-3xl border border-tavaura-ink/8 bg-white/95 p-4 shadow-tavaura-sm ${
                      isClickable
                        ? "cursor-pointer transition hover:bg-white hover:shadow-tavaura focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                        : ""
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        {job.garmentId ? (
                          <Link
                            href={getGarmentHref(job.garmentId)}
                            onClick={(event) => event.stopPropagation()}
                            className="block cursor-pointer truncate font-semibold text-tavaura-ink transition hover:text-tavaura-cocoa focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                          >
                            {job.garmentName}
                          </Link>
                        ) : (
                          <p className="truncate font-semibold text-tavaura-ink">{job.garmentName}</p>
                        )}
                        <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                          Product ID: {job.externalProductId}
                        </p>
                      </div>
                      <StatusBadge status={job.status} />
                    </div>

                    <div className="mt-3 grid gap-2 text-xs text-tavaura-ink/65 sm:grid-cols-2">
                      <p>Created {formatDate(job.createdAt)}</p>
                      <p>Updated {formatDate(job.updatedAt)}</p>
                    </div>

                    {isFailed && job.errorMessage && (
                      <p className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                        {job.errorMessage}
                      </p>
                    )}

                    {(isFailed || canQueue) && job.garmentId && (
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleRetry(job);
                        }}
                        disabled={isRetrying}
                        className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-4 py-2 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        <RefreshCw size={14} />
                        {isRetrying ? "Queueing..." : canQueue ? "Queue" : "Rebuild"}
                      </button>
                    )}
                  </article>
                );
              })}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
