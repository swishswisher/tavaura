import { CodeBlock } from "@/components/docs/CodeBlock";
import { DocsBackToRoot } from "@/components/docs/DocsBackToRoot";

const EMBED_SNIPPET = `<script src="https://cdn.tavaura.com/sdk/v1.js"></script>
<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "avatar-first"
  });
</script>`;

const PHOTO_FIRST_SNIPPET = `<script>
  Tavaura.init({
    tenantId: "YOUR_TENANT_ID",
    mode: "photo-first"
  });
</script>`;

export default function InstallationPage() {
  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tavaura-ink/70">
          Installation
        </p>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-tavaura-ink">
          Installation snippet
        </h1>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Get your tenant ID, paste the snippet, and verify the try-on button shows up on your product pages.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Step 1 — Get your Tenant ID</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Your Tenant ID comes from the Tavaura dashboard. For now, we&apos;ll provide it during onboarding.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Step 2 - Paste the snippet into your theme</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Add this to your site template (usually before the closing <code className="font-mono text-xs">&lt;/head&gt;</code> tag).
        </p>
        <CodeBlock code={EMBED_SNIPPET} language="html" />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Step 3 — Verify the widget appears</h2>
        <ul className="space-y-2 text-sm sm:text-base text-tavaura-ink/80 list-disc list-inside">
          <li>Open any product page.</li>
          <li>Look for the &quot;Try on with Tavaura&quot; button near Add to cart.</li>
          <li>If it’s missing, check the platform guides to confirm where to paste the snippet.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg sm:text-xl font-semibold text-tavaura-ink">Optional: configure modes</h2>
        <p className="text-sm sm:text-base leading-relaxed text-tavaura-ink/80">
          Switch to photo-first mode if you prefer selfies as the default.
        </p>
        <CodeBlock code={PHOTO_FIRST_SNIPPET} language="html" />
      </section>
      <DocsBackToRoot />
    </div>
  );
}
