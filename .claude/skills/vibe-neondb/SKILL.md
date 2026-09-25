---
name: "vibe-neondb"
description: "Add Prisma 7 + Neon PostgreSQL to an existing Next.js App Router app, using a Neon connection string the user brings themselves — Rabbit Deploy no longer provisions Neon databases through its own UI (retired in favor of Lakebase). Use when the user specifically names Neon/Postgres, OR when directed here by setup-db's routing. For a generic 'add a database'/'persist data'/'save this' request that doesn't name a provider, setup-db.md is the correct entry point instead — Lakebase is the default there, and Lakebase's own creation button in Rabbit Deploy still exists. Supersedes the older add-database skill — consolidates it with Prisma+Neon query/schema patterns and fixes a Prisma 7 driver-adapter gap that caused silent runtime failures."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: add-database
---

# vibe-neondb

Add Prisma 7 + PostgreSQL (Neon) readiness to an existing Next.js App Router
app. Do not convert the framework, initialize shadcn/ui, or add authentication
in this skill — those are separate stages. `vibe-govauth` (GovAuth/Better
Auth integration) never invokes this skill — it's always stateless and has
no database branch. This skill only runs when the user directly asks for a
database, separately from any auth setup.

---

## Step 0 — Check if a database already exists

```bash
echo "DATABASE_URL=${DATABASE_URL:+SET}"
```

**If already SET**, skip provisioning — verify connectivity (Step 4) and
proceed to whatever schema/wiring work was actually requested.

**If NOT set**, ask the user for a connection string directly — **Rabbit
Deploy no longer provisions Neon databases through its own UI** (that
capability has been retired in favor of Lakebase; there is no "Create
Neon DB" button anymore, don't guide anyone toward looking for one).
Treat this the same way `setup-db.md`'s Step 1 treats a genuinely
third-party database now:

> "Rabbit Deploy doesn't provision Neon databases directly anymore — for
> a database created here, Lakebase is the option available through the
> project page. If you specifically need Neon, bring your own connection
> string from an existing Neon project (or create one directly at
> neon.tech), and paste it here — I'll wire it up from there."

Once they paste a connection string, follow the **Quick-start** section
below to save it. **Never** tell them to look for a database-creation
button for Neon specifically — it doesn't exist; that button now only
creates Lakebase databases.

**Stop here.** Do not proceed with Prisma setup until `DATABASE_URL` is
confirmed available.

---

## Quick-start: user pastes a connection string directly in chat

If the user pastes a string like `postgresql://user:pass@host/dbname` in the
chat instead of using Env Vars:

1. Write it to `.env` (NOT `.env.local` — the Prisma CLI only reads `.env`):
   ```bash
   echo 'DATABASE_URL="<the-string-they-pasted>"' >> .env
   export DATABASE_URL="<the-string-they-pasted>"
   ```
2. **Never echo or log the full connection string back to the user** — it
   contains credentials. Confirm "Database URL saved" only.
3. Verify connectivity before anything else (Step 4).
4. If Prisma isn't installed yet, do Step 1 first, then return here.

---

## Step 1 — Install Prisma 7 with the driver adapter

Prisma 7's client is driver-adapter-based — installing `prisma` +
`@prisma/client` alone is **not sufficient**. A missing adapter doesn't fail
at `prisma generate` time; confirmed by direct test, it throws
`PrismaClientInitializationError` immediately when `new PrismaClient()` is
called with no adapter — not lazily at the first query. Confirm the adapter
is both installed AND passed into the `PrismaClient` constructor, not just
present as a transitive dependency.

```bash
npm install prisma@^7.0.0 --save-dev
npm install @prisma/client@^7.0.0 @prisma/adapter-pg@^7.0.0 pg
npx prisma init --datasource-provider postgresql
```

If Prisma is already installed, repair the existing setup instead of
duplicating config files.

Add a `postinstall` script so a clean deploy checkout (which never ran
`prisma generate` by hand) doesn't fail with `Module not found:
Can't resolve '.../generated/prisma/client'`:

```json
"scripts": {
  "postinstall": "prisma generate"
}
```

This template's baseline `package.json` ships without this script
intentionally — a project that never needs a database shouldn't carry it.
Only add it here, when this skill actually runs.

`prisma.config.ts` (already present in this template) does
`import "dotenv/config"` unconditionally. If `dotenv` isn't already
resolvable (`npm ls dotenv`), install it explicitly
(`npm install dotenv --save-dev`) — otherwise every `prisma generate`/
`prisma migrate` command, and the `postinstall` script itself, fails with
`Cannot find module 'dotenv/config'`.

---

## Step 2 — Configure environment

If the user added `DATABASE_URL` via Env Vars, it's already injected into
the container — **do NOT tell them to restart or end their VIBER session**
for this alone. Only a dev server restart is needed for the running process
to pick up a changed value:

```bash
supervisorctl restart dev-server
```

Add or update `.env.example` for documentation:
```bash
DATABASE_URL=""
```

Ensure `.env` is in `.gitignore` (should already be).

---

## Step 3 — Configure the Prisma schema

**Read the existing `prisma/schema.prisma` first — do not blindly
overwrite it.** This template ships with a real, working
`prisma/schema.prisma` already at the project root: it uses Prisma 7's
native `prisma-client` generator (NOT the legacy `prisma-client-js` — no
`previewFeatures = ["driverAdapters"]` needed, that flag is specific to
the older generator) with `output = "../src/generated/prisma"`, and it
already defines Better Auth's `User`/`Session`/`Account`/`Verification`
models. Confirmed by direct inspection of this exact template — this is
not a hypothetical default:

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

datasource db {
  provider = "postgresql"
}
```

- **Do not change the generator block** to `prisma-client-js` or add
  `previewFeatures` — that would be downgrading a working Prisma 7 native
  config to the legacy pattern for no reason.
- **Do not remove the existing `User`/`Session`/`Account`/`Verification`
  models** — they're already there by default in this template, not
  something this skill adds. If a caller (e.g. `vibe-entraid`) asks for
  these models "to be added," check first — they likely already exist;
  don't duplicate or redefine them.
- Add only new models needed by the current app or the module that
  requested a database, below the existing ones.
- The `datasource db` block intentionally has no `url = env("DATABASE_URL")`
  line in this template — the actual connection string is supplied via
  `prisma.config.ts`'s `datasource.url`, not inline in the schema file.
  Don't add that line back in; it would be redundant with, not
  complementary to, `prisma.config.ts`.

**Common schema patterns** (reference, adapt to the actual data model):

```prisma
// Enums
enum UserRole { REQUESTOR WORKSHOP_ADMIN SUPER_ADMIN }

// Defaults
model Example {
  id        String   @id @default(cuid())
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

// Json fields
model Config {
  notifications Json @default("{}")
}

// Unique constraints (e.g. OAuth account linking)
model Account {
  provider          String
  providerAccountId String
  @@unique([provider, providerAccountId])
}

// Relations
model Booking {
  categoryId String
  category   WorkshopCategory @relation(fields: [categoryId], references: [id])
}

// Single-row settings pattern
model Settings {
  id String @id @default("default")
  // ... fields with defaults
}
```

---

## Step 4 — Verify database readiness

```bash
npx prisma generate
```

If PostgreSQL is available:
```bash
npx prisma migrate dev --name init
```

If drift is detected because a table already exists (common when a prior
session created it directly), do NOT blindly reset the database. Diff the
live schema against `schema.prisma`, confirm they match, and baseline
instead of destroying data:
```bash
npx prisma migrate resolve --applied <migration>
```

If PostgreSQL is not reachable, stop and tell the user exactly what's wrong
— don't retry blindly. A quick standalone connectivity check:

```bash
npx tsx -e "
const { PrismaClient } = require('./src/generated/prisma/client');
const { PrismaPg } = require('@prisma/adapter-pg');
const p = new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }) });
p.\$connect().then(() => { console.log('OK - connected'); p.\$disconnect(); }).catch(e => console.error('FAIL:', e.message));
"
```

**Neon-specific:** `DATABASE_URL` includes `channel_binding=require` by
default. Tested directly against a live Neon connection (`pg@8.23.0` +
`@prisma/adapter-pg@7.9.1`): current versions connect fine with this
parameter left in place — do not strip it defensively, and never ask the
user to edit the env var itself.

**If you do see a connection rejected as insecure** after touching the
connection string, check whether something upstream stripped
`channel_binding` with a naive regex — `.replace(/[?&]channel_binding=require/, "")`
removes the `?` along with it when `channel_binding` is the first
parameter (Neon's default order), leaving a malformed
`...neondb&sslmode=require` with no leading `?`. `sslmode` then goes
unrecognized and Neon rejects the connection as insecure — confirmed by
direct test, this is worse than doing nothing. If stripping is ever
genuinely needed, use the URL API instead of regex:

```typescript
const url = new URL(process.env.DATABASE_URL || "")
url.searchParams.delete("channel_binding")
const connectionString = url.toString()
```

---

## Step 5 — Prisma Client Singleton

Prevents multiple `PrismaClient` instances during Next.js dev hot reload.
**Must use the driver adapter — a bare `new PrismaClient()` with no adapter
compiles fine but throws `PrismaClientInitializationError` on first real
query in Prisma 7.** Check `prisma.config.ts` for the actual generated
client import path before assuming a default:

```typescript
// src/lib/prisma.ts
import { PrismaClient } from "@/generated/prisma/client" // match this project's actual output path, not the Prisma 6 default
import { PrismaPg } from "@prisma/adapter-pg"

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

// channel_binding=require (Neon's default) does not need stripping —
// tested directly, current pg/@prisma/adapter-pg versions handle it fine.
// Do NOT reach for a regex strip here if a connection issue comes up —
// see Step 4's Neon-specific note for why that makes things worse, not better.
export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
  })

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma
```

---

## Step 6 — Wire the app to the database

Schema + migration + a working `PrismaClient` are necessary but NOT
sufficient for "the app uses the database." Close the loop:

- Create the server-side route(s)/server actions that read/write with
  Prisma (`src/app/api/**/route.ts` or server actions).
- Find every place the app currently persists this data another way —
  `localStorage`, in-memory arrays, JSON files — and replace those calls.
  Grep after editing to confirm nothing was left behind:
  ```bash
  grep -rn "localStorage" src/
  ```
- If this is brand-new persistence (no prior mechanism), still confirm the
  new UI actually calls the new route — not just that the route exists in
  isolation.

**If the thing being replaced is a mock/in-memory array already feeding
live client-side filtering, sorting, or search** (a dashboard or table the
user already approved before the database was added), default to
preserving that interactivity: fetch the full dataset once and keep
filtering/sorting/search running in the browser, rather than re-querying
the database on every filter change. Silently switching to a
per-filter-change database query changes the UX — filtering goes from
instant to a fetch/loading step — even though `design-system.md`'s
Implicit Requirements would still catch the *missing* loading state, it
won't catch the fact that a working instant-filter experience quietly
became a slower one. Only move filtering into the database query itself
when dataset size makes shipping the full set to the client genuinely
impractical, and say so explicitly rather than switching silently.

Add `export const dynamic = "force-dynamic"` to any page/route that queries
the database — Next.js static rendering fails if Prisma queries run at
build time.

---

## Step 7 — Verify end-to-end

Do not accept a single success as proof. Against the **running dev server**
(not a standalone script):

1. `curl` the API route to create a record.
2. `curl` it again in a **separate** request to confirm the record comes
   back — a value only living in server memory would still pass a single
   combined test but fail this one.
3. Query the database directly (short Prisma script, `prisma studio`, or
   raw SQL) to confirm the row is physically present in Postgres,
   independent of the app's own code path.
4. Load the page and confirm rendered data matches; grep the page source
   for the old storage mechanism to confirm it's gone.

Only report this stage as working after all four pass.

---

## Step 8 — Verify the app still builds

```bash
SELF_HEAL_BUILD_CHECK=1 npm run build
```

The env var routes output to `.next-buildcheck` instead of `.next` — this
keeps the check from colliding with the live dev server's own build
output (see self-heal.md). Keep it on every invocation below too.

If this fails, isolate whether your changes caused it before treating it as
a blocker:
```bash
git stash
SELF_HEAL_BUILD_CHECK=1 npm run build
git stash pop
```

- **If it fails identically on the pre-change code**, it's pre-existing —
  attempt a root-cause fix rather than only noting it. Check the build
  output for warnings immediately above the failure. In particular:
  **a stray `NODE_ENV=development` in the shell during a production build
  can corrupt React's dev/prod bundle selection during static
  prerendering**, producing errors like `Cannot read properties of null
  (reading 'useContext')` on Next's auto-generated `/_global-error` or
  `/_not-found` pages — this has nothing to do with the database work and
  everything to do with the ambient shell environment. Confirm by forcing
  the value directly (`NODE_ENV=production SELF_HEAL_BUILD_CHECK=1 npm run build`);
  if that alone fixes it, apply the fix at the script level:
  `"build": "prisma generate && NODE_ENV=production next build --webpack"`.
  Re-run standalone (no manual override) to confirm the fix holds, then
  restart the dev server to confirm the preview still serves correctly.
- **If it only fails after your changes**, fix it before reporting success.

---

## Seed data (optional)

`prisma/seed.ts`:
```typescript
import { PrismaClient } from "@/generated/prisma/client"
import { PrismaPg } from "@prisma/adapter-pg"

const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL! }),
})

async function main() {
  // Idempotent upserts, not blind creates
  await prisma.agency.upsert({
    where: { abbreviation: "GovTech" },
    update: { name: "Government Technology Agency" },
    create: { name: "Government Technology Agency", abbreviation: "GovTech" },
  })
}

main().then(() => prisma.$disconnect()).catch((e) => { console.error(e); process.exit(1) })
```

`package.json`:
```json
{ "prisma": { "seed": "tsx prisma/seed.ts" } }
```

Run: `npx prisma db seed`

---

## Common query patterns (reference)

```typescript
// Find many with includes
const bookings = await prisma.booking.findMany({
  include: { category: true, agency: true },
  orderBy: { createdAt: "desc" },
})

// Bulk create
await prisma.participant.createMany({
  data: participants.map(p => ({ bookingId: id, ...p })),
})

// Upsert
await prisma.settings.upsert({
  where: { id: "default" },
  update: { ...data },
  create: { id: "default", ...data },
})
```

---

## Common Pitfalls

- Prisma CLI reads `.env`, **not** `.env.local` — create `.env` for CLI
  commands to work at all.
- `channel_binding=require` in Neon connection strings does NOT need
  stripping with current `pg`/`@prisma/adapter-pg` versions — confirmed by
  direct connection test. If a naive regex strip is present anywhere, it
  likely malforms the query string instead (see Step 4) — remove it rather
  than trust it.
- `prisma generate` must run before `next build` — add the `postinstall`
  script (Step 1), or a clean deploy checkout fails.
- Next.js static rendering fails if Prisma queries run at build time — use
  `export const dynamic = "force-dynamic"` (Step 6).
- Prisma 7 needs a driver adapter passed into `PrismaClient` — `generate`
  succeeding does NOT prove queries will work (Step 1/5).
- "Reachable" and "migrated" are separate claims — verify each
  independently, don't assume one implies the other.

---

## Working Rules

- Confirm the app is already Next.js App Router before starting.
- Do not add auth models unless the calling skill (or the user) specifically
  asked for it.
- If PostgreSQL is unavailable, stop with clear instructions instead of
  repeatedly retrying.
- If package installation or migration fails twice, stop and explain the
  blocker rather than trying a third variation blind.
- At the end, tell the user to save before running another skill.

---

## Final Response

Summarize, distinguishing what was *checked* from what was *assumed*:

- Whether `DATABASE_URL` was already present or newly provisioned
- Prisma files created/updated, and whether the driver adapter was required
  and actually installed
- Whether migration ran, was baselined against existing tables, or was
  blocked by unavailability
- Which server routes were added and which old persistence mechanism was
  removed at each call site
- The actual Step 7 end-to-end verification result — not "connection
  works," but "wrote a record via the running app, read it back in a
  separate request, confirmed it directly in Postgres"
- Build verification result, and if it failed, whether it was pre-existing
  and what the root cause/fix was

End by reminding the user to save this VIBER session before running the
next skill.

---

## For AI agents

(See Common Pitfalls above for the driver-adapter and reachable-vs-migrated
gotchas — not repeated here.)

1. Never report "wired up" from schema/migration/client alone — Step 6 and
   Step 7 (rewiring call sites, four-part end-to-end verification) are
   mandatory, not optional polish.
2. On build failure, `git stash` + rebuild before diagnosing which side
   introduced it.
3. If another skill invoked this one because it needs a database, return
   control to that skill once `DATABASE_URL` is confirmed working — don't
   assume this skill's caller also wants schema/seed/query-pattern work
   done unless asked.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
