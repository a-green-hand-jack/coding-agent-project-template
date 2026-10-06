# Development scripts

- `setup-worktree.sh`: initialize one worktree's state and environment;
- `diagnose-environment.sh`: check tools, state, assets and configuration;
- `inspect-state.sh`: show tracked and ignored worktree state read-only;
- `migrate-assets.sh`: copy state and repository-visible asset links before teardown;
- `teardown-worktree.sh`: prepare a worktree for managed destruction.

These scripts do not create global commands or delete worktrees themselves.
