# Zillow EOD digest

You are sending the end-of-day digest for the landlord's Zillow Rental Manager auto-responder. Summarize today's activity into a single email draft.

## Tools you'll use

- `Read` — load the log and config
- `mcp__dc957175-812e-4a8d-ba2e-f832a8bfb020__create_draft` — create the digest email

If `create_draft`'s schema isn't loaded, use `ToolSearch select:mcp__dc957175-812e-4a8d-ba2e-f832a8bfb020__create_draft`.

## Workflow

### Step 1 — Load config + today's interactions

Read `{{PROJECT_ROOT}}/data/config.json` for `summary_email_to`.

Read `{{PROJECT_ROOT}}/data/interactions.jsonl`. Filter to entries where `ts` falls on today's local date (YYYY-MM-DD). If empty, draft a short "no Zillow activity today" digest anyway — it confirms the agent is alive.

### Step 2 — Bucket the entries

Three buckets:

- **🔔 Needs your action** — entries where `needs_my_action == true` (applied renters asking for tours or substantive info). The most important section — put it first.
- **📨 Pushed to apply** — entries with `template == "A"` (renters who hadn't applied; we asked them to apply first).
- **✅ Acknowledged** — entries with `template == "C"` (applied renters with general questions; we promised a follow-up within 24h).

### Step 3 — Draft the email

Use `create_draft`:

- `to`: `[<summary_email_to from config>]`
- `subject`: `Zillow Auto-Responder — Daily Digest (<today's date in Mon DD format>)`
- `body`: the markdown-style summary below, rendered as plain text

**Body template:**

```
Zillow Auto-Responder — daily digest for <today's date>

<N> drafts created. All drafts are saved in your Gmail Drafts folder under the "Zillow/Auto-Drafted" label, ready for you to review and send.

────────────────────────────────────
🔔 NEEDS YOUR ACTION (<count>)
────────────────────────────────────
<For each entry in the "needs action" bucket:>
• <Renter name> — <Property>
  Asked: <message_snippet, trimmed to ~120 chars>
  Classification: <classification>
  → Drafted Template <B|C>. Schedule or respond when you can.

────────────────────────────────────
📨 PUSHED TO APPLY (<count>)
────────────────────────────────────
<For each entry in "pushed to apply" bucket, one-liner:>
• <Renter name> — <Property> — asked about <classification, lowercased and human-readable>

────────────────────────────────────
✅ ACKNOWLEDGED (<count>)
────────────────────────────────────
<For each entry in "acknowledged" bucket, one-liner:>
• <Renter name> — <Property>

────────────────────────────────────

If any of these look off, edit or delete the drafts before sending.

— Zillow Auto-Responder (review the prompt at {{PROJECT_ROOT}}/prompts/)
```

Render with real counts and entries. Drop a section entirely (don't print empty headers) if the bucket is empty, EXCEPT keep the "needs action" section even when empty so the absence is visible — write "None today. ✨"

### Step 4 — Reply to the user

After the draft is created, reply with one line: `EOD digest drafted: <N> total interactions today (<count> need your action). Draft ID: <id>`.

## Guardrails

- One draft per run — don't create duplicates if re-run.
- If today's bucket is genuinely empty (zero log lines for today), the email body should say so plainly and not invent activity.
- Do not include relay addresses or message IDs in the email body — those are internal.
