---
name: "vibe-awsses"
description: "Send transactional email via AWS SES. Use when the user specifically names AWS SES, already has AWS credentials configured, or explicitly says their agency lacks Postman access, OR when directed here by setup-email's routing. For a generic 'send email'/'add email' request, setup-email.md is the correct entry point instead — Postman is the gov-standard default there."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: setup
---

# vibe-awsses

Transactional email via AWS SES, for POC applications. Not the gov
default (that's `vibe-postman`) — use this only when the user has a
specific reason to use AWS SES instead.

---

## Step 0 — Check AWS credentials

```bash
echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:+SET}" && echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:+SET}" && echo "AWS_SES_REGION=${AWS_SES_REGION:+SET}" && echo "SES_FROM_EMAIL=${SES_FROM_EMAIL:+SET}"
```

- If all SET → skip to Step 2.
- If NOT set → Step 1.

---

## Step 1 — Guide user to get AWS SES credentials

> "To send emails via AWS SES, you need AWS credentials with SES
> permissions. Here is how:
>
> 1. Log in to your **AWS Console** (use your agency's AWS account)
> 2. Go to **SES** (Simple Email Service) in your target region (e.g.
>    `ap-southeast-1` for Singapore)
> 3. Under **Verified identities**, verify the sender email address or
>    domain
>    - Click **Create identity** → choose Email address or Domain
>    - For email: AWS sends a verification link — click it
>    - For domain: add the DNS records AWS provides
> 4. Create an **IAM user** (or use existing) with `ses:SendEmail` and
>    `ses:SendRawEmail` permissions
> 5. Generate **Access Key ID** and **Secret Access Key** for that IAM
>    user
> 6. Note your **verified sender email** (e.g. `noreply@youragency.gov.sg`)
>
> Come back here once you have the credentials and verified sender email.
>
> **Note:** New AWS accounts start in SES **sandbox mode** — you can only
> send to verified emails. Request production access in the SES console
> to send to any recipient."

**Stop here.** Do not write any email code until the user confirms they
have credentials.

---

## Step 2 — Add credentials to environment

Show the user ALL values to add in **Advanced → Env Vars**:

| Variable | Value |
|----------|-------|
| `AWS_ACCESS_KEY_ID` | *(your IAM access key)* |
| `AWS_SECRET_ACCESS_KEY` | *(your IAM secret key)* |
| `AWS_SES_REGION` | *(e.g. `ap-southeast-1`)* |
| `SES_FROM_EMAIL` | *(your verified sender email)* |

After the user confirms, verify:
```bash
echo "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:+SET}" && echo "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:+SET}" && echo "AWS_SES_REGION=${AWS_SES_REGION:+SET}" && echo "SES_FROM_EMAIL=${SES_FROM_EMAIL:+SET}"
```
Don't proceed until all 4 show `SET`.

Restart automatically — don't ask the user to do it:
```bash
supervisorctl restart dev-server && sleep 3
```

---

## Step 3 — Install AWS SDK

```bash
npm install @aws-sdk/client-ses
```

---

## Step 4 — Create the email utility

Create `src/lib/ses-email.ts`:

```typescript
import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";

const ses = new SESClient({
  region: process.env.AWS_SES_REGION || "ap-southeast-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
  },
});

interface SendEmailParams {
  to: string | string[];
  subject: string;
  body: string;
  cc?: string[];
  bcc?: string[];
  replyTo?: string;
}

export async function sendEmail(params: SendEmailParams) {
  const fromEmail = process.env.SES_FROM_EMAIL;
  if (!fromEmail) {
    throw new Error("SES_FROM_EMAIL is not set. Add it in Advanced → Env Vars.");
  }
  if (!process.env.AWS_ACCESS_KEY_ID || !process.env.AWS_SECRET_ACCESS_KEY) {
    throw new Error("AWS credentials not set. Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Env Vars.");
  }

  const toAddresses = Array.isArray(params.to) ? params.to : [params.to];

  const command = new SendEmailCommand({
    Source: fromEmail,
    Destination: {
      ToAddresses: toAddresses,
      ...(params.cc && { CcAddresses: params.cc }),
      ...(params.bcc && { BccAddresses: params.bcc }),
    },
    Message: {
      Subject: { Data: params.subject, Charset: "UTF-8" },
      Body: { Html: { Data: params.body, Charset: "UTF-8" } },
    },
    ...(params.replyTo && { ReplyToAddresses: [params.replyTo] }),
  });

  const response = await ses.send(command);
  return { messageId: response.MessageId };
}
```

**Key points:**
- Server-side only — never import in client components
- Supports multiple recipients, CC, BCC, reply-to
- Region defaults to `ap-southeast-1` (Singapore)

---

## Step 5 — Create Next.js API route

Create `src/app/api/email/send/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/ses-email";

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
    });

    return NextResponse.json({ success: true, messageId: result.messageId }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to send email";
    const status = message.includes("credentials") ? 401 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
```

---

## Step 6 — Verify end-to-end

```bash
curl -X POST http://localhost:3001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@tech.gov.sg","subject":"Test from POC","body":"<p>Hello from my POC app!</p>"}'
```

Expected: `{"success":true,"messageId":"..."}`

Remind the user:
- If in SES sandbox mode, recipient must also be a verified email
- Check spam folder if email doesn't appear in inbox

**If the actual send route is guarded by a login check**, the curl above
will only ever hit the 401/redirect — it never reaches the real SES call,
so confirming the guard rejects unauthenticated requests is NOT the same
as confirming email sending actually works. Test the underlying function
directly, bypassing the HTTP route and its auth guard entirely:

```bash
npx tsx -e "
import { sendEmail } from './src/lib/ses-email';
sendEmail({ to: 'your-email@tech.gov.sg', subject: 'Test', body: '<p>Test</p>' })
  .then(r => console.log('OK', r))
  .catch(e => console.error('FAILED', e));
"
```

---

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Email address is not verified` | Sender not verified in SES | Verify the `SES_FROM_EMAIL` address in AWS SES console |
| `MessageRejected` | Recipient not verified (sandbox) | Either verify recipient or request SES production access |
| `InvalidClientTokenId` | Wrong access key | Check `AWS_ACCESS_KEY_ID` is correct |
| `SignatureDoesNotMatch` | Wrong secret key | Check `AWS_SECRET_ACCESS_KEY` is correct |
| `AccessDenied` | IAM user lacks SES permissions | Add `ses:SendEmail` policy to the IAM user |
| `Throttling` | Send rate exceeded | SES sandbox: 1 email/sec; production: higher — request increase |
| `Module not found: @aws-sdk/client-ses` | Package not installed | `npm install @aws-sdk/client-ses` |

## SES sandbox vs production

| | Sandbox (default) | Production |
|--|--|--|
| Send to | Verified emails only | Any email |
| Rate | 1 email/sec | 14 emails/sec (default, can increase) |
| Daily limit | 200 emails | 50,000+ |
| How to upgrade | SES console → Account dashboard → Request production access | — |

---

## Rules

- **Server-side only** — never call SES from client components.
- **Never log/echo AWS credentials** — only confirm they're SET.
- After setup, run the `self-heal` skill to verify the build passes.

---
*Prepared by CIOO Rabbit Team · For use with VIBER Studio on Rabbit Deploy*
