# Tests explained

This document explains what the test suite proves, what it does not prove, and
how much confidence it should provide. The short answer is: the tests are good
for the educational core of this agent, but they are not a production-readiness
certificate.

## Test environment and commands

The current deterministic suite was run on 2026-08-31 with:

- Python `3.14.3`;
- `pytest==9.1.1`;
- `openai==2.54.0`;
- `httpx==0.28.1`; and
- `python-dotenv==1.2.3`.

The ordinary test command is:

```powershell
uv run pytest
```

The observed result was:

```text
9 passed
```

Wall-clock duration varies by machine and cache state, so the durable assertion
is the pass count rather than one timing sample.

Branch coverage was measured separately with Coverage.py `7.16.0`:

```powershell
uv run --with coverage coverage run --branch --source=agent --data-file=.coverage-doc-audit -m pytest
uv run --with coverage coverage report --data-file=.coverage-doc-audit -m
```

The measurement reran all nine tests successfully and reported:

```text
Name       Stmts   Miss Branch BrPart  Cover
-------------------------------------------------
agent.py     131     45     34      6    63%
-------------------------------------------------
TOTAL        131     45     34      6    63%
```

The temporary coverage data file was removed after the report. Coverage.py was
used transiently; it was not added to the project's locked dependencies.

## How the test harness works

Most tests do not call OpenAI. They construct deterministic stand-ins for the
small portion of the API used by `run_agent`.

`FakeMessage` behaves like an assistant message. It stores normal text and an
optional list of tool calls. Its `model_dump` method produces the dictionary
shape that the application appends to conversation history.

`tool_call(...)` constructs an object containing a call ID, function name, and
JSON-encoded arguments. This mirrors the fields the OpenAI SDK exposes without
asking a model to generate them.

`FakeCompletions` returns a predetermined sequence of messages and logs every
request. A test can therefore say, in effect, "first request a tool, then answer
normally" and inspect both the result and the intermediate conversation.

`fake_client(...)` wraps those completions in the same
`client.chat.completions` shape used by the program.

Temporary directories supplied by pytest keep file-writing tests away from the
real project. The command test injects a fake confirmation function and a fake
runner, so it can prove whether execution would occur without launching an
actual process.

One test deliberately does use the real OpenAI Python SDK. It replaces the
network with `httpx.MockTransport`, allowing the test to inspect the SDK's JSON
request and return controlled Chat Completions responses locally.

## The nine tests

### 1. `test_plain_text_response_stops_without_tools`

This is the simplest stopping case. The fake model returns `"Done"` with an
empty tool-call list.

It verifies that:

- `run_agent` returns the assistant's text;
- the model is called exactly once; and
- the assistant message is appended to conversation history.

This test protects the rule that ordinary model text ends the inner agent loop.
It does not test missing content, malformed choices, streaming responses, or an
API exception.

### 2. `test_tool_result_is_returned_to_model`

The test creates `alpha.txt` in a temporary workspace. The first fake model
message requests `list_files`. The second returns a final answer.

It verifies that:

- the requested Python tool actually runs;
- the observed result is `alpha.txt`;
- the result is stored as a `role: "tool"` message;
- the original call ID, `call-1`, becomes `tool_call_id`;
- the model is called a second time with the enlarged history; and
- the second assistant response becomes the final return value.

This is the central agent-cycle test. It checks observation, action, feedback,
and termination in one controlled example.

### 3. `test_multiple_tool_calls_in_one_round`

The fake model requests two tools in the same response. It first writes
`note.txt`, then reads that file.

It verifies that:

- all tool calls in a response are executed;
- their order is preserved;
- `write_file` creates the expected content;
- `read_file` sees the just-written content; and
- both results are appended before the next model round.

It does not test parallel tool execution, partial failure among several calls,
or conflicting writes. The implementation is intentionally sequential.

### 4. `test_file_tools_are_confined_to_workspace`

This test sets a temporary workspace, writes `nested/hello.txt`, reads it back,
and lists the root directory. It then attempts to read `../outside.txt`.

It verifies that:

- parent directories are created automatically;
- UTF-8 text survives a write/read round trip;
- directories are shown with a trailing slash; and
- a simple `..` traversal outside the workspace raises `ValueError`.

This is a valuable safety regression test, but it is not a complete filesystem
security audit. It does not exercise symlinks, Windows junctions, UNC paths,
absolute paths, race conditions, permission failures, deleted files, binary
files, non-UTF-8 input, or very large content.

### 5. `test_command_requires_confirmation`

The test supplies a fake command runner and controls the answer to the approval
prompt.

It verifies that:

- answering `n` returns a refusal message;
- the runner is never called after refusal;
- answering `y` invokes the runner; and
- standard output is returned to the agent.

It does not launch a real shell. It therefore does not verify the working
directory, quoting behavior, PowerShell-versus-CMD differences, exit codes,
combined standard output and error, empty output, the 120-second timeout, or
process cleanup.

Most importantly, this is an approval test, not a sandbox test. An approved
shell command still has the user's operating-system permissions.

### 6. `test_unknown_tool_error_is_recoverable`

The test asks for a nonexistent tool named `not_a_tool`.

It verifies that `run_tool` returns an error string containing `unknown tool`
instead of crashing the entire program. Returning the failure to the model
gives the model an opportunity to correct its action.

It does not cover invalid JSON, a JSON value that is not an object, missing
arguments, unexpected arguments, wrong argument types, or an exception raised
inside each real tool.

### 7. `test_round_limit_prevents_infinite_loop`

The fake model requests a tool twice and never produces a normal answer. The
test runs the agent with `max_tool_rounds=2`.

It verifies that the loop raises a clear `RuntimeError` after the configured
number of rounds. This prevents an accidental unbounded sequence of API calls
and tool executions.

It does not test zero or negative limits, cancellation during a round, token or
cost budgets, elapsed-time budgets, or retries after transient API failures.

### 8. `test_real_openai_sdk_round_trip_with_mock_transport`

This is the suite's strongest protocol test. It creates a real `OpenAI` client
whose HTTP traffic goes to a local `httpx.MockTransport` handler.

The first synthetic HTTP response asks for `list_files`. The application runs
the tool. The second response says `Saw visible.txt`.

It verifies that:

- the real SDK accepts the request assembled by `run_agent`;
- all four JSON tool schemas are serialized into the first HTTP request;
- the SDK parses a Chat Completions tool-call response;
- the local tool result is sent in the next request with the right call ID; and
- a second SDK response becomes the final answer.

This closes an important gap left by permissive hand-written fakes. It still
does not test authentication, DNS, TLS, latency, rate limits, OpenAI service
behavior, model quality, or whether `gpt-5-mini` chooses sensible tools.

### 9. `test_tutorial_comments_do_not_change_the_program`

This test parses both `agent.py` and `agent_tutorial.py` into Python abstract
syntax trees and compares them after removing position metadata.

Python comments do not appear in an AST. Equality therefore verifies that the
tutorial and canonical files contain the same executable Python structure.

This is a strong and elegant check for the chosen documentation design. It does
not assess whether the comments are correct, complete, readable, faithful to
the transcript, or placed beside the best code segment. Those are editorial
and provenance questions, not syntax-tree properties.

## What the suite does not test

The largest untested area is the command-line shell around the core agent:

- `create_client` with a missing or present environment key;
- argument parsing for interactive and `--prompt` modes;
- `exit` and `quit` handling;
- printed output and process return codes;
- OpenAI exception handling in both CLI modes; and
- the module's `if __name__ == "__main__"` entry point.

Other important gaps are:

- a funded, live OpenAI response and live model-selected tool call;
- malformed or incomplete API responses;
- invalid JSON and invalid tool argument shapes;
- command timeout, failure, standard-error, and no-output branches;
- empty-directory and non-directory behavior in `list_files`;
- filesystem permissions, symlinks, junctions, races, and large files;
- prompt injection through file contents or tool output;
- destructive-but-approved commands;
- concurrent callers and mutation of the global `WORKSPACE_ROOT`;
- Python `3.10` through `3.13`, even though the package declares `>=3.10`;
- macOS and Linux behavior; and
- compatibility across the allowed future `openai>=2.0,<3.0` range.

The test suite also does not measure whether the agent solves useful coding
tasks. Behavioral evaluation would require a corpus of tasks, success criteria,
repeat runs, model/version recording, cost and latency measurements, and a safe
execution environment. That is a different layer from unit and protocol tests.

## Coverage assessment

The measured 63% branch coverage is moderate. It is not poor for a compact
tutorial whose untested lines are concentrated in the interactive CLI, but it
is too low to support a claim of production readiness.

The covered code is more important than the raw percentage suggests. The suite
exercises the core feedback loop, single and multiple tool calls, conversation
protocol, real filesystem changes in temporary directories, path traversal
rejection, command approval, unknown-tool recovery, loop termination, real SDK
serialization, and tutorial parity. Those are the highest-value invariants of
the example.

The uncovered branches are also meaningful. Coverage reported missing behavior
around absolute-path handling, the non-directory error, command timeout,
dictionary and fallback message conversions, non-object JSON arguments,
`create_client`, almost all of `main`, and direct module execution. A percentage
alone would hide that concentration.

Coverage was measured only for `agent.py`. `agent_tutorial.py` was intentionally
excluded because running the same tests against a duplicate file would inflate
the number without adding confidence. Its executable equivalence is checked by
AST parity instead.

## Quality assessment

Overall rating: **good educational regression suite; insufficient production
assurance**.

Strengths:

- Tests are deterministic, fast, and require no paid API access.
- Temporary directories isolate normal file side effects.
- Dependency injection makes command approval testable without a subprocess.
- The suite verifies message history, not merely final strings.
- Multiple tool calls and the infinite-loop guard cover nontrivial control flow.
- A real SDK plus mock transport tests the boundary that hand-written fakes may
  misrepresent.
- AST parity is precisely matched to the two-file documentation strategy.

Weaknesses:

- The CLI and client-construction code have almost no automated coverage.
- Error-path testing is narrow; only unknown tools and the loop ceiling are
  deliberate failures.
- The command test's fake runner cannot reveal platform or subprocess bugs.
- The global workspace root is mutated directly and not restored by a fixture.
  The current tests remain independent because each relevant test sets its own
  temporary root, but a fixture would make that invariant safer.
- Mock model responses are structurally simple and may be more cooperative than
  real or future SDK objects.
- There is no security test suite, fuzzing, property-based testing, load test,
  or model-behavior evaluation.
- The stated Python and dependency ranges are broader than the tested matrix.

## Highest-value next tests

If the project is extended, the next tests should be added in this order:

1. Test malformed JSON, non-object JSON, missing arguments, and tool exceptions
   as recoverable observations.
2. Test `run_command` timeout, standard error, nonzero exit, empty output, and
   the exact temporary working directory.
3. Test `create_client` and both CLI modes by controlling environment variables,
   arguments, input, output, and OpenAI errors.
4. Test empty and invalid directories, absolute in-workspace paths, symlinks or
   Windows junctions, and permission failures.
5. Run a small Python-version and operating-system matrix.
6. After API credits are available, add an opt-in live smoke test that records
   the model, request ID, elapsed time, and cost without making it part of the
   deterministic default suite.
7. For any production use, replace the approved unrestricted shell with a real
   sandbox and build adversarial security tests around that boundary.

Adding tests merely to raise 63% would be the wrong goal. The next test should
target the next plausible failure, especially one that could execute an unsafe
action, corrupt a file, hide an API incompatibility, or spend money in a loop.
