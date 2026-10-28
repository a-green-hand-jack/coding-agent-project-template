# Shared skills rules

Shared skills must avoid product names, private paths and provider-specific
assumptions. Each skill states what must be adapted in a destination project,
as slots or steps a destination can extend: destinations write their
adaptations only in a trailing `## In this repository` section (see
`template-adoption` step 5). A skill's own text never contains a line that is
exactly `## In this repository`, not even in an example.
Update the content registry when adding, renaming or retiring a shared skill.

`release-doc-audit/` covers release writing, rendered visual review and the
existing consistency audit; its `references/release-types.md` distinguishes
product upgrades, results, milestones/archives and concise releases. Keep
concrete project release examples outside shared packages.
