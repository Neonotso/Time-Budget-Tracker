on run argv
	-- Usage:
	-- osascript ableton_safe_restart.applescript "/path/to/Project.als"
	set projectPath to ""
	if (count of argv) > 0 then set projectPath to item 1 of argv
	
	tell application "Ableton Live 12 Suite" to activate
	delay 0.3
	
	tell application "System Events"
		tell process "Live"
			-- Stop playback (Space)
			keystroke space
			delay 0.1
			-- Save (Cmd+S)
			keystroke "s" using command down
			delay 0.3
			-- Quit (Cmd+Q)
			keystroke "q" using command down
			delay 0.6
			
			-- If save-confirm dialog appears, click Save
			if exists window 1 then
				try
					if exists button "Save" of window 1 then click button "Save" of window 1
				end try
			end if
		end tell
	end tell
	
	delay 1.0
	if projectPath is not "" then
		do shell script "open -a 'Ableton Live 12 Suite' " & quoted form of projectPath
	else
		do shell script "open -a 'Ableton Live 12 Suite'"
	end if
end run
