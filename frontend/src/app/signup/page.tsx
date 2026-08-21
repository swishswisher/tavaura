import Link from "next/link";
export default function SignupPage() {
  return (
    <main className="min-h-screen bg-tavaura-bg px-4 py-12 sm:px-6 lg:px-10 lg:py-16">
      <div className="mx-auto w-full max-w-3xl space-y-6 sm:space-y-8">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight text-tavaura-ink sm:text-4xl">
            Tavaura access is invitation-only
          </h1>
          <p className="max-w-2xl text-sm sm:text-base text-tavaura-ink/75">
            Merchant workspaces are created by the Tavaura platform team. An
            administrator will send a secure, expiring invitation to your work
            email when your workspace is ready.
          </p>
        </div>

        <div className="tavaura-glass-soft rounded-3xl px-5 py-6 shadow-tavaura sm:px-6 sm:py-7">
          <p className="text-sm text-tavaura-ink/75">
            Already invited or already have an account?
          </p>
          <Link
            href="/admin/login"
            className="mt-4 inline-flex rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-tavaura-white shadow-sm transition hover:bg-tavaura-ink/90"
          >
            Sign in to your workspace
          </Link>
        </div>

        <div className="text-sm text-tavaura-ink/70">
          <Link href="/" className="underline hover:text-tavaura-ink">
            Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}
