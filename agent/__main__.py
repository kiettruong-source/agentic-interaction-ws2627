"""Calendar agent: model and tools take turns until the model answers or the step limit is reached.

Usage: python -m agent "What is on 29 Oct 2026 and on 30 Oct 2026?"
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI

REPO_DIR = Path(__file__).resolve().parent.parent

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_day",
            "description": (
                "Get all appointments of one day from the user's calendar "
                "(start, end, title, location). An empty list means the day is free."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The day in ISO format YYYY-MM-DD, e.g. 2026-10-29.",
                    }
                },
                "required": ["date"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are a personal assistant with tools for the user's data. "
    "Use a tool whenever the answer depends on that data; never guess what a tool can look up. "
    "Work in steps: call tools until you have everything the task needs, then give the final answer. "
    "Dates are YYYY-MM-DD; if the year is missing, assume 2026. "
    "If a tool call fails, fix the call and retry if that can help; if there is no data, say so plainly. "
    "Answer briefly and in the language of the question: an English question gets an English answer "
    "even when the calendar entries are German."
)

CONFIG_KEYS = ("OPENAI_BASE_URL", "MODEL", "OPENAI_API_KEY", "DATA_BASE_URL")


class RunLog:
    """One JSONL file per run; each line is written at once so crashed runs keep their log.

    Events: user_task, tool_call, tool_result, final, error. The last line of a run is `final`
    or an `error` carrying `exit_code`.
    """

    def __init__(self, model):
        self.run_id = uuid.uuid4().hex
        self.model = model
        logs = REPO_DIR / "logs"
        logs.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = logs / f"{stamp}-{self.run_id[:8]}.jsonl"

    def __call__(self, event, **fields):
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        record = {"ts": ts, "run_id": self.run_id, "event": event, "model": self.model, **fields}
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def ms_since(start):
    return round((time.monotonic() - start) * 1000)


def get_calendar_day(base_url, date):
    """Returns (url, status, data). A tool reports any failure by raising; the loop tells the model."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("date must be YYYY-MM-DD")
    url = f"{base_url}/calendar/{date}.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return url, response.status, json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # not an empty day: a free day has a file with an empty list
            raise LookupError(f"there is no calendar data for {date}, so it is unknown whether "
                              "that day is free") from None
        raise


def fail(log, code, message, **fields):
    """End the run as an error: message to stderr, last line of the log, exit code."""
    print(message, file=sys.stderr)
    log("error", ok=False, message=message, exit_code=code, **fields)
    return code


def run(log, argv):
    question = " ".join(argv[1:]).strip()
    config = {k: os.environ.get(k, "") for k in CONFIG_KEYS}
    max_steps = os.environ.get("MAX_STEPS") or "10"
    log("user_task", task=question, base_url=config["OPENAI_BASE_URL"],
        data_base_url=config["DATA_BASE_URL"], max_steps=max_steps)

    if not question:
        return fail(log, 2, 'usage: python -m agent "<question>"')
    missing = [k for k, v in config.items() if not v]
    if missing:
        return fail(log, 2, f"missing in environment/.env: {', '.join(missing)}")
    if not max_steps.isdecimal() or int(max_steps) < 1:
        return fail(log, 2, f"MAX_STEPS must be a positive integer, got {max_steps!r}")

    client = OpenAI(base_url=config["OPENAI_BASE_URL"], api_key=config["OPENAI_API_KEY"], timeout=60)
    data_base_url = config["DATA_BASE_URL"].rstrip("/")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]

    for step in range(1, int(max_steps) + 1):  # one step = one model call
        started = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=config["MODEL"], messages=messages, tools=TOOLS)
        except BadRequestError as e:
            # The endpoint rejected the model's own output (e.g. a malformed tool call):
            # this step failed, the run goes on.
            log("error", step=step, ok=False, duration_ms=ms_since(started),
                message=str(e), type=type(e).__name__)
            messages.append({"role": "user", "content": f"Your last reply was rejected: {e}. Try again."})
            continue
        reply = response.choices[0].message
        tool_calls = reply.tool_calls or []
        info = {"step": step, "duration_ms": ms_since(started),
                "usage": response.usage and response.usage.model_dump()}

        if not tool_calls:
            if reply.content:  # text and no tool call: the model decided it is done
                print(reply.content)
                log("final", ok=True, answer=reply.content, exit_code=0, **info)
                return 0
            log("error", ok=False, message="empty reply from the model", type="EmptyReply", **info)
            continue

        messages.append({"role": "assistant", "content": reply.content,
                         "tool_calls": [c.model_dump() for c in tool_calls]})
        for call in tool_calls:
            tool, args = call.function.name, call.function.arguments
            try:
                args = json.loads(args or "{}")
            except ValueError:
                pass  # not JSON: logged as the model sent it, and the call below fails
            log("tool_call", tool=tool, args=args, ok=True, **info)
            tool_started = time.monotonic()
            try:
                if tool != "get_calendar_day":
                    raise ValueError(f"unknown tool {tool}")
                url, status, result = get_calendar_day(data_base_url, **args)
                ok = True
            except Exception as e:  # a failed tool call is a result the model reads, not the end of the run
                ok, url, status, result = False, None, None, {"error": f"{type(e).__name__}: {e}"}
            log("tool_result", step=step, tool=tool, args=args, ok=ok,
                duration_ms=ms_since(tool_started), url=url, status=status, result=result)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})
    return fail(log, 1, f"error: step limit of {max_steps} reached without an answer", type="StepLimit")


def main(argv):
    load_dotenv(REPO_DIR / ".env", override=False)  # real environment variables win
    log = RunLog(os.environ.get("MODEL", ""))
    try:
        return run(log, argv)
    except KeyboardInterrupt:
        return fail(log, 130, "interrupted")
    except Exception as e:  # anything a step could not recover from ends the run
        return fail(log, 1, f"error: {e}", type=type(e).__name__)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
