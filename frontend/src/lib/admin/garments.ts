import { authenticatedFetch, postJson } from "@/lib/api";

export type GarmentStatus = "ready" | "processing" | "failed" | "deleted" | string;

export type Garment = {
  id: string;
  tenantId: string;
  externalProductId: string;
  name: string;
  category: string;
  layer: string;
  sourceImageUrl: string;
  isActive: boolean;
  status: GarmentStatus;
  hasProcessedAsset: boolean;
  processedImageUrl: string | null;
  processedMaskUrl: string | null;
  processedTextureUrl: string | null;
  latestAssetCreatedAt: string | null;
  latestIngestionStatus: string | null;
  latestIngestionErrorMessage: string | null;
  createdAt: string;
  updatedAt: string;
};

export type CreateGarmentPayload = {
  externalProductId: string;
  name: string;
  category: string;
  layer: string;
  sourceImageUrl: string;
};

export async function listGarments() {
  return authenticatedFetch<Garment[]>("/api/garments");
}

export async function getGarment(garmentId: string) {
  return authenticatedFetch<Garment>(`/api/garments/${garmentId}`);
}

export async function createGarment(payload: CreateGarmentPayload) {
  return postJson<CreateGarmentPayload, Garment>("/api/garments", payload, {
    authenticated: true,
  });
}

export async function deleteGarment(garmentId: string) {
  await authenticatedFetch<void>(`/api/garments/${garmentId}`, {
    method: "DELETE",
  });
}

export async function retryGarmentIngestion(garmentId: string) {
  return postJson<{ garmentId: string }, { id: string; status: string }>(
    "/api/ingestion-jobs",
    { garmentId },
    { authenticated: true }
  );
}
