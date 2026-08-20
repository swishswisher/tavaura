import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

export default function CustomHtmlDocsPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Platforms
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          Custom HTML site
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          For simple sites, paste the embed snippet directly into your HTML template.
        </p>
      </header>

      <section className="space-y-3">
        <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base text-tavaura-ink/80">
          <li>Open your HTML template.</li>
          <li>Paste the snippet before the closing <code className="font-mono text-xs">&lt;/head&gt;</code> tag.</li>
          <li>Optionally include a container in your product layout where Tavaura can attach later.</li>
        </ol>
      </section>

      <CodeBlock code={EMBED_SNIPPET} language="html" />
      <DocsBackToRoot />
    </div>
  );
}
