import Link from "next/link";

export function DocsBackToRoot() {
  return (
    <div className="mt-10 border-t border-slate-200 pt-6">
      <Link
        href="/docs"
        className="inline-flex items-center gap-2 rounded-full bg-tavaura-ink px-4 py-2 text-sm font-medium text-tavaura-white shadow-sm hover:bg-tavaura-ink/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-cocoa/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
      >
        <span>↑</span>
        <span>Back to docs</span>
      </Link>
    </div>
  );
}
