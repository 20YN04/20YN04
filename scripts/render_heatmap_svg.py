#!/usr/bin/env python3
"""Render data/contributions.json as a self-contained animated heatmap SVG.

53 weeks by 7 days, revealed on a diagonal sweep, then frozen. The colour ramp
is the Warm Dark accent from the vault design system, not GitHub green — same
data, own palette.

  python scripts/render_heatmap_svg.py
  STATIC=1 python scripts/render_heatmap_svg.py   # frozen frame
"""

from __future__ import annotations

import json
import os

import _svg
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")

WIDTH = 862.0
PAD_X = 26.0
PAD_Y = 22.0
GUTTER = 34.0        # room for the weekday labels
GAP = 3.0
MONTH_H = 18.0
FOOT_H = 34.0

C_BG = "#0C0C0B"
C_BORDER = "#2A2A27"
C_INK = "#DCDCD6"
C_MUTED = "#8A8A85"
C_DIM = "#5A5A54"

# none → busiest. Warm Dark accent ramp, vault: Design & Styles/Mainstyle.md
RAMP = ["#191917", "#4A2410", "#7A360D", "#A8420C", "#C2410C", "#E8763A"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def levels(days):
    """Rank non-zero days into five buckets, so the ramp uses its whole range."""
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    if not counts:
        return [0] * len(days)
    cuts = [counts[min(len(counts) - 1, int(len(counts) * q))]
            for q in (0.40, 0.65, 0.82, 0.94)]
    out = []
    for entry in days:
        n = entry["count"]
        if n <= 0:
            out.append(0)
            continue
        level = 1
        for cut in cuts:
            if n > cut:
                level += 1
        out.append(min(level, 5))
    return out


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(payload, static=False):
    days = payload["days"]
    lv = levels(days)

    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    col0 = (first.weekday() + 1) % 7          # Sunday-first row index

    cells = []
    for i, entry in enumerate(days):
        slot = col0 + i
        cells.append((slot // 7, slot % 7, entry, lv[i]))
    weeks = max(c[0] for c in cells) + 1

    pitch = (WIDTH - PAD_X * 2 - GUTTER) / weeks
    size = pitch - GAP
    grid_h = pitch * 7 - GAP
    grid_x = PAD_X + GUTTER
    grid_y = PAD_Y + MONTH_H
    height = grid_y + grid_h + FOOT_H + PAD_Y

    span = weeks * 16.0 + 7 * 26.0
    o = []
    o.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
        'viewBox="0 0 %.2f %.2f" role="img" aria-label="%s contributions in the '
        'last year">' % (WIDTH, height, WIDTH, height, esc(payload["total"]))
    )
    o.append("<title>%s contributions in the last year</title>" % esc(payload["total"]))

    style = [
        "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono',monospace}",
        ".lbl{fill:%s;font-size:9px;letter-spacing:.6px}" % C_DIM,
        ".foot{fill:%s;font-size:10.5px;letter-spacing:.3px}" % C_MUTED,
        ".hi{fill:%s}" % C_INK,
    ]
    o.append("<style>%s</style>" % "".join(style))

    o.append('<rect x="0.5" y="0.5" width="%.2f" height="%.2f" rx="4" fill="%s" '
             'stroke="%s"/>' % (WIDTH - 1, height - 1, C_BG, C_BORDER))

    # month labels, one per month at the week it starts
    seen = set()
    for week, row, entry, _ in cells:
        month = entry["date"][:7]
        if month in seen:
            continue
        seen.add(month)
        if week == 0 and row > 0:
            continue
        idx = int(entry["date"][5:7]) - 1
        o.append('<text class="lbl" x="%.2f" y="%.2f">%s</text>'
                 % (grid_x + week * pitch, PAD_Y + 10, MONTHS[idx]))

    for row, label in DAY_LABELS.items():
        o.append('<text class="lbl" x="%.2f" y="%.2f" text-anchor="end">%s</text>'
                 % (PAD_X + GUTTER - 8, grid_y + row * pitch + size * 0.78, label))

    # the grid — a diagonal sweep, top-left to bottom-right
    for week, row, entry, level in cells:
        delay = "" if static else _svg.reveal(week * 0.016 + row * 0.026, 0.42)
        o.append(
            '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="2" '
            'fill="%s">%s<title>%s on %s</title></rect>'
            % (grid_x + week * pitch, grid_y + row * pitch, size, size,
               RAMP[level], delay,
               esc("%d contribution%s" % (entry["count"],
                                          "" if entry["count"] == 1 else "s")),
               esc(entry["date"]))
        )

    # footer: legend left, the numbers that matter right
    fy = grid_y + grid_h + 22
    o.append("<g>%s" % ("" if static else _svg.reveal(span / 1000.0 + 0.24, 0.6)))
    o.append('<text class="foot" x="%.2f" y="%.2f">Less</text>' % (PAD_X, fy))
    lx = PAD_X + 30
    for i, colour in enumerate(RAMP):
        o.append('<rect x="%.2f" y="%.2f" width="9" height="9" rx="2" fill="%s"/>'
                 % (lx + i * 12, fy - 8, colour))
    o.append('<text class="foot" x="%.2f" y="%.2f">More</text>'
             % (lx + len(RAMP) * 12 + 4, fy))

    best = payload["best_day"]
    o.append(
        '<text class="foot" x="%.2f" y="%.2f" text-anchor="end">'
        '<tspan class="hi">%s</tspan><tspan> contributions</tspan>'
        '<tspan dx="14">streak </tspan><tspan class="hi">%d</tspan>'
        '<tspan dx="14">longest </tspan><tspan class="hi">%d</tspan>'
        '<tspan dx="14">best day </tspan><tspan class="hi">%d</tspan>'
        '<tspan> on %s</tspan></text>'
        % (WIDTH - PAD_X, fy, esc("{:,}".format(payload["total"])),
           payload["current_streak"], payload["longest_streak"],
           best["count"], esc(best["date"]))
    )
    o.append("</g>")
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    with open(DATA, encoding="utf-8") as fh:
        payload = json.load(fh)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(payload, static=os.environ.get("STATIC") == "1"))
    print("wrote %s (%d days)" % (OUT, len(payload["days"])))


if __name__ == "__main__":
    main()
