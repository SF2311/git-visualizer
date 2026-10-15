"""Layout: positions History elements of a Repository Snapshot.

* Columns are by ancestry, not timestamp: each commit sits one column right of its
  newest (right-most) parent; root commits (and commits whose parents are hidden by the
  display limit) are in column 0.
* Lanes (rows): every branch owns the commits along its first-parent chain that no
  earlier branch owns; branches are taken in the given (stable) order, each owning
  branch gets its own lane. Commits owned by no branch (detached HEAD, tags, merged and
  deleted branches) form anonymous chains packed into free space of the lanes below.
* Labels on one commit are stacked: detached HEAD nearest the commit, then branch
  labels in branch order, then tags. An attached HEAD sits directly above its
  branch label.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from git_visualizer.snapshot import Branch, Commit, RepositorySnapshot

_LANE_GAP = 1
"""Empty columns required between two chains sharing a lane."""


@dataclass(frozen=True)
class LaneBand:
    """The stretch of a lane owned by ``branch``, from ``first_column`` to ``last_column``."""

    lane: int
    branch: str
    first_column: int
    last_column: int


@dataclass(frozen=True)
class HistoryLayout:
    columns: dict[str, int]
    lanes: dict[str, int]
    owners: dict[str, str | None]
    """Branch owning each commit (``None`` for commits on an anonymous chain)."""
    bands: tuple[LaneBand, ...]
    branch_slots: dict[str, int]
    tag_slots: dict[str, int]
    head_slot: int
    """Stack slot of the HEAD marker on its commit; -1 when HEAD has no commit."""
    lane_label_slots: tuple[int, ...]
    """Per lane: the most label slots used on any one of its commits."""

    @property
    def column_count(self) -> int:
        return 1 + max(self.columns.values(), default=-1)


def layout_history(snapshot: RepositorySnapshot, branch_order: Sequence[str]) -> HistoryLayout:
    """Lay out ``snapshot``; ``branch_order`` ranks branches for lane ownership."""
    commits = snapshot.commits
    columns = commit_columns(commits)
    by_hash = {commit.hash: commit for commit in commits}
    rank = {name: index for index, name in enumerate(branch_order)}
    branches = sorted(snapshot.branches, key=lambda b: (rank.get(b.name, len(rank)), b.name))

    owners: dict[str, str | None] = {}

    def claim_chain(tip: str, owner: str | None) -> list[str]:
        chain = []
        current: str | None = tip
        while current is not None and current in by_hash and current not in owners:
            owners[current] = owner
            chain.append(current)
            parents = by_hash[current].parents
            current = parents[0] if parents else None
        return chain

    branch_chains = [(b.name, claim_chain(b.commit_hash, b.name)) for b in branches]
    branch_chains = [(name, chain) for name, chain in branch_chains if chain]
    other_tips = [snapshot.head.commit_hash] if snapshot.head.commit_hash else []
    other_tips += [tag.commit_hash for tag in snapshot.tags]
    other_tips += [commit.hash for commit in commits]
    anonymous_chains = [chain for tip in other_tips if (chain := claim_chain(tip, None))]

    lanes: dict[str, int] = {}
    occupied: list[list[tuple[int, int]]] = []
    bands = []
    for name, chain in branch_chains:
        span = _span(chain, columns)
        bands.append(LaneBand(lane=len(occupied), branch=name, first_column=span[0], last_column=span[1]))
        lanes.update(dict.fromkeys(chain, len(occupied)))
        occupied.append([span])
    first_shared_lane = 1 if occupied else 0
    for chain in anonymous_chains:
        span = _span(chain, columns)
        lane = first_shared_lane
        while lane < len(occupied) and any(_overlaps(span, other) for other in occupied[lane]):
            lane += 1
        if lane == len(occupied):
            occupied.append([])
        occupied[lane].append(span)
        lanes.update(dict.fromkeys(chain, lane))

    branch_slots, tag_slots, head_slot, slots_per_commit = _stack_labels(snapshot, branches)
    lane_label_slots = [0] * len(occupied)
    for commit_hash, count in slots_per_commit.items():
        if commit_hash in lanes:
            lane = lanes[commit_hash]
            lane_label_slots[lane] = max(lane_label_slots[lane], count)

    return HistoryLayout(
        columns=columns,
        lanes=lanes,
        owners=owners,
        bands=tuple(bands),
        branch_slots=branch_slots,
        tag_slots=tag_slots,
        head_slot=head_slot,
        lane_label_slots=tuple(lane_label_slots),
    )


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


def _span(chain: Sequence[str], columns: dict[str, int]) -> tuple[int, int]:
    chain_columns = [columns[commit_hash] for commit_hash in chain]
    return min(chain_columns), max(chain_columns)


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return not (a[1] + _LANE_GAP < b[0] or b[1] + _LANE_GAP < a[0])


def _stack_labels(
    snapshot: RepositorySnapshot, ordered_branches: Sequence[Branch]
) -> tuple[dict[str, int], dict[str, int], int, dict[str, int]]:
    used: dict[str, int] = {}

    def next_slot(commit_hash: str) -> int:
        slot = used.get(commit_hash, 0)
        used[commit_hash] = slot + 1
        return slot

    head = snapshot.head
    head_slot = -1
    if head.commit_hash is not None and head.is_detached:
        head_slot = next_slot(head.commit_hash)
    branch_slots = {}
    for branch in ordered_branches:
        branch_slots[branch.name] = next_slot(branch.commit_hash)
        if branch.name == head.branch_name:
            head_slot = next_slot(branch.commit_hash)
    tag_slots = {tag.name: next_slot(tag.commit_hash) for tag in sorted(snapshot.tags, key=lambda t: t.name)}
    return branch_slots, tag_slots, head_slot, used
