// PLACEHOLDER — Replace this entire page with the user's requested app content.
// Do NOT create a new page and link here. Build directly in this file.
export default function Home() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="border-b border-zinc-100 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-14 sm:px-8 sm:py-16 lg:px-12">
          <div className="mb-10">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/govtech-logo.gif"
              alt="GovTech Singapore"
              width={280}
              height={120}
              className="-ml-2"
            />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl lg:text-5xl">
            Build your app with AI
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
            Describe what you want in plain English using the chat panel on the left.
            The AI will build pages, add features, and style your app — no coding required.
          </p>
        </div>
      </section>

      {/* Getting Started */}
      <section className="mx-auto max-w-7xl px-6 py-12 sm:px-8 lg:px-12">
        <h2 className="text-xl font-semibold text-zinc-900">Getting Started</h2>
        <p className="mt-1 text-base text-zinc-500">Follow these steps to build your application</p>

        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Step 1 */}
          <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-5 space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#5925DC] text-sm font-bold text-white">
              1
            </div>
            <h3 className="text-base font-medium text-zinc-900">Describe your idea</h3>
            <p className="text-sm leading-5 text-zinc-600">
              Use the chat panel to tell the AI what you want to build. Be as specific or as vague
              as you like — it will ask if it needs more detail.
            </p>
          </div>

          {/* Step 2 */}
          <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-5 space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#5925DC] text-sm font-bold text-white">
              2
            </div>
            <h3 className="text-base font-medium text-zinc-900">Watch it build</h3>
            <p className="text-sm leading-5 text-zinc-600">
              The AI will create components, add styling, and wire up functionality.
              You&apos;ll see changes appear in the preview pane in real-time.
            </p>
          </div>

          {/* Step 3 */}
          <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-5 space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#5925DC] text-sm font-bold text-white">
              3
            </div>
            <h3 className="text-base font-medium text-zinc-900">Iterate and save</h3>
            <p className="text-sm leading-5 text-zinc-600">
              Ask for changes, add features, or refine the design. When you&apos;re happy,
              hit Save to push your code to the repository.
            </p>
          </div>
        </div>
      </section>

      {/* Example Prompts */}
      <section className="border-t border-zinc-100 bg-zinc-50/50">
        <div className="mx-auto max-w-7xl px-6 py-12 sm:px-8 lg:px-12">
          <h2 className="text-xl font-semibold text-zinc-900">Try these prompts</h2>
          <p className="mt-1 text-base text-zinc-500">Copy any of these into the chat to get started</p>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Build a dashboard with stat cards showing total users, revenue, and active projects&rdquo;
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Create a team directory with search, showing name, role, department, and email&rdquo;
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Add a contact form with name, email, subject, and message fields&rdquo;
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Build a task tracker with status columns: To Do, In Progress, Done&rdquo;
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Create a landing page with hero section, feature highlights, and a CTA button&rdquo;
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
              <p className="text-base text-zinc-700">
                &ldquo;Add a settings page with tabs for General, Notifications, and Security&rdquo;
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Tips */}
      <section className="border-t border-zinc-100">
        <div className="mx-auto max-w-7xl px-6 py-12 sm:px-8 lg:px-12">
          <h2 className="text-xl font-semibold text-zinc-900">Tips</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1">
              <p className="text-base font-medium text-zinc-900">Be specific</p>
              <p className="text-sm text-zinc-500">
                &ldquo;Add a table with 5 columns&rdquo; works better than &ldquo;add some data&rdquo;
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-base font-medium text-zinc-900">Iterate freely</p>
              <p className="text-sm text-zinc-500">
                Ask for changes as many times as you want — &ldquo;make it more compact&rdquo; or &ldquo;change the color&rdquo;
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-base font-medium text-zinc-900">Attach screenshots</p>
              <p className="text-sm text-zinc-500">
                Upload a screenshot of a design you like and say &ldquo;make it look like this&rdquo;
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-base font-medium text-zinc-900">Save often</p>
              <p className="text-sm text-zinc-500">
                Hit Save to push your changes to the repo — you can always come back later
              </p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
