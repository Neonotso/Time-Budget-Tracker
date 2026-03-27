-- PNG-only micro test for reMarkable export dialog.
-- This version force-focuses reMarkable first, then clicks PNG.

set targetApp to "reMarkable"

tell application targetApp to activate
delay 0.7

tell application "System Events"
	-- Bring app process frontmost (extra safety)
	try
		tell process targetApp
			set frontmost to true
		end tell
	end try

	-- 1) semantic attempts first
	try
		tell process targetApp
			repeat with w in windows
				try
					if exists (first radio button of w whose name is "PNG") then
						click (first radio button of w whose name is "PNG")
						return "Clicked PNG radio by name"
					end if
				end try
				try
					if exists (first button of w whose name is "PNG") then
						click (first button of w whose name is "PNG")
						return "Clicked PNG button by name"
					end if
				end try
			end repeat
		end tell
	end try

	-- 2) calibrated fallback click point from TOOLS.md
	click at {851, 590}
	return "Clicked calibrated PNG point"
end tell
