# Read git state via the git CLI, not a git library

The visualizer reads repository state by running the installed `git` (`status --porcelain=v2`, `for-each-ref`, `log`, `reflog`, …) and parsing its output, rather than using libgit2/pygit2. This guarantees the Live View agrees with the git the lecturer types into, including In-progress Operation states (merge/rebase) where libraries sometimes lag behind.
