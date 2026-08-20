import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

export default function DocsHomePage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Getting started
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          Getting started
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Embed Tavaura to let shoppers try outfits on avatars or their own photos. Paste a tiny snippet and the widget handles the rest. Works with Shopify, WooCommerce, Wix, Squarespace, custom sites, and SPAs.
        </p>
      </header>

      <section className="space-y-4">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Quick install</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Drop this snippet into your theme and Tavaura will render a &quot;Try on with Tavaura&quot; entry point on your product pages.
        </p>
        <CodeBlock code={EMBED_SNIPPET} language="html" />
        <ul className="space-y-2 text-sm sm:text-base text-tavaura-ink/80 list-disc list-inside">
          <li>No build step required.</li>
          <li>No changes to your backend.</li>
          <li>Tavaura automatically inserts the try-on button near the Add to cart area.</li>
        </ul>
      </section>
      <DocsBackToRoot />
    </div>
  );
}
