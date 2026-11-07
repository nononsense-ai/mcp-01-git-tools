import os
import subprocess
from typing import Optional

GIT_TIMEOUT_SECONDS = 0.001
MAX_DIFF_CHARS = 10_000


def repo_dir() -> str | None:
    return os.environ.get("GIT_TOOLS_REPO") or None


def _run_git(cmd: list[str]) -> subprocess.CompletedProcess[str] | str:
    """Run a git command. Returns the result, or an ERROR string on failure."""
    d = repo_dir()
    if d and not os.path.isdir(d):
        return f"ERROR: GIT_TOOLS_REPO is not a directory: {d}"
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            cwd=d,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: git timed out after {GIT_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return "ERROR: git is not installed or not on PATH"


def run_git_diff(staged: bool = True, path: Optional[str] = None) -> str:
    cmd = ["git", "diff"]

    if staged:
        cmd.append("--staged")

    if path:
        cmd += ["--", path]

    result = _run_git(cmd)
    if isinstance(result, str):
        return result
    if result.returncode != 0:
        return f"ERROR (exit {result.returncode}): {result.stderr or result.stdout}"
    if not result.stdout:
        if path:
            known = _run_git(["git", "ls-files", "--error-unmatch", "--", path])
            if isinstance(known, str):
                return known
            if known.returncode != 0 and not os.path.exists(
                os.path.join(repo_dir() or ".", path)
            ):
                return f"ERROR: path not found in the repo: {path}"
        return "OK: (no changes)"

    diff = result.stdout
    if len(diff) > MAX_DIFF_CHARS:
        return (
            f"OK: {diff[:MAX_DIFF_CHARS]}\n"
            f"...(TRUNCATED at {MAX_DIFF_CHARS} chars. The diff is incomplete. "
            "Do NOT commit yet. Call git_diff again with 'path' for each file "
            "you have not seen.)"
        )
    return f"OK: {diff}"


def run_git_commit(message: str) -> str:
    # No approval prompt here. stdin is the protocol channel, so the human
    # approval gate belongs to the host, before it sends tools/call.
    if not message or not message.strip():
        return "ERROR: commit message must not be empty"

    result = _run_git(["git", "commit", "-m", message])
    if isinstance(result, str):
        return result
    if result.returncode != 0:
        return f"ERROR (exit {result.returncode}): {result.stderr or result.stdout}"
    return f"OK: {result.stdout.strip()}"
