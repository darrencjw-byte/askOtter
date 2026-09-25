---
name: "vibe-govauth"
description: "Add WOG AD or TechPass OAuth authentication via GovAuth using Better Auth's genericOAuth plugin, for POC applications on the sandbox environment. Use when the user specifically mentions GovAuth, WOGAD, or TechPass, OR when directed here by setup-auth's routing. For a generic 'add login'/'add authentication'/'sign in' request that doesn't name a provider, setup-auth.md is the correct entry point instead — it decides GovAuth vs direct TechPass vs direct WOG AD vs direct Entra ID before this skill gets involved. Does NOT cover direct Microsoft Entra ID SSO — this is specifically the GovAuth-proxied flow with dual-domain (VIBER session + main/POC) support, always stateless (no database)."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: govauth-setup
---

# vibe-govauth

Handle GovAuth-proxied OAuth login (WOGAD or TechPass) for POC applications
on `govauth.sandbox.gov.sg`. This does not cover direct Microsoft Entra ID
SSO (not via GovAuth) — different credentials, different registration
flow, different redirect URI pattern. Do not conflate the two. Reached via
`setup-auth`'s routing, or directly when the user names GovAuth/WOGAD/
TechPass specifically.

## Important: POC only

GovAuth on `govauth.sandbox.gov.sg` is for proof-of-concept applications
only. It is NOT for production use. Make this clear to the user.

**If the user mentions this is for production, don't proceed with this
skill at all** — tell them plainly: GovAuth is sandbox/POC only, and
production requires bypassing the proxy entirely. Direct them to
`.claude/skills/vibe-techpass/SKILL.md` (production TechPass) or
`.claude/skills/vibe-wogad/SKILL.md` (production WOG AD) instead, whichever
identity provider they need — both use Auth.js/NextAuth with the
provider's own Azure app registration, a heavier one-time registration
process than GovAuth's proxy but production-capable.

## Identity provider default

- **WOGAD** (Microsoft Entra ID, proxied through GovAuth) — default, for
  most government apps where users are public officers across WOG.
- **TechPass** (GovTech identity) — only if the user specifically asks, or
  their users are GovTech staff/vendors.

GovAuth treats each as a SEPARATE Application — one Identity Provider choice
per Application, its own Client ID/Secret, its own pair of redirect URIs. If
the user wants both, repeat Step 2 twice with different provider IDs.

---

## Step 0 — Check whether this was already started before

If this skill has been invoked before in this project, it may have stopped
partway (e.g. env vars were confirmed but the actual code was never
written). Do NOT restart from Step 1 blindly — check first:

```bash
ls src/lib/auth.ts src/lib/auth-client.ts src/app/login/page.tsx 2>/dev/null
```

- **None exist**: this is a fresh start. Proceed to Step 1 normally.
- **Some exist but not all**: a previous run stopped mid-way. Tell the user
  plainly: *"It looks like GovAuth setup was started before but not
  finished — [list what exists/is missing]. I'll pick up from where it
  left off rather than starting over."* Then resume at whichever step
  matches what's missing (e.g. `auth.ts` exists but `login/page.tsx`
  doesn't → resume at Step 6, not Step 1).
- **All exist**: read `auth.ts` to confirm it's actually wired up correctly
  (has a real `getAuth` factory, not a stub) and tell the user GovAuth
  already appears to be set up. Offer to verify it (Step 7) rather than
  reconfiguring from scratch.

---

## Step 1 — Check what the user already has

Ask ONE question:

> "Do you already have a GovAuth Client ID and Secret for this app? If yes,
> tell me and I'll walk you through the redirect URIs. If not, I'll guide
> you through registration first."

**Stop here if they don't have credentials yet** — go to Step 2. Do not
write any auth code until credentials are confirmed.

---

## Step 2 — Registration walkthrough (if user doesn't have credentials yet)

**This app needs TWO redirect URIs, not one** — one for the live VIBER
session preview domain, one for the stable main/POC deployment domain.
Missing either means login silently fails with `invalid_redirect` in
whichever context wasn't registered.

Tell the user:

> "Before registering, get both domains — bare domain only, no path for
> either of these:
>
> 1. **VIBER session domain**: open your VIBER Studio session → Preview
>    pane → 'Open in new tab'. Copy that URL (e.g.
>    `https://s3037-yourapp.cio.sandbox.gov.sg`). This changes every time
>    you start a fresh VIBER session — re-check it, don't assume an old
>    value is still valid.
> 2. **Main/POC domain**: your product's stable domain in Rabbit Deploy
>    (e.g. `https://yourapp.cio.sandbox.gov.sg`) — stays the same across
>    sessions.
>
> Then:
> 3. Go to https://govauth.sandbox.gov.sg/applications/new
> 4. Sign in with TechPass or WOGAD
> 5. Click **New Application**
> 6. Fill in:
>    - **Application Name**: your project name
>    - **Identity Provider**: WOGAD (default) or TechPass
>    - **Redirect URIs** — add BOTH, with the exact path Better Auth
>      builds for the underlying `callback/:id` core route. This full path
>      is the ONE place it belongs — never in an env var:
>      - `https://<viber-session-domain>/api/auth/callback/wogad`
>      - `https://<main-domain>/api/auth/callback/wogad`
>      ❌ NOT `/api/auth/oauth2/callback/wogad` (this was the path in
>      better-auth <1.7 — the `genericOAuth` plugin dropped its own
>      dedicated endpoints in 1.7.0 and now routes through the same
>      `callback/:id` core endpoint `socialProviders` uses. This template
>      pins `better-auth` to an exact version specifically so this path
>      never drifts under you — see `package.json`.)
>      ❌ NOT `/api/govauth/callback/wogad` (wrong path entirely)
>      Use `techpass` instead of `wogad` in the path if that's the provider.
> 7. Click **Create Application**
> 8. Copy the **Client ID** and **Client Secret** immediately — the secret
>    is shown once and never again.
>
> Come back and tell me once you have both."

**Stop here.** Do not write any auth code until credentials are confirmed.

---

## Step 3 — Session storage: always stateless, no database

This skill never touches a database, checks for one, or invokes
`vibe-neondb` — it always sets up the **stateless config**. State this,
don't ask about it:

> "Setting up login without a database — this covers showing who's logged
> in, gating features by email/role, and audit trails."

If the app later needs to call a GovTech/Microsoft API using the
signed-in user's own access (their calendar, files, or another system
that trusts this login), that's a separate, later ask — handled by
whatever the user requests at that point, not something this skill
detects or forks on.

Explicitly set `storeAccountCookie: false`. Better Auth's own default when no database is
configured (`storeAccountCookie: true`) stores OAuth provider tokens in an
encrypted cookie; that cookie gets chunked to dodge the single-cookie 4KB
limit, but the *aggregate* across session + account cookies can still
exceed the browser/proxy's total header size limit — this produces `431
Request Header Fields Too Large`, consistently reproducible on a second
login attempt once the first attempt's cookies haven't fully cleared.
WOGAD (backed by Microsoft Entra ID) is exactly the kind of provider that
issues large tokens where this bites. **Do not leave `storeAccountCookie`
at its default when going database-less — this is a confirmed,
reproducible bug, not a hypothetical risk.**

A second, independent contributor to the same cookie-size problem:
WOGAD/Entra ID's userinfo response includes a full base64-encoded profile
photo in its picture claim. Better Auth's `genericOAuth` plugin maps this
straight into `User.image` by default, and in the stateless path that
whole user object gets JWE-encrypted into the session cookie on every
request. Confirmed by direct test: this alone was ~2.5KB of a ~3.3KB
session payload. See Step 5's `mapProfileToUser` note — fix this
regardless — it's wasteful either way (a database row doesn't need a
duplicate copy of the user's photo any more than a cookie does).

---

## Step 4 — Generate the secret, confirm domains

```bash
SECRET=$(openssl rand -base64 32) && echo "$SECRET"
```

Do not ask the user to generate this. **Always show the generated value**
so they can copy it into Env Vars — it's a signing key, not a third-party
credential, safe to display.

Confirm both domains are actually available (from Step 2):
```bash
echo "DOMAIN_URI_VIBER=${DOMAIN_URI_VIBER:+SET}"
echo "DOMAIN_URI_MAIN=${DOMAIN_URI_MAIN:+SET}"
```

Show the user ALL values to add in **Advanced → Env Vars** — bare domains
only, no path (the path is built in code, not stored in the env var):

| Variable | Value |
|---|---|
| `WOGAD_CLIENT_ID` | *(from GovAuth)* |
| `WOGAD_CLIENT_SECRET` | *(from GovAuth)* |
| `BETTER_AUTH_SECRET` | *(the value just generated — show it)* |
| `DOMAIN_URI_VIBER` | *(the VIBER session domain, bare, no path)* |
| `DOMAIN_URI_MAIN` | *(the main/POC domain, bare, no path)* |

(Swap `WOGAD_CLIENT_ID`/`SECRET` for `TECHPASS_CLIENT_ID`/`SECRET` if using
TechPass.) No separate `BETTER_AUTH_URL` variable is needed — the code
below reads `DOMAIN_URI_MAIN` directly wherever a single fallback URL is
required; maintaining a second, identical variable is redundant.

**State the total count explicitly:** "That's **5 env vars total** — the 5
above. No database or `DATABASE_URL` needed for this setup."

After the user confirms, verify:
```bash
echo "WOGAD_CLIENT_ID=${WOGAD_CLIENT_ID:+SET}" && echo "WOGAD_CLIENT_SECRET=${WOGAD_CLIENT_SECRET:+SET}" && echo "BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET:+SET}"
```
Don't proceed until all show `SET`.

Restart automatically — don't ask the user to do it:
```bash
supervisorctl restart dev-server && sleep 3
```

**DO NOT STOP HERE.** The moment the user confirms the env vars are added
(e.g. "done", "added", "ok") — in that SAME response, continue immediately
into Step 5, 6, and 7. Do NOT say "What would you like to build today?" or
treat listing the env vars as the end of the task. Confirming env vars is
not the goal — a working login button, wired-up auth code, and a passing
build (Step 7) are the goal. If you stop here, the user has 5-6 env vars
sitting in a container with no code actually using them, and no way to
tell that from the outside — this exact failure has happened before.

---

## Step 5 — Wire up Better Auth with a per-domain factory

**Do NOT use a single static `baseURL` string, and do NOT use a multi-host
`baseURL` object (`{ allowedHosts, fallback, ... }`) either — the object
form is CONFIRMED BROKEN.** Better Auth's `genericOAuth` plugin only
supports a static `redirectURI` string per provider, resolved once at
startup — it does not read the object form or resolve anything from the
incoming request's Host header. Using either approach means login only
works from whichever single domain matches what was set at startup; the
other domain fails with GovAuth's `invalid_redirect`, sometimes with the
`redirect_uri` shown as a bare relative path with no domain at all.

Instead, `src/lib/auth.ts` exports a **factory function** — a fresh Better
Auth instance is built per request, using a plain string `baseURL` that
matches whichever domain the request actually came from:

```typescript
import { betterAuth } from "better-auth"
import { genericOAuth } from "better-auth/plugins"

export function getAuth(requestHost: string) {
  const viberHost = process.env.DOMAIN_URI_VIBER
    ? new URL(process.env.DOMAIN_URI_VIBER).host
    : undefined
  const activeDomain =
    requestHost === viberHost
      ? process.env.DOMAIN_URI_VIBER
      : process.env.DOMAIN_URI_MAIN

  return betterAuth({
    baseURL: activeDomain, // plain string only — never the object form
    secret: process.env.BETTER_AUTH_SECRET,
    trustedOrigins: process.env.NODE_ENV === "development" ? ["*"] : [],

    advanced: {
      useSecureCookies: process.env.NODE_ENV === "production",
      defaultCookieAttributes: {
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        httpOnly: true,
      },
    },
    account: {
      accountLinking: { enabled: true, trustedProviders: ["wogad"] },
      storeAccountCookie: false,
    },
    plugins: [
      genericOAuth({
        config: [{
          providerId: "wogad",
          redirectURI: `${activeDomain}/api/auth/callback/wogad`,
          discoveryUrl: "https://govauth.sandbox.gov.sg/.well-known/openid-configuration",
          clientId: process.env.WOGAD_CLIENT_ID || "",
          clientSecret: process.env.WOGAD_CLIENT_SECRET || "",
          // "offline_access" requests a refresh token — only include it if
          // the app genuinely needs to call a GovTech/Entra API using the
          // user's own access after login (see Step 3). Requesting it
          // unconditionally makes the token larger for no reason, which
          // raises 431 risk if storeAccountCookie is ever re-enabled.
          scopes: ["openid", "profile", "email"],
          pkce: true,
          // WOGAD/Entra ID's userinfo response includes a full base64
          // profile photo. Confirmed via the installed better-auth source
          // (generic-oauth/index.mjs): the plugin builds the user object
          // with {...rawFields, ...mapped} — mapped is spread last, so it
          // wins — but the field must be explicitly set to undefined here,
          // not just omitted, or the raw profile's value survives the
          // merge untouched. Keep whichever other claims the app actually
          // needs (name, email, etc.) — adapt to what this provider's
          // userinfo response actually returns, don't assume exact field
          // names without checking. Re-verified this merge order still
          // holds as of better-auth 1.7.0's plugin rewrite — check again
          // if the pinned version in package.json ever changes.
          mapProfileToUser: (profile) => ({
            ...profile,
            image: undefined,
          }),
        }],
      }),
    ],
  })
}
```

**Key points:**
- `|| ""` for client id/secret, not `!` — a missing value should fail at
  sign-in with a clear error, not crash the build.
- `trustedOrigins: ["*"]` in development only — required for the VIBER
  preview pane to work; never in production.
- **`mapProfileToUser` excluding `image` is not optional polish** — without
  it, the session payload is ~5x larger than it needs to be (confirmed by
  direct test: ~3.3KB vs ~620 bytes) purely from a profile photo nothing in
  a typical POC app actually displays. Include it every time, not just when
  someone notices the cookie looks large.

**For TechPass** instead of WOGAD: `providerId: "techpass"`, env vars
`TECHPASS_CLIENT_ID`/`TECHPASS_CLIENT_SECRET`, `trustedProviders:
["techpass"]`. **For both providers**: add both to the `config` array and
both to `trustedProviders` — each provider's `redirectURI` still needs
`${activeDomain}` so both stay correct across both domains.

### 5b — Client (`src/lib/auth-client.ts`)

```typescript
"use client"

import { createAuthClient } from "better-auth/react"

export const authClient = createAuthClient({
  baseURL: typeof window !== "undefined" ? window.location.origin : (process.env.DOMAIN_URI_MAIN || "http://localhost:3001"),
})

export const { signIn, signOut, useSession } = authClient
```

**No client plugin needed as of better-auth 1.7.0.** Earlier versions
required importing `genericOAuthClient` from `better-auth/client/plugins`
— that plugin was removed entirely in 1.7.0's rewrite (confirmed: the
export no longer exists, importing it fails). `genericOAuth`-configured
providers now sign in through the same core `signIn.social` mechanism
`socialProviders` uses, with no separate client plugin required. If you
ever see this skill or old code reference `genericOAuthClient`, that's a
leftover from targeting an older better-auth version — remove it.
`window.location.origin` makes the client work on whichever domain it's
actually loaded from without hardcoding — this fixes the client-side API
routing concern; it does NOT by itself fix the server-side `redirect_uri`
problem, which is what the factory in 5a solves.

### 5c — API route (`src/app/api/auth/[...all]/route.ts`)

**Must read the Host header from the incoming request, not from
`req.url`.** `new URL(req.url).host` returns the internal request URL
(e.g. `0.0.0.0:3001`) in a server context — it is NOT the domain the
browser actually connected to. Using it silently breaks multi-domain
support: every request resolves to the same wrong domain regardless of
which one the user is actually on.

```typescript
import { getAuth } from "@/lib/auth"
import { toNextJsHandler } from "better-auth/next-js"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

async function handle(req: Request) {
  const host = req.headers.get("host") || new URL(req.url).host
  return toNextJsHandler(getAuth(host))[req.method === "POST" ? "POST" : "GET"](req)
}

export const GET = handle
export const POST = handle
```

Do NOT build a static `betterAuth()` instance at module scope and import it
here — it must be built inside `getAuth()` per request.

---

## Step 6 — Login page and signed-in indicator

Ask which provider(s) the user actually configured in GovAuth, and only
show matching button(s).

**Create a DEDICATED page at `/login`** (its own route/file, e.g.
`src/app/login/page.tsx`). Do NOT put the sign-in button on the homepage —
leave the homepage as whatever it already was. If `/login` already exists,
put the button there; don't duplicate it onto the homepage too.

```tsx
"use client"
import { signIn } from "@/lib/auth-client"

export default function LoginPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="text-base text-zinc-600">Sign in with your WOG AD account to continue.</p>
        </div>
        <button
          onClick={() => signIn.social({ provider: "wogad", callbackURL: "/" })}
          className="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-4 text-left hover:bg-zinc-50 transition-colors"
        >
          <div>
            <p className="text-base font-medium">Sign in with WOG AD</p>
            <p className="text-sm text-zinc-500">For all public officers</p>
          </div>
        </button>
      </div>
    </div>
  )
}
```

**Add an auth nav indicator** — a visible "Sign in" entry point when
logged out, and the only reliable way to confirm login actually worked
(without opening DevTools) once logged in:
- Use `useSession()` to read the current session and conditionally render.
- **`<sgds-masthead>` has NO slots and is not customisable** — you cannot
  insert anything into it, "inline in the masthead" is not an option in
  this template. If `src/app/layout.tsx` doesn't already render
  `<sgds-mainnav>`, add it now, positioned directly below
  `<sgds-masthead>` (required ordering — masthead must appear above
  mainnav). Place this component in mainnav's documented `end` slot — the
  canonical location for "login button... or similar" right-aligned
  actions per this template's own design system reference.
- Still do NOT use `position: fixed`/`position: absolute` for the
  component's own styling — use plain flex inside the `end` slot. The
  masthead's internal "How to identify" panel can expand, and its
  behavior isn't documented or under app control, so a fixed-position
  element pinned near the top risks overlapping it regardless of which
  component structure is in play.
- **Visibility is inherently scoped to this skill having actually run** —
  this component and the `<sgds-mainnav>` insertion only exist in the
  codebase because this step created them. An app that never invokes
  `vibe-govauth` never gets this code at all, so nothing appears in its
  mainnav. Don't add a separate feature-flag/env-var check for this — the
  code's own presence already is the "is GovAuth integration enabled"
  signal.
- If signed in: show the user's name/email and a "Sign Out" button. On
  click, sign out AND redirect to `/login` afterward — don't leave the
  user on whatever page they clicked Sign Out from.
- If NOT signed in: show a "Sign in" link/button to `/login` — don't
  render nothing. Without this, a real user has no way to discover the
  login page short of typing the URL directly.
- **Any OTHER nav link you add for a login-gated feature (e.g. a
  "Reports" link to a page that requires sign-in) should default to the
  same visibility rule as `AuthNav` itself — hidden when signed out, not
  "shown to everyone, the destination page redirects."** Confirmed wrong
  in a real session: a nav link to a guarded page was left visible to
  signed-out visitors on the first pass, and the user had to explicitly
  point out "without signin cannot see the link" (i.e. it shouldn't be
  visible) before it got fixed to check the session the same way
  `AuthNav` does. The destination page's own guard is still required as
  the real security boundary — this is about matching the nav link's
  visibility to it, not replacing it.

```tsx
// src/app/layout.tsx — add <sgds-mainnav> below <sgds-masthead> if not already present
<sgds-masthead fluid></sgds-masthead>
<sgds-mainnav>
  <div slot="end">
    <AuthNav />
  </div>
</sgds-mainnav>
<main className="flex-1">{children}</main>
```

```tsx
// src/components/auth-nav.tsx
"use client"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { authClient, useSession } from "@/lib/auth-client"

export function AuthNav() {
  const { data: session, isPending } = useSession()
  const router = useRouter()

  if (isPending) return null

  if (!session?.user) {
    return (
      <Link href="/login" className="text-sm font-medium">
        Sign in
      </Link>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm">{session.user.name || session.user.email}</span>
      <button onClick={async () => { await authClient.signOut(); router.push("/login") }}>
        Sign Out
      </button>
    </div>
  )
}
```

**Guarding an entire page** (e.g. "add a login-only reports page") —
check `isPending` first and render nothing/a skeleton while it resolves,
THEN check the session. Don't fetch or render the page's real content
until both checks have passed — fetching data before the session check
resolves risks a signed-out visitor briefly seeing a flash of the
content before a redirect fires. Prefer an inline "sign in required"
prompt over a `router.push` redirect from a `useEffect` — a redirect
still has to render *something* on the tick before it fires, whereas an
inline prompt never touches the protected data at all:

```tsx
// In a protected page — show content only once signed in, prompt if not
"use client"
import { useSession, authClient } from "@/lib/auth-client"

export default function ProtectedPage() {
  const { data: session, isPending } = useSession()

  if (isPending) return <Skeleton />

  if (!session?.user) {
    return (
      <Card className="mx-auto max-w-md p-6 mt-12 text-center space-y-3">
        <p className="text-sm font-medium">Sign in required</p>
        <p className="text-xs text-muted-foreground">
          Sign in to access this page.
        </p>
        <Button onClick={() => authClient.signIn.social({ provider: "wogad" })}>
          Sign in
        </Button>
      </Card>
    )
  }

  // Only reached once session is confirmed — safe to fetch/render real data here
  return <RealPageContent />
}
```

---

## Step 7 — Verify

Don't accept "no error shown" as proof — verify each of these explicitly:

1. Confirm the two callback URLs derived from `DOMAIN_URI_VIBER` and
   `DOMAIN_URI_MAIN` match exactly what's registered in GovAuth.
2. `SELF_HEAL_BUILD_CHECK=1 npm run build` — fix any code errors (the env var keeps this from colliding with the live dev server's own build output, see self-heal.md). If it fails on
   `_global-error`/`_not-found` with a React context crash unrelated to
   anything just written, check for a stray `NODE_ENV` value in the shell
   before assuming it's this auth code — see `vibe-neondb`'s build
   verification step for the full diagnosis; it's a general
   build-environment issue, not GovAuth-specific.
3. Test the actual redirect_uri per domain, not just "click and see":
   ```bash
   curl -s -H "Host: <domain>" "http://localhost:3001/api/auth/sign-in/social" \
     -X POST -H "Content-Type: application/json" \
     -d '{"provider":"wogad","callbackURL":"/"}' | grep -o 'redirect_uri=[^&]*'
   ```
   Decode the URL-encoded value and confirm it matches
   `<domain>/api/auth/callback/wogad` exactly, for BOTH domains. If
   only one matches, the route handler is very likely still reading
   `req.url` instead of the Host header (Step 5c) — this is the same check
   that caught that exact bug previously.
4. A successful redirect with no error page is NOT proof a session was
   created — confirm the signed-in indicator (Step 6) actually appears.
5. Test a SECOND login attempt specifically, not just the first. A 431
   error here means `storeAccountCookie: false` wasn't actually applied —
   check the config, don't assume it took effect.

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `invalid_redirect`, `redirect_uri` shown is a bare path with no domain | Used the multi-host `baseURL` object form | Switch to the per-request factory (Step 5) |
| `invalid_redirect`, works from one domain but not the other | Route handler reads `req.url` instead of the Host header | Fix Step 5c |
| `431 Request Header Fields Too Large`, works once then breaks on retry | Default `storeAccountCookie: true` accumulating token cookies | Set `storeAccountCookie: false` (Step 3) |
| `invalid_client` | Wrong Client ID/Secret | User should re-check the GovAuth application page |
| Callback `404` | `src/app/api/auth/[...all]/route.ts` missing | Create it (Step 5c) |
| `BETTER_AUTH_SECRET is required` | Missing env var | Add in Advanced → Env Vars |
| Discovery URL fails | Check the URL is `https://govauth.sandbox.gov.sg/.well-known/openid-configuration` exactly (no trailing slash) | |
| Session/cookie payload much larger than expected (KBs, not hundreds of bytes) | OAuth profile claim includes a full base64 photo, mapped into `User.image` by default | Add `mapProfileToUser` excluding `image` (Step 5) |

---

## Rules

- **This is POC only** — GovAuth sandbox is not for production, remind the
  user.
- **Never ask for secrets in chat** — direct to Advanced → Env Vars. The
  generated `BETTER_AUTH_SECRET` is the one exception (not a third-party
  credential, safe to display).
- **Do not enforce auth on all pages by default** — scaffold the sign-in
  button and login page; let the user decide which pages to gate.
- **`DOMAIN_URI_MAIN`/`DOMAIN_URI_VIBER` are bare domains, no path** — the
  `/api/auth/callback/<providerId>` path is built in code, never
  stored in the env var. The full path only ever belongs in GovAuth's own
  Redirect URI field.
- **`better-auth` and `@better-auth/prisma-adapter` are pinned to an exact
  version in `package.json` (currently `1.7.0`), not a `^` range** — the
  `genericOAuth` plugin's endpoint paths changed between 1.6.x and 1.7.0
  (dropped its own `/oauth2/...` endpoints, moved to the shared
  `callback/:id` core route). Every path and client call in this skill is
  written against the pinned version. If that pin is ever bumped, re-verify
  this entire skill against the new version's actual installed source
  before trusting it — don't assume the paths carried over unchanged.
- **Don't skip Step 3's `storeAccountCookie: false`** — leaving it at
  Better Auth's default is a confirmed, reproducible 431 bug, not a
  theoretical risk.
- **Never invoke `vibe-neondb`, check `DATABASE_URL`, or write any Prisma
  code from this skill** — GovAuth setup is always stateless. If the user
  separately asks to add a database, that's a distinct request `CLAUDE.md`
  routes to `setup-db` (which in turn delegates to `vibe-neondb`) on its
  own; this skill has no part in that decision.
- After setup, run the `self-heal` skill to verify the build.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
