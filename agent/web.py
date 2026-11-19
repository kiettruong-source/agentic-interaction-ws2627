"""Local chat panel for the agent: python -m agent.web, then open http://127.0.0.1:8000

The page (agent/chat.html) posts a question to /api/ask. The server runs the same loop as the CLI,
so the run is logged to logs/ exactly as a CLI run, and answers with the exit code, the text the CLI
would print, and the run's log lines.
"""

import contextlib
import io
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

from agent.__main__ import REPO_DIR, RunLog, main

PAGE = Path(__file__).with_name("chat.html")
HERE = Path(__file__).parent
# Everything the page loads is served from here, so it also works offline. Only these exact files.
STATIC = {f"/fonts/{f.name}": (f, "font/woff2") for f in (HERE / "fonts").glob("*.woff2")}  # OFL
STATIC |= {f"/vendor/{f.name}": (f, "text/javascript; charset=utf-8") for f in (HERE / "vendor").glob("*.js")}
MAX_QUESTION = 2000  # characters
RUN_LOCK = threading.Lock()  # ponytail: one run at a time; stdout capture is process-wide
WINDOW = 60  # seconds; the free tier limits tokens per minute


def tokens_last_minute(logs_dir=None, now=None):
    """Tokens the model used in the last 60 s, summed from the run logs (CLI and panel runs alike).

    Each step's usage is counted once, even when one model reply asked for several tools.
    """
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(seconds=WINDOW)
    used, seen = 0, set()
    for path in Path(logs_dir or REPO_DIR / "logs").glob("*.jsonl"):
        if path.stat().st_mtime < time.time() - WINDOW - 5:
            continue  # untouched for a minute: nothing in it can count
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            usage, key = record.get("usage"), (record.get("run_id"), record.get("step"))
            if usage and key not in seen and datetime.fromisoformat(record["ts"]) >= since:
                seen.add(key)
                used += usage.get("total_tokens") or 0
    return used


def ask(question):
    """Run the agent once, like `python -m agent "<question>"`, and return what the page shows."""
    load_dotenv(REPO_DIR / ".env", override=False)
    log = RunLog(os.environ.get("MODEL", ""))
    out, err = io.StringIO(), io.StringIO()
    with RUN_LOCK, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(["agent", question], log)
    return {"exit_code": code, "answer": out.getvalue().strip(), "error": err.getvalue().strip(),
            "events": log.records}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self.reply(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/config":  # what the header shows; never the key
            load_dotenv(REPO_DIR / ".env", override=False)
            return self.reply(200, {"model": os.environ.get("MODEL", ""),
                                    "max_steps": os.environ.get("MAX_STEPS") or "10",
                                    "token_limit": int(limit) if (limit := os.environ.get("TOKEN_LIMIT", "")).isdecimal() else 8000})
        if self.path == "/api/usage":
            return self.reply(200, {"tokens": tokens_last_minute(), "window_s": WINDOW})
        if self.path in STATIC:  # exact names only, so no path tricks
            file, content_type = STATIC[self.path]
            return self.reply(200, file.read_bytes(), content_type)
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/ask":
            return self.reply(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            question = json.loads(self.rfile.read(min(length, 64_000)))["question"]
            if not isinstance(question, str) or not question.strip():
                raise ValueError("question must be a non-empty string")
            if len(question) > MAX_QUESTION:
                raise ValueError(f"question is longer than {MAX_QUESTION} characters")
        except (ValueError, KeyError, TypeError) as e:
            return self.reply(400, {"error": f"bad request: {e}"})
        self.reply(200, ask(question.strip()))

    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # keep the terminal quiet; runs are in logs/
        pass


def serve(port=8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)  # local only: the key stays here
    print(f"Agent chat panel on http://127.0.0.1:{port}  (Ctrl-C to stop)", file=sys.stderr)
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()


if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
