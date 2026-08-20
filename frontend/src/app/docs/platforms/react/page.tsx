import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

const MODULE_SNIPPET = `import { initTavaura } from "@tavaura/sdk";

initTavaura("#tavaura-widget", {
  tenantId: "YOUR_TENANT_ID",
  mode: "avatar-first"
});`;

export default function ReactDocsPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Platforms
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          React / SPA installation
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Start with the simple script tag, or opt into a module build for advanced setups.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Recommended: script snippet</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          The easiest way to integrate on single-page apps is to drop the script into your HTML shell.
        </p>
        <CodeBlock code={EMBED_SNIPPET} language="html" />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Advanced: module import (future)</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          For bundler setups, you can import from the SDK directly. This is optional; most teams should start with the script snippet first.
        </p>
        <CodeBlock code={MODULE_SNIPPET} language="ts" />
      </section>
      <DocsBackToRoot />
    </div>
  );
}
