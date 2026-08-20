"use client";

import { useState } from "react";
import { postJson } from "@/lib/api";

const COMMON_DOMAINS = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"];

function suggestEmailDomain(value: string): string | null {
  const lower = value.toLowerCase();
  const atIndex = lower.indexOf("@");
  if (atIndex === -1) return null;

  const local = lower.slice(0, atIndex);
  const domain = lower.slice(atIndex + 1);
  if (!domain || COMMON_DOMAINS.includes(domain)) return null;

  const suggestion = COMMON_DOMAINS.find((d) => d.startsWith(domain[0] ?? ""));
  return suggestion ? `${local}@${suggestion}` : null;
}

export function ContactSection() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [companyOrBrand, setCompanyOrBrand] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [emailSuggestion, setEmailSuggestion] = useState<string | null>(null);

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setEmail(value);
    setSuccess(false);
    setError(null);
    if (value.length > 5) {
      setEmailSuggestion(suggestEmailDomain(value));
    } else {
      setEmailSuggestion(null);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(false);

    if (!email || !message) {
      setError("Email and message are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await postJson<
        {
          name?: string;
          email: string;
          companyOrBrand?: string;
          message: string;
          context?: string;
        },
        { accepted: boolean; message?: string }
      >("/api/contact", {
        name: name || undefined,
        email,
        companyOrBrand: companyOrBrand || undefined,
        message,
        context: "general",
      });

      setSuccess(true);
      setName("");
      setEmail("");
      setMessage("");
      setCompanyOrBrand("");
      setEmailSuggestion(null);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message || "Something went wrong. Please try again.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section
      id="contact"
      className="rounded-3xl border border-tavaura-ink/10 bg-white/80 px-6 py-10 shadow-sm backdrop-blur-sm sm:px-8"
    >
      <div className="space-y-6">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tavaura-cocoa/80">
            Contact us
          </p>
          <h2 className="text-2xl font-semibold text-tavaura-ink">
            Let{"'"}s talk about your store
          </h2>
          <p className="text-sm text-tavaura-ink/80">
            Reach out with questions, integration plans, or feedback about your shopper experience.
            We{"'"}ll get back quickly with next steps.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-tavaura-ink" htmlFor="contact-name">
                Name (optional)
              </label>
              <input
                id="contact-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1 w-full rounded-xl border border-tavaura-ink/15 bg-white px-3 py-2 text-sm text-tavaura-ink shadow-sm outline-none focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink"
                placeholder="Your name"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-tavaura-ink" htmlFor="contact-company">
                Company / brand (optional)
              </label>
              <input
                id="contact-company"
                type="text"
                value={companyOrBrand}
                onChange={(event) => setCompanyOrBrand(event.target.value)}
                className="mt-1 w-full rounded-xl border border-tavaura-ink/15 bg-white px-3 py-2 text-sm text-tavaura-ink shadow-sm outline-none focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink"
                placeholder="Studio Aura"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-tavaura-ink" htmlFor="contact-email">
              Email address
            </label>
            <input
              id="contact-email"
              type="email"
              required
              value={email}
              onChange={handleEmailChange}
              className="mt-1 w-full rounded-xl border border-tavaura-ink/15 bg-white px-3 py-2 text-sm text-tavaura-ink shadow-sm outline-none focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink"
              placeholder="you@brand.com"
            />
            {emailSuggestion && (
              <p className="mt-1 text-xs text-tavaura-ink/70">
                Did you mean{" "}
                <button
                  type="button"
                  className="underline"
                  onClick={() => {
                    setEmail(emailSuggestion);
                    setEmailSuggestion(null);
                  }}
                >
                  {emailSuggestion}
                </button>
                ?
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-tavaura-ink" htmlFor="contact-message">
              Your message
            </label>
            <textarea
              id="contact-message"
              required
              rows={4}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              className="mt-1 w-full rounded-xl border border-tavaura-ink/15 bg-white px-3 py-2 text-sm text-tavaura-ink shadow-sm outline-none focus:border-tavaura-ink focus:ring-1 focus:ring-tavaura-ink"
              placeholder="Tell us about your store, use case, or questions..."
            />
          </div>

          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center">
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center justify-center rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-medium text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Sending..." : "Send message"}
            </button>
            {error && <p className="text-xs text-red-600">{error}</p>}
            {success && !error && (
              <p className="text-xs text-emerald-600">Message sent successfully.</p>
            )}
          </div>
        </form>
      </div>
    </section>
  );
}
