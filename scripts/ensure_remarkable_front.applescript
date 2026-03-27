-- Ensure reMarkable is frontmost, exit fullscreen from current front app when needed,
-- and dismiss stale export dialogs before automation begins.
-- Usage:
--   osascript scripts/ensure_remarkable_front.applescript

on appIsRunning(appName)
	tell application "System Events"
		return (name of processes) contains appName
	end tell
end appIsRunning

on frontAppName()
	tell application "System Events"
		set frontProc to first process whose frontmost is true
		return name of frontProc
	end tell
end frontAppName

on exitFullscreenIfNeeded(procName)
	try
		tell application "System Events"
			set theProc to first process whose name is procName
			set attrs to value of attributes of window 1 of theProc
			set fullscreenState to false
			repeat with a in attrs
				if (name of a) is "AXFullScreen" then
					set fullscreenState to value of a
					exit repeat
				end if
			end repeat
		end tell
		if fullscreenState is true then
			tell application "System Events" to keystroke "f" using {control down, command down}
			delay 0.6
		end if
	on error
		-- ignore if window/attribute not available
	end try
end exitFullscreenIfNeeded

set targetApp to "reMarkable"

set currentFront to frontAppName()
if currentFront is not targetApp then
	my exitFullscreenIfNeeded(currentFront)
end if

if my appIsRunning(targetApp) then
	tell application targetApp to activate
	delay 0.3
else
	tell application targetApp to activate
	delay 0.8
end if

-- best-effort nudge: ensure non-minimized main window gets focus
try
	tell application "System Events"
		tell process targetApp
			if (count of windows) > 0 then
				set frontmost to true
				perform action "AXRaise" of window 1
			end if
		end tell
	end tell
end try

-- Dismiss stale export/save dialogs that may be left open from prior runs.
-- 1) Try Escape.
tell application "System Events" to key code 53

delay 0.2

-- 2) If a modal is still present, try clicking Cancel/Close buttons.
try
	tell application "System Events"
		tell process targetApp
			if (count of windows) > 0 then
				repeat with w in windows
					try
						if exists (first button of w whose name is "Cancel") then
							click (first button of w whose name is "Cancel")
							exit repeat
						end if
					on error
					end try
					try
						if exists (first button of w whose name is "Close") then
							click (first button of w whose name is "Close")
							exit repeat
						end if
					on error
					end try
				end repeat
			end if
		end tell
	end tell
end try
