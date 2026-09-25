---
name: "vibe-npm"
description: "Install a regular npm package. Reached via setup-package. Use for any package that is not a shadcn/ui component — recharts, date-fns, framer-motion, etc."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# vibe-npm

Install an npm package and verify the build stays clean.

---

## Step 1 — Check if already installed

```bash
grep "<package-name>" package.json
```

If present, skip install — the package is already available.

---

## Step 2 — Install

```bash
npm install <package-name>
```

For dev-only dependencies (type definitions, build tools):
```bash
npm install -D <package-name>
```

**Rules:**
- Always use `npm` — this container only has npm, not pnpm or yarn
- Batch multiple packages in one command: `npm install pkg1 pkg2 pkg3`
- Never install speculatively — only when the code actively needs it

---

## Step 3 — Verify no conflicts

```bash
tail -5 /var/log/devserver.err
```

If the dev server crashed after install:
```bash
supervisorctl restart dev-server && sleep 5
```

If install fails with peer dependency errors:
```bash
npm install <package-name> --legacy-peer-deps
```

---

## Step 4 — Self-heal

```bash
tail -10 /var/log/devserver.err | grep -c "Error:"
```

If count > 0, follow `self-heal.md`.

---

## Common packages for this template

| Need | Package |
|------|---------|
| Charts | `recharts` |
| Date handling | `date-fns` |
| Tables with sorting/filtering | `@tanstack/react-table` |
| Drag and drop | `@dnd-kit/core @dnd-kit/sortable` |
| Rich text editor | `@tiptap/react @tiptap/starter-kit` |
| PDF generation | `@react-pdf/renderer` |
| CSV export | `papaparse` |
| File upload UI | `react-dropzone` |
| Animation | `framer-motion` |
| Dark mode | `next-themes` (already in dependencies) |

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
