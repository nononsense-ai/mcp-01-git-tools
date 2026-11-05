"""Talk to the server by hand: no SDK, just JSON lines over stdin/stdout.

Run from the 01-server folder:
    GIT_TOOLS_REPO=/path/to/a/repo uv run python scripts/raw_jsonrpc.py

Shows the three message kinds from the course:
  request (has an id) / response (same id) / notification (no id, no reply)
"""

import json
import os
import subprocess

p = subprocess.Popen(
    ["uv", "run", "git-tools-practice"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    env=os.environ.copy(),
)


def send(msg: dict) -> None:
    print(">>>", json.dumps(msg))
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()


def receive() -> None:
    print("<<<", p.stdout.readline().strip()[:600], "\n")


# 1. initialize: both sides declare what they support (capability negotiation)
send(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "raw", "version": "0"},
        },
    }
)
receive()

# 2. a NOTIFICATION: no id, so no response comes back
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

# 3. discovery: this is where gcommit's `available_tools` list now comes from
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
receive()

# 4. the call: this is what `execute_tool` / DISPATCH used to do
send(
    {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "git_diff", "arguments": {"staged": True}},
    }
)
receive()

p.terminate()
