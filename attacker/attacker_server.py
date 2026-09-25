"""
Simulates the attacker's machine: a tiny local HTTP server that receives
whatever an exfiltration request sends it and writes it to a log file.

This stands in for "somewhere on the internet the attacker controls."
In this project it only ever runs on 127.0.0.1 (our own machine) — it is
never a real external service.
"""

import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8000
LOG_FILE = "attacker/attacker_log.txt"


class ExfilLogHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] GET {self.path}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # Silence the default console logging; attacker_log.txt is our record.
        pass


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), ExfilLogHandler)
    print(f"Attacker server listening on http://{HOST}:{PORT}")
    server.serve_forever()
