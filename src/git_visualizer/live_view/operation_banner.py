"""German banner text explaining the In-progress Operation (e.g. "Merge läuft – 2 Konflikte")."""

from __future__ import annotations

from git_visualizer.snapshot import InProgressOperation, OperationKind

_NAMES = {
    OperationKind.MERGE: "Merge",
    OperationKind.REBASE: "Rebase",
    OperationKind.CHERRY_PICK: "Cherry-pick",
    OperationKind.REVERT: "Revert",
}


def banner_text(operation: InProgressOperation | None) -> str:
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
