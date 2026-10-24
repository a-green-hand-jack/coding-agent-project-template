#!/usr/bin/env bash
# Copy what a retiring worktree must keep into the canonical (primary) checkout,
# check the copy, and say what was left behind and why. Nothing is deleted.
#
#   migrate-assets.sh --to CANONICAL_PROJECT [--also NAME]... [--skip NAME=REASON]...
#
# Every top-level entry of .project/ gets one line: its action, size and why it
# may be left behind. The template's rules are in template_rule() below; a project
# adds rules for its own entries in .agents/scripts/migrate-project.rules (format
# below; NAME may be a shell wildcard such as plan-*.md). An entry without a rule
# that holds something stops the migration
# (exit 3) until it gets a rule or is named with --also (copy it too) or --skip
# (leave it, with the reason). Exit 1: a real copy of a login, an asset or link
# mapping would be overwritten, or the copy does not match its source. Exit 2:
# wrong arguments or an invalid rules file.
set -euo pipefail

usage() {
  echo "usage: $0 --to CANONICAL_PROJECT [--also NAME]... [--skip NAME=REASON]..." >&2
  exit 2
}
[[ "${1:-}" == '--to' && -n "${2:-}" ]] || usage
destination=$(realpath -m "$2")
shift 2
also_list=
skip_list=
while [[ $# -gt 0 ]]; do
  case $1 in
    --also) [[ -n "${2:-}" ]] || usage; also_list+="$2"$'\n'; shift 2 ;;
    --skip) [[ "${2:-}" == ?*=?* ]] || usage; skip_list+="$2"$'\n'; shift 2 ;;
    *) usage ;;
  esac
done

root=$(git rev-parse --show-toplevel)
cd "$root"
[[ "$destination" != "$root" && "$destination" != "$root"/* ]] || { echo 'destination must be outside this worktree' >&2; exit 1; }

in_list() { printf '%s' "$2" | grep -qxF -- "$1"; }

# The top-level entries of .project/ the template has rules for; keep in step with
# template_rule() below. A project rule, wildcard or not, may not match any of them.
template_names='state runs artifacts manifest assets.links home worktree.env credentials'
is_glob() { [[ $1 == *[*?[]* ]]; }
# Prints the first template entry name that the project rule NAME (a name or a
# wildcard) matches.
template_match() {
  local t
  for t in $template_names; do
    # shellcheck disable=SC2053
    if [[ $t == $1 ]]; then printf '%s\n' "$t"; return; fi
  done
}

# The template's rule for each top-level entry of .project/ it creates. Do not edit
# it in a project: template-upgrade replaces this script. Prints "<action>|<why>":
# copy, merge, drop, login or unknown. A login is a link to the canonical
# checkout's login directory (llm-credentials): the link is dropped, and a real
# directory or file is never migrated.
template_rule() {
  case $1 in
    state|runs|artifacts|manifest) echo 'copy|' ;;
    assets.links) echo "merge|the mappings are added to the destination's .project/assets.links" ;;
    home|worktree.env) echo 'drop|setup-worktree.sh rewrites it and it only names this worktree' ;;
    credentials) echo 'login|' ;;
    *) echo 'unknown|' ;;
  esac
}

# The project's rules for the entries its own setup creates, one per line:
#   NAME|ACTION|WHY
# with ACTION copy, drop (WHY says why it may be left behind) or login. NAME is an
# entry name or a shell wildcard (* ? [...]) for a class of entries, such as
# plan-*.md; a wildcard cannot contain '/', cannot be a login and cannot match an
# entry the template handles. An entry takes the first rule that fits: the
# template's, then a project rule with its exact name, then the first wildcard
# in the file that matches; the report names the wildcard that matched. Blank lines
# and lines starting with '#' are ignored. The template never ships this file, so
# template-upgrade keeps it; a rule for an entry the template already handles is
# refused, so a new template rule shows up as a conflict instead of being hidden.
rules_file=.agents/scripts/migrate-project.rules
project_rules=
if [[ -f $rules_file ]]; then
  line_no=0
  while IFS= read -r line || [[ -n $line ]]; do
    line_no=$((line_no + 1))
    [[ -z "${line//[[:space:]]/}" || $line == \#* ]] && continue
    IFS='|' read -r name action why <<<"$line"
    problem=
    if [[ -z $name || $name == */* || $name == . || $name == .. || $name == [[:space:]]* || $name == *[[:space:]] ]]; then
      problem="'$name' is not a plain entry name of .project/"
    elif is_glob "$name" && [[ $action == login ]]; then
      problem="a wildcard cannot be a login: $name"
    elif [[ -n $(template_match "$name") ]]; then
      if is_glob "$name"; then
        problem="the wildcard $name matches $(template_match "$name"), which the template already handles; make it narrower"
      else
        problem="the template already has a rule for $name; remove this line"
      fi
    elif in_list "$name" "$(printf '%s' "$project_rules" | cut -d'|' -f1)"; then
      problem="a second rule for $name"
    else
      case $action in
        copy|login) ;;
        drop) [[ -n "${why//[[:space:]]/}" ]] || problem="drop needs a reason: $name|drop|WHY" ;;
        *) problem="unknown action '$action' for $name (copy, drop or login)" ;;
      esac
    fi
    [[ -z $problem ]] || { echo "$rules_file:$line_no: $problem" >&2; exit 2; }
    project_rules+="$name|$action|$why"$'\n'
  done < "$rules_file"
fi

classify() {
  local rule pass name action why
  rule=$(template_rule "$1")
  [[ $rule == 'unknown|' ]] || { printf '%s\n' "$rule"; return; }
  for pass in exact wildcard; do
    while IFS='|' read -r name action why; do
      [[ -n $name ]] || continue
      if [[ $pass == exact ]]; then
        is_glob "$name" || [[ $name != "$1" ]] || { printf '%s|%s\n' "$action" "$why"; return; }
      else
        is_glob "$name" || continue
        # shellcheck disable=SC2053
        [[ $1 == $name ]] || continue
        printf '%s|rule %s%s\n' "$action" "$name" "${why:+: $why}"
        return
      fi
    done <<<"$project_rules"
  done
  echo 'unknown|'
}

skip_reason() { printf '%s' "$skip_list" | awk -F= -v n="$1" '$1 == n { sub(/^[^=]*=/, ""); print; exit }'; }
holds_nothing() {
  if [[ -L "$1" ]]; then return 1; fi
  if [[ -d "$1" ]]; then [[ -z "$(find "$1" ! -type d -print -quit)" ]]; else [[ ! -s "$1" ]]; fi
}

report=
say() { printf '%s\n' "$*"; report+="$*"$'\n'; }

fatal=0
fail_with() { [[ $fatal -ne 0 ]] || fatal=$1; }

# -- .project/ entries ------------------------------------------------------------------------
say '## .project/ entries'
say "$(printf '%-20s %-6s %7s  %s' ENTRY ACTION SIZE WHY)"
copy_entries=
merge_links=0
seen=
for path in .project/* .project/.[!.]*; do
  [[ -e "$path" || -L "$path" ]] || continue
  name=${path#.project/}
  seen+="$name"$'\n'
  size=$(du -sh "$path" 2>/dev/null | cut -f1 || true)
  IFS='|' read -r action why <<<"$(classify "$name")"
  if [[ $action == login ]]; then
    if in_list "$name" "$also_list" || in_list "$name" "$(printf '%s' "$skip_list" | cut -d= -f1)"; then
      echo "--also/--skip $name: it is a login, which is never copied and never left by choice" >&2
      exit 2
    fi
    if [[ -L "$path" ]]; then
      action=drop
      why="link to the canonical checkout's login; the link is dropped and the login is never copied"
    else
      action=blocked
      why='a real copy of a login: never migrated; check the canonical login, then remove it by hand'
      fail_with 1
    fi
  elif in_list "$name" "$also_list"; then
    [[ $action != copy && $action != merge ]] || { echo "--also $name: it is migrated anyway" >&2; exit 2; }
    action=copy
    why='copied because --also named it'
  elif in_list "$name" "$(printf '%s' "$skip_list" | cut -d= -f1)"; then
    [[ $action != copy && $action != merge ]] || { echo "--skip $name: it is always migrated" >&2; exit 2; }
    action=skip
    why="left behind on purpose: $(skip_reason "$name")"
  elif [[ $action == unknown ]]; then
    if holds_nothing "$path"; then
      action=drop
      why='empty; nothing to keep'
    else
      why="no rule for it: add one to $rules_file, or decide with --also NAME (copy it too) or --skip NAME=REASON (leave it)"
      fail_with 3
    fi
  fi
  say "$(printf '%-20s %-6s %7s  %s' "$name" "$action" "$size" "$why")"
  [[ $action != copy ]] || copy_entries+="$name"$'\n'
  [[ $action != merge ]] || merge_links=1
done
while IFS= read -r given; do
  [[ -z "$given" ]] || in_list "$given" "$seen" || { echo "--also/--skip $given: there is no .project/$given" >&2; exit 2; }
done <<<"$(printf '%s' "$also_list"; printf '%s' "$skip_list" | cut -d= -f1)"

if [[ -d .project/runs ]]; then
  say ''
  say 'note: before removing this worktree, check .project/runs/ with the project status command'
  say '      and archive what cannot be rebuilt; see .agents/skills/shared/long-running-supervision/'
  say '      and .agents/skills/shared/asset-lifecycle/.'
fi

# -- assets/ entries and link mappings ---------------------------------------------------------
say ''
say '## assets/'
asset_entries=
for entry in assets/* assets/.[!.]*; do
  [[ -e "$entry" || -L "$entry" ]] || continue
  # Tracked files and links reach the destination through Git, not migration.
  if git --literal-pathspecs ls-files --error-unmatch -- "$entry" >/dev/null 2>&1; then
    continue
  fi
  name=${entry#assets/}
  target="$destination/assets/$name"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ -L "$entry" && -L "$target" && "$(readlink "$entry")" == "$(readlink "$target")" ]]; then
      say "$(printf '%-20s %-6s %s' "$name" same 'the destination already links to the same target')"
      continue
    fi
    say "$(printf '%-20s %-6s %s' "$name" CONFLICT "the destination already has $target; not overwritten")"
    fail_with 1
    continue
  fi
  say "$(printf '%-20s %-6s %s' "$name" copy "$([[ -L "$entry" ]] && echo "link -> $(readlink "$entry")" || du -sh "$entry" | cut -f1)")"
  asset_entries+="$name"$'\n'
done
dest_links="$destination/.project/assets.links"
if [[ $merge_links -eq 1 ]]; then
  while IFS='=' read -r name target; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    have=$(awk -F= -v n="$name" '$1 == n { sub(/^[^=]*=/, ""); print; found = 1; exit } END { if (!found) exit 1 }' "$dest_links" 2>/dev/null) && found=1 || found=0
    if [[ $found -eq 1 && "$have" != "$target" ]]; then
      say "$(printf '%-20s %-6s %s' "$name" CONFLICT "$dest_links maps it to a different target")"
      fail_with 1
    fi
  done < .project/assets.links
fi

if [[ $fatal -ne 0 ]]; then
  echo >&2
  echo 'migration stopped before copying anything; resolve the lines above and run it again' >&2
  exit "$fatal"
fi

# -- copy --------------------------------------------------------------------------------------
stamp=$(date -u +%Y%m%dT%H%M%SZ)
migration="$destination/.project/migrations/$(basename "$root")-$stamp"
mkdir -p "$destination/.project/migrations" "$destination/assets"
mkdir "$migration"
while IFS= read -r name; do
  [[ -n "$name" ]] && cp -a ".project/$name" "$migration/"
done <<<"$copy_entries"
while IFS= read -r name; do
  [[ -n "$name" ]] && cp -a "assets/$name" "$destination/assets/$name"
done <<<"$asset_entries"
if [[ $merge_links -eq 1 ]]; then
  mkdir -p "$destination/.project"
  touch "$dest_links"
  [[ ! -s "$dest_links" || -z "$(tail -c1 "$dest_links")" ]] || printf '\n' >> "$dest_links"
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    grep -qxF -- "$line" "$dest_links" || printf '%s\n' "$line" >> "$dest_links"
  done < .project/assets.links
fi
printf 'migrated_from=%q\n' "$root" > "$migration/migrated-from.env"
printf '%s' "$report" > "$migration/migration-report.txt"

# -- verify the copy ---------------------------------------------------------------------------
diff_cmd='diff -rq'
! diff --no-dereference /dev/null /dev/null >/dev/null 2>&1 || diff_cmd='diff -rq --no-dereference'
same() { # SOURCE COPY
  if [[ -L "$1" ]]; then [[ -L "$2" && "$(readlink "$1")" == "$(readlink "$2")" ]]
  elif [[ -d "$1" ]]; then $diff_cmd "$1" "$2"
  else cmp -s "$1" "$2"
  fi
}
echo
echo '## verification'
verified=0
bad=0
while IFS= read -r name; do
  [[ -n "$name" ]] || continue
  if same ".project/$name" "$migration/$name"; then verified=$((verified + 1)); else echo "DIFFERS: .project/$name and $migration/$name" >&2; bad=1; fi
done <<<"$copy_entries"
while IFS= read -r name; do
  [[ -n "$name" ]] || continue
  if same "assets/$name" "$destination/assets/$name"; then verified=$((verified + 1)); else echo "DIFFERS: assets/$name and $destination/assets/$name" >&2; bad=1; fi
done <<<"$asset_entries"
if [[ $merge_links -eq 1 ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    if grep -qxF -- "$line" "$dest_links"; then verified=$((verified + 1)); else echo "MISSING in $dest_links: $line" >&2; bad=1; fi
  done < .project/assets.links
fi
if [[ $bad -ne 0 ]]; then
  echo 'verification FAILED: the copy does not match its source; keep the worktree and report this' >&2
  exit 1
fi
echo "verified: $verified item(s) identical to their source"

printf 'migrated_to=%s\n' "$destination"
printf 'migration=%s\n' "$migration"
printf 'state and asset links copied; source was not deleted\n'
