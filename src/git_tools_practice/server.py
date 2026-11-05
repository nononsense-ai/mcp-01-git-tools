from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import git_ops

mcp = MCPServer("git-tools")


def _unwrap(result: str) -> str:
    if result.startswith("ERROR"):
        raise ToolError(result)
    return result.removeprefix("OK: ").removeprefix("OK:")


@mcp.tool()
def git_diff(staged: bool = True) -> str:
    """Returns a git diff for the current repo

    Args:
        staged: If true(default), diff staged changes. If false, diff unstaged changes.
    """
    print("DEBUG: git_diff called")
    return _unwrap(git_ops.run_git_diff(staged=staged))


@mcp.tool()
def git_commit(message: str) -> str:
    """Creates a commit with a given message.
    Commits whatever is currently staged. Call git_diff first so the message
    describes the actual changes.
    Args:
        message: the commit message.
    """
    return _unwrap(git_ops.run_git_commit(message=message))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
