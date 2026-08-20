"use client";

import Image from "next/image";
import Link from "next/link";
import { type FormEvent, useState } from "react";
import { postJson } from "@/lib/api";
import { Camera, Shield, Sparkles, User, Wand2, Zap } from "lucide-react";

const BENEFITS = [
  {
    title: "Try outfits instantly",
    body: "See yourself dressed in new looks in seconds.",
    icon: Zap,
  },
  {
    title: "Photo try-on mode",
    body: "Use your own photo to preview outfits and shades.",
    icon: Camera,
  },
  {
    title: "Your avatar, your style",
    body: "Skin tone, hair, vibe, aesthetic — make it feel like you.",
    icon: User,
  },
];

const FEELS_STEPS = [
  {
    title: "Pick your avatar or upload photo",
    icon: User,
  },
  {
    title: "Choose a look",
    icon: Sparkles,
  },
  {
    title: "See the transformation",
    icon: Wand2,
  },
];

function SavePreferencesForm() {
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("From widget: Save your preferences");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email) {
      setError("Email is required.");
      return;
    }
    setStatus("loading");
    setError(null);
    try {
      await postJson<
        { email: string; message: string; name?: string; companyOrBrand?: string; context?: string },
        { accepted: boolean; message?: string }
      >("/api/contact", {
        email,
        message: `Save preferences waitlist: ${note || "No additional note."}`,
        context: "save-preferences",
      });
      setStatus("success");
      setEmail("");
    } catch (err) {
      setStatus("error");
      const message = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setError(message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-xl border border-tavaura-ink/15 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink sm:max-w-xs"
          placeholder="you@example.com"
        />
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          className="w-full rounded-xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink sm:flex-1"
          placeholder="Optional note"
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-semibold text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {status === "loading" ? "Sending..." : "Join waitlist"}
        </button>
        {status === "success" && (
          <span className="text-xs font-medium text-emerald-600">Thanks — we’ll email you when it’s ready.</span>
        )}
        {status === "error" && <span className="text-xs font-medium text-red-600">{error}</span>}
      </div>
    </form>
  );
}

export default function ForShoppersPage() {
  return (
    <div className="bg-white text-tavaura-ink">
      <div className="space-y-16 sm:space-y-20 lg:space-y-24 pb-16 sm:pb-20 lg:pb-24">
        <section className="pt-16 sm:pt-20 lg:pt-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-10 rounded-3xl border border-white/60 bg-gradient-to-br from-white via-tavaura-bg/60 to-white shadow-lg shadow-black/5 sm:gap-12 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:items-stretch px-6 py-10 sm:px-10 sm:py-14">
              <div className="space-y-6">
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-tavaura-ink/70">
                  For shoppers
                </p>
                <h1 className="text-3xl sm:text-4xl font-semibold leading-tight text-tavaura-ink">
                  See yourself in every style — before you buy.
                </h1>
                <p className="text-base sm:text-lg text-tavaura-ink/80">
                  Try-on confidence with avatars that match your vibe or use your own photo. Test outfits, accessories, and cosmetics so you know what feels right.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/#try-it-now"
                    className="rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-medium text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90"
                  >
                    Try it now
                  </Link>
                  <Link
                    href="#how-it-feels"
                    className="rounded-full border border-tavaura-ink/20 bg-white/80 px-5 py-2.5 text-sm font-medium text-tavaura-ink transition hover:bg-tavaura-ink/5"
                  >
                    How it works
                  </Link>
                </div>
              </div>
              <div className="mt-6 lg:mt-0 lg:flex lg:h-full lg:justify-end">
                <div className="relative h-full w-full">
                  <div className="flex h-full w-full items-stretch justify-end">
                    <div className="h-full w-full max-w-[420px] overflow-hidden rounded-r-3xl rounded-l-none bg-white/90 shadow-xl shadow-black/10">
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
              </div>
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mb-8 text-center sm:mb-10">
              <h2 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">
                Why you’ll love Tavaura
              </h2>
              <p className="mt-3 text-sm sm:text-base text-tavaura-ink/80">
                Fast, friendly try-ons that help you pick outfits with confidence.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {BENEFITS.map((item) => {
                const Icon = item.icon;
                return (
                  <article
                    key={item.title}
                    className="flex h-full flex-col gap-3 rounded-xl bg-white p-6 shadow-md shadow-black/5 ring-1 ring-slate-100"
                  >
                    <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-tavaura-ink text-tavaura-white">
                      <Icon size={18} />
                    </div>
                    <h3 className="text-base font-semibold text-tavaura-ink">
                      {item.title}
                    </h3>
                    <p className="text-sm text-tavaura-ink/80">{item.body}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="how-it-feels">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mb-8 text-center sm:mb-10">
              <h2 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">
                How it feels
              </h2>
              <p className="mt-3 text-sm sm:text-base text-tavaura-ink/80">
                Three quick steps to see your new look.
              </p>
            </div>
            <div className="flex flex-col gap-8 rounded-2xl border border-white/50 bg-white/80 p-5 shadow-lg shadow-black/5 backdrop-blur sm:p-6 md:flex-row md:items-start md:justify-between">
              {FEELS_STEPS.map((step, idx) => {
                const Icon = step.icon;
                return (
                  <div key={step.title} className="flex flex-1 items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-tavaura-ink text-tavaura-white">
                      <Icon size={20} />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-tavaura-ink/70">
                        Step {idx + 1}
                      </p>
                      <h3 className="text-sm sm:text-base font-semibold text-tavaura-ink">
                        {step.title}
                      </h3>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-2xl border border-white/50 bg-gradient-to-br from-white to-tavaura-bg/60 p-6 shadow-lg shadow-black/5 backdrop-blur sm:p-8">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-tavaura-ink text-tavaura-white">
                    <Shield size={20} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-tavaura-ink">
                      Privacy first
                    </h3>
                    <p className="text-sm text-tavaura-ink/80">
                      Your images stay yours. We don’t sell them, and processing is temporary unless you choose to save an avatar.
                    </p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm text-tavaura-ink/80 list-disc list-inside sm:max-w-sm">
                  <li>Optional save for future try-ons.</li>
                  <li>Designed to be GDPR-friendly.</li>
                  <li>We’ll share more as we roll out the full privacy center.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section
          id="save-preferences"
          className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8"
        >
          <div className="mt-24 rounded-3xl bg-tavaura-bg px-6 py-10 shadow-xl sm:px-10 sm:py-12">
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
              Save your Tavaura looks
            </h2>
            <p className="mt-3 max-w-2xl text-sm sm:text-base text-tavaura-ink/70">
              Soon you’ll be able to create a Tavaura account, save avatars and outfits, and pick up where you left off
              across different stores. For the early preview, you can join the waitlist and we’ll invite you as soon as
              it’s ready.
            </p>
            <div className="mt-6">
              <SavePreferencesForm />
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-3xl border border-white/60 bg-gradient-to-br from-white via-tavaura-bg/70 to-white px-6 py-10 shadow-xl shadow-black/5 sm:px-10 sm:py-12">
              <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] lg:items-center">
                <div className="space-y-4">
                  <h3 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">
                    Ready to see yourself in new looks?
                  </h3>
                  <p className="text-sm sm:text-base text-tavaura-ink/80">
                    Jump into Tavaura and preview outfits, accessories, and lipstick before you buy.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Link
                      href="/#try-it-now"
                      className="rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-medium text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90"
                    >
                      Try it now
                    </Link>
                  </div>
                </div>
                <div className="lg:justify-self-end">
                  <div className="flex h-full w-full items-stretch justify-end">
                    <div className="h-full w-full max-w-[360px] overflow-hidden rounded-r-3xl rounded-l-none bg-white/90 shadow-xl shadow-black/10">
                      <Image
                        src="/images/tavaura-hero-avatars.png"
                        alt="Tavaura avatars preview"
                        width={720}
                        height={720}
                        className="h-full w-full object-cover"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
