---
name: docker-objects-prefixed-and-removed
date: 2026-10-18
source: Issue #54, harvested from one downstream adopter of this template
applies_to: repositories whose product, tests, probes or diagnostics start images, containers, networks or volumes in Docker, especially on a shared or long-lived machine
---

# Docker objects carry the project prefix and are removed once expired

## Decision

1. **Every Docker object the project makes carries the project's prefix.** This
   covers images, containers, networks and volumes, including those made by
   tests, probes and diagnostics.
   - The prefix is short and chosen once by the project (`DOCKER_PREFIX`).
   - Images are named `<prefix>-<name>:<tag>`, for example
     `<prefix>-sandbox:<hash>`; containers `<prefix>-<run-id>` or
     `<prefix>-<run-id>-<role>`; networks and volumes the same way.
   - A label such as `<prefix>.run=<run-id>` is how the project finds its own
     objects later. Find objects by their label, and also check the name prefix
     before removing one.
2. **What expires is removed promptly.**
   - A run's or a test's containers are removed when it ends, whether it
     succeeded, failed or was stopped: `--rm`, or removal in a `finally` or
     teardown.
   - Containers left by runs that are no longer alive are removed at the next
     start.
   - When a new image tag is built, the superseded tags of the same repository
     are removed. Test-fixture images follow the same rule.
   - Whatever an agent makes for a probe or a diagnostic, it removes when done.
3. **Remove only what is the project's own and expired.**
   - Only objects with the project's prefix (or a former prefix, during a
     rename).
   - Never `-f`: Docker refuses to remove an image a container uses, and that
     guard stays.
   - Keep what a live run uses, what another worktree of the same repository
     currently uses (its current tag), and what a run that can still be resumed
     needs.
   - Never touch another project's objects, or an image the operator chose
     rather than one the project built.
   - The build cache is shared between projects and is out of scope.
4. **At close-out**, when a PR that changed an image or a test fixture is merged
   and its worktree is closed, the tags that belonged only to that branch are
   removed with it. See [`issue-close-out.md`](issue-close-out.md).

## Why

Several projects' containers and images sit side by side on a shared machine,
each with its own naming habits; telling whose an object is meant looking each
one up. One adopter tagged its images by a hash of their build content: every
change to a Dockerfile or a test-fixture image added a tag and none was ever
removed. Of its 20 images, 15 had expired (13 superseded test-fixture tags and 2
left from code deleted earlier) and together took several GB. The maintainer's
rule was that everything a project starts carries its prefix and that expired
objects are removed promptly, since in development most expire fast. The problem
is general: any project that runs containers on a shared or long-lived machine
accumulates expired images and leftover containers.

## Apply

The project fills one parameter in the `## In this repository` section at the
end of this record (see `template-adoption` step 5):

- `DOCKER_PREFIX`: the project's short prefix, and the label key built from it.

A project that starts no containers needs nothing from this record. Otherwise:

1. Before adding code or a test that starts a Docker object, name it with
   `DOCKER_PREFIX` and label it with the run id.
2. Remove a run's or test's containers in the same code path that started them,
   on success, failure and stop alike.
3. After building a new image tag, list the repository's tags and remove the
   superseded ones; do this for test-fixture images too.
4. Before removing an object, check that it carries `DOCKER_PREFIX` or a former
   prefix, and that no live run, other worktree's current tag or resumable run
   uses it. Do not pass `-f`.
5. When closing out a worktree whose PR changed an image or a test fixture,
   remove the tags only that branch used.
6. Remove your own probe and diagnostic objects before reporting the task done.
