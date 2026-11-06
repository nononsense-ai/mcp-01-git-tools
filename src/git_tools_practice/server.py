from typing import Optional

from mcp.server.mcpserver import MCPServer

from . import git_ops

mcp = MCPServer("git-tools")


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
    return git_ops.run_git_diff(staged=staged, path=path)


def main() -> None:
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
