# Agent from scratch

A tested, transcript-grounded reconstruction of the coding agent built in Tech
With Tim's video, [Building AI Agents in Pure Python - Beginner
Course](https://www.youtube.com/watch?v=c9AnqCeyxbI).

The project keeps the machinery visible: one OpenAI model, four ordinary Python
tools, and a loop that sends tool results back to the model until it returns a
normal answer. No agent framework is used.

## Live documentation

- [Documentation home](https://az9713.github.io/agent-from-scratch/)
- [Tests, explained](https://az9713.github.io/agent-from-scratch/tests-explained.html)
- [Development journey](https://az9713.github.io/agent-from-scratch/development-journey.html)

The same material is available as Markdown in
[`TESTS-EXPLAINED.md`](TESTS-EXPLAINED.md) and
[`DEVELOPMENT-JOURNEY.md`](DEVELOPMENT-JOURNEY.md).

## The agent loop

```text
user prompt
    ↓
OpenAI Chat Completions + four tool schemas
    ↓
assistant requests tools? ── no ──→ return the answer
    │
   yes
    ↓
run local Python tools → append tool results → call the model again
```

The four tools are:

- `list_files` — show files and directories in the workspace;
- `read_file` — read UTF-8 text;
- `write_file` — create or replace UTF-8 text files; and
- `run_command` — run a shell command only after explicit user approval.

## Two versions of the same program

[`agent.py`](agent.py) is the clean runnable implementation.

[`agent_tutorial.py`](agent_tutorial.py) is the learning version. It embeds
Tim's concepts as timestamped prose comments beside the corresponding code and
labels the safeguards that were added during reconstruction. An AST parity test
proves that the comments do not change the executable Python structure.

This two-file design keeps the operational program readable without separating
the tutorial prose from the code it explains.

## Set up

Requirements:

- Python 3.10 or newer;
- [`uv`](https://docs.astral.sh/uv/); and
- an OpenAI API key with available API credits.

Install the locked dependencies:

```powershell
uv sync --dev
```

Copy `.env.example` to `.env`, then replace the placeholder value:

```text
OPENAI_API_KEY=your-key-here
```

`.env` is ignored by Git and must never be committed.

The default model is `gpt-5-mini`, matching Tim's demonstration. Override it by
setting `OPENAI_MODEL` in `.env`.

## Run

Interactive conversation:

```powershell
uv run python agent.py
```

One prompt and exit:

```powershell
uv run python agent.py --prompt "Inspect this folder and explain the project."
```

The folder from which the program starts becomes its workspace. Direct file
tools reject paths outside that workspace. Every shell command pauses for a
literal `y` confirmation.

## Test

```powershell
uv run pytest
```

Current deterministic result: **9 passing tests**.

The suite covers the central model/tool feedback loop, one and multiple tool
calls, conversation message shape, file operations, path traversal rejection,
command approval, unknown-tool recovery, the maximum-round guard, actual OpenAI
SDK serialization through a local mock transport, and AST parity between the
two agent files.

Measured branch coverage of `agent.py` is **63%**. That is good coverage of the
educational core, not production assurance. The CLI, real subprocess behavior,
malformed inputs, hostile filesystem cases, cross-platform behavior, and a
funded live OpenAI call need more testing. Read
[`TESTS-EXPLAINED.md`](TESTS-EXPLAINED.md) for the test-by-test analysis.

## Safety boundary

This project adds safeguards that were outside the video's happy-path code:

- environment-based secret loading;
- confinement of direct file tools to the launch workspace;
- explicit approval before every shell command;
- recoverable tool errors;
- a 20-round model/tool ceiling; and
- a 120-second command timeout.

The shell tool is still not a sandbox. An approved command runs with the user's
operating-system permissions. Use the project only in a folder whose contents
may safely be modified.

## Source fidelity

The implementation preserves the architecture and visible behavior from Tim's
video, but it does not claim byte-for-byte recovery of his source. The API key
was intentionally unavailable, some operational details were not part of the
video, and this version adds explicit safety and testing infrastructure.

[`SOURCE_NOTES.md`](SOURCE_NOTES.md) records the timestamped evidence and the
boundary between visible source material and reconstruction. The raw transcript,
downloaded video evidence, environment secrets, local caches, and workstation
manifests are deliberately excluded from the public repository.

## Project map

| Path | Purpose |
|---|---|
| `agent.py` | Clean runnable coding agent |
| `agent_tutorial.py` | Same program with transcript-grounded teaching comments |
| `tests/test_agent.py` | Deterministic tool-loop and real-SDK mock-transport tests |
| `tests/test_tutorial.py` | AST equivalence test for the tutorial |
| `TESTS-EXPLAINED.md` | Detailed test coverage and quality analysis |
| `DEVELOPMENT-JOURNEY.md` | Decisions, failures, verification, and unfinished work |
| `TEST_REPORT.md` | Concise execution record |
| `SOURCE_NOTES.md` | Source provenance and reconstruction boundary |
| `index.html` | GitHub Pages documentation home |
| `tests-explained.html` | HTML version of the testing guide |
| `development-journey.html` | HTML version of the development journey |
| `scripts/build_docs.py` | Deterministic Markdown-to-HTML builder |

## Rebuild the HTML

```powershell
uv run python scripts/build_docs.py
```

The generated pages are self-contained. They use no remote fonts, scripts, or
images and support mobile screens, keyboard focus, reduced-motion preferences,
printing, section tracking, and code-block copying.

## Attribution

The teaching sequence and core agent architecture are derived from Tech With
Tim's public tutorial. This repository is an independent educational
reconstruction with additional safeguards, tests, documentation, and provenance
notes. Watch the [original video](https://www.youtube.com/watch?v=c9AnqCeyxbI)
for Tim's complete walkthrough and demonstrations.
