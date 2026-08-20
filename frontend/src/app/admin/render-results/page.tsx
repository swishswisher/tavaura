"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ExternalLink, Sparkles, Trash2 } from "lucide-react";
import { RenderPreviewImage } from "@/components/admin/RenderPreviewImage";
import {
  deleteRenderResult,
  listRenderResults,
  type RenderResultListItem,
} from "@/lib/admin/render-results";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function getStatusLabel(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "completed") return "Completed";
  if (normalizedStatus === "processing") return "Processing";
  if (normalizedStatus === "failed") return "Failed";
  if (normalizedStatus === "pending") return "Pending";

  return status || "Pending";
}

function getStatusClasses(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "completed") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200/80";
  }

  if (normalizedStatus === "processing") {
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

function RenderOutputButton({ item }: { item: RenderResultListItem }) {
  if (!item.outputImageUrl) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-tavaura-ink/12 bg-tavaura-bg/70 px-3 py-1.5 text-xs font-medium text-tavaura-ink/55">
        Output pending
      </span>
    );
  }

  return (
    <a
      href={item.outputImageUrl}
      target="_blank"
      rel="noreferrer"
      className="inline-flex cursor-pointer items-center gap-1 rounded-full border border-tavaura-ink/12 bg-white px-3 py-1.5 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
    >
      Open output
      <ExternalLink size={13} />
    </a>
  );
}

export default function AdminRenderResultsPage() {
  const [results, setResults] = useState<RenderResultListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadResults() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listRenderResults(100);
        if (isMounted) {
          setResults(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Unable to load render results."
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadResults();

    return () => {
      isMounted = false;
    };
  }, []);

  const hasResults = useMemo(() => results.length > 0, [results.length]);

  const handleDelete = async (item: RenderResultListItem) => {
    const confirmed = window.confirm("Delete this render?");
    if (!confirmed) {
      return;
    }

    setDeletingId(item.renderJobId);
    setError(null);
    setNotice(null);

    try {
      await deleteRenderResult(item.renderJobId);
      setResults((current) =>
        current.filter((result) => result.renderJobId !== item.renderJobId)
      );
      setNotice("Render was deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete render.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
            Render center
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink">
            Render Results
          </h1>
          <p className="mt-2 text-sm text-tavaura-ink/70">
            Review generated try-on outputs and render readiness.
          </p>
        </div>
        <Link
          href="/admin/garments"
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
        >
          <Sparkles size={16} />
          Open Garments
        </Link>
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
            Loading render results...
          </div>
        ) : !hasResults ? (
          <div className="rounded-3xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-tavaura-ink shadow-tavaura-sm">
              <Sparkles size={22} />
            </div>
            <p className="text-sm font-semibold text-tavaura-ink">No render results yet.</p>
            <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-tavaura-ink/60">
              Create a try-on render to see outputs here.
            </p>
          </div>
        ) : (
          <>
            <div className="hidden rounded-3xl border border-tavaura-ink/8 bg-white xl:block">
              <table className="w-full table-fixed text-left text-sm">
                <colgroup>
                  <col className="w-[14%]" />
                  <col className="w-[22%]" />
                  <col className="w-[12%]" />
                  <col className="w-[14%]" />
                  <col className="w-[15%]" />
                  <col className="w-[9%]" />
                  <col className="w-[14%]" />
                </colgroup>
                <thead className="bg-tavaura-bg/80 text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/55">
                  <tr>
                    <th className="rounded-tl-3xl px-4 py-3">Preview</th>
                    <th className="px-4 py-3">Garment</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3">Output</th>
                    <th className="px-4 py-3">Render Job</th>
                    <th className="rounded-tr-3xl px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-tavaura-ink/8">
                  {results.map((item) => (
                    <tr key={item.renderJobId}>
                      <td className="px-4 py-3">
                        <RenderPreviewImage
                          garmentName={item.garmentName}
                          imageUrl={item.previewImageUrl}
                          className="h-16 w-16"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <p className="truncate font-semibold text-tavaura-ink">
                          {item.garmentName}
                        </p>
                        <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                          Job ID: {item.renderJobId}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="truncate px-4 py-3 text-tavaura-ink/65">
                        {formatDate(item.createdAt)}
                      </td>
                      <td className="px-4 py-3">
                        <RenderOutputButton item={item} />
                      </td>
                      <td className="truncate px-4 py-3 text-xs text-tavaura-ink/55">
                        {item.renderJobId}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/admin/render-results/${item.renderJobId}`}
                            className="inline-flex cursor-pointer items-center rounded-full border border-tavaura-ink/12 bg-white px-3 py-1.5 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
                          >
                            Open details
                          </Link>
                          <button
                            type="button"
                            onClick={() => void handleDelete(item)}
                            disabled={deletingId === item.renderJobId}
                            aria-label={`Delete render for ${item.garmentName}`}
                            className="inline-flex cursor-pointer items-center rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:hidden">
              {results.map((item) => (
                <article
                  key={item.renderJobId}
                  className="rounded-3xl border border-tavaura-ink/8 bg-white/95 p-4 shadow-tavaura-sm"
                >
                  <div className="flex items-start gap-4">
                    <RenderPreviewImage
                      garmentName={item.garmentName}
                      imageUrl={item.previewImageUrl}
                      className="h-20 w-20 rounded-2xl"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-tavaura-ink">
                            {item.garmentName}
                          </p>
                          <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                            Job ID: {item.renderJobId}
                          </p>
                        </div>
                        <StatusBadge status={item.status} />
                      </div>
                      <p className="mt-3 text-xs text-tavaura-ink/60">
                        Created {formatDate(item.createdAt)}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <RenderOutputButton item={item} />
                    <Link
                      href={`/admin/render-results/${item.renderJobId}`}
                      className="inline-flex cursor-pointer items-center rounded-full border border-tavaura-ink/12 bg-white px-3 py-1.5 text-xs font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
                    >
                      Open details
                    </Link>
                    <button
                      type="button"
                      onClick={() => void handleDelete(item)}
                      disabled={deletingId === item.renderJobId}
                      className="inline-flex cursor-pointer items-center gap-1 rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <Trash2 size={13} />
                      {deletingId === item.renderJobId ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
