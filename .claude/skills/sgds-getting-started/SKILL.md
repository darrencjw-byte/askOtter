---
name: "sgds-getting-started"
description: "Starting point for any new application built with the SGDS web component library. Apply this skill first whenever a user is bootstrapping a new SGDS project, setting up a new app, or asking where to begin with SGDS. Covers font setup, foundation CSS, utilities, components, and app layout in the correct order."
metadata:
  author: singapore-design-system
  version: "0.0.0"
  audience: external
  category: setup
---

# Getting Started with SGDS

> **New to SGDS?** See **[sgds-workflow](../sgds-workflow/SKILL.md)** for the full skill map and reading order before continuing.

When building any application with the SGDS web component library, complete these four steps in order before writing any component or page code.

---

## Step 1 — Set the Font

SGDS foundation styles use the **Inter** typeface by default. Add the Google Fonts import to the `<head>` of your HTML document before any SGDS CSS. The URL below loads only the four weights defined by the SGDS design tokens (300, 400, 600, 700) in both normal and italic styles.

```html
<head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,600;0,14..32,700;1,14..32,300;1,14..32,400;1,14..32,600;1,14..32,700&display=swap"
    rel="stylesheet"
  />
</head>
```

> **Next.js (this template):** Skip the `<link>` tags above. Inter is already loaded via `next/font/google` in `src/app/layout.tsx` — that is the correct Next.js pattern (self-hosted, subsetting, no CDN). Adding CDN `<link>` tags on top of `next/font` causes duplicate font loading. Step 1 is already done; proceed to Step 2.

---

## Step 2 — Import Foundation and Utility CSS

**Put these three imports in their own dedicated CSS file — a `sgds.css` sitting alongside your main Tailwind entry point (e.g. `globals.css`), never merged into that same file.** `utility.css` re-imports Tailwind's own theme/utilities under the `sgds:` prefix, including a `@theme { --*: initial; ... }` reset — if this shares a processing context with your app's own `@import "tailwindcss"`, that reset wipes out Tailwind's *entire default, unprefixed* utility generation project-wide (confirmed: even non-color, non-themed utilities like `flex` stop generating). Keeping it in a separate file, imported as its own stylesheet, avoids the collision entirely.

`sgds.css` (new, dedicated file):
```css
/* 1. Theme tokens — must come first */
@import "@govtechsg/sgds-web-component/themes/day.css";
/* Optional — add only if supporting dark/night mode */
@import "@govtechsg/sgds-web-component/themes/night.css";

/* 2. Foundation styles (typography, headings, body, grid) */
@import "@govtechsg/sgds-web-component/css/sgds.css";

/* 3. Utility classes (sgds: prefix) — must be processed by Tailwind */
@import "@govtechsg/sgds-web-component/css/utility.css";
```

Then import this file as its own stylesheet wherever your app's root/entry point already imports its main CSS (in Next.js App Router, that's `src/app/layout.tsx`):
```tsx
import "./globals.css";
import "./sgds.css";
```

`utility.css` contains Tailwind v4 directives and **must be processed by your Tailwind pipeline** — it cannot be imported as a plain JS import. It just must not be `@import`ed *inside* the same file as your app's own `@import "tailwindcss"`.

> For full details on utility class setup, see **[sgds-utilities](../sgds-utilities/SKILL.md)**.

---

## Step 3 — Register SGDS Web Components

Import the component library once at your app entry point (JS/TS):

```js
import "@govtechsg/sgds-web-component";
```

This registers all `<sgds-*>` custom elements globally.

> For React, Vue, Angular, and Next.js-specific integration details, see **[sgds-components](../sgds-components/SKILL.md)**.

---

## Step 4 — Use an SGDS App Layout

Every SGDS application should be structured using one of the two recommended layout templates. Choose based on your app type:

| App type | Layout | Container class |
|----------|--------|-----------------|
| Public-facing, general-purpose | Simple App | `.sgds-container` |
| Internal tool, dashboard, transactional | Sidebar App | `.sgds-container-sidebar` |

**Simple App** (public-facing):

```html
<div>
  <sgds-masthead fluid></sgds-masthead>
  <sgds-mainnav fluid>
    <strong slot="brand">My App</strong>
  </sgds-mainnav>
</div>
<div class="sgds:flex sgds:flex-col sgds:w-full">
  <div class="sgds-container sgds:py-2-xl">
    <!-- Page content -->
  </div>
  <sgds-footer></sgds-footer>
</div>
```

**Sidebar App** (dashboards / internal tools):

```html
<div class="sgds:sticky sgds:top-0">
  <sgds-masthead fluid></sgds-masthead>
  <sgds-mainnav fluid>
    <strong slot="brand">My App</strong>
  </sgds-mainnav>
</div>
<div class="sgds:flex sgds:flex-row">
  <div class="sgds:sticky sgds:h-[calc(100vh-108px)] sgds:overflow-y-scroll sgds:top-27 sgds:w-68 sgds:border-r sgds:border-muted">
    <!-- Sidebar navigation -->
  </div>
  <div class="sgds:flex sgds:flex-col sgds:w-full">
    <div class="sgds-container-sidebar sgds:py-2-xl">
      <!-- Page content -->
    </div>
    <sgds-footer></sgds-footer>
  </div>
</div>
```

> For full layout details and responsive container breakpoints, see **[Application Shell](../sgds-blocks/reference/application-shell.md)**.

---

## For AI agents

**Component-first rule**: Before building any UI element with plain HTML and utility classes, always check whether an SGDS web component already covers the need. Consult the `components-*` skills first. Only fall back to custom markup when no SGDS component exists for the use case.

1. Always complete all four steps before generating any component or page code for a new SGDS project.
2. The font `<link>` tags must go in the HTML `<head>` — not in CSS or JS imports. For font customisation or theming, refer to **[sgds-theming](../sgds-theming/SKILL.md)**. **In Next.js (this template), font CDN `<link>` tags are NOT used** — Inter is already loaded via `next/font/google` in `layout.tsx`. Do not add them.
3. CSS import order within the dedicated `sgds.css` file matters: `themes/day.css` → `css/sgds.css` → `css/utility.css`. The theme file must come first so CSS variable tokens are available when foundation and utility styles are processed.
4. `css/utility.css` must be imported inside a CSS file processed by Tailwind v4 — importing it directly in JavaScript will not generate the `sgds:` utility classes. But it must NOT be imported inside the same file as your app's own `@import "tailwindcss"` — always keep it in its own separate file (Step 2), imported as its own stylesheet.
5. The single JS import `import "@govtechsg/sgds-web-component"` registers all components. Do not import individual components unless explicitly doing tree-shaking.
6. Always wrap page content in `.sgds-container` (simple app) or `.sgds-container-sidebar` (sidebar app) — never use raw `sgds:max-w-*` utilities to replicate container behaviour.
7. When in doubt about app type: public-facing digital services → simple app; internal tools, dashboards, admin portals → sidebar app.
