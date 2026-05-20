#!/usr/bin/env python3
"""3-day rotation: learn → case-study → audit (date-based, stable everywhere)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / ".rotation-state.json"
TRACKS = ("learn", "case-study", "audit")
TRACK_LABELS = {
    "learn": "Day A — Learn",
    "case-study": "Day B — Case study",
    "audit": "Day C — Audit",
}
ANCHOR = date(2026, 1, 1)


def track_for_date(d: date) -> str:
    days = (d - ANCHOR).days
    return TRACKS[days % len(TRACKS)]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(track: str, run_date: str) -> None:
    STATE_FILE.write_text(
        json.dumps({"last_track": track, "last_date": run_date}, indent=2) + "\n"
    )


def next_track(for_date: date | None = None) -> str:
    """Track for calendar day; same track if you re-run the same day."""
    today_date = for_date or date.today()
    today = today_date.isoformat()
    state = load_state()

    if state.get("last_date") == today and state.get("last_track") in TRACKS:
        return state["last_track"]

    track = track_for_date(today_date)
    save_state(track, today)
    return track


if __name__ == "__main__":
    print(next_track())
