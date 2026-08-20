import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

export default function ShopifyDocsPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Platforms
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          Shopify installation
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Add the Tavaura snippet to your Shopify theme so shoppers can try outfits directly on product pages.
        </p>
      </header>

      <section className="space-y-3">
        <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base text-tavaura-ink/80">
          <li>Go to Online Store ? Themes ? Edit code.</li>
          <li>Open your main layout file (e.g. <span className="font-mono">theme.liquid</span>).</li>
          <li>Paste the snippet before the closing <code className="font-mono text-xs">&lt;/head&gt;</code> tag.</li>
          <li>Save and open a product page to see the &quot;Try on with Tavaura&quot; button.</li>
        </ol>
      </section>

      <CodeBlock code={EMBED_SNIPPET} language="html" />
      <DocsBackToRoot />
    </div>
  );
}
