# Zillow Rental Manager Auto-Responder

Drafts polite replies to incoming Zillow Rental Manager messages, then sends an end-of-day digest so you know what needs your attention.

## How it works

Zillow Rental Manager has no direct API, so this agent works through Gmail. Zillow sends every renter message as an email to `your landlord inbox (configured via `data/config.json`)` from a `convo.zillow.com` relay address, and replies route back through the same relay. The agent processes that mailbox.

Two scheduled tasks do the work:

1. **`process-zillow-inbox`** — runs every 30 min from 7am–10pm
   - Finds unread messages from `convo.zillow.com`
   - Classifies each (tour request / general info / application question)
   - Checks whether the renter has already applied (cached in `data/applicants.json`)
   - Drafts a polite reply with the right template + disclaimer
   - Labels the thread for triage
   - Logs everything to `data/interactions.jsonl`

2. **`zillow-eod-summary`** — runs daily at 6pm
   - Reads today's log
   - Drafts a summary email to `your landlord inbox (configured via `data/config.json`)` listing every reply drafted and which tour requests need your action

## Auto-send via Gmail SMTP

Replies are sent automatically by `scripts/send_reply.py` using Gmail SMTP with an [App Password](https://myaccount.google.com/apppasswords). Workflow:

1. Agent identifies a new Zillow message it hasn't replied to
2. Renders the appropriate template (apply-first / tour-ack / general-ack)
3. Sends the reply via `send_reply.py` with proper threading headers
4. Labels the thread `Zillow/Auto-Replied` on successful send
5. Logs the full sent body to `data/interactions.jsonl` for audit
6. If the send fails, agent does NOT label — it retries on the next 3h run

**Dedup is rock-solid via three layers:**
- Gmail search filter excludes any thread carrying `Zillow/Auto-Replied` or `Zillow/Auto-Drafted` (legacy)
- Defensive label re-check before each send
- Pre-send scan of `interactions.jsonl` for any prior `"sent": true` entry on the same `thread_id`

No thread is ever replied to twice.

## Reply templates

Every reply ends with this disclaimer:

> *This is an automated reply. I review messages personally and will follow up on anything that needs a human response.*

- **No application yet** → Polite ask to apply (one fee covers all Zillow listings)
- **Applied + tour request** → Acknowledge, promise reply within 24h
- **Applied + general question** → Acknowledge, promise reply within 24h

## Gmail labels created

- `Zillow/Auto-Replied` — the lock label; agent has sent a reply on this thread
- `Zillow/Auto-Drafted` — legacy from the original draft-mode setup; kept as a secondary dedup lock
- `Zillow/Awaiting-Application` — renter hasn't applied yet
- `Zillow/Tour-Pending` — tour request needs your scheduling

## Files

| Path | Purpose | Committed? |
|---|---|---|
| `prompts/process_inbox.md` | Per-run agent prompt | ✅ |
| `prompts/eod_summary.md` | EOD digest prompt | ✅ |
| `scripts/send_reply.py` | SMTP helper invoked by the agent to send replies | ✅ |
| `data/config.example.json` | Template — copy to `data/config.json` and fill in | ✅ |
| `data/config.json` | Your `landlord_name`, `from_address`, `summary_email_to`, and **Gmail App Password** | ❌ gitignored (secret) |
| `data/interactions.jsonl` | Append-only log of every reply sent (full body for audit) | ❌ gitignored (PII) |
| `data/applicants.json` | Cache of renter → applied? → property | ❌ gitignored (PII) |

## Setup (cloning fresh)

```bash
# 1. Clone
git clone https://github.com/<your-username>/zillow-rental-auto-responder.git
cd zillow-rental-auto-responder

# 2. Fill in your config
cp data/config.example.json data/config.json
$EDITOR data/config.json   # set landlord_name, from_address, summary_email_to,
                           # AND gmail_app_password (16-char App Password from
                           # https://myaccount.google.com/apppasswords — requires 2FA)

# 3. Create the runtime data files
echo '{}' > data/applicants.json
touch data/interactions.jsonl

# 4. In Claude Code, set up the scheduled tasks pointing at this repo's
#    prompts/ directory. Both tasks should substitute {{PROJECT_ROOT}}
#    with the absolute path to this repo before executing the prompts.
```

The prompts use a `{{PROJECT_ROOT}}` placeholder for the absolute path so they're portable across machines.

## Pausing the agent

In Claude Code: `/schedule` → toggle the tasks off.
Or programmatically: `mcp__scheduled-tasks__update_scheduled_task` with `enabled: false`.

## Manual test run

Open `prompts/process_inbox.md` and paste the contents into a fresh Claude Code session.
