"use client";

import Link from "next/link";
import { useState } from "react";

export type SiteShellProps = {
  children: React.ReactNode;
};

const navLinks = [
  { href: "/", label: "Home" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#for-brands", label: "For brands" },
  { href: "#for-shoppers", label: "For shoppers" },
  { href: "#contact", label: "Contact" },
];

export function SiteShell({ children }: SiteShellProps) {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  const handleNavClick = () => setIsMobileNavOpen(false);

  return (
    <div className="relative min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.95),_#f5f7f8)]">
      <header className="fixed inset-x-0 top-0 z-30 border-b border-tavaura-ink/20 bg-tavaura-ink/85 text-tavaura-white backdrop-blur-xl shadow-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 text-sm sm:px-6">
          <Link href="/" className="text-base font-semibold tracking-tight">
            Tavaura
          </Link>
          <nav className="hidden items-center gap-6 text-sm font-medium text-tavaura-white/90 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="relative pb-1 transition hover:text-tavaura-white after:absolute after:inset-x-0 after:-bottom-0.5 after:h-[2px] after:origin-left after:scale-x-0 after:bg-tavaura-white/70 after:transition hover:after:scale-x-100"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <button
            type="button"
            className="flex flex-col gap-1.5 px-1 py-1 text-tavaura-white md:hidden"
            onClick={() => setIsMobileNavOpen(true)}
            aria-label="Open navigation menu"
          >
            <span className="h-0.5 w-6 rounded-full bg-tavaura-white" />
            <span className="h-0.5 w-6 rounded-full bg-tavaura-white" />
            <span className="h-0.5 w-6 rounded-full bg-tavaura-white" />
          </button>
        </div>
      </header>

      <main
        role="main"
        className="mx-auto max-w-5xl px-4 pb-12 pt-24 sm:px-6 sm:pt-28"
      >
        {children}
      </main>

      {isMobileNavOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 md:hidden"
            onClick={handleNavClick}
          />
          <nav className="fixed inset-y-0 right-0 z-50 w-64 bg-tavaura-ink text-tavaura-white shadow-xl md:hidden">
            <div className="flex items-center justify-between px-4 py-4">
              <Link
                href="/"
                className="text-base font-semibold tracking-tight"
                onClick={handleNavClick}
              >
                Tavaura
              </Link>
              <button
                type="button"
                className="text-2xl leading-none"
                onClick={handleNavClick}
                aria-label="Close navigation menu"
              >
                &times;
              </button>
            </div>
            <div className="flex flex-col gap-2 px-4 py-4 text-sm font-medium">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-xl px-4 py-3 text-tavaura-white/90 transition hover:bg-white/10"
                  onClick={handleNavClick}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </>
      )}
    </div>
  );
}
