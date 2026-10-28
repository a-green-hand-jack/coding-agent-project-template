# Development plane contract

This directory belongs to coding agent development, never to product runtime or
release payloads. Product code stays in the declared product tree, human docs
stay at the root, and runtime state stays in ignored `.project/`. External assets
keep their existing manifest/link policy.

## Six categories

| Category | Authority |
| --- | --- |
| `execution/` | Execution governance contracts; no template execution engine |
| `tests/` | Development checks and fixtures |
| `memory/` | Decisions, rationale and historical evidence |
| `knowledge/` | Current sourced facts and refresh conditions |
| `skills/` | Repeatable procedures and failure boundaries |
| `scripts/` | Public development commands and their implementation |

Each category has `shared/` and `project/`, and the category and both groups
have `AGENTS.md` plus a real relative `CLAUDE.md -> AGENTS.md` symlink (Git mode
120000). Shared may be empty. Deeper governance entries require an actual
boundary; individual skills use `SKILL.md`, not another AGENTS. The registry
policy explicitly lists allowed category-root files such as `entry-template.md`.
Do not add README files here.

Physical grouping is not reuse permission. Template-maintenance tests, harvest
and template history live in `project/` but retain `scope: template`; downstream
projects do not copy them. `shared_with_adaptation` retains the trailing
`## In this repository` section. Do not generalize local implementations merely
to fill shared directories.

## Naming

Use kebab-case for documents, skill directories and Shell commands; snake_case
for Python modules/packages, and `test_` for test modules. Active documents use
stable topic names. Dated evidence uses `topic-YYYY-MM-DD`, or `topic-YYYY-MM`
when only a month is known; never invent a day. Standard entrypoints, licenses,
Containerfiles, lockfiles and third-party payloads keep their required names
only through reasoned `policy.naming_exceptions` entries. An exception does not
exempt ownership, lifecycle or link checks.

## Registry authority

`.agents/content-registry.yaml` is the only content catalog. An independent
document, skill package or code package is a unit. Most specific path wins:
exact path, then glob, then longest package prefix; tied winners are errors.
Directory defaults may classify packages, but do not register an unknown memory
record or standalone script. `default_scope` preserves upgrade semantics; it
never makes an unregistered tracked file pass validation.

Schema 2 entries require stable `id`, `path`, `kind`, `scope`, `owner`, `summary`,
`status`, `source`, `updated`, plus adaptation/refresh/replacement fields as
applicable. IDs are allocated once and survive renames. Unknown historical
metadata is `unknown`; preserve partial dates. Registry owns paths, ownership,
lifecycle, summaries and replacement IDs. Body frontmatter owns content-specific
sources, observation dates and applicability; do not duplicate registry fields.
Generated marked indexes in group AGENTS derive from registry; never hand-edit
a second summary or state list. Retired/superseded entries keep provenance even
when their files are absent. Replacement chains must resolve without cycles. Memory/knowledge bodies may
remain under `status: superseded|retired` only with `retention: historical` and a
nonempty `retention_reason`; generated indexes label them as history, not current
guidance. This does not permit rejected or executable content to remain active.
Unambiguous old ID/path relationships migrate to stable IDs before frontmatter
is removed. Unresolved/ambiguous links or conflicting lifecycle authorities hold
source files and the registry for manual resolution without advancing versions.
An adopter's stable ID also retargets imported current relationships and migration
`to` identities; `upstream_id` and original `from` identities preserve provenance.
Known upstream prose descriptions already recorded as `legacy_lifecycle` remain
historical metadata, never invented live edges.

The on-disk schema uses a canonical YAML subset: block mappings for template
and writing, path-first flat entry records, and JSON flow values for nested
collections. No YAML tags/anchors/aliases or folded scalars. Unsupported syntax
fails explicitly. The parser and serializer are in `scripts/shared/content_registry.py`.
Keep `template`, `writing`, `optional`, `upgrade` and adoption decisions when
migrating; a schema1 file requires the target version's upgrade command.

## Change and verify

Before relocation, fix the schema and complete old/new identity/path map in the
registry's `migrations`. Each row records arrays of `from`/`to` identities,
`keep|move|rename|merge|extract|retire`, reason, source commit, and verification.
`entity: registration` rows describe legacy catalog-default expansion, not file
operations. File rows cover physical contents. Arrays allow many-to-many changes; a merge/extraction needs reviewed content
reconciliation, never automatic concatenation or overwrite. `legacy_inventory`
preserves the source entries, including explicit empty/history dispositions.
Git preserves the old authoritative body; do not introduce a runtime log store.

Read inbound links and replacement chains before distilling content. Keep unique
reasons and historical evidence; transfer procedures to skills and current facts
to knowledge, then route to them from AGENTS. Never delete by filename similarity.

Run `bash .agents/scripts/shared/check-development.sh`; regenerate marked indexes
with `--write-indexes`. Run `bash .agents/scripts/shared/check-shells.sh` to check
all nested Shell files. Update callers, imports, test discovery, CI and
adoption/upgrade references together. See `project-memory-governance` for the
workflow and root DEV for local acceptance.

Never store credentials, raw authentication files, private sessions or personal
data in the development tree.
