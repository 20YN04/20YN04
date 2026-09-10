#!/usr/bin/env python3
"""Render the branch graph as a looping animated GIF.

The art is drawn in full on every frame. The motion is a cobalt pulse that
travels along the graph and repeats. That matters twice over: the loop never
hides anything, and frame 1 is already the finished picture, so a renderer that
freezes animated images (Chrome with "Play animations" off) still shows the
whole graph instead of a blank card.

  python scripts/make_ascii_gif.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_ascii_svg as art  # noqa: E402  (canvas builder lives there)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ascii-branches.gif")

FONT_SIZE = 14
CAP_SIZE = 15
PAD_X = 40
PAD_Y = 34
CAPTION_H = 44

C_BG = (10, 12, 18)
C_BORDER = (30, 37, 52)
C_GLOW = (167, 196, 255)

CLASS_RGB = {
    "i": (220, 225, 236),
    "m": (130, 138, 156),
    "d": (69, 78, 99),
    "a": (46, 99, 220),
}

FRAMES = 64
FRAME_MS = 75
BAND = 9.0          # pulse half-width, in characters

FONTS = [
    ("/System/Library/Fonts/Menlo.ttc", 0),
    ("/System/Library/Fonts/SFNSMono.ttf", 0),
    ("/Library/Fonts/Andale Mono.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 0),
]


def load_font(size):
    for path, index in FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=index)
            except (OSError, ValueError):
                continue
    raise SystemExit("no monospace font found; add one to FONTS")


def blend(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def run_spans(chars, classes):
    """Same runs as the SVG, but carrying their start column."""
    out = []
    start = 0
    buf, cur = chars[0], classes[0]
    for i in range(1, len(chars)):
        if classes[i] == cur:
            buf += chars[i]
        else:
            out.append((start, buf, cur))
            start, buf, cur = i, chars[i], classes[i]
    out.append((start, buf, cur))
    return out


def main():
    cv = art.build()
    font = load_font(FONT_SIZE)
    cap_font = load_font(CAP_SIZE)

    char_w = font.getlength("0")
    line_h = float(FONT_SIZE)
    art_w = cv.cols * char_w
    art_h = cv.rows * line_h
    width = int(round(art_w + PAD_X * 2))
    height = int(round(art_h + PAD_Y * 2 + CAPTION_H))

    base = Image.new("RGB", (width, height), C_BG)
    d = ImageDraw.Draw(base)
    d.rectangle([1, 1, width - 2, height - 2], outline=C_BORDER, width=2)

    spans = [run_spans(cv.ch[r], cv.cl[r]) for r in range(cv.rows)]
    for r, row in enumerate(spans):
        y = PAD_Y + r * line_h
        for col, text, cls in row:
            d.text((PAD_X + col * char_w, y), text, font=font, fill=CLASS_RGB[cls])

    # caption, tracked out to match the SVG
    cx = float(PAD_X)
    cy = height - PAD_Y - CAP_SIZE + 6
    for ch in art.CAPTION:
        d.text((cx, cy), ch, font=cap_font, fill=CLASS_RGB["m"])
        cx += cap_font.getlength(ch) + 1.1

    travel = cv.cols + BAND * 2
    frames = []
    for i in range(FRAMES):
        head = -BAND + travel * (i / float(FRAMES))
        frame = base.copy()
        fd = ImageDraw.Draw(frame)

        lo = max(0, int(head - BAND) - 1)
        hi = min(cv.cols, int(head + BAND) + 2)
        for c in range(lo, hi):
            falloff = 1.0 - abs(c - head) / BAND
            if falloff <= 0:
                continue
            x = PAD_X + c * char_w
            for r in range(cv.rows):
                ch = cv.ch[r][c]
                if ch == " ":
                    continue
                y = PAD_Y + r * line_h
                fd.rectangle([x, y, x + char_w, y + line_h], fill=C_BG)
                fd.text((x, y), ch,
                        font=font,
                        fill=blend(CLASS_RGB[cv.cl[r][c]], C_GLOW, falloff * 0.92))

        if 0 <= head <= cv.cols:
            hx = PAD_X + head * char_w
            fd.line([hx, PAD_Y - 8, hx, PAD_Y + art_h + 8],
                    fill=blend(C_BG, CLASS_RGB["a"], 0.85), width=2)
        frames.append(frame)

    # one shared palette, taken from a frame that already contains the glow
    pal = frames[FRAMES // 2].convert("P", palette=Image.ADAPTIVE, colors=128)
    out = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]

    out[0].save(OUT, save_all=True, append_images=out[1:], loop=0,
                duration=FRAME_MS, optimize=True, disposal=2)
    kb = os.path.getsize(OUT) / 1024.0
    print("wrote %s (%dx%d, %d frames, %.0f KB)"
          % (OUT, width, height, FRAMES, kb))


if __name__ == "__main__":
    main()
