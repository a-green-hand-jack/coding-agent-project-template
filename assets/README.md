# Assets

Use this directory as the repository-visible entry point for large datasets,
model checkpoints and other external assets. Prefer a symlink whose target is on
managed external storage:

```text
assets/my-dataset -> /managed/storage/my-dataset
```

Commit the symlink and update [`MANIFEST.yaml`](MANIFEST.yaml). Do not commit
large binary payloads, credentials or untracked paths with no manifest entry.
