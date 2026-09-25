---
name: "vibe-resend"
description: "Send transactional email via Resend (resend.com), a developer-focused email API. Use when the user specifically names Resend, OR when directed here by setup-email's routing. For a generic 'send email'/'add email' request, setup-email.md is the correct entry point instead — Postman is the gov-standard default there. Not gov-approved as a default; use only on explicit request."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
  supersedes: email-setup-resend
---

# vibe-resend

Transactional email via Resend, for POC applications where the user has
specifically asked for it. No SDK needed — uses plain `fetch`. Not the
gov default (that's `vibe-postman`) — confirm with the user this is
actually what they want before implementing.

---

## Step 0 — Check credentials

```bash
echo "RESEND_API_KEY=${RESEND_API_KEY:+SET}" && echo "RESEND_FROM_ADDRESS=${RESEND_FROM_ADDRESS:+SET}"
```

- If both SET → skip to Step 2.
- If NOT set → Step 1.

---

## Step 1 — Guide user to get a Resend API key

> "To send emails via Resend:
>
> 1. Sign up or log in at https://resend.com
> 2. Verify your sending domain under **Domains** (add the DNS records
>    Resend gives you for DKIM + SPF)
> 3. Go to **https://resend.com/api-keys** → **Create API Key**
> 4. Set permission to **Sending access**, copy the key — it's shown once
>
> **Without a verified domain**, you can only send from
> `onboarding@resend.dev`, and only to your own Resend account email —
> testing only, not usable for a real app.
>
> Come back once you have the key and a verified domain."

**Stop here.** Do not write any email code until the user confirms.

---

## Step 2 — Add credentials to environment

| Variable | Value |
|----------|-------|
| `RESEND_API_KEY` | *(from Step 1)* |
| `RESEND_FROM_ADDRESS` | *(e.g. `noreply@yourdomain.com`, must match the verified domain)* |
| `RESEND_FROM_NAME` | *(your app name — optional)* |

After the user confirms, verify:
```bash
echo "RESEND_API_KEY=${RESEND_API_KEY:+SET}" && echo "RESEND_FROM_ADDRESS=${RESEND_FROM_ADDRESS:+SET}"
```
Don't proceed until both show `SET`.

Restart automatically:
```bash
supervisorctl restart dev-server && sleep 3
```

---

## Step 3 — Create the email utility

Create `src/lib/resend-email.ts`:

```typescript
interface SendEmailParams {
  to: string;
  subject: string;
  html: string;
}

export async function sendEmail({ to, subject, html }: SendEmailParams) {
  const fromAddress = process.env.RESEND_FROM_ADDRESS;
  if (!fromAddress) {
    throw new Error("RESEND_FROM_ADDRESS is not set. Add it in Advanced → Env Vars.");
  }
  if (!process.env.RESEND_API_KEY) {
    throw new Error("RESEND_API_KEY is not set. Add it in Advanced → Env Vars.");
  }

  const fromName = process.env.RESEND_FROM_NAME || "";
  const from = fromName ? `${fromName} <${fromAddress}>` : fromAddress;

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
    },
    body: JSON.stringify({ from, to: [to], subject, html }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || `Resend error: ${res.status}`);
  }

  return res.json();
}
```

**Key points:**
- Server-side only — never import in client components
- Resend returns `200` on success with `{ id }` — check `res.ok`, not a
  specific status code

---

## Step 4 — Create Next.js API route

Create `src/app/api/email/send/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/resend-email";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (!body.to || !body.subject || !body.html) {
      return NextResponse.json(
        { error: "Missing required fields: to, subject, html" },
        { status: 400 }
      );
    }

    const result = await sendEmail({ to: body.to, subject: body.subject, html: body.html });
    return NextResponse.json({ success: true, id: result.id }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to send email";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
```

---

## Step 5 — Verify end-to-end

```bash
curl -X POST http://localhost:3001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@tech.gov.sg","subject":"Test from POC","html":"<p>Hello from my POC app!</p>"}'
```

Expected: `{"success":true,"id":"..."}`

**If the actual send route is guarded by a login check**, the curl above
will only ever hit the 401/redirect — it never reaches the real Resend
call, so confirming the guard rejects unauthenticated requests is NOT the
same as confirming email sending actually works. Test the underlying
function directly, bypassing the HTTP route and its auth guard entirely:

```bash
npx tsx -e "
import { sendEmail } from './src/lib/resend-email';
sendEmail({ to: 'your-email@tech.gov.sg', subject: 'Test', html: '<p>Test</p>' })
  .then(r => console.log('OK', r))
  .catch(e => console.error('FAILED', e));
"
```

---

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401` | API key invalid or revoked | Regenerate at https://resend.com/api-keys |
| `403` / domain not authorised | From address domain not verified in Resend | Verify DNS records first |
| Silent failure despite `200` | Checking status code instead of `res.ok`/body shape | Resend returns `200` with `{ id }` on success — no `201` |
| Mail only reaches account owner | Using `onboarding@resend.dev` without a verified domain | Verify a real domain for production sending |

---

## Rules

- **Server-side only** — never call Resend from client components.
- **Never log/echo the API key** — only confirm it's SET.
- Confirm with the user this is genuinely what they want — Postman is the
  gov default for a reason; Resend is for when they've explicitly asked.
- After setup, run the `self-heal` skill to verify the build passes.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
