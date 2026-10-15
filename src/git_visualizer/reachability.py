"""Reachability in the Observed Repository, read via the git CLI (ADR 0003).

Read-only like the rest of the git reader (ADR 0001): ``rev-list`` never writes.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from git_visualizer.git_reader import _Git


def unreachable_commits(
    repository_path: Path, candidates: Sequence[str], *, head_commit: str | None
) -> set[str]:
    """Those of ``candidates`` that no shown ref reaches: no local branch, tag,
    Remote-tracking Branch or HEAD (``head_commit``). ``refs/stash`` does not count.

    Candidates git no longer knows are left out; if git fails, the result is empty.
    """
    if not candidates:
        return set()
    shown_refs = ["--branches", "--tags", "--remotes"]
    if head_commit is not None:
        shown_refs.append(head_commit)
    output = _Git(repository_path).run_optional(
        "rev-list", "--ignore-missing", *candidates, "--not", *shown_refs
    )
    if output is None:
        return set()
    return set(output.split()) & set(candidates)
