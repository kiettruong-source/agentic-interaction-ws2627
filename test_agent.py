"""Offline checks for the agent loop: scripted model replies and fake data, so no network and no tokens.

Run: python -m unittest
"""

import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from openai import BadRequestError
from openai.types.chat import ChatCompletionMessageFunctionToolCall as ToolCall

import agent.__main__ as agent

ENV = {"OPENAI_BASE_URL": "http://model", "MODEL": "test-model", "OPENAI_API_KEY": "key",
       "DATA_BASE_URL": "http://data", "MAX_STEPS": ""}
SPEC_EVENTS = {"user_task", "tool_call", "tool_result", "final", "error"}
DATA = {  # path under DATA_BASE_URL -> body; any other path is a 404
    "calendar/2026-10-29.json": {"date": "2026-10-29", "events": [{"title": "Standup Projektteam"}]},
    "calendar/2026-10-30.json": {"date": "2026-10-30", "events": []},
    "weather/muenchen/2026-10-29.json": {"city": "München", "condition": "Schauer", "rain_probability": 0.6},
    "transit/ulm/muenchen/2026-10-29.json": {"connections": [{"departure": "07:12", "train": "ICE 594"}]},
    "transit/ulm/muenchen/2026-10-31.json": {"connections": []},
    "context.json": {"now": "2026-10-29T07:20", "home": "Ulm"},
    "index.json": {"cities": {"ulm": "Ulm", "muenchen": "München"}},
}


def fake_urlopen(url, timeout=None):
    """The mock data: the paths in DATA exist, 2026-11-01 answers 500, 2026-11-02 has no network."""
    path = url.removeprefix("http://data/")
    if path in DATA:
        body = io.BytesIO(json.dumps(DATA[path]).encode())
        body.status = 200
        return body
    if "2026-11-02" in path:
        raise urllib.error.URLError("network down")
    raise urllib.error.HTTPError(url, 500 if "2026-11-01" in path else 404, "failed", {}, None)


def call(arguments, name="get_calendar_day"):
    """A tool call as the OpenAI client returns it; dict arguments are sent as JSON."""
    if not isinstance(arguments, str):
        arguments = json.dumps(arguments)
    return ToolCall(id=f"call-{name}-{arguments}", type="function",
                    function={"name": name, "arguments": arguments})


def day(date):
    return call(json.dumps({"date": date}))


def reply(content=None, *calls):
    """One model reply: text, tool calls, or neither."""
    return NS(choices=[NS(message=NS(content=content, tool_calls=list(calls)))], usage=None)


class AgentLoopTest(unittest.TestCase):
    def run_agent(self, script, question="What is on 29 and 30 Oct 2026?", **env):
        """Run main() against scripted model replies -> (exit code, stdout, log lines, model-call mock).

        Also checks what every run must leave behind: a log in the specified shape whose last
        line says how the run ended.
        """
        create = mock.Mock(side_effect=script)
        client = NS(chat=NS(completions=NS(create=create)))
        env = {**ENV, **env}
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(agent, "REPO_DIR", Path(tmp)), \
                mock.patch.object(agent, "OpenAI", return_value=client), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen) as urlopen, \
                mock.patch.dict(os.environ, env), \
                redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = agent.main(["agent", question] if question else ["agent"])
            self.requested = [c.args[0].removeprefix("http://data/") for c in urlopen.call_args_list
                              if not c.args[0].endswith("/index.json")]
            (logfile,) = Path(tmp, "logs").glob("*.jsonl")
            log = [json.loads(line) for line in logfile.read_text(encoding="utf-8").splitlines()]

        for line in log:
            self.assertLessEqual({"ts", "run_id", "event", "model"}, line.keys())
            self.assertIn(line["event"], SPEC_EVENTS)
            self.assertEqual(line["model"], env["MODEL"])
        self.assertEqual(len({line["run_id"] for line in log}), 1)
        self.assertEqual(log[0]["event"], "user_task")
        self.assertEqual(log[-1]["event"], "final" if code == 0 else "error")
        self.assertEqual((log[-1]["exit_code"], log[-1]["ok"]), (code, code == 0))
        return code, out.getvalue(), log, create

    def events(self, log, event):
        return [line for line in log if line["event"] == event]

    def test_several_steps(self):
        answer = "Standup on the 29th, nothing on the 30th."
        code, out, log, create = self.run_agent(
            [reply(None, day("2026-10-29")), reply(None, day("2026-10-30")), reply(answer)])
        self.assertEqual((code, out, create.call_count), (0, answer + "\n", 3))
        self.assertEqual([r["step"] for r in self.events(log, "tool_result")], [1, 2])
        self.assertEqual(log[-1]["answer"], answer)

    def test_several_tool_calls_in_one_step(self):
        code, _, log, create = self.run_agent(
            [reply(None, day("2026-10-29"), day("2026-10-30")), reply("done")])
        self.assertEqual((code, create.call_count), (0, 2))
        calls, results = self.events(log, "tool_call"), self.events(log, "tool_result")
        self.assertEqual([c["args"] for c in calls], [{"date": "2026-10-29"}, {"date": "2026-10-30"}])
        self.assertEqual([r["ok"] for r in results], [True, True])
        self.assertEqual(results[0]["tool"], "get_calendar_day")
        self.assertEqual(results[0]["url"], "http://data/calendar/2026-10-29.json")  # via DATA_BASE_URL
        self.assertIsInstance(results[0]["duration_ms"], int)

    def test_answer_without_a_tool(self):
        code, out, _, create = self.run_agent([reply("Hello!")], question="Hi")
        self.assertEqual((code, out, create.call_count), (0, "Hello!\n", 1))

    def test_step_limit_is_an_error(self):
        code, out, log, create = self.run_agent([reply(None, day("2026-10-29"))] * 5, MAX_STEPS="2")
        self.assertEqual((code, out, create.call_count), (1, "", 2))
        self.assertEqual(log[-1]["type"], "StepLimit")

    def test_failed_steps_do_not_abort_the_run(self):
        rejected = BadRequestError("tool call validation failed", response=mock.Mock(status_code=400), body=None)
        code, out, log, create = self.run_agent([
            reply(None,
                  call("{}", name="delete_everything"),  # unknown tool
                  call("{not json"),                     # arguments are not JSON
                  call('["2026-10-29"]'),                # arguments are not an object
                  day("29.10.2026"),                     # wrong date format
                  day("2026-12-24"),                     # 404: no data
                  day("2026-11-01"),                     # 500
                  day("2026-11-02")),                    # network down
            rejected,                                    # the endpoint rejects the model's reply
            reply(None),                                 # empty reply
            reply("I could not read the calendar."),
        ])
        self.assertEqual((code, out, create.call_count), (0, "I could not read the calendar.\n", 4))
        results = self.events(log, "tool_result")
        self.assertEqual([r["ok"] for r in results], [False] * 7)
        self.assertTrue(all(r["result"]["error"] for r in results))
        self.assertEqual(len(self.events(log, "tool_call")), 7)  # every result has its call, even bad JSON
        errors = self.events(log, "error")
        self.assertEqual([e["step"] for e in errors], [2, 3])
        self.assertFalse(any("exit_code" in e for e in errors))
        # The model was told about every failure: seven tool results and the rejection.
        roles = [m["role"] for m in create.call_args.kwargs["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant"] + ["tool"] * 7 + ["user"])

    def test_model_failure_ends_the_run_as_an_error(self):
        code, out, log, _ = self.run_agent([RuntimeError("connection lost")])
        self.assertEqual((code, out, log[-1]["type"]), (1, "", "RuntimeError"))

    def test_interrupt_still_closes_the_log(self):
        code, out, _, _ = self.run_agent([KeyboardInterrupt()])
        self.assertEqual((code, out), (130, ""))

    def test_bad_invocation(self):
        for question, env in ((None, {}), ("Hi", {"MODEL": ""}),
                              ("Hi", {"MAX_STEPS": "abc"}), ("Hi", {"MAX_STEPS": "0"})):
            with self.subTest(question=question, env=env):
                code, out, _, create = self.run_agent([], question=question, **env)
                self.assertEqual((code, out, create.call_count), (2, "", 0))

    # Exercise 4: weather and train connections

    def test_two_tools_in_one_run(self):
        answer = "ICE 594 at 07:12; take an umbrella (60% rain)."
        code, out, log, create = self.run_agent([
            reply(None, call({}, "get_context")),
            reply(None, call({"from_city": "ulm", "to_city": "muenchen", "date": "2026-10-29"},
                             "get_connections")),
            reply(None, call({"city": "muenchen", "date": "2026-10-29"}, "get_weather")),
            reply(answer),
        ], question="How do I get to Munich on 29 Oct 2026, and do I need an umbrella?")
        self.assertEqual((code, out, create.call_count), (0, answer + "\n", 4))
        results = self.events(log, "tool_result")
        self.assertEqual([r["tool"] for r in results], ["get_context", "get_connections", "get_weather"])
        self.assertEqual([r["ok"] for r in results], [True] * 3)
        self.assertEqual(self.requested, ["context.json", "transit/ulm/muenchen/2026-10-29.json",
                                          "weather/muenchen/2026-10-29.json"])
        self.assertEqual(results[0]["result"]["home"], "Ulm")  # the start city comes from the data

    def test_gaps_and_bad_arguments_never_become_values(self):
        weather = "get_weather"
        cases = [  # (tool, arguments, ok, error type the model reads)
            (weather, {"city": "berlin", "date": "2026-10-29"}, False, "ValueError"),    # not in index.json
            (weather, {"city": "munich", "date": "2026-10-29"}, False, "ValueError"),    # English name
            (weather, {"city": "ulm", "date": "2026-12-24"}, False, "LookupError"),      # no such day
            ("get_connections", {"from_city": "ulm", "to_city": "muenchen", "date": "2026-10-31"},
             True, None),                                                                # no trains: data, not a gap
            (weather, {"city": "München", "date": "2026-10-29"}, False, "ValueError"),  # not an id
            (weather, {"city": "../calendar", "date": "2026-10-29"}, False, "ValueError"),
            (weather, {"city": "muenchen", "date": "2026-02-31"}, False, "ValueError"),  # no such day
            (weather, {"city": "muenchen", "date": "29.10.2026"}, False, "ValueError"),
            (weather, {"city": "muenchen", "date": 20261029}, False, "ValueError"),      # not a string
            (weather, {"date": "2026-10-29"}, False, "ValueError"),                      # missing
            (weather, {"city": "muenchen", "date": "2026-10-29", "unit": "C"}, False, "ValueError"),
            ("get_context", {"city": "ulm"}, False, "ValueError"),                       # takes none
            ("get_train", {}, False, "ValueError"),                                      # unknown tool
        ]
        code, _, log, _ = self.run_agent(
            [reply(None, *(call(args, tool) for tool, args, _, _ in cases)), reply("No data.")])
        self.assertEqual(code, 0)
        results = self.events(log, "tool_result")
        self.assertEqual([r["ok"] for r in results], [ok for _, _, ok, _ in cases])
        for r, (_, _, ok, error) in zip(results, cases):
            if error:
                self.assertTrue(r["result"]["error"].startswith(error + ":"), r["result"])
        self.assertEqual(results[3]["result"], {"connections": []})
        self.assertIn("muenchen (München)", results[1]["result"]["error"])  # tells the model the real id
        # Invalid arguments are rejected before any request; only the two valid calls went out.
        self.assertEqual(self.requested, ["weather/ulm/2026-12-24.json", "transit/ulm/muenchen/2026-10-31.json"])

    def test_tool_table_matches_its_paths(self):
        from string import Formatter
        for name, (path, _, params) in agent.TOOLS.items():
            with self.subTest(tool=name):
                placeholders = {field for _, field, _, _ in Formatter().parse(path) if field}
                self.assertEqual(placeholders, set(params))
        self.assertEqual([s["function"]["name"] for s in agent.TOOL_SCHEMAS], list(agent.TOOLS))


class WebPanelTest(unittest.TestCase):
    """agent/web.py runs the same loop and returns what the page renders."""

    def test_ask_returns_answer_exit_code_and_log(self):
        create = mock.Mock(side_effect=[reply(None, day("2026-10-29")), reply("Standup at 09:00.")])
        client = NS(chat=NS(completions=NS(create=create)))
        import agent.web as web
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(agent, "REPO_DIR", Path(tmp)), \
                mock.patch.object(web, "REPO_DIR", Path(tmp)), \
                mock.patch.object(agent, "OpenAI", return_value=client), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
                mock.patch.dict(os.environ, ENV):
            run = web.ask("What is on 29 Oct 2026?")
            (logfile,) = Path(tmp, "logs").glob("*.jsonl")  # the web run is logged like a CLI run
            logged = [json.loads(line) for line in logfile.read_text(encoding="utf-8").splitlines()]
        self.assertEqual((run["exit_code"], run["answer"], run["error"]), (0, "Standup at 09:00.", ""))
        self.assertEqual(run["events"], logged)
        self.assertEqual([e["event"] for e in run["events"]], ["user_task", "tool_call", "tool_result", "final"])

    def test_tokens_last_minute_counts_each_step_once(self):
        import agent.web as web
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 11, 19, 12, 0, 0, tzinfo=timezone.utc)
        line = lambda secs_ago, step, tokens, event="tool_call": json.dumps({
            "ts": (now - timedelta(seconds=secs_ago)).isoformat(), "run_id": "r1", "event": event,
            "step": step, "usage": {"total_tokens": tokens}})
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "run.jsonl").write_text("\n".join([
                line(90, 1, 1000),               # older than a minute: not counted
                line(30, 2, 400), line(30, 2, 400),  # two tool calls from one reply: counted once
                line(5, 3, 650, "final"),
            ]) + "\n", encoding="utf-8")
            self.assertEqual(web.tokens_last_minute(tmp, now), 1050)
