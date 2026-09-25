---
name: "vibe-postman"
description: "Send transactional email via Singapore Government's Postman API (postman.gov.sg) — API key setup, send/status endpoints, attachments. Use when the user specifically names Postman, OR when directed here by setup-email's routing. For a generic 'send email'/'add email'/'OTP email'/'email notification' request that doesn't name a provider, setup-email.md is the correct entry point instead — it decides Postman vs AWS SES vs Resend vs SMTP before this skill gets involved."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# Skill: Postman Email API Setup (Gov SG)

Guide users to add transactional email sending to their POC app using Singapore Government's Postman email API.

## When to use

When the user asks to "send email", "add email", "email notification", "OTP email", "postman", "transactional email", or "send receipt".

## Important: Existing API users only

As of September 2023, Postman halted new programmatic email API onboarding. This skill is for teams that **already have API access**. If the user cannot log in or generate a key, they need to contact their agency's existing Postman admin.

Do NOT suggest AWS SES, SendGrid, or any third-party email service for government apps — use Postman.

---

## Step 0 — Check if user already has a Postman API key

Ask the user ONE question:

> "Do you already have a Postman API key for sending emails? If yes, paste it into **Advanced → Env Vars** as `POSTMAN_API_KEY`. If not, I will guide you through getting one."

---

## Step 1 — Guide user to get API key

If the user does NOT have an API key, guide them:

> "To send emails from your app, you need a Postman API key. Here is how to get one:
>
> 1. Go to https://legacy.postman.gov.sg/
> 2. Sign in with your government email (WOGAD or TechPass)
> 3. Navigate to the **API Key** section in your account
> 4. Click **Generate API Key**
> 5. **Copy the key immediately** — it is shown only once
> 6. Come back here and tell me you have the key
>
> **Note:** If you cannot access Postman or see an error about onboarding being halted, contact your agency's Postman admin — new programmatic API onboarding was paused in September 2023.
>
> **Default sender address:** All emails will come from `info@mail.postman.gov.sg` unless your agency has set up a custom domain (separate process with Postman team)."

**Stop here.** Do not write any email code until the user confirms they have the API key.

---

## Step 2 — Add API key to environment

Once the user has their API key, follow this EXACT sequence:

### 2.1 — Ask about custom sender name

> "Would you like a custom sender name for your emails (e.g. your app name like 'Invoice Tracker')? Recipients will see this name in their inbox instead of 'Postman'. If yes, tell me the name. If no, we will use the default."

### 2.2 — Show the user ALL values to add

> "Please add the following in **Advanced → Env Vars** (left sidebar → Advanced dropdown → Env Vars):
>
> | Variable | Value |
> |----------|-------|
> | `POSTMAN_API_KEY` | *(paste your API key from Postman)* |
> | `POSTMAN_FROM_NAME` | *(your app name, e.g. "Invoice Tracker")* — optional |
>
> Copy each value and add them. Let me know when done."

### 2.3 — Verify key is set

After user confirms:
```bash
echo "POSTMAN_API_KEY=${POSTMAN_API_KEY:+SET}"
```

If empty, tell the user the key is missing. Do NOT proceed until it shows SET.

### 2.4 — Write to .env as backup (idempotent)

```bash
grep -q "POSTMAN_API_KEY" .env 2>/dev/null || cat >> .env <<EOF
POSTMAN_API_KEY="${POSTMAN_API_KEY}"
POSTMAN_FROM_NAME="${POSTMAN_FROM_NAME:-Postman}"
EOF
```

### 2.5 — Restart dev server

```bash
supervisorctl restart dev-server && sleep 3
```

Do NOT ask the user to restart — just do it.

---

## Step 3 — Create the email utility

Create `src/lib/postman-email.ts`:

```typescript
const POSTMAN_BASE_URL = "https://api.postman.gov.sg/v1";

interface SendEmailParams {
  to: string;
  subject: string;
  body: string;
  cc?: string[];
  bcc?: string[];
  replyTo?: string;
  classification?: "URGENT" | "FOR_ACTION" | "FOR_INFO";
  tag?: string;
}

interface SendEmailResponse {
  id: number;
  from: string;
  recipient: string;
  status: string;
  created_at: string;
}

export async function sendEmail(params: SendEmailParams): Promise<SendEmailResponse> {
  const apiKey = process.env.POSTMAN_API_KEY;
  if (!apiKey) {
    throw new Error("POSTMAN_API_KEY is not set. Add it in Advanced → Env Vars.");
  }

  const fromName = process.env.POSTMAN_FROM_NAME || "Postman";
  const fromAddress = `${fromName} <info@mail.postman.gov.sg>`;

  const response = await fetch(`${POSTMAN_BASE_URL}/transactional/email/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      subject: params.subject,
      body: params.body,
      recipient: params.to,
      from: fromAddress,
      ...(params.replyTo && { reply_to: params.replyTo }),
      ...(params.cc && { cc: params.cc }),
      ...(params.bcc && { bcc: params.bcc }),
      ...(params.classification && { classification: params.classification }),
      ...(params.tag && { tag: params.tag }),
    }),
  });

  if (response.status === 429) {
    throw new Error("Rate limit exceeded (max 10 emails/sec). Try again shortly.");
  }
  if (response.status === 401) {
    throw new Error("Invalid API key. Check POSTMAN_API_KEY in Env Vars.");
  }
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Postman API error (${response.status}): ${errorBody}`);
  }

  return response.json();
}

export async function getEmailStatus(emailId: number) {
  const apiKey = process.env.POSTMAN_API_KEY;
  if (!apiKey) throw new Error("POSTMAN_API_KEY is not set.");

  const response = await fetch(`${POSTMAN_BASE_URL}/transactional/email/${emailId}`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });

  if (!response.ok) {
    throw new Error(`Failed to get email status (${response.status})`);
  }

  return response.json();
}
```

**Key points:**
- Server-side only — never import this in a client component
- Uses `POSTMAN_FROM_NAME` env var to customise the sender display name
- Handles rate limit (429), invalid key (401), and generic errors

---

## Step 4 — Create Next.js API route

Create `src/app/api/email/send/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/postman-email";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (!body.to || !body.subject || !body.body) {
      return NextResponse.json(
        { error: "Missing required fields: to, subject, body" },
        { status: 400 }
      );
    }

    const result = await sendEmail({
      to: body.to,
      subject: body.subject,
      body: body.body,
      cc: body.cc,
      bcc: body.bcc,
      replyTo: body.replyTo,
      classification: body.classification,
      tag: body.tag,
    });

    return NextResponse.json({ success: true, emailId: result.id }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to send email";
    const status = message.includes("Rate limit") ? 429 : message.includes("Invalid API key") ? 401 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
```

---

## Step 5 — Verify end-to-end

After creating the files, test:

```bash
curl -X POST http://localhost:3001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@tech.gov.sg","subject":"Test from POC","body":"<p>Hello from my POC app!</p>"}'
```

Expected: `{"success":true,"emailId":123}`

Tell the user to check their inbox. Remind them:
- Email delivery is **asynchronous** — a 201 response means accepted, not delivered
- Use the email ID to check status if needed

**If the actual send route is guarded by a login check** (e.g. it lives
behind auth middleware or its own `getSession()` check), the curl above
will only ever hit the 401/redirect — it never reaches the real Postman
call, so confirming the guard rejects unauthenticated requests is NOT
the same as confirming email sending actually works. Confirmed missed in
a real session: the AI verified the 401 guard and stopped there, leaving
the actual `sendEmail()` integration completely untested until the user
tried it manually later. To close that gap, test the underlying function
directly, bypassing the HTTP route and its auth guard entirely:

```bash
npx tsx -e "
import { sendEmail } from './src/lib/postman-email';
sendEmail({ to: 'your-email@tech.gov.sg', subject: 'Test', body: '<p>Test</p>' })
  .then(r => console.log('OK', r))
  .catch(e => console.error('FAILED', e));
"
```

This proves the Postman integration itself (endpoint, headers, payload
shape, API key) works, independent of whatever auth guard sits in front
of it. Do this BEFORE telling the user it's ready — don't let "the guard
returned 401" stand in for "the email actually sends."

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/transactional/email/send` | POST | Send one email (201 on success) |
| `/v1/transactional/email/{id}` | GET | Get email status by ID |
| `/v1/transactional/email` | GET | List sent emails (paginated) |

**Base URL:** `https://api.postman.gov.sg/v1`
**Auth:** `Authorization: Bearer <POSTMAN_API_KEY>`
**Rate limit:** 10 emails/second per account (429 if exceeded)

### Send parameters

| Param | Required | Notes |
|-------|----------|-------|
| subject | Yes | Email subject line |
| body | Yes | Email content (HTML supported) |
| recipient | Yes | Single recipient email address |
| from | No | Default: `info@mail.postman.gov.sg` — use `"App Name <info@mail.postman.gov.sg>"` for custom display name |
| reply_to | No | Reply-to address |
| cc | No | Array of email strings |
| bcc | No | Array of email strings |
| classification | No | `URGENT` / `FOR_ACTION` / `FOR_INFO` |
| tag | No | Custom label for tracking |

### Attachments (multipart/form-data only)

- Max 2MB per file
- Max 10 files per email
- Max 10MB total per email
- 34 supported types (pdf, docx, xlsx, png, jpg, csv, etc.)
- Only available to users with custom domain setup

### Email status lifecycle

`UNSENT` → `ACCEPTED` → `SENT` → `DELIVERED` → `OPENED`

Or: `BOUNCED` (hard/soft bounce) / `COMPLAINT` (marked as spam)

---

## Custom sender name vs custom domain

| Want | How |
|------|-----|
| Custom **name** (e.g. "Invoice Tracker") | Set `POSTMAN_FROM_NAME` env var — self-service, works immediately |
| Custom **email domain** (e.g. `noreply@myagency.gov.sg`) | Contact Postman team — requires DNS setup, takes ~2 weeks |

---

## Common errors

| Error | Fix |
|-------|-----|
| `POSTMAN_API_KEY is not set` | User forgot to add API key in Advanced → Env Vars |
| 401 Unauthorized | API key is invalid or expired — regenerate at legacy.postman.gov.sg |
| 429 Too Many Requests | Rate limit exceeded — implement retry with backoff or reduce send frequency |
| 413 Payload Too Large | Attachment exceeds 2MB or total exceeds 10MB |
| `Cannot access Postman portal` | New onboarding halted — contact agency Postman admin |

---

## Rules

- **Server-side only** — never call Postman API from client components
- **Never log/echo the full API key** — only confirm it is SET
- **Default sender** is `info@mail.postman.gov.sg` — customisable via display name
- **Do NOT suggest AWS SES, SendGrid, or Mailgun** — government apps use Postman
- **POC only** — remind user this is for sandbox/proof-of-concept
- **Bulk/campaign emails** are a different Postman feature (web UI campaigns, not this API)
- After setup, run the self-heal skill to verify build passes

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
