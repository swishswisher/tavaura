"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavGroup = {
  title: string;
  items: { label: string; href: string }[];
};

type SidebarProps = {
  groups: NavGroup[];
};

export function DocsSidebar({ groups }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="w-full max-w-xs flex-shrink-0 rounded-2xl border border-white/50 bg-white/70 p-4 shadow-sm shadow-black/5 backdrop-blur">
      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-tavaura-ink/70">
        Docs
      </div>
      <div className="space-y-6 text-sm">
        {groups.map((group) => (
          <div key={group.title} className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-tavaura-ink/60">
              {group.title}
            </p>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between rounded-xl px-3 py-2 transition hover:bg-tavaura-ink/5 ${
                      isActive
                        ? "bg-tavaura-ink/10 font-semibold text-tavaura-ink"
                        : "text-tavaura-ink/80"
                    }`}
                  >
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
