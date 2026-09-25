# Next.js Project Template (VIBER Studio)

A full-stack Next.js starter for building government digital services inside VIBER Studio.

## Stack

| Layer | Tech |
|-------|------|
| Framework | Next.js 16 (App Router), React 19 |
| Language | TypeScript 5 (strict mode) |
| Styling | Tailwind CSS 4, shadcn/ui (base-nova) |
| Database | PostgreSQL via Prisma 7 |
| Auth | Better Auth (GovAuth / Entra ID) or Auth.js (direct TechPass / WOG AD) |
| Forms | react-hook-form + Zod 4 |
| Icons | Lucide React |
| Toasts | Sonner |

## Getting Started

The dev server runs on **port 3001** and is already started in VIBER Studio.

```bash
supervisorctl restart dev-server       # Restart dev server (already running — never run npm run dev)
SELF_HEAL_BUILD_CHECK=1 npm run build  # Production build (env var avoids colliding with the live dev server's own build output)
npm run lint                           # Lint check
```

## Project Structure

```
src/
  app/              # Pages, layouts, API routes
    globals.css     # Tailwind + shadcn theme
    sgds.css        # SGDS CSS — keep separate from globals.css, never merge
  components/       # Shared components
    sgds-provider.tsx # SGDS web component loader (required)
    ui/               # shadcn/ui primitives
  lib/              # Utilities
  generated/prisma/ # Auto-generated Prisma client
prisma/
  schema.prisma     # Database schema
```

## Path Alias

`@/*` → `./src/*`

```typescript
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
```

## Database

PostgreSQL with Prisma 7. Schema includes User, Session, Account, and Verification models for authentication.

**To add a database:**

1. Go to your **product config** page and click **Create Database**
2. Leave **"Add schema access to my VIBER session"** checked (on by
   default) — this sets `DATABASE_URL` in your live session automatically,
   no copy/pasting needed
3. If it wasn't auto-injected (e.g. no live VIBER session yet), copy the
   connection string shown and add `DATABASE_URL` manually in Viber
   Studio → **Advanced dropdown → Env Vars** instead
4. Either way, only the dev server needs restarting for the running
   process to pick up the value — the whole VIBER session does not need
   to restart

```bash
npx prisma generate    # Regenerate client after schema changes
```

See `.env.example` for all required variables.

## Authentication

GovAuth (WOG AD/TechPass sandbox proxy) and direct Entra ID use Better Auth; direct production TechPass and WOG AD use Auth.js. Provider configured via skill — see `.claude/skills/setup-auth.md`.

## UI Components

shadcn/ui components available out of the box: button, card, input, label, sonner (toast).

Add more:
```bash
npx shadcn@latest add dialog table select textarea --yes
```

## Government Compliance

The Singapore government masthead and footer are included in the root layout. These are mandatory for all government digital services and must not be removed.

## VIBER Studio

This template is designed for AI-assisted development in VIBER Studio:

1. Open the AI chat and describe what you want to build
2. The agent builds and iterates in real time
3. Preview changes in the built-in browser pane
4. Save your work with the Save button when ready
