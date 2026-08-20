"use client";

import Image from "next/image";

export function HeroArt() {
  return (
    <div className="relative h-full w-full">
      <div className="flex h-full w-full items-stretch justify-center">
        <div className="h-full w-full max-w-md overflow-hidden rounded-r-3xl rounded-l-none bg-white/90 shadow-xl shadow-black/10">
          <Image
            src="/images/tavaura-hero-avatars.png"
            alt="Three diverse avatars styled with Tavaura"
            width={800}
            height={800}
            className="h-full w-full object-cover"
            priority
          />
        </div>
      </div>
    </div>
  );
}
