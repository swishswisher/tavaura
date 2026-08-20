import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

export default function WixDocsPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Platforms
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          Wix installation
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Add the snippet through Wix custom code so Tavaura loads on your product pages.
        </p>
      </header>

      <section className="space-y-3">
        <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base text-tavaura-ink/80">
          <li>Open your site in the Wix Editor.</li>
          <li>Use the custom code / tracking code area to add scripts.</li>
          <li>Paste the snippet to load on all pages or limit to product pages.</li>
          <li>Publish and test on a product page.</li>
        </ol>
      </section>

      <CodeBlock code={EMBED_SNIPPET} language="html" />
      <DocsBackToRoot />
    </div>
  );
}
