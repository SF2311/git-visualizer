"""Layout: positions History elements of a Repository Snapshot.

Columns are by ancestry, not timestamp: each commit sits one column right of its
newest (right-most) parent; root commits are in column 0.
"""

from __future__ import annotations

from collections.abc import Sequence

from git_visualizer.snapshot import Commit


def commit_columns(commits: Sequence[Commit]) -> dict[str, int]:
    """Column per commit hash. Parents not in ``commits`` count as column -1."""
    by_hash = {commit.hash: commit for commit in commits}
    columns: dict[str, int] = {}
    for start in commits:
        stack = [start.hash]
        while stack:
            current = stack[-1]
            if current in columns:
                stack.pop()
                continue
            pending = [p for p in by_hash[current].parents if p in by_hash and p not in columns]
            if pending:
                stack.extend(pending)
                continue
            columns[current] = 1 + max(
                (columns.get(p, -1) for p in by_hash[current].parents), default=-1
            )
            stack.pop()
    return columns
