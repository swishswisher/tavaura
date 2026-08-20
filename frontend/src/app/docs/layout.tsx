import Link from "next/link";
import { ReactNode } from "react";
import { DocsSidebar } from "./Sidebar";

const NAV_GROUPS = [
  {
    title: "Getting started",
    items: [
      { label: "Overview", href: "/docs" },
      { label: "Installation snippet", href: "/docs/installation" },
    ],
  },
  {
    title: "Platforms",
    items: [
      { label: "Shopify", href: "/docs/platforms/shopify" },
      { label: "WooCommerce", href: "/docs/platforms/woocommerce" },
      { label: "Wix", href: "/docs/platforms/wix" },
      { label: "Squarespace", href: "/docs/platforms/squarespace" },
      { label: "Custom HTML site", href: "/docs/platforms/custom-html" },
      { label: "React / SPA", href: "/docs/platforms/react" },
    ],
  },
];

type DocsLayoutProps = {
  children: ReactNode;
};

export default function DocsLayout({ children }: DocsLayoutProps) {
  return (
    <div className="min-h-screen bg-white">
      <div className="fixed left-4 top-4 z-40 sm:left-6 sm:top-6">
        <Link
          href="/"
          className="inline-flex items-center rounded-full bg-tavaura-ink px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-tavaura-ink/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-cocoa/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
        >
          <span>←</span>
          <span>Back to Home</span>
        </Link>
      </div>
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-12 sm:px-6 lg:flex-row lg:items-start lg:px-8 lg:py-14">
        <div className="w-full max-w-xs">
          <DocsSidebar groups={NAV_GROUPS} />
        </div>
        <main className="flex-1 rounded-2xl border border-white/50 bg-white/80 p-6 shadow-sm shadow-black/5 backdrop-blur sm:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
