"""Ticket 12: the lecture demo script.

The demo runs real git commands, but only inside a fresh temporary folder. These tests
point Python's temporary directory at ``tmp_path`` so that anything the demo creates
outside its own folder would show up there, run every step, and feed each step's
result through the Live View model to check what the audience is meant to see.
"""

from __future__ import annotations

import io
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from conftest import GitRepo
from model_output import prop, rows
from PySide6.QtGui import QGuiApplication

from git_visualizer import lecture_demo
from git_visualizer.lecture_demo import (
    STEPS,
    DemoFolder,
    Git,
    OutsideDemoFolderError,
    Step,
    Write,
    run_demo,
)
from git_visualizer.live_view import LiveViewModel


@pytest.fixture
def temp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The system temporary directory as seen by the demo, isolated per test."""
    root = tmp_path / "tmp"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    return root


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=path, check=True, capture_output=True, text=True
    ).stdout.strip()


def _quiet_run(**kwargs: Any) -> DemoFolder:
    return run_demo(out=io.StringIO(), **kwargs)


# --- Safety ------------------------------------------------------------------------


def test_the_demo_creates_everything_inside_one_new_temporary_folder(
    tmp_path: Path, temp_root: Path
) -> None:
    folder = _quiet_run(prompt=None)

    assert folder.root.parent == temp_root.resolve()
    assert folder.root.name.startswith("git-visualizer-demo-")
    assert [p.name for p in tmp_path.iterdir()] == ["tmp"]
    assert [p.name for p in temp_root.iterdir()] == [folder.root.name]
    assert {p.name for p in folder.root.iterdir()} == {"vorlesung", "server.git", "kollegin"}


def test_two_runs_never_share_a_folder(temp_root: Path) -> None:
    first = _quiet_run(prompt=lambda _: "q")
    second = _quiet_run(prompt=lambda _: "q")
    assert first.root != second.root
    assert not any(first.observed.iterdir()) and not any(second.observed.iterdir())


def test_commands_and_paths_outside_the_demo_folder_are_refused(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    (root / "vorlesung").mkdir(parents=True)
    folder = DemoFolder(root)

    with pytest.raises(OutsideDemoFolderError):
        folder.run(Git(("init", "../../anderswo")))
    with pytest.raises(OutsideDemoFolderError):
        folder.run(Git(("-C", "/", "status")))
    with pytest.raises(OutsideDemoFolderError):
        folder.run(Write("../../fremd.txt", "nein"))
    assert {p.name for p in tmp_path.iterdir()} == {"demo"}


def test_git_never_finds_a_repository_above_the_demo_folder(tmp_path: Path) -> None:
    outer = GitRepo(tmp_path)
    outer.git("init", "-q")
    root = tmp_path / "demo"
    (root / "vorlesung").mkdir(parents=True)

    # Without the ceiling, `git status` would report the outer repository and succeed.
    DemoFolder(root).run(Git(("status",), fails=True))


# --- Pausing -----------------------------------------------------------------------


def test_each_step_waits_for_enter_before_running_its_commands(temp_root: Path) -> None:
    folder = lecture_demo.create_demo_folder()
    prompts: list[str] = []
    finished: list[str] = []

    def enter(message: str) -> str:
        prompts.append(message)
        # Prompt 1 comes before any step, prompt n+1 before step n runs.
        assert len(finished) == max(0, len(prompts) - 2)
        if len(prompts) == 2:
            assert not (folder.observed / ".git").exists()
        return ""

    _quiet_run(prompt=enter, folder=folder, on_step_done=lambda step, _: finished.append(step.id))

    assert len(prompts) == len(STEPS) + 1
    assert len(finished) == len(STEPS)


def test_q_ends_the_demo_before_the_next_step_runs(temp_root: Path) -> None:
    answers = iter(["", "", "q"])  # start, run `git init`, quit before the next step
    folder = _quiet_run(prompt=lambda _: next(answers))

    assert (folder.observed / ".git").is_dir()
    assert not (folder.observed / "README.md").exists()


def test_the_demo_prints_explanations_commands_and_the_live_view_command(temp_root: Path) -> None:
    out = io.StringIO()
    folder = run_demo(prompt=None, out=out)
    text = out.getvalue()

    assert f"git-visualizer {folder.observed}" in text
    assert "$ git init -b main" in text
    assert "$ git rebase main" in text
    assert "Esc" in text
    assert "rm -rf" in text


def test_the_command_line_runs_without_pausing(temp_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert lecture_demo.main(["--no-pause"]) == 0
    [root] = list(temp_root.iterdir())
    assert _git(root / "vorlesung", "branch", "--show-current") == "neu"


# --- End state ---------------------------------------------------------------------


def test_after_all_steps_the_repositories_are_in_the_expected_state(temp_root: Path) -> None:
    folder = _quiet_run(prompt=None)
    observed = folder.observed

    assert _git(observed, "status", "--porcelain") == ""
    assert not (observed / ".git" / "MERGE_HEAD").exists()
    assert not (observed / ".git" / "rebase-merge").exists()
    assert _git(observed, "branch", "--show-current") == "neu"
    assert set(_git(observed, "branch", "--format=%(refname:short)").split()) == {"main", "login", "farbe", "neu"}
    assert _git(observed, "rev-parse", "main") == _git(observed, "rev-parse", "origin/main")
    assert _git(observed, "rev-parse", "--abbrev-ref", "neu@{upstream}") == "origin/neu"
    assert _git(folder.root / "server.git", "rev-parse", "--is-bare-repository") == "true"
    assert _git(folder.root / "server.git", "rev-parse", "main") == _git(observed, "rev-parse", "main")
    assert "Beitrag der Kollegin" in _git(observed, "log", "--format=%s", "main")
    assert (observed / "config.txt").read_text() == "farbe = lila\n"


# --- What the Live View shows at each step ------------------------------------------


@dataclass
class Facts:
    banner: str
    ghosts: int
    head_detached: bool
    head_is_merge: bool
    added_commits: int
    working_tree: dict[str, tuple[str, bool]]
    staging_area: dict[str, str]
    ahead_behind: dict[str, tuple[int, int]]
    remote_tracking: set[str]
    last_fetched: float | None
    file_transitions: set[tuple[str, str]]


def _facts(model: LiveViewModel) -> Facts:
    commits = rows(model, "commits")
    head = prop(model, "headCommitHash")
    remotes = rows(model, "remotes")
    return Facts(
        banner=prop(model, "operationBanner"),
        ghosts=sum(1 for c in commits if c["isGhost"]),
        head_detached=prop(model, "headDetached"),
        head_is_merge=any(c["isMerge"] for c in commits if c["hash"] == head),
        added_commits=len(prop(model, "addedCommitHashes")),
        working_tree={f["path"]: (f["change"], f["conflicted"]) for f in rows(model, "workingTreeFiles")},
        staging_area={f["path"]: f["change"] for f in rows(model, "stagingAreaFiles")},
        ahead_behind={b["name"]: (b["ahead"], b["behind"]) for b in rows(model, "branchLabels")},
        remote_tracking={label["name"] for label in rows(model, "remoteTrackingLabels")},
        last_fetched=remotes[0]["lastFetched"] if remotes else None,
        file_transitions={(t["kind"], t["path"]) for t in prop(model, "fileTransitions")},
    )


@pytest.fixture(scope="module")
def facts(qapp: QGuiApplication, tmp_path_factory: pytest.TempPathFactory) -> dict[str, Facts]:
    """The Live View model's view of the Observed Repository after every demo step."""
    patch = pytest.MonkeyPatch()
    patch.setattr(tempfile, "tempdir", str(tmp_path_factory.mktemp("demo-tmp")))
    models: list[LiveViewModel] = []
    result: dict[str, Facts] = {}

    def observe(step: Step, folder: DemoFolder) -> None:
        if not models:
            models.append(LiveViewModel(folder.observed))
        model = models[0]
        if step.live_view_key == "Esc":
            model.clearGhostCommits()
        else:
            model.notifyRepositoryChanged()
        result[step.id] = _facts(model)

    try:
        _quiet_run(prompt=None, on_step_done=observe)
    finally:
        patch.undo()
    return result


def test_every_step_is_observed(facts: dict[str, Facts]) -> None:
    assert list(facts) == [step.id for step in STEPS]
    assert len({step.id for step in STEPS}) == len(STEPS)


def test_add_and_partial_staging_move_files_between_the_columns(facts: dict[str, Facts]) -> None:
    assert facts["first-file"].working_tree == {"README.md": ("untracked", False)}
    assert facts["first-add"].staging_area == {"README.md": "new"}
    assert facts["first-add"].working_tree == {}
    assert ("fileCommitted", "README.md") in facts["first-commit"].file_transitions
    assert facts["first-commit"].staging_area == {}
    assert facts["partial-staging"].staging_area == {"README.md": "modified"}
    assert facts["partial-staging"].working_tree == {"README.md": ("modified", False)}
    assert ("fileMoved", "README.md") in facts["unstage"].file_transitions
    assert facts["unstage"].staging_area == {}


def test_fast_forward_adds_no_commit_but_the_three_way_merge_does(facts: dict[str, Facts]) -> None:
    assert facts["fast-forward"].added_commits == 0
    assert not facts["fast-forward"].head_is_merge
    assert facts["three-way-merge"].added_commits == 1
    assert facts["three-way-merge"].head_is_merge


def test_the_merge_conflict_shows_the_banner_until_the_merge_is_concluded(facts: dict[str, Facts]) -> None:
    assert facts["conflict"].banner == "Merge läuft – 1 Konflikt"
    assert facts["conflict"].working_tree["config.txt"][1] is True
    assert facts["resolve"].banner == "Merge läuft – keine Konflikte mehr"
    assert "config.txt" in facts["resolve"].staging_area
    assert "config.txt" not in facts["resolve"].working_tree
    assert facts["conclude-merge"].banner == ""
    assert facts["conclude-merge"].head_is_merge


def test_amend_rebase_and_branch_deletion_leave_ghost_commits(facts: dict[str, Facts]) -> None:
    assert facts["typo-commit"].ghosts == 0
    assert facts["amend"].ghosts == 1
    assert facts["rebase-setup"].ghosts == 0  # cleared by the next ref move
    assert facts["rebase"].ghosts == 2
    assert facts["clear-ghosts"].ghosts == 0  # Esc
    assert facts["delete-unmerged-branch"].ghosts == 3


def test_the_paused_rebase_shows_progress_and_a_detached_head(facts: dict[str, Facts]) -> None:
    assert facts["rebase-conflict"].banner == "Rebase 1/3 – 1 Konflikt"
    assert facts["rebase-conflict"].head_detached
    assert facts["rebase-abort"].banner == ""
    assert not facts["rebase-abort"].head_detached


def test_remote_steps_show_ahead_behind_against_the_upstream(facts: dict[str, Facts]) -> None:
    assert facts["remote-create"].remote_tracking == set()
    assert facts["push-upstream"].remote_tracking == {"origin/main"}
    assert facts["push-upstream"].last_fetched == 0  # a push is not a fetch
    main = {step: facts[step].ahead_behind["main"] for step in (
        "push-upstream", "local-ahead", "push", "colleague-pushes", "fetch", "diverged", "pull", "push-merged"
    )}
    assert main == {
        "push-upstream": (0, 0),
        "local-ahead": (1, 0),
        "push": (0, 0),
        "colleague-pushes": (0, 0),  # the Live View never fetches
        "fetch": (0, 1),
        "diverged": (1, 1),
        "pull": (2, 0),
        "push-merged": (0, 0),
    }
    last_fetched = facts["fetch"].last_fetched
    assert last_fetched is not None and last_fetched > 0


def test_a_branch_pushed_without_u_has_no_counter_until_it_gets_an_upstream(facts: dict[str, Facts]) -> None:
    assert "origin/neu" in facts["push-without-upstream"].remote_tracking
    assert facts["push-without-upstream"].ahead_behind["neu"] == (-1, -1)
    assert facts["set-upstream"].ahead_behind["neu"] == (0, 0)
