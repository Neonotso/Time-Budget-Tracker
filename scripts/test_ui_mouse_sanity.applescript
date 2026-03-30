-- UI mouse sanity check
-- 1) Brings reMarkable front
-- 2) Performs two obvious clicks on screen

tell application "reMarkable" to activate
delay 0.8

tell application "System Events"
	-- top-left-ish
	click at {200, 200}
	delay 0.5
	-- middle-ish
	click at {900, 500}
end tell

return "done"
