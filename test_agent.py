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
DAYS = {"2026-10-29": [{"title": "Standup Projektteam"}], "2026-10-30": []}


def fake_urlopen(url, timeout=None):
    """The mock calendar: two days exist, one answers 500, one has no network, the rest are 404."""
    date = url.rsplit("/", 1)[-1].removesuffix(".json")
    if date in DAYS:
        body = io.BytesIO(json.dumps({"date": date, "events": DAYS[date]}).encode())
        body.status = 200
        return body
    if date == "2026-11-02":
        raise urllib.error.URLError("network down")
    raise urllib.error.HTTPError(url, 500 if date == "2026-11-01" else 404, "failed", {}, None)


def call(arguments, name="get_calendar_day"):
    """A tool call as the OpenAI client returns it."""
    return ToolCall(id=f"call-{arguments}", type="function", function={"name": name, "arguments": arguments})


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
                mock.patch("urllib.request.urlopen", fake_urlopen), \
                mock.patch.dict(os.environ, env), \
                redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = agent.main(["agent", question] if question else ["agent"])
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
