"""What the Live View shows of the In-progress Operation (merge, rebase, cherry-pick, revert),
including the German banner text (e.g. "Merge läuft – 2 Konflikte")."""

from __future__ import annotations

from dataclasses import dataclass

from git_visualizer.snapshot import InProgressOperation, OperationKind

_NAMES = {
    OperationKind.MERGE: "Merge",
    OperationKind.REBASE: "Rebase",
    OperationKind.CHERRY_PICK: "Cherry-pick",
    OperationKind.REVERT: "Revert",
}


def _banner_text(operation: InProgressOperation | None) -> str:
    """The banner for ``operation``; "" when nothing is in progress.

    A rebase shows its progress ("Rebase 2/5") and only mentions conflicts while there
    are some; the other operations always say whether conflicts remain.
    """
    if operation is None:
        return ""
    name = _NAMES[operation.kind]
    if operation.kind is OperationKind.REBASE:
        progress = f"{name} {operation.step}/{operation.total}" if operation.total else f"{name} läuft"
        if operation.conflict_count == 0:
            return progress
        return f"{progress} – {_conflicts(operation.conflict_count)}"
    if operation.conflict_count == 0:
        return f"{name} läuft – keine Konflikte mehr"
    return f"{name} läuft – {_conflicts(operation.conflict_count)}"


def _conflicts(count: int) -> str:
    return "1 Konflikt" if count == 1 else f"{count} Konflikte"


@dataclass(frozen=True)
class OperationState:
    kind: str = ""
    """Empty when none, else ``merge``, ``rebase``, ``cherry-pick`` or ``revert``."""
    step: int = 0
    """Rebase progress; 0 when unknown or not a rebase (like ``total``)."""
    total: int = 0
    conflict_count: int = 0
    banner: str = ""
    """German banner text, e.g. "Merge läuft – 2 Konflikte"; empty when none."""

    @classmethod
    def of(cls, operation: InProgressOperation | None) -> OperationState:
        if operation is None:
            return cls()
        return cls(
            kind=operation.kind.value,
            step=operation.step,
            total=operation.total,
            conflict_count=operation.conflict_count,
            banner=_banner_text(operation),
        )
