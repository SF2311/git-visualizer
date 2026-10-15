"""A small read-only list model for QML, backed by rows of plain values."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from typing import Any

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, QObject, QPersistentModelIndex, Qt


class RowListModel(QAbstractListModel):
    """List model whose rows are mappings from QML role name to value.

    With ``key_roles``, :meth:`set_rows` updates row by row: rows whose key is gone are
    removed, new keys are inserted, kept rows are moved into the new order and changed
    in place. QML delegates of kept rows then persist (and can animate their changes)
    instead of being rebuilt. Without ``key_roles`` every update resets the model.
    """

    def __init__(
        self,
        role_names: Sequence[str],
        parent: QObject | None = None,
        *,
        key_roles: Sequence[str] = (),
    ) -> None:
        super().__init__(parent)
        self._role_names = tuple(role_names)
        self._key_roles = tuple(key_roles)
        unknown = set(self._key_roles) - set(self._role_names)
        if unknown:
            raise ValueError(f"key roles {sorted(unknown)} are not roles")
        self._rows: list[Mapping[str, Any]] = []

    def set_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        for row in rows:
            missing = set(self._role_names) - row.keys()
            if missing:
                raise ValueError(f"row is missing roles {sorted(missing)}")
        if not self._key_roles:
            self.beginResetModel()
            self._rows = list(rows)
            self.endResetModel()
            return
        new_keys = [self._key(row) for row in rows]
        if len(set(new_keys)) != len(new_keys):
            raise ValueError("rows have duplicate keys")
        self._remove_rows_not_in(set(new_keys))
        for position, row in enumerate(rows):
            self._place(position, row)

    def _key(self, row: Mapping[str, Any]) -> Hashable:
        return tuple(row[role] for role in self._key_roles)

    def _remove_rows_not_in(self, keys: set[Hashable]) -> None:
        position = len(self._rows) - 1
        while position >= 0:
            if self._key(self._rows[position]) in keys:
                position -= 1
                continue
            last = position
            while position >= 0 and self._key(self._rows[position]) not in keys:
                position -= 1
            self.beginRemoveRows(QModelIndex(), position + 1, last)
            del self._rows[position + 1 : last + 1]
            self.endRemoveRows()

    def _place(self, position: int, row: Mapping[str, Any]) -> None:
        """Make ``row`` the row at ``position``; rows before it are already in place."""
        key = self._key(row)
        current = next(
            (index for index in range(position, len(self._rows)) if self._key(self._rows[index]) == key),
            None,
        )
        if current is None:
            self.beginInsertRows(QModelIndex(), position, position)
            self._rows.insert(position, dict(row))
            self.endInsertRows()
            return
        if current != position:
            self.beginMoveRows(QModelIndex(), current, current, QModelIndex(), position)
            self._rows.insert(position, self._rows.pop(current))
            self.endMoveRows()
        if any(self._rows[position][role] != row[role] for role in self._role_names):
            self._rows[position] = dict(row)
            index = self.index(position, 0)
            self.dataChanged.emit(index, index)

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
