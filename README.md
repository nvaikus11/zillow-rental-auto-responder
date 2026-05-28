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

## ⚠️ Drafts, not auto-sends

The Gmail MCP can only **create drafts**, not send. Workflow:
1. Agent drafts a reply in Gmail
2. Thread gets labeled `Zillow/Auto-Drafted`
3. You review and hit Send in Gmail (one click each)
4. EOD email reminds you of pending drafts

If you want true auto-send later, we'd layer Zapier's "Send Gmail" on top.

## Reply templates

Every reply ends with this disclaimer:

> *This is an automated reply. I review messages personally and will follow up on anything that needs a human response.*

- **No application yet** → Polite ask to apply (one fee covers all Zillow listings)
- **Applied + tour request** → Acknowledge, promise reply within 24h
- **Applied + general question** → Acknowledge, promise reply within 24h

## Gmail labels created

- `Zillow/Auto-Drafted` — agent has drafted a reply
- `Zillow/Awaiting-Application` — renter hasn't applied yet
- `Zillow/Tour-Pending` — tour request needs your scheduling

## Files

| Path | Purpose | Committed? |
|---|---|---|
| `prompts/process_inbox.md` | Per-run agent prompt | ✅ |
| `prompts/eod_summary.md` | EOD digest prompt | ✅ |
| `data/config.example.json` | Template — copy to `data/config.json` and fill in | ✅ |
| `data/config.json` | Your real `landlord_name` + `summary_email_to` | ❌ gitignored |
| `data/interactions.jsonl` | Append-only log of every reply drafted | ❌ gitignored (PII) |
| `data/applicants.json` | Cache of renter → applied? → property | ❌ gitignored (PII) |

## Setup (cloning fresh)

```bash
# 1. Clone
git clone https://github.com/<your-username>/zillow-rental-auto-responder.git
cd zillow-rental-auto-responder

# 2. Fill in your config
cp data/config.example.json data/config.json
$EDITOR data/config.json   # set landlord_name and summary_email_to

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
