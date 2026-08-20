"use client";

/* Generated try-on previews may be blob or data URLs and intentionally bypass next/image. */
/* eslint-disable @next/next/no-img-element */

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

type TryOnMode = "avatar" | "photo";
type AvatarPresetId = "pregnant" | "tallSlim" | "curvy" | "everyday";
type LookId = "street" | "smart" | "evening";

type ProcessResponse = {
  imageUrl: string;
};

const AVATAR_PRESETS: { id: AvatarPresetId; label: string; description: string }[] = [
  {
    id: "pregnant",
    label: "Pregnant avatar",
    description: "Third-trimester bump, soft knit dress vibe.",
  },
  {
    id: "tallSlim",
    label: "Tall & sharp",
    description: "Long lines, fitted denim and tailored layers.",
  },
  {
    id: "curvy",
    label: "Curvy",
    description: "Curvy build with a wrap top and soft drape.",
  },
  {
    id: "everyday",
    label: "Everyday",
    description: "Average build in relaxed tee and pants.",
  },
];

const LOOKS: { id: LookId; label: string; blurb: string }[] = [
  {
    id: "street",
    label: "Streetwear",
    blurb: "Relaxed layers, sneakers, off-duty vibe.",
  },
  {
    id: "smart",
    label: "Smart casual",
    blurb: "Blazer, tapered pants, clean lines.",
  },
  {
    id: "evening",
    label: "Evening",
    blurb: "Dress or sharp tailoring, night-out energy.",
  },
];

const GARMENTS: { id: LookId; label: string; src: string }[] = [
  { id: "street", label: "Jacket", src: "/demo-garments/jacket.png" },
  { id: "smart", label: "Blazer", src: "/demo-garments/tshirt.png" },
  { id: "evening", label: "Dress", src: "/demo-garments/dress.png" },
];

export function TryItNow() {
  const [mode, setMode] = useState<TryOnMode>("avatar");
  const [selectedAvatar, setSelectedAvatar] = useState(AVATAR_PRESETS[0]);
  const [selectedLook, setSelectedLook] = useState(LOOKS[0]);
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overlayGarment, setOverlayGarment] = useState<string | null>(GARMENTS[0].src);

  const summaryText = useMemo(
    () => `Avatar: ${selectedAvatar.label} • Look: ${selectedLook.label} • Mode: ${mode === "avatar" ? "Avatar" : "Photo"}`,
    [mode, selectedAvatar.label, selectedLook.label]
  );

  useEffect(() => {
    return () => {
      if (photoPreview) {
        URL.revokeObjectURL(photoPreview);
      }
    };
  }, [photoPreview]);

  const handleFile = async (file: File) => {
    setError(null);
    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Max file size is 5MB.");
      return;
    }

    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }
    const localPreview = URL.createObjectURL(file);
    setPhotoPreview(localPreview);
    setIsProcessing(true);
    setProcessedImageUrl(null);

    let processedUrl: string | null = localPreview;

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://localhost:5225/api/demo/process-photo", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Upload failed (${res.status})`);
      }

      const data = (await res.json()) as ProcessResponse;
      if (data?.imageUrl) {
        processedUrl = data.imageUrl;
      }
    } catch (err) {
      console.warn("Background removal failed, using raw photo", err);
      processedUrl = localPreview;
    } finally {
      setProcessedImageUrl(processedUrl);
      setError(null);
      setIsProcessing(false);
    }
  };

  const onInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      void handleFile(file);
    }
  };

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      void handleFile(file);
    }
  };

  const onDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const resetPhoto = () => {
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }
    setPhotoPreview(null);
    setProcessedImageUrl(null);
    setOverlayGarment(GARMENTS[0].src);
    setError(null);
  };

  const isAvatarMode = mode === "avatar";

  return (
    <section className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur sm:p-6 lg:p-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-semibold text-tavaura-ink sm:text-2xl">Try it now</h2>
        <div className="flex gap-2">
          {(["avatar", "photo"] as TryOnMode[]).map((tab) => {
            const active = mode === tab;
            return (
              <button
                key={tab}
                type="button"
                onClick={() => setMode(tab)}
                className={`cursor-pointer rounded-full px-4 py-2 text-sm font-semibold transition ${
                  active ? "bg-tavaura-ink text-white shadow" : "bg-white/5 text-tavaura-ink hover:bg-white/20"
                }`}
              >
                {tab === "avatar" ? "Avatar" : "Upload photo"}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-tavaura-ink/80">Setup</h3>

          {isAvatarMode ? (
            <div className="space-y-2 rounded-xl border border-white/10 bg-white/60 p-3 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Avatar presets</p>
              <div className="space-y-2">
                {AVATAR_PRESETS.map((preset) => {
                  const active = preset.id === selectedAvatar.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => setSelectedAvatar(preset)}
                      className={`w-full cursor-pointer rounded-xl border px-3 py-2 text-left transition ${
                        active ? "border-tavaura-ink bg-white/10" : "border-white/10 bg-white/5 hover:bg-white/10"
                      }`}
                    >
                      <div className="text-sm font-semibold text-tavaura-ink">{preset.label}</div>
                      <div className="text-xs text-tavaura-ink/70">{preset.description}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-3 rounded-xl border border-white/10 bg-white/70 p-3 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Upload your photo</p>
              <div
                onDrop={onDrop}
                onDragOver={onDragOver}
                className="flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-tavaura-ink/20 bg-white/80 px-4 py-6 text-center text-tavaura-ink shadow-sm transition hover:border-tavaura-ink/40"
              >
                <input id="try-upload" type="file" accept="image/*" onChange={onInputChange} className="hidden" />
                <label htmlFor="try-upload" className="flex cursor-pointer flex-col items-center gap-2 text-sm">
                  <span className="rounded-full bg-tavaura-ink px-3 py-1 text-xs font-semibold text-white">Photo</span>
                  <span className="font-semibold">Click to upload or drag an image</span>
                  <span className="text-xs text-tavaura-ink/70">PNG/JPEG up to 5MB</span>
                </label>
              </div>
              {isProcessing && (
                <div className="rounded-xl border border-white/10 bg-white/80 px-4 py-3 text-sm text-tavaura-ink">
                  Processing…
                </div>
              )}
              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
                  {error}
                </div>
              )}
              {processedImageUrl && (
                <button type="button" onClick={resetPhoto} className="cursor-pointer text-sm font-semibold text-tavaura-ink underline">
                  Try with a different photo
                </button>
              )}
            </div>
          )}

          <div className="space-y-2 rounded-xl border border-white/10 bg-white/60 p-3 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Pick a look</p>
            <div className="flex flex-wrap gap-2">
              {LOOKS.map((look) => {
                const active = look.id === selectedLook.id;
                return (
                  <button
                    key={look.id}
                    type="button"
                    onClick={() => setSelectedLook(look)}
                    className={`cursor-pointer rounded-full border px-3 py-2 text-sm transition ${
                      active
                        ? "border-tavaura-ink bg-tavaura-ink text-white"
                        : "border-white/10 bg-white/5 text-tavaura-ink hover:bg-white/10"
                    }`}
                  >
                    {look.label}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-tavaura-ink/70">{selectedLook.blurb}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/70">Preview</p>

          {isAvatarMode ? (
            <div className="mt-3 space-y-3">
              <div className="overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-tavaura-ink/10 to-white/60 p-6 text-center text-tavaura-ink shadow">
                <div className="mx-auto h-48 w-40 rounded-[48%] bg-white/80 shadow-inner" />
                <p className="mt-4 text-sm text-tavaura-ink">Avatar preview coming here</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/80 px-4 py-3 text-sm text-tavaura-ink shadow-sm">
                Avatar: {selectedAvatar.label} · Look: {selectedLook.label}
              </div>
              <p className="text-xs text-tavaura-ink/70">
                In the full viewer, this avatar subtly moves and turns while wearing this look.
              </p>
            </div>
          ) : (
            <div className="mt-3 space-y-3">
              <div className="relative overflow-hidden rounded-xl border border-white/10 bg-black/10 shadow">
                {processedImageUrl ? (
                  <div className="relative">
                    <img src={processedImageUrl} alt="Processed" className="h-64 w-full rounded-xl object-cover" />
                    {overlayGarment && (
                      <img
                        src={overlayGarment}
                        alt="Selected garment"
                        className="pointer-events-none absolute inset-0 mx-auto w-full max-w-[90%] object-contain drop-shadow-lg"
                      />
                    )}
                  </div>
                ) : (
                  <div className="flex h-64 items-center justify-center px-4 text-sm text-tavaura-ink/60">
                    Upload a photo on the left to see your look.
                  </div>
                )}
              </div>
              {processedImageUrl && (
                <div className="flex flex-wrap gap-2">
                  {GARMENTS.map((garment) => (
                    <button
                      key={garment.id}
                      type="button"
                      disabled={!processedImageUrl}
                      onClick={() => setOverlayGarment(garment.src)}
                      className={`cursor-pointer rounded-full border px-3 py-2 text-sm transition ${
                        overlayGarment === garment.src
                          ? "border-tavaura-ink bg-white/20 text-tavaura-ink"
                          : "border-white/15 bg-white/5 text-tavaura-ink/80 hover:bg-white/10 disabled:opacity-50"
                      }`}
                    >
                      {garment.label}
                    </button>
                  ))}
                </div>
              )}
              <div className="rounded-xl border border-white/10 bg-white/80 px-4 py-3 text-sm text-tavaura-ink shadow-sm">
                Look: {selectedLook.label}
              </div>
              <p className="text-xs text-tavaura-ink/70">
                This is a demo overlay. In the full product, garments and lipstick are tuned per store.
              </p>
              {processedImageUrl && (
                <button
                  type="button"
                  onClick={resetPhoto}
                  className="text-sm font-semibold text-tavaura-ink underline"
                >
                  Try with a different photo
                </button>
              )}
            </div>
          )}

          <div className="mt-4 rounded-xl border border-white/10 bg-white/90 p-3 text-xs text-tavaura-ink/70">
            Demo visualization (static for now)
            <div className="mt-2 overflow-hidden rounded-lg border border-white/20 bg-white">
              <Image
                src="/images/tavaura-hero-avatars.png"
                alt="Tavaura demo avatars"
                width={400}
                height={400}
                className="h-full w-full object-cover"
              />
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-white/10 bg-white/70 px-4 py-3 text-sm text-tavaura-ink shadow-sm">
            {summaryText}
          </div>
        </div>
      </div>
    </section>
  );
}
