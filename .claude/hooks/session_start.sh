#!/usr/bin/env bash
# SessionStart: sync the current branch to its upstream (if clean) and surface state.
# Repo/branch-agnostic — safe to drop into any repo. No tests (saves credits).
set -u
UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)"
if [ -n "$UPSTREAM" ] && [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  git fetch -q 2>/dev/null \
    && git merge --ff-only "$UPSTREAM" -q 2>/dev/null \
    && echo "✓ synced with $UPSTREAM"
else
  echo "⚠ no upstream or local changes present — skipping auto-pull"
fi
echo; echo "===== HANDOFF.md ====="
[ -f HANDOFF.md ] && cat HANDOFF.md || echo "(no HANDOFF.md yet)"
echo; echo "===== last 5 commits ====="
git log --oneline -5 2>/dev/null
