"""Helpers the template's own tests share about its releases.

Not a test module: `discover` imports it and finds nothing to run. It answers
which tags are the template's own releases, and whether this checkout is the
template repository.

The template's own tests (`scope: template` in the registry) compare releases
and the migration history recorded in them. A repository copied from the
template has its own tag namespace and no template releases, so those tests skip
there instead of failing its first push; `template-adoption` step 5 removes them
once the copy adopts the template properly.
"""
from __future__ import annotations

import functools
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ".agents/content-registry.yaml"


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False)


def normalize(url: str) -> str:
    """The same remote written as https, without a trailing `.git` or case."""
    url = url.strip().lower()
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    url = re.sub(r"^ssh://(?:git@)?([^/]+)/", r"https://\1/", url)
    url = re.sub(r"^https?://", "https://", url)
    return url.rstrip("/").removesuffix(".git")


@functools.lru_cache(maxsize=1)
def repository() -> str:
    """`template.repository` from the registry: where these releases come from."""
    text = (ROOT / REGISTRY).read_text(encoding="utf-8")
    found = re.search(r"^template:\n(?:  .*\n)*?  repository: (\S+)", text, re.M)
    return found.group(1) if found else ""


def is_template_checkout() -> bool:
    """Whether `origin` is the template repository itself.

    Decided by the remote, not by how many tags happen to exist: a copy with two
    `v*` tags of its own is not the template and must not be treated as it.
    """
    remote = git("remote", "get-url", "origin")
    return remote.returncode == 0 and repository() != "" and normalize(remote.stdout) == normalize(repository())


@functools.lru_cache(maxsize=1)
def release_tags() -> tuple[str, ...]:
    """The template's own release tags: each one's registry declares that version.

    Filtering by content, not by name, keeps a copy's product tags out of the
    release comparisons.
    """
    version = re.compile(r"^template:\n(?:  .*\n)*?  version: (\S+)", re.M)
    tags = []
    for tag in git("tag", "-l", "v*").stdout.split():
        if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            continue
        registry = git("show", f"{tag}:{REGISTRY}")
        found = version.search(registry.stdout) if registry.returncode == 0 else None
        if found is not None and found.group(1) == tag:
            tags.append(tag)
    return tuple(tags)


def require_releases(case: unittest.TestCase, tags: tuple[str, ...] | list[str] | None = None,
                     minimum: int = 2) -> tuple[str, ...]:
    """The template's release tags, or a skip outside the template repository.

    Inside it the same condition fails: the template must keep testing its own
    releases, so a missing fetch is reported instead of skipped.
    """
    tags = release_tags() if tags is None else tuple(tags)
    if len(tags) >= minimum:
        return tags
    missing = (f"this checkout carries {len(tags)} template release tag(s) of {minimum} needed:"
               f" the template's own tests need the template's release history"
               f" (`git fetch --tags {repository() or 'the template repository'}`)")
    if is_template_checkout():
        case.fail(f"the release tags are missing: git fetch --tags origin — {missing}")
    case.skipTest(f"{missing}; outside the template repository they skip (template-adoption step 5 removes them)")
    return ()
