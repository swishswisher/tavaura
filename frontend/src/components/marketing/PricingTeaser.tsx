export function PricingTeaser() {
  return (
    <section id="pricing" className="py-16 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-white/20 bg-white/80 p-6 text-center shadow-lg shadow-black/5 backdrop-blur sm:p-8 lg:p-10">
          <h2 className="text-2xl font-semibold text-tavaura-ink sm:text-3xl">
            Pricing that scales with your store
          </h2>
          <p className="mt-3 text-sm text-tavaura-ink/80 sm:text-base">
            Simple plans for boutiques, brands, and everything in between.
          </p>
          <p className="mt-2 text-xs text-tavaura-ink/60 sm:text-sm">Full pricing coming soon.</p>

          <div className="mt-6 flex justify-center">
            <a
              href="#contact"
              className="inline-flex items-center justify-center rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-tavaura-ink/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-tavaura-ink"
            >
              Talk to us about pricing
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
