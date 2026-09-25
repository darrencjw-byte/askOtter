---
name: "vibe-lakebasedb"
description: "Add Prisma 7 + Databricks Lakebase PostgreSQL to an existing Next.js App Router app, provisioned through Rabbit Deploy's database-creation button (labeled 'Create Lakebase DB' only when Neon is also enabled on the workspace, otherwise a generic 'Create Database'). Use when the user specifically names Lakebase or Databricks, OR when directed here by setup-db's routing — this is the default provider for a generic 'add a database'/'persist data' request that doesn't name one."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# vibe-lakebasedb

Add Prisma 7 + PostgreSQL (Databricks Lakebase) readiness to an existing
Next.js App Router app. Lakebase is genuine Postgres under the hood
(confirmed: its control-plane API returns `compute_provisioner:
"k8s-neonvm"` — it's Neon's engine behind a Databricks-branded API
surface), so the application-level pattern here is nearly identical to
`vibe-neondb`'s. Do not convert the framework, initialize shadcn/ui, or
add authentication in this skill — those are separate stages.

**What's actually verified vs assumed:** confirmed directly in
`betarabbitdeploy`'s own code (`components/projects/DatabasePanel.tsx`)
that the database-creation button shows a plain, generic **Create
Database** label when only one provider is enabled on the workspace.
Rabbit Deploy is retiring Neon provisioning in favor of Lakebase, so
going forward this button should just say **Create Database** and always
create a Lakebase database — the older two-separate-buttons behavior
(when both Neon and Lakebase were enabled on the same workspace) is a
historical artifact of the dual-provider period, not something to design
around anymore. It hands the app a plain `connectionUri`, not
`DATABRICKS_HOST`/`DATABRICKS_TOKEN` directly. Also confirmed: Lakebase's
connection string does **not** have a Neon-`channel_binding`-style
quirk — tested directly, see Step 4.

---

## Step 0 — Ensure user has a database

```bash
echo "DATABASE_URL=${DATABASE_URL:+SET}"
```

**If NOT set**, guide the user — do NOT tell them to go to Databricks
directly or create an external workspace account:

> "To add a database, use the **Create Database** button in your project's
> config page:
>
> 1. Go to your project page in **Rabbit Deploy** (not Databricks
>    directly)
> 2. Scroll to **Additional Resources → Database**
> 3. Click **Create Database** — if your workspace has both Neon and
>    Lakebase enabled, you'll see two separately-labeled buttons instead;
>    click **Create Lakebase DB**
> 4. Leave **"Add schema access to my VIBER session"** checked (it's on
>    by default) — this automatically sets `DATABASE_URL` in your live
>    session, no copying/pasting into Env Vars needed
>
> Come back and tell me once it's created — I'll check `DATABASE_URL`
> directly rather than asking you to paste anything."

**Confirmed directly in this platform's own code**
(`app/api/projects/[id]/lakebase-database/route.ts` +
`lib/services/viber-session-env.service.ts`): with that checkbox left
checked, creation auto-injects `DATABASE_URL` straight into the running
VIBER session via the same live-edit path the Env Vars dialog itself
uses — a dev server restart (`supervisorctl restart dev-server`) is
still needed for the running process to pick up the new value, but no
manual copy/paste step exists in this path at all.

**Fallback — only if `DATABASE_URL` still isn't set after the button
click** (e.g. the checkbox was unchecked, or there's no live VIBER
session yet for this product so the checkbox never appeared): guide the
user to copy the connection string shown and add it manually via
**Advanced → Env Vars** instead.

**If database creation isn't available at all on this workspace**
(no button shown), tell the user plainly rather than guessing — Rabbit
Deploy no longer provisions Neon as an alternative here, so there's no
fallback provider to offer through the platform's own UI. `vibe-neondb`
still exists, but only for a user who brings their own external Neon
connection string, not as something this workspace's button can create.

**Stop here.** Do not proceed with Prisma setup until `DATABASE_URL` is
confirmed available.

**If already SET**, skip provisioning — verify connectivity (Step 4) and
proceed to whatever schema/wiring work was actually requested.

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

Same requirement as `vibe-neondb` — Prisma 7's client is driver-adapter
based:

```bash
npm install prisma@^7.0.0 --save-dev
npm install @prisma/client@^7.0.0 @prisma/adapter-pg@^7.0.0 pg
npx prisma init --datasource-provider postgresql
```

If Prisma is already installed, repair the existing setup instead of
duplicating config files.

Add the `postinstall` script if not already present (see `vibe-neondb`'s
Step 1 for why this matters for clean deploy checkouts):

```json
"scripts": {
  "postinstall": "prisma generate"
}
```

`prisma.config.ts` (already present in this template) does
`import "dotenv/config"` unconditionally. If `dotenv` isn't already
resolvable (`npm ls dotenv`), install it explicitly
(`npm install dotenv --save-dev`) — otherwise every `prisma generate`/
`prisma migrate` command, and the `postinstall` script itself, fails with
`Cannot find module 'dotenv/config'`. This is a template-level Prisma
config detail, not Lakebase-specific — same fix as `vibe-neondb`.

---

## Step 2 — Configure environment

If `DATABASE_URL` was added via Env Vars, it's already injected — only a
dev server restart is needed:

```bash
supervisorctl restart dev-server
```

Add or update `.env.example`:
```bash
DATABASE_URL=""
```

Ensure `.env` is in `.gitignore`.

---

## Step 3 — Configure the Prisma schema

**Read the existing `prisma/schema.prisma` first — do not blindly
overwrite it.** Same as `vibe-neondb`: this template ships with a real,
working `prisma/schema.prisma` already at the project root, using Prisma
7's native `prisma-client` generator (NOT `prisma-client-js` —
`previewFeatures = ["driverAdapters"]` is specific to the older generator
and not needed here) with `output = "../src/generated/prisma"`, and it
already defines Better Auth's `User`/`Session`/`Account`/`Verification`
models:

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

datasource db {
  provider = "postgresql"
}
```

- **Do not change the generator block** or add back `previewFeatures` —
  that would downgrade a working Prisma 7 native config for no reason.
- **Do not remove the existing Better Auth models** — they're already
  there by default, not something this skill adds. If a caller (e.g.
  `vibe-entraid`) asks for these models "to be added," check first —
  they likely already exist.
- Add only new models below the existing ones.
- The `datasource db` block intentionally has no
  `url = env("DATABASE_URL")` line — the connection string comes from
  `prisma.config.ts`'s `datasource.url` instead. Don't add that line back.

---

## Step 4 — Verify database readiness

```bash
npx prisma generate
```

If reachable:
```bash
npx prisma migrate dev --name init
```

Quick standalone connectivity check (adjust import path to this project's
actual generated client location):

```bash
npx tsx -e "
const { PrismaClient } = require('./src/generated/prisma/client');
const { PrismaPg } = require('@prisma/adapter-pg');
const p = new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }) });
p.\$connect().then(() => { console.log('OK - connected'); p.\$disconnect(); }).catch(e => console.error('FAIL:', e.message));
"
```

**Lakebase-specific:** confirmed directly (same test as `vibe-neondb`'s
Step 4) that Lakebase's connection string does not carry a
Neon-`channel_binding`-style quirk — no defensive stripping needed here
either. If a connection is rejected as insecure after the string was
touched by any code, that's the same class of bug `vibe-neondb`'s Step 4
documents for Neon (a naive regex strip malforming the query string) —
check for that before assuming Lakebase has its own separate issue.

---

## Step 5 — Prisma Client Singleton

Identical pattern to `vibe-neondb`'s Step 5 — the adapter is mandatory,
not optional:

```typescript
// src/lib/prisma.ts
import { PrismaClient } from "@/generated/prisma/client" // match this project's actual output path
import { PrismaPg } from "@prisma/adapter-pg"

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
  })

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma
```

A bare `new PrismaClient()` with no adapter throws
`PrismaClientInitializationError` immediately on construction — confirmed
for both Neon and Lakebase; the underlying engine and driver-adapter
requirement are identical.

---

## Step 6 — Wire the app to the database

Same as `vibe-neondb`'s Step 6 — schema + migration + a working
`PrismaClient` are necessary but NOT sufficient. Create the actual
read/write call sites, find and replace every place the app currently
persists data another way (`grep -rn "localStorage" src/` after editing
to confirm nothing was left behind), and add
`export const dynamic = "force-dynamic"` to any page/route querying the
database.

**If a mock/in-memory array already feeds live client-side
filtering/sorting/search**, default to preserving that — fetch the full
dataset once and keep filtering client-side, don't silently switch to
re-querying the database on every filter change. See `vibe-neondb`'s
Step 6 for the full reasoning; only go server-side on filtering when
dataset size genuinely requires it, and say so explicitly.

---

## Step 7 — Verify end-to-end

Same four-part standard as `vibe-neondb`'s Step 7 — do not accept a
single success as proof:

1. `curl` the API route to create a record.
2. `curl` it again in a separate request to confirm it persisted.
3. Query the database directly to confirm the row is physically present.
4. Load the page and confirm rendered data matches; grep for the old
   storage mechanism to confirm it's gone.

---

## Step 8 — Verify the app still builds

```bash
SELF_HEAL_BUILD_CHECK=1 npm run build
```

If it fails, isolate with `git stash` + rebuild before treating it as a
blocker — see `vibe-neondb`'s Step 8 for the full build-environment
diagnosis pattern (stray `NODE_ENV` corrupting static prerendering is not
Lakebase-specific, it's a general Next.js build-environment issue).

---

## Seed data / query patterns / final response

This file doesn't duplicate `vibe-neondb`'s "Seed data", "Common query
patterns", and "Final Response" sections — those are Prisma-ORM-level
patterns (not Neon-specific connection-string quirks), so they apply here
unchanged. See `vibe-neondb`'s corresponding sections directly.

---

## Rules

- **Confirm the app is already Next.js App Router** before starting.
- **Do not add auth models** unless the calling context specifically
  asked for it.
- **If database creation isn't available at all on this workspace**, say
  so plainly rather than guessing — there's no in-platform fallback
  provider to offer anymore (Neon is bring-your-own-string only, see
  `vibe-neondb`).
- At the end, tell the user to save before running another skill.

---

## For AI agents

(See Common Pitfalls-equivalent notes above for the driver-adapter and
reachable-vs-migrated gotchas — not repeated here.)

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
