#!/usr/bin/env python3
"""Generate today's draft markdown (AI optional)."""
from __future__ import annotations

import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rotation import TRACK_LABELS, next_track  # noqa: E402

CURRICULUM = ROOT / "config" / "curriculum.json"
AUDIT_TARGETS = ROOT / "config" / "audit-targets.json"


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "draft"


def fill_template(path: Path, mapping: dict) -> str:
    out = path.read_text()
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def call_openai(prompt: str) -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You write concise, accurate engineering notes for a public learning repo. No fluff. Use markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        print(f"OpenAI error: {e}", file=sys.stderr)
        return None


def call_anthropic(prompt: str) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        print(f"Anthropic error: {e}", file=sys.stderr)
        return None


def ai_complete(prompt: str) -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return call_openai(prompt)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return call_anthropic(prompt)
    return None


def generate_learn(today: str, topic: str) -> tuple[Path, Path | None]:
    tpl = ROOT / "templates" / "day-a-learn.md"
    slug = slugify(topic)
    note_path = ROOT / "notes" / f"{today}-{slug}.md"
    example_path = ROOT / "examples" / today / f"{slug}.js"

    prompt = f"""Write sections for a learn-in-public note on: "{topic}".
Return JSON only with keys:
what_i_learned, why_it_matters, example_code, gotcha, link_1, link_2, lang
(example_code should be short, runnable JavaScript or TypeScript unless topic dictates otherwise)"""

    ai = ai_complete(prompt)
    if ai:
        try:
            # extract JSON from markdown fence if present
            m = re.search(r"\{[\s\S]*\}", ai)
            data = json.loads(m.group() if m else ai)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    mapping = {
        "TITLE": topic,
        "DATE": today,
        "WHAT_I_LEARNED": data.get(
            "what_i_learned",
            f"(Draft) Explain {topic} in your own words after reading docs.",
        ),
        "WHY_IT_MATTERS": data.get(
            "why_it_matters", "Add why this matters for backend/frontend work."
        ),
        "EXAMPLE_CODE": data.get(
            "example_code", "// TODO: add minimal runnable example\nconsole.log('hello');"
        ),
        "GOTCHA": data.get("gotcha", "TODO: one common mistake"),
        "LINK_1": data.get("link_1", "https://developer.mozilla.org/"),
        "LINK_2": data.get("link_2", "https://nodejs.org/docs/"),
        "LANG": data.get("lang", "javascript"),
    }
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(fill_template(tpl, mapping))

    example_path.parent.mkdir(parents=True, exist_ok=True)
    if data.get("example_code"):
        example_path.write_text(data["example_code"].strip() + "\n")
        return note_path, example_path
    return note_path, None


def generate_case_study(today: str, theme: str) -> Path:
    tpl = ROOT / "templates" / "day-b-case-study.md"
    slug = slugify(theme)
    out_path = ROOT / "case-studies" / f"{today}-{slug}.md"

    prompt = f"""Hypothetical system design practice: "{theme}".
Return JSON with keys: context, functional_reqs, non_functional_reqs, constraints,
mermaid_diagram (flowchart TD syntax only, no backticks), opt_a, opt_b,
recommendation, tradeoffs, failure_modes, week1, month3"""

    ai = ai_complete(prompt)
    data = {}
    if ai:
        try:
            m = re.search(r"\{[\s\S]*\}", ai)
            data = json.loads(m.group() if m else ai)
        except json.JSONDecodeError:
            data = {}

    mapping = {
        "TITLE": f"Hypothetical: {theme}",
        "DATE": today,
        "CONTEXT": data.get("context", f"Public design exercise: {theme}."),
        "FUNCTIONAL_REQS": data.get("functional_reqs", "TODO"),
        "NON_FUNCTIONAL_REQS": data.get("non_functional_reqs", "TODO: scale, latency, cost"),
        "CONSTRAINTS": data.get("constraints", "TODO"),
        "MERMAID_DIAGRAM": data.get(
            "mermaid_diagram", "flowchart TD\n  Client --> API\n  API --> DB"
        ),
        "OPT_A": data.get("opt_a", "Monolith"),
        "OPT_B": data.get("opt_b", "Microservices"),
        "RECOMMENDATION": data.get("recommendation", "TODO after review"),
        "TRADEOFFS": data.get("tradeoffs", "TODO"),
        "FAILURE_MODES": data.get("failure_modes", "TODO"),
        "WEEK1": data.get("week1", "MVP scope"),
        "MONTH3": data.get("month3", "Hardening and scale"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(fill_template(tpl, mapping))
    return out_path


def generate_audit(today: str) -> Path:
    tpl = ROOT / "templates" / "day-c-audit.md"
    targets = load_json(AUDIT_TARGETS)
    repos = targets.get("repos") or []
    if not repos:
        raise SystemExit("No audit targets in config/audit-targets.json")

    target = random.choice(repos)
    name = target["name"]
    ref = target.get("github") or name
    slug = slugify(name)
    out_path = ROOT / "audits" / f"{today}-{slug}.md"

    prompt = f"""You are doing a hypothetical static audit checklist for an engineer's OWN open source repo: {ref}.
Do NOT claim you scanned production systems. Return JSON:
scope, sev1, finding1, fix1, sev2, finding2, fix2, strengths, pr_1, pr_2
Focus on: dependencies, secrets, error handling, tests, README, API validation."""

    ai = ai_complete(prompt)
    data = {}
    if ai:
        try:
            m = re.search(r"\{[\s\S]*\}", ai)
            data = json.loads(m.group() if m else ai)
        except json.JSONDecodeError:
            data = {}

    mapping = {
        "TITLE": f"Audit: {name}",
        "DATE": today,
        "TARGET_NAME": name,
        "TARGET_REF": ref,
        "SCOPE": data.get(
            "scope",
            f"Static checklist review of {ref} (verify findings manually before merge).",
        ),
        "SEV1": data.get("sev1", "medium"),
        "SEV2": data.get("sev2", "low"),
        "STRENGTHS": data.get("strengths", "TODO: what is already good"),
        "PR_1": data.get("pr_1", "Add tests for core API paths"),
        "PR_2": data.get("pr_2", "Document env vars in README"),
    }
    body = fill_template(tpl, mapping)
    # inject findings table rows if AI returned them
    if data.get("finding1"):
        body = body.replace(
            "| F1 | {{SEV1}} | | | |",
            f"| F1 | {data.get('sev1', 'medium')} | general | {data['finding1']} | {data.get('fix1', '')} |",
        )
    if data.get("finding2"):
        body = body.replace(
            "| F2 | {{SEV2}} | | | |",
            f"| F2 | {data.get('sev2', 'low')} | general | {data['finding2']} | {data.get('fix2', '')} |",
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body)
    return out_path


def main() -> int:
    load_env()
    today = date.today().isoformat()
    track = next_track()
    curriculum = load_json(CURRICULUM)

    print(f"Track: {track} ({TRACK_LABELS[track]})")

    if track == "learn":
        topic = os.environ.get("TOPIC_HINT") or random.choice(curriculum["learn_topics"])
        note, ex = generate_learn(today, topic)
        print(f"Note: {note.relative_to(ROOT)}")
        if ex:
            print(f"Example: {ex.relative_to(ROOT)}")
    elif track == "case-study":
        theme = os.environ.get("CASE_STUDY_HINT") or random.choice(
            curriculum["case_study_themes"]
        )
        path = generate_case_study(today, theme)
        print(f"Case study: {path.relative_to(ROOT)}")
    else:
        path = generate_audit(today)
        print(f"Audit: {path.relative_to(ROOT)}")

    # output for shell scripts
    print(f"TRACK={track}")
    print(f"DATE={today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
