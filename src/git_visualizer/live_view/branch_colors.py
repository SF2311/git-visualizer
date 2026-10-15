"""Stable branch colors and branch order across refreshes of one Live View session."""

from __future__ import annotations

from collections.abc import Iterable

PALETTE_SIZE = 8
"""Number of branch colors; must match ``Theme.branchColors`` in QML."""

_PRIMARY_BRANCHES = ("main", "master")


class BranchColors:
    """Remembers a color index and a rank per branch name for as long as it exists.

    A new branch gets the lowest color index not used by any current branch (wrapping
    around when all are taken) and ranks after all known branches; several new branches
    keep the order they are given in. ``main``/``master`` always rank first so the
    primary line stays in the top lane.
    """

    def __init__(self) -> None:
        self._colors: dict[str, int] = {}
        self._seen: dict[str, int] = {}
        self._counter = 0

    def update(self, branch_names: Iterable[str]) -> None:
        names = list(dict.fromkeys(branch_names))
        for gone in set(self._colors) - set(names):
            del self._colors[gone]
            del self._seen[gone]
        new_names = [name for name in names if name not in self._colors]
        for name in sorted(new_names, key=lambda name: name not in _PRIMARY_BRANCHES):
            used = set(self._colors.values())
            free = [index for index in range(PALETTE_SIZE) if index not in used]
            self._colors[name] = free[0] if free else len(self._colors) % PALETTE_SIZE
            self._seen[name] = self._counter
            self._counter += 1

    def color_index(self, branch_name: str) -> int:
        return self._colors[branch_name]

    def ordered_names(self) -> list[str]:
        return sorted(self._seen, key=lambda name: (name not in _PRIMARY_BRANCHES, self._seen[name]))
