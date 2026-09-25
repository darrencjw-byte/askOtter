---
name: "vibe-techpass"
description: "Add direct TechPass SSO (not via GovAuth) using Auth.js v5 (NextAuth) with the microsoft-entra-id provider. Use when the user specifically names TechPass as a direct connection (not through GovAuth), OR when directed here by setup-auth's routing. For a generic 'add login' request, setup-auth.md is the correct entry point instead. Always stateless by default (JWT session, no database) — a persistent DB-backed user profile is an optional addition, not a prerequisite."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: techpass-authentication
---

# vibe-techpass

Standalone direct TechPass SSO — connects straight to TechPass's Azure AD
tenant via Auth.js v5, without GovAuth's proxy. Use when the user
explicitly wants direct TechPass (not the simpler GovAuth-proxied path).
This is a different library (NextAuth, not Better Auth) and a different
registration flow than `vibe-govauth` — do not conflate the two, and do not
mix Better Auth code into this skill.

## Direct vs GovAuth — confirm which they need

GovAuth's proxied TechPass option (`vibe-govauth`) is simpler: no
separate Azure app registration, no agency admin required, sandbox/POC
ready immediately. Recommend `vibe-govauth` first unless the user:
- Has an existing TechPass Azure app registration and wants to use it
- Needs claims/scopes GovAuth's proxy doesn't expose
- Has explicitly asked for direct TechPass (no proxy)

---

## Step 0 — Check whether this was already started before

```bash
ls src/lib/auth.ts src/app/api/auth/[...nextauth]/route.ts src/app/login/page.tsx 2>/dev/null
```

- **None exist**: fresh start, proceed to Step 1.
- **Some exist but not all**: a previous run stopped mid-way — tell the
  user plainly what's missing and resume at the matching step rather than
  restarting.
- **All exist**: check whether `src/lib/auth.ts` already uses
  `next-auth/providers/microsoft-entra-id` (this skill) vs
  `next-auth/providers/microsoft-entra-id` with `id: "azure-ad"` (`vibe-wogad` — a
  second NextAuth provider can coexist in the same config, this doesn't
  necessarily mean overwrite) vs Better Auth (`vibe-govauth` or
  `vibe-entraid` — do not overwrite a working, different auth setup
  without confirming with the user first).

---

## Step 1 — Check what the user already has

Ask ONE question:

> "Do you already have a TechPass Azure AD app registration (Client ID,
> Tenant ID, Client Secret)? If yes, tell me and I'll walk you through the
> redirect URIs. If not, I'll guide you through registration first."

**Stop here if they don't have credentials yet** — go to Step 2.

---

## Step 2 — Registration walkthrough (if user doesn't have credentials yet)

**This app needs TWO redirect URLs registered, not one** — the live VIBER
session preview domain and the stable main/POC domain. Missing either
means login fails from whichever domain wasn't registered.

Tell the user:

> "Before registering, get both domains:
>
> 1. **VIBER session domain**: Preview pane → 'Open in new tab'
>    (e.g. `https://s3037-yourapp.cio.sandbox.gov.sg`) — changes every
>    fresh VIBER session, re-check it, don't assume an old value still
>    works.
> 2. **Main/POC domain**: your product's stable domain in Rabbit Deploy
>    (e.g. `https://yourapp.cio.sandbox.gov.sg`).
>
> Then, in your TechPass Azure AD app registration:
> 3. Add BOTH redirect URLs, using the exact path Auth.js builds:
>    - `https://<viber-session-domain>/api/auth/callback/microsoft-entra-id`
>    - `https://<main-domain>/api/auth/callback/microsoft-entra-id`
> 4. Add a logout URL: `https://<domain>/api/auth/signout` for each domain (Auth.js v5's catch-all route has no `logout` action — the valid one is `signout`).
> 5. Generate a Client Secret under Certificates & Secrets.
> 6. Copy the Client ID, Tenant ID, and Client Secret.
>
> Come back and tell me once you have all three."

**Stop here.** Do not write any auth code until credentials are confirmed.

---

## Step 3 — Generate the secret, confirm domains, set env vars

```bash
SECRET=$(openssl rand -base64 33) && echo "$SECRET"
```

Show the user ALL values to add in **Advanced → Env Vars**:

| Variable | Value |
|---|---|
| `AUTH_SECRET` | *(the value just generated — show it)* |
| `TECHPASS_DIRECT_CLIENT_ID` | *(Client ID from Step 2)* |
| `TECHPASS_DIRECT_CLIENT_SECRET` | *(Client Secret from Step 2)* |
| `TECHPASS_TENANT_ID` | *(Tenant ID from Step 2)* |

That's **4 env vars total**. No `DATABASE_URL` needed for this setup.

After the user confirms, verify:
```bash
echo "AUTH_SECRET=${AUTH_SECRET:+SET}" && echo "TECHPASS_DIRECT_CLIENT_ID=${TECHPASS_DIRECT_CLIENT_ID:+SET}" && echo "TECHPASS_DIRECT_CLIENT_SECRET=${TECHPASS_DIRECT_CLIENT_SECRET:+SET}" && echo "TECHPASS_TENANT_ID=${TECHPASS_TENANT_ID:+SET}"
```
Don't proceed until all show `SET`.

Restart automatically:
```bash
supervisorctl restart dev-server && sleep 3
```

**DO NOT STOP HERE.** Continue immediately into Step 4-6 in the same
response — confirming env vars is not the goal, working login is.

---

## Step 4 — Install next-auth and wire up Auth.js (stateless, no database)

Install next-auth if not already present:

```bash
npm install next-auth@^5.0.0-0
```

**`trustHost: true` is what makes this work across both the VIBER-session
and main/POC domains** — Auth.js computes the callback URL from the
incoming request's actual Host header rather than a single hardcoded
value. This is a different (and simpler) mechanism than `vibe-govauth`'s
per-request `getAuth(host)` factory, which was needed because Better
Auth's `genericOAuth` plugin has no equivalent trust-the-request-host
option. **Not yet empirically verified against the dual-domain redirect
scenario within this project** — Step 6's test is what actually confirms
it, don't assume it works from `trustHost` alone.

`src/lib/auth.ts`:

```typescript
import NextAuth from "next-auth";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  providers: [
    MicrosoftEntraId({
      clientId: process.env.TECHPASS_DIRECT_CLIENT_ID!,
      clientSecret: process.env.TECHPASS_DIRECT_CLIENT_SECRET!,
      issuer: `https://login.microsoftonline.com/${process.env.TECHPASS_TENANT_ID}/v2.0`,
    }),
  ],
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
});
```

No `database` adapter, no Prisma import — this is the stateless default.
Do not add one unless Step 5 is explicitly requested.

`src/app/api/auth/[...nextauth]/route.ts`:

```typescript
import { handlers } from "@/lib/auth";
export const { GET, POST } = handlers;
```

`middleware.ts` — re-export pattern, avoids Edge Runtime env var issues:

```typescript
export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/auth).*)"],
};
```

Root layout — add `SessionProvider` around `{children}` only. **Do NOT replace the whole layout** — the existing layout already has `SgdsProvider`, `<sgds-masthead>`, `<sgds-footer>`, and `<Toaster>` which are mandatory and must stay.

In `src/app/layout.tsx`, add the import and wrap `{children}` inside `<main>`:

```tsx
// Add this import at the top of src/app/layout.tsx:
import { SessionProvider } from "next-auth/react";

// Change only the <main> line — keep everything else untouched:
// BEFORE: <main className="flex-1">{children}</main>
// AFTER:
<main className="flex-1">
  <SessionProvider>{children}</SessionProvider>
</main>
```

The full layout around it (`SgdsProvider`, masthead, footer, Toaster) must remain unchanged.

Login page (`src/app/login/page.tsx`) — dedicated page, not the homepage:

```tsx
"use client"
import { signIn } from "next-auth/react"

export default function LoginPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="text-base text-zinc-600">Sign in with TechPass to continue.</p>
        </div>
        <button
          onClick={() => signIn("microsoft-entra-id", { callbackUrl: "/" })}
          className="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-4 text-left hover:bg-zinc-50 transition-colors"
        >
          <p className="text-base font-medium">Sign in with TechPass</p>
        </button>
      </div>
    </div>
  )
}
```

Signed-in indicator — same placement rules as `vibe-govauth`'s Step 6
(`<sgds-mainnav>`'s `end` slot, `<sgds-masthead>` has no slots, no
`position: fixed`):

```tsx
"use client"
import { useSession, signOut } from "next-auth/react"
import Link from "next/link"

export function AuthNav() {
  const { data: session, status } = useSession()
  if (status === "loading") return null
  if (!session?.user) {
    return <Link href="/login" className="text-sm font-medium">Sign in</Link>
  }
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm">{session.user.name || session.user.email}</span>
      <button onClick={() => signOut({ callbackUrl: "/login" })}>Sign Out</button>
    </div>
  )
}
```

**Any OTHER nav link you add for a login-gated feature should default
to the same visibility rule as `AuthNav` itself — hidden when signed
out, not "shown to everyone, the destination page redirects."**
Confirmed wrong in a real session (on `vibe-govauth`, but the same
mistake applies here): a nav link to a guarded page was left visible to
signed-out visitors on the first pass, and the user had to explicitly
point out it shouldn't be visible before it got fixed to check the
session the same way `AuthNav` does. The destination page's own guard is
still the real security boundary — this is about matching the nav
link's visibility to it, not replacing it.

**Guarding an entire page** (e.g. "add a login-only reports page") —
check `status === "loading"` first and render nothing/a skeleton while
it resolves, THEN check the session. Don't fetch or render the page's
real content until both checks have passed — fetching data before the
session check resolves risks a signed-out visitor briefly seeing a flash
of the content before a redirect fires. Prefer an inline "sign in
required" prompt over a `router.push` redirect from a `useEffect` — a
redirect still has to render *something* on the tick before it fires,
whereas an inline prompt never touches the protected data at all:

```tsx
// In a protected page — show content only once signed in, prompt if not
"use client"
import { useSession, signIn } from "next-auth/react"

export default function ProtectedPage() {
  const { data: session, status } = useSession()

  if (status === "loading") return <Skeleton />

  if (!session?.user) {
    return (
      <Card className="mx-auto max-w-md p-6 mt-12 text-center space-y-3">
        <p className="text-sm font-medium">Sign in required</p>
        <p className="text-xs text-muted-foreground">
          Sign in with TechPass to access this page.
        </p>
        <Button onClick={() => signIn("techpass")}>Sign in</Button>
      </Card>
    )
  }

  // Only reached once session is confirmed — safe to fetch/render real data here
  return <RealPageContent />
}
```

---

## Step 5 — Optional: persistent DB-backed user profile

Only do this if the user explicitly asks for it (e.g. "remember user
roles", "track which users have logged in"). Do not add this by default —
Step 4's stateless setup is the default for a reason.

If requested: hand off to `.claude/skills/setup-db.md` first, then add a
`signIn`/`jwt` callback that upserts into a `User`/`Account` table via
Prisma. This is a genuinely different config, not a small addition —
treat it as its own step with the user's explicit confirmation before
writing it.

---

## Step 6 — Verify

1. `SELF_HEAL_BUILD_CHECK=1 npm run build` — fix any errors (the env var keeps this from colliding with the live dev server's own build output, see self-heal.md). If it fails on `_global-error`/`_not-found` with a React context crash unrelated to anything just written, check for a stray `NODE_ENV` value in the shell before assuming it's this auth code — see `vibe-neondb`'s build verification step for the full diagnosis; it's a general build-environment issue, not TechPass-specific.
2. Confirm both callback URLs are registered exactly as shown in Step 2.
3. **Test login from BOTH domains separately** — this is the actual proof
   `trustHost: true` is resolving the dual-domain scenario correctly, not
   an assumption. If one domain works and the other gets
   `redirect_uri_mismatch`, `trustHost` isn't resolving the Host header as
   expected — this needs further investigation (check for a hardcoded
   `AUTH_URL`/`NEXTAUTH_URL` env var overriding the dynamic behavior, and
   remove it if present).
4. Confirm the signed-in indicator (Step 4) actually shows the user's
   name — a clean redirect with no error is not proof a session exists.

---

## Optional: reduce to a single registered redirect URI (after POC deployment)

**Only relevant once the app is actually deployed to POC.** This
mechanism proxies the OAuth callback through the main/POC domain's real
`/api/auth` route, so that route must be live and reachable — skip this
during VIBER-only testing, where Step 2's dual-URI setup is the only
option that works.

Auth.js v5's `redirectProxyUrl` option lets TechPass register **only
the main/POC domain's** redirect URI, instead of both. Confirmed via
Auth.js's own docs (`authjs.dev`) — this is Auth.js-specific, not
available to `vibe-govauth`/`vibe-entraid`'s Better Auth stack, which has
no equivalent option; those skills' `getAuth(host)` factory is Better
Auth's own (different) workaround for the same dual-domain problem.

**How it works:** a sign-in started from the VIBER preview domain saves
that domain in the OAuth `state` parameter, but sets `redirect_uri` to
the stable main/POC domain. TechPass redirects back to main/POC,
Auth.js validates `state`, then redirects the browser back to the
actual VIBER preview domain. The main/POC domain is a real pass-through
in this flow, not just a placeholder — the round trip fails if it isn't
live and reachable.

**Setup:**
1. Remove the VIBER-session redirect URI from the TechPass app
   registration — keep only:
   `https://<main-domain>/api/auth/callback/microsoft-entra-id`
2. Set `AUTH_REDIRECT_PROXY_URL=https://<main-domain>/api/auth` in
   **Advanced → Env Vars**, with **"Also apply to POC deployment"
   checked** — Auth.js's docs are explicit that if this isn't also set
   in the stable environment, the proxy is silently disabled.
3. **`AUTH_SECRET` must be the identical value in both the VIBER session
   and the POC deployment.** The proxy's security relies entirely on
   both sides validating `state` with the same secret, not on domain
   matching. If POC already has its own independently-generated
   `AUTH_SECRET`, check "Also apply to POC deployment" when (re)setting
   it, or copy the POC value back into the VIBER session — don't leave
   the two to diverge.
4. Re-test login from the VIBER preview domain — confirm it completes
   the full round trip (redirected to main/POC, then back to the
   preview URL, signed in).

**Trade-off:** this trims the app registration to one redirect URI, at
the cost of a genuine runtime dependency on the main/POC domain being up
during every VIBER-session login. If POC is ever down, VIBER-session
login breaks too. The default dual-URI setup (Step 2) has no such
coupling — each domain authenticates independently. Only switch to this
if the user specifically wants fewer registered URIs; it is not a
strict improvement over the default.

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `Module not found: Can't resolve 'next-auth'` | next-auth not installed | Run `npm install next-auth@^5.0.0-0` before Step 4 |
| `MissingSecret` | `AUTH_SECRET` not reaching the container | Set in Advanced → Env Vars, not just locally |
| `redirect_uri_mismatch` on one domain only | `trustHost` not resolving that domain's Host header, or a hardcoded `AUTH_URL` overriding it | Remove any hardcoded `AUTH_URL`/`NEXTAUTH_URL`, confirm both URLs are registered in the app registration |
| `Invalid client_id` | Wrong TechPass credentials | User should re-check the Azure app registration |
| 404 on `/` | No root page redirect | Create `src/app/page.tsx`, or confirm one already exists |
| Auth works but middleware doesn't redirect | Custom middleware logic instead of the re-export pattern | Use `export { auth as middleware }`, handle redirects via Auth.js's own `authorized` callback if route protection is needed |

---

## Rules

- **Never write Better Auth / `genericOAuth` code here** — that's entirely
  `vibe-govauth`'s responsibility for the GovAuth-proxied path.
- **Stateless by default** — do not add a Prisma/database adapter unless
  Step 5 is explicitly requested.
- **Never add middleware that blocks all routes** by default — scaffold
  auth, let the user decide which pages to gate.
- **Never ask for secrets in chat** beyond the generated `AUTH_SECRET`
  (not a third-party credential, safe to display) — direct everything else
  to Advanced → Env Vars.
- After setup, run the `self-heal` skill to verify the build.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
