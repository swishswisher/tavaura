"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, ExternalLink } from "lucide-react";
import { RenderPreviewImage } from "@/components/admin/RenderPreviewImage";
import {
  getRenderResult,
  type RenderResultDetail,
} from "@/lib/admin/render-results";

function formatDate(value: string | null) {
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

export default function AdminRenderResultDetailPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;

  const [result, setResult] = useState<RenderResultDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadResult() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getRenderResult(jobId);
        if (isMounted) {
          setResult(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load render result.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    if (jobId) {
      void loadResult();
    }

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3 rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
            Render center
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink">
            Render Result Detail
          </h1>
          <p className="mt-2 text-sm text-tavaura-ink/70">Render Job: {jobId}</p>
        </div>
        <Link
          href="/admin/render-results"
          className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-4 py-2 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
        >
          <ArrowLeft size={16} />
          Back to results
        </Link>
      </section>

      {isLoading ? (
        <section className="rounded-[2rem] border border-white/70 bg-white/80 p-10 text-center text-sm font-medium text-tavaura-ink/65 shadow-tavaura-sm backdrop-blur">
          Loading render result...
        </section>
      ) : error ? (
        <section className="flex items-start gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </section>
      ) : result ? (
        <section className="grid gap-5 rounded-[2rem] border border-white/70 bg-white/80 p-4 shadow-tavaura-sm backdrop-blur sm:p-5 lg:grid-cols-[minmax(0,1fr)_340px]">
          <article className="rounded-3xl border border-tavaura-ink/10 bg-white p-4 shadow-sm">
            <RenderPreviewImage
              garmentName="Render Preview"
              imageUrl={result.previewImageUrl}
              className="aspect-[4/5] h-auto w-full rounded-2xl"
            />
          </article>

          <article className="space-y-4 rounded-3xl border border-tavaura-ink/10 bg-white p-5 shadow-sm">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-tavaura-ink/55">
                Status
              </p>
              <span
                className={`mt-2 inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${getStatusClasses(
                  result.status
                )}`}
              >
                {getStatusLabel(result.status)}
              </span>
            </div>

            <dl className="space-y-3 text-sm text-tavaura-ink/75">
              <div>
                <dt className="text-xs uppercase tracking-[0.14em] text-tavaura-ink/50">
                  Created
                </dt>
                <dd className="mt-1">{formatDate(result.createdAt)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.14em] text-tavaura-ink/50">
                  Started
                </dt>
                <dd className="mt-1">{formatDate(result.startedAt)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.14em] text-tavaura-ink/50">
                  Completed
                </dt>
                <dd className="mt-1">{formatDate(result.completedAt)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.14em] text-tavaura-ink/50">
                  Render Result ID
                </dt>
                <dd className="mt-1 break-all text-xs text-tavaura-ink/65">
                  {result.renderResultId}
                </dd>
              </div>
            </dl>

            {result.errorMessage && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
                {result.errorMessage}
              </div>
            )}

            <a
              href={result.outputImageUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-tavaura-ink px-4 py-2 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
            >
              Open output image
              <ExternalLink size={16} />
            </a>
          </article>
        </section>
      ) : null}
    </div>
  );
}
