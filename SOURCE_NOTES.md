# Source and reconstruction notes

## Source

- Video: Tech With Tim, *Building AI Agents in Pure Python - Beginner Course*
- URL: <https://www.youtube.com/watch?v=c9AnqCeyxbI>
- Published: 2026-08-30 (YouTube metadata)
- Duration: 37:24
- Retrieved: 2026-08-31 in America/Los_Angeles

Coverage: full metadata and audio/captions; substantial visual inspection of the
code-building sequences using the downloaded 4K video; timestamp-addressable.

## What is directly visible

- `03:21-11:50`: an OpenAI Chat Completions call using `gpt-5-mini` and a list of
  messages.
- `13:15-17:08`: conversation history stored by appending user and assistant
  messages.
- `17:08-28:09`: JSON function schemas, `message.tool_calls`, `json.loads` of
  function arguments, execution of Python tools, and `role: tool` results tied
  back with `tool_call_id`.
- `28:09-33:00`: the final `agent.py`: imports; client/model; system prompt;
  `list_files`, `read_file`, `write_file`, and confirmed `run_command`; `TOOLS`;
  four schemas; `run_tool`; repeated model/tool loop; interactive `main`.
- `33:00-36:20`: live demonstrations in which the agent inspects the folder,
  creates a Snake project, runs commands with confirmation, fixes errors, and
  completes the task.

## Reconstruction boundary

`agent.py` preserves the visible architecture and visible tool behavior. The
following are deliberate gap-fills, not claims about the video's exact source:

- API key comes from `.env`/`OPENAI_API_KEY`; the video's literal key is blurred.
- The instruction message uses the current `developer` role rather than the
  video's `system` role.
- Direct file access is limited to the launch workspace.
- Parent directories are created when writing a nested file.
- Tool parsing handles dictionaries and SDK objects and returns errors to the
  model instead of crashing.
- The loop has a configurable 20-round ceiling.
- The OpenAI client is created lazily so imports and tests do not require a key.
- A one-shot command-line mode and deterministic mocked tests were added.

The final source is therefore a faithful, runnable reconstruction, not a claim
of byte-for-byte recovery from the creator's repository.
