#!/usr/bin/env python3
"""
Pushover notification script
"""

import os
import requests

# Load credentials from secrets
PUSHOVER_USER_KEY = "uy2dh2bf67ssmpnk8q3b3uuabvcxxu"
PUSHOVER_API_TOKEN = "acgk6c8e5hx1jh15hmy7vhc6t9jg37"

def send_notification(message, title="Sally"):
    """Send a Pushover notification"""
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": title
    }
    response = requests.post(url, data=data)
    return response.status_code == 200

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: pushover_notification.py <message>")
        sys.exit(1)
    
    msg = " ".join(sys.argv[1:])
    if send_notification(msg):
        print("Notification sent!")
    else:
        print("Failed to send notification")
