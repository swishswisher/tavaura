import Link from "next/link";

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-white/10 bg-tavaura-ink text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-sm sm:flex-row sm:items-center sm:justify-between sm:gap-3 sm:px-6 lg:px-8">
        <div className="text-center sm:text-left">
          <div className="text-base font-semibold">Tavaura</div>
          <div className="text-tavaura-white/70">Giving aura to your avatar.</div>
          <div className="text-xs text-tavaura-white/60">
            {"\u00a9"} {year} Tavaura
          </div>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4 text-center text-tavaura-white/80 sm:justify-end">
          <Link href="/docs" className="transition hover:text-white">
            Docs
          </Link>
          <a href="#pricing" className="transition hover:text-white">
            Pricing
          </a>
          <a href="#contact" className="transition hover:text-white">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
