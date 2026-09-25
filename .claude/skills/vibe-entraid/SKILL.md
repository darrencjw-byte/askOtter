---
name: "vibe-entraid"
description: "Add direct Microsoft Entra ID (Azure AD) SSO — not WOG AD/TechPass via GovAuth, not the whole-of-government tenant specifically — using Better Auth's built-in socialProviders.microsoft, for an organisation's own Entra ID app registration. Use when the user specifically names direct Entra ID/Azure AD SSO, OR when directed here by setup-auth's routing. For a generic 'add login' request, setup-auth.md is the correct entry point instead."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# vibe-entraid

Direct Microsoft Entra ID SSO for POC applications, using Better Auth's
built-in `socialProviders.microsoft` — for an organisation's own Azure AD
app registration, not the whole-of-government WOGAD tenant specifically
(that's `vibe-govauth`'s GovAuth-proxied path) and not TechPass (that's
`vibe-techpass`). Do not conflate the three — different credentials,
different registration flows, different libraries even (this uses Better
Auth; `vibe-techpass` uses Auth.js/NextAuth).

**Dual-domain support:** a VIBER session is always reachable on two
domains — the live preview (`DOMAIN_URI_VIBER`) and the stable main/POC
deployment (`DOMAIN_URI_MAIN`) — and login must work on both. Better
Auth's built-in `socialProviders` routes DO support this natively via the
dynamic `baseURL` config form (`baseURL: { allowedHosts, fallback }`),
which resolves per request from the incoming Host header. This is
different from `vibe-govauth`'s `genericOAuth` **plugin**, which freezes
its own `ctx.baseURL` once at plugin-init time and needs a custom
per-request `getAuth(requestHost)` factory to work around that —
`socialProviders` has no such limitation, so this skill uses the dynamic
`baseURL` form directly in a single static `betterAuth()` call (Step 3),
no factory needed.

---

## Step 0 — Check whether this was already started before

```bash
ls src/lib/auth.ts src/lib/auth-client.ts src/app/login/page.tsx 2>/dev/null
```

- **None exist**: fresh start, proceed to Step 1.
- **Some exist but not all**: resume at the matching step, don't restart.
- **All exist**: check whether `src/lib/auth.ts` already uses Better
  Auth's `socialProviders.microsoft` (this skill) vs NextAuth
  (`vibe-techpass`) or `genericOAuth` (`vibe-govauth`) — don't overwrite a
  different, working auth setup without confirming with the user first.

---

## Step 1 — Check env vars

```bash
echo "BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET:+SET}" && echo "DOMAIN_URI_VIBER=${DOMAIN_URI_VIBER:+SET}" && echo "DOMAIN_URI_MAIN=${DOMAIN_URI_MAIN:+SET}" && echo "MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID:+SET}" && echo "DATABASE_URL=${DATABASE_URL:+SET}"
```

**Required for this path:**
- `DATABASE_URL` — this path needs a database to store sessions. If not
  set, hand off to `.claude/skills/setup-db.md` first — don't implement a
  database connection inline here. **Better Auth's `User`/`Session`/`Account`/`Verification`
  models are already present in this template's `prisma/schema.prisma` — do
  not ask `vibe-neondb` to add them again. Only invoke `setup-db` to get a
  `DATABASE_URL` and run migrations.**
- `BETTER_AUTH_SECRET` — signing secret (generate with
  `openssl rand -base64 32` if missing, always show the generated value)
- `DOMAIN_URI_VIBER` — the live VIBER session preview domain, bare, no
  path (e.g. `https://s3037-yourapp.cio.sandbox.gov.sg`) — changes every
  fresh VIBER session, re-check it, don't assume an old value still works
- `DOMAIN_URI_MAIN` — the stable main/POC domain, bare, no path (e.g.
  `https://yourapp.cio.sandbox.gov.sg`)
- `MICROSOFT_CLIENT_ID` + `MICROSOFT_CLIENT_SECRET` + `MICROSOFT_TENANT_ID`
  — the organisation's own Entra ID app registration credentials

---

## Step 2 — If credentials/env vars are missing

Tell the user:

> "Direct Microsoft Entra ID SSO needs a few things configured first:
> 1. A PostgreSQL database (`DATABASE_URL`) — I'll set this up via
>    `setup-db` if you don't have one yet (the database schema models are
>    already in `prisma/schema.prisma` — no changes needed there)
> 2. Auth secret (`BETTER_AUTH_SECRET`) and both domains (`DOMAIN_URI_VIBER`, `DOMAIN_URI_MAIN`)
> 3. Your organisation's Entra ID app registration credentials — register
>    BOTH of these exact redirect URIs in the app registration:
>    - `https://<viber-session-domain>/api/auth/callback/microsoft`
>    - `https://<main-domain>/api/auth/callback/microsoft`
>
> Go to Advanced → Env Vars to add the secrets/credentials, then let me
> know once they're in."

**Then scaffold the UI without connecting it:**
- Create login page at `src/app/login/page.tsx` with a Microsoft sign-in
  button.
- Button shows a toast: "Auth not configured yet — add credentials in Env
  Vars".
- Don't add middleware that blocks access to existing pages.

**DO NOT STOP HERE.** The moment the user confirms the credentials are
added, continue immediately into Step 3 onward in the same response.

---

## Step 3 — Wire up Better Auth

1. **Check if auth files exist:**
```bash
ls src/lib/auth.ts src/lib/auth-client.ts 2>/dev/null
```

2. **If missing, create `src/lib/auth.ts`** — requires `src/lib/prisma.ts`
   to already exist (from `setup-db`/`vibe-neondb`; do not write a Prisma
   client here):
```typescript
import { betterAuth } from "better-auth";
import { prismaAdapter } from "@better-auth/prisma-adapter";
import { prisma } from "@/lib/prisma";

const viberHost = process.env.DOMAIN_URI_VIBER
  ? new URL(process.env.DOMAIN_URI_VIBER).host
  : undefined;
const mainHost = process.env.DOMAIN_URI_MAIN
  ? new URL(process.env.DOMAIN_URI_MAIN).host
  : undefined;

export const auth = betterAuth({
  database: prismaAdapter(prisma, { provider: "postgresql" }),
  secret: process.env.BETTER_AUTH_SECRET,
  // Dynamic baseURL — resolved per request from the incoming Host header,
  // so both the VIBER-session preview domain and the stable main/POC
  // domain work from this single static betterAuth() instance.
  baseURL: {
    allowedHosts: [viberHost, mainHost].filter((h): h is string => Boolean(h)),
    fallback: process.env.DOMAIN_URI_MAIN,
  },
  socialProviders: {
    microsoft: {
      clientId: process.env.MICROSOFT_CLIENT_ID!,
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET!,
      tenantId: process.env.MICROSOFT_TENANT_ID!,
    },
  },
});
```

3. **Create auth client** (`src/lib/auth-client.ts`):
```typescript
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: typeof window !== "undefined" ? window.location.origin : (process.env.DOMAIN_URI_MAIN || "http://localhost:3001"),
});
```

4. **Create API route** (`src/app/api/auth/[...all]/route.ts`):
```typescript
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

export const { GET, POST } = toNextJsHandler(auth);
```

5. **Run migrations** — the Better Auth models are already in `prisma/schema.prisma`. If `setup-db` was used, migrations were already run and include these tables — skip this step. Only run if the database was provisioned outside of `setup-db`:
```bash
npx prisma migrate dev --name init-auth
```

---

## Step 4 — Signed-in indicator and route protection

Same placement rules as `vibe-govauth`'s Step 6 (`<sgds-mainnav>`'s `end`
slot, `<sgds-masthead>` has no slots, no `position: fixed`).

```tsx
// In a protected page — show content if logged in, prompt if not
"use client";
import { authClient } from "@/lib/auth-client";

export default function ProtectedPage() {
  const { data: session, isPending } = authClient.useSession();

  if (isPending) return <Skeleton />;

  if (!session) {
    return (
      <Card className="mx-auto max-w-md p-6 mt-12 text-center space-y-3">
        <p className="text-sm font-medium">Sign in required</p>
        <p className="text-xs text-muted-foreground">
          Sign in with your Microsoft account to access this page.
        </p>
        <Button onClick={() => authClient.signIn.social({ provider: "microsoft" })}>
          Sign in with Microsoft
        </Button>
      </Card>
    );
  }

  return <>{/* Protected content */}</>;
}
```

**Never add middleware that blocks all routes** — scaffold, don't enforce
unless explicitly asked.

---

## Step 5 — Verify

1. `SELF_HEAL_BUILD_CHECK=1 npm run build` — fix any errors (the env var keeps this from colliding with the live dev server's own build output, see self-heal.md). If it fails on `_global-error`/`_not-found` with a React context crash unrelated to anything just written, check for a stray `NODE_ENV` value in the shell before assuming it's this auth code — see `vibe-neondb`'s build verification step for the full diagnosis; it's a general build-environment issue, not Entra ID-specific.
2. Test login from BOTH the VIBER-session and main/POC domains
   separately. If one fails with `redirect_uri mismatch`, confirm
   `DOMAIN_URI_VIBER` and `DOMAIN_URI_MAIN` are both set and that both
   hosts are landing in `allowedHosts` (Step 3) — and that both callback
   URLs are registered in the Entra ID app registration.
3. Confirm the signed-in indicator actually shows the user's name/email —
   a clean redirect is not proof a session was created.

---

## Common errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `BETTER_AUTH_SECRET is not defined` | Missing env var | Add in Advanced → Env Vars |
| `Can't reach database` | `DATABASE_URL` missing/wrong | Hand off to `setup-db` |
| `Invalid client_id` | Wrong Entra ID credentials | User should verify their Azure app registration |
| `redirect_uri mismatch` | The domain actually used isn't in `allowedHosts` (Step 3), or isn't registered in the Entra ID app | Confirm `DOMAIN_URI_VIBER`/`DOMAIN_URI_MAIN` are both set and both callback URLs are registered |
| `Session not found` | Database has no session tables | Run `npx prisma migrate dev --name init-auth` |
| `Module not found: better-auth` | Package not installed | `npm install better-auth @better-auth/prisma-adapter` |

---

## Rules

- **Never write GovAuth/`genericOAuth` code here** — that's entirely
  `vibe-govauth`'s responsibility.
- **Never write Auth.js/NextAuth code here** — that's `vibe-techpass`'s
  responsibility.
- **This path always needs a database** — hand off to `setup-db` rather
  than skipping or implementing a connection inline.
- **Never add middleware that blocks all routes** by default.
- After setup, run the `self-heal` skill to verify the build.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
