#!/usr/bin/env bash
# Generate today's draft and open a PR (or leave on draft branch for local merge).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

echo "==> learn-in-public: generating draft"
OUTPUT="$(python3 "$ROOT/scripts/generate_draft.py")"
echo "$OUTPUT"

TRACK="$(echo "$OUTPUT" | sed -n 's/^TRACK=//p' | tail -1)"
DATE="$(echo "$OUTPUT" | sed -n 's/^DATE=//p' | tail -1)"
BRANCH="draft/${DATE}-${TRACK}"

# Ensure git repo
if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git fetch origin main 2>/dev/null || true
git checkout main 2>/dev/null || git checkout -b main
git pull origin main 2>/dev/null || true

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "Branch $BRANCH already exists. Checkout and edit, or delete it to regenerate."
  git checkout "$BRANCH"
  exit 0
fi

git checkout -b "$BRANCH"
git add notes case-studies audits examples 2>/dev/null || true
git add -A

if git diff --staged --quiet; then
  echo "Nothing to commit."
  exit 0
fi

MSG=""
case "$TRACK" in
  learn) MSG="draft(learn): $DATE" ;;
  case-study) MSG="draft(case-study): $DATE" ;;
  audit) MSG="draft(audit): $DATE" ;;
  *) MSG="draft: $DATE" ;;
esac

git commit -m "$MSG"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  git push -u origin "$BRANCH" 2>/dev/null || git push -u origin "$BRANCH" --force-with-lease
  gh pr create \
    --title "$MSG — review required" \
    --body "$(cat <<EOF
## Draft for $DATE ($TRACK)

- [ ] I read [REVIEW.md](../blob/main/REVIEW.md) and edited this draft
- [ ] Removed AI mistakes and added a personal note
- [ ] Ready to merge after review

**Do not merge until you've reviewed.**

Merge with: \`./scripts/approve.sh\` or GitHub PR UI.
EOF
)" \
    --label "needs-review" 2>/dev/null || gh pr create --title "$MSG — review required" --body "Review required. See REVIEW.md."
  echo ""
  echo "PR opened. Review in GitHub or Cursor, then run: ./scripts/approve.sh"
else
  echo ""
  echo "No GitHub CLI (gh) or not logged in."
  echo "Draft is on branch: $BRANCH"
  echo "After review: ./scripts/approve.sh"
  echo ""
  echo "Install gh: brew install gh && gh auth login"
fi
