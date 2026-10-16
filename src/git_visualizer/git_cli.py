"""The lock-free git runner every reader uses (ADR 0001, ADR 0003).

Commands run with ``--no-optional-locks`` and ``GIT_OPTIONAL_LOCKS=0`` so that even
``git status`` never refreshes the index on disk or takes a lock. Callers only run
read-only commands through it.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


class GitCli:
    """Runs git in one repository folder, read-only and without optional locks."""

    def __init__(self, repository_path: Path) -> None:
        self._path = repository_path
        env = dict(os.environ)
        env["GIT_OPTIONAL_LOCKS"] = "0"
        env["LC_ALL"] = "C"
        env.pop("GIT_DIR", None)
        env.pop("GIT_WORK_TREE", None)
        self._env = env

    def run(self, *args: str, stdin: str | None = None) -> str:
        """Run git; ``stdin`` is fed to it (e.g. revisions for ``--stdin``)."""
        result = self._run(args, stdin)
        if result.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout

    def run_optional(self, *args: str) -> str | None:
        """Run git; ``None`` instead of an error if it exits non-zero."""
        result = self._run(args, None)
        return result.stdout if result.returncode == 0 else None

    def _run(self, args: tuple[str, ...], stdin: str | None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "--no-optional-locks", "-C", str(self._path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self._env,
            input=stdin if stdin is not None else "",
        )
