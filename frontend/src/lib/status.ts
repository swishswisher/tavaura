export type NormalizedIngestionStatus =
  | "processing"
  | "completed"
  | "failed"
  | "pending";

export function normalizeIngestionStatus(
  status: string | null | undefined
): NormalizedIngestionStatus {
  const normalized = status?.trim().toLowerCase();

  if (!normalized || normalized === "unknown") {
    return "pending";
  }

  if (
    normalized === "queued" ||
    normalized === "pending" ||
    normalized === "running" ||
    normalized === "in_progress" ||
    normalized === "processing"
  ) {
    return "processing";
  }

  if (normalized === "completed" || normalized === "success") {
    return "completed";
  }

  if (normalized === "failed" || normalized === "error") {
    return "failed";
  }

  return "pending";
}
