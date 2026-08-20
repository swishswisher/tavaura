"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

function SignupPageContent() {
  const searchParams = useSearchParams();
  const source = searchParams.get("from") ?? undefined;
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!email || !email.includes("@")) {
      setError("Please enter a valid email.");
      return;
    }

    setStatus("submitting");
    try {
      const res = await fetch("/api/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, from: source }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.error ?? "Something went wrong. Please try again.");
        setStatus("error");
        return;
      }

      setEmail("");
      setStatus("success");
    } catch {
      setError("Network error. Please try again.");
      setStatus("error");
    }
  };

  return (
    <main className="min-h-screen bg-tavaura-bg px-4 py-12 sm:px-6 lg:px-10 lg:py-16">
      <div className="mx-auto w-full max-w-3xl space-y-6 sm:space-y-8">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight text-tavaura-ink sm:text-4xl">
            Create your Tavaura account
          </h1>
          <p className="max-w-2xl text-sm sm:text-base text-tavaura-ink/75">
            Save avatars, outfits, and cosmetics to your Tavaura account and pick up where you left off across stores.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="tavaura-glass-soft rounded-3xl px-5 py-6 shadow-tavaura sm:px-6 sm:py-7"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-3">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@brand.com"
              className="w-full rounded-xl border border-tavaura-ink/15 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink sm:flex-1"
            />
            <button
              type="submit"
              disabled={status === "submitting"}
              className="rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {status === "submitting" ? "Saving..." : "Continue"}
            </button>
          </div>
          <p className="mt-3 text-xs text-tavaura-ink/70">
            Use your work or brand email. We’ll use it to create your Tavaura account and send important updates.
          </p>
          {status === "success" && (
            <p className="mt-2 text-sm text-emerald-500">
              You’re in. We’ll email you details about your Tavaura account.
            </p>
          )}
          {error && (
            <p className="mt-2 text-sm text-rose-500">
              {error}
            </p>
          )}
        </form>

        <div className="text-sm text-tavaura-ink/70">
          <Link href="/" className="underline hover:text-tavaura-ink">
            Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function SignupPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-tavaura-bg px-4 py-12 sm:px-6 lg:px-10 lg:py-16">
          <div className="mx-auto w-full max-w-3xl">
            <div className="tavaura-glass-soft rounded-3xl px-5 py-6 text-sm text-tavaura-ink shadow-tavaura sm:px-6 sm:py-7">
              Loading signup...
            </div>
          </div>
        </main>
      }
    >
      <SignupPageContent />
    </Suspense>
  );
}
