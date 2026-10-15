"""Git reader: reads the Observed Repository via the git CLI (ADR 0003).

Passive by design (ADR 0001): only read-only commands are run, with optional locks
disabled, so the Observed Repository is never modified and no lock files are taken.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from git_visualizer.file_status import STATUS_ARGS, parse_status
from git_visualizer.snapshot import Branch, Commit, Head, RepositorySnapshot, Tag

DEFAULT_MAX_COMMITS = 30
"""Default display limit: how many of the most recent commits the History shows."""

_COMMIT_FORMAT = "--format=%H%x00%P%x00%s%x1e"


class GitError(RuntimeError):
    pass


class NotARepositoryError(GitError):
    pass


def read_snapshot(
    repository_path: Path, *, max_commits: int = DEFAULT_MAX_COMMITS
) -> RepositorySnapshot:
    """Read an immutable Repository Snapshot of the repository at ``repository_path``.

    The History holds commits reachable from local branches, tags and HEAD (never
    ``refs/stash``): the ``max_commits`` most recent ones plus any ref tip beyond them.
    """
    git = _Git(repository_path)
    if git.run_optional("rev-parse", "--git-dir") is None:
        raise NotARepositoryError(str(repository_path))
    head = _read_head(git)
    branches = _read_branches(git)
    tags = _read_tags(git)
    tips = [branch.commit_hash for branch in branches] + [tag.commit_hash for tag in tags]
    if head.commit_hash is not None:
        tips.append(head.commit_hash)
    commits, hidden_commit_count = _read_commits(git, tips, max_commits=max_commits)
    working_tree, staging_area = parse_status(git.run(*STATUS_ARGS))
    return RepositorySnapshot(
        commits=commits,
        branches=branches,
        head=head,
        tags=tags,
        hidden_commit_count=hidden_commit_count,
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


def _read_tags(git: _Git) -> tuple[Tag, ...]:
    """Tags pointing (directly or via an annotated tag) at a commit."""
    output = git.run(
        "for-each-ref",
        "--format=%(refname:short)%00%(objecttype)%00%(objectname)%00%(*objecttype)%00%(*objectname)",
        "refs/tags",
    )
    tags = []
    for line in output.splitlines():
        name, kind, target, peeled_kind, peeled_target = line.split("\0")
        if kind == "commit":
            tags.append(Tag(name=name, commit_hash=target))
        elif peeled_kind == "commit":
            tags.append(Tag(name=name, commit_hash=peeled_target))
    return tuple(tags)


def _read_commits(
    git: _Git, tips: list[str], *, max_commits: int
) -> tuple[tuple[Commit, ...], int]:
    """The most recent ``max_commits`` commits reachable from ``tips`` (children before
    parents), plus tips not among them; and how many reachable commits are left out."""
    if not tips:
        return (), 0
    revisions = "\n".join(dict.fromkeys(tips)) + "\n"
    commits = _parse_commits(
        git.run("log", "--date-order", f"--max-count={max_commits}", _COMMIT_FORMAT, "--stdin", stdin=revisions)
    )
    if len(commits) < max_commits:
        return tuple(commits), 0
    shown = {commit.hash for commit in commits}
    missing_tips = [tip for tip in dict.fromkeys(tips) if tip not in shown]
    if missing_tips:
        commits += _parse_commits(
            git.run("log", "--no-walk=unsorted", _COMMIT_FORMAT, "--stdin", stdin="\n".join(missing_tips) + "\n")
        )
    total = int(git.run("rev-list", "--count", "--stdin", stdin=revisions).strip())
    return tuple(commits), total - len(commits)


def _parse_commits(output: str) -> list[Commit]:
    commits = []
    for record in output.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        commit_hash, parents, subject = record.split("\0", 2)
        commits.append(Commit(hash=commit_hash, parents=tuple(parents.split()), subject=subject))
    return commits
