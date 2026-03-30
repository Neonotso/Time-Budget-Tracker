import http.server
import socketserver
import json

PORT = 18790
AUTH_TOKEN = "7db4a33f134b2b604fde890330cb61d332f20e474b0e1503"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        auth = self.headers.get('X-Auth-Token')
        if auth != AUTH_TOKEN:
            self.send_response(401)
            self.end_headers()
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        print(f"Relaying command: {data.get('text')}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
