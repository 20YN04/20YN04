#!/usr/bin/env python3
"""Pull the real contribution calendar off the public GitHub profile page.

No token, no API key. GitHub serves the calendar as plain HTML at
https://github.com/users/<user>/contributions, which is public for every
account. Writes data/contributions.json with one entry per day plus the
derived stats the SVGs need.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "20YN04")
URL = "https://github.com/users/%s/contributions" % USER
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "contributions.json")

HEADERS = {
    "User-Agent": "profile-art/1.0 (+https://github.com/%s)" % USER,
    "Accept": "text/html",
    "X-Requested-With": "XMLHttpRequest",
}


def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    # Counts live in the <tool-tip> elements, keyed by the cell's id.
    counts = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        m = re.search(r"^(No|\d[\d,]*)\s+contribution", tip.get_text(strip=True))
        if m:
            raw = m.group(1)
            counts[target] = 0 if raw == "No" else int(raw.replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        day = td.get("data-date")
        if not day:
            continue
        count = counts.get(td.get("id"))
        if count is None:
            count = int(td.get("data-count") or 0)
        days.append({
            "date": day,
            "count": count,
            "level": int(td.get("data-level") or 0),
        })

    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    """Current and longest run of consecutive days with at least one commit.

    Today is excluded from breaking the current streak — a day still in
    progress is not a gap yet.
    """
    longest = run = 0
    for entry in days:
        if entry["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    today = date.today().isoformat()
    current = 0
    for entry in reversed(days):
        if entry["date"] > today:
            continue
        if entry["count"] > 0:
            current += 1
        elif entry["date"] == today:
            continue
        else:
            break
    return current, longest


def main():
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    days = parse(resp.text)
    if not days:
        raise SystemExit("no contribution cells found — GitHub markup changed?")

    # Keep the trailing 53 weeks, aligned so each column is a full Sun-Sat week.
    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    start = last - timedelta(days=371)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday
    days = [d for d in days if d["date"] >= start.isoformat()]

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    months = {}
    for entry in days:
        months[entry["date"][:7]] = months.get(entry["date"][:7], 0) + entry["count"]

    payload = {
        "user": USER,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"] > 0),
        "months": months,
        "days": days,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")

    print("%s: %d days, %d contributions, streak %d (longest %d)"
          % (USER, len(days), total, current, longest))


if __name__ == "__main__":
    sys.exit(main())
