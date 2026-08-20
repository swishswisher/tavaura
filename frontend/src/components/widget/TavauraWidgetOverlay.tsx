"use client";

import { useEffect } from "react";
import { TavauraWidget } from "./TavauraWidget";

export type TavauraWidgetOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
  onSavePreferences?: () => void;
  onDownloadTavaura?: () => void;
};

export function TavauraWidgetOverlay({
  isOpen,
  onClose,
  onSavePreferences,
  onDownloadTavaura,
}: TavauraWidgetOverlayProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.classList.add("tavaura-overlay-open");
      document.body.style.overflow = "hidden";
      return () => {
        document.body.classList.remove("tavaura-overlay-open");
        document.body.style.overflow = "";
      };
    }
    return;
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[999] overflow-y-auto bg-transparent backdrop-blur-xl pointer-events-auto"
      onClick={onClose}
    >
      <div
        className="relative mx-3 min-h-screen flex items-center justify-center p-4 sm:mx-4 sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative w-full max-w-[950px] max-h-[85vh] overflow-hidden rounded-2xl bg-tavaura-bg shadow-tavaura-lg sm:rounded-3xl">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 h-9 w-9 flex items-center justify-center rounded-full bg-tavaura-ink text-white hover:bg-tavaura-ink/90 shadow-lg shadow-black/30 transition sm:right-6 sm:top-6"
            aria-label="Close widget"
          >
            <span className="text-lg leading-none">&times;</span>
          </button>

          <div className="h-full overflow-y-auto overscroll-contain scroll-smooth p-4 sm:p-6 lg:p-8">
            <TavauraWidget
              onClose={onClose}
              onSavePreferences={onSavePreferences}
              onDownloadTavaura={onDownloadTavaura}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
