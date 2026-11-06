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


async def test_diff_path_limits_to_one_file(repo):
    (repo / "a.txt").write_text("alpha\n")
    (repo / "b.txt").write_text("bravo\n")
    git(repo, "add", "a.txt", "b.txt")
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {"path": "b.txt"})
    assert not result.is_error
    assert "+bravo" in text_of(result)
    assert "+alpha" not in text_of(result)


async def test_diff_truncates_large_diff(repo):
    (repo / "big.txt").write_text("x" * 30_000 + "\n")
    git(repo, "add", "big.txt")
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {})
    assert not result.is_error
    assert "TRUNCATED" in text_of(result)
    assert "path" in text_of(result)


async def test_repo_path_that_is_a_file_is_a_clear_error(repo, monkeypatch):
    (repo / "a.txt").write_text("hi\n")
    monkeypatch.setenv("GIT_TOOLS_REPO", str(repo / "a.txt"))
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {})
    assert result.is_error
    assert "not a directory" in text_of(result)


async def test_repo_path_that_does_not_exist_is_a_clear_error(repo, monkeypatch):
    monkeypatch.setenv("GIT_TOOLS_REPO", str(repo / "missing"))
    async with Client(mcp) as client:
        result = await client.call_tool("git_diff", {})
    assert result.is_error
    assert "not a directory" in text_of(result)


async def test_commit_creates_a_commit(repo):
    (repo / "a.txt").write_text("hello\n")
    git(repo, "add", "a.txt")
    async with Client(mcp) as client:
        result = await client.call_tool("git_commit", {"message": "add a.txt"})
    assert not result.is_error
    log = subprocess.run(
        ["git", "log", "--format=%s"], cwd=repo, capture_output=True, text=True
    )
    assert log.stdout.strip() == "add a.txt"


async def test_commit_with_empty_message_is_an_error(repo):
    async with Client(mcp) as client:
        result = await client.call_tool("git_commit", {"message": "   "})
    assert result.is_error
    assert "must not be empty" in text_of(result)


async def test_commit_with_nothing_staged_keeps_the_reason(repo):
    async with Client(mcp) as client:
        result = await client.call_tool("git_commit", {"message": "nothing here"})
    assert result.is_error
    assert "nothing" in text_of(result).lower()
