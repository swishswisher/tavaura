const EXPERIENCES = [
  {
    title: "Outfit try-on",
    badge: "Apparel",
    body: "Let shoppers layer tops, bottoms and outerwear on avatars or selfies so they can see the full look before they buy.",
  },
  {
    title: "Lipstick & cosmetics",
    badge: "Cosmetics",
    body: "Preview lipstick shades and simple face overlays on uploaded photos, so buyers can compare tones that match their skin.",
  },
  {
    title: "Saved avatars & looks",
    badge: "Profiles",
    body: "Give returning shoppers a familiar avatar and wardrobe so they can quickly build new looks from your latest drops.",
  },
  {
    title: "Shareable looks",
    badge: "Social",
    body: "Generate clean exports of styled avatars or selfies that shoppers can share, helping your products travel further.",
  },
];

export function ExperiencesSection() {
  return (
    <section className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-semibold text-tavaura-ink sm:text-3xl">Experiences you can offer</h2>
          <p className="mt-3 text-sm text-tavaura-ink/80 sm:text-base">
            Turn static product shots into interactive try-ons for outfits, cosmetics, and stylized avatars.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:gap-8">
          {EXPERIENCES.map((item) => (
            <article
              key={item.title}
              className="flex flex-col gap-3 rounded-2xl border border-white/40 bg-white/70 p-5 shadow-lg shadow-black/5 backdrop-blur transition-shadow hover:shadow-xl hover:shadow-black/10 sm:p-6"
            >
              <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/60">
                <span className="rounded-full bg-tavaura-ink px-2 py-0.5 text-[0.65rem] text-white">
                  {item.badge}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-tavaura-ink sm:text-base">{item.title}</h3>
              <p className="text-xs sm:text-sm leading-relaxed text-tavaura-ink/80">{item.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
