"use client";

import { useEffect, useRef, useState } from "react";
import { TavauraWidgetOverlay } from "@/components/widget/TavauraWidgetOverlay";
import { useRouter } from "next/navigation";

export default function Page() {
  const router = useRouter();
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const hintTimeoutRef = useRef<number | null>(null);
  const seenRef = useRef(false);

  useEffect(() => {
    const btn = buttonRef.current;
    if (!btn) return;
    seenRef.current = typeof window !== "undefined" ? window.localStorage.getItem("tavaura_hint_seen") === "1" : true;
    if (seenRef.current) return;

    const clearHintTimeout = () => {
      if (hintTimeoutRef.current) {
        window.clearTimeout(hintTimeoutRef.current);
        hintTimeoutRef.current = null;
      }
    };

    const markSeen = () => {
      seenRef.current = true;
      if (typeof window !== "undefined") {
        window.localStorage.setItem("tavaura_hint_seen", "1");
      }
      clearHintTimeout();
      btn.classList.remove("tavaura-hint");
    };

    const playHint = () => {
      if (seenRef.current) return;
      btn.classList.add("tavaura-hint");
      const onEnd = () => {
        btn.classList.remove("tavaura-hint");
        btn.removeEventListener("animationend", onEnd);
        markSeen();
      };
      btn.addEventListener("animationend", onEnd);
    };

    const triggerDelayedHint = () => {
      clearHintTimeout();
      hintTimeoutRef.current = window.setTimeout(playHint, 2000);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.5 && !seenRef.current) {
            observer.disconnect();
            triggerDelayedHint();
          }
        });
      },
      { threshold: 0.5 }
    );
    observer.observe(btn);

    const cancel = () => {
      markSeen();
      observer.disconnect();
    };

    btn.addEventListener("mouseenter", cancel);
    btn.addEventListener("focus", cancel);
    btn.addEventListener("click", cancel);

    return () => {
      clearHintTimeout();
      observer.disconnect();
      btn.classList.remove("tavaura-hint");
      btn.removeEventListener("mouseenter", cancel);
      btn.removeEventListener("focus", cancel);
      btn.removeEventListener("click", cancel);
    };
  }, []);

  const handleOpen = () => {
    setIsWidgetOpen(true);
    const btn = buttonRef.current;
    if (btn) btn.classList.remove("tavaura-hint");
    if (hintTimeoutRef.current) window.clearTimeout(hintTimeoutRef.current);
    seenRef.current = true;
    if (typeof window !== "undefined") window.localStorage.setItem("tavaura_hint_seen", "1");
  };

  const handleSavePreferences = () => {
    setIsWidgetOpen(false);
    router.push("/signup?from=widget-save");
  };

  const handleDownloadTavaura = () => {
    setIsWidgetOpen(false);
    router.push("/signup?from=widget-download");
  };

  return (
    <main className="min-h-screen bg-tavaura-bg px-4 py-10 sm:px-6 lg:px-10 lg:py-16">
      <div className="mx-auto w-full max-w-sm space-y-6 sm:max-w-3xl lg:max-w-5xl sm:space-y-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          SDK demo · Product page
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-tavaura-ink sm:text-4xl">
          Everyday Aura Midi Dress
        </h1>
        <div className="space-y-4 sm:space-y-5">
          <div className="flex w-full max-w-sm mx-auto items-center justify-center rounded-3xl bg-gradient-to-br from-tavaura-ink/10 via-white to-tavaura-ink/5 p-4 shadow-lg shadow-black/5 sm:max-w-lg sm:p-6 lg:max-w-full">
            <div className="relative mx-auto w-full max-w-xs overflow-hidden rounded-3xl bg-gradient-to-b from-emerald-200 via-emerald-400 to-emerald-600 shadow-[0_24px_80px_rgba(15,23,42,0.35)] sm:max-w-sm">
              <div className="aspect-[4/5]" />
            </div>
          </div>
          <div className="w-full max-w-sm mx-auto rounded-2xl border border-slate-100 bg-white p-4 shadow-sm shadow-black/5 sm:max-w-none sm:p-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="text-lg font-semibold text-tavaura-ink">$148.00</span>
              <span className="rounded-full bg-tavaura-ink/10 px-3 py-1 text-xs font-semibold text-tavaura-ink">
                In stock
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-tavaura-ink/80">
              A versatile midi dress with a flattering drape and subtle sheen. Designed to work with layers or stand on its own with confidence.
            </p>
            <ul className="mt-3 list-disc list-inside space-y-1 text-sm text-tavaura-ink/80">
              <li>Soft stretch fabric with gentle structure.</li>
              <li>Machine-washable, travel friendly.</li>
              <li>Fits true to size; model is 5&apos;8&quot; wearing size S.</li>
            </ul>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <button
                className="w-full rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-semibold text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90 sm:w-auto"
                type="button"
              >
                Add to cart
              </button>
              <button
                type="button"
                onClick={handleOpen}
                ref={buttonRef}
                className="tavaura-tryon-cta relative w-full rounded-full border border-tavaura-ink/20 bg-white px-5 py-2.5 text-sm font-semibold text-tavaura-ink transition hover:bg-tavaura-ink/5 sm:w-auto"
              >
                <span className="relative z-10">Try on with Tavaura</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <TavauraWidgetOverlay
        isOpen={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        onSavePreferences={handleSavePreferences}
        onDownloadTavaura={handleDownloadTavaura}
      />
    </main>
  );
}
