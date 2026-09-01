# Development Journey — `agent_tutorial.py`, a transcript-grounded coding agent

**Date:** 2026-08-31

**Deliverable:** `agent_tutorial.py` in the project root

**Brief:** "I added Tim's video transcript. Can you create a tutorial as if Tim is walking through the code. Write in prose and match each of his explanation or concept with the corresponding code segment. Embed the prose in the code as comments. do you think this is the best way to add explanation to the code ? let me know."

**Final artifact:** `agent_tutorial.py`

**Canonical runnable counterpart:** `agent.py`

> Reconstruction disclosure: the tutorial was built earlier in this same Codex
> task, but that part of the live conversation had already been compacted when
> this journey was requested. This account is reconstructed from the surviving
> task summary, the user's messages, the source and artifact manifests, the
> executable files, timestamped comments, dependency lock, and test report. It
> does not pretend to be a verbatim command log where the original output is no
> longer available.

## 1. The brief — recover the code, then teach through it

The work began with a broader request:

> "Can you watch \"[https://www.youtube.com/watch?v=c9AnqCeyxbI&t=1506s](https://www.youtube.com/watch?v=c9AnqCeyxbI\&t=1506s)\" and extract the code that builds an agent from scratch. Feel in any gap. Once you have the complete code, please test it to make sure it works. ask me if any question"

That request contained three distinct obligations. Recover the code shown in a
video. Fill omissions without disguising invented material as Tim's source.
Then test the result rather than handing over an unexecuted transcription.

The user later supplied two pieces of human input that changed the work:

> "i added OPENAI_API_KEY in ./.env"

and then:

> "I added Tim's video transcript. Can you create a tutorial as if Tim is walking through the code. Write in prose and match each of his explanation or concept with the corresponding code segment. Embed the prose in the code as comments. do you think this is the best way to add explanation to the code ? let me know."

The second message changed the deliverable from only a reconstructed program to
a literate program. Each major explanation in the transcript had to sit beside
the code that implements it. The comments also had to remain prose, not become
a forest of terse labels.

The interpretation was deliberately narrow. "As if Tim is walking through the
code" meant preserving his pedagogical sequence and concepts in paraphrase. It
did not mean impersonating him, fabricating quotes, or claiming that added
safety code appeared in the video.

The current request asked for this account using Claude's `dev-journey` skill.
That skill was found locally at
`%USERPROFILE%\.claude\skills\dev-journey\SKILL.md` and used directly. The
skill required failures, rejected alternatives, limits, and unfinished work to
remain visible.

## 2. Cold start — turning a video into auditable source material

The workspace started as a source-recovery task, not an existing software
repository. The initial local transcript was only a tiny URL/chapter-style
stub, about 305 bytes. It was not enough to reconstruct code or align concepts
to individual functions.

The source was therefore acquired in several representations:

- YouTube metadata and description;
- English caption tracks;
- a 130,264,327-byte 1080p video;
- a 346,835,575-byte 4K video-only stream;
- selected high-resolution frames from code-building portions; and
- later, the user's 47,016-byte `transcript.txt`.

The source identity was recorded as Tech With Tim's *Building AI Agents in Pure
Python - Beginner Course*, video ID `c9AnqCeyxbI`, duration 37:24. The evidence
was kept under `evidence/c9AnqCeyxbI/`. `source-manifest.json` records the
canonical URL, retrieval date, extraction method, coverage, and SHA-256 hashes.

The captions explained the ideas, but screenshots were necessary for code
shape. The 4K stream mattered because identifiers, indentation, schema fields,
and message roles are easy to misread at lower resolution. The code-building
sequence was inspected especially around these ranges:

- `03:21-11:50`: first OpenAI Chat Completions request;
- `13:15-17:08`: persistent conversation messages;
- `17:08-28:09`: function schemas and the tool-call protocol;
- `28:09-33:00`: the assembled `agent.py`; and
- `33:00-36:20`: the agent building and debugging a Snake project.

The first hard rule emerged here: **a caption can recover intent; a code frame
is needed to recover syntax.** Neither one alone was enough.

The project was then established as a Python package-shaped workspace using
`pyproject.toml` and `uv.lock`. The tested environment ended at:

- Python `3.14.3`;
- `openai==2.54.0`;
- `httpx==0.28.1`;
- `python-dotenv==1.2.3`; and
- `pytest==9.1.1`.

The directory is not a Git repository. The development-journey instruction to
commit and push therefore did not apply. Nothing was silently published.

## 3. Design decisions

### 3.1 Faithful reconstruction, not fictional byte recovery

Two approaches were possible. One was to present a supposedly exact copy of
the code visible in the video. That would have been cleaner rhetorically and
less honest technically: the API key was blurred, some frames were incomplete,
and captions do not encode punctuation.

The chosen approach preserved the visible architecture and behavior while
labelling every deliberate gap-fill. `SOURCE_NOTES.md` is the boundary ledger.
It says what was directly visible and what was added for a runnable result.

**A reconstruction becomes trustworthy when inference has an address.** Here,
the address is either a video timestamp or an explicit "reconstruction
gap-fill" label.

### 3.2 Keep the video's Chat Completions architecture

The current OpenAI ecosystem offers newer abstractions, including the Responses
API and higher-level agent frameworks. Switching would have produced a more
contemporary sample but a worse reconstruction. The code therefore retains the
video's `client.chat.completions.create(...)` call, `tools` array,
`message.tool_calls`, and `role: "tool"` responses with `tool_call_id`.

The rejected alternatives were LangChain, an agent SDK, and a custom protocol.
All three would hide the mechanism the tutorial is meant to expose.

### 3.3 One model, four tools, one loop

The agent uses the video's deliberately small architecture:

1. Send conversation history and tool schemas to `gpt-5-mini`.
2. Append the assistant message to history.
3. If it contains tool calls, dispatch each local Python function.
4. Append each result with its matching `tool_call_id`.
5. Ask the model again.
6. Stop when the model returns ordinary text.

The four capabilities are `list_files`, `read_file`, `write_file`, and
`run_command`. This is enough for a model to inspect a project, edit it, run a
check, observe the result, and revise.

No planner, retrieval system, vector database, memory service, streaming UI,
parallel execution, or multi-agent layer was added. Those were YAGNI cuts. Each
would make the example more impressive and the agent loop less visible.

### 3.4 Fill operational gaps without changing the lesson

The video demonstrates the happy path. A copied happy path would be fragile in
a real folder, so `agent.py` adds:

- `.env` loading instead of a key literal;
- the current `developer` instruction role instead of the video's `system`
  role;
- a workspace boundary for direct file tools;
- automatic parent-directory creation on nested writes;
- recoverable malformed and unknown tool errors;
- a 20-round default ceiling;
- a 120-second shell-command timeout;
- a fixed shell working directory;
- lazy client construction; and
- interactive plus one-shot command-line modes.

The rejected extreme was turning the reconstruction into a hardened sandbox.
That would require process isolation, command allowlists, resource controls,
and probably containers. The project instead preserves Tim's confirmation gate:
every shell command pauses for an explicit `y`.

The distinction matters. File confinement is a real restriction.
`run_command(..., shell=True)` is not sandboxing. Approval reduces accidental
execution; it does not make an approved command safe.

### 3.5 Separate the clean program from the teaching program

When the transcript arrived, three documentation designs were considered:

1. Put all prose into `agent.py`.
2. Write a separate Markdown tutorial with copied code snippets.
3. Keep `agent.py` clean and create an executable commented twin.

Option 1 gives perfect proximity but makes the working program harder to scan.
Option 2 gives better long-form typography but lets prose and copied snippets
drift away from the real code. Option 3 was chosen: `agent_tutorial.py` contains
the same syntax tree as `agent.py`, with timestamped prose comments beside each
concept.

This hybrid is the best arrangement for this project. Embedded prose comments
are excellent for line-by-line learning. They are not the best sole form of
documentation. `README.md` remains the short operator guide,
`SOURCE_NOTES.md` remains the provenance ledger, and this document records the
process and failures.

### 3.6 Paraphrase the transcript; do not manufacture quotations

The comments follow Tim's explanation order and include timestamps such as
`00:34-03:14`, `28:11-30:24`, and `23:21-23:37`. They explain the model/tool
boundary, JSON schemas, conversation state, the repeated loop, and why ordinary
text is the stopping condition.

Transcript language was paraphrased. This avoids long copied passages and also
corrects the noise inherent in automatic captions. Added material is labelled
`GAP-FILL` or `RECONSTRUCTION GAP-FILL` inside the file.

### 3.7 Prove that the tutorial did not fork the program

Manual comparison was rejected as too weak. Comment-heavy source can conceal a
changed literal, reordered statement, or missing branch.

`tests/test_tutorial.py` parses both files with Python's `ast` module and
compares `ast.dump(..., include_attributes=False)`. Comments disappear from
the abstract syntax tree. Equality therefore proves that the executable Python
structure is identical, while ignoring line numbers and comment placement.

That test turns "the comments are the only difference" from an editorial claim
into an executable invariant.

## 4. The crux — aligning Tim's mental model with executable control flow

The hard part was not adding many comments. It was putting each explanation at
the point where the program makes it true.

The tutorial begins with Tim's big picture before the imports: an agent is a
model that can observe, act through tools, inspect results, and repeat. This
prevents the reader from mistaking an agent for one unusually long prompt.

The imports and constants then establish the runtime. Comments explain why the
model identifier, round ceiling, working directory, and instruction prompt are
configuration rather than the agent itself.

Workspace confinement is documented before `_workspace_path`. This material is
not attributed to Tim. It explains the reconstruction's safety boundary and
why relative paths are resolved beneath the launch directory.

The four Python functions come next because Tim first makes capabilities real.
A model cannot directly read a disk or launch a process. These functions are
ordinary deterministic code. They form the action side of the agent.

`TOOLS` explains dispatch: the function name emitted by the model becomes a
lookup key. `TOOL_SCHEMAS` then explains the other half of the contract. The
model sees JSON descriptions, not Python function objects. Each schema defines
a name, description, argument object, required fields, and a ban on extra
properties.

The SDK compatibility helpers are explicitly marked as reconstruction. Their
job is to accept both dictionary-shaped test doubles and attribute-based OpenAI
SDK objects. That keeps deterministic tests simple without rewriting runtime
logic for the test suite.

`run_tool` sits exactly where textual intention crosses into local side effect.
Its comments follow the sequence: locate the function object, parse JSON
arguments, reject malformed input, look up the tool, execute it, and return a
string observation. Failures go back to the model as observations so it may
recover.

`run_agent` contains the actual agent. Its comments number the loop:

1. Ask the model what to do next.
2. Preserve the assistant message.
3. Stop if there are no tools.
4. Otherwise execute every requested tool.
5. Attach results to the correct call IDs.
6. Repeat with the enlarged history.

The outer `main` loop is then distinguished from the inner loop. The outer loop
handles human turns. The inner loop handles autonomous model/tool rounds for
one human request. Mixing those two loops is a common beginner confusion, so
the tutorial treats the separation as a first-class concept.

The central lesson is visible in code rather than stated abstractly:
**tool results become new context, and new context lets the model choose the
next action.** That feedback cycle is the agent.

## 5. Tools and features used

| Tool or feature | What it did in this session |
|---|---|
| YouTube URL and metadata | Established source identity, publication data, duration, and chapter timing. |
| `yt-dlp` acquisition | Retrieved captions, metadata, a 1080p video, and a 4K stream for inspection. |
| High-resolution frame inspection | Recovered code structure and identifiers that captions could not contain. |
| `transcript.txt` | Supplied the full timestamped explanation used to align prose comments to code. |
| PowerShell and `rg` | Inventoried files, searched headings, inspected exact versions, and checked local skill locations. |
| `uv` | Resolved the Python environment, produced `uv.lock`, and ran the project and tests. |
| OpenAI Python SDK `2.54.0` | Implemented the same Chat Completions/tool-call protocol used by the reconstructed agent. |
| `httpx.MockTransport` | Exercised real SDK serialization and parsing without spending API credits. |
| `pytest 9.1.1` | Verified tool behavior, loop behavior, failure handling, and tutorial parity. |
| Python `ast` | Proved that `agent_tutorial.py` and `agent.py` have identical executable structure. |
| SHA-256 manifests | Bound sources and outputs to exact bytes and exposed later drift. |
| Claude `dev-journey` skill | Supplied the structure and required this account to preserve failures, limits, rejected alternatives, and unfinished work. |
| Codex skill discovery | Located the Claude skill after it was absent from Codex's advertised skill catalog. |

No subagents were spawned. The source analysis, reconstruction, commentary,
tests, and this retrospective were performed inline in one task. The coding
agent being built defaults to `gpt-5-mini`; that is not a claim about the host
model running this development session.

## 6. What went wrong, and the fixes

### 6.1 The starting transcript was not a transcript

The first local text was only a short URL/chapter artifact, roughly 305 bytes.
Treating it as complete would have produced a concept summary with guessed
code.

The fix was to acquire captions and video, then inspect the code-building
sections visually. When the user later added the full transcript, it became the
primary commentary source and was hashed into `source-manifest.json`.

Near-miss: captions plus general Python knowledge could have produced plausible
code quickly. Plausible is not source-grounded. The manifest and timestamp
notes prevented that shortcut from being presented as extraction.

### 6.2 The API key could not be recovered from the video

The video's key was blurred, as it should be. Hard-coding a placeholder or
copying a secret into source would have created both a broken example and a
security failure.

The fix was `.env` plus `python-dotenv`, with `.env` excluded in `.gitignore`.
Only `.env.example` was made distributable. The user's manual addition of
`OPENAI_API_KEY` was a necessary human-in-the-loop step.

Near-miss avoided: validation commands inspected the presence and behavior of
the key, not its value. The secret is not stored in any manifest or this doc.

### 6.3 The first test collection could not import the module

The initial test run failed with:

```text
ModuleNotFoundError: No module named 'agent'
```

The project root was not on pytest's import path in that invocation. The fix
was the explicit setting in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

The lesson was simple: **a green implementation cannot exist before the test
runner can import it. Test collection is part of the test.**

### 6.4 A funded live model response was unavailable

After the user added `.env`, the one-shot CLI successfully loaded the key and
reached OpenAI's Chat Completions endpoint with `gpt-5-mini`. The service
returned HTTP `429` with the error code:

```text
credit_balance_exhausted
```

The exact full response wrapper is no longer present after transcript
compaction, so it is not reconstructed here as a fake verbatim block. The
durable `TEST_REPORT.md` records the code and its interpretation: the selected
API project had no remaining credits.

The code could not fix account billing. Instead, the test suite added a real
OpenAI SDK round trip through `httpx.MockTransport`. This verified request
serialization, four transmitted tool schemas, SDK response parsing, the
tool-result message, and the second model round without contacting OpenAI.

Important boundary: that is strong protocol verification, but it is not a live
model response. The project says so.

### 6.5 Mock objects could have hidden an SDK incompatibility

The first deterministic loop tests used small fake message objects. They were
excellent for controlling one tool call, several calls, and infinite loops.
They could still have passed while the actual OpenAI SDK serialized something
differently.

The fix was not to discard the fakes. It was to add one integration-shaped test
using the real `OpenAI` client against a local mock transport. Unit control and
SDK realism now cover different failure surfaces.

### 6.6 The tutorial could silently drift from the runnable agent

Duplicating `agent.py` to add commentary created a maintenance hazard. A copied
file can diverge after one innocent edit.

The AST parity test was the fix. It failed by design if executable syntax in
one file ceased to match the other. Hashes for both files were also recorded in
`artifact-manifest.json`.

### 6.7 The transcript arrived after the runnable reconstruction

The first pass necessarily used captions, video frames, and visible code. The
user's later full transcript could have been treated as merely supplemental.
That would have missed the user's actual request to make Tim's conceptual
sequence drive the tutorial.

The code was reread against `transcript.txt`. Commentary sections were placed
around the matching program regions, timestamps were added, and reconstruction
material was marked separately. The executable program was not rewritten to
make the prose easier.

### 6.8 The requested skill appeared missing

`dev-journey` was absent from the provided Codex skill catalog. A local search
of the Codex and agent skill roots found no match, and `npx skills find
dev-journey` returned unrelated public skills such as `journey` and
`journey-mapping`.

A final check of Claude's own configuration found the exact requested file at
`%USERPROFILE%\.claude\skills\dev-journey\SKILL.md`. The workflow switched to
that instruction file. No substitute was installed and no public package was
misrepresented as Claude's skill.

## 7. Verification

The final deterministic command was:

```powershell
uv run pytest
```

The recorded result was:

```text
9 passed
```

The nine tests establish these observed properties:

1. A plain assistant response stops the inner loop without calling tools.
2. One tool result is attached to the right `tool_call_id` and sent back.
3. Multiple tool calls in a single model response execute in order.
4. File listing, reading, nested writing, UTF-8 behavior, and rejection of
   `../outside.txt` work in a temporary workspace.
5. A declined shell command never reaches the command runner; an approved one does.
6. An unknown tool becomes a recoverable error string.
7. Repeated tool calls hit the configured round ceiling instead of looping forever.
8. The real OpenAI SDK works through a local two-round mock transport.
9. The tutorial's AST equals the canonical program's AST.

The source manifest was separately validated against its recorded evidence
hashes. The artifact manifest was validated against seven output files before
this development-journey document was added. This document and the changed
README are rehashed as part of the current update.

What was not verified:

- No funded live OpenAI response completed because the API project returned
  `credit_balance_exhausted`.
- Therefore, no live model-selected tool call completed over the public API.
- Byte-for-byte identity with Tim's private or unpublished source was neither
  possible nor claimed.
- The shell tool was not promoted as a security sandbox.
- No Git commit or remote publication was tested because this folder has no
  `.git` repository.

Costs and limits were also recorded. No dollar cost was measured. The live API
attempt consumed no successful completion because the credit balance was
exhausted. Source acquisition stored at least 477,099,902 bytes across the two
video files, before captions, metadata, thumbnails, and local source files.
The agent's safety ceilings are 20 model/tool rounds and 120 seconds per
approved command unless configuration changes them.

## 8. Where things stand

`agent_tutorial.py` is complete as a transcript-grounded, executable tutorial.
It preserves the behavior of `agent.py` and places Tim's concepts next to the
corresponding implementation. The comments distinguish source explanation from
reconstruction gap-fills.

The durable knowledge stores are:

- `agent_tutorial.py`: the line-by-line teaching artifact;
- `agent.py`: the clean runnable version;
- `README.md`: setup, operation, safety, and documentation entry points;
- `SOURCE_NOTES.md`: timestamped source coverage and inference boundary;
- `TEST_REPORT.md`: deterministic, SDK-level, and blocked-live evidence;
- `source-manifest.json`: exact source provenance and hashes;
- `artifact-manifest.json`: exact output purposes, dependencies, and hashes;
- `tests/test_agent.py`: behavioral and protocol checks;
- `tests/test_tutorial.py`: the comments-only parity invariant; and
- `DEVELOPMENT-JOURNEY.md`: this session reconstruction and audit trail.

One external item remains unfinished. A real model response and public-API tool
round still require credits on the OpenAI API project associated with the
user's key. Once funded, the concrete check is:

```powershell
uv run python agent.py --prompt "Use list_files on the current directory, then summarize what you see."
```

The deliverable stands without that check because the local behavior and real
SDK protocol path are covered deterministically. It should not, however, be
described as live-end-to-end verified until that command returns a model answer
and a real `list_files` tool round is observed.

Future edits should change `agent.py` first, mirror the executable change into
`agent_tutorial.py`, update the nearby explanation if necessary, run all tests,
and refresh affected hashes. If the AST parity test fails after a comment-only
edit, stop: the tutorial has accidentally become a different program.
