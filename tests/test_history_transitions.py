"""Ticket 05: animated History transitions — the model compares consecutive Repository
Snapshots and exposes what changed, and updates its lists row by row (keyed) so the
view's delegates persist and can animate instead of being rebuilt."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from conftest import GitRepo
from model_output import prop, rows
from PySide6.QtCore import QAbstractItemModel

from git_visualizer.live_view import LiveViewModel


def _watching(repo: GitRepo) -> LiveViewModel:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    return model


def _transitions(model: LiveViewModel) -> set[tuple[str, str, str, str, str]]:
    return {
        (t["kind"], t["refType"], t["refName"], t["fromHash"], t["toHash"])
        for t in rows(model, "transitions")
    }


def _head(repo: GitRepo) -> str:
    return repo.git("rev-parse", "HEAD").strip()


def test_the_first_refresh_has_no_transitions(repo: GitRepo) -> None:
    repo.commit("Erster Commit")

    model = _watching(repo)

    assert _transitions(model) == set()
    assert prop(model, "addedCommitHashes") == []


def test_new_commit_is_added_and_moves_its_branch_and_head(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    model = _watching(repo)

    second = repo.commit("Zweiter Commit")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("commitAdded", "", "", "", second),
        ("refMoved", "branch", "main", first, second),
        ("headMoved", "", "", first, second),
    }
    assert prop(model, "addedCommitHashes") == [second]


def test_first_commit_in_a_fresh_repository(repo: GitRepo) -> None:
    model = _watching(repo)

    first = repo.commit("Erster Commit")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("commitAdded", "", "", "", first),
        ("refAdded", "branch", "main", "", first),
        ("headMoved", "", "", "", first),
    }


def test_branch_created(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    model = _watching(repo)

    repo.git("branch", "feature")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {("refAdded", "branch", "feature", "", first)}


def test_switch_moves_head_and_attaches_it_to_the_other_branch(repo: GitRepo) -> None:
    base = repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    feature = repo.commit("Feature", file="feature.txt")
    model = _watching(repo)

    repo.git("switch", "-q", "main")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("headMoved", "", "", feature, base),
        ("headAttached", "branch", "main", "", ""),
    }


def test_detaching_head(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    second = repo.commit("Zweiter Commit")
    model = _watching(repo)

    repo.git("checkout", "-q", "--detach", first)
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("headMoved", "", "", second, first),
        ("headDetached", "branch", "main", "", ""),
    }


def test_fast_forward_merge_moves_the_label_without_adding_a_commit(repo: GitRepo) -> None:
    base = repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    feature = repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    model = _watching(repo)

    repo.git("merge", "-q", "--ff-only", "feature")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("refMoved", "branch", "main", base, feature),
        ("headMoved", "", "", base, feature),
    }
    assert prop(model, "addedCommitHashes") == []


def test_three_way_merge_adds_the_merge_commit(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    main = repo.commit("Hauptlinie")
    model = _watching(repo)

    repo.git("merge", "-q", "--no-edit", "feature")
    model.notifyRepositoryChanged()
    merge = _head(repo)

    assert _transitions(model) == {
        ("commitAdded", "", "", "", merge),
        ("refMoved", "branch", "main", main, merge),
        ("headMoved", "", "", main, merge),
    }


def test_deleted_branch_label_is_removed_and_kept_as_leaving_label(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    feature = repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    repo.git("merge", "-q", "--ff-only", "feature")
    model = _watching(repo)
    [before] = [b for b in rows(model, "branchLabels") if b["name"] == "feature"]

    repo.git("branch", "-q", "-d", "feature")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {("refRemoved", "branch", "feature", feature, "")}
    assert [b["name"] for b in rows(model, "branchLabels")] == ["main"]
    assert rows(model, "leavingLabels") == [
        {
            "refType": "branch",
            "name": "feature",
            "colorIndex": before["colorIndex"],
            "column": before["column"],
            "lane": before["lane"],
            "stackIndex": before["stackIndex"],
        }
    ]


def test_tags_added_moved_and_removed(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    model = _watching(repo)

    repo.git("tag", "v1")
    model.notifyRepositoryChanged()
    assert _transitions(model) == {("refAdded", "tag", "v1", "", first)}

    second = repo.commit("Zweiter Commit")
    repo.git("tag", "-f", "v1")
    model.notifyRepositoryChanged()
    assert ("refMoved", "tag", "v1", first, second) in _transitions(model)

    repo.git("tag", "-d", "v1")
    model.notifyRepositoryChanged()
    assert _transitions(model) == {("refRemoved", "tag", "v1", second, "")}
    assert [(label["refType"], label["name"]) for label in rows(model, "leavingLabels")] == [("tag", "v1")]


def test_only_the_coalesced_difference_is_reported(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    model = _watching(repo)

    second = repo.commit("Zweiter Commit")
    third = repo.commit("Dritter Commit")
    repo.git("branch", "kurzlebig")
    repo.git("branch", "-q", "-D", "kurzlebig")
    model.notifyRepositoryChanged()

    assert _transitions(model) == {
        ("commitAdded", "", "", "", second),
        ("commitAdded", "", "", "", third),
        ("refMoved", "branch", "main", first, third),
        ("headMoved", "", "", first, third),
    }


def test_refresh_without_changes_has_no_transitions(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = _watching(repo)
    repo.commit("Zweiter Commit")
    model.notifyRepositoryChanged()

    model.notifyRepositoryChanged()

    assert _transitions(model) == set()
    assert prop(model, "addedCommitHashes") == []


def test_working_tree_change_keeps_leaving_labels(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("branch", "feature")
    model = _watching(repo)
    repo.git("branch", "-q", "-d", "feature")
    model.notifyRepositoryChanged()

    repo.write("notizen.txt", "neu\n")
    model.notifyRepositoryChanged()

    assert [label["name"] for label in rows(model, "leavingLabels")] == ["feature"]


# --- Keyed list updates: delegates persist across refreshes -----------------------


class _ListSignals:
    def __init__(self, list_model: QAbstractItemModel) -> None:
        self.events: list[tuple[str, int, int]] = []
        list_model.modelReset.connect(lambda: self.events.append(("reset", -1, -1)))
        list_model.rowsInserted.connect(lambda _p, first, last: self.events.append(("inserted", first, last)))
        list_model.rowsRemoved.connect(lambda _p, first, last: self.events.append(("removed", first, last)))
        list_model.rowsMoved.connect(lambda *_args: self.events.append(("moved", -1, -1)))
        list_model.dataChanged.connect(
            lambda top, bottom, *_args: self.events.append(("changed", top.row(), bottom.row()))
        )


@contextmanager
def _recording(model: LiveViewModel, list_property: str) -> Iterator[list[tuple[str, int, int]]]:
    list_model = prop(model, list_property)
    assert isinstance(list_model, QAbstractItemModel)
    signals = _ListSignals(list_model)
    yield signals.events


def _hashes(model: LiveViewModel) -> list[Any]:
    return [c["hash"] for c in rows(model, "commits")]


def test_new_commit_is_inserted_as_one_row_without_a_reset(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = _watching(repo)

    with _recording(model, "commits") as events:
        second = repo.commit("Zweiter Commit")
        model.notifyRepositoryChanged()

    position = _hashes(model).index(second)
    assert events == [("inserted", position, position)]


def test_moved_branch_label_is_updated_in_place(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = _watching(repo)

    with _recording(model, "branchLabels") as events:
        repo.commit("Zweiter Commit")
        model.notifyRepositoryChanged()

    assert events == [("changed", 0, 0)]


def test_deleted_branch_label_is_removed_as_one_row(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("branch", "feature")
    model = _watching(repo)
    position = [b["name"] for b in rows(model, "branchLabels")].index("feature")

    with _recording(model, "branchLabels") as events:
        repo.git("branch", "-q", "-d", "feature")
        model.notifyRepositoryChanged()

    assert ("removed", position, position) in events
    assert not any(kind in ("reset", "inserted") for kind, _first, _last in events)


def test_unchanged_refresh_emits_no_row_signals(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("tag", "v1")
    model = _watching(repo)

    with _recording(model, "commits") as commits, _recording(model, "edges") as edges, _recording(
        model, "branchLabels"
    ) as labels, _recording(model, "tagLabels") as tags, _recording(model, "laneBands") as bands:
        model.notifyRepositoryChanged()

    assert (commits, edges, labels, tags, bands) == ([], [], [], [], [])


class _Mirror:
    """A view's copy of a list model, kept only through the model's row signals."""

    def __init__(self, list_model: QAbstractItemModel) -> None:
        self._model = list_model
        self._roles = list_model.roleNames()
        self.rows: list[dict[str, Any]] = [self._read(row) for row in range(list_model.rowCount())]
        list_model.modelReset.connect(self._reset)
        list_model.rowsInserted.connect(self._inserted)
        list_model.rowsRemoved.connect(self._removed)
        list_model.rowsMoved.connect(self._moved)
        list_model.dataChanged.connect(self._changed)

    def _read(self, row: int) -> dict[str, Any]:
        index = self._model.index(row, 0)
        return {bytes(name.data()).decode(): self._model.data(index, role) for role, name in self._roles.items()}

    def _reset(self) -> None:
        self.rows = [self._read(row) for row in range(self._model.rowCount())]

    def _inserted(self, _parent: Any, first: int, last: int) -> None:
        self.rows[first:first] = [self._read(row) for row in range(first, last + 1)]

    def _removed(self, _parent: Any, first: int, last: int) -> None:
        del self.rows[first : last + 1]

    def _moved(self, _parent: Any, first: int, last: int, _destination: Any, row: int) -> None:
        moving = self.rows[first : last + 1]
        del self.rows[first : last + 1]
        row = row - len(moving) if row > last else row
        self.rows[row:row] = moving

    def _changed(self, top: Any, bottom: Any, *_args: Any) -> None:
        for row in range(top.row(), bottom.row() + 1):
            self.rows[row] = self._read(row)


def test_row_signals_keep_a_view_in_step_with_the_lists(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature 1", file="feature.txt")
    repo.git("tag", "v1")
    model = _watching(repo)
    names = ("commits", "edges", "branchLabels", "tagLabels", "laneBands", "leavingLabels")
    mirrors: dict[str, _Mirror] = {}
    for name in names:
        list_model = prop(model, name)
        assert isinstance(list_model, QAbstractItemModel)
        mirrors[name] = _Mirror(list_model)

    steps: list[Callable[[], object]] = [
        lambda: repo.git("switch", "-q", "main"),
        lambda: repo.commit("Hauptlinie"),
        lambda: repo.git("switch", "-q", "-c", "zweig"),
        lambda: repo.commit("Zweig", file="zweig.txt"),
        lambda: repo.git("switch", "-q", "main"),
        lambda: repo.git("merge", "-q", "--no-edit", "feature"),
        lambda: repo.git("rebase", "-q", "main", "zweig"),
        lambda: repo.git("branch", "-q", "-D", "feature"),
        lambda: repo.git("tag", "-d", "v1"),
        lambda: repo.git("checkout", "-q", "--detach", "HEAD~1"),
    ]
    for step in steps:
        step()
        model.notifyRepositoryChanged()
        for name in names:
            assert mirrors[name].rows == rows(model, name), name
