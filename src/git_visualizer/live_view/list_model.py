"""A small read-only list model for QML, backed by rows of plain values."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, QObject, QPersistentModelIndex, Qt


class RowListModel(QAbstractListModel):
    """List model whose rows are mappings from QML role name to value."""

    def __init__(self, role_names: Sequence[str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._role_names = tuple(role_names)
        self._rows: list[Mapping[str, Any]] = []

    def set_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        for row in rows:
            missing = set(self._role_names) - row.keys()
            if missing:
                raise ValueError(f"row is missing roles {sorted(missing)}")
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            Qt.ItemDataRole.UserRole + offset: QByteArray(name.encode())
            for offset, name in enumerate(self._role_names)
        }

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        offset = role - Qt.ItemDataRole.UserRole
        if not 0 <= offset < len(self._role_names):
            return None
        return self._rows[index.row()][self._role_names[offset]]
