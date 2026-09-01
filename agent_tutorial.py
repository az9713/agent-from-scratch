"""A small coding agent reconstructed from Tech With Tim's pure-Python tutorial.

The model gets four local tools and may call them repeatedly until it returns a
plain-text answer. File access is confined to the workspace used at launch.
Shell commands always require an explicit confirmation.
"""

# TIM'S BIG PICTURE — 00:34-03:14
#
# Before we touch the implementation, keep one compact mental model in mind.
# An agent is a model, a set of tools, and a loop. The model is the reasoning
# engine, but by itself it only generates text. The tools are ordinary pieces
# of software—here, Python functions—that can affect the outside world. The
# loop lets the model ask for a tool, inspect its result, and decide what to do
# next. Conversation history supplies the context that makes those decisions
# coherent across many turns.
#
# This file follows that same progression. It is the runnable `agent.py` with
# tutorial comments added; the comments are paraphrased from Tim's transcript.
# Timestamp labels point to the corresponding explanation in the video.

from __future__ import annotations

# PROJECT SETUP AND IMPORTS — 03:21-05:24 and 19:47-20:03
#
# Tim creates a small UV project and installs the OpenAI Python package. The
# package is not an agent framework; it is simply a convenient client for the
# API. `json`, `os`, and `subprocess` come with Python. JSON decodes the model's
# tool arguments, OS/path utilities operate on files, and subprocess executes a
# command only after our harness approves it.
#
# `argparse`, `pathlib`, typing helpers, and dotenv are gap-fills in this tested
# reconstruction. They give us a usable command line, safer paths, clear type
# contracts, and environment-based secret loading without changing the agent's
# model-tools-loop architecture.

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


# MODEL CONFIGURATION AND SECRETS — 06:47-07:27, 10:24-11:38, 29:03-29:42
#
# Every agent needs a model it can call. Tim keeps the model name in one place
# so it is easy to switch where requests go. He demonstrates `gpt-5-mini`.
#
# He also warns that an API key should not be exposed and is better stored in
# an environment variable. We follow that safer path: dotenv reads the local
# `.env`, while Git ignores that file. No key is embedded in this source.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

# GAP-FILL: Tim describes an agent as able to loop indefinitely, but an actual
# program needs a failure boundary. Twenty model/tool rounds are ample for the
# tutorial and prevent a confused model from consuming unbounded time or money.
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "20"))

# GAP-FILL: Tim says the working directory is the folder from which the agent
# was launched. We turn that statement into an enforceable file boundary.
WORKSPACE_ROOT = Path.cwd().resolve()

# SYSTEM INSTRUCTIONS — 08:54-09:46 and 29:28-29:42
#
# Tim explains three message roles. A user message contains the human's input;
# an assistant message records what the model said; and the initial instruction
# tells the model what kind of assistant it is and what capabilities it has.
# This prompt says that our model is a coding agent and names its four tools.

SYSTEM_PROMPT = """You are a coding agent running in the user's terminal.
You can list files, read files, write files, and run shell commands.
Use your tools to complete the user's task, then briefly summarize what you did.
The working directory is the folder the user launched you from.
Never access files outside that working directory."""


# WORKSPACE CONFINEMENT — RECONSTRUCTION GAP-FILL
#
# The video focuses on the happy-path mechanism. These two helpers add a safety
# property: direct file tools may operate only inside the launch folder. Tests
# can also point the boundary at a temporary directory without touching real
# project files.

def set_workspace_root(path: str | Path) -> None:
    """Set the workspace boundary. Primarily useful for embedding and tests."""

    global WORKSPACE_ROOT
    WORKSPACE_ROOT = Path(path).resolve()


def _workspace_path(path: str = ".") -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = WORKSPACE_ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path is outside the workspace: {path}") from exc
    return resolved


# THE FOUR REAL TOOLS — 28:11-30:24
#
# These are ordinary Python functions. This distinction is central to Tim's
# explanation: the language model never reaches into the filesystem or runs a
# command itself. It can only emit text saying which tool it would like to use.
# Our Python harness decides whether and how that request becomes real action.

def list_files(path: str = ".") -> str:
    # Tim's first tool gives the model a view of a directory. We append `/` to
    # directory names so the model can distinguish folders from files.
    directory = _workspace_path(path)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    entries = []
    for entry in os.scandir(directory):
        entries.append(entry.name + ("/" if entry.is_dir() else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"


def read_file(path: str) -> str:
    # TOOL-CALLING FOUNDATION — 19:53-20:14
    # Tim begins with this simplest example: accept a path and return the text
    # in that file. Returning the result matters because it becomes new context
    # that the model can reason over in its next API call.
    return _workspace_path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    # The model supplies both a path and the complete desired contents. Tim
    # notes at 28:31-28:44 that overwriting a file can also be destructive and
    # deserves a guardrail in a production system. His tutorial leaves that
    # approval step out; this reconstruction instead confines writes to the
    # workspace and creates missing parent folders.
    target = _workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Saved {path} ({len(content)} characters)"


def run_command(
    command: str,
    *,
    confirm: Callable[[str], str] | None = None,
    runner: Callable[..., Any] | None = None,
) -> str:
    """Run a command in the workspace after the user explicitly approves it."""

    # COMMAND GUARDRAIL — 18:44-19:40 and 29:49-30:18
    # A shell command may install software, create directories, or execute code,
    # so the harness asks the human before it acts. Notice where the permission
    # check lives: in deterministic Python, not in a hope that the model will
    # restrain itself. If the user says no, that refusal itself becomes a tool
    # result the model can observe and adapt to.
    confirm = confirm or input
    runner = runner or subprocess.run
    answer = confirm(f"  Run '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."

    try:
        result = runner(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=WORKSPACE_ROOT,
        )
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 120 seconds."

    # Both standard output and errors are useful observations for the model. A
    # silent command still returns its exit code so the next step is informed.
    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


# TOOL DISPATCH TABLE — 30:24-30:39
#
# The model will return a tool name as text, such as `read_file`. This dictionary
# is the bridge from that text name to the real Python function. Later,
# `run_tool` can select `TOOLS[name]` rather than writing a long if/elif chain.

TOOLS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}

# TOOL SCHEMAS: THE MODEL'S MENU — 17:08-18:19, 20:14-21:38, 30:39-31:11
#
# The dictionary above is for Python; the schemas below are for the model. Tim
# emphasizes that the model cannot see a Python function. It sees a structured
# description of each tool: its name, what it does, and the arguments it needs.
# Accurate names and descriptions are therefore not cosmetic—they steer when
# and how the model chooses a capability.
#
# Every schema says this tool is a function. `parameters` is a JSON Schema
# object. `properties` describes the available arguments, and `required` says
# which ones must be present. The four blocks are repetitive because we are
# deliberately building without a framework that would generate them for us.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the files in a directory. Folders end with /.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to list, e.g. '.'",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to read",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a UTF-8 text file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full contents of the file",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return its output. The user approves it first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run",
                    }
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
]


# SDK COMPATIBILITY HELPERS — RECONSTRUCTION GAP-FILL
#
# Tim's on-screen code works directly with OpenAI SDK objects. Tests and other
# callers may also provide plain dictionaries. These helpers normalize both
# representations. They preserve the *whole* assistant message—especially its
# tool calls—because Tim explains at 22:32-23:21 that saving only human-readable
# content would throw away the model's requested actions.

def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _assistant_message(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    if isinstance(message, dict):
        return message

    data: dict[str, Any] = {
        "role": "assistant",
        "content": getattr(message, "content", None),
    }
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        data["tool_calls"] = tool_calls
    return data


# EXECUTING ONE REQUESTED TOOL — 23:29-24:03 and 31:11-31:38
#
# A tool call arrives with three important pieces: a unique ID, a function
# name, and arguments encoded as JSON text. Again, the model has not performed
# the action—it has merely proposed a structured action. Here is the glue that
# turns that proposal into a real Python call.

def run_tool(tool_call: Any) -> str:
    try:
        function = _field(tool_call, "function")
        name = _field(function, "name")

        # Convert the model's JSON string, for example `{"path":"notes.txt"}`,
        # into a Python dictionary that can be expanded as keyword arguments.
        raw_arguments = _field(function, "arguments")
        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise TypeError("tool arguments must be a JSON object")
        if name not in TOOLS:
            raise KeyError(f"unknown tool: {name}")

        # The visible log makes the harness's activity legible to the user.
        print(f"  tool: {name}({arguments})")
        return str(TOOLS[name](**arguments))

    # ERROR AS OBSERVATION — 24:23-25:46 and 31:31-31:38
    # Tim demonstrates a missing file. Crashing would terminate the agent, but
    # returning the error gives the model information it can reason about. It
    # may try another path, ask the user, or explain what is missing.
    except Exception as error:  # Return tool failures to the model so it can recover.
        return f"Error: {error}"


# THE INNER AGENT LOOP — 01:50-02:43, 23:21-27:59, 31:38-32:40
#
# Tim calls this function “one run” of the agent: one user request may require
# many model calls and many tool calls. The loop continues until the model gives
# a normal answer with no more requested tools.

def run_agent(
    messages: list[dict[str, Any]],
    client: Any,
    *,
    model: str = MODEL,
    max_tool_rounds: int = MAX_TOOL_ROUNDS,
) -> str:
    for _ in range(max_tool_rounds):
        # STEP 1: CALL THE MODEL — 05:24-08:08 and 21:45-22:32
        # `messages` is the full context assembled so far. `tools` is the menu
        # of allowed structured actions. The API returns text, a list of tool
        # calls, or both; it still executes none of those tools itself.
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message

        # STEP 2: PRESERVE THE MODEL'S ENTIRE MESSAGE — 23:03-23:21
        # This records assistant text and any tool-call IDs/arguments. It is the
        # durable conversation trace that the next API call must see.
        messages.append(_assistant_message(message))

        tool_calls = _field(message, "tool_calls")

        # STEP 3A: NO TOOLS MEANS THIS RUN IS FINISHED — 23:21-23:37
        # A plain-text response is the model signalling that it has reached an
        # answer for the current user prompt, so we leave the inner loop.
        if not tool_calls:
            return _field(message, "content") or ""

        # STEP 3B: EXECUTE EVERY REQUESTED TOOL — 23:29-24:03, 27:19-27:53
        # One assistant message may request several independent tools. We run
        # each and attach each result to its unique call ID.
        for tool_call in tool_calls:
            result = run_tool(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": _field(tool_call, "id"),
                    "content": result,
                }
            )

        # There is no explicit `continue` because reaching the end naturally
        # starts the next iteration. The model now sees its previous request
        # plus the actual tool results and can choose its next action.

    # GAP-FILL: a finite ceiling converts a runaway agent into a clear error.
    raise RuntimeError(f"Agent exceeded {max_tool_rounds} model/tool rounds")


# CREATE THE API CLIENT — 03:21-04:59 and 10:24-11:24
#
# Client construction is delayed until execution so importing the module and
# running offline tests do not require a secret. The OpenAI client reads the
# key loaded from `.env`. A valid key and API credits are separate requirements.

def create_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add a key, "
            "or set it in your shell environment."
        )
    return OpenAI()


# THE OUTER CONVERSATION LOOP — 13:18-17:01 and 32:40-33:26
#
# The inner loop completes one task. This outer loop lets the human start task
# after task while retaining the same message history. Tim's memory experiment
# is crucial here: models do not remember prior API calls. “Memory” is our code
# resending the accumulated messages every time. The list is the active context
# window; context engineering is the later problem of deciding what belongs in
# it when it grows too large.

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reconstructed mini coding agent.")
    parser.add_argument("--prompt", help="Run one prompt non-interactively, then exit.")
    args = parser.parse_args()

    try:
        client = create_client()
    except RuntimeError as error:
        print(f"Error: {error}")
        return 2

    # Current OpenAI guidance uses the `developer` role for application-level
    # instructions on newer models. Tim's video shows the older `system` label;
    # the conceptual job is the same: seed the conversation with instructions
    # that should govern every subsequent turn.
    messages: list[dict[str, Any]] = [
        {"role": "developer", "content": SYSTEM_PROMPT}
    ]

    # One-shot mode is a reconstruction convenience for scripts and smoke tests.
    if args.prompt:
        messages.append({"role": "user", "content": args.prompt})
        try:
            print(run_agent(messages, client))
        except OpenAIError as error:
            print(f"OpenAI API error: {error}")
            return 1
        return 0

    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break

        # USER MESSAGE — 14:51-15:14
        # Append what the human just asked before calling the model. Because the
        # same list survives the loop, earlier user, assistant, and tool messages
        # remain available as context on the next turn.
        messages.append({"role": "user", "content": user_input})
        try:
            reply = run_agent(messages, client)
            print(f"\nAgent: {reply}")
        except OpenAIError as error:
            print(f"\nOpenAI API error: {error}")
    return 0


# Standard Python entry-point guard: importing this file exposes its functions
# without launching an interactive terminal; executing it starts `main`.
if __name__ == "__main__":
    raise SystemExit(main())
