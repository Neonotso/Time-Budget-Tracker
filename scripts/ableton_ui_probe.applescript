on run argv
	-- Usage:
	-- osascript ableton_ui_probe.applescript [containsText]
	set needle to ""
	if (count of argv) > 0 then set needle to item 1 of argv
	set needleLower to do shell script "echo " & quoted form of needle & " | tr '[:upper:]' '[:lower:]'"
	
	tell application "System Events"
		tell process "Live"
			set outLines to {}
			
			on scanElements(elList, needleLower, outLines)
				repeat with e in elList
					try
						set r to role of e
					on error
						set r to ""
					end try
					try
						set t to title of e
					on error
						set t to ""
					end try
					try
						set d to description of e
					on error
						set d to ""
					end try
					set lineText to (r as text) & " | " & (t as text) & " | " & (d as text)
					set lineLower to do shell script "echo " & quoted form of lineText & " | tr '[:upper:]' '[:lower:]'"
					if needleLower is "" or lineLower contains needleLower then
						set end of outLines to lineText
					end if
					try
						set kids to UI elements of e
						my scanElements(kids, needleLower, outLines)
					end try
				end repeat
				return outLines
			end scanElements
			
			set topKids to UI elements of window 1
			set outLines to my scanElements(topKids, needleLower, outLines)
			
			repeat with ln in outLines
				log ln
			end repeat
		end tell
	end tell
end run
