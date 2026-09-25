---
name: "vibe-shadcn"
description: "Install a shadcn/ui component via the CLI. Reached via setup-package. Always check SGDS has no equivalent before installing — SGDS components are the default in this template."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# vibe-shadcn

Install a shadcn/ui component when SGDS has no equivalent for the need.

---

## Step 0 — SGDS gate

**SGDS already covers all of these — do NOT install a shadcn equivalent
for any of them without an explicit user reason:**

| Need | Use instead |
|------|-------------|
| Buttons, badges, alerts | `<sgds-button>`, `<sgds-badge>`, `<sgds-alert>` |
| Cards | `<sgds-card>`, `<sgds-icon-card>`, `<sgds-image-card>` |
| Tables (no sorting/filtering) | `<sgds-table>` |
| Inputs, select, checkbox, datepicker | `<sgds-input>`, `<sgds-select>`, `<sgds-checkbox>`, `<sgds-datepicker>` |
| Tabs, accordions | `<sgds-tab>`, `<sgds-accordion>` |
| Navigation, breadcrumb, pagination | `<sgds-mainnav>`, `<sgds-sidebar>`, `<sgds-breadcrumb>`, `<sgds-pagination>` |
| Tooltip, skeleton, dropdown/action menu | `<sgds-tooltip>`, `<sgds-skeleton>`, `<sgds-dropdown>`, `<sgds-overflow-menu>` |

This table is a quick gate, not exhaustive — for anything not listed
above, check `.claude/skills/sgds-components/SKILL.md`'s "Available
Components" table (the complete, authoritative list) before concluding
SGDS has no equivalent.

**Shadcn is appropriate for:** Dialog/AlertDialog (complex React state),
Table *specifically when sorting/filtering is needed* (plain display
tables still use `<sgds-table>`), complex form state with
react-hook-form, Toast (sonner — already installed), and anything else
genuinely not covered by SGDS after checking the table above.

---

## Step 1 — Check if already installed

Pre-installed in this template: `button`, `card`, `input`, `label`, `sonner`. Skip install if already present.

```bash
ls src/components/ui/ | grep -i "<component-name>"
```

---

## Step 2 — Install

```bash
npx shadcn@latest add <component-name> --yes
```

Always use `--yes` to skip prompts. Never manually create files in `src/components/ui/` — always use the CLI.

If the install fails, check that `components.json` exists at the project root.

---

## Step 3 — Verify and import

```bash
ls src/components/ui/<component-name>.tsx
```

Then import:
```tsx
import { ComponentName } from "@/components/ui/component-name"
```

---

## Step 4 — Self-heal

```bash
tail -10 /var/log/devserver.err | grep -c "Error:"
```

If count > 0, follow `self-heal.md`.

---

## Commonly needed shadcn components (no SGDS equivalent)

| Need | Install |
|------|---------|
| Confirmation before destructive action | `alert-dialog` |
| Complex modal with React state | `dialog` |
| Dividers | `separator` |
| Charts | use `recharts` via `vibe-npm` instead |

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
