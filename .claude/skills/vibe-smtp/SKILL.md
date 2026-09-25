---
name: "vibe-smtp"
description: "Send transactional email via a custom SMTP server or relay (own mail server, Mailgun/SendGrid SMTP bridge) using nodemailer. Use when the user specifically names SMTP, or a specific SMTP-fronted provider (Mailgun, SendGrid via SMTP), OR when directed here by setup-email's routing. For a generic 'send email'/'add email' request, setup-email.md is the correct entry point instead — Postman is the gov-standard default there. Not gov-approved as a default; use only on explicit request."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: email-setup-smtp
---

# vibe-smtp

Transactional email via a custom SMTP server or relay, using nodemailer.
Not the gov default (that's `vibe-postman`) — confirm with the user this
is actually what they want. No hosted-provider account needed — credentials
come from whatever mail server/relay the user already has.

---

## Step 0 — Check credentials

```bash
echo "SMTP_HOST=${SMTP_HOST:+SET}" && echo "SMTP_PORT=${SMTP_PORT:+SET}" && echo "SMTP_USERNAME=${SMTP_USERNAME:+SET}" && echo "SMTP_PASSWORD=${SMTP_PASSWORD:+SET}"
```

- If all SET → skip to Step 2.
- If NOT set → Step 1.

---

## Step 1 — Ask for SMTP details

> "To send emails via SMTP, I need your mail server's connection details —
> host, port, username, and password (from your own mail server, or a
> provider that exposes SMTP like Mailgun or SendGrid's SMTP bridge). Some
> providers require an app-specific password instead of your normal
> login (e.g. Gmail with 2FA enabled).
>
> Come back once you have these."

**Stop here.** Do not write any email code until the user confirms.

---

## Step 2 — Add credentials to environment

| Variable | Value |
|----------|-------|
| `SMTP_HOST` | *(e.g. `mail.yourdomain.com`)* |
| `SMTP_PORT` | *(587 recommended — see port reference below)* |
| `SMTP_USERNAME` | *(from Step 1)* |
| `SMTP_PASSWORD` | *(from Step 1)* |
| `SMTP_FROM_ADDRESS` | *(e.g. `noreply@yourdomain.com`)* |
| `SMTP_FROM_NAME` | *(your app name — optional)* |

**Port reference:**

| Port | Mode | When to use |
|------|------|-------------|
| 25 | Plain | Legacy, often blocked by ISPs |
| 465 | SSL/TLS | Older SSL — set `secure: true` |
| 587 | STARTTLS | Recommended for most providers |
| 2525 | STARTTLS | Fallback if 587 is blocked |

After the user confirms, verify:
```bash
echo "SMTP_HOST=${SMTP_HOST:+SET}" && echo "SMTP_PORT=${SMTP_PORT:+SET}" && echo "SMTP_USERNAME=${SMTP_USERNAME:+SET}" && echo "SMTP_PASSWORD=${SMTP_PASSWORD:+SET}"
```
Don't proceed until all show `SET`.

Restart automatically:
```bash
supervisorctl restart dev-server && sleep 3
```

---

## Step 3 — Install nodemailer

```bash
npm install nodemailer
```

---

## Step 4 — Create the email utility

Create `src/lib/smtp-email.ts`:

```typescript
import nodemailer from "nodemailer";

interface SendEmailParams {
  to: string;
  subject: string;
  html: string;
}

export async function sendEmail({ to, subject, html }: SendEmailParams) {
  if (!process.env.SMTP_HOST || !process.env.SMTP_USERNAME || !process.env.SMTP_PASSWORD) {
    throw new Error("SMTP credentials not set. Add SMTP_HOST/USERNAME/PASSWORD in Env Vars.");
  }

  const port = parseInt(process.env.SMTP_PORT || "587");
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port,
    secure: port === 465,
    auth: {
      user: process.env.SMTP_USERNAME,
      pass: process.env.SMTP_PASSWORD,
    },
    tls: { rejectUnauthorized: process.env.NODE_ENV === "production" },
  });

  const fromName = process.env.SMTP_FROM_NAME || "";
  const fromAddress = process.env.SMTP_FROM_ADDRESS || process.env.SMTP_USERNAME;
  const from = fromName ? `"${fromName}" <${fromAddress}>` : fromAddress;

  await transporter.sendMail({ from, to, subject, html });
}
```

**Key points:**
- Server-side only — never import in client components
- Port 465 uses `secure: true`; ports 587/2525 use STARTTLS (nodemailer
  handles the upgrade automatically)
- `rejectUnauthorized: false` behavior only applies outside production —
  never disable certificate checking in production

---

## Step 5 — Create Next.js API route

Create `src/app/api/email/send/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/smtp-email";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (!body.to || !body.subject || !body.html) {
      return NextResponse.json(
        { error: "Missing required fields: to, subject, html" },
        { status: 400 }
      );
    }

    await sendEmail({ to: body.to, subject: body.subject, html: body.html });
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to send email";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
```

---

## Step 6 — Verify end-to-end

```bash
curl -X POST http://localhost:3001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@tech.gov.sg","subject":"Test from POC","html":"<p>Hello from my POC app!</p>"}'
```

Expected: `{"success":true}`

**If the actual send route is guarded by a login check**, the curl above
will only ever hit the 401/redirect — it never reaches the real SMTP
call, so confirming the guard rejects unauthenticated requests is NOT the
same as confirming email sending actually works. Test the underlying
function directly, bypassing the HTTP route and its auth guard entirely:

```bash
npx tsx -e "
import { sendEmail } from './src/lib/smtp-email';
sendEmail({ to: 'your-email@tech.gov.sg', subject: 'Test', html: '<p>Test</p>' })
  .then(r => console.log('OK', r))
  .catch(e => console.error('FAILED', e));
"
```

---

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| Mail bounces / marked as spam | From address not authorised by SPF/DKIM on the SMTP server | Confirm the sending domain's SPF/DKIM covers this from address |
| Auth failure | Provider requires an app-specific password | Generate one instead of using the normal account password (e.g. Gmail with 2FA) |
| Connection refused | Wrong port for the server's expected mode | Check port reference above — 465 needs `secure: true`, 587/2525 use STARTTLS |
| Works in dev, fails in production | `rejectUnauthorized: false` left on, or a cert issue only checked in prod | Never disable certificate checking outside dev |

---

## Rules

- **Server-side only** — never call the SMTP transport from client
  components.
- **Never log/echo `SMTP_PASSWORD`** — only confirm it's SET.
- Confirm with the user this is genuinely what they want — Postman is the
  gov default for a reason; SMTP is for when they have their own mail
  server/relay to use.
- After setup, run the `self-heal` skill to verify the build passes.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
