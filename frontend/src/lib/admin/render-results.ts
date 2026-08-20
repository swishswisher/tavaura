import { authenticatedFetch } from "@/lib/api";

export type RenderResultStatus =
  | "completed"
  | "processing"
  | "failed"
  | "pending"
  | string;

export type RenderResultListItem = {
  renderJobId: string;
  renderResultId: string | null;
  garmentName: string;
  status: RenderResultStatus;
  errorMessage: string | null;
  outputImageUrl: string | null;
  previewImageUrl: string | null;
  createdAt: string;
};

export type RenderResultDetail = {
  renderJobId: string;
  status: RenderResultStatus;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  renderResultId: string;
  outputImageUrl: string;
  previewImageUrl: string;
  createdAt: string;
};

export async function listRenderResults(limit = 50) {
  const safeLimit = Number.isFinite(limit)
    ? Math.min(200, Math.max(1, Math.floor(limit)))
    : 50;
  return authenticatedFetch<RenderResultListItem[]>(`/api/render-results?limit=${safeLimit}`);
}

export async function getRenderResult(jobId: string) {
  return authenticatedFetch<RenderResultDetail>(`/api/render-results/${jobId}`);
}

export async function deleteRenderResult(jobId: string) {
  await authenticatedFetch<void>(`/api/render-results/${jobId}`, {
    method: "DELETE",
  });
}
