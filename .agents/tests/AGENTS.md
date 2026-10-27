# Development checks rules

Tests here are diagnostic and seam-focused. Do not increase coverage merely to
mirror implementation, and do not treat these checks as product acceptance when
the real public entrypoint or long-running runtime has not been exercised.

In the template repository, the `test_template_*.py` files are the template's
own tests of its scripts (`scope: template`; a project does not copy them):
`upgrade-template.sh` against a fixture template with three tags and from an
older real release to the release candidate, `probe-credentials.sh` with setup
and diagnostics against fixture credential files, `migrate-assets.sh` rules and
`new-agent-prompt.sh` against fixture repositories (including a declared parent
integration target and the default dev target), and the branch-model checks
of `diagnose-environment.sh`. They write only to temporary directories, and
CI runs them:

```bash
python3 -m unittest discover -s .agents/tests -p 'test_template_*.py'
```

The real-release test needs the release tags (`git fetch --tags origin`).
