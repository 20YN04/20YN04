#!/usr/bin/env python3
"""Draw the branch graph as an animated ASCII banner, self-contained in one SVG.

Feature branches leave main, carry their own commits, and merge back. The last
branch is still open. The whole graph reveals left to right, like commits
landing, then freezes.

GitHub strips <script> and inline CSS from markdown but renders SVGs embedded
via <img> with their CSS keyframes intact, so every moving part lives in here.

  python scripts/make_ascii_svg.py          # writes ascii-branches.svg
  STATIC=1 python scripts/make_ascii_svg.py # frozen frame, for local preview
"""

from __future__ import annotations

import os

import _svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID_PATH = os.path.join(ROOT, "data", "ascii-branches.txt")
OUT_PATH = os.path.join(ROOT, "ascii-branches.svg")

COLS = 158
FONT_SIZE = 9.0
LINE_HEIGHT = 9.0
CHAR_W = 5.4          # monospace advance at 9px is ~0.6em
PAD_X = 26.0
PAD_Y = 22.0
CAPTION_H = 28.0

# Warm Dark palette — vault: Design & Styles/Mainstyle.md
C_BG = "#0C0C0B"
C_BORDER = "#2A2A27"
C_INK = "#DCDCD6"
C_MUTED = "#8A8A85"
C_DIM = "#4A4A44"
C_ACCENT = "#C2410C"

CLASS_FILL = {"i": C_INK, "m": C_MUTED, "d": C_DIM, "a": C_ACCENT}

MAIN_ROW = 13
CAPTION = "one branch = one discrete thing   \u00b7   delete it after the merge"

# (start, end, lane, label). end=None means the branch is still open.
BRANCHES = [
    (4,   42,  9, "feat/kotscore-engine"),
    (22,  56, 17, "fix/plate-mount"),
    (34,  80,  5, "refactor/rag-index"),
    (50,  92, 21, "chore/worktree-sweep"),
    (72, 114, 17, "docs/agents-block"),
    (92, 130,  9, "test/browser-verify"),
    (114, None, 5, "feat/animated-profile-readme"),
]


class Canvas(object):
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.ch = [[" "] * cols for _ in range(rows)]
        self.cl = [["i"] * cols for _ in range(rows)]

    def put(self, r, c, char, cls):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.ch[r][c] = char
            self.cl[r][c] = cls

    def text(self, r, c, s, cls):
        for i, char in enumerate(s):
            self.put(r, c + i, char, cls)


def build():
    rows = max(lane for _, _, lane, _ in BRANCHES) + 4
    rows = max(rows, MAIN_ROW + 4)
    cv = Canvas(COLS, rows)

    plan = []
    for start, end, lane, label in BRANCHES:
        dr = abs(MAIN_ROW - lane)
        run_start = start + dr
        run_end = COLS - 1 if end is None else end - dr
        plan.append(dict(start=start, end=end, lane=lane, label=label, dr=dr,
                         up=lane < MAIN_ROW, run_start=run_start, run_end=run_end,
                         cls="a" if end is None else "i"))

    # main — the spine everything returns to
    for c in range(COLS):
        cv.put(MAIN_ROW, c, "-", "m")

    # 1. horizontal runs
    for b in plan:
        for c in range(b["run_start"], b["run_end"] + 1):
            cv.put(b["lane"], c, "-", b["cls"])

    # 2. diagonals last, so a passing line reads as crossing over
    for b in plan:
        for k in range(1, b["dr"] + 1):
            r = MAIN_ROW - k if b["up"] else MAIN_ROW + k
            cv.put(r, b["start"] + k, "/" if b["up"] else "\\", b["cls"])
        cv.put(MAIN_ROW, b["start"], "o", "i")
        if b["end"] is not None:
            for k in range(1, b["dr"] + 1):
                r = b["lane"] + k if b["up"] else b["lane"] - k
                cv.put(r, b["run_end"] + k, "\\" if b["up"] else "/", b["cls"])
            cv.put(MAIN_ROW, b["end"], "o", "i")

    # 3. each branch carries its name, placed where no line crosses it
    for b in plan:
        tag = " " + b["label"] + " "
        lo, hi = b["run_start"] + 1, b["run_end"] - 1
        ideal = b["run_start"] + max(1, (b["run_end"] - b["run_start"] + 1 - len(tag)) // 2)
        spot = None
        for ls in sorted(range(lo, hi - len(tag) + 2), key=lambda x: abs(x - ideal)):
            if all(cv.ch[b["lane"]][c] == "-" for c in range(ls, ls + len(tag))):
                spot = ls
                break
        if spot is None:
            spot = max(lo, min(ideal, hi - len(tag) + 1))
            print("warning: no clear window for %s" % b["label"])
        cv.text(b["lane"], spot, tag, "a" if b["cls"] == "a" else "d")
        b["tag_span"] = (spot, spot + len(tag) - 1)

    # 4. commits on each branch, in whatever line is left
    for b in plan:
        ls, le = b["tag_span"]
        for c in (b["run_start"] + 2, ls - 3, le + 3, b["run_end"] - 2):
            if b["run_start"] <= c <= b["run_end"] and cv.ch[b["lane"]][c] == "-":
                cv.put(b["lane"], c, "*", b["cls"])
        if b["end"] is None:
            cv.put(b["lane"], b["run_end"], "*", "a")

    # 5. commits that landed straight on main
    for c in (1, 30, 66, 104, 140, 156):
        if cv.ch[MAIN_ROW][c] == "-":
            cv.put(MAIN_ROW, c, "o", "m")

    return crop(cv)


def crop(cv):
    """Trim empty rows, keeping one blank row of breathing space."""
    used = [r for r in range(cv.rows) if "".join(cv.ch[r]).strip()]
    top = max(0, used[0] - 1)
    bottom = min(cv.rows, used[-1] + 2)
    out = Canvas(cv.cols, bottom - top)
    out.ch = [row[:] for row in cv.ch[top:bottom]]
    out.cl = [row[:] for row in cv.cl[top:bottom]]
    return out


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(chars, classes):
    """Collapse a row into (text, class) runs so each row is a few tspans."""
    out = []
    buf = chars[0]
    cur = classes[0]
    for char, cls in zip(chars[1:], classes[1:]):
        if cls == cur:
            buf += char
        else:
            out.append((buf, cur))
            buf, cur = char, cls
    out.append((buf, cur))
    return out


def render(cv, static=False):
    art_w = cv.cols * CHAR_W
    art_h = cv.rows * LINE_HEIGHT
    width = art_w + PAD_X * 2
    height = art_h + PAD_Y * 2 + CAPTION_H
    sweep = 2.2

    o = []
    o.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
        'viewBox="0 0 %.2f %.2f" role="img" '
        'aria-label="ASCII git graph: feature branches leaving main and merging '
        'back, the last one still open">' % (width, height, width, height)
    )
    o.append("<title>branch per task</title>")

    style = [
        "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono',monospace;white-space:pre}",
    ]
    for key, fill in CLASS_FILL.items():
        style.append(".%s{fill:%s}" % (key, fill))
    style.append(".cap{fill:%s;font-size:10px;letter-spacing:1.4px}" % C_MUTED)
    o.append("<style>%s</style>" % "".join(style))

    o.append(
        '<rect x="0.5" y="0.5" width="%.2f" height="%.2f" rx="4" fill="%s" '
        'stroke="%s"/>' % (width - 1, height - 1, C_BG, C_BORDER)
    )

    if static:
        o.append("<g>")
    else:
        o.append(
            '<defs><clipPath id="sweep"><rect x="%.2f" y="0" width="%.2f" '
            'height="%.2f">%s</rect></clipPath></defs>'
            % (PAD_X, art_w, height, _svg.wipe(art_w, sweep))
        )
        o.append('<g clip-path="url(#sweep)">')

    baseline = PAD_Y + FONT_SIZE
    for r in range(cv.rows):
        parts = []
        for text, cls in runs(cv.ch[r], cv.cl[r]):
            parts.append('<tspan class="%s">%s</tspan>' % (cls, esc(text)))
        o.append(
            '<text x="%.2f" y="%.2f" font-size="%.2f" textLength="%.2f" '
            'lengthAdjust="spacingAndGlyphs" xml:space="preserve">%s</text>'
            % (PAD_X, baseline + r * LINE_HEIGHT, FONT_SIZE, art_w, "".join(parts))
        )
    o.append("</g>")

    if not static:
        # the playhead rides the wipe edge, then leaves. Hidden when frozen.
        o.append(
            '<rect x="%.2f" y="%.2f" width="1" height="%.2f" fill="%s" opacity="0">'
            '%s'
            '<animateTransform attributeName="transform" type="translate" '
            'values="0 0;%.2f 0" dur="%.3fs" fill="freeze" calcMode="spline" '
            'keyTimes="0;1" keySplines="%s"/></rect>'
            % (PAD_X, PAD_Y - 4, art_h + 8, C_ACCENT, _svg.playhead(sweep),
               art_w, sweep, _svg.EASE)
        )

    o.append("<g>%s<text class=\"cap\" x=\"%.2f\" y=\"%.2f\" "
             "xml:space=\"preserve\">%s</text></g>"
             % ("" if static else _svg.reveal(sweep - 0.2, 0.6),
                PAD_X, height - PAD_Y + 6, esc(CAPTION)))
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    cv = build()
    os.makedirs(os.path.dirname(GRID_PATH), exist_ok=True)
    with open(GRID_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join("".join(row).rstrip() for row in cv.ch) + "\n")
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(render(cv, static=os.environ.get("STATIC") == "1"))
    print("wrote %s (%d x %d)" % (OUT_PATH, cv.cols, cv.rows))


if __name__ == "__main__":
    main()
