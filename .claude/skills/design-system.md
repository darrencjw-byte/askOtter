---
name: "design-system"
description: "Visual standards and design guidelines for building UI in this template — mandatory SGDS page shell (masthead/footer), component selection (SGDS-first, shadcn fallback), government/enterprise vocabulary, accessibility, and iterative feedback. Read this alongside sgds-workflow/SKILL.md when building any UI."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: design
---

# Skill: Design System & Visual Standards

Read this skill when building any UI — pages, dashboards, forms, landing pages. SGDS components are the default; Vercel/Stripe/Supabase visual language applies to shadcn fallback elements only.

---

## Mandatory Page Shell (COMPLIANCE)

**Every page must have `<sgds-masthead>` at the top and `<sgds-footer>` at the bottom. These are Singapore government compliance requirements — never remove, hide, or conditionally render them.**

All pages inherit this shell from the root layout automatically:

```tsx
// src/app/layout.tsx (already wired — do not change the shell)
<body>
  <SgdsProvider>                        {/* bootstraps SGDS web components — must stay */}
    <sgds-masthead fluid></sgds-masthead>

    {/* ↑ COMPLIANCE — always present, always visible */}

    <main>{children}</main>

    {/* ↓ COMPLIANCE — always present, always visible */}

    <sgds-footer
      contactHref="#"
      feedbackHref="#"
      privacyHref="/privacy"
      termsOfUseHref="/terms"
    ></sgds-footer>
    <Toaster richColors position="top-right" /> {/* global sonner toast — already wired, do not remove */}
  </SgdsProvider>
</body>
```

- **`SgdsProvider`** — client component at `@/components/sgds-provider` that dynamically imports the SGDS web component library on mount. Must wrap the entire body. Never remove it.
- **`fluid`** on `<sgds-masthead>` — makes the masthead full-width. Always include it.
- **`<sgds-footer>` attributes** — update `contactHref` and `feedbackHref` to real URLs when the app has them; `privacyHref="/privacy"` and `termsOfUseHref="/terms"` are pre-wired to existing pages.

Only the `<main>` content changes between pages. Navigation (`<sgds-mainnav>`), sidebars, and page-specific layouts all go inside `<main>`.

---

## Component Priority (SGDS-First)

Before writing any UI markup, check if an SGDS component covers the need. Fall back to shadcn only when SGDS has no equivalent.

| Need | Use SGDS | Fallback to shadcn/ui |
|------|----------|----------------------|
| Buttons, badges, alerts | `<sgds-button>`, `<sgds-badge>`, `<sgds-alert>` | Never — no shadcn fallback exists for these |
| Cards | `<sgds-card>`, `<sgds-icon-card>`, `<sgds-image-card>` | Never — no shadcn fallback exists for these |
| Tables | `<sgds-table>` | `<Table>` if sorting/filtering logic needed |
| Modals, drawers | `<sgds-modal>`, `<sgds-drawer>` | `<Dialog>` only if complex React state required |
| Forms, inputs, selects | `<sgds-input>`, `<sgds-select>`, `<sgds-checkbox>` | Never — no shadcn fallback exists for these |
| Tabs, accordions | `<sgds-tab>`, `<sgds-accordion>` | Never — no shadcn fallback exists for these |
| Navigation | `<sgds-mainnav>`, `<sgds-sidebar>` (still RC — use `<sgds-sidenav>` instead for a stable production nav), `<sgds-breadcrumb>` | Never — no shadcn fallback exists for these |
| Pagination | `<sgds-pagination>` | Never — no shadcn fallback exists for these |
| Toast notifications | — | `sonner` (SGDS toast is not React-friendly) |
| Charts | — | `recharts` or ECharts per `sgds-data-visualisation` |

**Check each row independently — a fallback granted to one component does
not carry over to others used alongside it.** Observed in a real session:
an agent's own stated plan bundled Table's sorting/filtering exception
together with Select and Badge under one justification ("I'll install
shadcn table/select/badge — used for the data-dense table & filters"),
even though the Table row's exception is specific to Tables and the
Select/Badge rows say "Never." In that instance the actual implementation
still ended up using `<sgds-select>`/`<sgds-badge>` correctly — the flawed
reasoning didn't make it into code that time — but treat the pattern
itself as the warning sign: if a plan groups a shadcn exception together
with sibling components "because they're part of the same view," stop and
check each row against what's actually being written, not what an
already-justified neighbour is using.

This table decides *which library* — it does not cover *how to compose*
what's chosen. Read [frontend-design/SKILL.md](frontend-design/SKILL.md)
for grounding two decisions that stay open even in an all-SGDS build:
`sgds-theming`'s brand colour/font/night-mode choice, and how
`sgds-blocks` get combined and ordered on the page. It also covers
whatever fills a genuine SGDS gap (shadcn, an approved third-party
library, or custom code) — see "Interior Design Principles" below for
that case specifically.

---

## Style Selection by Context

Detect the type of page from the user's prompt and apply the matching treatment. When a prompt matches more than one row (e.g. "admin dashboard" hits both "dashboard" and "admin"), earlier rows in this table take priority.

| Prompt signals | Style mode | Treatment |
|---------------|-----------|-----------|
| "dashboard", "analytics", "metrics", "overview" | **Data-dense app** | Compact density, `tabular-nums` everywhere, stat cards + tables, muted palette |
| "landing page", "marketing", "homepage", "hero" | **Marketing** | Relaxed density, large hero headline, generous sections, one bold CTA |
| "settings", "preferences", "profile", "account" | **Form-focused** | Card containers per section, `<Tabs>` for grouping, save button bottom-right |
| "admin", "manage", "list of", "CRUD" | **Dense table** | Full-width table with search/filter bar, action dropdowns per row |
| "form", "submit", "apply", "register" | **Single-purpose form** | Centred `max-w-md` card, generous spacing, one primary submit button |
| "blog", "article", "content", "documentation" | **Prose** | `max-w-3xl`, `prose` typography classes, generous `space-y-6` |
| "chat", "messages", "conversation" | **Chat UI** | Flex column, messages bottom-aligned, input bar fixed bottom |
| "kanban", "board", "pipeline", "workflow" | **Board layout** | Horizontal scrolling columns, card items with drag handle visual |
| "calendar", "schedule", "events" | **Time-based** | Grid by time slots, today highlighted, event chips with category colours |

---

## Interior Design Principles (Non-SGDS Elements)

When SGDS has no equivalent, follow these principles — regardless of what actually ends up implementing the gap: a shadcn/ui component, a user-approved third-party library (installed via `vibe-npm` after the confirm-before-proceeding warning), or pure custom Tailwind/React with no library at all. They are inspired by Vercel/Stripe/Supabase but adapted for government context.

**Before applying the fixed rules below, read [frontend-design/SKILL.md](frontend-design/SKILL.md)** — it grounds the specific palette/typography/layout choice in the app's actual subject matter instead of defaulting to the same look every time. It operates *within* the register defined here (clean, calm, restrained), not instead of it — the rules below remain the floor.

**Design voice:**
- Clean, engineered, calm — not playful or marketing-heavy
- Ink-near-black on near-white canvas. One accent colour used sparingly (CTAs, active states only).
- Font ceiling: weight 600 (semibold) on headings — never `font-bold` (700)
- Use `tabular-nums` on all numbers in tables and stat cards (prevents layout shift, signals precision)

**Spacing (4px base unit):**
- Standard card padding: `p-6` (24px). `p-4` on primary cards feels cramped.
- Section gaps: `space-y-8`. Hero bands: `py-16`.
- Page reads as: large gaps between sections, tight interior within sections.

**Status colours (always pair bg tint + text — never colour alone):**
```tsx
// Success
className="bg-emerald-50 text-emerald-700"
// Warning
className="bg-amber-50 text-amber-700"
// Error
className="bg-red-50 text-red-700"
// Info
className="bg-blue-50 text-blue-700"
```

**Card elevation:**
- Default card: `rounded-xl border border-border/50 shadow-sm`
- Hover lift: `transition-shadow hover:shadow-md`
- Modal: `shadow-xl` with `backdrop-blur-sm` on the overlay

**Things that make UI look cheap (avoid):**
- ❌ Single heavy `shadow-lg` on cards — use subtle stacked shadows or just a border
- ❌ Multiple competing accent colours on one page
- ❌ Inconsistent padding (mixing `p-4` and `p-6` on same-level cards)
- ❌ Numbers without `tabular-nums` in data tables
- ❌ Raw `<select>` or `<input>` without SGDS or shadcn styling
- ❌ Full-width content without `max-w-` constraint

---

## Iterative Feedback Interpretation

When the user gives vague follow-up feedback, map it to concrete changes:

| User says | Action |
|-----------|--------|
| "make it better" / "improve it" | Add missing loading states, empty states, hover effects, consistent spacing, better typography hierarchy |
| "more professional" | Remove playful colours, tighten spacing, add subtle borders, use `font-medium` instead of bold, mute secondary text |
| "more modern" | Add micro-animations (`transition-all`), reduce borders, increase radius |
| "simplify" / "cleaner" | Remove decorative elements, reduce to 2 colours, increase whitespace, fewer card borders |
| "make it pop" / "more visual" | Add gradient accent, larger stat numbers, coloured status badges, subtle shadows on cards |
| "too cramped" / "more space" | Increase `gap` and `p` values by one step (4→6, 6→8), add section separators |
| "too much whitespace" / "compact" | Reduce `gap` and `p` by one step, use `text-xs` for secondary info |
| "make it dark" / "dark mode" | For shadcn-only elements: add `next-themes`, wrap in ThemeProvider, add toggle button in header. **This does NOT affect the mandatory `<sgds-masthead>`/`<sgds-mainnav>`/`<sgds-footer>` shell** — those need SGDS's own independent night mode (`.sgds-night-theme` class + `themes/night.css`, see sgds-theming skill) added separately, or the shell will stay in day mode while shadcn areas go dark. |

**Key rule:** Change ONLY what the feedback refers to. Do not rebuild the page from scratch.

---

## Gov/Enterprise Vocabulary

Government and enterprise users phrase things differently from startup developers:

| They say | They mean | Build this |
|----------|-----------|-----------|
| "module" | A feature section or bounded area | A page or tab with its own nav item |
| "portal" | A dashboard with role-based views | Dashboard with sidebar nav, role-filtered content |
| "workplan" / "work plan" | A project tracker with timelines | Kanban board or table with status + dates |
| "tracker" | A CRUD table with status workflow | Table with Status badge column, filter by status |
| "directory" | A searchable list of people/items | Table with search, avatar+name column, contact info |
| "registry" | A formal lookup table with CRUD | Admin table with Add/Edit/Delete, validation |
| "submission" / "request form" | A multi-step form with review | Wizard form with steps, review page before submit |
| "report" / "reporting" | Data visualisation with filters | Charts + stat cards + date range picker |
| "approval workflow" | A list with approve/reject actions | Table with pending items, action buttons, status trail |
| "audit trail" / "activity log" | Chronological event list | Timeline view with filters, timestamps, actor names |
| "role-based access" | Different views per user type | Conditional rendering based on role, nav items filtered |
| "export" | Download as CSV/PDF | Button that triggers file download, show loading state |

---

## Multi-turn Context Rules

1. **Read the current page first** — before making any changes, understand what's already built
2. **Add, don't replace** — unless the user says "start over", add alongside existing elements
3. **Match the existing style** — if the page uses SGDS cards, add more SGDS cards
4. **Maintain layout integrity** — do not break the grid structure or move existing elements unless asked
5. **Remember earlier decisions** — colour scheme, layout pattern, component choices stay consistent
6. **Do not re-introduce removed things** — if the user asked to remove something, do not add it back

**When user says "start fresh" / "redo" / "scrap this":**
- Clear the page content but keep the root layout shell (masthead, footer)
- Reset to the placeholder homepage state
- Ask what they want to build next (exception to the "don't ask" rule)

---

## Implicit Requirements

Things users always expect but never explicitly ask for. Add these automatically:

**Every page must have:**
- [ ] `<sgds-masthead>` at top and `<sgds-footer>` at bottom (inherited from root layout — verify it's there)
- [ ] Responsive layout (works on mobile without horizontal scroll)
- [ ] Loading state (skeleton or spinner) if data is fetched
- [ ] Empty state when there's no data (icon + message + action)
- [ ] Proper heading hierarchy (only one `h1` per page)

**Every form must have:**
- [ ] Client-side validation with inline error messages
- [ ] Submit button disabled while submitting (loading spinner)
- [ ] Success feedback (toast or redirect)
- [ ] Proper `<label>` on every input (not just placeholders)

**Every table must have:**
- [ ] At least 5–8 rows of realistic mock data
- [ ] Hover state on rows
- [ ] Empty state when filtered to zero results
- [ ] Column headers that explain the content

**Every action (create/edit/delete) must have:**
- [ ] Confirmation dialog before destructive actions
- [ ] Success toast after completion
- [ ] Error handling if it fails
- [ ] Loading state on the trigger button

**Mock/seed data must also be deterministic, not just realistic.** Never use
`Date.now()`, `Math.random()`, or a mutable module-level counter inside data
that renders during initial page load (module-level constants, or a
`useState(() => ...)` initializer) — the value differs between the server
render and the client's hydration pass, causing a hydration mismatch.
Confirmed in a real session: a module-level reference-number counter and
`Date.now()`/`Math.random()` inside seed records caused exactly this. Use
fixed literals or an index-based calculation instead (e.g. `` `REQ-${1000 +
i}` `` from the array index, not an incrementing counter).

---

## Scope Judgment

| Situation | Approach |
|-----------|----------|
| First prompt, full feature described | Go all-in — build a complete working page |
| User points at something specific | Be surgical — change only what they reference |
| User says "beautiful", "polished", "for a demo" | Add extra polish (animations, consistent spacing, quality mock data) |
| User says "simple", "basic", "MVP" | Keep it minimal — no extra features |

**Never over-build:**
- Do not add auth unless asked
- Do not add database unless persistence is explicitly needed
- Do not add dark mode unless requested
- Do not create separate pages when everything fits on one

---

## Accessibility

- All interactive elements must be keyboard-navigable (use semantic HTML: `<button>`, `<a>`, not `<div onClick>`)
- Images need descriptive alt text (not "image" or "icon")
- Colour must not be the only differentiator — pair with icons or text labels
- Form inputs must have visible `<label>` elements (not just placeholders)
- Use `aria-label` on icon-only buttons
- Focus states must be visible — do not override `focus-visible` styles

---

## Images & SVGs

**1. Lucide icons (preferred for UI icons):**
```tsx
import { Users, DollarSign, TrendingUp } from "lucide-react"
<Users className="h-5 w-5 text-muted-foreground" />
```

**2. SVG/PNG as static asset:**
```tsx
{/* eslint-disable-next-line @next/next/no-img-element */}
<img src="/logo.svg" alt="Logo" className="h-8 w-auto" />
```
Place files in `public/` — served at the root URL.

**Rules:**
- For icons in plain React/shadcn markup: always use Lucide React — do
  not create custom SVG icon components
- **Exception — inside an SGDS component's dedicated icon slot** (e.g.
  `slot="leftIcon"`/`"rightIcon"` on `<sgds-button>`, or icon slots on
  `<sgds-icon-list>` and similar): use `<sgds-icon name="...">`, never a
  Lucide component. Confirmed in a real session: a Lucide `X` placed
  inside `slot="leftIcon"` had to be caught and fixed after the fact —
  the slot expects an `<sgds-icon>` element specifically. See
  [sgds-components/reference/icon.md](sgds-components/reference/icon.md).
- **`<sgds-icon>`'s `name` attribute is validated only at runtime, not by
  `tsc` or the build** — a typo, or a guessed name from another icon
  library (e.g. Bootstrap Icons' `-fill`/`-lg` suffixes, which don't
  exist in SGDS's registry), silently renders nothing and only logs a
  browser-console warning. Since `self-heal.md` now runs `tsc --noEmit`
  only (not a full build, and never the browser console), this class of
  bug is invisible to the automatic check — grep every
  `<sgds-icon name="...">` you write against `icon.md`'s Available Icon
  Names list before considering the work done, don't rely on self-heal
  to catch it.
- For logos/illustrations: place in `public/` and use `<img>`
- Never use `next/image` for SVGs — it adds unnecessary complexity
- Do not inline large SVG markup in JSX — save as a file and import
- When a placeholder image is needed, use a coloured `<div>` with an icon, not a broken image URL

**3. Fetching and processing real photos (e.g. from the web):**

The VIBER session container runs on a small, fixed resource plan shared by
four services at once (`caddy`, `code-server`, `agent-sidecar`, `dev-server`)
— confirmed by a real incident where firing a second build check before the
first returned caused a SIGKILL (OOM) on this container (see self-heal.md).
Downloading and processing several large images back-to-back is the same
class of risk: decoding a large image into memory for resizing can spike
usage well past the compressed file size, and doing that for multiple images
in quick succession — on top of the dev-server and code-server already
resident — can trip the same OOM kill, which surfaces to the user as a
generic `502`/"Chat error" with no clear cause. If this template is ever
deployed on a container with meaningfully more memory, this whole rule
becomes unnecessary caution rather than a real requirement — it exists
specifically because of the small shared footprint described above, not as
a general best practice.

Given that constraint, while it holds:
- Process one image at a time: download → downscale/compress immediately →
  confirm the result → only then move to the next. Do not download several
  large images first and process them all together afterward.
- Prefer requesting an already-small version at the source (many image
  hosts support a size/width query param) over downloading a full-resolution
  original and resizing it locally.
- Do not run image processing back-to-back with another memory-heavy step
  (e.g. a production build check) in the same turn — finish and confirm one
  before starting the other.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
