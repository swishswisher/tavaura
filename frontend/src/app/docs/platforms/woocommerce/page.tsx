import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

export default function WooCommerceDocsPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Platforms
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          WooCommerce installation
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Add the Tavaura embed to your WordPress theme so try-ons appear on product pages.
        </p>
      </header>

      <section className="space-y-3">
        <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base text-tavaura-ink/80">
          <li>In WordPress admin, go to Appearance ? Theme File Editor, or use a header/footer script plugin.</li>
          <li>Paste the snippet in the <code className="font-mono text-xs">&lt;head&gt;</code> of your active theme.</li>
          <li>Save and visit a product page.</li>
        </ol>
      </section>

      <CodeBlock code={EMBED_SNIPPET} language="html" />
      <DocsBackToRoot />
    </div>
  );
}
