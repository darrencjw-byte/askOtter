---
name: "setup-auth"
description: "Main-category router for authentication/login setup. Use when the user asks to add login, sign-in, authentication, SSO, or protected routes. Confirms which auth solution to use — GovAuth (WOG AD/TechPass proxied, sandbox/POC only, no database), direct TechPass (production, no database), direct WOG AD (production, no database), or direct Microsoft Entra ID SSO for another org's own tenant (needs a database) — then delegates to vibe-govauth, vibe-techpass, vibe-wogad, or vibe-entraid accordingly. Does not implement anything itself — always delegates."
metadata:
  author: viber-studio
  version: "4.0.0"
  audience: internal
  category: setup
  routes_to: vibe-govauth, vibe-techpass, vibe-wogad, vibe-entraid
---

# setup-auth — Authentication setup router

This is the entry point for any auth/login request. Its only job is to
determine which of the four supported auth solutions applies, then
delegate. **Never write auth code here** — every specific implementation
belongs entirely to the skill it's delegated to.

---

## Step 1 — Determine which solution

**If the request already names a solution, skip straight to the matching
step — don't ask:**
- Mentions GovAuth, WOG AD, or WOGAD, or TechPass without saying "direct"
  or "production" → Step 2A (GovAuth-proxied is the default for these —
  it's sandbox/POC only, see the note below).
- Explicitly says "direct TechPass", "TechPass without GovAuth", or
  "TechPass in production" → Step 2B.
- Explicitly says "direct WOG AD", "WOG AD without GovAuth", or "WOG AD in
  production" → Step 2C.
- Explicitly says "direct Microsoft Entra ID", "Azure AD SSO", or
  similarly names an organisation's own SEPARATE Entra ID app
  registration (not WOG AD, not TechPass — a genuinely different tenant,
  e.g. the agency's own independent Azure setup) → Step 2D.

**If GovAuth was chosen but the user mentions this is for production**,
stop and redirect: GovAuth (`govauth.sandbox.gov.sg`) is sandbox/POC only,
never production. Go to Step 2B (TechPass) or Step 2C (WOG AD) instead,
whichever identity provider they need.

**If the request names a provider that isn't any of the above** (e.g.
Google login, Okta, Auth0, plain email/password) — **implement what the
user actually asked for.** This router's job is to provide sensible
defaults and guidance for a *generic* request, not to gatekeep which
providers exist. Use general best-practice knowledge for that provider
rather than forcing the user toward one of the four just because those
are the ones with dedicated skills here. Mention briefly that GovAuth is
the gov-standard default for POC if the user seems undecided, but don't
block a specific, explicit request.

**If the request is generic** ("add login", "I need auth", "add SSO",
"protect this page") with no solution named, ask ONE question:

> "For Singapore government POC apps, I'd recommend **GovAuth** (WOG AD or
> TechPass) as the default — it's the standard sandbox auth proxy and
> doesn't need a database. Note GovAuth is sandbox/POC only — if this is
> for production, you'll need direct TechPass or direct WOG AD instead
> (heavier registration, but production-capable). Which would you like?"

Default to GovAuth if the user has no strong preference and hasn't
mentioned production — simplest (no database, no separate app
registration of your own) and the gov-standard path for POC apps.

---

## Step 2A — GovAuth (sandbox/POC only): hand off to vibe-govauth

Read `.claude/skills/vibe-govauth/SKILL.md` and follow it from its own
Step 0 onward. Covers WOG AD and TechPass, both proxied through GovAuth.
Always stateless, no database. **Not for production** — `vibe-govauth`
itself reminds the user of this, but confirm it's actually appropriate
before starting if the user's request hints at a production deployment.

---

## Step 2B — Direct TechPass (production): hand off to vibe-techpass

Read `.claude/skills/vibe-techpass/SKILL.md` and follow it from its own
Step 0 onward. Uses Auth.js/NextAuth, not Better Auth — a different
library and registration flow than GovAuth's TechPass option. Stateless
by default, no database. This is the production path for TechPass —
heavier registration than GovAuth's proxy (typically needs the agency's
own TechPass admin), confirm that's genuinely needed before starting.

---

## Step 2C — Direct WOG AD (production): hand off to vibe-wogad

Read `.claude/skills/vibe-wogad/SKILL.md` and follow it from its own
Step 0 onward. Uses Auth.js/NextAuth, same library as `vibe-techpass` but
a separate Azure app registration and tenant. Stateless by default, no
database. This is the production path for WOG AD — heavier registration
than GovAuth's proxy (typically needs the agency's own Azure/IT admin),
confirm that's genuinely needed before starting.

---

## Step 2D — Direct Microsoft Entra ID, other tenant: hand off to vibe-entraid

Read `.claude/skills/vibe-entraid/SKILL.md` and follow it from its own
Step 0 onward. For an organisation's own SEPARATE Entra ID app
registration — not WOG AD (that's `vibe-wogad`), not TechPass (that's
`vibe-techpass`). This path always needs a database; `vibe-entraid`
handles requesting that itself, do not check `DATABASE_URL` here.

---

## Rules

- **Never write GovAuth, Auth.js/NextAuth, or Better-Auth-Entra-ID code
  here** — every implementation belongs entirely to the skill it's
  delegated to.
- **Do not conflate the four solutions** — different credentials,
  different registration flows, and in most cases different libraries
  entirely (Better Auth for `vibe-govauth`/`vibe-entraid`, Auth.js for
  `vibe-techpass`/`vibe-wogad`).
- **GovAuth is never the answer for a production deployment** — catch
  this in Step 1, don't let it reach `vibe-govauth` only for that skill
  to have to say no.
- If the user separately asks to add a database, that's a distinct
  request `CLAUDE.md` routes to `setup-db` on its own — this router has no
  part in that decision except where `vibe-entraid` explicitly needs one.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
