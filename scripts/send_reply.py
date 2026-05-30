#!/usr/bin/env python3
"""Send a threaded reply via Gmail SMTP. Called by the Zillow auto-responder agent.

Usage (body on stdin):

    echo "Hi, thanks for your interest..." | python3 send_reply.py \\
        --to "qm14b8kvk9fci10hbpqytpyvra@convo.zillow.com" \\
        --subject "Re: Jane is requesting information about 123 Main St" \\
        --in-reply-to "<CABCdef@mail.gmail.com>"

Reads config from data/config.json (must include from_address + gmail_app_password).
Exits 0 on success, prints error to stderr and exits non-zero on failure.

Stdlib-only — no pip install required.
"""
from __future__ import annotations

import argparse
import json
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.json"


def main() -> int:
    p = argparse.ArgumentParser(description="Send a Gmail SMTP reply with proper threading headers.")
    p.add_argument("--to", required=True, help="Recipient email (the convo.zillow.com relay)")
    p.add_argument("--subject", required=True, help="Subject line (caller should prepend 'Re: ')")
    p.add_argument(
        "--in-reply-to",
        required=True,
        dest="in_reply_to",
        help="Original Message-ID header value, WITH angle brackets, e.g. '<abc@mail.gmail.com>'",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and validate but do not actually send. Prints the full message to stdout.",
    )
    args = p.parse_args()

    # Load config
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except FileNotFoundError:
        print(f"ERROR: config not found at {CONFIG_PATH}", file=sys.stderr)
        return 1

    from_addr = cfg.get("from_address")
    app_password = cfg.get("gmail_app_password")

    if not from_addr:
        print("ERROR: from_address missing in data/config.json", file=sys.stderr)
        return 1
    if not args.dry_run and (not app_password or "<<" in str(app_password)):
        print(
            "ERROR: gmail_app_password not set in data/config.json. "
            "Generate one at https://myaccount.google.com/apppasswords",
            file=sys.stderr,
        )
        return 1

    # Read body from stdin
    body = sys.stdin.read()
    if not body.strip():
        print("ERROR: empty body on stdin", file=sys.stderr)
        return 1

    # Build the message
    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = from_addr
    msg["To"] = args.to
    msg["In-Reply-To"] = args.in_reply_to
    msg["References"] = args.in_reply_to
    msg.set_content(body)

    if args.dry_run:
        print("--- DRY RUN — message NOT sent ---")
        print(msg.as_string())
        return 0

    # Send via Gmail SMTPS (port 465, implicit TLS)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(from_addr, app_password)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        print(
            f"ERROR: SMTP auth failed ({e}). "
            "Check gmail_app_password — it must be a 16-char App Password, not your normal Gmail password.",
            file=sys.stderr,
        )
        return 2
    except (smtplib.SMTPException, OSError) as e:
        print(f"ERROR: SMTP send failed: {e}", file=sys.stderr)
        return 3

    print(f"OK sent to={args.to} subject={args.subject!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
