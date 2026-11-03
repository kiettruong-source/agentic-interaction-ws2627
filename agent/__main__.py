"""Calendar agent: one pass model -> tool -> model.

Usage: python -m agent "Was steht am 29.10.2026 im Kalender?"
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

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
    "Dates are YYYY-MM-DD; if the year is missing, assume 2026. "
    "If a tool returns no data or an error, say so plainly. "
    "Answer briefly, in the language of the question."
)

CONFIG_KEYS = ("OPENAI_BASE_URL", "MODEL", "OPENAI_API_KEY", "DATA_BASE_URL")


class RunLog:
    """One JSONL file per run; each line is flushed immediately so crashed runs keep their log."""

    def __init__(self):
        self.run_id = uuid.uuid4().hex
        logs = REPO_DIR / "logs"
        logs.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.file = open(logs / f"{stamp}-{self.run_id[:8]}.jsonl", "a", encoding="utf-8")

    def __call__(self, event, **fields):
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        record = {"ts": ts, "run_id": self.run_id, "event": event, **fields}
        self.file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self.file.flush()


def get_calendar_day(base_url, date):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return None, None, {"date": date, "events": [], "error": "date must be YYYY-MM-DD"}
    url = f"{base_url}/calendar/{date}.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return url, response.status, json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return url, 404, {"date": date, "events": [], "error": "no data for this day"}
        raise


def fail(log, code, message, **fields):
    print(message, file=sys.stderr)
    log("error", message=message, **fields)
    return code


def run(log, argv):
    question = " ".join(argv[1:]).strip()
    load_dotenv(REPO_DIR / ".env", override=False)  # real environment variables win
    config = {k: os.environ.get(k, "") for k in CONFIG_KEYS}
    log("start", question=question, model=config["MODEL"],
        base_url=config["OPENAI_BASE_URL"], data_base_url=config["DATA_BASE_URL"])

    if not question:
        return fail(log, 2, 'usage: python -m agent "<question>"')
    missing = [k for k, v in config.items() if not v]
    if missing:
        return fail(log, 2, f"missing in environment/.env: {', '.join(missing)}")

    client = OpenAI(base_url=config["OPENAI_BASE_URL"], api_key=config["OPENAI_API_KEY"])
    data_base_url = config["DATA_BASE_URL"].rstrip("/")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]

    try:
        # Pass 1: the model must pick the tool call(s).
        log("model_request", messages=messages, tools=TOOLS)
        response = client.chat.completions.create(
            model=config["MODEL"], messages=messages, tools=TOOLS, tool_choice="required")
        reply = response.choices[0].message
        tool_calls = reply.tool_calls or []
        calls = [c.model_dump() for c in tool_calls]
        log("model_response", content=reply.content, tool_calls=calls,
            usage=response.usage and response.usage.model_dump())
        messages.append({"role": "assistant", "content": reply.content, "tool_calls": calls})

        # Run every requested tool call (a question may cover several days).
        for call in tool_calls:
            args = json.loads(call.function.arguments or "{}")
            log("tool_call", name=call.function.name, arguments=args)
            if call.function.name == "get_calendar_day":
                url, status, result = get_calendar_day(data_base_url, args.get("date", ""))
            else:
                url, status, result = None, None, {"error": f"unknown tool {call.function.name}"}
            log("tool_result", name=call.function.name, url=url, status=status, result=result)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})

        # Pass 2: answer from the tool results.
        log("model_request", messages=messages)
        response = client.chat.completions.create(model=config["MODEL"], messages=messages)
        answer = response.choices[0].message.content or ""
        log("model_response", content=answer, usage=response.usage and response.usage.model_dump())
    except Exception as e:
        return fail(log, 1, f"error: {e}", type=type(e).__name__)

    print(answer)
    log("answer", text=answer)
    return 0


def main(argv):
    log = RunLog()
    code = run(log, argv)
    log("end", exit_code=code)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
