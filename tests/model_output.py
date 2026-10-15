"""Read Live View model output exactly as QML sees it (Qt properties and role names)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractItemModel, QObject


def prop(model: QObject, name: str) -> Any:
    """A Qt property of ``model``, read through the meta-object like QML does."""
    if model.metaObject().indexOfProperty(name) < 0:
        raise AttributeError(f"{type(model).__name__} has no Qt property {name!r}")
    return model.property(name)


def rows(model: QObject, list_property: str) -> list[dict[str, Any]]:
    """All rows of the list model property ``list_property``, keyed by QML role names."""
    list_model = prop(model, list_property)
    assert isinstance(list_model, QAbstractItemModel)
    role_names = {role: bytes(name.data()).decode() for role, name in list_model.roleNames().items()}
    result: list[dict[str, Any]] = []
    for row in range(list_model.rowCount()):
        index = list_model.index(row, 0)
        result.append({name: list_model.data(index, role) for role, name in role_names.items()})
    return result
