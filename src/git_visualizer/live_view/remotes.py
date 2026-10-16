"""Rows for Remote boxes and Remote-tracking Branch labels, and their German texts."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from git_visualizer.history_layout import HistoryLayout
from git_visualizer.remote_reader import normalized_url
from git_visualizer.snapshot import RemoteTrackingBranch, RepositorySnapshot

REMOTE_ROLES = ("name", "url", "shortUrl", "lastFetched", "trackingBranches")
REMOTE_TRACKING_ROLES = (
    "name",
    "remote",
    "commitHash",
    "column",
    "lane",
    "colorIndex",
    "stackIndex",
    "isUpstream",
)

_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_SCP_LIKE = re.compile(r"^(?:[^/@:]+@)?([^/:]{2,}):(?!//)(.*)$")
_MAX_PATH_LENGTH = 30


def remote_rows(
    snapshot: RepositorySnapshot, layout: HistoryLayout, color_of: Callable[[str], int]
) -> list[dict[str, Any]]:
    """One row per Remote. ``lastFetched`` is a Unix timestamp, 0 if never fetched;
    ``trackingBranches`` lists ``{name, colorIndex}`` of its Remote-tracking Branches."""
    return [
        {
            "name": remote.name,
            "url": remote.url,
            "shortUrl": short_url(remote.url),
            "lastFetched": remote.last_fetched or 0.0,
            "trackingBranches": [
                {"name": tracking.name, "colorIndex": _color(tracking, layout, color_of)}
                for tracking in sorted(snapshot.remote_tracking_branches, key=lambda t: t.name)
                if tracking.remote == remote.name
            ],
        }
        for remote in snapshot.remotes
    ]


def remote_tracking_rows(
    snapshot: RepositorySnapshot,
    layout: HistoryLayout,
    color_of: Callable[[str], int],
    position: Callable[[str], dict[str, int]],
) -> list[dict[str, Any]]:
    """One label row per Remote-tracking Branch, colored like the local branch whose
    Upstream it is (``colorIndex`` -1 when it is nobody's Upstream)."""
    return [
        {
            "name": tracking.name,
            "remote": tracking.remote,
            "commitHash": tracking.commit_hash,
            **position(tracking.commit_hash),
            "colorIndex": _color(tracking, layout, color_of),
            "stackIndex": layout.remote_tracking_slots[tracking.name],
            "isUpstream": tracking.name in layout.upstream_of,
        }
        for tracking in snapshot.remote_tracking_branches
    ]


def _color(tracking: RemoteTrackingBranch, layout: HistoryLayout, color_of: Callable[[str], int]) -> int:
    local = layout.upstream_of.get(tracking.name)
    return -1 if local is None else color_of(local)


def short_url(url: str) -> str:
    """A Remote URL shortened for the projector: no scheme, credentials or ``.git`` for
    network URLs; long local paths keep their last two components."""
    if scheme := _SCHEME.match(url):
        rest = url[scheme.end() :]
        if scheme.group().lower() == "file://":
            return _short_path(rest)
        return normalized_url(url)[scheme.end() :]
    if scp := _SCP_LIKE.match(url):
        return normalized_url(f"{scp.group(1)}:{scp.group(2)}")
    return _short_path(url)


def _short_path(path: str) -> str:
    path = path.rstrip("/\\")
    parts = re.split(r"[/\\]", path)
    if len(path) <= _MAX_PATH_LENGTH or len(parts) <= 3:
        return path
    return "…/" + "/".join(parts[-2:])


def last_fetch_text(last_fetched: float, now: float) -> str:
    """E.g. "zuletzt geholt vor 12 Min."; ``last_fetched`` 0 means never fetched."""
    if last_fetched <= 0:
        return "noch nie geholt"
    age = max(0.0, now - last_fetched)
    if age < 60:
        return "zuletzt geholt gerade eben"
    if age < 3600:
        return f"zuletzt geholt vor {int(age // 60)} Min."
    if age < 86400:
        return f"zuletzt geholt vor {int(age // 3600)} Std."
    days = int(age // 86400)
    return f"zuletzt geholt vor {days} {'Tag' if days == 1 else 'Tagen'}"
