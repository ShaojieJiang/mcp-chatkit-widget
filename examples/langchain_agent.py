"""LangChain agent example that calls the MCP ChatKit widget tools.

Requires `langchain`, `langchain-mcp-adapters`, and a provider-specific LLM
implementation such as `langchain-openai`.
Set `OPENAI_API_KEY` (or your provider's API key env var) before running.
"""

from __future__ import annotations
import argparse
import asyncio
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient


DEFAULT_MODEL = "openai:gpt-4o-mini"
DEFAULT_PROMPT = (
    "Act as a travel concierge and call the flight_tracker widget so I can see "
    "the latest progress on flight SB845 from San Francisco to London."
)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments used by the example."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a LangChain Zero-Shot agent that fetches MCP tools exposed by "
            "the mcp-chatkit-widget server."
        )
    )
    parser.add_argument(
        "--model",
        "-m",
        default=DEFAULT_MODEL,
        help=(
            "Language model identifier "
            "(e.g., openai:gpt-4o-mini or claude-sonnet-4-5-20250929)."
        ),
    )
    parser.add_argument(
        "--prompt",
        "-p",
        default=DEFAULT_PROMPT,
        help="Instruction that urges the agent to use the widgets.",
    )
    parser.add_argument(
        "--widgets-dir",
        "-w",
        type=Path,
        default=Path(__file__).resolve().parent / "widgets",
        help="Path to the curated widgets directory.",
    )
    parser.add_argument(
        "--server-name",
        "-s",
        default="chatkit",
        help="Name used by MultiServerMCPClient to identify the widget server.",
    )
    return parser.parse_args()


def _build_mcp_connection(server_name: str, widgets_dir: Path) -> dict[str, Any]:
    """Create the stdio connection config for mcp-chatkit-widget."""
    return {
        server_name: {
            "transport": "stdio",
            "command": "mcp-chatkit-widget",
            "args": ["--widgets-dir", str(widgets_dir)],
        }
    }


def _extract_structured_content(observation: Any) -> Mapping[str, Any] | None:
    """Return structured widget payloads that may live inside a tool observation."""
    artifact = None
    if isinstance(observation, tuple) and len(observation) == 2:
        _, artifact = observation
    elif isinstance(observation, Mapping):
        artifact = observation.get("artifact") or observation.get("structured_content")
    elif hasattr(observation, "artifact"):
        artifact = getattr(observation, "artifact", None)

    if isinstance(artifact, Mapping):
        structured = artifact.get("structured_content")
        if isinstance(structured, Mapping):
            return structured
        if isinstance(structured, list):
            # Some adapters wrap the payload in a list.
            first = structured[0] if structured else None
            if isinstance(first, Mapping):
                return first
    return None


def _render_content(content: Any) -> str | None:
    """Create a lightweight representation of content blocks returned from tools."""
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, Mapping):
        return json.dumps(content, indent=2)
    if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
        parts: list[str] = []
        for part in content:
            text = _render_content(part)
            if text:
                parts.append(text)
        return "\n".join(parts)
    return str(content)


def _summarize_tool_observation(observation: Any) -> None:
    """Print any available text or structured payload returned by the tool."""
    text_content = None
    structured = None
    if isinstance(observation, tuple) and len(observation) == 2:
        text_content = _render_content(observation[0])
    else:
        text_content = _render_content(observation)

    structured = _extract_structured_content(observation)

    if text_content:
        print(f"    Observed text:\n{text_content}")
    if structured:
        print("    Structured widget payload:")
        print(json.dumps(structured, indent=2))


def _build_tool_call_name_map(messages: Sequence[Any]) -> dict[str, str]:
    tool_name_by_call: dict[str, str] = {}
    for message in messages:
        tool_calls: Sequence[Any] | None = None
        if isinstance(message, AIMessage):
            tool_calls = message.tool_calls
        elif isinstance(message, Mapping):
            tool_calls = message.get("tool_calls")
        if not tool_calls:
            continue
        for call in tool_calls:
            if not call:
                continue
            if isinstance(call, Mapping):
                tool_call_id = call.get("id")
                tool_name = call.get("name")
            else:
                tool_call_id = getattr(call, "id", None)
                tool_name = getattr(call, "name", None)
            if tool_call_id is None or not tool_name:
                continue
            tool_name_by_call[str(tool_call_id)] = tool_name
    return tool_name_by_call


def _extract_tool_message_payload(
    message: Any,
) -> tuple[str | None, Any | None, Any | None] | None:
    if isinstance(message, ToolMessage):
        return (
            message.tool_call_id,
            message.content,
            getattr(message, "artifact", None),
        )
    if isinstance(message, Mapping) and message.get("type") == "tool":
        return (
            message.get("tool_call_id"),
            message.get("content"),
            message.get("artifact"),
        )
    return None


def _display_last_tool_response(messages: Sequence[Any] | None) -> None:
    """Print the most recent tool response captured in the chat history."""
    if not messages:
        print("No tool responses were recorded.")
        return
    if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)):
        print("No tool responses were recorded.")
        return

    tool_name_by_call = _build_tool_call_name_map(messages)

    for message in reversed(messages):
        payload = _extract_tool_message_payload(message)
        if not payload:
            continue
        tool_call_id, content, artifact = payload
        if content is None and artifact is None:
            continue
        tool_name = (
            tool_name_by_call.get(str(tool_call_id))
            if tool_call_id is not None
            else None
        )
        print("\nLast tool response recorded:")
        if tool_name:
            print(f"  Tool: `{tool_name}`")
        if tool_call_id:
            print(f"  Tool call ID: {tool_call_id}")
        _summarize_tool_observation((content, artifact))
        return

    print("No tool responses were recorded.")


def _extract_last_ai_response(messages: Sequence[Any]) -> str | None:
    """Return the content of the most recent AI message."""
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message.content.strip()
    return None


async def _run_agent(
    prompt: str,
    model: str,
    widgets_dir: Path,
    server_name: str,
) -> None:
    """Fetch MCP widget tools and run a LangChain agent against them."""
    connections = _build_mcp_connection(server_name, widgets_dir)
    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()

    print("Discovered widget tools:")
    for tool in tools:
        desc = getattr(tool, "description", None) or "<no description provided>"
        print(f"- `{tool.name}`: {desc}")

    llm = init_chat_model(model, temperature=0.0)
    agent = create_agent(llm, tools)

    print("\nInvoking agent with prompt:")
    print(f"> {prompt}\n")

    result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    output: str | None = None
    messages: Sequence[Any] | None = None

    if isinstance(result, Mapping):
        output = result.get("output")
        messages = result.get("messages")
        if (
            output is None
            and isinstance(messages, Sequence)
            and not isinstance(messages, (str, bytes))
        ):
            output = _extract_last_ai_response(messages)

    if output:
        print("Agent final answer:")
        print(output)
    else:
        print("Agent did not return a final text answer.")

    _display_last_tool_response(messages)


async def main() -> None:
    """Entry point used by the example script."""
    args = _parse_args()
    if not args.widgets_dir.exists():
        raise SystemExit(
            f"Widgets directory not found: {args.widgets_dir}. "
            "Run `uv run make sync` and verify the path."
        )
    await _run_agent(
        prompt=args.prompt,
        model=args.model,
        widgets_dir=args.widgets_dir.resolve(),
        server_name=args.server_name,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main())
