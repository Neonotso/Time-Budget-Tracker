#!/usr/bin/env bash
set -euo pipefail

# Lightweight check to confirm Messages.app automation is reachable.
# This does NOT send any message.

/usr/bin/osascript <<'APPLESCRIPT'
tell application "Messages"
  if not running then launch
  set svcNames to {}
  try
    repeat with s in (every service)
      set end of svcNames to (name of s)
    end repeat
  on error
    -- Some setups don't expose service/account names cleanly; just confirm app automation works.
    set svcNames to {"Messages app reachable"}
  end try
  return svcNames
end tell
APPLESCRIPT

echo "✅ Messages automation reachable"
