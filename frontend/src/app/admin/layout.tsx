"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  LayoutDashboard,
  ListTodo,
  LogOut,
  Menu,
  Package,
  Settings,
  Sparkles,
  X,
} from "lucide-react";
import { getToken, removeToken } from "@/lib/auth";

type AdminLayoutProps = {
  children: ReactNode;
};

const navItems = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/garments", label: "Garments", icon: Package },
  { href: "/admin/ingestion-jobs", label: "Jobs", icon: ListTodo },
  { href: "/admin/render-results", label: "Renders", icon: Sparkles },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginRoute = pathname === "/admin/login";
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [hasToken, setHasToken] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  useEffect(() => {
    const token = getToken();
    setHasToken(Boolean(token));
    setIsCheckingAuth(false);

    if (!token && !isLoginRoute) {
      router.replace("/admin/login");
      return;
    }

    if (token && isLoginRoute) {
      router.replace("/admin");
    }
  }, [isLoginRoute, router]);

  useEffect(() => {
    if (!isMobileNavOpen) {
      return;
    }

    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMobileNavOpen]);

  const handleLogout = () => {
    setIsMobileNavOpen(false);
    removeToken();
    setHasToken(false);
    router.replace("/admin/login");
  };

  const closeMobileNav = () => {
    setIsMobileNavOpen(false);
  };

  if (isLoginRoute) {
    return <>{children}</>;
  }

  if (isCheckingAuth || !hasToken) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-tavaura-bg px-4">
        <div className="rounded-2xl border border-white/70 bg-white/80 px-5 py-4 text-sm font-medium text-tavaura-ink shadow-tavaura backdrop-blur">
          Opening merchant studio...
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.98),_#f5f7f8_48%,_rgba(31,53,60,0.1))] text-tavaura-ink">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-tavaura-ink/10 bg-tavaura-ink text-white shadow-2xl shadow-tavaura-ink/20 lg:flex lg:flex-col">
        <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-tavaura-ink shadow-tavaura-sm">
            <BarChart3 size={20} />
          </div>
          <div>
            <div className="text-base font-semibold tracking-tight">Tavaura</div>
            <div className="text-xs text-white/60">Merchant admin</div>
          </div>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/admin"
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-white text-tavaura-ink shadow-tavaura-sm"
                    : "text-white/75 hover:bg-white/10 hover:text-white"
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-4">
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium text-white/80 transition hover:bg-white/10 hover:text-white"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-tavaura-ink/10 bg-white/75 px-4 py-4 shadow-sm backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
            <div className="flex items-center gap-3 lg:hidden">
              <button
                type="button"
                onClick={() => setIsMobileNavOpen(true)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-tavaura-ink/10 bg-white/90 text-tavaura-ink shadow-sm transition hover:bg-tavaura-ink/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/20"
                aria-label="Open admin navigation"
                aria-expanded={isMobileNavOpen}
              >
                <Menu size={20} />
              </button>
              <Link href="/admin" className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-tavaura-ink text-white">
                  <BarChart3 size={18} />
                </span>
                <span className="font-semibold">Tavaura Admin</span>
              </Link>
            </div>
            <div className="hidden lg:block">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-ink/50">
                Merchant studio
              </p>
              <p className="text-sm text-tavaura-ink/70">
                Manage catalog prep, renders, and storefront readiness.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 rounded-full border border-tavaura-ink/15 bg-white px-4 py-2 text-sm font-medium text-tavaura-ink shadow-sm transition hover:bg-tavaura-ink/5 lg:hidden"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>

      <AnimatePresence>
        {isMobileNavOpen && (
          <>
            <motion.button
              type="button"
              className="fixed inset-0 z-40 bg-tavaura-ink/45 backdrop-blur-sm lg:hidden"
              aria-label="Close admin navigation"
              onClick={closeMobileNav}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-[min(21rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-r-2xl border-r border-white/25 bg-tavaura-ink/88 text-white shadow-2xl shadow-tavaura-ink/30 backdrop-blur-2xl lg:hidden"
              initial={{ x: "-105%", opacity: 0.92 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "-105%", opacity: 0.92 }}
              transition={{ type: "spring", stiffness: 360, damping: 34 }}
            >
              <div className="flex h-20 items-center justify-between gap-3 border-b border-white/10 px-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/95 text-tavaura-ink shadow-tavaura-sm">
                    <BarChart3 size={20} />
                  </div>
                  <div>
                    <div className="text-base font-semibold tracking-tight">Tavaura</div>
                    <div className="text-xs text-white/60">Merchant admin</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={closeMobileNav}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/10 text-white shadow-sm transition hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30"
                  aria-label="Close admin navigation"
                >
                  <X size={19} />
                </button>
              </div>

              <nav className="flex-1 space-y-2 px-4 py-6">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    item.href === "/admin"
                      ? pathname === item.href
                      : pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeMobileNav}
                      className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                        isActive
                          ? "bg-white text-tavaura-ink shadow-tavaura-sm"
                          : "text-white/80 hover:bg-white/10 hover:text-white"
                      }`}
                    >
                      <Icon size={18} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>

              <div className="border-t border-white/10 p-4">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium text-white/85 transition hover:bg-white/10 hover:text-white"
                >
                  <LogOut size={18} />
                  <span>Logout</span>
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
