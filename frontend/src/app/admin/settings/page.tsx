"use client";

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  Globe,
  KeyRound,
  Mail,
  RefreshCw,
  ShieldCheck,
  Store,
  Trash2,
  UploadCloud,
} from "lucide-react";
import {
  changeAdminPassword,
  getAdminSettings,
  regenerateAdminApiKey,
  requestWorkspaceDeletion,
  signOutOtherAdminSessions,
  updateAdminBrandProfile,
  updateAdminWebhookUrl,
  uploadAdminLogo,
  type AdminUsagePlan,
} from "@/lib/admin/settings";
import { saveToken } from "@/lib/auth";

type BrandProfile = {
  brandName: string;
  supportEmail: string;
  websiteUrl: string;
};

type BrandErrors = Partial<Record<keyof BrandProfile, string>>;

const initialBrandProfile: BrandProfile = {
  brandName: "",
  supportEmail: "",
  websiteUrl: "",
};

const initialUsagePlan: AdminUsagePlan = {
  garmentsProcessedThisMonth: 0,
  rendersThisMonth: 0,
  currentPlan: "",
  usageRemaining: 0,
};

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isValidHttpUrl(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function buildSdkSnippet(apiKey: string) {
  return `<script src="https://cdn.tavaura.com/sdk/v1/tavaura.min.js"></script>
<script>
  window.Tavaura.init({
    apiKey: "${apiKey}",
    merchantId: "your-merchant-id",
    environment: "production"
  });
</script>`;
}

function statusMessageClasses(tone: "success" | "error") {
  if (tone === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }

  return "border-rose-200 bg-rose-50 text-rose-700";
}

function StatusMessage({
  message,
  tone,
}: {
  message: string | null;
  tone: "success" | "error";
}) {
  if (!message) {
    return null;
  }

  return (
    <div
      className={`flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${statusMessageClasses(
        tone
      )}`}
    >
      {tone === "success" ? (
        <CheckCircle2 size={18} className="mt-0.5 flex-shrink-0" />
      ) : (
        <AlertTriangle size={18} className="mt-0.5 flex-shrink-0" />
      )}
      <span>{message}</span>
    </div>
  );
}

export default function AdminSettingsPage() {
  const logoInputRef = useRef<HTMLInputElement>(null);
  const [brandProfile, setBrandProfile] = useState<BrandProfile>(initialBrandProfile);
  const [brandErrors, setBrandErrors] = useState<BrandErrors>({});
  const [brandSuccess, setBrandSuccess] = useState<string | null>(null);
  const [brandError, setBrandError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingBrand, setIsSavingBrand] = useState(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);

  const [apiKey, setApiKey] = useState("");
  const [isApiKeyVisible, setIsApiKeyVisible] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [integrationSuccess, setIntegrationSuccess] = useState<string | null>(null);
  const [integrationError, setIntegrationError] = useState<string | null>(null);
  const [isSavingWebhook, setIsSavingWebhook] = useState(false);
  const [isRegeneratingApiKey, setIsRegeneratingApiKey] = useState(false);

  const [usagePlan, setUsagePlan] = useState<AdminUsagePlan>(initialUsagePlan);

  const [securitySuccess, setSecuritySuccess] = useState<string | null>(null);
  const [securityError, setSecurityError] = useState<string | null>(null);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isSigningOutSessions, setIsSigningOutSessions] = useState(false);

  const [dangerSuccess, setDangerSuccess] = useState<string | null>(null);
  const [dangerError, setDangerError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isRequestingDeletion, setIsRequestingDeletion] = useState(false);

  const sdkSnippet = useMemo(() => buildSdkSnippet(apiKey), [apiKey]);
  const maskedApiKey = useMemo(() => {
    if (apiKey.length <= 8) {
      return apiKey || "Loading...";
    }

    return `${apiKey.slice(0, 7)}${"*".repeat(Math.max(8, apiKey.length - 11))}${apiKey.slice(
      -4
    )}`;
  }, [apiKey]);

  const usageCards = [
    {
      label: "Garments Processed This Month",
      value: isLoading ? "--" : usagePlan.garmentsProcessedThisMonth.toLocaleString(),
      helper: "Assets prepared in current billing cycle",
    },
    {
      label: "Renders This Month",
      value: isLoading ? "--" : usagePlan.rendersThisMonth.toLocaleString(),
      helper: "Try-on outputs generated this month",
    },
    {
      label: "Current Plan",
      value: isLoading || !usagePlan.currentPlan ? "--" : usagePlan.currentPlan,
      helper: "Up to 2,000 renders per month",
    },
    {
      label: "Usage Remaining",
      value: isLoading ? "--" : usagePlan.usageRemaining.toLocaleString(),
      helper: "Before next plan cycle reset",
    },
  ];

  useEffect(() => {
    let isMounted = true;

    async function loadSettings() {
      setIsLoading(true);
      setBrandError(null);
      setIntegrationError(null);

      try {
        const settings = await getAdminSettings();
        if (!isMounted) {
          return;
        }

        setBrandProfile({
          brandName: settings.brandProfile.brandName,
          supportEmail: settings.brandProfile.supportEmail,
          websiteUrl: settings.brandProfile.websiteUrl,
        });
        setApiKey(settings.integration.apiKey);
        setWebhookUrl(settings.integration.webhookUrl);
        setUsagePlan(settings.usage);
      } catch (err) {
        if (!isMounted) {
          return;
        }

        const message = err instanceof Error ? err.message : "Unable to load settings.";
        setBrandError(message);
        setIntegrationError(message);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  const clearBrandNotices = () => {
    setBrandSuccess(null);
    setBrandError(null);
  };

  const clearIntegrationNotices = () => {
    setIntegrationSuccess(null);
    setIntegrationError(null);
  };

  const clearSecurityNotices = () => {
    setSecuritySuccess(null);
    setSecurityError(null);
  };

  const handleBrandSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearBrandNotices();

    const nextProfile = {
      brandName: brandProfile.brandName.trim(),
      supportEmail: brandProfile.supportEmail.trim(),
      websiteUrl: brandProfile.websiteUrl.trim(),
    };

    const errors: BrandErrors = {};

    if (!nextProfile.brandName) {
      errors.brandName = "Brand name is required.";
    }

    if (!nextProfile.supportEmail) {
      errors.supportEmail = "Support email is required.";
    } else if (!isValidEmail(nextProfile.supportEmail)) {
      errors.supportEmail = "Enter a valid email address.";
    }

    if (!nextProfile.websiteUrl) {
      errors.websiteUrl = "Website URL is required.";
    } else if (!isValidHttpUrl(nextProfile.websiteUrl)) {
      errors.websiteUrl = "Enter a valid website URL.";
    }

    setBrandErrors(errors);

    if (Object.keys(errors).length > 0) {
      setBrandError("Please resolve the highlighted fields and try again.");
      return;
    }

    setIsSavingBrand(true);

    try {
      const settings = await updateAdminBrandProfile(nextProfile);
      setBrandProfile({
        brandName: settings.brandProfile.brandName,
        supportEmail: settings.brandProfile.supportEmail,
        websiteUrl: settings.brandProfile.websiteUrl,
      });
      setUsagePlan(settings.usage);
      setBrandSuccess("Brand profile saved successfully.");
    } catch (err) {
      setBrandError(err instanceof Error ? err.message : "Unable to save brand profile.");
    } finally {
      setIsSavingBrand(false);
    }
  };

  const updateBrandField = (field: keyof BrandProfile, value: string) => {
    setBrandProfile((current) => ({ ...current, [field]: value }));
    setBrandErrors((current) => ({ ...current, [field]: undefined }));
    clearBrandNotices();
  };

  const handleLogoUploadClick = () => {
    clearBrandNotices();
    logoInputRef.current?.click();
  };

  const handleLogoFileChange = async (file: File | undefined) => {
    if (!file) {
      return;
    }

    clearBrandNotices();
    setIsUploadingLogo(true);

    try {
      await uploadAdminLogo(file);
      setBrandSuccess("Logo uploaded successfully.");
    } catch (err) {
      setBrandError(err instanceof Error ? err.message : "Unable to upload logo.");
    } finally {
      setIsUploadingLogo(false);
      if (logoInputRef.current) {
        logoInputRef.current.value = "";
      }
    }
  };

  const copyToClipboard = async (value: string, successMessage: string) => {
    try {
      if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) {
        throw new Error("Clipboard API unavailable.");
      }

      await navigator.clipboard.writeText(value);
      clearIntegrationNotices();
      setIntegrationSuccess(successMessage);
    } catch {
      clearIntegrationNotices();
      setIntegrationError("Unable to copy right now. Please copy manually.");
    }
  };

  const handleRegenerateApiKey = async () => {
    clearIntegrationNotices();
    setIsRegeneratingApiKey(true);

    try {
      const settings = await regenerateAdminApiKey();
      setApiKey(settings.integration.apiKey);
      setIntegrationSuccess("API key regenerated. Update connected clients immediately.");
    } catch (err) {
      setIntegrationError(err instanceof Error ? err.message : "Unable to regenerate API key.");
    } finally {
      setIsRegeneratingApiKey(false);
    }
  };

  const handleSaveWebhook = async () => {
    clearIntegrationNotices();

    if (!webhookUrl.trim()) {
      setIntegrationError("Webhook URL is required.");
      return;
    }

    if (!isValidHttpUrl(webhookUrl.trim())) {
      setIntegrationError("Enter a valid webhook URL.");
      return;
    }

    setIsSavingWebhook(true);

    try {
      const settings = await updateAdminWebhookUrl(webhookUrl.trim());
      setWebhookUrl(settings.integration.webhookUrl);
      setIntegrationSuccess("Webhook URL saved.");
    } catch (err) {
      setIntegrationError(err instanceof Error ? err.message : "Unable to save webhook URL.");
    } finally {
      setIsSavingWebhook(false);
    }
  };

  const handleChangePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearSecurityNotices();

    if (!currentPassword || !newPassword) {
      setSecurityError("Current password and new password are required.");
      return;
    }

    if (newPassword.length < 8) {
      setSecurityError("New password must be at least 8 characters.");
      return;
    }

    setIsChangingPassword(true);

    try {
      const response = await changeAdminPassword({ currentPassword, newPassword });
      saveToken(response.accessToken);
      setCurrentPassword("");
      setNewPassword("");
      setIsPasswordModalOpen(false);
      setSecuritySuccess("Password changed successfully.");
    } catch (err) {
      setSecurityError(err instanceof Error ? err.message : "Unable to change password.");
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleSignOutOtherSessions = async () => {
    clearSecurityNotices();
    setIsSigningOutSessions(true);

    try {
      const response = await signOutOtherAdminSessions();
      saveToken(response.accessToken);
      setSecuritySuccess("Other sessions have been signed out.");
    } catch (err) {
      setSecurityError(err instanceof Error ? err.message : "Unable to sign out other sessions.");
    } finally {
      setIsSigningOutSessions(false);
    }
  };

  const handleDeleteWorkspaceConfirm = async () => {
    setDangerSuccess(null);
    setDangerError(null);
    setIsRequestingDeletion(true);

    try {
      const response = await requestWorkspaceDeletion();
      setDangerSuccess(response.message);
      setIsDeleteModalOpen(false);
    } catch (err) {
      setDangerError(err instanceof Error ? err.message : "Unable to request workspace deletion.");
    } finally {
      setIsRequestingDeletion(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
          Settings
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink sm:text-4xl">
          Merchant Settings
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-tavaura-ink/70 sm:text-base">
          Manage your workspace, branding, integrations, and security.
        </p>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur sm:p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
            <Store size={18} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-tavaura-ink">Brand Profile</h2>
            <p className="text-sm text-tavaura-ink/60">
              Keep merchant identity and support details up to date.
            </p>
          </div>
        </div>

        <form onSubmit={handleBrandSave} className="mt-6 space-y-5">
          <div className="grid gap-4 lg:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-tavaura-ink">Store / Brand Name</span>
              <input
                value={brandProfile.brandName}
                onChange={(event) => updateBrandField("brandName", event.target.value)}
                aria-invalid={Boolean(brandErrors.brandName)}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-rose-100"
                placeholder="Tavaura Studio"
              />
              {brandErrors.brandName && (
                <p className="text-xs font-medium text-rose-700">{brandErrors.brandName}</p>
              )}
            </label>

            <label className="space-y-2">
              <span className="flex items-center gap-2 text-sm font-medium text-tavaura-ink">
                <Mail size={14} />
                Support Email
              </span>
              <input
                type="email"
                value={brandProfile.supportEmail}
                onChange={(event) => updateBrandField("supportEmail", event.target.value)}
                aria-invalid={Boolean(brandErrors.supportEmail)}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-rose-100"
                placeholder="support@yourbrand.com"
              />
              {brandErrors.supportEmail && (
                <p className="text-xs font-medium text-rose-700">{brandErrors.supportEmail}</p>
              )}
            </label>

            <label className="space-y-2 lg:col-span-2">
              <span className="flex items-center gap-2 text-sm font-medium text-tavaura-ink">
                <Globe size={14} />
                Website URL
              </span>
              <input
                type="url"
                value={brandProfile.websiteUrl}
                onChange={(event) => updateBrandField("websiteUrl", event.target.value)}
                aria-invalid={Boolean(brandErrors.websiteUrl)}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-rose-100"
                placeholder="https://www.yourbrand.com"
              />
              {brandErrors.websiteUrl && (
                <p className="text-xs font-medium text-rose-700">{brandErrors.websiteUrl}</p>
              )}
            </label>
          </div>

          <div className="rounded-2xl border border-dashed border-tavaura-ink/20 bg-tavaura-bg/70 p-5">
            <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <p className="text-sm font-semibold text-tavaura-ink">Logo Upload</p>
                <p className="mt-1 text-xs text-tavaura-ink/60">
                  Upload a square logo for merchant profile surfaces.
                </p>
              </div>
              <input
                ref={logoInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event) => void handleLogoFileChange(event.target.files?.[0])}
              />
              <button
                type="button"
                onClick={handleLogoUploadClick}
                disabled={isUploadingLogo}
                className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-4 py-2 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <UploadCloud size={16} />
                {isUploadingLogo ? "Uploading..." : "Upload Logo"}
              </button>
            </div>
          </div>

          <StatusMessage message={brandError} tone="error" />
          <StatusMessage message={brandSuccess} tone="success" />

          <button
            type="submit"
            disabled={isSavingBrand}
            className="inline-flex cursor-pointer items-center justify-center rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSavingBrand ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur sm:p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
            <KeyRound size={18} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-tavaura-ink">Integrations</h2>
            <p className="text-sm text-tavaura-ink/60">
              Manage API credentials and webhook endpoints.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-5">
          <div className="space-y-2">
            <span className="text-sm font-medium text-tavaura-ink">API Key</span>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                readOnly
                value={isApiKeyVisible ? apiKey : maskedApiKey}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 font-mono text-sm text-tavaura-ink shadow-sm"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsApiKeyVisible((current) => !current)}
                  className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-4 py-2 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
                >
                  {isApiKeyVisible ? <EyeOff size={15} /> : <Eye size={15} />}
                  {isApiKeyVisible ? "Hide" : "Reveal"}
                </button>
                <button
                  type="button"
                  onClick={() => void copyToClipboard(apiKey, "API key copied.")}
                  className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-4 py-2 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
                >
                  <Copy size={15} />
                  Copy
                </button>
              </div>
            </div>
          </div>

          <label className="space-y-2">
            <span className="text-sm font-medium text-tavaura-ink">Webhook URL</span>
            <input
              type="url"
              value={webhookUrl}
              onChange={(event) => {
                setWebhookUrl(event.target.value);
                clearIntegrationNotices();
              }}
              className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
              placeholder="https://merchant.example.com/webhooks/tavaura"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-tavaura-ink">SDK Install Snippet</span>
            <textarea
              readOnly
              value={sdkSnippet}
              className="min-h-32 w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 font-mono text-xs text-tavaura-ink shadow-sm"
            />
          </label>

          <StatusMessage message={integrationError} tone="error" />
          <StatusMessage message={integrationSuccess} tone="success" />

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <button
              type="button"
              onClick={() => void handleRegenerateApiKey()}
              disabled={isRegeneratingApiKey}
              className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full border border-tavaura-ink/12 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCw size={15} />
              {isRegeneratingApiKey ? "Regenerating..." : "Regenerate API Key"}
            </button>
            <button
              type="button"
              onClick={() => void copyToClipboard(sdkSnippet, "SDK snippet copied.")}
              className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
            >
              <Copy size={15} />
              Copy Snippet
            </button>
            <button
              type="button"
              onClick={() => void handleSaveWebhook()}
              disabled={isSavingWebhook}
              className="inline-flex cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/12 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSavingWebhook ? "Saving..." : "Save Webhook URL"}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur sm:p-6">
        <h2 className="text-lg font-semibold text-tavaura-ink">Usage &amp; Plan</h2>
        <p className="mt-1 text-sm text-tavaura-ink/60">
          Track monthly usage and plan limits at a glance.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {usageCards.map((card) => (
            <article
              key={card.label}
              className="rounded-3xl border border-white/70 bg-white/90 p-5 shadow-tavaura-sm"
            >
              <p className="text-sm font-medium text-tavaura-ink/70">{card.label}</p>
              <p className="mt-3 text-3xl font-semibold tracking-tight text-tavaura-ink">
                {card.value}
              </p>
              <p className="mt-3 text-xs leading-5 text-tavaura-ink/60">{card.helper}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-tavaura-sm backdrop-blur sm:p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tavaura-ink/10 text-tavaura-ink">
            <ShieldCheck size={18} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-tavaura-ink">Security</h2>
            <p className="text-sm text-tavaura-ink/60">Protect account access and active sessions.</p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <button
            type="button"
            onClick={() => {
              clearSecurityNotices();
              setIsPasswordModalOpen(true);
            }}
            className="inline-flex cursor-pointer items-center justify-center rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
          >
            Change Password
          </button>
          <button
            type="button"
            onClick={() => void handleSignOutOtherSessions()}
            disabled={isSigningOutSessions}
            className="inline-flex cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/12 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSigningOutSessions ? "Signing out..." : "Sign Out Other Sessions"}
          </button>
        </div>

        <div className="mt-4">
          <StatusMessage message={securityError} tone="error" />
          <StatusMessage message={securitySuccess} tone="success" />
        </div>
      </section>

      <section className="rounded-3xl border border-rose-200/80 bg-rose-50/80 p-5 shadow-tavaura-sm backdrop-blur sm:p-6">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-rose-100 text-rose-700">
            <AlertTriangle size={18} />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-rose-700">Danger Zone</h2>
            <p className="mt-1 text-sm text-rose-700/80">
              Deleting a workspace is irreversible and removes access to linked resources.
            </p>
            {dangerSuccess && (
              <p className="mt-3 rounded-xl border border-rose-200 bg-white/70 px-3 py-2 text-xs text-rose-700">
                {dangerSuccess}
              </p>
            )}
            {dangerError && (
              <p className="mt-3 rounded-xl border border-rose-200 bg-white/70 px-3 py-2 text-xs text-rose-700">
                {dangerError}
              </p>
            )}
            <button
              type="button"
              onClick={() => {
                setDangerError(null);
                setIsDeleteModalOpen(true);
              }}
              className="mt-4 inline-flex cursor-pointer items-center justify-center gap-2 rounded-full border border-rose-300 bg-white px-5 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
            >
              <Trash2 size={15} />
              Delete Workspace
            </button>
          </div>
        </div>
      </section>

      {isPasswordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-tavaura-ink/50 px-4 backdrop-blur-sm">
          <form
            onSubmit={(event) => void handleChangePassword(event)}
            className="w-full max-w-md rounded-3xl border border-white/60 bg-white/95 p-6 shadow-2xl shadow-tavaura-ink/25"
          >
            <h3 className="text-xl font-semibold text-tavaura-ink">Change Password</h3>
            <p className="mt-2 text-sm leading-6 text-tavaura-ink/70">
              Update your merchant admin password and refresh this session.
            </p>

            <div className="mt-5 space-y-4">
              <label className="space-y-2">
                <span className="text-sm font-medium text-tavaura-ink">Current Password</span>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
                />
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-tavaura-ink">New Password</span>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
                />
              </label>
            </div>

            <div className="mt-4">
              <StatusMessage message={securityError} tone="error" />
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => {
                  setCurrentPassword("");
                  setNewPassword("");
                  setIsPasswordModalOpen(false);
                }}
                className="inline-flex cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/12 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isChangingPassword}
                className="inline-flex cursor-pointer items-center justify-center rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isChangingPassword ? "Saving..." : "Save Password"}
              </button>
            </div>
          </form>
        </div>
      )}

      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-tavaura-ink/50 px-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl border border-white/60 bg-white/95 p-6 shadow-2xl shadow-tavaura-ink/25">
            <h3 className="text-xl font-semibold text-tavaura-ink">Confirm Workspace Deletion</h3>
            <p className="mt-2 text-sm leading-6 text-tavaura-ink/70">
              This records a tenant-scoped workspace deletion request for backend processing.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                className="inline-flex cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/12 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleDeleteWorkspaceConfirm()}
                disabled={isRequestingDeletion}
                className="inline-flex cursor-pointer items-center justify-center rounded-full bg-rose-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isRequestingDeletion ? "Requesting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
