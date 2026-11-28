"""Serve TokenQR, the production Relay handler, and a fake upstream on loopback."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import runpy
import subprocess
import sys
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

# server.py starts a public listener at import time. Capture its handler instead
# and mount it on an ephemeral loopback port, without changing Relay semantics.
with patch("http.server.HTTPServer") as start_relay:
    runpy.run_path(str(ROOT / "server.py"))
Relay = start_relay.call_args.args[1]

EVENTS = {"relay": [], "chat": []}
LOCK = threading.Lock()


class FixtureRelay(Relay):
    def do_POST(self):
        with LOCK:
            EVENTS["relay"].append(self.path)
        super().do_POST()

    def log_message(self, *args):
        pass


class Site(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/_fixture/events":
            with LOCK:
                self.json_response(200, EVENTS)
        elif self.path in {"/tokenqr.html", "/vendor/qrcode.js"}:
            super().do_GET()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self.send_error(404)
        content = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        authorization_ok = self.headers.get("Authorization") == "Bearer integration-dummy"
        with LOCK:
            EVENTS["chat"].append({"authorization_ok": authorization_ok, "body": content})
        if not authorization_ok or content != {
            "model": "fixture-model",
            "messages": [{"role": "user", "content": "Synthetic acceptance greeting"}],
            "stream": False,
        }:
            return self.json_response(422, {"error": "unexpected fixture chat request"})
        self.json_response(200, {"choices": [{"message": {"content": "dummy-upstream-reached"}}]})

    def json_response(self, status, data):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    with (
        ThreadingHTTPServer(("127.0.0.1", 0), FixtureRelay) as relay,
        ThreadingHTTPServer(("127.0.0.1", 0), partial(Site, directory=ROOT)) as site,
    ):
        for server in (site, relay):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        result = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("consent.mjs")),
                f"http://127.0.0.1:{site.server_port}",
                f"http://127.0.0.1:{relay.server_port}/relay",
                *sys.argv[1:],
            ],
            check=False,
        )
    sys.exit(result.returncode)
