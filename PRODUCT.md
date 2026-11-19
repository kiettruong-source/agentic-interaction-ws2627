# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python standard library only (`http.server`) serving one static HTML page; no new pip dependencies.
GSAP, marked and DOMPurify are vendored in `agent/vendor/` and the fonts in `agent/fonts/`, so the
panel works offline. The CLI agent in `agent/__main__.py` stays the graded interface; the web panel
is an extra that calls the same loop.

## Users

The developer of this course project (a student at Ulm University, course *Human AI Interaction*,
winter term 2026/27), demoing and testing their own agent locally, and showing it to classmates and
tutors. They want to talk to the agent without the terminal and see what it actually did.

## Product Purpose

A local chat panel for the personal agent. You type a question; the panel runs the real agent loop
and shows the answer together with how it got there: each step, which tool it called with which
arguments, whether the call worked, and how the run ended. Success: every kind of agent outcome is
readable at a glance in a calm, unhurried surface.

## Capabilities and Constraints

- The agent answers about a mock calendar, weather, train connections, and the user's context
  (tools `get_calendar_day`, `get_weather`, `get_connections`, `get_context`), all read from
  `DATA_BASE_URL`. Data covers 26 Oct to 8 Nov 2026, cities `ulm` and `muenchen`, and only some days.
- Answer types the panel must show: plain text/markdown answers, calendar days (appointments or
  free), weather (temperature, condition in German, rain probability, wind), train connections
  (departure, arrival, train, changes, price), "no data" answers, failed steps that the run
  recovered from, the step limit (exit 1), endpoint/fatal errors (exit 1), bad configuration (exit 2).
- Model: `openai/gpt-oss-20b` on Groq's free tier, 8,000 tokens per minute; one run takes seconds,
  so the panel needs a clear waiting state.
- Invocation, configuration and the JSONL run log stay as in the course's interface specification.
- Runs locally only; the API key never reaches the browser.

## Brand Commitments

- Pinned by the user (19 Nov 2026, replacing the earlier neon/meme brief): a calm Japanese vibe in
  pastel colours. No memes or slang: each outcome gets its plain name plus one short, soft line
  (e.g. "Found it.", "Not in the records. Nothing made up.").
- Original work only; no symbols tied to militarism or nationalism (e.g. no Rising Sun rays).

## Evidence on Hand

Real agent runs and their logs in `logs/`; mock data at `DATA_BASE_URL`. No screenshots, brand
assets, or testimonials exist; none may be invented.

## Product Principles

- Show the loop, not just the answer: every step the agent took is visible and honest.
- Never dress up a failure: a step limit or "no data" looks like what it is.
- Calm over clever: nothing on the page competes with the answer.
