"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { AlertCircle, ArrowLeft, CheckCircle2, PackagePlus } from "lucide-react";
import {
  createGarment,
  retryGarmentIngestion,
  type CreateGarmentPayload,
} from "@/lib/admin/garments";

const categoryOptions = [
  "hoodie",
  "shirt",
  "pants",
  "dress",
  "shoes",
  "jacket",
  "cosmetics",
  "other",
];

const layerOptions = ["innerwear", "upper", "outerwear", "full-body", "accessory"];

const initialForm: CreateGarmentPayload = {
  externalProductId: "",
  name: "",
  category: "",
  layer: "",
  sourceImageUrl: "",
};

type FormErrors = Partial<Record<keyof CreateGarmentPayload, string>>;

function RequiredMark() {
  return <span className="text-rose-600">*</span>;
}

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return <p className="text-xs font-medium text-rose-700">{message}</p>;
}

function isValidHttpUrl(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function validateForm(payload: CreateGarmentPayload) {
  const errors: FormErrors = {};

  if (!payload.name) {
    errors.name = "Garment name is required.";
  }

  if (!payload.externalProductId) {
    errors.externalProductId = "Product ID is required.";
  }

  if (!payload.category) {
    errors.category = "Choose a category.";
  }

  if (!payload.layer) {
    errors.layer = "Choose a layer.";
  }

  if (!payload.sourceImageUrl) {
    errors.sourceImageUrl = "Source image URL is required.";
  } else if (!isValidHttpUrl(payload.sourceImageUrl)) {
    errors.sourceImageUrl = "Enter a valid image URL.";
  }

  return errors;
}

export default function NewGarmentPage() {
  const router = useRouter();
  const [form, setForm] = useState<CreateGarmentPayload>(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const updateField = (field: keyof CreateGarmentPayload, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const payload: CreateGarmentPayload = {
      externalProductId: form.externalProductId.trim(),
      name: form.name.trim(),
      category: form.category.trim(),
      layer: form.layer.trim(),
      sourceImageUrl: form.sourceImageUrl.trim(),
    };

    const nextErrors = validateForm(payload);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const garment = await createGarment(payload);
      await retryGarmentIngestion(garment.id);
      setSuccess("Garment created successfully. Processing has started.");
      window.setTimeout(() => {
        router.replace(`/admin/garments/${garment.id}`);
      }, 900);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create garment.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href="/admin/garments"
        className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-tavaura-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-tavaura-ink shadow-sm transition hover:bg-white"
      >
        <ArrowLeft size={16} />
        Garments
      </Link>

      <section className="rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-7">
        <div className="max-w-2xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
            New catalog asset
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-tavaura-ink">
            Add garment
          </h1>
          <p className="text-sm leading-6 text-tavaura-ink/70">
            Create a catalog item and start processing it for try-on readiness.
          </p>
        </div>

        {success && (
          <div className="mt-6 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 size={18} className="mt-0.5 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {error && (
          <div className="mt-6 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 max-w-5xl space-y-6">
          <div className="grid gap-5 xl:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-tavaura-ink">
                Garment Name <RequiredMark />
              </span>
              <input
                value={form.name}
                onChange={(event) => updateField("name", event.target.value)}
                aria-invalid={Boolean(errors.name)}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-rose-100"
                placeholder="Black Hoodie"
              />
              <FieldError message={errors.name} />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-tavaura-ink">
                Product ID <RequiredMark />
              </span>
              <input
                value={form.externalProductId}
                onChange={(event) => updateField("externalProductId", event.target.value)}
                aria-invalid={Boolean(errors.externalProductId)}
                className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-rose-100"
                placeholder="sku-500"
              />
              <p className="text-xs leading-5 text-tavaura-ink/55">
                Unique product identifier used for syncing inventory.
              </p>
              <FieldError message={errors.externalProductId} />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-tavaura-ink">
                Category <RequiredMark />
              </span>
              <select
                value={form.category}
                onChange={(event) => updateField("category", event.target.value)}
                aria-invalid={Boolean(errors.category)}
                className="w-full cursor-pointer rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-rose-100"
              >
                <option value="">Select category</option>
                {categoryOptions.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
              <FieldError message={errors.category} />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-tavaura-ink">
                Layer <RequiredMark />
              </span>
              <select
                value={form.layer}
                onChange={(event) => updateField("layer", event.target.value)}
                aria-invalid={Boolean(errors.layer)}
                className="w-full cursor-pointer rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-rose-100"
              >
                <option value="">Select layer</option>
                {layerOptions.map((layer) => (
                  <option key={layer} value={layer}>
                    {layer}
                  </option>
                ))}
              </select>
              <FieldError message={errors.layer} />
            </label>
          </div>

          <label className="block max-w-5xl space-y-2">
            <span className="text-sm font-medium text-tavaura-ink">
              Source Image URL <RequiredMark />
            </span>
            <input
              type="url"
              value={form.sourceImageUrl}
              onChange={(event) => updateField("sourceImageUrl", event.target.value)}
              aria-invalid={Boolean(errors.sourceImageUrl)}
              className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10 aria-[invalid=true]:border-rose-300 aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-rose-100"
              placeholder="https://example.com/product.png"
            />
            <FieldError message={errors.sourceImageUrl} />
          </label>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-65"
            >
              <PackagePlus size={17} />
              {isSubmitting ? "Creating garment..." : "Create Garment"}
            </button>
            <Link
              href="/admin/garments"
              className="inline-flex cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/10 bg-white px-5 py-3 text-sm font-semibold text-tavaura-ink shadow-sm transition hover:bg-tavaura-ink/5"
            >
              Cancel
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
