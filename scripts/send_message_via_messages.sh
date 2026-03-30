#!/usr/bin/env bash
set -euo pipefail

# Send an iMessage/SMS via macOS Messages.app using AppleScript.
#
# Usage:
#   scripts/send_message_via_messages.sh --help
#   scripts/send_message_via_messages.sh --dry-run "+16162777088" "Test from Sally"
#   scripts/send_message_via_messages.sh "+16162777088" "Task finished"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage:
  send_message_via_messages.sh [--dry-run] <recipient> <message>

Examples:
  send_message_via_messages.sh --dry-run "+16162777088" "Hello"
  send_message_via_messages.sh "+16162777088" "Ableton render finished"

Notes:
- recipient can be a phone number (+E.164 recommended) or an email tied to iMessage.
- First run may prompt for macOS Automation permission (Terminal/iTerm -> Messages).
- SMS delivery depends on iPhone Text Message Forwarding/relay being enabled.
EOF
  exit 0
fi

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 2 ]]; then
  echo "❌ Missing arguments. Use --help for usage." >&2
  exit 2
fi

RECIPIENT="$1"
shift
MESSAGE="$*"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] would send to: $RECIPIENT"
  echo "[dry-run] message: $MESSAGE"
  exit 0
fi

/usr/bin/osascript - "$RECIPIENT" "$MESSAGE" <<'APPLESCRIPT'
on run argv
  set targetRecipient to item 1 of argv
  set outgoingMessage to item 2 of argv

  tell application "Messages"
    if not running then launch

    -- If recipient looks like a phone number, prefer SMS relay service first.
    set targetService to missing value
    set looksLikePhone to false
    if targetRecipient starts with "+" then set looksLikePhone to true
    if targetRecipient starts with "1" then set looksLikePhone to true

    if looksLikePhone then
      try
        set targetService to 1st service whose service type = SMS
      end try
    end if

    -- Fallback to iMessage, then any service.
    if targetService is missing value then
      try
        set targetService to 1st service whose service type = iMessage
      on error
        set targetService to 1st service
      end try
    end if

    -- Create/resolve buddy and send.
    set targetBuddy to buddy targetRecipient of targetService
    send outgoingMessage to targetBuddy
  end tell

  return "sent"
end run
APPLESCRIPT

echo "✅ Sent via Messages.app"
