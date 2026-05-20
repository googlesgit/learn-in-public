# learn-in-public

A 3-day rotation repo for **real** engineering growth — not empty commits.

| Day | Track | Folder |
|-----|--------|--------|
| A | What I learned + code example | `notes/` + `examples/` |
| B | Hypothetical system design (public sources only) | `case-studies/` |
| C | Quality / security audit (your projects only) | `audits/` |

**Rule:** AI drafts → you review → you merge. Nothing hits `main` without your approval.

---

## Quick start (from Cursor or terminal)

```bash
cd ~/projects/learn-in-public

# 1. One-time: copy env and add your API key
cp .env.example .env
# Edit .env — set OPENAI_API_KEY or ANTHROPIC_API_KEY (optional; templates work without AI)

# 2. Generate today's draft (opens a PR if gh is installed, else local branch)
./scripts/run-today.sh

# 3. Review the file, edit in Cursor, then approve:
./scripts/approve.sh
```

---

## Connect from Cursor

1. **File → Open Folder** → `~/projects/learn-in-public`
2. Install recommended extensions if prompted (optional).
3. Terminal in Cursor uses the same commands as above.
4. After first push, clone on other machines:  
   `git clone https://github.com/googlesgit/learn-in-public.git`

---

## GitHub setup (one time)

1. Create repo: https://github.com/new → name: `learn-in-public` → public → no README (we have one).
2. From this folder:

```bash
cd ~/projects/learn-in-public
git init
git branch -M main
git remote add origin https://github.com/googlesgit/learn-in-public.git
git add -A
git commit -m "chore: initial learn-in-public structure"
git push -u origin main
```

3. **Secrets** (for cloud automation): Repo → Settings → Secrets → Actions  
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (optional)  
4. **Install GitHub CLI** (for PR flow from your Mac):  
   `brew install gh && gh auth login`

---

## Automation modes

| Mode | How |
|------|-----|
| **Local** | `./scripts/run-today.sh` — draft on branch `draft/YYYY-MM-DD-*` |
| **Cloud** | Actions → "Daily draft" → Run workflow (or cron 14:00 UTC) |
| **Approve** | `./scripts/approve.sh` or merge PR on GitHub |

Scheduled workflows **never merge to main** — they only open PRs labeled `needs-review`.

---

## Profile tip

Pin this repo and link your best `case-studies/` and `notes/` in your profile README.
