"""Personal agent: model and tools take turns until the model answers or the step limit is reached.

Tools read the user's calendar, weather, train connections and context from DATA_BASE_URL.

Usage: python -m agent "How do I get to Munich on 29 Oct 2026, and do I need an umbrella?"
"""

import functools
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI

REPO_DIR = Path(__file__).resolve().parent.parent

# Parameter kinds. The pattern is sent to the model and checked again before any request.
DATE = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$",
        "description": "Day as YYYY-MM-DD, e.g. 2026-10-29. If the year is missing, use 2026."}
CITY = {"type": "string", "pattern": r"^[a-z]+$",
        "description": "City id: the German city name in lowercase ASCII with ü as ue. "
                       "Munich/München is muenchen, Ulm is ulm."}

TOOLS = {  # name: (path under DATA_BASE_URL, description for the model, parameters)
    "get_calendar_day": (
        "calendar/{date}.json",
        "Appointments of one day in the user's calendar (start, end, title, location). "
        "An empty list means the day is free.",
        {"date": DATE}),
    "get_weather": (
        "weather/{city}/{date}.json",
        "Weather forecast for one city on one day: temperature in °C, condition (in German), "
        "rain probability from 0 to 1, wind in km/h.",
        {"city": CITY, "date": DATE}),
    "get_connections": (
        "transit/{from_city}/{to_city}/{date}.json",
        "Train connections from one city to another on one day: departure, arrival, train, "
        "changes, price in EUR. An empty list means there are no trains.",
        {"from_city": CITY, "to_city": CITY, "date": DATE}),
    "get_context": (
        "context.json",
        "The user's current date and time, home city, quiet hours and hints. Use it when the "
        "start city or today's date is not given.",
        {}),
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": params, "required": list(params)}}}
    for name, (_, description, params) in TOOLS.items()
]

SYSTEM_PROMPT = (
    "You are a personal assistant with tools for the user's data: calendar, weather, train "
    "connections and context. "
    "Use a tool whenever the answer depends on that data; never guess what a tool can look up. "
    "Work in steps: call tools until you have everything the task needs, then give the final answer. "
    "If the start city or today's date is not given, look it up with get_context. "
    "Never state a time, train, price, temperature or any other value that no tool returned. "
    "If a tool call fails, fix the call and retry if that can help; if there is no data, say plainly "
    "that it is unknown. "
    "To decide about an umbrella, use the rain probability. "
    "Answer briefly and in the language of the question: an English question gets an English answer "
    "even when the data is German."
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


@functools.cache
def known_cities(base_url):
    """City ids and names from the data's index.json, e.g. {"muenchen": "München"}; read once per run."""
    with urllib.request.urlopen(f"{base_url}/index.json", timeout=10) as response:
        return json.load(response)["cities"]


def fetch(base_url, tool, args):
    """Run one tool: check its arguments, then GET its file. Returns (url, status, data).

    A tool reports any failure by raising; the loop turns that into a result the model reads.
    """
    if tool not in TOOLS:
        raise ValueError(f"unknown tool {tool}; tools are {', '.join(TOOLS)}")
    path, _, params = TOOLS[tool]
    if not isinstance(args, dict) or set(args) != set(params):
        raise ValueError(f"expected exactly these parameters: {', '.join(params) or 'none'}")
    for name, value in args.items():
        # Every value must match its pattern, so nothing can step outside DATA_BASE_URL.
        if not isinstance(value, str) or not re.fullmatch(params[name]["pattern"], value):
            raise ValueError(f"{name}={value!r} is invalid. {params[name]['description']}")
        if params[name] is DATE:
            date.fromisoformat(value)  # rejects days that do not exist, e.g. 2026-02-31
        if params[name] is CITY and value not in (cities := known_cities(base_url)):
            known = ", ".join(f"{id} ({city})" for id, city in cities.items())
            raise ValueError(f"{name}={value!r} is not a city in the data. Known city ids: {known}. "
                             "If the user's city is not among them, there is no data for it.")
    path = path.format(**args)
    url = f"{base_url}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return url, response.status, json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # missing data, not empty data: an empty day or route has a file with []
            raise LookupError(f"there is no data for {path}: the value is unknown, do not guess it. "
                              "Check the city id and date, or tell the user it is unknown.") from None
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
                model=config["MODEL"], messages=messages, tools=TOOL_SCHEMAS)
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
                url, status, result = fetch(data_base_url, tool, args)
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
