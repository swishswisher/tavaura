"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Clock3,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import { GarmentImage } from "@/components/admin/GarmentImage";
import {
  deleteGarment,
  getGarment,
  retryGarmentIngestion,
  type Garment,
} from "@/lib/admin/garments";
import { createRenderJob } from "@/lib/admin/render-jobs";

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function statusClasses(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "ready") return "bg-emerald-50 text-emerald-700 ring-emerald-200/80";
  if (normalizedStatus === "processing") return "bg-amber-50 text-amber-700 ring-amber-200/80";
  if (normalizedStatus === "failed") return "bg-rose-50 text-rose-700 ring-rose-200/80";
  return "bg-slate-100 text-slate-600 ring-slate-200/80";
}

function statusLabel(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "ready") return "Ready";
  if (normalizedStatus === "processing") return "Processing";
  if (normalizedStatus === "failed") return "Failed";
  if (normalizedStatus === "draft") return "Draft";
  if (normalizedStatus === "pending") return "Pending";
  return status || "Pending";
}

export default function GarmentDetailPage() {
  const router = useRouter();
  const params = useParams<{ garmentId: string }>();
  const garmentId = params.garmentId;
  const [garment, setGarment] = useState<Garment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadGarment() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getGarment(garmentId);
        if (isMounted) {
          setGarment(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load garment.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadGarment();

    return () => {
      isMounted = false;
    };
  }, [garmentId]);

  const handleRetry = async () => {
    setIsRetrying(true);
    setError(null);
    setNotice(null);
    try {
      await retryGarmentIngestion(garmentId);
      setNotice("Asset rebuild was queued.");
      const updated = await getGarment(garmentId);
      setGarment(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to rebuild asset.");
    } finally {
      setIsRetrying(false);
    }
  };

  const handleCreateRender = async () => {
    if (!garment) {
      return;
    }

    setIsRendering(true);
    setError(null);
    setNotice(null);
    try {
      await createRenderJob({ garmentId: garment.id });
      setNotice("Render queued.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to queue render.");
    } finally {
      setIsRendering(false);
    }
  };

  const handleDelete = async () => {
    if (!garment) {
      return;
    }

    const confirmed = window.confirm("Delete this garment?");
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await deleteGarment(garment.id);
      router.replace("/admin/garments");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete garment.");
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href="/admin/garments"
        className="inline-flex items-center gap-2 rounded-full border border-tavaura-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-tavaura-ink shadow-sm transition hover:bg-white"
      >
        <ArrowLeft size={16} />
        Garments
      </Link>

      {error && (
        <div className="flex items-start gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
          <span>{notice}</span>
          {notice === "Render queued." && (
            <Link
              href="/admin/renders"
              className="inline-flex cursor-pointer items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-emerald-800 shadow-sm transition hover:bg-emerald-100"
            >
              View renders
            </Link>
          )}
        </div>
      )}

      {isLoading ? (
        <section className="rounded-[2rem] border border-white/70 bg-white/80 px-5 py-14 text-center text-sm font-medium text-tavaura-ink/65 shadow-tavaura backdrop-blur-xl">
          Loading garment...
        </section>
      ) : garment ? (
        <>
          <section className="grid gap-6 rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl lg:grid-cols-[380px_minmax(0,1fr)] lg:p-7">
            <GarmentImage
              name={garment.name}
              imageUrl={garment.sourceImageUrl}
              className="aspect-[4/5] w-full rounded-3xl shadow-tavaura-sm"
              iconClassName="h-8 w-8"
              initialsClassName="text-lg"
            />

            <div className="space-y-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
                    Garment detail
                  </p>
                  <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink">
                    {garment.name}
                  </h1>
                  <p className="mt-2 text-sm text-tavaura-ink/65">
                    Product ID (SKU) {garment.externalProductId}
                  </p>
                </div>
                <span
                  className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${statusClasses(garment.status)}`}
                >
                  {statusLabel(garment.status)}
                </span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-tavaura-ink/8 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/50">
                    Category
                  </p>
                  <p className="mt-1 text-sm font-semibold text-tavaura-ink">{garment.category}</p>
                </div>
                <div className="rounded-2xl border border-tavaura-ink/8 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/50">
                    Layer
                  </p>
                  <p className="mt-1 text-sm font-semibold text-tavaura-ink">{garment.layer}</p>
                </div>
                <div className="rounded-2xl border border-tavaura-ink/8 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/50">
                    Created
                  </p>
                  <p className="mt-1 text-sm font-semibold text-tavaura-ink">
                    {formatDateTime(garment.createdAt)}
                  </p>
                </div>
                <div className="rounded-2xl border border-tavaura-ink/8 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/50">
                    Updated
                  </p>
                  <p className="mt-1 text-sm font-semibold text-tavaura-ink">
                    {formatDateTime(garment.updatedAt)}
                  </p>
                </div>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="button"
                  onClick={() => void handleCreateRender()}
                  disabled={isRendering || !garment.processedImageUrl}
                  className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  <Sparkles size={17} />
                  {isRendering ? "Queueing render..." : "Create Try-On Render"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleRetry()}
                  disabled={isRetrying}
                  className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  <RefreshCw size={17} />
                  {isRetrying ? "Queueing..." : "Rebuild Asset"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleDelete()}
                  disabled={isDeleting}
                  className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-5 py-3 text-sm font-semibold text-rose-700 shadow-sm transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  <Trash2 size={17} />
                  {isDeleting ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
                  <ShieldCheck size={19} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-tavaura-ink">
                    Processed asset readiness
                  </h2>
                  <p className="text-sm text-tavaura-ink/60">
                    Derived from the latest garment asset.
                  </p>
                </div>
              </div>

              <div className="mt-5 space-y-3">
                <div className="flex items-center justify-between rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3">
                  <span className="text-sm font-medium text-tavaura-ink">Processed image</span>
                  <span className={garment.processedImageUrl ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-amber-700"}>
                    {garment.processedImageUrl ? "Ready" : "Pending"}
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3">
                  <span className="text-sm font-medium text-tavaura-ink">Mask</span>
                  <span className={garment.processedMaskUrl ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-amber-700"}>
                    {garment.processedMaskUrl ? "Ready" : "Pending"}
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3">
                  <span className="text-sm font-medium text-tavaura-ink">Texture</span>
                  <span className={garment.processedTextureUrl ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-amber-700"}>
                    {garment.processedTextureUrl ? "Ready" : "Pending"}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
                  <Clock3 size={19} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-tavaura-ink">Ingestion history</h2>
                  <p className="text-sm text-tavaura-ink/60">
                    Latest job status for this Product ID (SKU).
                  </p>
                </div>
              </div>
              <div className="mt-5 rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-4">
                <p className="text-sm font-semibold text-tavaura-ink">
                  {garment.latestIngestionStatus ?? "No ingestion job yet"}
                </p>
                <p className="mt-2 text-xs leading-5 text-tavaura-ink/60">
                  {garment.latestIngestionErrorMessage ??
                    (garment.latestAssetCreatedAt
                      ? `Latest asset created ${formatDateTime(garment.latestAssetCreatedAt)}.`
                      : "Queue ingestion when you are ready to process this garment.")}
                </p>
              </div>
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-[2rem] border border-white/70 bg-white/80 px-5 py-14 text-center shadow-tavaura backdrop-blur-xl">
          <p className="text-sm font-semibold text-tavaura-ink">Garment not found</p>
          <p className="mt-2 text-xs text-tavaura-ink/60">
            This garment may have been deleted or belongs to another tenant.
          </p>
        </section>
      )}
    </div>
  );
}
