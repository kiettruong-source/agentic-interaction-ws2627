# agentic-interaction-ws2627

Exercises for *Human AI Interaction*, winter term 2026/27, Ulm University.

## The agent (Exercises 1 and 3)

`agent/` answers a question about the mock calendar. Model and tools take turns: each step is one
model call, in which the model either asks for a tool or answers. An answer ends the run with exit
code 0. A run that has no answer after `MAX_STEPS` steps ends as an error.

The model has one tool, `get_calendar_day(date)`, which reads
`{DATA_BASE_URL}/calendar/{YYYY-MM-DD}.json` (HTTP 404 = no data, not a crash).
The default model asks for one tool per step, so a question about *n* days takes *n* + 1 steps.

A failed step does not end the run. A tool call that fails (bad date, no data, network down, unknown
tool) goes back to the model as an error result. A reply that the endpoint rejects, or an empty reply,
is logged and followed by the next step.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (not committed). Environment variables take precedence over it:

```
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL=openai/gpt-oss-20b
OPENAI_API_KEY=<your key>
DATA_BASE_URL=https://jhbelz.github.io/agentic-interaction-data/v1
```

Any OpenAI-compatible endpoint works; the agent uses the `openai` library, not `groq`.
Optional: `MAX_STEPS` (default 10) is the most model calls one run may make.

### Run

```bash
python -m agent "What is on 29 Oct 2026 and on 30 Oct 2026?"
python -m agent "Was steht am 29.10.2026 im Kalender?"
MAX_STEPS=1 python -m agent "What is on 29 Oct 2026 and on 30 Oct 2026?"   # hits the step limit
```

| Exit code | Meaning |
|---|---|
| 0 | the answer is on stdout |
| 1 | error on stderr: step limit reached, or the model endpoint failed |
| 2 | missing question or configuration |
| 130 | interrupted with Ctrl-C |

### Logs

Each run writes its own JSONL file to `logs/<UTC timestamp>-<run id>.jsonl` (not committed).
Every line has `ts`, `run_id`, `event` and `model`.

| Event | When | Other fields |
|---|---|---|
| `user_task` | first line | `task`, `base_url`, `data_base_url`, `max_steps` |
| `tool_call` | the model asked for a tool | `step`, `tool`, `args`, `ok`, `duration_ms` and `usage` of the model call |
| `tool_result` | the tool finished | `step`, `tool`, `args`, `ok`, `duration_ms` of the tool, `url`, `status`, `result` |
| `final` | the model answered | `step`, `ok: true`, `duration_ms`, `usage`, `answer`, `exit_code: 0` |
| `error` | a step or the run failed | `ok: false`, `message`, usually `type`; `step` and `duration_ms` for a failed step; `exit_code` only if it ended the run |

The last line says how the run ended: `final`, or an `error` with `exit_code` (`type` is `StepLimit`
when the step limit was reached). An `error` without `exit_code` is a failed step the run recovered from.

### Tests

```bash
python -m unittest
```

`test_agent.py` runs the loop against scripted model replies and fake calendar data, so it needs no
network and no tokens. It covers several steps, the step limit, failed steps, and the log format.
