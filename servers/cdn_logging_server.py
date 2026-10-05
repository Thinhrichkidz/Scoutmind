"""
A "compromised legitimate image host" for the allowlist re-attack.

It listens on 127.0.0.1:8001, the same origin the defence allows
(config.ALLOWED_ORIGINS), so render_image() is permitted to reach it. Unlike
the silent image_source_server.py, it also records every request line,
including the query string. That models an allowlisted CDN whose access logs
the attacker can read.

The lines go into attacker/attacker_log.txt, because that file stands for
"what the attacker can read". It is only started for the allowlisted-origin
experiment, never together with image_source_server.py (same port).
"""

import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8001
# Resolved from this file's location, not from the launch directory.
LOG_FILE = Path(__file__).resolve().parent.parent / "attacker" / "attacker_log.txt"


class CdnLoggingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] GET {self.path}\n")

        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silence the default console logging; the log file is the record.
        pass


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), CdnLoggingHandler)
    print(f"CDN logging server listening on http://{HOST}:{PORT}")
    server.serve_forever()
