# Test report

Tested on 2026-08-31 from the project root.

## Deterministic verification

Command: `uv run pytest`

Result after adding the transcript-grounded tutorial: **9 passed**.

Coverage includes:

- plain assistant response and stopping condition;
- one tool call followed by a final answer;
- multiple tool calls in one model response;
- conversation/tool-result formatting with `tool_call_id`;
- actual OpenAI Python SDK request serialization and response parsing through a
  local mock transport;
- UTF-8 file listing, reading, and writing;
- rejection of paths outside the workspace;
- mandatory shell-command approval;
- recoverable unknown-tool errors;
- maximum-round protection against an infinite agent loop.
- syntax-tree parity proving that `agent_tutorial.py` differs from `agent.py`
  only by comments.

## Live OpenAI verification

The one-shot CLI loaded the locally supplied `.env` key and reached the OpenAI
Chat Completions endpoint with `gpt-5-mini`. OpenAI returned HTTP 429 with
`credit_balance_exhausted`: the selected API project has no credits remaining.
No live model response or live tool call could therefore complete.

This is an external account-billing limitation. The same model/tool request
path is covered offline using the real OpenAI Python SDK. After credits are
added, rerun:

```powershell
uv run python agent.py --prompt "Use list_files on the current directory, then summarize what you see."
```

See `TESTS-EXPLAINED.md` for a test-by-test explanation, measured branch
coverage, untested behavior, and a critical assessment of suite quality.
