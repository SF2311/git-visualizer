"""The display limit N is configurable on the command line."""

from __future__ import annotations

from pathlib import Path

from git_visualizer.app import _parse_args


def test_max_commits_defaults_to_thirty() -> None:
    assert _parse_args(["/tmp/repo"]).max_commits == 30


def test_max_commits_option() -> None:
    args = _parse_args(["--max-commits", "50", "/tmp/repo"])
    assert args.max_commits == 50
    assert args.repository == Path("/tmp/repo")
