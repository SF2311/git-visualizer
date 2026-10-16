"""Reads Remotes and Remote-tracking Branches from the Observed Repository's metadata.

Passive like the rest of the git reader (ADR 0001): only local configuration, refs,
reflogs and ``FETCH_HEAD`` are read. Nothing here contacts a Remote, so Remote-tracking
Branches are exactly as fresh as the lecturer's last fetch.

The last-fetch time of a Remote is the newest of

* the reflog entries of its Remote-tracking Branches (and ``<remote>/HEAD``) written by
  ``fetch``, ``pull`` or ``clone`` (not ``push``, which updates them without fetching),
* the modification time of ``FETCH_HEAD`` if it records this Remote's URL (a fetch that
  brought nothing new writes no reflog entry but still rewrites ``FETCH_HEAD``).
"""

from __future__ import annotations

import os
from pathlib import Path

from git_visualizer.git_cli import GitCli
from git_visualizer.snapshot import Remote, RemoteTrackingBranch

_REMOTES_PREFIX = "refs/remotes/"
_FETCHING_REFLOG_ACTIONS = ("fetch", "pull", "clone")


def read_remotes(git: GitCli) -> tuple[tuple[Remote, ...], tuple[RemoteTrackingBranch, ...]]:
    """The configured Remotes and all Remote-tracking Branches (``<remote>/HEAD`` excluded)."""
    urls = _remote_urls(git)
    tracking_branches: list[RemoteTrackingBranch] = []
    refs_by_remote: dict[str, list[str]] = {}
    output = git.run(
        "for-each-ref",
        "--format=%(refname)%00%(symref)%00%(objectname)%00%(objecttype)",
        _REMOTES_PREFIX.rstrip("/"),
    )
    for line in output.splitlines():
        refname, symref, commit_hash, kind = line.split("\0")
        name = refname.removeprefix(_REMOTES_PREFIX)
        remote = _remote_of(name, urls)
        refs_by_remote.setdefault(remote, []).append(refname)
        if not symref and kind == "commit":
            tracking_branches.append(RemoteTrackingBranch(name=name, remote=remote, commit_hash=commit_hash))

    fetched_at = _reflog_fetch_times(git, [ref for refs in refs_by_remote.values() for ref in refs])
    fetch_head_urls, fetch_head_time = _fetch_head(git)
    remotes = []
    for remote_name, url in urls.items():
        times = [fetched_at[ref] for ref in refs_by_remote.get(remote_name, []) if ref in fetched_at]
        if fetch_head_time is not None and _normalized_url(url) in fetch_head_urls:
            times.append(fetch_head_time)
        remotes.append(Remote(name=remote_name, url=url, last_fetched=max(times, default=None)))
    return tuple(remotes), tuple(tracking_branches)


def _remote_urls(git: GitCli) -> dict[str, str]:
    """URL per configured Remote, in configuration order."""
    output = git.run_optional("config", "-z", "--get-regexp", r"^remote\..*\.url$")
    urls: dict[str, str] = {}
    for entry in (output or "").split("\0"):
        if not entry:
            continue
        key, _, value = entry.partition("\n")
        urls.setdefault(key.removeprefix("remote.").removesuffix(".url"), value)
    return urls


def _remote_of(tracking_name: str, urls: dict[str, str]) -> str:
    """The Remote a Remote-tracking Branch belongs to; remote names may contain ``/``."""
    matches = [name for name in urls if tracking_name.startswith(name + "/")]
    return max(matches, key=len) if matches else tracking_name.split("/", 1)[0]


def _reflog_fetch_times(git: GitCli, refs: list[str]) -> dict[str, float]:
    """Per ref, the time of its newest reflog entry written by fetch/pull/clone."""
    if not refs:
        return {}
    output = git.run_optional("log", "--walk-reflogs", "--date=unix", "--format=%gD%x00%gs", *refs, "--")
    times: dict[str, float] = {}
    for line in (output or "").splitlines():
        selector, _, message = line.partition("\0")
        ref, _, rest = selector.rpartition("@{")
        if not message.startswith(_FETCHING_REFLOG_ACTIONS) or not rest.rstrip("}").isdigit():
            continue
        times[ref] = max(times.get(ref, 0.0), float(rest.rstrip("}")))
    return times


def _fetch_head(git: GitCli) -> tuple[set[str], float | None]:
    """The (normalized) URLs recorded in ``FETCH_HEAD`` and its modification time."""
    path_output = git.run_optional("rev-parse", "--path-format=absolute", "--git-path", "FETCH_HEAD")
    if path_output is None:
        return set(), None
    path = Path(path_output.strip())
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        modified = os.stat(path).st_mtime
    except OSError:
        return set(), None
    urls = {_normalized_url(line.rpartition(" of ")[2]) for line in content.splitlines() if " of " in line}
    return urls, modified


def _normalized_url(url: str) -> str:
    """``url`` as git records it in ``FETCH_HEAD``: no credentials, no ``.git``/``/`` suffix."""
    scheme, separator, rest = url.partition("://")
    if separator:
        authority, slash, path = rest.partition("/")
        url = f"{scheme}://{authority.rpartition('@')[2]}{slash}{path}"
    url = url.rstrip("/")
    return url.removesuffix(".git").rstrip("/")
