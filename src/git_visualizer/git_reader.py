"""Git reader: reads the Observed Repository via the git CLI (ADR 0003).

Passive by design (ADR 0001): only read-only commands are run, with optional locks
disabled, so the Observed Repository is never modified and no lock files are taken.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from git_visualizer.file_status import STATUS_ARGS, parse_status
from git_visualizer.snapshot import Branch, Commit, Head, RepositorySnapshot


class GitError(RuntimeError):
    pass


class NotARepositoryError(GitError):
    pass


def read_snapshot(repository_path: Path) -> RepositorySnapshot:
    """Read an immutable Repository Snapshot of the repository at ``repository_path``."""
    git = _Git(repository_path)
    if git.run_optional("rev-parse", "--git-dir") is None:
        raise NotARepositoryError(str(repository_path))
    head = _read_head(git)
    branches = _read_branches(git)
    commits = _read_commits(git, has_head_commit=head.commit_hash is not None)
    working_tree, staging_area = parse_status(git.run(*STATUS_ARGS))
    return RepositorySnapshot(
        commits=commits,
        branches=branches,
        head=head,
        working_tree=working_tree,
        staging_area=staging_area,
    )


class _Git:
    def __init__(self, repository_path: Path) -> None:
        self._path = repository_path
        env = dict(os.environ)
        env["GIT_OPTIONAL_LOCKS"] = "0"
        env["LC_ALL"] = "C"
        env.pop("GIT_DIR", None)
        env.pop("GIT_WORK_TREE", None)
        self._env = env

    def run(self, *args: str) -> str:
        result = self._run(args)
        if result.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout

    def run_optional(self, *args: str) -> str | None:
        """Run git; ``None`` instead of an error if it exits non-zero."""
        result = self._run(args)
        return result.stdout if result.returncode == 0 else None

    def _run(self, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "--no-optional-locks", "-C", str(self._path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self._env,
            stdin=subprocess.DEVNULL,
        )


def _read_head(git: _Git) -> Head:
    symbolic = git.run_optional("symbolic-ref", "-q", "--short", "HEAD")
    commit = git.run_optional("rev-parse", "-q", "--verify", "HEAD^{commit}")
    return Head(
        branch_name=symbolic.strip() if symbolic else None,
        commit_hash=commit.strip() if commit else None,
    )


def _read_branches(git: _Git) -> tuple[Branch, ...]:
    output = git.run("for-each-ref", "--format=%(refname:short)%00%(objectname)", "refs/heads")
    branches = []
    for line in output.splitlines():
        name, commit_hash = line.split("\0")
        branches.append(Branch(name=name, commit_hash=commit_hash))
    return tuple(branches)


def _read_commits(git: _Git, *, has_head_commit: bool) -> tuple[Commit, ...]:
    """Commits reachable from local branches and HEAD, newest first (topological order)."""
    revisions = ["--branches"]
    if has_head_commit:
        revisions.append("HEAD")
    output = git.run("log", "--topo-order", "--format=%H%x00%P%x00%s%x1e", *revisions, "--")
    commits = []
    for record in output.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        commit_hash, parents, subject = record.split("\0", 2)
        commits.append(Commit(hash=commit_hash, parents=tuple(parents.split()), subject=subject))
    return tuple(commits)
