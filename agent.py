"""A small coding agent reconstructed from Tech With Tim's pure-Python tutorial.

The model gets four local tools and may call them repeatedly until it returns a
plain-text answer. File access is confined to the workspace used at launch.
Shell commands always require an explicit confirmation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "20"))
WORKSPACE_ROOT = Path.cwd().resolve()

SYSTEM_PROMPT = """You are a coding agent running in the user's terminal.
You can list files, read files, write files, and run shell commands.
Use your tools to complete the user's task, then briefly summarize what you did.
The working directory is the folder the user launched you from.
Never access files outside that working directory."""


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


def list_files(path: str = ".") -> str:
    directory = _workspace_path(path)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    entries = []
    for entry in os.scandir(directory):
        entries.append(entry.name + ("/" if entry.is_dir() else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"


def read_file(path: str) -> str:
    return _workspace_path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
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

    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


TOOLS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}

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


def run_tool(tool_call: Any) -> str:
    try:
        function = _field(tool_call, "function")
        name = _field(function, "name")
        raw_arguments = _field(function, "arguments")
        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise TypeError("tool arguments must be a JSON object")
        if name not in TOOLS:
            raise KeyError(f"unknown tool: {name}")
        print(f"  tool: {name}({arguments})")
        return str(TOOLS[name](**arguments))
    except Exception as error:  # Return tool failures to the model so it can recover.
        return f"Error: {error}"


def run_agent(
    messages: list[dict[str, Any]],
    client: Any,
    *,
    model: str = MODEL,
    max_tool_rounds: int = MAX_TOOL_ROUNDS,
) -> str:
    for _ in range(max_tool_rounds):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message
        messages.append(_assistant_message(message))

        tool_calls = _field(message, "tool_calls")
        if not tool_calls:
            return _field(message, "content") or ""

        for tool_call in tool_calls:
            result = run_tool(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": _field(tool_call, "id"),
                    "content": result,
                }
            )

    raise RuntimeError(f"Agent exceeded {max_tool_rounds} model/tool rounds")


def create_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add a key, "
            "or set it in your shell environment."
        )
    return OpenAI()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reconstructed mini coding agent.")
    parser.add_argument("--prompt", help="Run one prompt non-interactively, then exit.")
    args = parser.parse_args()

    try:
        client = create_client()
    except RuntimeError as error:
        print(f"Error: {error}")
        return 2

    messages: list[dict[str, Any]] = [
        {"role": "developer", "content": SYSTEM_PROMPT}
    ]

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
        messages.append({"role": "user", "content": user_input})
        try:
            reply = run_agent(messages, client)
            print(f"\nAgent: {reply}")
        except OpenAIError as error:
            print(f"\nOpenAI API error: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
