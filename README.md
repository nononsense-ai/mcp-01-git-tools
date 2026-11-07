# mcp-01-git-tools

A small MCP server in Python that exposes two git tools over stdio. This is part 1 of a series on MCP; the server side comes first, and a client that talks to it comes in the next part.

No model is involved, so you don't need an API key. Anything that speaks MCP can connect: Claude Desktop, Claude Code, the MCP Inspector, or a client you write yourself.

## Tools

| Tool | Arguments | What it does |
|---|---|---|
| `git_diff` | `staged: bool = True`, `path: str \| None = None` | Runs `git diff --staged` (or plain `git diff` when `staged` is false), optionally for one file. Returns `(no changes)` if the diff is empty, or an error if `path` does not exist in the repo. The tool cuts diffs over 10,000 characters and adds a note telling the model to call again with `path`. |
| `git_commit` | `message: str` | Runs `git commit -m <message>` on whatever is staged. Rejects empty messages. |

The tool descriptions come from the docstrings and the input schemas come from the type hints, so there's nothing to keep in sync by hand. The `git_commit` docstring tells the model to call `git_diff` first so the message matches the real changes.

Failures raise `ToolError`, which the client sees as an error result with the reason in the text. Git timeouts (10 seconds), a missing `git` binary and a `GIT_TOOLS_REPO` that isn't a directory each get their own message.

## Requirements

- Python 3.14 or newer
- `git`
- [uv](https://docs.astral.sh/uv/)
- Node.js, only if you want the Inspector (it runs through `npx`)

## Setup

```bash
git clone https://github.com/nononsense-ai/mcp-01-git-tools.git
cd mcp-01-git-tools
uv sync
```

## Pointing it at a repo

The server runs git in the folder named by the `GIT_TOOLS_REPO` environment variable. If it's unset, git runs in whatever directory the server was started from, which is rarely what you want. Set it every time.

## Running it

Directly (it will look hung, because it's waiting for JSON on stdin):

```bash
GIT_TOOLS_REPO=/path/to/a/repo uv run git-tools-practice
```

In the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector@latest \
  -e GIT_TOOLS_REPO=/path/to/a/repo \
  uv run git-tools-practice
```

Keep the `-e` flag. The Inspector doesn't forward your shell's variables to the server it launches, so `GIT_TOOLS_REPO=... npx ...` won't work.

In Claude Code:

```bash
claude mcp add git-tools -e GIT_TOOLS_REPO=/path/to/a/repo -- \
  uv --directory /absolute/path/to/mcp-01-git-tools run git-tools-practice
```

In Claude Desktop (this is the exercise in the video): open Settings, Developer, Edit Config, and add the server to `claude_desktop_config.json`. Desktop doesn't use your shell's PATH, so give the full path to `uv` (`which uv`) and use absolute paths everywhere:

```json
{
  "mcpServers": {
    "git-tools": {
      "command": "/absolute/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-01-git-tools",
        "run",
        "git-tools-practice"
      ],
      "env": {
        "GIT_TOOLS_REPO": "/absolute/path/to/a/repo"
      }
    }
  }
}
```

Quit Claude Desktop completely (Cmd+Q on a Mac) and reopen it. `git-tools` should appear with `git_diff` and `git_commit`. If it doesn't, check `~/Library/Logs/Claude/mcp-server-git-tools.log`. Use a throwaway repo for `GIT_TOOLS_REPO`, and keep Desktop's per-call approval on for `git_commit`.

## Watching the raw protocol

[scripts/raw_jsonrpc.py](scripts/raw_jsonrpc.py) starts the server as a subprocess and speaks to it with hand-written JSON lines, no SDK. It walks through the four-step handshake: `initialize`, the `notifications/initialized` notification (no `id`, so no reply), `tools/list`, and a `tools/call` for `git_diff`.

```bash
GIT_TOOLS_REPO=/path/to/a/repo uv run python scripts/raw_jsonrpc.py
```

## Tests

```bash
uv run pytest
```

The tests create a throwaway repo in a temp directory and call the tools through an in-memory MCP client. They cover `git_diff` (nothing staged, a staged file, one file by `path`, truncation), `git_commit` (success, empty message, nothing staged) and a bad `GIT_TOOLS_REPO`.

## Layout

```
mcp-01-git-tools/
  src/git_tools_practice/
    git_ops.py   subprocess wrappers around git, return "OK: ..." or "ERROR: ..." strings
    server.py    the MCP tools; turns ERROR strings into ToolError
  scripts/
    raw_jsonrpc.py
  tests/
    test_server.py
```

`git_ops.py` knows nothing about MCP, and `server.py` knows nothing about subprocesses. The split keeps the git code testable without a protocol in the way.

## Things to know

- stdout belongs to the protocol. Don't `print()` in tool code; log to stderr.
- `git_commit` has no approval step. The host or client is responsible for asking a human before it sends `tools/call`. Keep tool approval on for `git_commit`; do not connect this server to a client that auto-approves it.
- [src/git_tools_practice/__init__.py](src/git_tools_practice/__init__.py) still holds the `uv init` placeholder `main()`; the real entry point is `server:main`.

## Code at each step

The tutorial builds the server in steps. The `steps` branch holds steps 1 to 6, tagged `p01-step-1` through `p01-step-6`; `p01-step-7` is the code at the end of Step 7, and `p01-step-8` adds the unknown-path check from Step 8F, which is the final code on `main`. Steps 4 and 5 share a commit, because the Inspector runs the same code as the entry point. To see the code at a step:

```bash
git checkout p01-step-3
git checkout main   # back to the final code
```

## Links

- Website: [nononsensecode.dev](https://nononsensecode.dev)
- YouTube: [@nononsenseaeye](https://www.youtube.com/@nononsenseaeye)
- Instagram: [@nononsenseaeye](https://www.instagram.com/nononsenseaeye)

## Next

Part 2 builds the client: an agent launches this server, fetches the tool list from it instead of hard-coding one, and asks for your approval before sending `git_commit`.
