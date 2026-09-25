---
name: "self-heal"
description: "Detect and fix build errors after file changes. Run after every set of edits — checks dev server logs, then runs a TypeScript check (`tsc --noEmit`) to catch type/import errors cheaply. Does not run a full production build — see Verification Checklist for why."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# Skill: Self-Heal Build Errors

Automatically detect and fix build errors from the dev server after making changes.

## When to use

Run this skill **once per response** — after ALL the files for the
current user request are written, not after each individual file, and
not mid-way through a multi-file feature. Run it right before responding
to the user, not as a per-file habit.

## Steps

1. **Check dev server health:**
```bash
tail -30 /var/log/devserver.err 2>/dev/null | grep -E "Error:|error TS|SyntaxError|Module not found|Cannot find module|Expected|Unexpected token|npm ERR!|ECONNREFUSED|fetch failed|Invariant:|NEXT_NOT_FOUND"
```

2. **If errors found**, read the full error context:
```bash
tail -50 /var/log/devserver.err
```

3. **Parse the error** — identify:
   - Which file has the error (look for file paths like `./src/app/page.tsx`)
   - What line number (look for `:123:` patterns)
   - What type of error (missing import, syntax, type mismatch)

**Before treating a match as a live problem, confirm it's current, not a
stale line still sitting in the tail window.** A rolling log keeps old
entries around after they're already fixed — e.g. `Module not found` for a
file you just created can be the compiler's error from *before* the file
existed, not a sign the import is still broken right now. Don't conclude
"still broken" purely because the string appears somewhere in the last 30-50
lines. Confirm it's live with either:
- The file genuinely doesn't exist (`ls` the exact path from the error), or
- A fresh trigger (`curl` the page, or touch/save a file) followed by a new
  `tail`, and the same error reappears in the newly-added lines — not just
  present somewhere in the unchanged tail.
If the file exists and no fresh trigger reproduces it, it's stale — move on
without "fixing" something that isn't actually broken.

4. **Fix the root cause** — common fixes:
   - `Module not found` → check import path, install missing package
   - `Expected '</'` → unclosed JSX tag, fix the component
   - `error TS` → type error, fix the type
   - `SyntaxError: Unexpected` → syntax issue, check for typos
   - `Cannot find module` → wrong import path or missing dependency

5. **Verify the fix:**
```bash
sleep 2 && tail -10 /var/log/devserver.err 2>/dev/null | grep -Ec "Error:|error TS|SyntaxError|Module not found|Cannot find module|Expected|Unexpected token|npm ERR!|ECONNREFUSED|fetch failed|Invariant:|NEXT_NOT_FOUND"
```
   Reuse the exact same pattern as step 1 — a narrower one here (e.g. just
   `"Error:"`) misses lowercase signatures like `error TS2345`, which would
   report a lingering TypeScript error as 0 matches (false success).
   If count > 0, repeat from step 2 (max 3 attempts).

6. **Confirm dev server is running:**
```bash
supervisorctl status dev-server
```
   If FATAL/EXITED: `supervisorctl restart dev-server && sleep 5`

Run the type check (see Verification Checklist below) after this.

## Complete POC Build Failure Guide

**This routine check only runs `tsc --noEmit`, so only the "TypeScript
errors" section below is something it will actually surface on its
own.** The other sections are kept as reference for the categories `tsc
--noEmit` cannot see — build-time rendering, CSS pipeline, package/
dependency, and env-var issues only surface when an actual `npm run
build` runs (the real POC deploy, or a manual build). This skill does
not run that automatically anymore — see Verification Checklist below
for why, and what that trade-off means.

Before concluding a *TypeScript* error is "pre-existing" or "unrelated
to my changes" and moving on, check the table below for a matching row.
Several have exact, verified one-line fixes (e.g. the
`sgds-elements.d.ts` row) — dismissing the error instead of applying the
documented fix means the user gets told the app is "ready" while it may
still have a real type error. A working dev server preview is NOT proof
the code is fully deploy-ready — the dev server, `tsc --noEmit`, and a
real production build are three different processes with different
failure modes.

### TypeScript errors (most common)

| Error | Fix |
|-------|-----|
| `Property 'sgds-*' does not exist on type 'JSX.IntrinsicElements'` | Ensure `sgds-elements.d.ts` exists at project root AND is listed in `tsconfig.json` include. Never use `@ts-expect-error`. |
| `Type 'X' is not assignable to type 'Y'` | Fix the type mismatch in the source file |
| `Cannot find name 'X'` | Missing import — add the import statement |
| `Property 'X' does not exist on type 'Y'` | Wrong property name or missing type definition |
| `Parameter 'X' implicitly has an 'any' type` | Add explicit type annotation |
| `'X' refers to a value, but is being used as a type` | Use `typeof X` or import the correct type |

### Module resolution errors

| Error | Fix |
|-------|-----|
| `Module not found: Can't resolve '@/generated/prisma/client'` | Run `npx prisma generate` — the client is gitignored and must be regenerated. Also ensure `"postinstall": "prisma generate"` is in package.json scripts. |
| `Cannot find module 'X'` | Run `npm install X` |
| `Module not found: Can't resolve '@/components/X'` | File doesn't exist — create it or fix the import path |
| `Module not found: Can't resolve '@/lib/X'` | File doesn't exist — create it or fix the import path |

### Build-time rendering errors

| Error | Fix |
|-------|-----|
| `PrismaClientInitializationError` / `Can't reach database` during build | Add `export const dynamic = 'force-dynamic'` to any page/route that uses Prisma. The POC build has no real DATABASE_URL. |
| `fetch failed` / `ECONNREFUSED` during build | A page is fetching from an API at build time. Add `export const dynamic = 'force-dynamic'` or gate the fetch with `if (typeof window === 'undefined' && process.env.BUILD_MODE)` |
| `used \`headers()\`/\`cookies()\` inside \`generateStaticParams\`` / `...without an HTTP request` / `used \`headers()\` inside "use cache"` (Next 16 splits this into several specific messages with their own error codes — E1134/E833/E838/E839 — confirmed against the installed next@16.2.9 source; the older generic `Invariant: headers() expects to have requestAsyncStorage` string doesn't exist in this version) | Server-side function called somewhere a build-time/cached/`after()` context can't provide a real request — add `export const dynamic = 'force-dynamic'` to the page/route, or move the call outside the cache/`after()` scope |
| `Cannot read properties of null (reading 'useContext')` on `/_global-error` or `/_not-found` | Ambient shell has `NODE_ENV=development` when `next build` runs inside this VIBER sandbox — confirmed reproducible, unrelated to Prisma. This is a sandbox-shell artifact only — the real Northflank Docker build (`templates/northflank/Dockerfile`) never sets `NODE_ENV`, so it wouldn't hit this on its own, which is why the template's `package.json` build script now ships with the fix pre-applied. If you see this error, first check whether that prefix is still there before re-adding it: `"build": "prisma generate && NODE_ENV=production next build --webpack"` (the prefix must sit directly on the `next build` command, not on an earlier command joined by `&&` — a `VAR=val cmd1 && cmd2` prefix only scopes to `cmd1`, confirmed by testing both forms). |

### CSS/Styling errors

| Error | Fix |
|-------|-----|
| `CssSyntaxError: Unexpected }` | Stray closing brace in globals.css — check bracket matching |
| `Error evaluating Node.js code` in CSS file | Invalid CSS syntax — check the globals.css file for errors |
| SGDS CSS import errors | The 3 SGDS imports (`themes/day.css` → `css/sgds.css` → `css/utility.css`, in that order) must live in their own dedicated CSS file (e.g. `src/app/sgds.css`), imported as its own stylesheet — never merged into the same file as `@import "tailwindcss"`. Missing `utility.css` means all `sgds:` classes silently produce no output; merging it into the same file as Tailwind's own import means EVERY unprefixed Tailwind utility (not just `sgds:` ones — plain `flex`, `p-4`, all of them) silently stops generating instead. |

### Next.js specific errors

| Error | Fix |
|-------|-----|
| `You're importing a component that needs 'useState'` | Add `"use client"` at top of the file |
| `Event handlers cannot be passed to Client Component props` | The component needs `"use client"` |
| `Unsupported Server Component type: undefined` | A default export is missing or the file has a syntax error |
| `Error: NEXT_NOT_FOUND` during static generation | A `notFound()` is called at build time — add `export const dynamic = 'force-dynamic'` |
| `output: "standalone"` related errors | Do NOT remove `output: "standalone"` from next.config.ts |

### Package/dependency errors

| Error | Fix |
|-------|-----|
| `npm ERR! peer dep` | Add `--legacy-peer-deps` or fix the version conflict |
| `npm ERR! ERESOLVE` | Version conflict — check package.json for incompatible versions |
| `prisma generate` fails | Ensure `prisma` is in devDependencies and `@prisma/client` in dependencies |

### Environment variable errors

| Error | Fix |
|-------|-----|
| `BETTER_AUTH_SECRET is required` | The build sets `BETTER_AUTH_SECRET=build-placeholder` automatically. If your code reads it at build time, guard with `process.env.BUILD_MODE` |
| Any env var required at build time | The POC builder injects placeholders. Your code should NOT validate env vars at build time — only at request time. |

## Verification Checklist

There is no observable "before the user saves" moment — the Save button
does a plain `git commit`/`push` with no build gate of its own (confirmed
against the actual Save route), and there's no other hook that tells
this skill when a full production build is about to matter. Run:

```bash
npx tsc --noEmit 2>&1 | tail -50

# If it fails: grep the error against the "TypeScript errors" section of
# the Complete POC Build Failure Guide above BEFORE doing anything else —
# do not treat it as "pre-existing" as a substitute for applying a
# documented fix. Fix and retry (max 3 attempts).
```

**Why this skill runs `tsc --noEmit` instead of a full `npm run build`:**
VIBER session containers run on a small, fixed resource plan shared by
four services at once (`caddy`, `code-server`, `agent-sidecar`,
`dev-server`) — as little as 1 shared vCPU. A full `npm run build` maxes
out that single core while the dev server is trying to serve the live
preview on the same core. Confirmed on a real session: firing a second
`npm run build` before the first returned caused a SIGKILL (OOM), and a
separate session that ran 6 of these checks back-to-back saw the dev
server's own compile times climb from ~10s to ~39s and stay there,
alongside a string of dev-server restarts nobody triggered — the
container had simply run out of CPU. Since this check runs once per
response, running a full build every time was untenable on this
resource plan. `tsc --noEmit` gives most of the everyday error-catching
value (missing imports, wrong types, `sgds-*` prop mistakes) at a small
fraction of the CPU/memory cost.

**What this trade-off means — read this before telling a user something
is "ready":** `tsc --noEmit` passing is NOT proof the POC deploy will
succeed. It only rules out TypeScript errors. It does NOT catch CSS
pipeline bugs (e.g. an SGDS import silently breaking Tailwind
site-wide), build-time rendering errors
(`PrismaClientInitializationError`, misused `headers()`/`cookies()`),
package/dependency install failures, or missing build-time env vars —
see the other sections of the Complete POC Build Failure Guide above
for what those look like. Those only surface in an actual `npm run
build`, which this skill does not run automatically. If the user is
about to deploy to POC and it genuinely matters, say so plainly and
offer to run a real `npm run build` as a one-off check — don't imply
`tsc --noEmit` passing already covers it.

**Restart the dev server only when one of these is actually true — do
NOT restart automatically after every check:**
- This response edited `package.json`, `next.config.ts`, or `.env`
- `supervisorctl status dev-server` shows FATAL/EXITED

**Before restarting for any other reason ("the preview looks down",
"curl/tail seems stuck", "the server seems to have gone quiet"), run
`supervisorctl status dev-server` first.** This call is nearly free and
answers definitively — it does not wait on the app itself the way
`curl`/`tail` do. A slow or empty response from `curl`/`tail` is NOT by
itself evidence of a crash: these containers run on a single shared CPU
core (confirmed via `cat /sys/fs/cgroup/cpu.stat` — sessions have been
observed throttled ~50% of scheduling periods), so `next dev` can go
quiet for real stretches under load without being down. Restarting when
it wasn't actually down just adds another CPU-heavy cold compile on top
of the load that made it look slow in the first place — worsening the
exact problem you were reacting to.

```bash
supervisorctl restart dev-server
```

**Restart sparingly — confirmed from a real VIBER session log: 34
dev-server restarts happened in one 46-minute session building a single
feature**, roughly one every 80 seconds. Each restart has a real window
where the preview isn't reachable (dev server down between exit and
"entered RUNNING state"); the more restarts, the more chances a user's
refresh lands in that gap and the preview appears broken when nothing is
actually wrong. Batch all files for the current response, verify once,
restart only if actually warranted by the list above.

## Rules

- Never report success to the user if errors remain — this includes a
  failing `tsc --noEmit` even when the dev server preview looks fine.
  They are separate processes; a working preview is never proof the
  type check passes.
- Never dismiss a type error as "pre-existing" or "unrelated" without
  first checking the Complete POC Build Failure Guide's TypeScript
  errors section above for a matching, documented fix.
- Fix ALL errors in one pass, not one at a time.
- Never say a change is "ready to deploy" or "build-ready" based on
  `tsc --noEmit` alone — it doesn't cover CSS, build-time rendering,
  package, or env-var failures (see Verification Checklist above). If
  deploy-readiness genuinely matters for this response, say so and
  offer to run a real `npm run build` as a separate, explicit step.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
