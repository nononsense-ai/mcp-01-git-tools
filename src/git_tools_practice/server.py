from typing import Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import git_ops

mcp = MCPServer(
    "git-tools",
    instructions=(
        "Tools for reading staged git changes and creating commits in one "
        "repository. Always inspect the diff before committing."
    ),
)


def _unwrap(result: str) -> str:
    if result.startswith("ERROR"):
        raise ToolError(result)
    return result.removeprefix("OK: ").removeprefix("OK:")


@mcp.tool()
def git_diff(staged: bool = True, path: Optional[str] = None) -> str:
    """Returns a git diff for the current repo.

    By default returns the staged diff. Pass 'path' to see the diff of a
    single file, which is useful when the full diff is too large or has been
    truncated.

    Args:
        staged: If true (default), diff staged changes. If false, diff unstaged changes.
        path: Optional. Relative path of a single file to diff.
    """
    return _unwrap(git_ops.run_git_diff(staged=staged, path=path))


@mcp.tool()
def git_commit(message: str) -> str:
    """Creates a commit with a given message.

    Commits whatever is currently staged. Call git_diff first so the message
    describes the actual changes.

    Args:
        message: The commit message.
    """
    return _unwrap(git_ops.run_git_commit(message=message))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
