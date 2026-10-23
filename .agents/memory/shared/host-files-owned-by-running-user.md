---
name: host-files-owned-by-running-user
date: 2026-10-23
source: Issue #79, harvested from two downstream adopters of this template
scope: shared
applies_to: repositories whose scripts, tests, containers, harnesses, logs, caches, releases or archives leave files on a host, especially a shared or nearly full machine without sudo
status: active
supersedes: null
superseded_by: null
---

# Files left on the host belong to the running user

## Decision

Every file, directory, log, cache and mounted output that the project, its
agents and its containers leave on the host is owned by the user who runs them.

- Do not use `sudo` to create or modify project files, and do not write system
  directories or root-owned bind mounts.
- When a tool writes to the host as root by default, change the execution
  surface so it does not: a non-root user inside the container, a bind mount of
  a user-owned directory, a harness run as the user.
- Cleanup that meets files it does not own stops and reports; it does not work
  around them with `sudo`.

## Why

Without `sudo`, a root-owned file cannot be removed by the user who needs the
space. Two downstream projects met this. One found about 15 GB of logs owned by
root on a disk at 97% use and, with no `sudo`, could only leave them. The other
decided Docker may stay rootful but everything the product leaves on host paths
must belong to the user, and moved a volume with a user-side symlink instead of
a root write. Ownership is part of the execution-surface design: choosing it at
the start costs less than asking an administrator later, and `sudo` turns
disposable space into a blocker.

## Apply

- Create temporary space with `mktemp -d` or under the project's state
  directory, never with elevated rights.
- Run containers as a non-root user, and mount user-owned or user-home
  directories for their output.
- Before cleaning a path, check ownership:
  `find <path> -xdev ! -user "$(id -u)"`.
- If that finds anything, stop and report the paths and the command that
  produced them; fix the producing command's execution surface.
- Before publishing or archiving assets, confirm they belong to the user.
- The rule covers scripts, tests, container mounts, logs, caches, releases and
  archives, not only temporary directories.
