#!/usr/bin/env bash
# Merge approved draft into main and push (counts as YOUR contribution after review).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CURRENT="$(git branch --show-current)"

merge_pr_via_gh() {
  if command -v gh >/dev/null 2>&1; then
    PR_NUM="$(gh pr list --head "$CURRENT" --json number -q '.[0].number' 2>/dev/null || true)"
    if [[ -n "$PR_NUM" && "$PR_NUM" != "null" ]]; then
      echo "Merging PR #$PR_NUM via GitHub CLI..."
      gh pr merge "$PR_NUM" --merge --delete-branch
      git checkout main
      git pull origin main
      echo "Merged and pushed."
      exit 0
    fi
  fi
  return 1
}

if [[ "$CURRENT" == "main" ]]; then
  echo "You are on main. Checkout a draft branch first, e.g.:"
  git branch | grep 'draft/' || true
  exit 1
fi

if [[ ! "$CURRENT" =~ ^draft/ ]]; then
  echo "Expected a draft/* branch, got: $CURRENT"
  exit 1
fi

echo "==> Review checklist: $ROOT/REVIEW.md"
echo "==> Diff against main:"
git diff main...HEAD --stat
echo ""
read -r -p "Merge this draft to main? [y/N] " ok
[[ "$ok" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

if merge_pr_via_gh; then
  exit 0
fi

git checkout main
git pull origin main 2>/dev/null || true
git merge --no-ff "$CURRENT" -m "${CURRENT//draft\//publish: }"
git push origin main 2>/dev/null || echo "Push manually: git push origin main"
git branch -d "$CURRENT" 2>/dev/null || true
echo "Merged locally to main. Push if needed."
