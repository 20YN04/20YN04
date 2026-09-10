#!/usr/bin/env python3
"""Render the selected-work list as a card, in the same system as the others.

Same cobalt ground, same mono key/value rhythm as the neofetch card, same
reveal that survives a frozen renderer (see scripts/_svg.py).

  python scripts/make_work_card.py
  STATIC=1 python scripts/make_work_card.py   # frozen frame
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _svg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "selected-work.svg")

WIDTH = 862.0
PAD_X = 30.0
PAD_Y = 26.0
KEY_X = 0.0
VAL_X = 102.0
ROW_H = 20.0
BLOCK_GAP = 16.0
HEAD_H = 44.0

C_BG = "#0A0C12"
C_BORDER = "#1E2534"
C_INK = "#DCE1EC"
C_MUTED = "#828A9C"
C_DIM = "#454E63"
C_ACCENT = "#2E63DC"

TITLE = "selected work"

# (name, badge, badge_tone, [(line, tone), ...])
WORK = [
    ("KotKompas", "public", "dim", [
        ("student-housing review platform", "ink"),
        ("KotScore engine — Bayesian rating, anti-manipulation, "
         "review privacy by design. 180+ commits.", "muted"),
        ("Laravel · Livewire · Filament · PostgreSQL", "dim"),
        ("github.com/woutvanlommel/KotKompas", "dim"),
    ]),
    ("Coeus", "private", "dim", [
        ("white-label knowledge base", "ink"),
        ("Local-first desktop app over your own docs — cited answers, "
         "swappable AI providers, offline.", "muted"),
        ("Next.js · TypeScript · Tauri · RAG", "dim"),
    ]),
    ("Ynarchive", "in progress", "accent", [
        ("studio site", "ink"),
        ("Scroll-driven frontend. The home of my own builds and client work.",
         "muted"),
        ("Next.js · GSAP · Three.js", "dim"),
    ]),
]

TONE = {"ink": "v", "muted": "vm", "dim": "vd", "accent": "va"}


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(static=False):
    rows = sum(len(lines) for _, _, _, lines in WORK)
    height = (PAD_Y + HEAD_H + rows * ROW_H
              + (len(WORK) - 1) * BLOCK_GAP + PAD_Y)

    o = []
    o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
             'viewBox="0 0 %.2f %.2f" role="img" aria-label="Selected work">'
             % (WIDTH, height, WIDTH, height))
    o.append("<title>selected work</title>")

    style = [
        "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono',monospace}",
        ".host{fill:%s;font-size:14px;letter-spacing:.2px}" % C_INK,
        ".hint{fill:%s;font-size:10px;letter-spacing:1.4px}" % C_DIM,
        ".k{fill:%s;font-size:11px;letter-spacing:1.2px}" % C_MUTED,
        ".badge{fill:%s;font-size:10px;letter-spacing:1.4px}" % C_DIM,
        ".badge.accent{fill:%s}" % C_ACCENT,
        ".v{fill:%s;font-size:12.5px}" % C_INK,
        ".vm{fill:%s;font-size:11.5px}" % C_MUTED,
        ".vd{fill:%s;font-size:11px}" % C_DIM,
        ".va{fill:%s;font-size:11px}" % C_ACCENT,
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
             % (PAD_X, PAD_Y + 16, esc(TITLE)))
    o.append('<text class="hint" x="%.2f" y="%.2f" text-anchor="end">%d '
             'PROJECTS</text>' % (WIDTH - PAD_X, PAD_Y + 16, len(WORK)))
    o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="1" fill="%s"/>'
             % (PAD_X, PAD_Y + 28, WIDTH - PAD_X * 2, C_BORDER))
    o.append("</g>")

    y = PAD_Y + HEAD_H + 12
    step = 1
    for name, badge, badge_tone, lines in WORK:
        for j, (text, tone) in enumerate(lines):
            o.append("<g>%s" % anim(step))
            if j == 0:
                o.append('<text class="k" x="%.2f" y="%.2f">%s</text>'
                         % (PAD_X + KEY_X, y, esc(name.upper())))
                o.append('<text class="badge%s" x="%.2f" y="%.2f" '
                         'text-anchor="end">%s</text>'
                         % (" accent" if badge_tone == "accent" else "",
                            WIDTH - PAD_X, y, esc(badge.upper())))
            o.append('<text class="%s" x="%.2f" y="%.2f">%s</text>'
                     % (TONE[tone], PAD_X + VAL_X, y, esc(text)))
            o.append("</g>")
            y += ROW_H
            step += 1
        y += BLOCK_GAP

    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(static=os.environ.get("STATIC") == "1"))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
