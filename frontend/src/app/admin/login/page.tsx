"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";
import { ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
import { postJson } from "@/lib/api";
import { saveToken } from "@/lib/auth";

type LoginResponse = {
  accessToken: string;
  tokenType: string;
  expiresAtUtc: string;
  role: string;
  tenantId: string | null;
  userId: string;
  email: string;
};

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Email and password are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await postJson<
        { email: string; password: string },
        LoginResponse
      >("/api/auth/login", {
        email: email.trim(),
        password,
      });

      if (!response.accessToken) {
        throw new Error("Login succeeded but no access token was returned.");
      }

      saveToken(response.accessToken);
      router.replace("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.98),_#f5f7f8_46%,_rgba(31,53,60,0.12))] px-4 py-8 text-tavaura-ink sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center">
        <div className="grid w-full gap-8 lg:grid-cols-[minmax(0,0.92fr)_minmax(420px,0.68fr)] lg:items-center">
          <section className="space-y-8">
            <Link
              href="/"
              className="inline-flex items-center rounded-full border border-tavaura-ink/10 bg-white/80 px-4 py-2 text-sm font-medium text-tavaura-ink shadow-sm transition hover:bg-white"
            >
              Tavaura
            </Link>

            <div className="max-w-xl space-y-5">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tavaura-ink/60">
                Merchant admin
              </p>
              <h1 className="text-4xl font-semibold tracking-tight text-tavaura-ink sm:text-5xl">
                Prepare every product for confident try-on.
              </h1>
              <p className="text-base leading-7 text-tavaura-ink/75 sm:text-lg">
                Sign in to manage garments, monitor render activity, and keep your Tavaura storefront experience ready for shoppers.
              </p>
            </div>

            <div className="grid max-w-2xl gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/70 bg-white/70 p-4 shadow-tavaura-sm backdrop-blur">
                <ShieldCheck className="mb-3 text-tavaura-cocoa" size={22} />
                <p className="text-sm font-semibold">Tenant-aware access</p>
                <p className="mt-1 text-xs leading-5 text-tavaura-ink/70">
                  Your workspace resolves from the authenticated merchant identity.
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/70 p-4 shadow-tavaura-sm backdrop-blur">
                <LockKeyhole className="mb-3 text-tavaura-cocoa" size={22} />
                <p className="text-sm font-semibold">JWT protected</p>
                <p className="mt-1 text-xs leading-5 text-tavaura-ink/70">
                  Admin calls use Bearer auth against the Tavaura API.
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-2xl shadow-tavaura-ink/10 backdrop-blur-xl sm:p-7">
            <div className="rounded-[1.5rem] border border-tavaura-ink/10 bg-gradient-to-b from-white to-tavaura-bg/60 p-5 sm:p-6">
              <div className="mb-6 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
                  Secure sign in
                </p>
                <h2 className="text-2xl font-semibold text-tavaura-ink">
                  Welcome back
                </h2>
                <p className="text-sm text-tavaura-ink/70">
                  Use your merchant admin credentials.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-tavaura-ink" htmlFor="admin-email">
                    Email address
                  </label>
                  <input
                    id="admin-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-tavaura-ink/15 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
                    placeholder="merchant@example.com"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-tavaura-ink" htmlFor="admin-password">
                    Password
                  </label>
                  <input
                    id="admin-password"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-tavaura-ink/15 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
                    placeholder="Your password"
                  />
                </div>

                {error && (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  {isSubmitting ? "Signing in..." : "Sign in"}
                  {!isSubmitting && <ArrowRight size={16} />}
                </button>
              </form>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
