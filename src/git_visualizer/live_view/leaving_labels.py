"""Leaving labels: removed branch, tag and Remote-tracking Branch labels, kept at their
last position so that the view can fade them out."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from git_visualizer.live_view.transitions import RefType, Transition, TransitionKind

LEAVING_LABEL_ROLES = ("refType", "name", "colorIndex", "column", "lane", "stackIndex")
_NO_COLOR = -1


class LeavingLabels:
    def __init__(self) -> None:
        self._shown: dict[tuple[str, str], dict[str, Any]] = {}

    def remember(
        self,
        branch_rows: Sequence[dict[str, Any]],
        tag_rows: Sequence[dict[str, Any]],
        tracking_rows: Sequence[dict[str, Any]],
    ) -> None:
        """Keep where each label is drawn now, so a removed one can fade out there."""
        labelled = [(RefType.BRANCH, row, row["colorIndex"]) for row in branch_rows]
        labelled += [(RefType.TAG, row, _NO_COLOR) for row in tag_rows]
        labelled += [(RefType.REMOTE_TRACKING, row, row["colorIndex"]) for row in tracking_rows]
        self._shown = {
            (str(ref_type), row["name"]): {
                "refType": str(ref_type),
                "name": row["name"],
                "colorIndex": color,
                "column": row["column"],
                "lane": row["lane"],
                "stackIndex": row["stackIndex"],
            }
            for ref_type, row, color in labelled
            if row["column"] >= 0
        }

    def removed_by(self, transitions: Sequence[Transition]) -> list[dict[str, Any]] | None:
        """The remembered labels whose refs ``transitions`` remove; ``None`` when no
        transition moves a ref, so the labels leaving before stay as they are."""
        if not any(transition.moves_ref for transition in transitions):
            return None
        return [
            self._shown[(transition.ref_type, transition.ref_name)]
            for transition in transitions
            if transition.kind is TransitionKind.REF_REMOVED
            and (transition.ref_type, transition.ref_name) in self._shown
        ]
