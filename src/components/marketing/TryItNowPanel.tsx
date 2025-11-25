"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

type TryOnMode = "avatar" | "photo";
type AvatarPresetId = "pregnant" | "tallSlim" | "curvy" | "average";
type LookId = "street" | "smart" | "evening";

const AVATAR_PRESETS: { id: AvatarPresetId; label: string; description: string }[] = [
  { id: "pregnant", label: "Pregnant avatar", description: "Third-trimester bump, soft knit dress" },
  { id: "tallSlim", label: "Tall slim", description: "Sharp silhouette, fitted jeans" },
  { id: "curvy", label: "Curvy", description: "Curvy build, wrap top and skirt" },
  { id: "average", label: "Everyday", description: "Average build, relaxed tee and pants" },
];

const LOOKS: { id: LookId; label: string; blurb: string }[] = [
  { id: "street", label: "Streetwear", blurb: "Relaxed layers, sneakers, off-duty vibe" },
  { id: "smart", label: "Smart casual", blurb: "Blazer, tapered pants, clean lines" },
  { id: "evening", label: "Evening", blurb: "Dress or sharp tailoring, night-out energy" },
];

export function TryItNowPanel() {
  const [mode, setMode] = useState<TryOnMode>("avatar");
  const [selectedAvatar, setSelectedAvatar] = useState(AVATAR_PRESETS[0]);
  const [selectedLook, setSelectedLook] = useState(LOOKS[0]);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [appliedSummary, setAppliedSummary] = useState<string | null>(null);

  const summaryText = useMemo(
    () =>
      `Avatar: ${selectedAvatar.label} • Look: ${selectedLook.label} • Mode: ${mode === "avatar" ? "Avatar" : "Photo"}`,
    [mode, selectedAvatar.label, selectedLook.label]
  );

  const handleApplyLook = () => {
    setIsApplying(true);
    // TODO: Replace timeout with real /api/tryon call once backend is ready.
    setTimeout(() => {
      setIsApplying(false);
      setAppliedSummary(summaryText);
    }, 650);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }
    const url = URL.createObjectURL(file);
    setPhotoPreview(url);
  };

  const handleClearPhoto = () => {
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }
    setPhotoPreview(null);
  };

  useEffect(() => {
    return () => {
      if (photoPreview) {
        URL.revokeObjectURL(photoPreview);
      }
    };
  }, [photoPreview]);

  return (
    <section className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur sm:p-6 lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:gap-6">
        <div className="grid w-full grid-cols-2 gap-2 sm:w-auto sm:max-w-sm">
          {["avatar", "photo"].map((tab) => {
            const label = tab === "avatar" ? "Avatar" : "Upload photo";
            const active = mode === tab;
            return (
              <button
                key={tab}
                type="button"
                onClick={() => setMode(tab as TryOnMode)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition sm:w-full ${
                  active
                    ? "bg-tavaura-ink text-white shadow"
                    : "bg-white/5 text-tavaura-ink hover:bg-white/20"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Avatar preset</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {AVATAR_PRESETS.map((preset) => {
                const active = preset.id === selectedAvatar.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => setSelectedAvatar(preset)}
                    className={`rounded-xl border p-3 text-left transition ${
                      active
                        ? "border-tavaura-ink bg-white/10"
                        : "border-white/10 bg-white/5 hover:bg-white/10"
                    }`}
                  >
                    <div className="text-sm font-semibold text-tavaura-ink">{preset.label}</div>
                    <div className="text-xs text-tavaura-ink/70">{preset.description}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Look</p>
            <div className="flex flex-wrap gap-2">
              {LOOKS.map((look) => {
                const active = look.id === selectedLook.id;
                return (
                  <button
                    key={look.id}
                    type="button"
                    onClick={() => setSelectedLook(look)}
                    className={`rounded-full border px-3 py-2 text-sm transition ${
                      active
                        ? "border-tavaura-ink bg-white/10 text-tavaura-ink"
                        : "border-white/15 bg-white/5 text-tavaura-ink/80 hover:bg-white/10"
                    }`}
                  >
                    {look.label}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-tavaura-ink/70">{selectedLook.blurb}</p>
          </div>

          {mode === "photo" && (
            <div className="space-y-2">
              <label className="text-sm font-semibold text-tavaura-ink" htmlFor="try-photo">
                Upload a photo
              </label>
              <input
                id="try-photo"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="w-full text-sm text-tavaura-ink"
              />
              {photoPreview && (
                <div className="space-y-2">
                  <div className="overflow-hidden rounded-xl border border-white/10">
                    <img
                      src={photoPreview}
                      alt="Uploaded preview"
                      className="max-h-64 w-full object-cover"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleClearPhoto}
                    className="text-xs font-semibold text-tavaura-ink underline"
                  >
                    Clear photo
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-4 rounded-2xl border border-white/10 bg-white/40 p-4 shadow-sm backdrop-blur">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Preview</p>
            <div className="rounded-xl border border-white/10 bg-white/70 px-4 py-3 text-sm text-tavaura-ink shadow-sm">
              {appliedSummary || summaryText}
            </div>
          </div>

          <div className="space-y-2 text-xs text-tavaura-ink/70">
            <p>Demo visualization (static for now)</p>
            <div className="overflow-hidden rounded-xl border border-white/10 bg-white/90 shadow">
              <Image
                src="/images/tavaura-hero-avatars.png"
                alt="Tavaura demo avatars"
                width={640}
                height={640}
                className="h-full w-full object-cover"
              />
            </div>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={handleApplyLook}
              disabled={isApplying}
              className="inline-flex items-center justify-center rounded-full bg-tavaura-ink px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isApplying ? "Applying..." : "Apply this look"}
            </button>
            {mode === "photo" && photoPreview && (
              <p className="text-xs text-tavaura-ink/70">Using your uploaded photo.</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
