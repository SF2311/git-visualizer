# Git Visualizer

A read-only, projector-friendly live view of a real git repository that a lecturer manipulates in a separate terminal during a lecture.

## Language

### The view

**Observed Repository**:
The real git repository on disk that the visualizer displays; it is changed only by tools outside the visualizer.
_Avoid_: Simulation, sandbox, demo repo

**Live View**:
The visualizer's display of the Observed Repository's current state, shown on a second screen or projector.
_Avoid_: Dashboard, editor

### The Three Areas

**Three Areas**:
The Working Tree, the Staging Area and the History; the first two list only changed files, the History is the commit graph.
_Avoid_: Three trees, stages

**Working Tree**:
The files on disk; in the Live View it lists only untracked, modified and conflicted files that are not (fully) staged.
_Avoid_: Workspace, working directory

**Staging Area**:
The snapshot prepared for the next commit (German UI: "Staging Bereich").
_Avoid_: Index, cache

**History**:
The graph of commits reachable from branches, Remote-tracking Branches, tags and HEAD.
_Avoid_: Repository (as an area), log, tree

**HEAD**:
The pointer to what is currently checked out — a branch, or directly a commit when detached; shown as its own marker.
_Avoid_: Current branch (when HEAD is detached)

### Remotes

**Remote**:
A named reference to another repository (e.g. `origin`), shown as its own box in the Live View.
_Avoid_: Server, origin (as a generic term)

**Remote-tracking Branch**:
The local, last-fetched snapshot of a branch on a Remote (e.g. `origin/main`); never refreshed by the visualizer itself.
_Avoid_: Remote branch

**Upstream**:
The Remote-tracking Branch configured for a local branch (e.g. via `git push -u`); it pairs the two visually and defines ahead/behind. A branch with no Upstream has no ahead/behind, even if a Remote-tracking Branch of the same name exists.
_Avoid_: Tracking branch, same-named remote branch

### History changes

**Ghost Commit**:
A commit that was reachable before a state change and is not afterwards (e.g. the originals after a rebase or amend), shown faded until the next ref change or until cleared.
_Avoid_: Dangling commit, orphan

**In-progress Operation**:
A merge or rebase that git has started but not finished, typically paused on a conflict.
_Avoid_: Pending state
