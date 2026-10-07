# Assets

Use this directory as the repository-visible entry point for large datasets,
model checkpoints and other external assets. Keep the stable manifest and this
document in Git, but create machine-specific links locally. A link target must
never be committed because it can expose an absolute path and will usually be
invalid on another machine:

```text
assets/my-dataset -> /managed/storage/my-dataset
```

Add the asset's logical name, source, version, checksum and rebuildability to
[`MANIFEST.yaml`](MANIFEST.yaml). Put local link mappings in the ignored
`.project/assets.links` file, one `name=absolute/path` entry per line, then run
`bash .agents/scripts/setup-worktree.sh` to create the links. Do not commit
large binary payloads, credentials or unregistered paths.
