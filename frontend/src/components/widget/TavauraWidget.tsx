"use client";

/* Storefront and generated preview URLs are runtime-controlled and cannot use next/image safely. */
/* eslint-disable @next/next/no-img-element */

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type WidgetModeProp = "avatar-first" | "photo-first" | undefined;
type ActiveMode = "avatar" | "photo";
type GarmentId = "dress" | "jacket" | "tshirt";

type Garment = {
  id: GarmentId;
  name: string;
  desc: string;
  img: string;
};

const GARMENTS: Garment[] = [
  { id: "dress", name: "Midi dress", desc: "Soft drape, midi length", img: "/demo-garments/dress.png" },
  { id: "jacket", name: "Layered jacket", desc: "Street-ready outerwear", img: "/demo-garments/jacket.png" },
  { id: "tshirt", name: "Everyday tee", desc: "Staple top for layering", img: "/demo-garments/tshirt.png" },
];

export type TavauraWidgetProps = {
  mode?: WidgetModeProp;
  tenantId?: string;
  onClose?: () => void;
  onSavePreferences?: () => void;
  onDownloadTavaura?: () => void;
};

export function TavauraWidget({
  mode: modeProp = "avatar-first",
  tenantId,
  onClose,
  onSavePreferences,
  onDownloadTavaura,
}: TavauraWidgetProps) {
  const router = useRouter();
  const initialMode: ActiveMode = modeProp === "photo-first" ? "photo" : "avatar";
  const [mode, setMode] = useState<ActiveMode>(initialMode);
  const [selectedGarment, setSelectedGarment] = useState<GarmentId>("dress");
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] = useState<"idle" | "preparing">("idle");

  const selectedGarmentData = useMemo(
    () => GARMENTS.find((g) => g.id === selectedGarment) ?? GARMENTS[0],
    [selectedGarment]
  );

  const hasPhoto = Boolean(photoPreviewUrl);

  const previewHelper =
    mode === "photo"
      ? hasPhoto
        ? "Photo loaded - garment overlays are simulated."
        : "No photo yet - we'll use your selfie here."
      : "Avatars keep proportions and tone; garments update instantly.";

  useEffect(() => {
    return () => {
      if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
    };
  }, [photoPreviewUrl]);

  const handlePhotoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert("Please choose an image under 5MB.");
      return;
    }
    if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
    const url = URL.createObjectURL(file);
    setPhotoPreviewUrl(url);
  };

  const handleSavePreferencesClick = () => {
    if (typeof onSavePreferences === "function") {
      onSavePreferences();
      return;
    }
    if (typeof onClose === "function") {
      onClose();
    }
    setTimeout(() => {
      router.push("/signup?from=widget-save");
    }, 150);
  };

  const handleDownloadClick = () => {
    if (downloadStatus === "preparing") return;
    setDownloadStatus("preparing");
    if (typeof onDownloadTavaura === "function") {
      onDownloadTavaura();
    }
  };

  return (
    <section className="tavaura-glass-surface w-full rounded-[24px] text-tavaura-ink shadow-tavaura sm:rounded-[28px] md:rounded-[32px] max-h-[85vh] overflow-hidden overflow-y-auto">
      <div className="flex items-center justify-between gap-3 px-4 pt-4 sm:px-5 sm:pt-5">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-tavaura-ink/70">
          {tenantId ? `Try it with Tavaura \u00b7 ${tenantId}` : "Try it with Tavaura"}
        </div>
        <div className="inline-flex flex-wrap items-center gap-1 rounded-full bg-slate-100 p-1 text-sm">
          {(["avatar", "photo"] as ActiveMode[]).map((tab) => (
            <button
              key={tab}
              type="button"
              aria-pressed={mode === tab}
              onClick={() => setMode(tab)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                mode === tab
                  ? "bg-tavaura-ink text-tavaura-white shadow-tavaura-sm"
                  : "text-tavaura-ink/70 hover:text-tavaura-ink"
              }`}
            >
              {tab === "avatar" ? "Avatar" : "Photo"}
            </button>
          ))}
        </div>
      </div>

      {mode === "photo" && (
        <div className="mx-4 mt-3 rounded-2xl border border-tavaura-ink/10 bg-white/80 px-4 py-3 text-xs text-tavaura-ink/80 shadow-sm sm:mx-5 sm:text-sm">
          <label className="block cursor-pointer space-y-1">
            <span className="font-semibold text-tavaura-ink">Upload a photo</span>
            <span className="block text-[11px] sm:text-xs text-tavaura-ink/60">
              PNG or JPG up to 5MB. Demo only — stays in your browser.
            </span>
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={handlePhotoChange} />
          </label>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 items-start gap-6 px-4 pb-5 sm:gap-8 sm:px-5 sm:pb-6 md:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <div className="flex w-full max-w-full flex-col items-center gap-3 rounded-3xl bg-tavaura-ink px-4 pt-4 pb-6 text-tavaura-white shadow-inner sm:px-6 sm:pt-6 sm:pb-8">
          <div className="inline-flex items-center gap-2 self-start rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/90">
            {mode === "avatar" ? "Avatar preview" : hasPhoto ? "Your photo" : "Upload a photo to unlock"}
          </div>
          <div className="flex flex-1 w-full items-center justify-center">
            {mode === "photo" && photoPreviewUrl ? (
              <div className="relative mx-auto w-full max-w-[320px] overflow-hidden rounded-3xl shadow-2xl aspect-[3/4] sm:max-w-[360px]">
                <img src={photoPreviewUrl} alt="Uploaded preview" className="h-full w-full object-cover" />
              </div>
            ) : (
              <div className="relative mx-auto mt-3 w-full max-w-[260px] sm:max-w-[280px] aspect-[3/5] rounded-3xl bg-gradient-to-b from-emerald-300 to-emerald-500 shadow-lg">
                <div className="absolute inset-x-2 top-2 h-3 rounded-full bg-white/40" />
                <div className="mb-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-1 text-[11px] font-semibold text-tavaura-ink shadow-sm">
                  {selectedGarmentData.name}
                </div>
              </div>
            )}
          </div>
          <p className="text-xs leading-relaxed text-white/70">{previewHelper}</p>
        </div>

        <div className="space-y-3">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-tavaura-ink">Sample garments</h3>
            <p className="text-xs text-tavaura-ink/70">Choose a piece to preview on your avatar or photo.</p>
          </div>

          <div className="flex flex-col gap-2">
            {GARMENTS.map((garment) => {
              const active = garment.id === selectedGarment;
              return (
                <button
                  key={garment.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setSelectedGarment(garment.id)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                    active
                      ? "border-tavaura-ink/80 bg-white shadow-sm"
                      : "border-slate-200 hover:border-tavaura-ink/60 hover:bg-slate-50/60"
                  }`}
                >
                  <div className="h-10 w-10 overflow-hidden rounded-lg bg-slate-100">
                    <img src={garment.img} alt={garment.name} className="h-full w-full object-contain" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-tavaura-ink">{garment.name}</div>
                    <div className="text-xs text-tavaura-ink/70">{garment.desc}</div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="my-6 border-t border-tavaura-ink/10" />

          <section className="space-y-3">
            <h4 className="text-sm font-semibold text-tavaura-ink">Save your preferences</h4>
            <button
              type="button"
              className="w-full rounded-full bg-tavaura-ink px-5 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-tavaura-ink/90 sm:w-auto"
              onClick={handleSavePreferencesClick}
            >
              Save your preferences
            </button>
            <p className="text-xs text-tavaura-ink/70">
              Save your avatar style and looks, so you can pick up where you left off.
            </p>
          </section>

          <section className="space-y-3">
            <h4 className="text-sm font-semibold text-tavaura-ink">Download your Tavaura</h4>
            <button
              type="button"
              className="w-full rounded-full border border-tavaura-ink/30 px-5 py-2 text-sm font-semibold text-tavaura-ink transition shadow-sm hover:bg-tavaura-ink/5 sm:w-auto"
              onClick={handleDownloadClick}
              disabled={downloadStatus === "preparing"}
            >
              {downloadStatus === "preparing" ? "Preparing your Tavaura…" : "Download your Tavaura"}
            </button>
            <p className="text-xs text-tavaura-ink/60">
              Get a short animated clip of your avatar with a subtle &apos;made with Tavaura&apos; watermark.
            </p>
          </section>

          <p className="text-[11px] text-tavaura-ink/60">In production, these tiles would be driven by your real catalog.</p>
        </div>
      </div>
    </section>
  );
}
