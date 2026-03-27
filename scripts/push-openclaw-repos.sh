#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/.openclaw}"
COMMIT_MSG="${2:-chore: automated backup sync}"
DRY_RUN="${DRY_RUN:-0}"
STRICT_CLEAN="${STRICT_CLEAN:-0}"

repos=(
  "$ROOT"
  "$ROOT/workspace-gus"
  "$ROOT/workspace-hector"
)

say() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

show_status_summary() {
  local output="$1"
  local shown=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    printf '%s\n' "$line"
    shown=$((shown + 1))
    if [[ "$shown" -ge 50 ]]; then
      printf '... (%s more lines omitted)\n' "$(printf '%s\n' "$output" | awk 'NF{count++} END{print (count>50?count-50:0)}')"
      break
    fi
  done <<< "$output"
}

has_remote() {
  git remote get-url origin >/dev/null 2>&1
}

current_branch() {
  git branch --show-current 2>/dev/null || true
}

tracked_ignore_conflicts() {
  git ls-files --cached --ignored --exclude-standard 2>/dev/null || true
}

working_tree_changes() {
  git status --porcelain
}

push_repo() {
  local repo="$1"
  local branch
  local status_output
  local tracked_ignored

  if [[ ! -d "$repo/.git" ]]; then
    say "Skipping $repo (not a git repo)"
    return
  fi

  say "Checking $repo"
  cd "$repo"

  if ! has_remote; then
    say "Skipping $repo (no origin remote configured)"
    return
  fi

  tracked_ignored="$(tracked_ignore_conflicts)"
  if [[ -n "$tracked_ignored" ]]; then
    say "WARNING: tracked files now match .gitignore in $repo"
    printf '%s\n' "$tracked_ignored"
    if [[ "$STRICT_CLEAN" == "1" ]]; then
      say "Skipping $repo because STRICT_CLEAN=1"
      return
    fi
  fi

  status_output="$(working_tree_changes)"
  if [[ -z "$status_output" ]]; then
    say "No local changes in $repo"
  else
    say "Changes found in $repo"
    show_status_summary "$status_output"
    run git add -A

    if [[ "$DRY_RUN" == "1" ]]; then
      say "Dry run: skipping staged diff check and commit in $repo"
    elif [[ -n "$(git diff --cached --name-only)" ]]; then
      git commit -m "$COMMIT_MSG"
    else
      say "Nothing commit-worthy after staging in $repo"
    fi
  fi

  branch="$(current_branch)"
  if [[ -z "$branch" ]]; then
    branch="main"
  fi

  say "Pushing $repo ($branch)"
  run git push origin "$branch"
}

for repo in "${repos[@]}"; do
  push_repo "$repo"
done

say "Done"
