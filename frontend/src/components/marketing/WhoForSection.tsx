const AUDIENCES = [
  {
    label: "Fashion brands",
    description:
      "Collections, capsules, and drops that deserve to be seen on real bodies, not just flat grids.",
  },
  {
    label: "Online boutiques",
    description:
      "Curated pieces from multiple labels where fit and vibe matter as much as price.",
  },
  {
    label: "Cosmetics merchants",
    description:
      "Lipstick, tints, and simple face products that benefit from shade previews on real faces.",
  },
  {
    label: "Marketplaces",
    description:
      "Multi-vendor platforms that want a consistent try-on layer across many storefronts.",
  },
  {
    label: "DTC startups",
    description:
      "Young brands that need every visitor to feel confident enough to hit Add to cart.",
  },
  {
    label: "Creators & influencers",
    description:
      "Personal brands selling merch or collabs with audiences who love to try the look first.",
  },
];

export function WhoForSection() {
  return (
    <section
      id="who"
      className="bg-gradient-to-b from-white via-tavaura-bg/50 to-white py-16 sm:py-20 lg:py-24"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10 sm:mb-12">
          <h2 className="text-xs sm:text-sm font-semibold tracking-[0.16em] text-tavaura-ink/70 uppercase">
            Who Tavaura is for
          </h2>
          <p className="mt-3 text-lg sm:text-xl text-tavaura-ink/85 max-w-2xl mx-auto">
            From indie boutiques to global marketplaces, Tavaura adds try-on magic to the stores your shoppers already love.
          </p>
        </div>

        <div className="rounded-3xl bg-white/80 shadow-lg shadow-black/5 ring-1 ring-black/5 px-4 py-6 sm:px-6 sm:py-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {AUDIENCES.map((aud) => (
              <article
                key={aud.label}
                className="h-full rounded-2xl bg-white shadow-sm shadow-black/5 ring-1 ring-slate-100 px-5 py-4 sm:px-6 sm:py-5 flex flex-col gap-2 hover:shadow-md hover:shadow-black/10 hover:-translate-y-0.5 transition-transform transition-shadow cursor-pointer"
              >
                <h3 className="text-sm sm:text-base font-semibold text-tavaura-ink">
                  {aud.label}
                </h3>
                <p className="text-xs sm:text-sm text-tavaura-ink/75 leading-relaxed">
                  {aud.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
