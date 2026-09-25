# CLAUDE.md

## Stack

Next.js 16 · App Router · React 19 · TypeScript 5 · Tailwind CSS 4 · Singapore Government Design System (`@govtechsg/sgds-web-component`) · Better Auth · Prisma 7 (PostgreSQL)

## Component Priority (IMPORTANT)

**SGDS components are the DEFAULT.** Always use `<sgds-*>` web components first. Only fall back to shadcn/ui when SGDS does not have an equivalent.

Before writing any UI markup, consult `.claude/skills/sgds-workflow/SKILL.md` → then the relevant skill (`sgds-components`, `sgds-blocks`, `sgds-templates`).

| Need | Use SGDS | Fallback to shadcn/ui |
|------|----------|----------------------|
| Buttons, badges, alerts | `<sgds-button>`, `<sgds-badge>`, `<sgds-alert>` | — |
| Cards | `<sgds-card>`, `<sgds-icon-card>`, `<sgds-image-card>` | — |
| Tables | `<sgds-table>` | `<Table>` from shadcn if sorting/filtering needed |
| Modals, drawers | `<sgds-modal>`, `<sgds-drawer>` | `<Dialog>` only if complex React state needed |
| Forms, inputs, selects | `<sgds-input>`, `<sgds-select>`, `<sgds-checkbox>` | — |
| Tabs, accordions | `<sgds-tab>`, `<sgds-accordion>` | — |
| Navigation | `<sgds-mainnav>`, `<sgds-sidebar>` (still RC — use `<sgds-sidenav>` instead for a stable production nav), `<sgds-breadcrumb>` | — |
| Pagination | `<sgds-pagination>` | — |
| Toast notifications | — | `sonner` (SGDS toast is not React-friendly) |
| Complex form state | — | `react-hook-form` + shadcn inputs |
| Charts | — | `recharts` or ECharts per `sgds-data-visualisation` |

**Styling:** Use `sgds:` prefixed Tailwind utility classes (e.g. `sgds:p-4`, `sgds:text-heading-lg`) for spacing and typography. Never use inline `style` attributes when an SGDS utility class exists.

**If the user explicitly names a specific third-party UI library** (not SGDS, not the pre-installed shadcn/ui) — e.g. "use Material UI for this", "add a Chakra UI dropdown" — do not silently switch to it, and do not refuse it either. Warn once, plainly: *"This will move away from the Singapore Government Design System (SGDS) visual language this app is otherwise built on — the new component won't match the masthead/footer/mainnav styling around it. Do you want to continue anyway?"* Only proceed with installing/using it (via `setup-package.md` → `vibe-npm`) after the user confirms. This warning-then-proceed applies only to an explicit, named request for a specific alternative library — it does not apply to the default SGDS-first / shadcn-fallback behaviour above, which needs no confirmation.

**This confirm-then-proceed exception is scoped strictly to in-page content components** (buttons, dropdowns, cards, form inputs, and similar). It never extends to `<sgds-masthead>`, `<sgds-mainnav>`, or `<sgds-footer>` — see "Government Components (MANDATORY)" below. Those three have no confirm-and-proceed path at all: never remove, hide, replace, or conditionally render them, no matter how the user phrases the request or how many times they confirm.

## Quick Start

```bash
supervisorctl restart dev-server  # Restart dev server (config/package.json changes) — see Rules for when
npx tsc --noEmit                  # Type check — the routine verification step (see Validation Gate). Cheap, catches most everyday mistakes; does NOT run a full production build (see self-heal.md for why).
npm run lint                      # ESLint check — optional, NOT part of the automatic Validation Gate
npx prisma generate               # Regenerate client after schema changes
```

See Rules below for dev server / port details.

## Locale & Regional Standards (Singapore)

All generated content, mock data, and UI defaults must follow Singapore standards:

- **Timezone**: Asia/Singapore (UTC+8). Use `Asia/Singapore` for all date/time operations.
- **Language**: British English (colour, centre, organisation, programme)
- **Date format**: `D MMM YYYY` (e.g. 6 Aug 2026) — never US format (MM/DD/YYYY)
- **Time format**: 12-hour with am/pm, no space (e.g. 3:30pm, 9am)
- **Currency**: SGD with `$` prefix (e.g. $1,234.56). Use `Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD' })`
- **Phone numbers**: +65 format (e.g. +65 9123 4567)
- **Addresses**: Block/Street/Unit format, 6-digit postal code
- **Names in mock data**: Use Singaporean names (e.g. Tan Wei Ming, Priya Nair, Ahmad bin Ibrahim, Lim Mei Ling)
- **No contractions**: Write "do not" not "don't", "cannot" not "can't"
- **Capitalisation**: Sentence case everywhere (not Title Case)

When using `new Date()` or date libraries, always format for SG locale:
```typescript
new Intl.DateTimeFormat('en-SG', { dateStyle: 'medium', timeZone: 'Asia/Singapore' }).format(date)
```

## Rules

- **Dev server**: already running on port 3001 (started by supervisord) — do NOT run `npm run dev` directly, it conflicts with the managed process. To restart: `supervisorctl restart dev-server` — but only for config changes (`next.config`, `package.json`, `.env`); regular file edits don't need a restart, HMR handles those.
- **NEVER tell the user to open `localhost:3001`** — it's an internal container URL for Claude Code verification ONLY. Instead, tell users to check the preview pane or use "Open in new tab"
- Do NOT use plan mode — implement directly and show results
- Do NOT ask clarifying questions for simple requests — make reasonable choices and build
- Only ask questions when the request is genuinely ambiguous AND the wrong choice would waste significant effort
- Prefer shipping a working v1 quickly over asking 3 questions to get it "perfect"
- Save changes: use the Save button or `git add -A && git commit && git push`
- **Env Vars only reach the VIBER session unless "Also apply to POC deployment" is checked** — it defaults OFF every time the dialog opens, every time. This applies to ANY env var, regardless of what feature it's for — not just auth/DB/email. Whenever telling a user to add one that the deployed product itself needs to actually work (not just the VIBER preview), remind them to check it before saving. **This checkbox is hidden entirely if the project has never been deployed to POC** — if so, tell the user to deploy to POC first, then come back to Env Vars.

## Efficiency (reduce tool call noise)

Every tool call shows in the chat as a loading line. Minimize unnecessary calls:

- **BEFORE importing any shadcn component**: follow `setup-package.md` → `vibe-shadcn`. Check SGDS has no equivalent first. Pre-installed: button, card, input, label, sonner. Everything else (badge, table, dialog, tabs, skeleton, select, dropdown-menu, etc.) MUST be installed via `npx shadcn@latest add <name> --yes` first or the build will crash with "Module not found".
- **Batch related checks into one command** — not `tail` then `grep` then `tail` again. Use: `tail -30 /var/log/devserver.err | grep -E "Error:|SyntaxError"`
- **Do not read files you just wrote** — you already know the content
- **Do not run `ls` before creating a file** — just write it directly
- **Do not curl localhost after every change** — check `tail -5 /var/log/devserver.err` once instead
- **Do not restart the dev server for plain file edits** — see Rules above for when a restart is actually needed
- **One verify step after edits, not three** — single `tail -5 /var/log/devserver.err`. If clean, move on.
- **Skip `supervisorctl status`** unless you just restarted something
- **Do not `rm` then recreate a file** — just overwrite it with Write
- **Do not npm install packages one by one** — batch them: `npm install pkg1 pkg2 pkg3`

**Target: 5-8 tool calls per user prompt, not 15-20.**

## First Prompt Experience (CRITICAL)

The user's first prompt is the most important moment. The output must look **polished and complete**, not like a wireframe. Follow these rules for the FIRST build:

**Speed:**
- Do NOT narrate your process ("Let me check SGDS...", "Reading references...", "Let me first look at..."). Just build.
- ONE message to the user max before showing results: a short line like "Building your invoice dashboard..." then start coding.
- Never read multiple skill files in sequence before writing code — read what you need inline as you build. Exception: `sgds-workflow/SKILL.md` and `design-system.md` (see Design & Visual Standards below) are the one required upfront pair for any UI work — that read is fast. This rule is guarding against a slow upfront tour through per-component reference docs (button.md, select.md, etc.) — check those inline as you build each piece, not before starting.

**Visual quality on first render:**
- Every stat card MUST have: a Lucide icon (top-right), a large number with `tabular-nums`, a trend indicator with colour (green=up, red=down)
- Status badges MUST be clearly coloured: green for paid/complete, amber for pending, red for overdue
- Tables MUST have: alternating row hover states, proper column alignment (numbers right-aligned), at least 6-8 rows of realistic mock data
- Page header MUST have: clear title + subtitle + primary action button (right-aligned)
- Cards MUST have visible borders or subtle shadows — never float flat on white
- The overall page must look like a finished product on first load, not a prototype

**Content quality:**
- Mock data must be realistic and contextual (real invoice numbers like INV-2026-001234, real vendor names like "Acme Supplies Pte Ltd")
- Numbers must use proper SGD formatting ($8,450.00) with `tabular-nums`
- Dates in Singapore format (15 Jul 2026)
- At least 6-8 table rows so the page looks full, not empty

**Layout quality:**
- All content must sit within `max-w-7xl mx-auto` container — never clip left/right edges
- Proper padding on all sides (`px-6 sm:px-8 lg:px-12`)
- Stat cards in responsive grid that does not overflow on mobile
- Search/filter bar visually distinct from the table (proper spacing between them)

### Avoiding Build Errors in Preview

The preview pane auto-refreshes on every file save. To prevent users seeing transient build errors:

- **Write complete files** — never leave a half-written component. Finish the entire file before moving to the next.
- **Create dependencies first** — if a page imports a new component, create the component file BEFORE editing the page.
- **Add imports and exports together** — never save a file with an import that points to a not-yet-created file.
- **If adding multiple related files** (e.g., a new page + its components + an API route), create them in dependency order: utilities → components → page.
- The template includes `global-error.tsx` and `error.tsx` which show a graceful "Building..." spinner instead of a red error screen. Do NOT remove these files.

## Understanding User Intent

When the user's request is ambiguous or short, apply these defaults — expand it into a complete implementation, don't ask "what columns do you want?":

| User says | Build this |
|-----------|-------------|
| "create a dashboard" | Stats cards + data table on the homepage, mock data, no DB |
| "add a form" / "add a contact form" | Full form with validation (e.g. contact form: Name, Email, Subject, Message), loading state on submit, success toast, clear-on-submit or redirect |
| "make it look better" | Improve spacing, add shadows/borders, better typography hierarchy |
| "add authentication" / "add login" / "login" / "add SSO" / "sign in" / "need users to log in" / "protect this page" | **Read `.claude/skills/setup-auth.md` first** — the category router. It decides GovAuth (POC only) vs direct TechPass vs direct WOG AD vs direct Entra ID and delegates to `vibe-govauth`/`vibe-techpass`/`vibe-wogad`/`vibe-entraid` accordingly; do not skip straight to any of them yourself. |
| "connect to database" / "add database" / "save data" / "persist" | **Read `.claude/skills/setup-db.md` first** — the category router. It delegates to `vibe-neondb` or `vibe-lakebasedb`; do not skip straight to either yourself. |
| "send email" / "add email" / "email notification" / "OTP email" / "send receipt" | **Read `.claude/skills/setup-email.md` first** — the category router. It decides Postman vs AWS SES vs Resend vs SMTP and delegates accordingly; do not skip straight to any provider yourself. |
| "deploy this" | Run `SELF_HEAL_BUILD_CHECK=1 npm run build` to confirm it passes (this already runs type checking), then tell user to Save |
| "fix this" / "it's broken" | Check terminal for errors first, then check the browser, fix root cause |
| "add a chart" | Use recharts (install if needed), responsive container, proper axis labels |
| "make it responsive" | Ensure all layouts stack on mobile, test at 375px width |
| "add dark mode" | For shadcn-only elements: `next-themes` + CSS variables, toggle in header, respect system preference. **This alone does not theme `<sgds-masthead>`/`<sgds-mainnav>`/`<sgds-footer>`** — see `sgds-theming/SKILL.md`'s night mode (`.sgds-night-theme` class + `themes/night.css`), which must be added too, or the mandatory shell stays in day mode while shadcn areas go dark. |
| "add a table" / "add a user table" | Sortable columns (e.g. user table: Name, Email, Role, Status, Actions), search filter, pagination, empty state, loading skeleton |
| "add notifications" | Toast system with sonner, success/error/info variants |
| "add a sidebar" | Collapsible nav with icons, active state highlight, responsive (drawer on mobile) |
| "create a settings page" | Tabbed layout (General, Notifications, Security), form with save button, success feedback |
| "build a to-do app" | Add/edit/delete/complete tasks, filter by status, persist in local state, clean empty state |
| "create a landing page" | Hero section, feature highlights (3-card grid), CTA button, responsive |
| "build a file upload" | Drag-and-drop zone, file type validation, progress indicator, file list with remove |

Always build the FULL feature in one pass — make sensible defaults and let the user refine. Ship a working v1, not a skeleton.


## Design & Visual Standards

For all UI work, follow this order:
1. **`.claude/skills/sgds-workflow/SKILL.md`** — always first; maps which SGDS skill covers the current task (components, blocks, templates, forms, layouts, writing)
2. **`.claude/skills/design-system.md`** — read alongside for visual standards: mandatory page shell, style selection by context, gov/enterprise vocabulary, iterative feedback, accessibility

## Proactive Behavior

After completing the user's request, automatically:
1. Add loading/empty states if the page fetches data and doesn't have them
2. Ensure all buttons have hover states and `cursor-pointer`
3. Verify the layout doesn't break at mobile widths (use responsive classes)
4. Add toast notifications for create/update/delete actions if not present
5. Fix any errors before responding — see Validation Gate below

Do NOT proactively:
- Add features the user didn't ask for (no "I also added X")
- Refactor existing working code
- Change the styling approach unless asked
- Add authentication to pages unless requested
- Add database code unless persistence is explicitly needed

## Context Awareness

- Before modifying a page, READ the existing code first to understand what's already built
- When the user says "add X to the page" — add it to the CURRENT page they're viewing, not a new page
- If the project already has a color scheme/theme, match it — don't introduce conflicting colors
- When adding features to existing UI, maintain the existing layout structure and spacing patterns
- Check if similar components already exist before creating new ones (avoid duplication)
- If the user references something on screen ("that button", "the table above"), infer from the current page context

## Error Recovery

- If `npm run dev` crashes: read the error, fix the root cause, restart with `supervisorctl restart dev-server`
- If a package install fails: try an alternative (e.g., `chart.js` → use `recharts` instead)
- If the user says "it doesn't look right": check for missing CSS classes, layout issues, or wrong component usage — fix the most likely visual problem
- If TypeScript errors after a change: fix ALL errors in one pass, don't fix one at a time
- If the build fails: check for missing imports, type mismatches, and server/client boundary issues first
- If a component renders blank: check for missing "use client" directive, undefined data, or conditional rendering bugs
- Never leave the project in a broken state — if a change breaks something, revert or fix before responding

## How to Respond

- After making changes: briefly state what you built (1-2 sentences), don't list every file changed
- When encountering an error: state the error, state the fix, apply it — don't explain the theory
- Never paste the full contents of a file back to the user — they can see it in the editor
- If a task takes multiple steps, show progress ("Adding the table component... now connecting the data... done")
- End with what the user should see in the preview pane ("You should now see a dashboard with 3 stat cards and a data table")

## Data & Database

**Default: NO database.** Build features with client-side state, hardcoded data, or mock data unless the user explicitly signals they need persistence.

Trigger phrases that mean "use the database":
- "save/store data", "persistent", "database", "connect to DB"
- "share with team/colleagues/users"
- "multiple users need to see the same data"
- "remember between sessions"

If the user says "create a dashboard" / "build a page" / "add a feature" without mentioning persistence → use local state, static/mock data, or fetch from an API. Do NOT create `src/lib/prisma.ts` or add models to `schema.prisma`.

**Prisma is available when needed** — see the Database section below for setup instructions.

When you DO create database code, install the driver adapter first —
`npm install @prisma/adapter-pg pg` — then use this exact pattern for
`src/lib/prisma.ts`. Prisma 7 requires a driver adapter — `new PrismaClient()`
with no adapter throws `PrismaClientInitializationError` immediately
(confirmed by direct test), not just at generate time:
```typescript
import { PrismaClient } from "@/generated/prisma/client"
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

### Prisma Generate Rule (CRITICAL)

If you edit `prisma/schema.prisma` OR create `src/lib/prisma.ts`, you **MUST** run immediately:
```bash
npx prisma generate
```
Without this, `@/generated/prisma/client` won't resolve and the build will break. The generated client is `.gitignored` — it must be regenerated in every fresh environment.

**Prisma 7 import path** — always use `/client` suffix:
```typescript
import { PrismaClient } from "@/generated/prisma/client"
```
Do NOT use `@/generated/prisma` (no index.ts exists in Prisma 7's custom output).

## Structure

```
src/
  app/              # Pages, layouts, API routes (route.ts)
    globals.css     # Tailwind 4 CSS (theme variables defined here)
    sgds.css        # SGDS theme/foundation/utility imports — dedicated file, NEVER merge into globals.css (breaks all unprefixed Tailwind utilities)
    layout.tsx      # Root layout — SgdsProvider + <sgds-masthead fluid> + <sgds-footer> (COMPLIANCE)
    page.tsx        # Home page
    privacy/        # Privacy policy page
    terms/          # Terms of use page
  components/
    sgds-provider.tsx # Bootstraps SGDS web components on mount — DO NOT remove
    ui/             # shadcn/ui primitives — DO NOT edit manually
  lib/
    utils.ts        # cn() helper for Tailwind class merging
  generated/
    prisma/         # Auto-generated Prisma client (do not edit)
prisma/
  schema.prisma     # Database schema
public/             # Static assets
```

## Path Alias

`@/*` maps to `./src/*` — use `@/components/...`, `@/lib/...`, etc.

## Pre-installed shadcn/ui Components

button, card, input, label, sonner (toast)

To add more shadcn components:
```bash
npx shadcn@latest add <component-name>
```

Commonly needed additions (install on demand):
- `table` — for data tables
- `dialog` — for modals and confirmation prompts
- `tabs` — for tabbed interfaces
- `badge` — for status indicators
- `skeleton` — for loading states
- `alert-dialog` — for destructive action confirmations
- `dropdown-menu` — for action menus
- `select` — for dropdown selects
- `textarea` — for multi-line inputs
- `separator` — for visual dividers

## Database (Prisma 7 — Available When Needed)

Prisma is pre-configured but should only be used when the user requests data persistence. Schema at `prisma/schema.prisma`. Client output goes to `src/generated/prisma`.

**For database setup, follow `.claude/skills/setup-db.md`** — the category router, which delegates to `vibe-lakebasedb` (Databricks Lakebase, the default — the only provider Rabbit Deploy still provisions through its own UI) or `vibe-neondb` (Neon, bring-your-own connection string only) for the actual DB creation, env var configuration, and Prisma wiring. Do not skip straight to either specific skill.

### Prisma Schema

`prisma/schema.prisma` contains Better Auth models (User, Session, Account, Verification). These are **required for authentication — do not remove or rename them**.

When adding database features:
- Add new models BELOW the existing auth models
- Run `npx prisma generate` after schema changes
- Add `export const dynamic = 'force-dynamic'` to any page/route that queries the database

Do NOT run `prisma migrate` or `prisma db push` ad-hoc — migrations must go through the gated flow in the relevant database skill (`vibe-neondb` or `vibe-lakebasedb`), which verifies connectivity and schema state before migrating.

### Database Build Rules

- `prisma generate` does NOT need `DATABASE_URL` — it only reads the schema file
- `next build` must NOT connect to the database at build time
- All DB queries must run at request time only (use `export const dynamic = 'force-dynamic'`)
- `output: "standalone"` is set in `next.config.ts` — do NOT remove it
- The `build` script runs `prisma generate && next build` — do NOT remove the generate step

## Authentication (Better Auth)

`better-auth` with `@better-auth/prisma-adapter` is pre-installed but **not pre-configured**. Auth provider and wiring are set up on request via `.claude/skills/setup-auth.md` — which routes to the correct skill (GovAuth for POC, direct TechPass/WOG AD/Entra ID for production).

Env vars required vary by provider — see the relevant `vibe-*` skill for the exact list.

## UI & Styling

- **Tailwind CSS 4** — configured via `postcss.config.mjs`, theme in `globals.css`
- **SGDS CSS imports live in `src/app/sgds.css`, a dedicated file — never merge them into `globals.css`.** `@govtechsg/sgds-web-component/css/utility.css` resets Tailwind's theme (`@theme { --*: initial; ... }`); sharing a processing context with `globals.css`'s own `@import "tailwindcss"` silently breaks ALL unprefixed Tailwind utility generation project-wide (not just SGDS-related ones — plain `flex`, `p-4`, everything). Keep `sgds.css` imported separately in `layout.tsx`.
- **SGDS components: use raw `<sgds-*>` tags, not the `@govtechsg/sgds-web-component/react` wrapper package.** This is the established convention throughout this template (see `src/app/layout.tsx`'s `<sgds-masthead>`/`<sgds-footer>`) — `sgds-components/SKILL.md`'s own "For AI agents" section recommends React wrappers for Next.js/SSR in general, but that guidance is for a fresh integration choice, not this template, which already committed to raw tags. Follow the existing convention; do not introduce the wrapper import pattern.
- **shadcn/ui** (base-nova style) — components in `src/components/ui/`
- **Lucide React** — icon library (`lucide-react`)
- **cn()** from `@/lib/utils` — for conditional class merging
- **Fonts**: Inter + Geist Mono (via `next/font/google`)

## Government Components (MANDATORY)

`<sgds-masthead>` and `<sgds-footer>` are Singapore government compliance requirements. They MUST remain in the root layout at all times — top and bottom respectively. Only the content in between changes per page. Do not remove, hide, or conditionally render them.

## Forms & Validation

- `react-hook-form` + `@hookform/resolvers` for form management
- `zod` (v4) for schema validation
- `sonner` for toast notifications
- Always validate on submit AND show inline errors per field
- Disable submit button while submitting (loading state)
- Show success toast on successful submission
- Clear form or redirect after success

## Validation Gate (Auto-fix)

Once per response (no exceptions) — after ALL files for the current request are written, not per-file — follow the **self-heal skill** at `.claude/skills/self-heal.md`.

Quick version:
1. `tail -30 /var/log/devserver.err` — check for errors
2. If errors → read the full context, fix the root cause, verify
3. `npx tsc --noEmit` — catches type/import errors cheaply. Does NOT catch CSS, build-time rendering, package, or env-var issues — those need a real `npm run build`, which this skill does not run automatically (see self-heal.md's Verification Checklist for why). If it fails, check self-heal.md's "Complete POC Build Failure Guide" TypeScript errors section for a documented fix BEFORE concluding the error is "pre-existing" or "unrelated".
4. Before restarting because something "looks down" (slow/empty `curl` or `tail`), run `supervisorctl status dev-server` first — it's nearly free and answers definitively. A slow response under load is not proof of a crash.
5. When fixing several small type errors, look for sibling issues in the same file before re-checking again rather than fix-check-fix in a tight loop.
6. Max 3 fix attempts. If still broken, tell the user.

**NEVER report "done" or "ready to deploy" to the user if the type check is broken, or based on the type check alone when deploy-readiness genuinely matters — see self-heal.md's Rules.** Always self-heal first.

## Skills (`.claude/skills/`)

Reusable procedures the AI follows for common tasks:

| Skill | File | Purpose |
|-------|------|---------|
| **Self-Heal** | `.claude/skills/self-heal.md` | Detect + fix build errors from `/var/log/devserver.err` after every change |
| **SGDS Workflow** | `.claude/skills/sgds-workflow/SKILL.md` | ALWAYS read first for UI work — maps all SGDS skills and reading order |
| **SGDS Getting Started** | `.claude/skills/sgds-getting-started/SKILL.md` | Mandatory first step for a new SGDS project — font, foundation CSS, utilities, components, layout order |
| **SGDS Components** | `.claude/skills/sgds-components/SKILL.md` | All 47 `<sgds-*>` web components — check before writing custom HTML |
| **SGDS Utilities** | `.claude/skills/sgds-utilities/SKILL.md` | All `sgds:` Tailwind utility classes for spacing, typography, colours |
| **SGDS Blocks** | `.claude/skills/sgds-blocks/SKILL.md` | Reusable page sections: hero, stats, cards, CTA, filters, forms |
| **SGDS Templates** | `.claude/skills/sgds-templates/SKILL.md` | Full page layouts: dashboard, login, form, list, settings |
| **SGDS Layouts** | `.claude/skills/sgds-layouts/SKILL.md` | Page arrangement: full-width vs sidebar, aside panels |
| **SGDS Forms** | `.claude/skills/sgds-forms/SKILL.md` | Form validation, constraint API, FormData handling |
| **SGDS Patterns** | `.claude/skills/sgds-patterns/SKILL.md` | Typography hierarchy, content standards |
| **SGDS Theming** | `.claude/skills/sgds-theming/SKILL.md` | Brand colours, dark mode, font customisation |
| **SGDS Data Viz** | `.claude/skills/sgds-data-visualisation/SKILL.md` | Charts with ECharts + SGDS colour palette |
| **SGDS Writing** | `.claude/skills/sgds-writing/SKILL.md` | UK English, sentence case, no contractions, gov UI copy |
| **Design System** | `.claude/skills/design-system.md` | Visual standards — mandatory masthead/footer shell, SGDS-first component selection, accessibility |
| **Frontend Design** | `.claude/skills/frontend-design/SKILL.md` | Reached via design-system.md (Component Priority note and Interior Design Principles) — grounds palette/typography/layout choices in the app's actual subject: sgds-theming's colour/font/night-mode choice, sgds-blocks composition, and anything outside SGDS's territory (shadcn, an approved third-party library, or custom code); never overrides an `<sgds-*>` component's own internal styling |
| **Auth Setup (setup-auth)** | `.claude/skills/setup-auth.md` | Category router — decides GovAuth (POC only) vs direct TechPass vs direct WOG AD vs direct Entra ID, always delegates, never implements |
| **GovAuth Setup (vibe-govauth)** | `.claude/skills/vibe-govauth/SKILL.md` | Reached via `setup-auth` — GovAuth OAuth 2.0, sandbox/POC only, never production (WOG AD or TechPass proxied), guides portal registration + wires up Better Auth, always stateless |
| **Direct TechPass (vibe-techpass)** | `.claude/skills/vibe-techpass/SKILL.md` | Reached via `setup-auth` — production-capable TechPass SSO without GovAuth's proxy, Auth.js v5/NextAuth, stateless by default |
| **Direct WOG AD (vibe-wogad)** | `.claude/skills/vibe-wogad/SKILL.md` | Reached via `setup-auth` — production-capable WOG AD SSO without GovAuth's proxy, Auth.js v5/NextAuth, stateless by default |
| **Direct Entra ID (vibe-entraid)** | `.claude/skills/vibe-entraid/SKILL.md` | Reached via `setup-auth` — an organisation's own SEPARATE Microsoft Entra ID app registration (not WOG AD, not TechPass), Better Auth, always needs a database |
| **Database Setup (setup-db)** | `.claude/skills/setup-db.md` | Category router — decides Lakebase (default) vs Neon, always delegates, never implements |
| **Lakebase Database (vibe-lakebasedb)** | `.claude/skills/vibe-lakebasedb/SKILL.md` | Reached via `setup-db` — Prisma 7 + Databricks Lakebase (genuine Postgres underneath), provisioned via Rabbit Deploy's own UI |
| **Add Database (vibe-neondb)** | `.claude/skills/vibe-neondb/SKILL.md` | Reached via `setup-db` — Prisma 7 + Neon PostgreSQL, driver-adapter, migration, verification — bring your own connection string, Rabbit Deploy no longer provisions Neon |
| **Email Setup (setup-email)** | `.claude/skills/setup-email.md` | Category router — decides Postman vs AWS SES vs Resend vs SMTP, always delegates, never implements |
| **Postman Email (vibe-postman)** | `.claude/skills/vibe-postman/SKILL.md` | Reached via `setup-email` — Postman transactional email API (gov standard), API key setup + send/status endpoints |
| **AWS SES Email (vibe-awsses)** | `.claude/skills/vibe-awsses/SKILL.md` | Reached via `setup-email` — AWS SES transactional email, explicit-request only |
| **Resend Email (vibe-resend)** | `.claude/skills/vibe-resend/SKILL.md` | Reached via `setup-email` — Resend transactional email, explicit-request only |
| **SMTP Email (vibe-smtp)** | `.claude/skills/vibe-smtp/SKILL.md` | Reached via `setup-email` — custom SMTP server/relay via nodemailer, explicit-request only |
| **Package Setup (setup-package)** | `.claude/skills/setup-package.md` | Category router — decides shadcn component vs npm package, always delegates, never implements |
| **Add shadcn Component (vibe-shadcn)** | `.claude/skills/vibe-shadcn/SKILL.md` | Reached via `setup-package` — SGDS gate first, then `npx shadcn@latest add`, verify, build check |
| **Add npm Package (vibe-npm)** | `.claude/skills/vibe-npm/SKILL.md` | Reached via `setup-package` — `npm install`, verify, build check |

These skills evolve over time. When adding new capabilities, create a new `.md` file in `.claude/skills/` and reference it here.

## Key Conventions

- Server Components by default; add `"use client"` only when needed
- API routes go in `src/app/api/.../route.ts`
- Validate all API inputs with Zod
- Use `@/` imports, never relative paths crossing directories
- Functional components only
- Keep strict TypeScript — no `any`

## Homepage (`src/app/page.tsx`)

The homepage is a **placeholder meant to be replaced**. When the user asks to build app content (dashboards, landing pages, forms, etc.):
- **Replace the homepage content directly** — do NOT create a separate page and link to it from home
- The homepage should become the app's main entry point with the user's requested content
- Only create sub-pages (`src/app/<route>/page.tsx`) for genuinely separate sections (e.g., settings, detail views)

## Adding New Pages

Create `src/app/<route>/page.tsx`. It automatically inherits the root layout with masthead and footer.

## Adding API Routes

Create `src/app/api/<path>/route.ts`:
```typescript
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ data: "value" });
}
```
