---
name: "vibe-wogad"
description: "Add direct WOG AD (Whole-of-Government Active Directory) SSO — production-grade, not via GovAuth's sandbox proxy — using Auth.js v5 (NextAuth) with a dedicated Azure AD provider. Use when the user specifically names WOG AD as a direct/production connection (not through GovAuth), OR when directed here by setup-auth's routing, OR when vibe-govauth's POC-only limitation is the reason they need this. For a generic 'add login' request, setup-auth.md is the correct entry point instead. Always stateless by default (JWT session, no database) — a persistent DB-backed user profile is an optional addition, not a prerequisite."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: techpass-wogad-authentication (WOG AD portion only)
---

# vibe-wogad

Direct WOG AD SSO — connects straight to the Whole-of-Government Active
Directory's own Azure AD tenant via Auth.js v5, without GovAuth's proxy.
**This is the production path** — `vibe-govauth`'s GovAuth-proxied WOG AD
option is sandbox/POC-only; this skill is what a user needs once they're
actually deploying to production. Different library than `vibe-govauth`
(NextAuth, not Better Auth) and a different registration flow than
`vibe-techpass` (separate Azure app registration, separate tenant) — do
not conflate the three, and do not mix Better Auth code into this skill.

---

## Important: this is the production path, confirm that's actually needed

Direct WOG AD requires the user's own Azure app registration within the
WOG AD tenant — a heavier registration process than GovAuth's proxy.
Confirm with the user this is genuinely what they want:
- **Still in POC/testing?** `vibe-govauth` (GovAuth-proxied) is simpler —
  one Application, no separate Azure app registration. Suggest that
  first unless the user has explicitly said this is for production.
- **Actually deploying to production?** GovAuth is sandbox-only — this
  skill (or `vibe-techpass` for TechPass) is the correct path.

---

## Step 0 — Check whether this was already started before

```bash
ls src/lib/auth.ts src/app/api/auth/[...nextauth]/route.ts src/app/login/page.tsx 2>/dev/null
```

- **None exist**: fresh start, proceed to Step 1.
- **Some exist but not all**: resume at the matching step, don't restart.
- **All exist**: check whether `src/lib/auth.ts` already uses
  `next-auth/providers/microsoft-entra-id` with `id: "azure-ad"` and a WOG AD tenant
  (this skill) vs TechPass (`vibe-techpass`), Better Auth (`vibe-entraid`/`vibe-govauth`)
  — don't overwrite a different, working auth setup without confirming
  with the user first.

---

## Step 1 — Check what the user already has

Ask ONE question:

> "Do you already have a WOG AD Azure app registration (Client ID, Tenant
> ID, Client Secret)? If yes, tell me and I'll walk you through the
> redirect URLs. If not, I'll guide you through registration first — note
> this typically requires your agency's IT/Azure admin, since WOG AD app
> registrations aren't self-service the way GovAuth's sandbox is."

**Stop here if they don't have credentials yet** — go to Step 2.

---

## Step 2 — Registration walkthrough (if user doesn't have credentials yet)

**This app needs TWO redirect URLs registered, not one** — the live VIBER
session preview domain and the stable main/POC domain (or, for a genuine
production deployment, the actual production domain — confirm which
domains are actually relevant with the user, since production WOG AD
apps typically don't run inside a VIBER session at all).

Tell the user:

> "In your WOG AD Azure app registration:
>
> 1. Add BOTH redirect URLs, using the exact path Auth.js builds — one
>    domain registered is not enough, this app runs on two:
>    - `https://<viber-session-domain>/api/auth/callback/azure-ad`
>    - `https://<main-domain>/api/auth/callback/azure-ad`
> 2. Add a logout URL for each domain: `https://<domain>/api/auth/signout` (Auth.js v5's catch-all route has no `logout` action — the valid one is `signout`)
> 3. Request the scopes: `openid profile email User.Read`
> 4. Generate a Client Secret under Certificates & Secrets.
> 5. Copy the Client ID, Tenant ID, and Client Secret.
>
> Come back and tell me once you have all three. This typically goes
> through your agency's Azure/IT admin, not a self-service portal."

**Stop here.** Do not write any auth code until credentials are confirmed.

---

## Step 3 — Generate the secret, set env vars

```bash
SECRET=$(openssl rand -base64 33) && echo "$SECRET"
```

Show the user ALL values to add in **Advanced → Env Vars**:

| Variable | Value |
|---|---|
| `AUTH_SECRET` | *(the value just generated — show it)* |
| `WOGAD_DIRECT_CLIENT_ID` | *(Client ID from Step 2)* |
| `WOGAD_DIRECT_CLIENT_SECRET` | *(Client Secret from Step 2)* |
| `WOGAD_TENANT_ID` | *(Tenant ID from Step 2)* |

That's **4 env vars total**. No `DATABASE_URL` needed for this setup.

After the user confirms, verify:
```bash
echo "AUTH_SECRET=${AUTH_SECRET:+SET}" && echo "WOGAD_DIRECT_CLIENT_ID=${WOGAD_DIRECT_CLIENT_ID:+SET}" && echo "WOGAD_DIRECT_CLIENT_SECRET=${WOGAD_DIRECT_CLIENT_SECRET:+SET}" && echo "WOGAD_TENANT_ID=${WOGAD_TENANT_ID:+SET}"
```
Don't proceed until all show `SET`.

Restart automatically:
```bash
supervisorctl restart dev-server && sleep 3
```

**DO NOT STOP HERE.** Continue immediately into Step 4-6 in the same
response.

---

## Step 4 — Install next-auth and wire up Auth.js (stateless, no database)

Install next-auth if not already present:

```bash
npm install next-auth@^5.0.0-0
```

Same `trustHost: true` mechanism as `vibe-techpass` — resolves the
callback domain from the incoming request's Host header rather than a
single hardcoded value. **Not yet empirically verified against the
dual-domain redirect scenario within this project** — Step 6's test
confirms it, don't assume it works from `trustHost` alone.

`src/lib/auth.ts`:

```typescript
import NextAuth from "next-auth";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  providers: [
    MicrosoftEntraId({
      id: "azure-ad",
      name: "WOG AD",
      clientId: process.env.WOGAD_DIRECT_CLIENT_ID!,
      clientSecret: process.env.WOGAD_DIRECT_CLIENT_SECRET!,
      issuer: `https://login.microsoftonline.com/${process.env.WOGAD_TENANT_ID}/v2.0`,
      authorization: { params: { scope: "openid profile email User.Read" } },
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

`middleware.ts` — re-export pattern:

```typescript
export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/auth).*)"],
};
```

Root layout — add `SessionProvider` around `{children}` inside `<main>` only. **Do NOT replace the whole layout** — keep `SgdsProvider`, `<sgds-masthead>`, `<sgds-footer>`, and `<Toaster>` untouched. See `vibe-techpass`'s Step 4 for the exact diff pattern.

Login page (`src/app/login/page.tsx`):

```tsx
"use client"
import { signIn } from "next-auth/react"

export default function LoginPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="text-base text-zinc-600">Sign in with WOG AD to continue.</p>
        </div>
        <button
          onClick={() => signIn("azure-ad", { callbackUrl: "/" })}
          className="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-4 text-left hover:bg-zinc-50 transition-colors"
        >
          <p className="text-base font-medium">Sign in with WOG AD</p>
        </button>
      </div>
    </div>
  )
}
```

Signed-in indicator — same `AuthNav` pattern as `vibe-techpass`'s Step 4
(same `<sgds-mainnav>` placement rules). Same rules apply for any OTHER
nav link to a login-gated feature (hide it when signed out, don't rely
on the destination page alone) and for guarding an entire page's content
(check `status === "loading"` then session before rendering/fetching
anything) — see `vibe-techpass`'s Step 4 for both patterns, just swap
the `signIn("techpass")` call for this provider's own sign-in trigger.

**Two claim-parsing gotchas confirmed from a real production WOG AD
integration, worth carrying forward even in the stateless default:**
- Entra sometimes omits `profile.email` — always also check
  `profile.userPrincipalName` as a fallback when reading the signed-in
  user's email from the session.
- WOG AD delivers `userPrincipalName` in Active Directory account casing
  (e.g. `Patrick_Ng@tech.gov.sg`) — normalize to lowercase before using
  it as a lookup key anywhere (comparisons, display, or a future
  DB-backed profile in Step 5).

---

## Step 5 — Optional: persistent DB-backed user profile

Only do this if the user explicitly asks for it (e.g. "remember user
roles", "auto-register users on first login", "track division/department
by email domain"). Do not add this by default.

If requested: hand off to `.claude/skills/setup-db.md` first, then add a
`signIn`/`jwt` callback that upserts into a `User`/`Account` table via
Prisma — remembering the email-casing and `userPrincipalName` fallback
gotchas above when doing the lookup. This is a genuinely different
config, not a small addition — treat it as its own step with the user's
explicit confirmation before writing it.

---

## Step 6 — Verify

1. `SELF_HEAL_BUILD_CHECK=1 npm run build` — fix any errors (the env var keeps this from colliding with the live dev server's own build output, see self-heal.md). If it fails on `_global-error`/`_not-found` with a React context crash unrelated to anything just written, check for a stray `NODE_ENV` value in the shell before assuming it's this auth code — see `vibe-neondb`'s build verification step for the full diagnosis; it's a general build-environment issue, not WOG AD-specific.
2. Confirm the callback URL is registered exactly as shown in Step 2.
3. **Test login from every domain this app is actually served on** — the
   real proof `trustHost: true` resolves correctly, not an assumption. If
   one domain works and another gets `redirect_uri_mismatch`, `trustHost`
   isn't resolving that Host header — check for a hardcoded
   `AUTH_URL`/`NEXTAUTH_URL` env var overriding the dynamic behavior.
4. Confirm the signed-in indicator actually shows the user's name.

---

## Optional: reduce to a single registered redirect URI (after deployment)

**Only relevant once the app is actually deployed** (POC or production —
whichever stable domain the user settled on in Step 2). This mechanism
proxies the OAuth callback through that stable domain's real
`/api/auth` route, so that route must be live and reachable — skip this
while only running inside a VIBER session with no deployed counterpart
yet, where Step 2's dual-URI setup is the only option that works.

Auth.js v5's `redirectProxyUrl` option lets WOG AD register **only the
stable domain's** redirect URI, instead of both. Confirmed via Auth.js's
own docs (`authjs.dev`) — this is Auth.js-specific, not available to
`vibe-govauth`/`vibe-entraid`'s Better Auth stack, which has no
equivalent option; those skills' `getAuth(host)` factory is Better
Auth's own (different) workaround for the same dual-domain problem.

**How it works:** a sign-in started from the VIBER preview (or other
non-stable) domain saves that domain in the OAuth `state` parameter, but
sets `redirect_uri` to the stable domain. WOG AD redirects back to the
stable domain, Auth.js validates `state`, then redirects the browser
back to the actual originating domain. The stable domain is a real
pass-through in this flow, not just a placeholder — the round trip fails
if it isn't live and reachable.

**Setup:**
1. Remove the non-stable redirect URI from the WOG AD app registration —
   keep only: `https://<stable-domain>/api/auth/callback/azure-ad`
2. Set `AUTH_REDIRECT_PROXY_URL=https://<stable-domain>/api/auth` in
   **Advanced → Env Vars**, applied to every environment this app runs
   in — Auth.js's docs are explicit that if this isn't also set in the
   stable environment, the proxy is silently disabled.
3. **`AUTH_SECRET` must be the identical value in every environment.**
   The proxy's security relies entirely on all sides validating `state`
   with the same secret, not on domain matching. Don't let a
   separately-provisioned deployment generate its own independent
   `AUTH_SECRET` — copy the same value across, or explicitly sync it.
4. Re-test login from the non-stable domain — confirm it completes the
   full round trip (redirected to the stable domain, then back, signed
   in).

**Trade-off:** this trims the app registration to one redirect URI, at
the cost of a genuine runtime dependency on the stable domain being up
during every login from elsewhere. The default dual-URI setup (Step 2)
has no such coupling — each domain authenticates independently. Only
switch to this if the user specifically wants fewer registered URIs; it
is not a strict improvement over the default — and for a genuine
production WOG AD deployment with no VIBER-session domain in the
picture at all, there may be nothing to reduce in the first place.

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `Module not found: Can't resolve 'next-auth'` | next-auth not installed | Run `npm install next-auth@^5.0.0-0` before Step 4 |
| `MissingSecret` | `AUTH_SECRET` not reaching the container | Set in Advanced → Env Vars |
| `redirect_uri_mismatch` on one domain only | `trustHost` not resolving that domain's Host header, or a hardcoded `AUTH_URL` overriding it | Remove any hardcoded `AUTH_URL`/`NEXTAUTH_URL`, confirm the URL is registered |
| `Invalid client_id` | Wrong WOG AD credentials | User should re-check the Azure app registration with their agency admin |
| Session missing email | Entra omitted `profile.email` | Fall back to `profile.userPrincipalName` |
| Duplicate users / failed lookups (if Step 5 added) | Email casing mismatch (`userPrincipalName` in AD casing) | Always normalize email to lowercase before any DB lookup |

---

## Rules

- **Never write GovAuth/Better Auth code here** — that's entirely
  `vibe-govauth`'s responsibility for the sandbox/POC path.
- **Never write TechPass provider config here** — that's `vibe-techpass`.
- **Stateless by default** — do not add a Prisma/database adapter unless
  Step 5 is explicitly requested.
- **This is the production path — confirm that's actually needed** before
  walking the user through a heavier registration process than GovAuth's.
- **Never add middleware that blocks all routes** by default.
- Always normalize email casing before any lookup — WOG AD delivers
  Active Directory casing, not lowercase.
- After setup, run the `self-heal` skill to verify the build.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
