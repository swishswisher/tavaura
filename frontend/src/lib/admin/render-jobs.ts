import { postJson } from "@/lib/api";

export type CreateRenderJobPayload = {
  garmentId: string;
  avatarImageUrl?: string;
};

export type RenderJobResponse = {
  id: string;
  tenantId: string;
  avatarId: string;
  garmentId: string;
  garmentAssetId: string;
  assetVersionId: string;
  status: string;
  attemptCount: number;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export async function createRenderJob(payload: CreateRenderJobPayload) {
  return postJson<CreateRenderJobPayload, RenderJobResponse>(
    "/api/admin/render-jobs",
    payload,
    { authenticated: true }
  );
}
