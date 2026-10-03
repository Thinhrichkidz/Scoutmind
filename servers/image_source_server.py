"""A legitimate local image-source simulation with a tiny fixed GET response."""

from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8001


class ImageSourceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # render_image() simulates a display; it only needs a successful GET.
        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Keep the demo console quiet, like the attacker-simulation server.
        pass


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), ImageSourceHandler)
    print(f"Image source listening on http://{HOST}:{PORT}")
    server.serve_forever()
