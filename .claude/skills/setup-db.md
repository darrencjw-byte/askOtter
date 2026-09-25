---
name: "setup-db"
description: "Main-category router for database setup. Use when the user asks to add a database, persist data, save/store data, or replace localStorage/in-memory/mock data with real storage. Confirms which provider to use — Databricks Lakebase (default) or Neon PostgreSQL — then delegates to vibe-lakebasedb or vibe-neondb accordingly. Does not implement anything itself — always delegates."
metadata:
  author: viber-studio
  version: "2.0.0"
  audience: internal
  category: setup
  routes_to: vibe-lakebasedb, vibe-neondb
---

# setup-db — Database setup router

This is the entry point for any database request. It does not implement
database setup itself — it confirms which provider applies, then hands
off entirely to the specific skill that does the actual work. Do not
duplicate `vibe-neondb`'s or `vibe-lakebasedb`'s steps here; if this file
starts accumulating Prisma/schema/migration instructions of its own,
that's a sign the router boundary is being violated.

---

## Step 1 — Determine which provider

**If the request already names a provider, skip straight to the matching
step — don't ask:**
- Mentions Lakebase, Databricks, Postgres generically, or just "add a
  database"/"persist this"/"save this data" with no provider named →
  Step 2A. **Lakebase is the default — every generic request resolves
  here.**
- Mentions Neon specifically → Step 2B.

**If the request names a provider that isn't either of the above** (e.g.
MongoDB, Supabase, PlanetScale, SQLite) — **implement what the user
actually asked for.** This router's job is to provide sensible defaults
for a *generic* request, not to gatekeep which providers exist. Use
general best-practice knowledge for that database rather than forcing the
user toward Lakebase/Neon just because those are the ones with dedicated
skills here. Mention briefly that Lakebase is the default on this platform
if the user seems undecided, but don't block a specific, explicit request.

**Never name the specific provider to the user unless they named one
first, or the conversation has reached a step that requires it (e.g.
which exact button to click).** For a generic request, talk about "a
database" / "persistence" — not "I'll set up Lakebase for you." Neon and
Lakebase are both plain Postgres underneath with an identical
application-level pattern (see `vibe-lakebasedb`'s own note on this) —
which one actually gets provisioned is an implementation detail the user
didn't ask about, not something worth surfacing unprompted.

---

## Step 2A — Lakebase (default): hand off to vibe-lakebasedb

Read `.claude/skills/vibe-lakebasedb/SKILL.md` and follow it from its own
Step 0 onward. That skill owns: checking/provisioning `DATABASE_URL` via
Rabbit Deploy's database-creation button, installing Prisma 7 with the
`@prisma/adapter-pg` driver adapter, configuring `schema.prisma`, running
migrations, wiring the app's actual read/write call sites, and the
four-part end-to-end verification.

**If the user explicitly asked for Lakebase by name**, check first
whether it's actually enabled on this workspace (`vibe-lakebasedb`'s
Step 0 covers this) — if it isn't, tell them plainly and offer Neon
instead rather than silently provisioning the wrong thing under a generic
button label. **If the request was generic** (no provider named), this
check doesn't matter — whichever provider the workspace's database button
actually creates works identically for everything downstream.

---

## Step 2B — Neon: hand off to vibe-neondb

Read `.claude/skills/vibe-neondb/SKILL.md` and follow it from its own
Step 0 onward. **Rabbit Deploy no longer provisions Neon databases** —
that capability was retired in favor of Lakebase, so this path asks the
user for their own connection string instead of guiding them to any
button. Same underlying Postgres/Prisma pattern as Step 2A either way,
just a different provider by explicit request, brought by the user
rather than provisioned here.

---

## Rules

- **Never install Prisma, write `src/lib/prisma.ts`, or touch
  `schema.prisma` from this file** — that's entirely the delegated
  skill's responsibility. If you find yourself about to write Prisma code
  directly from here, stop and go read the actual skill instead.
- **Don't skip straight to a specific skill without this file's Step 1**
  — Step 1 is what keeps the routing decision correct as more providers
  get added.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
