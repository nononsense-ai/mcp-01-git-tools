import subprocess

import pytest
from mcp import Client

from git_tools_practice.server import mcp


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    monkeypatch.setenv("GIT_TOOLS_REPO", str(tmp_path))
    return tmp_path


def text_of(result) -> str:
    return "".join(c.text for c in result.content if c.type == "text")


async def test_diff_with_nothing_staged(repo):
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {})
    assert not result.is_error
    assert text_of(result) == "(no changes)"


async def test_diff_shows_staged_change(repo):
    (repo / "a.txt").write_text("hello\n")
    git(repo, "add", "a.txt")
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {})
    assert not result.is_error
    assert "+hello" in text_of(result)
