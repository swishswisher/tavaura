import { authenticatedFetch } from "@/lib/api";

export type IngestionJobStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "needs_review"
  | string;

export type IngestionJob = {
  id: string;
  garmentId: string | null;
  garmentName: string;
  externalProductId: string;
  status: IngestionJobStatus;
  attemptCount: number;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export async function listIngestionJobs() {
  return authenticatedFetch<IngestionJob[]>("/api/ingestion-jobs");
}
