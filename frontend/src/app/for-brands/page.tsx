import Image from "next/image";
import Link from "next/link";
import { Globe, LineChart, RotateCw, Zap } from "lucide-react";

const VALUE_TILES = [
  {
    title: "Increase conversions",
    body: "Shoppers who visualize outfits are far more likely to buy.",
    icon: LineChart,
  },
  {
    title: "Reduce returns",
    body: "Better expectations lead to fewer sizing and fit-related returns.",
    icon: RotateCw,
  },
  {
    title: "Works on any platform",
    body: "Shopify, WooCommerce, Squarespace, Wix, headless stacks — we plug in fast.",
    icon: Globe,
  },
  {
    title: "Setup in minutes",
    body: "Drop in a snippet, keep your brand, and launch a focused try-on panel.",
    icon: Zap,
  },
];

const WORKFLOW_STEPS = [
  {
    title: "Install the snippet",
    body: "Add a lightweight embed that keeps shoppers on your site.",
  },
  {
    title: "Sync your products",
    body: "Connect your catalog or upload key looks you want to feature.",
  },
  {
    title: "Shoppers try looks instantly",
    body: "Avatars or selfies layered with your garments and shades in real time.",
  },
];

const FEATURES = [
  {
    title: "Avatars that match their vibe",
    bullets: [
      "Skin tone, hairstyle, body type, pregnancy options",
      "Stylized but true-to-fit silhouettes",
      "Preset looks your team can curate",
    ],
  },
  {
    title: "Photo try-on mode",
    bullets: [
      "Upload a selfie with automatic background cleanup",
      "Layer garments or lipstick in seconds",
      "No downloads or app install required",
    ],
  },
  {
    title: "Real-time outfit preview",
    bullets: [
      "Mix colors, jackets, and accessories",
      "Shareable exports for campaigns",
      "Analytics-ready events for your team",
    ],
  },
];

export default function ForBrandsPage() {
  return (
    <div className="bg-white text-tavaura-ink">
      <div className="space-y-16 sm:space-y-20 lg:space-y-24 pb-16 sm:pb-20 lg:pb-24">
        <section className="pt-16 sm:pt-20 lg:pt-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-10 rounded-3xl border border-white/60 bg-gradient-to-br from-white via-tavaura-bg/60 to-white shadow-lg shadow-black/5 sm:gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-stretch px-6 py-10 sm:px-10 sm:py-14">
              <div className="space-y-6">
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-tavaura-ink/70">
                  For brands & retailers
                </p>
                <h1 className="text-3xl sm:text-4xl font-semibold leading-tight text-tavaura-ink">
                  Give your shoppers a try-on experience that actually converts
                </h1>
                <p className="text-base sm:text-lg text-tavaura-ink/80">
                  Tavaura helps fashion and beauty brands lift conversion, cut returns, and engage shoppers with avatars and selfie try-ons that feel tailored to their store.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/#contact"
                    className="rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-medium text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90"
                  >
                    Book a demo
                  </Link>
                  <Link
                    href="/#try-it-now"
                    className="rounded-full border border-tavaura-ink/20 bg-white/80 px-5 py-2.5 text-sm font-medium text-tavaura-ink transition hover:bg-tavaura-ink/5"
                  >
                    Try it now
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
              <h2 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">Why brands choose Tavaura</h2>
              <p className="mt-3 text-sm sm:text-base text-tavaura-ink/80">
                A try-on layer that works anywhere and converts like a premium fitting room.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {VALUE_TILES.map((tile) => {
                const Icon = tile.icon;
                return (
                  <article
                    key={tile.title}
                    className="flex h-full flex-col gap-3 rounded-2xl border border-white/50 bg-white/80 p-5 shadow-lg shadow-black/5 backdrop-blur hover:shadow-xl hover:shadow-black/10 transition-shadow"
                  >
                    <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-tavaura-ink text-tavaura-white">
                      <Icon size={18} />
                    </div>
                    <h3 className="text-base font-semibold text-tavaura-ink">{tile.title}</h3>
                    <p className="text-sm text-tavaura-ink/80">{tile.body}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mb-8 text-center sm:mb-10">
              <h2 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">How integration works</h2>
              <p className="mt-3 text-sm sm:text-base text-tavaura-ink/80">
                A three-step handoff that keeps your brand in control.
              </p>
            </div>
            <div className="flex flex-col items-start gap-8 rounded-2xl border border-white/50 bg-white/70 p-5 shadow-lg shadow-black/5 backdrop-blur sm:p-6 md:flex-row md:items-start md:justify-between">
              {WORKFLOW_STEPS.map((step, index) => (
                <div key={step.title} className="flex flex-1 items-start gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-tavaura-ink text-tavaura-white text-sm font-semibold">
                    {index + 1}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-semibold text-tavaura-ink">{step.title}</h3>
                    <p className="text-sm text-tavaura-ink/80">{step.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mb-8 text-center sm:mb-10">
              <h2 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">What your shoppers get</h2>
              <p className="mt-3 text-sm sm:text-base text-tavaura-ink/80">
                A polished try-on experience for avatars and selfies across your catalog.
              </p>
            </div>
            <div className="space-y-6">
              {FEATURES.map((feature) => (
                <article
                  key={feature.title}
                  className="flex flex-col gap-5 rounded-2xl border border-white/50 bg-white/80 p-5 shadow-lg shadow-black/5 backdrop-blur sm:flex-row sm:items-center sm:justify-between sm:p-6"
                >
                  <div className="flex-1 space-y-3">
                    <h3 className="text-base font-semibold text-tavaura-ink">{feature.title}</h3>
                    <ul className="space-y-2 text-sm text-tavaura-ink/80 list-disc list-inside">
                      {feature.bullets.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex-1">
                    <div className="overflow-hidden rounded-2xl border border-white/50 bg-gradient-to-br from-tavaura-bg to-white shadow-md shadow-black/5">
                      <Image
                        src="/images/tavaura-hero-avatars.png"
                        alt="Tavaura avatar preview"
                        width={640}
                        height={480}
                        className="h-full w-full object-cover"
                      />
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-3xl border border-white/60 bg-gradient-to-br from-white via-tavaura-bg/70 to-white px-6 py-10 shadow-xl shadow-black/5 sm:px-10 sm:py-12">
              <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] lg:items-center">
                <div className="space-y-4">
                  <h3 className="text-2xl sm:text-3xl font-semibold text-tavaura-ink">Ready to offer try-on?</h3>
                  <p className="text-sm sm:text-base text-tavaura-ink/80">
                    Give your shoppers a focused try-on panel that works on any storefront and keeps them buying with confidence.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Link
                      href="/#contact"
                      className="rounded-full bg-tavaura-ink px-5 py-2.5 text-sm font-medium text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90"
                    >
                      Contact us
                    </Link>
                    <Link
                      href="/#try-it-now"
                      className="rounded-full border border-tavaura-ink/20 bg-white/80 px-5 py-2.5 text-sm font-medium text-tavaura-ink transition hover:bg-tavaura-ink/5"
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
