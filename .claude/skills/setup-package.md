---
name: "setup-package"
description: "Category router for adding packages or UI components. Use when the user asks to install a package, add a UI component, or a skill needs a dependency that isn't present. Routes to vibe-shadcn (shadcn/ui components) or vibe-npm (regular npm packages)."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  routes_to: vibe-shadcn, vibe-npm
---

# setup-package

Route to the correct installation skill based on what is being added.

## Routing

| What is needed | Read |
|----------------|------|
| A UI component from shadcn/ui (button, dialog, table, badge, etc.) | `.claude/skills/vibe-shadcn/SKILL.md` |
| Any other npm package (recharts, date-fns, framer-motion, etc.) | `.claude/skills/vibe-npm/SKILL.md` |

**Before routing to `vibe-shadcn`:** always ask yourself if SGDS already covers the need (see CLAUDE.md component priority table). If `<sgds-button>`, `<sgds-table>`, etc. applies — use SGDS instead and do not install a shadcn component at all.

**If the request explicitly names a third-party UI library that is neither SGDS nor shadcn/ui** (e.g. Material UI, Chakra UI, Ant Design, Bootstrap) — before routing to `vibe-npm`, warn the user once: *"This will move away from the Singapore Government Design System (SGDS) visual language this app is otherwise built on — the new component won't match the masthead/footer/mainnav styling around it. Do you want to continue anyway?"* Only proceed to `vibe-npm` after they confirm. This confirmation step applies only when a specific alternative library is explicitly named — normal SGDS-first / shadcn-fallback routing above needs no confirmation.

## Rules

- **Never run `npm install` or the shadcn CLI directly from this
  file** — that's entirely the delegated skill's responsibility. If you
  find yourself about to install something directly from here, stop and
  go read `vibe-shadcn`/`vibe-npm` instead.
- **Don't skip straight to a specific skill without checking the SGDS
  component priority table first** — that's what keeps this router from
  installing shadcn components SGDS already covers.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
