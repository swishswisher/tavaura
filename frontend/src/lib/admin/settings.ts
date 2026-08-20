import { authenticatedFetch } from "@/lib/api";

export type AdminBrandProfile = {
  brandName: string;
  supportEmail: string;
  websiteUrl: string;
  logoUrl: string | null;
};

export type AdminIntegrationSettings = {
  apiKey: string;
  webhookUrl: string;
};

export type AdminUsagePlan = {
  garmentsProcessedThisMonth: number;
  rendersThisMonth: number;
  currentPlan: string;
  usageRemaining: number;
};

export type AdminSettingsResponse = {
  brandProfile: AdminBrandProfile;
  integration: AdminIntegrationSettings;
  usage: AdminUsagePlan;
};

export type LoginResponse = {
  accessToken: string;
  tokenType: string;
  expiresAtUtc: string;
  role: string;
  tenantId: string | null;
  userId: string;
  email: string;
};

function jsonHeaders() {
  return {
    "Content-Type": "application/json",
  };
}

export async function getAdminSettings() {
  return authenticatedFetch<AdminSettingsResponse>("/api/admin/settings");
}

export async function updateAdminBrandProfile(payload: {
  brandName: string;
  supportEmail: string;
  websiteUrl: string;
}) {
  return authenticatedFetch<AdminSettingsResponse>("/api/admin/settings/brand", {
    method: "PATCH",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
}

export async function uploadAdminLogo(file: File) {
  const formData = new FormData();
  formData.append("logo", file);

  return authenticatedFetch<AdminSettingsResponse>("/api/admin/settings/logo", {
    method: "POST",
    body: formData,
  });
}

export async function updateAdminWebhookUrl(webhookUrl: string) {
  return authenticatedFetch<AdminSettingsResponse>("/api/admin/settings/webhook", {
    method: "PUT",
    headers: jsonHeaders(),
    body: JSON.stringify({ webhookUrl }),
  });
}

export async function regenerateAdminApiKey() {
  return authenticatedFetch<AdminSettingsResponse>("/api/admin/settings/api-key/regenerate", {
    method: "POST",
  });
}

export async function changeAdminPassword(payload: {
  currentPassword: string;
  newPassword: string;
}) {
  return authenticatedFetch<LoginResponse>("/api/admin/settings/password", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
}

export async function signOutOtherAdminSessions() {
  return authenticatedFetch<LoginResponse>("/api/admin/settings/sessions/sign-out-others", {
    method: "POST",
  });
}

export async function requestWorkspaceDeletion() {
  return authenticatedFetch<{ message: string; status: string }>(
    "/api/admin/settings/workspace/delete-request",
    {
      method: "POST",
    }
  );
}
