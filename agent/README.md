# Owen's Agent

A general-purpose Claude agent that runs in your terminal. It chats with you, and when it helps it can:

- **search the web** and read web pages
- **list, read, write and edit files** in one workspace folder (it cannot reach files outside it)
- **run shell commands** in that folder, and it asks you `y/N` before each one

It runs on Claude Opus 5.5 with adaptive thinking, streams replies as they're written, and keeps the conversation going until you quit.

## Setup

You need Python 3.10 or newer and an Anthropic API key from https://platform.claude.com.

```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Use it

```bash
python agent.py                          # chat; workspace = this folder
python agent.py -w ~/my-project          # let it work in another folder
python agent.py "what's in README.md?"   # one task, then exit
```

Options:

| Flag | What it does |
|---|---|
| `-w, --workspace DIR` | Folder the agent may read and write (default: current folder) |
| `-e, --effort LEVEL` | How hard it thinks: `low`, `medium`, `high` (default), `xhigh`, `max` |
| `--show-thinking` | Print short summaries of Claude's reasoning |
| `--yes` | Run shell commands without asking. Only use this in a folder you don't mind it changing |

Chat commands: `/help`, `/reset`, `/usage`, `/effort LEVEL`, `/thinking`, `/exit`.

## How it works

`agent.py` is one file, about 400 lines:

- **`Tools`**: the five local tools. Every path goes through `_path()`, which refuses anything outside the workspace. `run_shell` asks before running anything.
- **`SCHEMAS`** describes those tools to Claude. `SERVER_TOOLS` adds web search and web fetch, which run on Anthropic's side.
- **`Agent.ask()`** is the agent loop: send the conversation → stream the reply → if Claude asked for tools, run them and send the results back → repeat until Claude answers. It stops after 50 steps per request.
- If a safety check declines a request, it's automatically retried on a fallback model (`fallbacks: "default"`).

### Add your own tool

1. Write a method on `Tools` that takes string arguments and returns a string. Raise `ToolError("...")` for problems Claude should know about.
2. Add a matching `_tool(...)` entry to `SCHEMAS`, with a description that says *when* Claude should call it.

## Cost

Each message is billed by the Anthropic API (Opus 5.5: $4 per million input tokens, $20 per million output). Repeated context is cached automatically, which makes long chats cheaper. Type `/usage` to see tokens used. For cheaper, faster replies, use `-e low` or `-e medium`.
