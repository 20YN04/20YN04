#!/usr/bin/env python3
"""Render the neofetch-style info card as a self-contained animated SVG.

Static facts live in ROWS. The uptime line is pulled from
data/contributions.json when it exists, so the card refreshes with the
heatmap instead of going stale.

  python scripts/make_info_card.py
  STATIC=1 python scripts/make_info_card.py   # frozen frame
"""

from __future__ import annotations

import json
import os

import _svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "info-card.svg")

WIDTH = 862.0
PAD_X = 30.0
PAD_Y = 26.0
KEY_X = 30.0
VAL_X = 132.0
ROW_H = 24.0
HEAD_H = 44.0

C_BG = "#0C0C0B"
C_BORDER = "#2A2A27"
C_INK = "#DCDCD6"
C_MUTED = "#8A8A85"
C_DIM = "#4A4A44"
C_ACCENT = "#C2410C"

HOST = "yentl@ynarchive"

ROWS = [
    ("role", "Solo designer + full-stack developer", "ink"),
    ("base", "Belgium · EU · NL / EN", "ink"),
    ("front", "Next.js · React · Angular · TypeScript · Tailwind · Vite", "ink"),
    ("back", "Laravel · Livewire · Python · Node.js · PostgreSQL · Supabase", "ink"),
    ("motion", "GSAP · Three.js · scroll-driven frontends", "ink"),
    ("security", "Honeypots · firewalls · malware analysis", "ink"),
    ("design", "Figma · Swiss grid · four colours, one accent", "ink"),
    ("shell", "zsh · macOS · Obsidian second brain", "ink"),
    ("uptime", None, "ink"),                                   # filled from data
    ("rule", "never commit straight to main", "accent"),
    ("open to", "full-stack & AI engineering roles", "accent"),
]


def uptime():
    try:
        with open(DATA, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (IOError, ValueError):
        return "—"
    return "{:,} contributions this year · {} day streak · longest {}".format(
        payload["total"], payload["current_streak"], payload["longest_streak"])


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(static=False):
    rows = [(k, v if v is not None else uptime(), t) for k, v, t in ROWS]
    height = PAD_Y + HEAD_H + len(rows) * ROW_H + PAD_Y

    o = []
    o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
             'viewBox="0 0 %.2f %.2f" role="img" aria-label="%s">'
             % (WIDTH, height, WIDTH, height, esc(HOST)))
    o.append("<title>%s</title>" % esc(HOST))

    style = [
        "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono',monospace}",
        ".host{fill:%s;font-size:14px;letter-spacing:.2px}" % C_INK,
        ".hint{fill:%s;font-size:10px;letter-spacing:1.4px}" % C_DIM,
        ".k{fill:%s;font-size:11px;letter-spacing:1.2px}" % C_MUTED,
        ".v{fill:%s;font-size:12.5px}" % C_INK,
        ".v.accent{fill:%s}" % C_ACCENT,
    ]
    o.append("<style>%s</style>" % "".join(style))

    o.append('<rect x="0.5" y="0.5" width="%.2f" height="%.2f" rx="4" fill="%s" '
             'stroke="%s"/>' % (WIDTH - 1, height - 1, C_BG, C_BORDER))

    def anim(i):
        if static:
            return ""
        return _svg.reveal(i * 0.062) + _svg.slide(i * 0.062)

    o.append("<g>%s" % anim(0))
    o.append('<text class="host" x="%.2f" y="%.2f">%s</text>'
             % (PAD_X, PAD_Y + 16, esc(HOST)))
    o.append('<text class="hint" x="%.2f" y="%.2f" text-anchor="end">NEOFETCH</text>'
             % (WIDTH - PAD_X, PAD_Y + 16))
    o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="1" fill="%s"/>'
             % (PAD_X, PAD_Y + 28, WIDTH - PAD_X * 2, C_BORDER))
    o.append("</g>")

    y = PAD_Y + HEAD_H + 12
    for i, (key, value, tone) in enumerate(rows):
        cls = "v accent" if tone == "accent" else "v"
        o.append("<g>%s" % anim(i + 1))
        o.append('<text class="k" x="%.2f" y="%.2f">%s</text>'
                 % (PAD_X + KEY_X - 30, y + i * ROW_H, esc(key.upper())))
        o.append('<text class="%s" x="%.2f" y="%.2f">%s</text>'
                 % (cls, PAD_X + VAL_X - 30, y + i * ROW_H, esc(value)))
        o.append("</g>")

    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(static=os.environ.get("STATIC") == "1"))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
