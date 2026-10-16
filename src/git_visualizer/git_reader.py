"""Git reader: reads the Observed Repository via the git CLI (ADR 0003).

Passive by design (ADR 0001): only read-only commands are run, with optional locks
disabled, so the Observed Repository is never modified and no lock files are taken.
"""

from __future__ import annotations

from pathlib import Path

from git_visualizer.file_status import STATUS_ARGS, parse_status
from git_visualizer.git_cli import GitCli, GitError
from git_visualizer.in_progress_operation import read_in_progress_operation
from git_visualizer.remote_reader import read_remotes
from git_visualizer.snapshot import Branch, Commit, Head, RepositorySnapshot, Tag

DEFAULT_MAX_COMMITS = 30
"""Default display limit: how many of the most recent commits the History shows."""

_COMMIT_FORMAT = "--format=%H%x00%P%x00%s%x1e"


class NotARepositoryError(GitError):
    pass


def read_snapshot(
    repository_path: Path, *, max_commits: int = DEFAULT_MAX_COMMITS
) -> RepositorySnapshot:
    """Read an immutable Repository Snapshot of the repository at ``repository_path``.

    The History holds commits reachable from local branches, Remote-tracking Branches,
    tags and HEAD (never ``refs/stash``): the ``max_commits`` most recent ones plus any ref tip beyond them.
    """
    git = GitCli(repository_path)
    if git.run_optional("rev-parse", "--absolute-git-dir") is None:
        raise NotARepositoryError(str(repository_path))
    head = _read_head(git)
    branches = _read_branches(git)
    tags = _read_tags(git)
    remotes, remote_tracking_branches = read_remotes(git)
    tips = [branch.commit_hash for branch in branches]
    tips += [tracking.commit_hash for tracking in remote_tracking_branches]
    tips += [tag.commit_hash for tag in tags]
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
        remote_tracking_branches=remote_tracking_branches,
        remotes=remotes,
        in_progress_operation=read_in_progress_operation(git, working_tree),
    )


def _read_head(git: GitCli) -> Head:
    symbolic = git.run_optional("symbolic-ref", "-q", "--short", "HEAD")
    commit = git.run_optional("rev-parse", "-q", "--verify", "HEAD^{commit}")
    return Head(
        branch_name=symbolic.strip() if symbolic else None,
        commit_hash=commit.strip() if commit else None,
    )


def _read_branches(git: GitCli) -> tuple[Branch, ...]:
    """Local branches with their configured Upstream and ahead/behind against it."""
    output = git.run(
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:track,nobracket)",
        "refs/heads",
    )
    branches = []
    for line in output.splitlines():
        name, commit_hash, upstream, track = line.split("\0")
        ahead, behind = _parse_track(track) if upstream else (None, None)
        branches.append(
            Branch(name=name, commit_hash=commit_hash, upstream=upstream or None, ahead=ahead, behind=behind)
        )
    return tuple(branches)


def _parse_track(track: str) -> tuple[int | None, int | None]:
    """``ahead 2, behind 1`` → (2, 1); in sync → (0, 0); Upstream ref gone → (None, None)."""
    if track == "gone":
        return None, None
    counts = {"ahead": 0, "behind": 0}
    for part in filter(None, (p.strip() for p in track.split(","))):
        direction, _, count = part.partition(" ")
        counts[direction] = int(count)
    return counts["ahead"], counts["behind"]


def _read_tags(git: GitCli) -> tuple[Tag, ...]:
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
    git: GitCli, tips: list[str], *, max_commits: int
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
