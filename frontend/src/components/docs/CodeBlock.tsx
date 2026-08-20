"use client";

import { useState } from "react";

const LABELS: Record<string, string> = {
  html: "HTML",
  js: "JS",
  ts: "TS",
  bash: "Bash",
};

type CodeBlockProps = {
  code: string;
  language?: "html" | "js" | "ts" | "bash";
};

export function CodeBlock({ code, language = "html" }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.warn("Copy failed", err);
    }
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 text-slate-50">
      <div className="flex items-center justify-between px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-300">
        <span>{LABELS[language] ?? language.toUpperCase()}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-[11px] font-medium text-slate-100 transition hover:border-slate-500 hover:text-white"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto px-4 pb-4 text-[12px] leading-relaxed sm:text-sm">
        <code>{code}</code>
      </pre>
    </div>
  );
}
