#!/usr/bin/env bash
# Print a read-only summary of this worktree's Git, .project/ and asset state, and
# the containers that mount a path inside it.
#
# Exit 3: a container (running or stopped) has a mount whose source is inside this
# worktree, or an installed container runtime cannot be queried. Either is a live
# task for close-out: removing the worktree would remove data a container still
# refers to. The check is skipped when no container runtime is installed.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
echo '## repository'
printf 'root: %s\n' "$root"
printf 'branch: %s\n' "$(git symbolic-ref --quiet --short HEAD || echo detached)"
echo
echo '## git status (including ignored state)'
git status --short --ignored
echo
echo '## project state'
if [[ -d .project ]]; then
  du -sh .project 2>/dev/null || true
  find .project -maxdepth 2 -type f -print | sort
else
  echo '.project does not exist; run setup-worktree.sh'
fi
echo
echo '## assets'
find assets -maxdepth 1 -type l -printf '%f -> %l\n' 2>/dev/null || true
echo
echo '## containers mounting this worktree'
live=0
runtimes=0
inside() { [[ "$1" == "$root" || "$1" == "$root"/* ]]; }
for runtime in docker podman; do
  command -v "$runtime" >/dev/null 2>&1 || continue
  runtimes=1
  if ! ids=$("$runtime" ps -aq 2>&1); then
    printf '%s: FAIL cannot list containers: %s\n' "$runtime" "$(head -n 1 <<<"$ids")"
    live=1
    continue
  fi
  if [[ -z "$ids" ]]; then printf '%s: none\n' "$runtime"; continue; fi
  format='{{$n := .Name}}{{$s := .State.Status}}{{range .Mounts}}{{$n}}{{"\t"}}{{$s}}{{"\t"}}{{.Source}}{{"\t"}}{{.Destination}}{{"\n"}}{{end}}'
  found=0
  for id in $ids; do
    # A container removed since `ps` is skipped; any other failure cannot be judged.
    if ! mounts=$("$runtime" inspect --type container --format "$format" "$id" 2>/dev/null); then
      if still=$("$runtime" ps -aq --filter "id=$id" 2>/dev/null) && [[ -z "$still" ]]; then continue; fi
      printf '%s: FAIL cannot inspect container %s\n' "$runtime" "$id"
      live=1
      continue
    fi
    while IFS=$'\t' read -r name status source destination; do
      [[ -n "$source" ]] || continue
      resolved=$(realpath -m -- "$source" 2>/dev/null || printf '%s' "$source")
      if inside "$source" || inside "$resolved"; then
        printf '%s: LIVE %s (%s) mounts %s at %s\n' "$runtime" "${name#/}" "$status" "$source" "$destination"
        found=1
        live=1
      fi
    done <<<"$mounts"
  done
  [[ $found -eq 1 ]] || printf '%s: none\n' "$runtime"
done
[[ $runtimes -eq 1 ]] || echo 'skip: no container runtime (docker, podman) installed'
if [[ $live -ne 0 ]]; then
  echo 'live task: a container mounts this worktree or cannot be checked; report to the maintainer before removing it' >&2
  exit 3
fi
