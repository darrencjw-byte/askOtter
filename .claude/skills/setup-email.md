---
name: "setup-email"
description: "Main-category router for email sending. Use when the user asks to send email, add email, email notification, OTP email, send receipt, or transactional email. Confirms which provider to use — Postman (postman.gov.sg, the gov-standard default), AWS SES, Resend, or SMTP — then delegates to vibe-postman/vibe-awsses/vibe-resend/vibe-smtp accordingly. Does not implement anything itself — always delegates."
metadata:
  author: viber-studio
  version: "3.0.0"
  audience: internal
  category: setup
  routes_to: vibe-postman, vibe-awsses, vibe-resend, vibe-smtp
---

# setup-email — Email setup router

This is the entry point for any email-sending request. Its only job is to
determine which provider applies, then delegate. **Never write email code
here** — every specific implementation belongs entirely to the skill it's
delegated to.

---

## Step 1 — Determine which provider

**If the request already names a provider, skip straight to the matching
step — don't ask:**
- Mentions Postman, postman.gov.sg, or just "email"/"send email"/"OTP
  email"/"send receipt" with no provider named → Step 2A. **Postman is
  the default — every generic request resolves here.**
- Explicitly says "AWS SES", "use SES", "AWS email", already has AWS
  credentials configured, or says their agency lacks Postman access →
  Step 2B.
- Explicitly says "Resend" → Step 2C.
- Explicitly says "SMTP", or names a specific SMTP-fronted provider
  (Mailgun, SendGrid via SMTP) → Step 2D.

**If the request names a provider that isn't any of the above** (e.g.
SendGrid's own API, Mailgun's own API, Brevo) — **implement what the user
actually asked for.** This router's job is to provide sensible defaults
and guidance for a *generic* request, not to gatekeep which providers
exist. Use general best-practice knowledge for that provider rather than
forcing the user toward Postman/SES/Resend/SMTP just because those are
the ones with dedicated skills here. Mention briefly that Postman is the
gov-standard default if the user seems undecided, but don't block a
specific, explicit request.

Every named-provider case above — listed or not — resolves to a step or
to "implement what was asked." There is no remaining case that needs a
clarifying question.

---

## Step 2A — Postman: hand off to vibe-postman

Read `.claude/skills/vibe-postman/SKILL.md` and follow it from its own
Step 0 onward. That skill owns the entire flow — API key check,
onboarding guidance, the email utility, API route, and end-to-end
verification.

One thing worth telling the user before handing off, since it's easy to
miss: as of September 2023, Postman halted new programmatic email API
onboarding — this only works for teams that already have API access. If
the user cannot log in or generate a key, they need their agency's
existing Postman admin, not a new signup.

---

## Step 2B — AWS SES: hand off to vibe-awsses

Read `.claude/skills/vibe-awsses/SKILL.md` and follow it from its own
Step 0 onward.

---

## Step 2C — Resend: hand off to vibe-resend

Read `.claude/skills/vibe-resend/SKILL.md` and follow it from its own
Step 0 onward.

---

## Step 2D — SMTP: hand off to vibe-smtp

Read `.claude/skills/vibe-smtp/SKILL.md` and follow it from its own
Step 0 onward.

---

## Rules

- **Never write Postman, AWS SES, Resend, or SMTP code here** — every
  implementation belongs entirely to the skill it's delegated to.
- **Postman is the default** — don't suggest AWS SES, Resend, or SMTP
  unless the conditions in Step 1 are actually met.
- **Don't conflate the four solutions** — different credentials,
  different registration flows, different libraries in some cases.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
