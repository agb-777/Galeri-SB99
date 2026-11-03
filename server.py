#!/usr/bin/env python3
"""Tiny local server for the gallery + admin.

Run:   python3 server.py            (port 8000)
       python3 server.py 8080       (custom port)
       python3 server.py 8000 data.json   (custom file to auto-save, default url.json)

It serves the files in this folder and lets admin.html auto-save url.json.
Only this machine can connect (127.0.0.1), and the only file it can write is the one below.
"""
import http.server
import json
import os
import sys
import tempfile

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
FILE = os.path.basename(sys.argv[2]) if len(sys.argv) > 2 else "url.json"
ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES = 20 * 1024 * 1024
ALLOWED_HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # -- helpers ---------------------------------------------------------
    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _same_origin(self):
        if self.headers.get("Host", "") not in ALLOWED_HOSTS:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin.replace("http://", "", 1) in ALLOWED_HOSTS

    def end_headers(self):
        # Always serve fresh files so the site preview shows the latest url.json
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # -- routes ----------------------------------------------------------
    def do_GET(self):
        if self.path == "/__admin/ping":
            if not self._same_origin():
                return self._json(403, {"ok": False, "error": "forbidden"})
            return self._json(200, {"ok": True, "file": FILE})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/__admin/save":
            return self._json(404, {"ok": False, "error": "not found"})
        if not self._same_origin() or self.headers.get("X-Admin") != "1":
            return self._json(403, {"ok": False, "error": "forbidden"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json(400, {"ok": False, "error": "bad length"})
        if length <= 0 or length > MAX_BYTES:
            return self._json(413, {"ok": False, "error": "body too large or empty"})

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"ok": False, "error": "not valid JSON"})
        if not isinstance(data, (list, dict)):
            return self._json(400, {"ok": False, "error": "JSON must be a list or object"})

        target = os.path.join(ROOT, FILE)
        try:
            if os.path.exists(target):  # keep one backup of the previous version
                with open(target, "rb") as old, open(target + ".bak", "wb") as bak:
                    bak.write(old.read())
            fd, tmp = tempfile.mkstemp(dir=ROOT, prefix=".url-", suffix=".tmp")
            with os.fdopen(fd, "wb") as f:
                f.write(raw)
            os.replace(tmp, target)  # atomic: the file is never half-written
        except OSError as err:
            return self._json(500, {"ok": False, "error": str(err)})
        return self._json(200, {"ok": True, "file": FILE})

    def log_message(self, fmt, *args):
        if "/__admin/" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving {ROOT}")
        print(f"  Gallery: http://localhost:{PORT}/")
        print(f"  Admin:   http://localhost:{PORT}/admin.html   (auto-saves to {FILE})")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
