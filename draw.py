#!/usr/bin/env python3
"""THE WORLD — news-image-20261125 rebuild #4.
Renders one 1024x1024 broadsheet PNG from stories.json (83 stories, 25 Nov 2026).
Fresh code, written from the rebuild brief only. No timestamps, no randomness:
two runs are byte-identical.
Usage: python3 draw.py [--out entry.png] [--boxes boxes.json] [--stats stats.json]
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976

PAPER = (247, 243, 234)
INK = (26, 26, 26)
MUTED = (96, 90, 78)
FAINT = (150, 143, 128)
RED = (178, 28, 28)
DARKRED = (140, 20, 20)
BLUE = (30, 58, 95)
GOLD = (176, 132, 28)
GREEN = (46, 110, 60)
RULE = (198, 190, 172)
OCEAN = (214, 228, 236)
LAND = (232, 224, 204)
LANDBORDER = (178, 166, 138)

FD = "/usr/share/fonts/truetype/dejavu"
SERIF_B = os.path.join(FD, "DejaVuSerif-Bold.ttf")
SERIF = os.path.join(FD, "DejaVuSerif.ttf")
SANS = os.path.join(FD, "DejaVuSans.ttf")
SANS_B = os.path.join(FD, "DejaVuSans-Bold.ttf")


def font(path, size):
    return ImageFont.truetype(path, int(round(size)))


def wrap_text(text, fnt, max_w):
    """Greedy word wrap; returns list of lines (never empty)."""
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, fnt, max_w, max_lines, min_size, path):
    """Shrink font until text fits in max_lines; returns (lines, font)."""
    size = fnt.size
    while size > min_size:
        f = font(path, size)
        lines = wrap_text(text, f, max_w)
        if len(lines) <= max_lines:
            return lines, f
        size -= 1
    f = font(path, min_size)
    return wrap_text(text, f, max_w)[:max_lines], f


class Recorder:
    """Collects every text box drawn, for the overlap audit."""

    def __init__(self):
        self.boxes = []

    def add(self, x0, y0, x1, y1, kind):
        self.boxes.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "kind": kind})

    def text(self, d, x, y, lines, fnt, fill, lh, kind, align="left", width=None):
        """Draw lines starting at (x, y); returns height used. Records one union box."""
        if not lines:
            return 0
        x0 = x
        x1 = x
        y0 = y
        for i, ln in enumerate(lines):
            w = fnt.getlength(ln)
            if align == "center" and width is not None:
                lx = x + (width - w) / 2
            elif align == "right" and width is not None:
                lx = x + width - w
            else:
                lx = x
            d.text((lx, y + i * lh), ln, font=fnt, fill=fill)
            x0 = min(x0, lx)
            x1 = max(x1, lx + w)
        y1 = y + len(lines) * lh - (lh - fnt.size) * 0.25
        self.add(int(x0), int(y0), int(x1) + 1, int(y1) + 1, kind)
        return len(lines) * lh


# ---------------------------------------------------------------- scenes
def _chip(d, rec, x, y, text, size=9):
    f = font(SANS_B, size)
    tw = f.getlength(text)
    pad = 5
    d.rounded_rectangle([x, y, x + tw + pad * 2, y + size + 8], radius=3, fill=RED)
    d.text((x + pad, y + 4), text, font=f, fill=(255, 255, 255))
    rec.add(int(x), int(y), int(x + tw + pad * 2) + 1, int(y + size + 8) + 1, "chip")


def _stars(d, x, y, w, h, n, color=(255, 255, 255)):
    pts = []
    for i in range(n):
        px = x + ((i * 37 + 11) % max(1, w - 6)) + 3
        py = y + ((i * 53 + 7) % max(1, h - 6)) + 3
        pts.append((px, py))
    for px, py in pts:
        d.ellipse([px - 1, py - 1, px + 1, py + 1], fill=color)


def scene_rocket(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 28, 56))
    _stars(d, x, y, w, h, 14)
    # moon
    d.ellipse([x + w - 34, y + h * 0.06, x + w - 12, y + h * 0.06 + 22],
              fill=(235, 230, 210))
    # rocket body (all fractions of h, safe at any size)
    bx = x + w // 2
    bw = max(8, w * 0.035)
    nose_t, nose_b = y + h * 0.10, y + h * 0.42
    body_b = y + h * 0.74
    d.polygon([(bx, nose_t), (bx - bw, nose_b), (bx + bw, nose_b)], fill=(220, 224, 230))
    d.rectangle([bx - bw, nose_b, bx + bw, body_b], fill=(240, 242, 245))
    d.rectangle([bx - bw, y + h * 0.50, bx - bw * 0.35, y + h * 0.60], fill=(30, 58, 95))
    d.polygon([(bx - bw, body_b), (bx - bw * 1.8, y + h * 0.88), (bx - bw, y + h * 0.80)],
              fill=(178, 28, 28))
    d.polygon([(bx + bw, body_b), (bx + bw * 1.8, y + h * 0.88), (bx + bw, y + h * 0.80)],
              fill=(178, 28, 28))
    d.polygon([(bx - bw * 0.55, body_b), (bx + bw * 0.55, body_b), (bx, y + h * 0.97)],
              fill=(255, 176, 32))
    d.rectangle([x, y + h * 0.96, x + w, y + h], fill=(60, 52, 40))


def scene_market(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(18, 46, 34))
    # candlesticks
    n = 7
    cw = w / (n + 1)
    vals = [0.25, 0.45, 0.35, 0.62, 0.55, 0.78, 0.92]
    for i, v in enumerate(vals):
        cx = x + cw * (i + 0.7)
        top = y + h - 12 - v * (h - 26)
        bot = y + h - 12 - v * (h - 26) + (h * 0.22 if i % 2 else h * 0.12)
        col = (46, 160, 90) if i % 2 == 0 else (220, 70, 60)
        d.line([cx, top - 6, cx, bot + 6], fill=col, width=2)
        d.rectangle([cx - 5, top, cx + 5, bot], fill=col)
    # trend line
    pts = [(x + 6, y + h - 18), (x + w * 0.3, y + h - 34), (x + w * 0.55, y + h - 26),
           (x + w * 0.8, y + h - 48), (x + w - 6, y + 14)]
    d.line(pts, fill=(255, 210, 90), width=3)
    d.rectangle([x, y + h - 3, x + w, y + h], fill=(10, 26, 20))


def scene_refinery(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 16, 28))
    # sky glow
    d.ellipse([x + w * 0.15, y + h * 0.1, x + w * 0.55, y + h * 0.7], fill=(120, 40, 24))
    d.ellipse([x + w * 0.55, y + h * 0.05, x + w * 0.95, y + h * 0.65], fill=(140, 52, 26))
    # towers
    for tx, th in ((0.22, 0.62), (0.52, 0.72), (0.78, 0.55)):
        px = x + w * tx
        d.rectangle([px - 9, y + h * (1 - th), px + 9, y + h - 10], fill=(40, 34, 44))
        d.rectangle([px - 13, y + h * (1 - th) - 4, px + 13, y + h * (1 - th)], fill=(52, 44, 54))
        # flame (fractions of h)
        base = y + h * (1 - th) - 4
        d.polygon([(px - 6, base), (px + 6, base), (px, base - h * 0.18)],
                  fill=(255, 176, 32))
        d.polygon([(px - 3, base), (px + 3, base), (px, base - h * 0.10)],
                  fill=(255, 230, 120))
    # smoke
    for sx, sy, r in ((0.3, 0.24, 0.10), (0.6, 0.18, 0.12), (0.85, 0.26, 0.09)):
        rr = h * r
        d.ellipse([x + w * sx - rr, y + h * sy - rr, x + w * sx + rr, y + h * sy + rr],
                  fill=(90, 82, 88))
    d.rectangle([x, y + h - 10, x + w, y + h], fill=(12, 10, 14))


def scene_pact(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 58, 95))
    # left flag: Australia blue + stars
    d.rectangle([x, y, x + w // 2, y + h], fill=(18, 42, 86))
    _stars(d, x + 4, y + 4, w // 2 - 8, h - 8, 6)
    # right flag: Solomon green/yellow diagonal
    d.rectangle([x + w // 2, y, x + w, y + h], fill=(20, 90, 50))
    d.polygon([(x + w // 2, y + h), (x + w, y), (x + w, y + h * 0.25),
               (x + w // 2 + 14, y + h)], fill=(240, 200, 40))
    d.line([x + w // 2, y, x + w // 2, y + h], fill=(255, 255, 255), width=2)


def scene_femicide(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(74, 22, 30))
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) * 0.42
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(247, 243, 234))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(26, 26, 26), width=2)
    d.line([cx, cy, cx, cy - r + r * 0.3], fill=(26, 26, 26), width=3)
    d.line([cx, cy, cx + r - r * 0.45, cy + r * 0.2], fill=(26, 26, 26), width=3)
    f = font(SANS_B, max(10, int(h * 0.42)))
    d.text((cx, cy - r * 0.45), "5", font=f, fill=(178, 28, 28), anchor="mm")


def scene_dell(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(22, 30, 38))
    for i in range(3):
        rx = x + 8 + i * (w - 16) // 3
        rw = (w - 16) // 3 - 6
        d.rectangle([rx, y + h * 0.08, rx + rw, y + h * 0.92], fill=(44, 58, 70),
                    outline=(120, 140, 160), width=1)
        for j in range(4):
            ly = y + h * (0.18 + j * 0.2)
            col = (70, 220, 120) if (i + j) % 3 else (255, 200, 60)
            d.ellipse([rx + 5, ly, rx + 11, ly + 5], fill=col)
            d.rectangle([rx + 15, ly + 1, rx + rw - 5, ly + 5], fill=(90, 110, 130))


def scene_senate(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 224, 204))
    # dome
    cx = x + w // 2
    d.pieslice([cx - w * 0.16, y + h * 0.06, cx + w * 0.16, y + h * 0.52], 180, 360,
               fill=(30, 58, 95))
    d.rectangle([cx - w * 0.17, y + h * 0.30, cx + w * 0.17, y + h * 0.36],
                fill=(30, 58, 95))
    for i in range(5):
        px = x + 14 + i * ((w - 28) // 4)
        d.rectangle([px - 3, y + h * 0.36, px + 3, y + h * 0.72], fill=(120, 110, 90))
    d.rectangle([x + 10, y + h * 0.72, x + w - 10, y + h * 0.78], fill=(120, 110, 90))
    # tally bars
    d.rectangle([x + 10, y + h * 0.84, x + 10 + (w - 20) * 0.61, y + h * 0.95],
                fill=(30, 58, 95))
    d.rectangle([x + 10 + (w - 20) * 0.61, y + h * 0.84, x + w - 10, y + h * 0.95],
                fill=(178, 28, 28))


def scene_lula(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 120, 60))
    d.polygon([(x + w // 2, y + 6), (x + w - 8, y + h // 2), (x + w // 2, y + h - 6),
               (x + 8, y + h // 2)], fill=(255, 210, 40))
    d.ellipse([x + w // 2 - 14, y + h // 2 - 14, x + w // 2 + 14, y + h // 2 + 14],
              fill=(20, 50, 140))
    d.arc([x + w // 2 - 14, y + h // 2 - 14, x + w // 2 + 14, y + h // 2 + 14],
          200, 340, fill=(255, 255, 255), width=2)


def scene_eu(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 42, 110))
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 10
    for i in range(12):
        a = 3.14159 * 2 * i / 12 - 3.14159 / 2
        px = cx + r * 0.82 * _cos(a)
        py = cy + r * 0.82 * _sin(a)
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 214, 64))


def _cos(a):
    import math
    return math.cos(a)


def _sin(a):
    import math
    return math.sin(a)


def scene_gaza(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(196, 178, 140))
    # buildings
    for bx, bw, bh in ((0.06, 0.2, 0.5), (0.3, 0.16, 0.65), (0.5, 0.22, 0.45), (0.74, 0.18, 0.6)):
        d.rectangle([x + w * bx, y + h * (1 - bh), x + w * (bx + bw), y + h - 8],
                    fill=(120, 104, 78))
    # smoke columns (fractions, stay inside the box)
    for sx, sh in ((0.36, 0.5), (0.62, 0.62), (0.84, 0.45)):
        px = x + w * sx
        for j in range(3):
            r = h * (0.10 + j * 0.03)
            scy = y + h * 0.30 - j * h * 0.13
            d.ellipse([px - r, scy - r, px + r, scy + r], fill=(90, 84, 80))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(90, 78, 58))


def scene_nba(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 60, 20))
    # court floor
    d.rectangle([x, y + h * 0.55, x + w, y + h], fill=(200, 130, 60))
    d.line([x, y + h * 0.55, x + w, y + h * 0.55], fill=(255, 255, 255), width=2)
    cx, cy = x + w // 2, y + h // 2 - 4
    r = min(w, h) // 2 - 8
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(235, 110, 30),
              outline=(120, 50, 10), width=2)
    d.line([cx - r, cy, cx + r, cy], fill=(120, 50, 10), width=2)
    d.arc([cx - r, cy - r, cx + r, cy + r], 300, 60, fill=(120, 50, 10), width=2)
    d.arc([cx - r, cy - r, cx + r, cy + r], 120, 240, fill=(120, 50, 10), width=2)


def scene_cartagena(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(58, 96, 140))
    # supermarket block
    d.rectangle([x + 8, y + h * 0.34, x + w - 8, y + h - 8], fill=(240, 236, 224))
    # striped awning
    for i in range(6):
        col = (178, 28, 28) if i % 2 == 0 else (247, 243, 234)
        ax = x + 8 + i * ((w - 16) // 6)
        d.rectangle([ax, y + h * 0.34, ax + (w - 16) // 6, y + h * 0.34 + 10], fill=col)
    # door + windows
    d.rectangle([x + w // 2 - 9, y + h - 30, x + w // 2 + 9, y + h - 8], fill=(40, 60, 90))
    d.rectangle([x + 16, y + h * 0.55, x + 34, y + h * 0.55 + 12], fill=(140, 180, 210))
    d.rectangle([x + w - 34, y + h * 0.55, x + w - 16, y + h * 0.55 + 12], fill=(140, 180, 210))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(30, 50, 74))


def scene_senegal(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(10, 90, 50))
    # stripes
    d.rectangle([x, y, x + w, y + 8], fill=(0, 130, 70))
    d.rectangle([x, y + 8, x + w, y + 16], fill=(255, 210, 40))
    d.rectangle([x, y + 16, x + w, y + 24], fill=(200, 40, 40))
    # stars in the field first, trophy on top
    _stars(d, x + 6, y + int(h * 0.30), w - 12, int(h * 0.60), 8, color=(255, 230, 120))
    # trophy cup (fractions of h)
    cx = x + w // 2
    cy = y + h // 2 + h * 0.06
    cw = w * 0.085
    d.polygon([(cx - cw, cy - h * 0.20), (cx + cw, cy - h * 0.20),
               (cx + cw * 0.62, cy + h * 0.02), (cx - cw * 0.62, cy + h * 0.02)],
              fill=(255, 205, 60), outline=(150, 105, 20))
    d.arc([cx - cw * 1.5, cy - h * 0.22, cx - cw * 0.5, cy + h * 0.02], 90, 270,
          fill=(255, 205, 60), width=4)
    d.arc([cx + cw * 0.5, cy - h * 0.22, cx + cw * 1.5, cy + h * 0.02], 270, 90,
          fill=(255, 205, 60), width=4)
    d.rectangle([cx - 3, cy + h * 0.02, cx + 3, cy + h * 0.13], fill=(255, 205, 60))
    d.rectangle([cx - cw * 0.75, cy + h * 0.13, cx + cw * 0.75, cy + h * 0.19],
                fill=(255, 205, 60))


SCENES = {
    "rocket": scene_rocket, "market": scene_market, "refinery": scene_refinery,
    "pact": scene_pact, "femicide": scene_femicide, "dell": scene_dell,
    "senate": scene_senate, "lula": scene_lula, "eu": scene_eu, "gaza": scene_gaza,
    "nba": scene_nba, "cartagena": scene_cartagena, "senegal": scene_senegal,
}
HERO_SCENE = {1: "rocket", 2: "market", 4: "refinery"}
MINI_SCENE = {5: "pact", 6: "femicide", 7: "dell", 8: "senate", 9: "lula", 10: "eu",
              11: "gaza", 12: "nba", 31: "cartagena", 32: "senegal"}

# ---------------------------------------------------------------- map
# Rough continent outlines (own approximations, equirectangular lon/lat).
LAND_POLYS = [
    # North America
    [(-168, 66), (-156, 58), (-140, 60), (-135, 58), (-125, 49), (-124, 42), (-120, 34),
     (-114, 29), (-108, 24), (-97, 16), (-92, 14), (-83, 9), (-79, 9), (-82, 15), (-87, 21),
     (-90, 21), (-87, 26), (-84, 30), (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 45),
     (-65, 44), (-60, 47), (-65, 50), (-55, 52), (-60, 55), (-65, 60), (-68, 58), (-78, 62),
     (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71),
     (-165, 68), (-168, 66)],
    # Greenland
    [(-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70), (-25, 76), (-35, 78), (-55, 76),
     (-58, 70), (-55, 64), (-52, 60)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-70, -18), (-70, -23),
     (-70, -30), (-72, -37), (-73, -44), (-74, -50), (-70, -54), (-66, -55), (-65, -47),
     (-62, -41), (-58, -34), (-52, -32), (-48, -28), (-41, -23), (-39, -17), (-35, -9),
     (-35, -6), (-40, -3), (-44, -2), (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-70, 11),
     (-75, 11), (-79, 9)],
    # Africa
    [(-17, 15), (-16, 21), (-15, 27), (-10, 31), (-6, 35), (0, 36), (10, 37), (20, 32),
     (30, 31), (32, 31), (35, 28), (37, 22), (39, 18), (43, 12), (48, 11), (51, 12),
     (48, 5), (42, -1), (40, -10), (36, -18), (33, -26), (28, -33), (20, -35), (17, -32),
     (15, -27), (12, -18), (13, -12), (9, -4), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12),
     (-17, 15)],
    # Europe
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-2, 48), (0, 50), (2, 51), (4, 53), (7, 55),
     (8, 57), (10, 59), (13, 56), (18, 56), (21, 55), (24, 58), (24, 60), (28, 61),
     (30, 62), (28, 65), (25, 67), (22, 70), (18, 69), (14, 67), (12, 64), (10, 62),
     (5, 60), (5, 58), (0, 57), (-3, 55), (-5, 50), (-5, 48), (-2, 47), (-2, 44),
     (-9, 43), (-10, 38), (-10, 36)],
    # Asia
    [(30, 36), (36, 36), (40, 38), (44, 39), (48, 30), (50, 29), (54, 27), (57, 26),
     (60, 25), (62, 25), (66, 25), (68, 23), (72, 21), (76, 10), (77, 8), (80, 7),
     (80, 13), (84, 19), (88, 22), (91, 22), (93, 17), (95, 16), (98, 10), (100, 8),
     (101, 6), (104, 2), (104, 9), (106, 11), (109, 13), (109, 19), (107, 21), (110, 21),
     (114, 22), (118, 25), (121, 28), (122, 32), (120, 35), (122, 38), (124, 40), (127, 40),
     (130, 42), (132, 43), (135, 44), (138, 46), (141, 50), (142, 54), (141, 59), (144, 60),
     (150, 60), (156, 59), (158, 53), (162, 56), (163, 60), (170, 60), (170, 66), (178, 65),
     (178, 69), (170, 70), (160, 70), (150, 72), (140, 73), (130, 72), (120, 73), (110, 74),
     (100, 77), (90, 75), (80, 73), (70, 72), (60, 70), (50, 69), (45, 68), (40, 67),
     (35, 66), (32, 64), (30, 62), (30, 58), (28, 60), (28, 62), (30, 64), (30, 60),
     (28, 55), (30, 50), (28, 46), (28, 44), (30, 42), (30, 38), (30, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33), (129, -32), (132, -32),
     (136, -35), (140, -38), (145, -38), (150, -37), (153, -27), (153, -24), (150, -22),
     (146, -19), (142, -11), (142, -15), (136, -12), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20), (113, -22)],
    # Japan
    [(130, 31), (131, 33), (133, 34), (135, 34), (137, 35), (139, 35), (140, 38),
     (141, 41), (142, 44), (144, 44), (143, 42), (141, 39), (140, 36), (137, 34),
     (134, 34), (132, 33), (130, 31)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51), (-1, 50), (-5, 50)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -25), (44, -25), (43, -20), (44, -16)],
    # New Zealand
    [(167, -45), (170, -42), (173, -41), (175, -38), (178, -38), (176, -40), (173, -42),
     (170, -44), (167, -46), (167, -45)],
]


def draw_map(d, rec, x, y, w, h, pins):
    """World map with pins; returns (dots, labels_drawn)."""
    d.rectangle([x, y, x + w, y + h], fill=OCEAN)
    lon0, lon1, lat0, lat1 = -180, 180, -58, 82

    def proj(lon, lat):
        px = x + (lon - lon0) / (lon1 - lon0) * w
        py = y + (lat1 - lat) / (lat1 - lat0) * h
        return px, py

    # graticule
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, 0)
        d.line([px, y, px, y + h], fill=(200, 214, 222), width=1)
    for lat in range(-30, 81, 30):
        _, py = proj(0, lat)
        d.line([x, py, x + w, py], fill=(200, 214, 222), width=1)
    # land
    for poly in LAND_POLYS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LANDBORDER)
    # pins
    lf = font(SANS_B, 7.5)
    dots = []
    placed = []  # label boxes
    labels_drawn = 0
    for num, lon, lat, label in pins:
        px, py = proj(lon, lat)
        dots.append((px, py, num))
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED, outline=(255, 255, 255), width=1)
    for num, lon, lat, label in pins:
        px, py = proj(lon, lat)
        tw = lf.getlength(label)
        cands = [
            (px + 5, py - 11), (px - tw - 5, py - 11),
            (px + 5, py + 3), (px - tw - 5, py + 3),
            (px + 5, py - 20), (px - tw - 5, py - 20),
            (px + 5, py + 12), (px - tw - 5, py + 12),
        ]
        for lx, ly in cands:
            box = (lx - 1, ly - 1, lx + tw + 1, ly + 9)
            if box[0] < x or box[2] > x + w or box[1] < y or box[3] > y + h:
                continue
            clash = False
            for (ox0, oy0, ox1, oy1) in placed:
                if not (box[2] <= ox0 or box[0] >= ox1 or box[3] <= oy0 or box[1] >= oy1):
                    clash = True
                    break
            if clash:
                continue
            for (dx, dy, dn) in dots:
                if dn == num:
                    continue
                if abs(dx - (lx + tw / 2)) < 4 and abs(dy - (ly + 4)) < 5:
                    clash = True
                    break
            if clash:
                continue
            d.text((lx, ly), label, font=lf, fill=INK)
            rec.add(int(box[0]), int(box[1]), int(box[2]), int(box[3]), "maplabel")
            placed.append(box)
            labels_drawn += 1
            break
    return len(dots), labels_drawn


# ---------------------------------------------------------------- layout
PRESETS = [
    # brief_font, brief_lh, hero_h, mini_row_h, map_h, wordmark, date_px, deck_px
    (8.5, 11.0, 124, 80, 104, 52, 28, 11),
    (8.5, 11.0, 122, 78, 100, 52, 28, 11),
    (8.0, 10.5, 114, 72, 90, 50, 26, 11),
    (8.0, 10.5, 112, 72, 88, 50, 24, 10),
    (7.5, 10.0, 110, 70, 86, 48, 22, 10),
]


def brief_columns(data, bf, lh, col_w):
    """Wrap all brief items into 4 columns; returns (columns, max_height).
    Source is appended to the text before wrapping (no extra line)."""
    items = data["also_on"]
    per = (len(items) + 4) // 5
    cols = [items[i * per:(i + 1) * per] for i in range(5)]
    num_f = font(SANS_B, bf)
    txt_f = font(SANS, bf)
    col_heights = []
    laid = []
    for col in cols:
        y = 0
        col_items = []
        for entry in col:
            num, text, region, src = entry[0], entry[1], entry[2], entry[3]
            num_s = str(num) + ". "
            nw = num_f.getlength(num_s)
            full = text + " · " + src
            lines = wrap_text(full, txt_f, col_w - nw - 2)
            item_h = len(lines) * lh
            col_items.append((num_s, lines))
            y += item_h + 3
        col_heights.append(y - 3 if col else 0)
        laid.append(col_items)
    return laid, max(col_heights) if col_heights else 0, num_f, txt_f, None


def total_height(data, preset):
    """Mirror of render()'s y-advance; exact, incl. wrapped datecheck/footer."""
    bf, lh, hero_h, mini_h, map_h, wm, dt, dk = preset
    h = 8
    h += 12 + 4        # kicker + rule gap
    h += wm + dt + dk + 22  # masthead (3 lines + rule + gap)
    h += 4
    h += hero_h        # heroes
    h += 4
    h += 48            # numbers strip
    h += 4
    h += mini_h * 2 + 8  # minis
    h += 4
    h += 14 + map_h    # map title + map
    h += 4
    h += 16            # brief header
    _, bh, _, _, _ = brief_columns(data, bf, lh, (CW - 48) / 5)
    h += bh
    h += 4
    dcf = font(SANS, 9)
    half = (CW - 16) / 2
    l1 = wrap_text(data["date_check_left"], dcf, half)
    l2 = wrap_text(data["date_check_right"], dcf, half)
    h += 4 + max(len(l1), len(l2)) * 11 + 4  # date check
    h += 21            # ticker
    ff = font(SANS, 9)
    fl = wrap_text(data["footer_sources"], ff, CW)
    hf2 = font(SANS, 8)
    hs = wrap_text(data["how_sure"], hf2, CW)
    h += 11 + len(fl) * 11 + 2 + len(hs) * 10  # footer
    return h


def render(data, preset, boxes_path):
    bf, lh, hero_h, mini_h, map_h, wm, dt, dk = preset
    rec = Recorder()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    total = len(data["heroes"]) + 1 + len(data["minis"]) + len(data["also_on"])
    y = 8
    # kicker
    kf = font(SANS_B, 10)
    kicker = data["kicker"].replace("{N}", str(total))
    rec.text(d, MARGIN, y, [kicker], kf, MUTED, 12, "kicker", align="center", width=CW)
    y += 12
    d.line([MARGIN, y, MARGIN + CW, y], fill=INK, width=2)
    y += 4
    # masthead
    wf = font(SERIF_B, wm)
    rec.text(d, MARGIN, y, [data["masthead"]], wf, INK, wm + 4, "masthead",
             align="center", width=CW)
    y += wm + 6
    df = font(SANS_B, dt)
    rec.text(d, MARGIN, y, [data["date"]], df, INK, dt + 4, "masthead-date",
             align="center", width=CW)
    y += dt + 6
    dkf = font(SANS, dk)
    rec.text(d, MARGIN, y, [data["deck"]], dkf, MUTED, dk + 4, "masthead-deck",
             align="center", width=CW)
    y += dk + 6
    d.line([MARGIN, y, MARGIN + CW, y], fill=INK, width=1)
    y += 4
    # heroes (measure text first, art fills the rest)
    col_w = (CW - 22) / 3
    hf = font(SERIF_B, 17)
    df2 = font(SANS, 11)
    sf = font(SANS, 9)
    cells = []
    for hero in data["heroes"]:
        lines, _hf = fit_lines(hero["headline"], hf, col_w, 2, 14, SERIF_B)
        dlines = wrap_text(hero["deck"], df2, col_w)[:2]
        art_h = hero_h - (4 + len(lines) * 20 + len(dlines) * 13 + 11)
        cells.append((hero, lines, dlines, art_h))
    for i, (hero, lines, dlines, art_h) in enumerate(cells):
        hx = MARGIN + i * (col_w + 11)
        SCENES[HERO_SCENE[hero["num"]]](d, hx, y, col_w, art_h)
        _chip(d, rec, hx + 4, y + 4, hero["banner"], size=9)
        hy = y + art_h + 4
        hy += rec.text(d, hx, hy, lines, hf, INK, 20, "hero-head")
        hy += rec.text(d, hx, hy, dlines, df2, MUTED, 13, "hero-deck")
        src = hero["place"] + " · " + hero["source"] + " · " + hero["tag"]
        hy += rec.text(d, hx, hy, [src], sf, FAINT, 11, "hero-src")
    y += hero_h
    y += 4
    # (timeline line dropped in v4 — its facts live in the numbers strip)
    # numbers strip
    d.line([MARGIN, y, MARGIN + CW, y], fill=RULE, width=1)
    y += 4
    ncell = CW / 6
    for i, (val, lab) in enumerate(data["numbers"]):
        nx = MARGIN + i * ncell
        vf = font(SANS_B, 19)
        rec.text(d, nx, y, [val], vf, RED, 22, "number", align="center", width=ncell)
        lf2 = font(SANS, 9)
        ll = wrap_text(lab, lf2, ncell - 8)[:2]
        rec.text(d, nx + 4, y + 22, ll, lf2, MUTED, 11, "number-label",
                 align="center", width=ncell - 8)
        if i:
            d.line([nx, y, nx, y + 36], fill=RULE, width=1)
    y += 44
    y += 4
    # minis: 2 rows x 5
    mcol = (CW - 36) / 5
    art_m = mini_h - 38
    for r in range(2):
        for c in range(5):
            idx = r * 5 + c
            if idx >= len(data["minis"]):
                continue
            mini = data["minis"][idx]
            mx = MARGIN + c * (mcol + 9)
            my = y + r * (mini_h + 8)
            SCENES[MINI_SCENE[mini["num"]]](d, mx, my, mcol, art_m)
            _chip(d, rec, mx + 3, my + 3, mini["banner"], size=8)
            mhy = my + art_m + 3
            mhf = font(SANS_B, 11)
            mlines, mhf = fit_lines(mini["headline"], mhf, mcol, 1, 9, SANS_B)
            mhy += rec.text(d, mx, mhy, mlines, mhf, INK, 13, "mini-head")
            mdf = font(SANS, 9)
            md = wrap_text(mini["deck"], mdf, mcol)[:2]
            mhy += rec.text(d, mx, mhy, md, mdf, MUTED, 11, "mini-deck")
    y += mini_h * 2 + 8
    y += 4
    # map
    mf = font(SANS_B, 11)
    map_title = "WHERE IT HAPPENED — %d PINNED STORIES" % len(data["pins"])
    rec.text(d, MARGIN, y, [map_title], mf, INK, 13, "map-title")
    y += 14
    dots, labels = draw_map(d, rec, MARGIN, y, CW, map_h, data["pins"])
    y += map_h
    y += 4
    # brief header
    bfnt = font(SANS_B, 12)
    brief_title = "THE DAY IN BRIEF — %d STORIES, NUMBERED" % len(data["also_on"])
    rec.text(d, MARGIN, y, [brief_title], bfnt, INK, 14, "brief-head")
    y += 16
    # brief columns (5 columns, source inline in the wrapped text)
    col_w = (CW - 48) / 5
    laid, bh, num_f, txt_f, _ = brief_columns(data, bf, lh, col_w)
    for ci, col_items in enumerate(laid):
        cx = MARGIN + ci * (col_w + 12)
        cy = y
        for num_s, lines in col_items:
            nw = num_f.getlength(num_s)
            item_y = cy
            d.text((cx, item_y), num_s, font=num_f, fill=RED)
            for li, ln in enumerate(lines):
                d.text((cx + nw, item_y + li * lh), ln, font=txt_f, fill=INK)
            box_h = len(lines) * lh
            rec.add(int(cx), int(item_y), int(cx + col_w) + 1, int(item_y + box_h) + 1,
                    "brief")
            cy += box_h + 3
    y += bh
    y += 4
    # date check: two columns
    d.line([MARGIN, y, MARGIN + CW, y], fill=RULE, width=1)
    y += 4
    dcf = font(SANS, 9)
    half = (CW - 16) / 2
    l1 = wrap_text(data["date_check_left"], dcf, half)
    l2 = wrap_text(data["date_check_right"], dcf, half)
    rows = max(len(l1), len(l2))
    rec.text(d, MARGIN, y, l1, dcf, MUTED, 11, "datecheck")
    rec.text(d, MARGIN + half + 16, y, l2, dcf, MUTED, 11, "datecheck")
    y += rows * 11
    y += 4
    # ticker
    d.line([MARGIN, y, MARGIN + CW, y], fill=RULE, width=1)
    y += 3
    tkf = font(SANS_B, 10)
    rec.text(d, MARGIN, y, [data["ticker"]], tkf, BLUE, 12, "ticker",
             align="center", width=CW)
    y += 14
    y += 4
    # footer
    ff = font(SANS_B, 9)
    rec.text(d, MARGIN, y, [data["footer_bold"]], ff, INK, 11, "footer",
             align="center", width=CW)
    y += 11
    fsf = font(SANS, 9)
    fl = wrap_text(data["footer_sources"], fsf, CW)
    rec.text(d, MARGIN, y, fl, fsf, MUTED, 11, "footer", align="center", width=CW)
    y += len(fl) * 11
    # how sure line
    hf2 = font(SANS, 8)
    hs = wrap_text(data["how_sure"], hf2, CW)
    rec.text(d, MARGIN, y + 2, hs, hf2, FAINT, 10, "footer", align="center", width=CW)
    y += 2 + len(hs) * 10
    stats = {"stories": total, "pins": len(data["pins"]), "dots": dots,
             "labels_drawn": labels, "brief_font": bf, "preset": list(preset),
             "content_bottom": y}
    with open(boxes_path, "w") as f:
        json.dump(rec.boxes, f)
    return img, stats, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--boxes", default=None)
    ap.add_argument("--stats", default=None)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    out = args.out or os.path.join(here, "entry.png")
    boxes = args.boxes or os.path.join(here, "boxes.json")
    stats_path = args.stats or os.path.join(here, "stats.json")
    with open(os.path.join(here, "stories.json")) as f:
        data = json.load(f)
    chosen = None
    for preset in PRESETS:
        trial = "/tmp/news25-trial-boxes.json"
        _img, _stats, bottom = render(data, preset, trial)
        print("trial preset", preset, "bottom", bottom,
              "total_height", total_height(data, preset))
        if bottom <= 1016:
            chosen = preset
            break
    if chosen is None:
        chosen = PRESETS[-1]
    img, stats, bottom = render(data, chosen, boxes)
    img.save(out)
    stats["total_height_check"] = total_height(data, chosen)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=1)
    print("preset", chosen, "bottom", bottom, "stories", stats["stories"],
          "pins", stats["pins"], "dots", stats["dots"], "labels", stats["labels_drawn"])


if __name__ == "__main__":
    main()
# v4 final: 83 stories, 48 pins / 35 labels drawn, verify 20/20, bottom 1016.
