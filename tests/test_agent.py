from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI

import agent


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list | None = None

    def model_dump(self, exclude_none: bool = True):
        result = {"role": "assistant", "content": self.content}
        if self.tool_calls is not None:
            result["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in self.tool_calls
            ]
        if exclude_none:
            result = {key: value for key, value in result.items() if value is not None}
        return result


def tool_call(call_id: str, name: str, **arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


class FakeCompletions:
    def __init__(self, messages):
        self._messages = iter(messages)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = next(self._messages)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_client(*messages):
    completions = FakeCompletions(messages)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=completions),
        completions_log=completions,
    )


def test_plain_text_response_stops_without_tools():
    client = fake_client(FakeMessage(content="Done", tool_calls=[]))
    messages = [{"role": "user", "content": "Say done"}]

    assert agent.run_agent(messages, client) == "Done"
    assert len(client.completions_log.calls) == 1
    assert messages[-1] == {"role": "assistant", "content": "Done", "tool_calls": []}


def test_tool_result_is_returned_to_model(tmp_path):
    (tmp_path / "alpha.txt").write_text("alpha", encoding="utf-8")
    agent.set_workspace_root(tmp_path)
    client = fake_client(
        FakeMessage(tool_calls=[tool_call("call-1", "list_files", path=".")]),
        FakeMessage(content="I found alpha.txt", tool_calls=[]),
    )
    messages = [{"role": "user", "content": "List files"}]

    assert agent.run_agent(messages, client) == "I found alpha.txt"
    tool_message = next(message for message in messages if message["role"] == "tool")
    assert tool_message == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "alpha.txt",
    }
    assert len(client.completions_log.calls) == 2


def test_multiple_tool_calls_in_one_round(tmp_path):
    agent.set_workspace_root(tmp_path)
    client = fake_client(
        FakeMessage(
            tool_calls=[
                tool_call("call-write", "write_file", path="note.txt", content="hello"),
                tool_call("call-read", "read_file", path="note.txt"),
            ]
        ),
        FakeMessage(content="Created and checked note.txt", tool_calls=[]),
    )
    messages = [{"role": "user", "content": "Create a note"}]

    assert agent.run_agent(messages, client) == "Created and checked note.txt"
    results = [message["content"] for message in messages if message["role"] == "tool"]
    assert results == ["Saved note.txt (5 characters)", "hello"]


def test_file_tools_are_confined_to_workspace(tmp_path):
    agent.set_workspace_root(tmp_path)
    assert agent.write_file("nested/hello.txt", "hello") == "Saved nested/hello.txt (5 characters)"
    assert agent.read_file("nested/hello.txt") == "hello"
    assert "nested/" in agent.list_files(".")

    with pytest.raises(ValueError, match="outside the workspace"):
        agent.read_file("../outside.txt")


def test_command_requires_confirmation(tmp_path):
    agent.set_workspace_root(tmp_path)
    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        return SimpleNamespace(stdout="ok", stderr="", returncode=0)

    declined = agent.run_command("anything", confirm=lambda _: "n", runner=runner)
    assert declined == "The user declined to run this command."
    assert called is False

    approved = agent.run_command("anything", confirm=lambda _: "y", runner=runner)
    assert approved == "ok"
    assert called is True


def test_unknown_tool_error_is_recoverable():
    result = agent.run_tool(tool_call("bad", "not_a_tool"))
    assert result.startswith("Error:")
    assert "unknown tool" in result


def test_round_limit_prevents_infinite_loop(tmp_path):
    agent.set_workspace_root(tmp_path)
    client = fake_client(
        FakeMessage(tool_calls=[tool_call("1", "list_files", path=".")]),
        FakeMessage(tool_calls=[tool_call("2", "list_files", path=".")]),
    )

    with pytest.raises(RuntimeError, match="exceeded 2"):
        agent.run_agent([], client, max_tool_rounds=2)


def test_real_openai_sdk_round_trip_with_mock_transport(tmp_path):
    """Exercise actual SDK request serialization and response parsing offline."""

    agent.set_workspace_root(tmp_path)
    (tmp_path / "visible.txt").write_text("visible", encoding="utf-8")
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-sdk",
                        "type": "function",
                        "function": {
                            "name": "list_files",
                            "arguments": json.dumps({"path": "."}),
                        },
                    }
                ],
            }
            finish_reason = "tool_calls"
        else:
            message = {"role": "assistant", "content": "Saw visible.txt"}
            finish_reason = "stop"

        return httpx.Response(
            200,
            json={
                "id": f"chatcmpl-{len(requests)}",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-5-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": finish_reason,
                    }
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAI(
        api_key="test-key",
        base_url="https://mock.openai.local/v1",
        http_client=http_client,
    )
    messages = [{"role": "user", "content": "List files"}]

    assert agent.run_agent(messages, client) == "Saw visible.txt"
    assert len(requests[0]["tools"]) == 4
    assert requests[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call-sdk",
        "content": "visible.txt",
    }
