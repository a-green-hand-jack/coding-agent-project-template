# Script directory rules

Scripts may prepare environments, inspect state, migrate assets and invoke the
project's public CLI. They must not create a second runtime layer, global command,
or hidden state store. Destructive operations require an explicit, inspectable
precondition and should be delegated to the approved worktree or asset manager.
