# Roadmap

## You (setup once)

- [ ] Create GitHub repo `googlesgit/learn-in-public`
- [ ] Push this folder
- [ ] Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in repo Secrets (optional)
- [ ] `brew install gh && gh auth login`
- [ ] Copy `.env.example` → `.env` for local AI drafts

## Daily loop

| Step | Command |
|------|---------|
| 1. Draft | `./scripts/run-today.sh` |
| 2. Review | Edit files + `REVIEW.md` checklist |
| 3. Approve | `./scripts/approve.sh` |

## Rotation

| Calendar pattern | Track |
|------------------|--------|
| Day 1 (anchor cycle) | Learn |
| Day 2 | Case study |
| Day 3 | Audit |
| Repeats | … |

Anchor: 2026-01-01 = learn. Same schedule on GitHub Actions and your Mac.
