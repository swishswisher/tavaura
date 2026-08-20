"use client";

/* eslint-disable @next/next/no-img-element */

import { ImageOff } from "lucide-react";
import { useMemo, useState } from "react";

type RenderPreviewImageProps = {
  garmentName: string;
  imageUrl?: string | null;
  alt?: string;
  className?: string;
  imageClassName?: string;
};

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function getInitials(name: string) {
  const words = name
    .trim()
    .split(/[\s_-]+/)
    .filter(Boolean);

  if (words.length >= 2) {
    return `${words[0][0]}${words[1][0]}`.toUpperCase();
  }

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return "TR";
}

export function RenderPreviewImage({
  garmentName,
  imageUrl,
  alt,
  className,
  imageClassName,
}: RenderPreviewImageProps) {
  const normalizedImageUrl = imageUrl?.trim();
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const initials = useMemo(() => getInitials(garmentName), [garmentName]);
  const shouldShowImage =
    Boolean(normalizedImageUrl) && failedImageUrl !== normalizedImageUrl;

  return (
    <div
      className={cx(
        "relative flex shrink-0 overflow-hidden rounded-2xl border border-tavaura-ink/10 bg-white shadow-sm",
        className
      )}
    >
      {shouldShowImage ? (
        <img
          src={normalizedImageUrl}
          alt={alt ?? `${garmentName} render preview`}
          onError={() => setFailedImageUrl(normalizedImageUrl ?? null)}
          className={cx("h-full w-full object-cover", imageClassName)}
        />
      ) : (
        <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.96),_rgba(245,247,248,0.92)_48%,_rgba(31,53,60,0.1))] px-2 text-center">
          <ImageOff size={18} className="text-tavaura-ink/35" aria-hidden="true" />
          <span className="text-xs font-semibold tracking-[0.12em] text-tavaura-ink/65">
            {initials}
          </span>
        </div>
      )}
    </div>
  );
}
