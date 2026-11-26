from __future__ import annotations

import importlib.util
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "open_when_ready.py"
SPEC = importlib.util.spec_from_file_location("open_when_ready", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(helper)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        pass


class WaitForHttpTests(unittest.TestCase):
    def test_returns_true_once_server_answers(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/"
            self.assertTrue(helper.wait_for_http(url, timeout=2))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_returns_false_for_a_closed_port(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        self.assertFalse(helper.wait_for_http(f"http://127.0.0.1:{port}/", timeout=0.3))


if __name__ == "__main__":
    unittest.main()