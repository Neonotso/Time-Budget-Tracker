#!/usr/bin/env python3
"""
Hey Sally Listener - Receives messages from iPhone Shortcut via Tailscale
Run as a daemon via launchd
"""

import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Load token from secrets
TOKEN_FILE = os.path.expanduser("~/.openclaw/workspace/.secrets/hey_sally_listener_token.env")
LOG_FILE = "/tmp/hey-sally-listener.log"

def log(msg):
    """Write to both stdout and log file"""
    timestamp = subprocess.run(["date"], capture_output=True, text=True).stdout.strip()
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def get_current_session_id():
    """Get the current main session ID from OpenClaw sessions.json"""
    sessions_file = os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json")
    try:
        with open(sessions_file, "r") as f:
            data = json.load(f)
        # Find the agent:main:main session
        if "agent:main:main" in data:
            return data["agent:main:main"].get("sessionId")
    except Exception as e:
        log(f"Error reading sessions.json: {e}")
    return None

def load_token():
    with open(TOKEN_FILE, "r") as f:
        for line in f:
            if line.startswith("X-Auth-Token="):
                return line.split("=", 1)[1].strip()
    raise ValueError("X-Auth-Token not found in secrets")

EXPECTED_TOKEN = load_token()

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Custom logging with timestamps
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_POST(self):
        # Validate Content-Type
        if self.headers.get("Content-Type") != "application/json":
            self.send_error(400, "Content-Type must be application/json")
            return

        # Validate auth token
        auth_token = self.headers.get("X-Auth-Token")
        if auth_token != EXPECTED_TOKEN:
            log(f"Auth failed! Got: {auth_token[:20]}... Expected: {EXPECTED_TOKEN[:20]}...")
            self.send_error(401, "Invalid or missing X-Auth-Token")
            return

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            log(f"Invalid JSON: {body[:100]}")
            self.send_error(400, "Invalid JSON body")
            return

        # Extract text field
        text = data.get("text")
        if not text:
            log("Missing 'text' field")
            self.send_error(400, "Missing 'text' field in JSON body")
            return

        # Forward to OpenClaw agent (run asynchronously)
        log(f"Received message: {text[:50]}...")
        
        # Send Pushover notification that a message was received
        try:
            import requests
            pushover_response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": "acgk6c8e5hx1jh15hmy7vhc6t9jg37",
                    "user": "uy2dh2bf67ssmpnk8q3b3uuabvcxxu",
                    "message": f"📱 New message: {text}",
                    "title": "Sally"
                },
                timeout=10
            )
            log(f"Pushover notification sent: {pushover_response.status_code}")
        except Exception as e:
            log(f"Pushover notification error: {e}")
        
        # Forward to OpenClaw agent asynchronously
        env = os.environ.copy()
        env["PATH"] = "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        
        # Dynamically get current main session ID
        session_id = get_current_session_id()
        if not session_id:
            log("ERROR: Could not get current session ID, message not forwarded")
            self.send_response(500)
            self.end_headers()
            return
        
        # Run in background - don't wait for response
        try:
            subprocess.Popen(
                ["/opt/homebrew/bin/openclaw", "agent", "--session-id", session_id, "--message", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            log(f"OpenClaw agent invoked (async) with session {session_id[:8]}...")
        except Exception as e:
            log(f"Error calling openclaw agent: {e}")
        except Exception as e:
            log(f"Error calling openclaw agent: {e}")

        # Respond success
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"status": "ok", "message": "received"}
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        # Health check endpoint
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"status": "ok", "service": "hey-sally-listener"}
        self.wfile.write(json.dumps(response).encode())

def run_server(port=18790):
    server_address = ("", port)
    httpd = HTTPServer(server_address, RequestHandler)
    log(f"Hey Sally listener starting on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
