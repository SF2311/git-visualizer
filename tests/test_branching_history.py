"""Ticket 03: a branching History — columns by ancestry, lanes and colors per branch,
merge edges, HEAD attached/detached, tags, hidden stash, truncation to N commits."""

from __future__ import annotations

from typing import Any

from conftest import GitRepo
from model_output import prop, rows

from git_visualizer.live_view import LiveViewModel


def _refreshed(repo: GitRepo, **kwargs: Any) -> LiveViewModel:
    model = LiveViewModel(repo.path, **kwargs)
    model.notifyRepositoryChanged()
    return model


def _commits_by_hash(model: LiveViewModel) -> dict[str, dict[str, Any]]:
    return {c["hash"]: c for c in rows(model, "commits")}


def _edges(model: LiveViewModel) -> set[tuple[str, str]]:
    return {(e["childHash"], e["parentHash"]) for e in rows(model, "edges")}


def _branch(model: LiveViewModel, name: str) -> dict[str, Any]:
    [label] = [b for b in rows(model, "branchLabels") if b["name"] == name]
    return label


def _two_branches_with_three_way_merge(repo: GitRepo) -> dict[str, str]:
    base = repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    feature = repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    main = repo.commit("Hauptlinie")
    repo.git("merge", "-q", "--no-edit", "feature")
    merge = repo.git("rev-parse", "HEAD").strip()
    return {"base": base, "feature": feature, "main": main, "merge": merge}


def test_three_way_merge_has_edges_from_both_parents(repo: GitRepo) -> None:
    c = _two_branches_with_three_way_merge(repo)

    model = _refreshed(repo)

    assert _edges(model) == {
        (c["feature"], c["base"]),
        (c["main"], c["base"]),
        (c["merge"], c["main"]),
        (c["merge"], c["feature"]),
    }
    commits = _commits_by_hash(model)
    assert commits[c["merge"]]["isMerge"] is True
    assert commits[c["main"]]["isMerge"] is False


def test_columns_follow_ancestry_one_right_of_the_newest_parent(repo: GitRepo) -> None:
    c = _two_branches_with_three_way_merge(repo)

    commits = _commits_by_hash(_refreshed(repo))

    assert {name: commits[h]["column"] for name, h in c.items()} == {
        "base": 0,
        "feature": 1,
        "main": 1,
        "merge": 2,
    }


def test_columns_ignore_timestamps(repo: GitRepo) -> None:
    base = repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature 1", file="feature.txt")
    repo.commit("Feature 2", file="feature.txt")
    repo.git("switch", "-q", "main")
    # A commit dated far in the past still sits one column right of its parent.
    repo.write("old.txt", "alt\n")
    repo.git("add", "old.txt")
    old_date = {"GIT_COMMITTER_DATE": "2001-01-01T00:00:00", "GIT_AUTHOR_DATE": "2001-01-01T00:00:00"}
    repo.git("commit", "-q", "-m", "Alt datiert", env=old_date)
    old = repo.git("rev-parse", "HEAD").strip()

    commits = _commits_by_hash(_refreshed(repo))

    assert commits[base]["column"] == 0
    assert commits[old]["column"] == 1


def test_each_branch_has_its_own_lane_and_color(repo: GitRepo) -> None:
    c = _two_branches_with_three_way_merge(repo)

    model = _refreshed(repo)
    commits = _commits_by_hash(model)
    main, feature = _branch(model, "main"), _branch(model, "feature")

    assert main["colorIndex"] != feature["colorIndex"]
    for name in ("base", "main", "merge"):
        assert commits[c[name]]["lane"] == main["lane"] == 0
        assert commits[c[name]]["colorIndex"] == main["colorIndex"]
    assert commits[c["feature"]]["lane"] == feature["lane"] == 1
    assert commits[c["feature"]]["colorIndex"] == feature["colorIndex"]
    lanes = {band["lane"]: band for band in rows(model, "laneBands")}
    assert lanes[0]["colorIndex"] == main["colorIndex"]
    assert lanes[1]["colorIndex"] == feature["colorIndex"]
    assert (lanes[1]["firstColumn"], lanes[1]["lastColumn"]) == (1, 1)


def test_edges_take_the_color_of_the_branching_lane(repo: GitRepo) -> None:
    c = _two_branches_with_three_way_merge(repo)

    model = _refreshed(repo)
    feature_color = _branch(model, "feature")["colorIndex"]
    edges = {(e["childHash"], e["parentHash"]): e for e in rows(model, "edges")}

    fork = edges[(c["feature"], c["base"])]
    merge = edges[(c["merge"], c["feature"])]
    assert fork["colorIndex"] == merge["colorIndex"] == feature_color
    assert (fork["parentColumn"], fork["parentLane"], fork["childColumn"], fork["childLane"]) == (0, 0, 1, 1)
    assert (merge["parentColumn"], merge["parentLane"], merge["childColumn"], merge["childLane"]) == (1, 1, 2, 0)


def test_branch_colors_are_stable_across_refreshes(repo: GitRepo) -> None:
    _two_branches_with_three_way_merge(repo)
    model = _refreshed(repo)
    before = {b["name"]: b["colorIndex"] for b in rows(model, "branchLabels")}

    repo.git("branch", "aaa-neu")
    repo.git("switch", "-q", "feature")
    repo.commit("Weiter am Feature", file="feature.txt")
    model.notifyRepositoryChanged()

    after = {b["name"]: b["colorIndex"] for b in rows(model, "branchLabels")}
    assert after["main"] == before["main"]
    assert after["feature"] == before["feature"]
    assert after["aaa-neu"] not in (before["main"], before["feature"])


def test_detached_head_points_directly_at_a_commit(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    repo.commit("Zweiter Commit")
    repo.git("checkout", "-q", "--detach", first)

    model = _refreshed(repo)

    assert prop(model, "headDetached") is True
    assert prop(model, "headBranch") == ""
    assert prop(model, "headCommitHash") == first
    assert prop(model, "headColumn") == 0
    assert prop(model, "headLane") == 0
    assert _branch(model, "main")["hasHead"] is False


def test_attached_head_sits_directly_above_its_branch_label(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("branch", "feature")

    model = _refreshed(repo)

    assert prop(model, "headDetached") is False
    assert _branch(model, "main")["hasHead"] is True
    assert prop(model, "headStackIndex") == _branch(model, "main")["stackIndex"] + 1


def test_multiple_labels_on_one_commit_are_stacked(repo: GitRepo) -> None:
    tip = repo.commit("Erster Commit")
    repo.git("branch", "feature")
    repo.git("tag", "v1.0")
    repo.git("checkout", "-q", "--detach")

    model = _refreshed(repo)

    slots = [b["stackIndex"] for b in rows(model, "branchLabels")]
    slots += [t["stackIndex"] for t in rows(model, "tagLabels")]
    slots.append(prop(model, "headStackIndex"))
    assert sorted(slots) == [0, 1, 2, 3]
    assert prop(model, "headStackIndex") == 0  # detached HEAD sits directly on the commit
    assert prop(model, "laneLabelSlots") == [4]
    assert all(b["commitHash"] == tip for b in rows(model, "branchLabels"))


def test_tags_are_shown_as_labels_and_keep_their_commits_visible(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    repo.git("tag", "v1.0", first)
    repo.git("switch", "-q", "-c", "experiment")
    experiment = repo.commit("Experiment")
    repo.git("tag", "-a", "-m", "Annotiert", "v2.0-exp")
    repo.git("switch", "-q", "main")
    repo.git("branch", "-q", "-D", "experiment")

    model = _refreshed(repo)

    tags = {t["name"]: t for t in rows(model, "tagLabels")}
    assert tags["v1.0"]["commitHash"] == first
    assert tags["v2.0-exp"]["commitHash"] == experiment  # annotated tag peeled to its commit
    assert tags["v2.0-exp"]["column"] == 1
    assert experiment in _commits_by_hash(model)


def test_stash_and_its_commits_are_hidden(repo: GitRepo) -> None:
    tip = repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")
    repo.write("neu.txt", "neu\n")
    repo.git("add", "neu.txt")
    repo.git("stash", "-q")

    model = _refreshed(repo)

    assert list(_commits_by_hash(model)) == [tip]
    assert [b["name"] for b in rows(model, "branchLabels")] == ["main"]
    assert rows(model, "tagLabels") == []


def test_only_the_most_recent_commits_are_shown(repo: GitRepo) -> None:
    hashes = [repo.commit(f"Commit {i}") for i in range(8)]

    model = _refreshed(repo, max_commits=5)

    commits = _commits_by_hash(model)
    assert set(commits) == set(hashes[3:])
    assert prop(model, "historyTruncated") is True
    assert prop(model, "hiddenCommitCount") == 3
    assert commits[hashes[3]]["column"] == 0
    [collapsed] = [e for e in rows(model, "edges") if e["toCollapsed"]]
    assert collapsed["childHash"] == hashes[3]
    assert collapsed["parentColumn"] == -1


def test_history_within_the_limit_is_not_truncated(repo: GitRepo) -> None:
    for i in range(5):
        repo.commit(f"Commit {i}")

    model = _refreshed(repo, max_commits=5)

    assert len(rows(model, "commits")) == 5
    assert prop(model, "historyTruncated") is False
    assert prop(model, "hiddenCommitCount") == 0
    assert not any(e["toCollapsed"] for e in rows(model, "edges"))


def test_default_limit_is_about_thirty_commits(repo: GitRepo) -> None:
    for i in range(32):
        repo.commit(f"Commit {i}")

    model = _refreshed(repo)

    assert len(rows(model, "commits")) == 30
    assert prop(model, "hiddenCommitCount") == 2


def test_old_branch_tip_beyond_the_limit_stays_visible(repo: GitRepo) -> None:
    repo.commit("Basis")
    old = repo.commit("Alter Stand")
    repo.git("branch", "alt")
    for i in range(6):
        repo.commit(f"Neu {i}")

    model = _refreshed(repo, max_commits=3)

    assert old in _commits_by_hash(model)
    assert _branch(model, "alt")["column"] >= 0


def test_commits_of_a_merged_and_deleted_branch_keep_a_neutral_lane(repo: GitRepo) -> None:
    c = _two_branches_with_three_way_merge(repo)
    repo.git("branch", "-q", "-d", "feature")

    commits = _commits_by_hash(_refreshed(repo))

    assert commits[c["feature"]]["lane"] == 1
    assert commits[c["feature"]]["colorIndex"] == -1
    assert commits[c["merge"]]["lane"] == 0


def test_commits_on_detached_head_are_on_no_branch(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("checkout", "-q", "--detach")
    detached = repo.commit("Ohne Branch")

    model = _refreshed(repo)

    commit = _commits_by_hash(model)[detached]
    assert commit["colorIndex"] == -1
    assert prop(model, "headLane") == commit["lane"] == 1
    assert prop(model, "laneCount") == 2


def test_on_startup_older_branches_get_the_upper_lanes(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "zzz-alt")
    old = repo.commit("Alt", file="alt.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Weiter")
    repo.git("switch", "-q", "-c", "aaa-neu")
    repo.commit("Neu 1", file="neu.txt")
    new = repo.commit("Neu 2", file="neu.txt")

    commits = _commits_by_hash(_refreshed(repo))

    assert commits[old]["lane"] < commits[new]["lane"]
