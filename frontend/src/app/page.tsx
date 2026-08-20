import Link from "next/link";
import { ContactSection } from "@/components/marketing/ContactSection";
import { ExperiencesSection } from "@/components/marketing/ExperiencesSection";
import { HeroArt } from "@/components/marketing/HeroArt";
import { HowItWorksSection } from "@/components/marketing/HowItWorksSection";
import { PricingTeaser } from "@/components/marketing/PricingTeaser";
import { WhoForSection } from "@/components/marketing/WhoForSection";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SiteShell } from "@/components/layout/SiteShell";
import { TryItNow } from "@/components/try-it-now/TryItNow";

const heroCtaClasses =
  "rounded-full px-5 py-2.5 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2";

export default function Home() {
  return (
    <>
      <SiteShell>
        <div className="space-y-16 sm:space-y-20">
          <section id="hero">
            <div className="rounded-3xl bg-gradient-to-b from-white to-tavaura-bg/60 px-6 py-12 shadow-lg sm:px-10 sm:py-16">
              <div className="grid items-center gap-10 text-center lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-stretch lg:text-left">
                <div className="space-y-6">
                  <div className="inline-flex items-center gap-2 rounded-full border border-tavaura-ink/10 bg-white/80 px-3 py-1 text-xs font-medium text-tavaura-ink/80 shadow-sm">
                    <span className="h-1.5 w-1.5 rounded-full bg-tavaura-cocoa" />
                    <span>
                      Early preview {"\u00b7"} Tavaura
                    </span>
                  </div>

                  <div className="space-y-4">
                    <h1 className="text-3xl font-semibold text-tavaura-ink sm:text-4xl md:text-5xl">
                      Tavaura {"\u2014"} giving aura to your avatar
                    </h1>
                    <p className="text-base text-tavaura-ink/80 sm:text-lg">
                      Tavaura lets shoppers virtually try on outfits and cosmetics in 3D {"\u2014"} using smart avatars or
                      their own photos {"\u2014"} with a plug-in that brands can embed in any online store.
                    </p>
                  </div>

                  <div className="flex flex-wrap justify-center gap-3 lg:justify-start">
                    <Link
                      href="#how-it-works"
                      className={`${heroCtaClasses} bg-tavaura-ink text-tavaura-white shadow-sm hover:bg-tavaura-ink/90`}
                    >
                      See how it works
                    </Link>
                    <Link
                      href="#for-brands"
                      className={`${heroCtaClasses} border border-tavaura-ink/15 bg-white/90 text-tavaura-ink hover:bg-tavaura-ink/5`}
                    >
                      For brands &amp; shops
                    </Link>
                  </div>
                </div>

                <div className="mt-6 lg:mt-0 lg:flex lg:h-full lg:justify-end">
                  <HeroArt />
                </div>
              </div>
            </div>
          </section>

          <TryItNow />

          <HowItWorksSection />
          <ExperiencesSection />
          <PricingTeaser />
          <WhoForSection />
          <ContactSection />
        </div>
      </SiteShell>
      <SiteFooter />
    </>
  );
}
