"""Ghost Commits: commits that were reachable before a state change and are not after.

The rule (spec, "Ghost Commits"):

* A commit shown in the previous Repository Snapshot becomes a Ghost Commit when no
  shown ref or HEAD reaches it any more (``refs/stash`` does not count). Commits that
  only dropped out of the display limit are still reachable and do not.
* Ghost Commits are cleared by the next transition that moves a ref
  (:attr:`Transition.moves_ref`); the transition that created them does not clear
  them. Other changes (HEAD only, Working Tree, Staging Area) keep them.
* A Ghost Commit shown again (e.g. checked out) is an ordinary commit again, and does
  not grow in again as an added commit.
* :meth:`GhostCommits.clear` drops them all (``Esc``); a fresh start has none.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace

from git_visualizer.live_view.transitions import Transition, TransitionKind
from git_visualizer.snapshot import Commit, RepositorySnapshot


@dataclass(frozen=True)
class GhostCommit:
    commit: Commit
    color_index: int
    """The color the commit had while it was reachable."""


class GhostCommits:
    def __init__(self) -> None:
        self._ghosts: dict[str, GhostCommit] = {}
        self._shown_colors: dict[str, int] = {}

    def update(
        self,
        previous: RepositorySnapshot,
        current: RepositorySnapshot,
        transitions: Sequence[Transition],
        *,
        unreachable: Callable[[list[str]], set[str]],
    ) -> list[Transition]:
        """Apply the change ``previous`` → ``current``; ``unreachable`` filters hashes no
        shown ref reaches. Returns ``transitions`` without the ``commitAdded`` of former
        Ghost Commits: they are already on screen, so they must not grow in."""
        previous_ghosts = set(self._ghosts)
        shown = {commit.hash for commit in current.commits}
        moves_ref = any(transition.moves_ref for transition in transitions)
        # Older ghosts first: a ghost's parent may only become a ghost later, and the
        # layout walks chains from child to parent.
        kept = {} if moves_ref else {h: g for h, g in self._ghosts.items() if h not in shown}
        candidates = [commit for commit in previous.commits if commit.hash not in shown]
        gone = unreachable([commit.hash for commit in candidates]) if candidates else set()
        kept.update(
            (commit.hash, GhostCommit(commit, self._shown_colors.get(commit.hash, -1)))
            for commit in candidates  # newest first, children before parents
            if commit.hash in gone
        )
        self._ghosts = kept
        return [
            transition
            for transition in transitions
            if not (transition.kind is TransitionKind.COMMIT_ADDED and transition.to_hash in previous_ghosts)
        ]

    def remember_shown_colors(self, colors: Mapping[str, int]) -> None:
        """The colors of the commits as just shown, kept by those that become ghosts."""
        self._shown_colors = dict(colors)

    def shown_with(self, snapshot: RepositorySnapshot) -> RepositorySnapshot:
        """``snapshot`` with the Ghost Commits appended after its reachable commits."""
        return replace(snapshot, commits=snapshot.commits + self.commits)

    def clear(self) -> None:
        self._ghosts = {}

    @property
    def hashes(self) -> list[str]:
        return list(self._ghosts)

    @property
    def commits(self) -> tuple[Commit, ...]:
        """The Ghost Commits, ordered so that children come before their parents."""
        return tuple(ghost.commit for ghost in self._ghosts.values())

    def color_index(self, commit_hash: str) -> int | None:
        """The ghost's color, or ``None`` if ``commit_hash`` is no Ghost Commit."""
        ghost = self._ghosts.get(commit_hash)
        return None if ghost is None else ghost.color_index
