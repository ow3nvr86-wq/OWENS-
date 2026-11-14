#!/usr/bin/env python3
"""Owen's Agent: a general-purpose Claude agent for the terminal.

It chats with you, searches the web, reads and writes files in a workspace
folder, and runs shell commands (each one only after you approve it).

Run:
    python agent.py                     # chat in the current folder
    python agent.py --workspace ~/proj  # let it work in another folder
    python agent.py "summarise README.md"   # one task, then exit

Inside the chat, type /help for commands.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_TOKENS = 64000
MAX_TOOL_OUTPUT = 30_000  # characters returned to Claude per tool call
SHELL_TIMEOUT = 120  # seconds

SYSTEM_PROMPT = """You are Owen's Agent, a capable general-purpose assistant running in the user's terminal.

You can search and fetch web pages, read, write and edit files inside the workspace folder, and run shell commands there. The user approves every shell command before it runs, so explain briefly what a command does when it isn't obvious.

How to work:
- For a simple question, just answer it. Use tools when they actually help: current facts, the user's files, running code.
- Look before you change things: read a file before editing it, list a folder before guessing paths.
- Prefer edit_file for small changes to an existing file; use write_file for new files or full rewrites.
- If a tool fails, read the error and try a different approach rather than repeating the same call.
- When you finish a task, say plainly what you did and what (if anything) is left for the user.
- Keep answers short and readable in a terminal. Use plain text or light Markdown."""

# ---------------------------------------------------------------- colours
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def dim(t: str) -> str:
    return _c("2", t)


def cyan(t: str) -> str:
    return _c("36", t)


def yellow(t: str) -> str:
    return _c("33", t)


def red(t: str) -> str:
    return _c("31", t)


def bold(t: str) -> str:
    return _c("1", t)


# ---------------------------------------------------------------- tools
class ToolError(Exception):
    """A tool failed in a way Claude should hear about and recover from."""


class Tools:
    """Client-side tools. Every path is confined to the workspace root."""

    def __init__(self, root: Path, auto_approve: bool):
        self.root = root.resolve()
        self.auto_approve = auto_approve

    # -- helpers
    def _path(self, raw: str) -> Path:
        target = (self.root / raw).resolve()
        if not target.is_relative_to(self.root):
            raise ToolError(f"'{raw}' is outside the workspace ({self.root}).")
        return target

    @staticmethod
    def _clip(text: str) -> str:
        if len(text) <= MAX_TOOL_OUTPUT:
            return text
        half = MAX_TOOL_OUTPUT // 2
        return f"{text[:half]}\n\n... [{len(text) - MAX_TOOL_OUTPUT} characters cut] ...\n\n{text[-half:]}"

    # -- tool implementations
    def list_files(self, path: str = ".") -> str:
        target = self._path(path)
        if not target.is_dir():
            raise ToolError(f"'{path}' is not a folder.")
        lines = []
        for p in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if p.name in {".git", "node_modules", "__pycache__", ".venv", "venv"}:
                continue
            rel = p.relative_to(self.root)
            lines.append(f"{rel}/" if p.is_dir() else f"{rel}  ({p.stat().st_size:,} bytes)")
        return "\n".join(lines) or "(empty folder)"

    def read_file(self, path: str) -> str:
        target = self._path(path)
        if not target.is_file():
            raise ToolError(f"'{path}' does not exist or is not a file.")
        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ToolError(f"'{path}' is not a UTF-8 text file.")
        numbered = "\n".join(f"{i:>5}  {line}" for i, line in enumerate(text.splitlines(), 1))
        return self._clip(numbered or "(empty file)")

    def write_file(self, path: str, contents: str) -> str:
        target = self._path(path)
        existed = target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
        return f"{'Overwrote' if existed else 'Created'} {path} ({len(contents):,} characters)."

    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        target = self._path(path)
        if not target.is_file():
            raise ToolError(f"'{path}' does not exist.")
        text = target.read_text(encoding="utf-8")
        count = text.count(old_text)
        if count == 0:
            raise ToolError("old_text was not found. Read the file again and copy the text exactly.")
        if count > 1:
            raise ToolError(f"old_text appears {count} times. Include more surrounding lines so it is unique.")
        target.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {path}."

    def run_shell(self, command: str) -> str:
        print(yellow(f"\n  $ {command}"))
        if not self.auto_approve:
            try:
                answer = input(yellow("  Run this command? [y/N] ")).strip().lower()
            except EOFError:
                answer = ""
            if answer not in {"y", "yes"}:
                return "The user declined to run this command. Ask them what they would like instead."
        try:
            proc = subprocess.run(
                command, shell=True, cwd=self.root, capture_output=True,
                text=True, timeout=SHELL_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {SHELL_TIMEOUT} seconds.")
        out = (proc.stdout or "") + (f"\n[stderr]\n{proc.stderr}" if proc.stderr else "")
        return self._clip(f"exit code {proc.returncode}\n{out.strip() or '(no output)'}")

    # -- dispatch
    def run(self, name: str, args: dict) -> str:
        spec = SCHEMAS.get(name)
        if spec is None:
            raise ToolError(f"Unknown tool '{name}'.")
        # Validate input ourselves: with eager input streaming the API does not.
        props = spec["input_schema"]["properties"]
        missing = [k for k in spec["input_schema"].get("required", []) if k not in args]
        wrong = [k for k, v in args.items() if k not in props or not isinstance(v, str)]
        if missing or wrong:
            raise ToolError(f"Invalid input. Missing: {missing or 'none'}; bad or unknown fields: {wrong or 'none'}.")
        return getattr(self, name)(**args)


def _tool(name: str, description: str, props: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
            "required": required,
            "additionalProperties": False,
        },
    }


SCHEMAS = {
    t["name"]: t
    for t in [
        _tool("list_files",
              "List the files and folders at a path in the workspace. Call this before reading "
              "or writing when you are not sure what exists.",
              {"path": "Folder path relative to the workspace root. Defaults to '.'."}, []),
        _tool("read_file",
              "Read a UTF-8 text file from the workspace. Output has line numbers. Call this "
              "before editing a file or when the user asks about a file's contents.",
              {"path": "File path relative to the workspace root."}, ["path"]),
        _tool("write_file",
              "Create a new file or completely replace an existing one. Use for new files or "
              "full rewrites; use edit_file for small changes.",
              {"path": "File path relative to the workspace root.",
               "contents": "The complete file contents."}, ["path", "contents"]),
        _tool("edit_file",
              "Replace one exact, unique snippet of text in an existing file. old_text must "
              "match the file exactly (without the line-number prefix from read_file).",
              {"path": "File path relative to the workspace root.",
               "old_text": "The exact text to replace. Must appear exactly once.",
               "new_text": "The replacement text."}, ["path", "old_text", "new_text"]),
        _tool("run_shell",
              "Run a shell command in the workspace folder and return its output. The user "
              "must approve each command. Use it to run code, tests, git, or installed CLIs.",
              {"command": "The bash command to run."}, ["command"]),
    ]
}

SERVER_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 8},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8},
]


# ---------------------------------------------------------------- agent
class Agent:
    def __init__(self, tools: Tools, effort: str, show_thinking: bool):
        self.client = anthropic.Anthropic()
        self.tools = tools
        self.effort = effort
        self.show_thinking = show_thinking
        self.messages: list = []
        self.usage = {"input": 0, "output": 0, "cache_read": 0}

    def _stream_turn(self):
        """Send the conversation, print the reply as it streams, return the final message."""
        thinking = {"type": "adaptive", "display": "summarized" if self.show_thinking else "omitted"}
        with self.client.beta.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[*SCHEMAS.values(), *SERVER_TOOLS],
            messages=self.messages,
            thinking=thinking,
            output_config={"effort": self.effort},
            cache_control={"type": "ephemeral"},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "thinking" and self.show_thinking:
                        print(dim("\n[thinking] "), end="", flush=True)
                    elif block.type == "text":
                        print("\n", end="")
                    elif block.type == "server_tool_use":
                        print(cyan(f"\n  [{block.name}]"), end="", flush=True)
                    elif block.type == "tool_use":
                        print(cyan(f"\n  [{block.name}] "), end="", flush=True)
                elif event.type == "content_block_delta":
                    d = event.delta
                    if d.type == "text_delta":
                        print(d.text, end="", flush=True)
                    elif d.type == "thinking_delta" and self.show_thinking:
                        print(dim(d.thinking), end="", flush=True)
            message = stream.get_final_message()
        print()
        u = message.usage
        self.usage["input"] += (u.input_tokens or 0) + (u.cache_creation_input_tokens or 0)
        self.usage["cache_read"] += u.cache_read_input_tokens or 0
        self.usage["output"] += u.output_tokens or 0
        return message

    def ask(self, user_text: str) -> None:
        self.messages.append({"role": "user", "content": user_text})
        json_retries = 0
        for _ in range(50):  # hard cap on steps per request
            try:
                message = self._stream_turn()
                json_retries = 0
            except ValueError:
                # The SDK could not parse a streamed tool input at all; re-issue the turn.
                json_retries += 1
                if json_retries > 2:
                    raise
                print(red("  (malformed tool input, retrying)"))
                continue

            self.messages.append({"role": "assistant", "content": message.content})

            if message.stop_reason == "pause_turn":
                continue  # a long server-side search paused; resend so it resumes
            if message.stop_reason == "refusal":
                print(red("  Claude declined this request."))
                return

            tool_uses = [b for b in message.content if b.type == "tool_use"]
            if not tool_uses:
                if message.stop_reason == "max_tokens":
                    print(red("  (reply hit the length limit and was cut off)"))
                return
            if message.stop_reason == "max_tokens":
                # A truncated tool input can parse as a valid partial object. Don't run it.
                self.messages.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                     "content": "Your tool input was cut off by the output limit. Send a smaller one."}
                    for b in tool_uses]})
                continue

            results = []
            for block in tool_uses:
                args = block.input if isinstance(block.input, dict) else {}
                try:
                    output = self.tools.run(block.name, args)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
                    if block.name != "run_shell":
                        print(dim(f"  {output.splitlines()[0][:100] if output else 'done'}"))
                except ToolError as e:
                    print(red(f"  error: {e}"))
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "is_error": True, "content": str(e)})
                except Exception as e:  # keep the loop alive; tell Claude what broke
                    print(red(f"  error: {e}"))
                    results.append({"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                                    "content": json.dumps({"error": f"{type(e).__name__}: {e}"})})
            self.messages.append({"role": "user", "content": results})
        print(red("  Stopped after 50 steps. Say 'continue' to keep going."))


# ---------------------------------------------------------------- CLI
HELP = """Commands:
  /help         show this help
  /reset        start a fresh conversation
  /usage        tokens used this session
  /effort LEVEL set thinking effort: low, medium, high, xhigh, max
  /thinking     toggle showing Claude's thinking summaries
  /exit         quit (Ctrl-D also works)"""


def repl(agent: Agent) -> None:
    print(bold("Owen's Agent") + dim(f"  ({MODEL}, effort {agent.effort})"))
    print(dim(f"Workspace: {agent.tools.root}"))
    print(dim("Type /help for commands.\n"))
    while True:
        try:
            text = input(bold("you › ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not text:
            continue
        if text.startswith("/"):
            cmd, _, arg = text.partition(" ")
            if cmd in {"/exit", "/quit"}:
                return
            elif cmd == "/help":
                print(HELP)
            elif cmd == "/reset":
                agent.messages.clear()
                print(dim("Conversation cleared."))
            elif cmd == "/usage":
                u = agent.usage
                print(dim(f"input {u['input']:,}  cached {u['cache_read']:,}  output {u['output']:,} tokens"))
            elif cmd == "/effort" and arg in {"low", "medium", "high", "xhigh", "max"}:
                agent.effort = arg
                print(dim(f"Effort set to {arg}."))
            elif cmd == "/thinking":
                agent.show_thinking = not agent.show_thinking
                print(dim(f"Thinking summaries {'on' if agent.show_thinking else 'off'}."))
            else:
                print(dim("Unknown command. Type /help."))
            continue
        run_safely(agent, text)


def run_safely(agent: Agent, text: str) -> None:
    try:
        agent.ask(text)
    except KeyboardInterrupt:
        print(red("\n  Interrupted."))
        _drop_unfinished_turn(agent)
    except anthropic.AuthenticationError:
        print(red("  Authentication failed. Set ANTHROPIC_API_KEY (see README)."))
        _drop_unfinished_turn(agent)
    except anthropic.RateLimitError:
        print(red("  Rate limited. Wait a moment and try again."))
        _drop_unfinished_turn(agent)
    except anthropic.APIStatusError as e:
        print(red(f"  API error {e.status_code}: {e.message}"))
        _drop_unfinished_turn(agent)
    except anthropic.APIConnectionError:
        print(red("  Network error. Check your connection."))
        _drop_unfinished_turn(agent)


def _drop_unfinished_turn(agent: Agent) -> None:
    """After a failure, roll history back to the last finished exchange so it stays valid."""
    while agent.messages:
        last = agent.messages[-1]
        types = [getattr(b, "type", None) for b in last["content"]] if last["role"] == "assistant" else []
        if types and "tool_use" not in types and types[-1] != "server_tool_use":
            return
        agent.messages.pop()


def main() -> None:
    parser = argparse.ArgumentParser(description="A general-purpose Claude agent for your terminal.")
    parser.add_argument("task", nargs="*", help="run one task and exit (otherwise opens a chat)")
    parser.add_argument("-w", "--workspace", default=".", help="folder the agent may read and write (default: here)")
    parser.add_argument("-e", "--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--yes", action="store_true", help="run shell commands without asking (careful)")
    parser.add_argument("--show-thinking", action="store_true", help="print Claude's thinking summaries")
    args = parser.parse_args()

    root = Path(args.workspace).expanduser()
    if not root.is_dir():
        sys.exit(f"Workspace '{root}' is not a folder.")
    agent = Agent(Tools(root, auto_approve=args.yes), args.effort, args.show_thinking)

    if args.task:
        run_safely(agent, " ".join(args.task))
    else:
        repl(agent)


if __name__ == "__main__":
    main()
