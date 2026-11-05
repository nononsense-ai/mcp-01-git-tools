import os
import subprocess
from typing import Optional

GIT_TIMEOUT_SECONDS = 10


def repo_dir() -> Optional[str]:
    return os.environ.get("GIT_TOOLS_REPO") or None


def _run_git(cmd: list[str]) -> subprocess.CompletedProcess[str] | str:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            cwd=repo_dir(),
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: git timeout after {GIT_TIMEOUT_SECONDS} seconds"
    except FileNotFoundError:
        return f"ERROR: git is not installed or not in PATH"


def run_git_diff(staged: bool = True) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    result = _run_git(cmd)
    if isinstance(result, str):
        return result
    if result.returncode != 0:
        return f"ERROR: {result.stderr}"
    return result.stdout or "(no changes)"


def run_git_commit(message: str) -> str:
    if not message or not message.strip():
        return "ERROR: commit message must not be empty"

    cmd = ["git", "commit", "-m", message]
    result = _run_git(cmd)
    if isinstance(result, str):
        return result
    if result.returncode != 0:
        return f"ERROR: (exit {result.returncode}): {result.stderr or result.stdout}"

    return f"OK: {result.stdout.strip()}"
