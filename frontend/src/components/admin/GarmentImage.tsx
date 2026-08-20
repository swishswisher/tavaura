"use client";

/* eslint-disable @next/next/no-img-element */

import { Package } from "lucide-react";
import { useMemo, useState } from "react";

type GarmentImageProps = {
  name: string;
  imageUrl?: string | null;
  alt?: string;
  className?: string;
  imageClassName?: string;
  iconClassName?: string;
  initialsClassName?: string;
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

  return "TG";
}

export function GarmentImage({
  name,
  imageUrl,
  alt,
  className,
  imageClassName,
  iconClassName,
  initialsClassName,
}: GarmentImageProps) {
  const normalizedImageUrl = imageUrl?.trim();
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const initials = useMemo(() => getInitials(name), [name]);
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
          alt={alt ?? name}
          onError={() => setFailedImageUrl(normalizedImageUrl ?? null)}
          className={cx("h-full w-full object-cover", imageClassName)}
        />
      ) : (
        <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.96),_rgba(245,247,248,0.92)_48%,_rgba(31,53,60,0.1))] px-2 text-center">
          <Package
            size={18}
            className={cx("text-tavaura-ink/35", iconClassName)}
            aria-hidden="true"
          />
          <span
            className={cx(
              "text-xs font-semibold tracking-[0.12em] text-tavaura-ink/65",
              initialsClassName
            )}
          >
            {initials}
          </span>
        </div>
      )}
    </div>
  );
}
