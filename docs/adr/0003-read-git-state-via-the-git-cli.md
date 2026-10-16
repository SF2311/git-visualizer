# Read git state via the git CLI, not a git library

The visualizer reads repository state by running the installed `git` (`status --porcelain=v2`, `for-each-ref`, `log`, `reflog`, …) and parsing its output, rather than using libgit2/pygit2. This guarantees the Live View agrees with the git the lecturer types into, including In-progress Operation states (merge/rebase) where libraries sometimes lag behind.

## Consequences/Exceptions

All git commands run through the lock-free `GitCli` (`--no-optional-locks`, `GIT_OPTIONAL_LOCKS=0`). Git state is read only through git commands, with two exceptions where no git command exposes the value. Both locate the file with `git rev-parse --git-path` (so linked worktrees work) and only read it:

- **Rebase progress**: `rebase-merge/msgnum`/`end` and `rebase-apply/next`/`last` (plus `rebase-apply/applying`, which marks `git am`). `git status --porcelain=v2` has no rebase information. Long `git status` prints "Last commands done"/"Next commands to do" only for the merge backend, in prose, and nothing for the apply backend, and it would need a second Working Tree scan on every refresh. Whether a merge, cherry-pick or revert is in progress is read with `git cat-file --batch-check` on `MERGE_HEAD`, `CHERRY_PICK_HEAD` and `REVERT_HEAD`.
- **Fetches that brought nothing new**: such a fetch writes no reflog entry. It only rewrites `FETCH_HEAD`, and no git command prints which URLs `FETCH_HEAD` records or when it was written. Its content and modification time are read for the "zuletzt geholt" time. Reflog fetch times come from `git log --walk-reflogs`.

Watching files with the watcher is not reading git state and is not affected.
