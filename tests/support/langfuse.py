"""
A stand-in Langfuse server for the telemetry tests: it records each ingestion request and answers the statuses it is given.
"""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PUBLIC_KEY = "pk-test"
SECRET_KEY = "sk-test"
ENV_VARS = ("SPECWORKS_LANGFUSE_PUBLIC_KEY", "SPECWORKS_LANGFUSE_SECRET_KEY", "SPECWORKS_LANGFUSE_HOST")


class Server:
    """
    Answers each request with the next status of ``statuses`` (the last one repeats); ``requests`` holds what it got.
    """

    def __init__(self, statuses=(200,)):
        self.statuses = list(statuses)
        self.requests: list[dict] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - the name http.server calls
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                try:
                    data = json.loads(body)
                except ValueError:
                    data = None
                server.requests.append({"path": self.path, "authorization": self.headers.get("Authorization"), "body": data})
                status = server.statuses[min(len(server.requests), len(server.statuses)) - 1]
                payload = json.dumps({"successes": [], "errors": []} if status < 300 else {"message": "refused"}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def batches(self) -> list[list[dict]]:
        return [request["body"]["batch"] for request in self.requests]


class Silent:
    """
    A host that accepts the connection but never answers.
    """

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.url = f"http://127.0.0.1:{self.sock.getsockname()[1]}"
        return self

    def __exit__(self, *exc):
        self.sock.close()


def clear_env(monkeypatch):
    """
    No SPECWORKS_LANGFUSE_* nor plain LANGFUSE_* variable from the machine running the tests.
    """
    for name in (*ENV_VARS, "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"):
        monkeypatch.delenv(name, raising=False)


def set_keys(monkeypatch, host=None):
    monkeypatch.setenv("SPECWORKS_LANGFUSE_PUBLIC_KEY", PUBLIC_KEY)
    monkeypatch.setenv("SPECWORKS_LANGFUSE_SECRET_KEY", SECRET_KEY)
    if host is not None:
        monkeypatch.setenv("SPECWORKS_LANGFUSE_HOST", host)


def opt_in(root, host=None):
    """
    Append a ``telemetry`` block opting in to the top level's config.
    """
    config = root / ".specworks/config.yml"
    block = "telemetry:\n  langfuse: true\n" + (f"  host: {host}\n" if host else "")
    config.write_text(config.read_text(encoding="utf-8").rstrip("\n") + "\n" + block, encoding="utf-8")


def event_lines(folder) -> list[dict]:
    path = folder / "events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
