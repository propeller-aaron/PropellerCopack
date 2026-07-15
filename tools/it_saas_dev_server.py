"""Local static server with /it/api/apollo proxy for live Apollo refreshes.

Usage:
  python tools/it_saas_dev_server.py
  # then open http://127.0.0.1:8765/it/

The dashboard stores the API key in the browser and posts it to
/it/api/apollo so the key never needs to live in committed files.
"""

from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from refresh_it_saas import fetch_apollo  # noqa: E402


class ItHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        if self.path.startswith("/it/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/it/api/apollo":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers", "Content-Type, X-Api-Key"
            )
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/it/api/apollo":
            self._apollo_response()
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/it/api/apollo":
            self._apollo_response()
            return
        self.send_error(405, "Method not allowed")

    def _read_api_key(self) -> str:
        key = (self.headers.get("X-Api-Key") or "").strip()
        length = int(self.headers.get("Content-Length") or 0)
        if length > 0:
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                key = (payload.get("apiKey") or payload.get("api_key") or key or "").strip()
        return key

    def _apollo_response(self):
        api_key = self._read_api_key()
        if not api_key:
            self._json(400, {"error": "API key required. Pass X-Api-Key or JSON apiKey."})
            return
        try:
            data = fetch_apollo(api_key)
            self._json(200, data)
        except Exception as exc:  # noqa: BLE001 - surface Apollo errors to UI
            self._json(502, {"error": str(exc)})

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), ItHandler)
    print(f"IT dashboard: http://127.0.0.1:{port}/it/")
    print(f"Apollo proxy: POST http://127.0.0.1:{port}/it/api/apollo")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
