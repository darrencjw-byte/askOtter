import Link from "next/link";

// TODO: Replace with your team's actual contact email
const contactEmail = "your-team@agency.gov.sg";

export default function TermsPage() {
  return (
    <div className="bg-white">
      <section className="mx-auto max-w-3xl px-6 py-16 sm:px-8">
        <nav aria-label="Breadcrumb" className="mb-8 flex items-center gap-2 text-sm text-zinc-500">
          <Link href="/" className="hover:text-zinc-900 underline-offset-4 hover:underline">
            Home
          </Link>
          <span aria-hidden="true">/</span>
          <span className="text-zinc-900">Terms of Use</span>
        </nav>

        <h1 className="text-3xl font-semibold text-zinc-950">
          Terms of Use
        </h1>
        <p className="mt-5 text-base leading-7 text-zinc-700">
          Terms of Use coming soon. Contact{" "}
          <a
            href={`mailto:${contactEmail}`}
            className="font-medium text-zinc-950 underline underline-offset-4"
          >
            {contactEmail}
          </a>{" "}
          for questions.
        </p>
      </section>
    </div>
  );
}
