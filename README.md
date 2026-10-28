# agentic-interaction-ws2627

Exercises for *Agentic Interaction*, winter term 2026/27, Ulm University.

## Exercise 1: First Tool Call

`agent/` answers a question about the mock calendar in one pass: model → tool → model.
The model gets one tool, `get_calendar_day(date)`, which reads
`{DATA_BASE_URL}/calendar/{YYYY-MM-DD}.json` (HTTP 404 = no data, not a crash).

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

### Run

```bash
python -m agent "Was steht am 29.10.2026 im Kalender?"
```

The answer goes to stdout, exit code 0. Errors go to stderr (exit 1, or 2 for a missing question or config).

### Logs

Each run writes its own JSONL file to `logs/<UTC timestamp>-<run id>.jsonl` (not committed).
Each line is one event with `ts`, `run_id`, `event` and event fields:
`start`, `model_request`, `model_response`, `tool_call`, `tool_result`, `answer`, `error`, `end`.
