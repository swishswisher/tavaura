import React from "react";

const STEPS = [
  {
    id: 1,
    title: "Plug Tavaura into your store",
    body: "Drop a tiny snippet into Shopify, WooCommerce, Squarespace or your custom stack. Tavaura opens as a focused try-on panel, not a new site.",
  },
  {
    id: 2,
    title: "Sync your products",
    body: "Upload product shots or connect your catalog. Our tools prepare garments for avatar layering and selfie overlays.",
  },
  {
    id: 3,
    title: "Let shoppers try looks",
    body: "Shoppers build stylized avatars or upload a photo, then layer outfits and lipstick in a few taps.",
  },
  {
    id: 4,
    title: "See what converts",
    body: "Dashboards show which looks, sizes and colors people actually try—so you can tune inventory and campaigns.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-16 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-semibold text-tavaura-ink sm:text-3xl">How Tavaura works</h2>
          <p className="mt-3 text-sm text-tavaura-ink/80 sm:text-base">
            From snippet to styled avatars and selfies in four simple steps.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {STEPS.map((step) => (
            <div
              key={step.id}
              className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-white/40 p-4 backdrop-blur shadow-lg shadow-black/5 transition-shadow hover:shadow-xl hover:shadow-black/10 sm:p-5"
            >
              <div className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-tavaura-ink text-xs font-semibold text-white">
                {step.id}
              </div>
              <h3 className="text-sm font-semibold text-tavaura-ink sm:text-base">{step.title}</h3>
              <p className="text-xs text-tavaura-ink/80 sm:text-sm">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
