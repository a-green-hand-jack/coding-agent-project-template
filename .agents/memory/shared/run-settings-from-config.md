---
name: run-settings-from-config
date: 2026-10-15
source: Issue #30, harvested from two independent downstream adopters of this template
scope: shared
applies_to: repositories whose product has commands that start runs with tunable parameters such as limits, rounds, agent, model, reasoning effort, resources, image or network
status: active
supersedes: null
superseded_by: null
---

# Run parameters come from configuration, not code

## Decision

1. **A value a run command can tune is a setting, not a constant in code.**
   This covers time limits, round counts, agent, model, reasoning effort,
   resource limits, image and network.
2. **Defaults live in one configuration file that ships with the product, with
   one table per command.** A new command defines its settings there first, then
   reads them.
3. **Overrides apply in a fixed order:** shipped defaults, then a
   runner-supplied file passed with the override flag, then the command's own
   arguments. A later source wins per key.
4. **The loader rejects unknown keys and wrongly typed values.** It never
   ignores them silently, so a misspelled key fails the run instead of running
   with a default.
5. **At run start, the effective settings are written into the run record.**
   Resume and retry reuse the recorded settings and do not re-read the
   configuration file.
6. **Settings hold no credentials and no machine-local default paths.** A run's
   grants (keys, mounts, compute) are separate from settings and may override
   their limits. See [`llm-credentials.md`](llm-credentials.md).

## Why

Run parameters kept as constants in code make every model change or budget
change a code change and a PR. A run cannot be reproduced with the settings it
used, because the code has moved on. Resume and retry silently pick up whatever
the code or file says now, so one run can mix two sets of settings. A loader
that ignores unknown keys turns a typo into a default nobody chose. Two
downstream adopters reached these rules separately, from different origins.

## Apply

Each project fills four parameters:

- `CONFIG_FILE`: the location and format of the shipped configuration file.
- `COMMAND_TABLE`: how a table is named after its command.
- `RECORD_FIELD`: the field of the run record that holds the effective settings.
- `CONFIG_FLAG`: the name of the runner-supplied file flag.

Then:

1. Before adding a run command, add its table to `CONFIG_FILE` with a default for
   every tunable value; read values only through the loader.
2. Before adding a tunable value to code, add it to the command's table instead.
3. Write the effective settings to `RECORD_FIELD` when the run starts; make
   resume and retry read `RECORD_FIELD` and nothing else.
4. Keep credentials, mounts and compute grants out of `CONFIG_FILE`; pass them as
   separate grants. A grant may lower or raise a limit, and the run record notes
   that it did.
5. Before committing a configuration file or run record, check that it holds no
   credential value and no machine-local path.

The template ships no loader. Each project implements the rules in its own
product code.
