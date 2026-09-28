"""Costumes (SVG) and sounds (synthesized WAV) for both styles: classic and nyan."""
import io
import math
import pathlib
import random
import struct
import wave

import aseprite

STYLES = ("classic", "nyan")


# =============================== SVG helpers ===============================

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{body}</svg>')


def text(x, y, s, size, fill="#fff", anchor="middle", extra=""):
    s = s.replace("&", "&amp;")
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Pixel" font-size="{size}" '
            f'fill="{fill}" {extra}>{s}</text>')


def pixels(grid, palette, px, ox=0, oy=0):
    """Render a list of strings (one char per pixel, '.' = empty) as merged <rect> runs."""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            c = row[x]
            if c == ".":
                x += 1
                continue
            run = x
            while run < len(row) and row[run] == c:
                run += 1
            out.append(f'<rect x="{ox + x * px:g}" y="{oy + y * px:g}" width="{(run - x) * px:g}" '
                       f'height="{px:g}" fill="{palette[c]}"/>')
            x = run
    return "".join(out)


RAINBOW = ["#ff0000", "#ff9900", "#ffff00", "#33ff00", "#0099ff", "#6633ff"]


# =============================== Nyan cat pixel art ===============================

CAT_PALETTE = {"K": "#000", "T": "#ffcc99", "P": "#ff99ff", "S": "#ff3399", "G": "#999999",
               "W": "#fff", "R": "#ff9999"}


def cat_grid(frame):
    """34x22 Pop-Tart cat facing right; frame 2 shifts legs/tail for the run cycle."""
    w, h = 34, 22
    g = [["."] * w for _ in range(h)]

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = c

    def orect(x0, y0, x1, y1, c):
        rect(x0, y0, x1, y1, "K")
        rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, c)

    step = frame - 1
    orect(0, 9 + step, 5, 12 + step, "G")                       # tail
    for lx in (5, 10, 17, 24):                                  # legs
        orect(lx + step, 17, lx + 3 + step, 21, "G")
    orect(4, 0, 24, 16, "T")                                    # toast crust
    for x, y in ((4, 0), (24, 0), (4, 16), (24, 16)):
        g[y][x] = "."
    rect(6, 2, 22, 14, "P")                                     # frosting
    for x, y in ((6, 2), (22, 2), (6, 14), (22, 14)):
        g[y][x] = "T"
    for x, y in ((9, 4), (13, 3), (18, 5), (8, 9), (12, 7), (16, 10), (20, 8), (10, 12), (15, 13), (19, 12)):
        g[y][x] = "S"                                           # sprinkles
    orect(20, 5, 23, 9, "G")                                    # ears
    orect(29, 5, 32, 9, "G")
    orect(19, 8, 33, 19, "G")                                   # head
    for x in (21, 22, 30, 31):
        g[8][x] = "G"
    g[19][19] = g[19][33] = "."
    rect(22, 11, 23, 12, "K"); g[11][22] = "W"                  # eyes
    rect(29, 11, 30, 12, "K"); g[11][29] = "W"
    g[13][26] = "K"                                             # nose + "w" mouth
    for x in (24, 26, 28):
        g[15][x] = "K"
    for x in (25, 27):
        g[16][x] = "K"
    rect(20, 14, 21, 15, "R"); rect(31, 14, 32, 15, "R")        # cheeks
    return ["".join(r) for r in g]


def cat_head_grid():
    return [
        ".KK......KK.",
        "KGGK....KGGK",
        "KGGGKKKKGGGK",
        "KGGGGGGGGGGK",
        "KGKWGGGGKWGK",
        "KGKKGGGGKKGK",
        "KRGGGKGGGGRK",
        "KGGKGKGKGGGK",
        ".KGGGGGGGGK.",
        "..KKKKKKKK..",
    ]


# =============================== costume builders ===============================

def classic_rock(seed):
    rnd = random.Random(seed)
    pts = []
    for i in range(11):
        a = math.radians(i * 360 / 11 + rnd.uniform(-10, 10))
        r = rnd.uniform(30, 43)
        pts.append(f"{45 + r * math.cos(a):.1f},{45 + r * math.sin(a):.1f}")
    return svg(90, 90, f'<polygon points="{" ".join(pts)}" fill="#000" stroke="#fff" '
                       f'stroke-width="2.5" stroke-linejoin="round"/>')


ART_DIR = pathlib.Path(__file__).with_name("art")


def pixel_art(filename, px):
    """Hand-drawn .aseprite sprite -> crisp vector costume (one rect per horizontal run of equal pixels).
    Returns (svg, rotation center x, rotation center y)."""
    w, h, grid = aseprite.read_rgba(ART_DIR / filename)
    rects = []
    for y, row in enumerate(grid):
        x = 0
        while x < w:
            r, g, b, a = row[x]
            run = x + 1
            while run < w and row[run] == row[x]:
                run += 1
            if a:
                opacity = f' fill-opacity="{a / 255:.3f}"' if a < 255 else ""
                rects.append(f'<rect x="{x * px:g}" y="{y * px:g}" width="{(run - x) * px:g}" height="{px:g}" '
                             f'fill="#{r:02x}{g:02x}{b:02x}"{opacity}/>')
            x = run
    return svg(round(w * px, 2), round(h * px, 2), "".join(rects)), w * px / 2, h * px / 2


def classic_ship(flame):
    fire = ('<polyline points="7,8 0,12 7,16" fill="none" stroke="#fff" stroke-width="1.5"/>' if flame else "")
    return svg(34, 24, '<polygon points="32,12 4,2 9,12 4,22" fill="#000" stroke="#fff" '
                       f'stroke-width="2" stroke-linejoin="round"/>{fire}')


def classic_ufo():
    return svg(64, 26, '<polygon points="2,16 14,10 50,10 62,16 50,23 14,23" fill="#000" stroke="#fff" '
                       'stroke-width="2" stroke-linejoin="round"/>'
                       '<polygon points="22,10 26,3 38,3 42,10" fill="#000" stroke="#fff" stroke-width="2"/>'
                       '<line x1="2" y1="16" x2="62" y2="16" stroke="#fff" stroke-width="2"/>')


def star(size, fill, stroke):
    c, pts = size / 2, []
    for i in range(10):
        r = c - 1 if i % 2 == 0 else c * 0.45
        a = math.radians(-90 + i * 36)
        pts.append(f"{c + r * math.cos(a):.2f},{c + r * math.sin(a):.2f}")
    return svg(size, size, f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')


def heart():
    return svg(10, 9, '<path d="M5,8.5 L1,4.5 A2.3,2.3 0 0 1 5,1.8 A2.3,2.3 0 0 1 9,4.5 Z" fill="#ff5fa2"/>')


def bone():
    return svg(14, 7, '<rect x="3" y="2" width="8" height="3" fill="#fff5e1"/>'
                      '<circle cx="3" cy="2" r="2" fill="#fff5e1"/><circle cx="3" cy="5" r="2" fill="#fff5e1"/>'
                      '<circle cx="11" cy="2" r="2" fill="#fff5e1"/><circle cx="11" cy="5" r="2" fill="#fff5e1"/>')


def rainbow_segment():
    return svg(10, 18, "".join(f'<rect x="0" y="{i * 3}" width="10" height="3" fill="{c}"/>'
                               for i, c in enumerate(RAINBOW)))


def space(style):
    if style == "classic":
        return svg(480, 360, '<rect width="480" height="360" fill="#000"/>')
    stars = "".join(f'<rect x="{(i * 97) % 480}" y="{(i * 57 + 23) % 360}" width="{2 + i % 2 * 2}" '
                    f'height="{2 + i % 2 * 2}" fill="#fff"/>' for i in range(30))
    return svg(480, 360, f'<rect width="480" height="360" fill="#0f3d73"/>{stars}')


def title(style):
    sub = text(210, 132, "BY DANIEL GODRI NETO", 14, "#aaa")
    if style == "classic":
        return svg(420, 140, text(210, 90, "ASTEROIDS", 60) + sub)
    grad = ('<defs><linearGradient id="rb" x1="0" x2="1">'
            + "".join(f'<stop offset="{i / 5:.2f}" stop-color="{c}"/>' for i, c in enumerate(RAINBOW))
            + "</linearGradient></defs>")
    trail = "".join(f'<rect x="0" y="{8 + i * 4}" width="118" height="4" fill="{c}"/>' for i, c in enumerate(RAINBOW))
    cat = pixels(cat_grid(1), CAT_PALETTE, 1.3, ox=112, oy=0)
    outline = 'stroke="#1a0033" stroke-width="2" paint-order="stroke"'  # stays readable over yarn balls
    return svg(420, 140, grad + trail + cat + text(290, 34, "NYAN", 34, "#ff99ff", extra=outline)
               + text(210, 100, "ASTEROIDS", 52, "url(#rb)", extra=outline) + sub)


def button(label):
    return svg(220, 30, '<rect x="1" y="1" width="218" height="28" rx="4" fill="#111a2e" stroke="#fff" '
                        f'stroke-width="2"/>{text(110, 21, label, 16)}')


def lines_panel(lines, boxes):
    """480x360 panel; each line is (y, text, size, color). Boxes (x, y, w, h) darken what drifts behind the text."""
    backing = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#000" fill-opacity="0.6"/>'
                      for x, y, w, h in boxes)
    return svg(480, 360, backing + "".join(text(240, y, s, size, color) for y, s, size, color in lines))


CONTROL_HELP = {
    "arrows": ("TURN: LEFT / RIGHT     THRUST: UP", "FIRE: SPACE     HYPERSPACE: DOWN"),
    "wasd": ("TURN: A / D     THRUST: W", "FIRE: SPACE     HYPERSPACE: S"),
}

BUTTON_LABELS = {
    "play": "PLAY", "config": "CONFIG", "credits": "CREDITS", "back": "BACK",
    "sound on": "SOUND: ON", "sound off": "SOUND: OFF",
    **{f"volume {v}": f"VOLUME: {v}%" for v in (100, 75, 50, 25)},
    "controls arrows": "CONTROLS: ARROWS", "controls wasd": "CONTROLS: WASD",
    "style classic": "STYLE: CLASSIC", "style nyan": "STYLE: NYAN CAT",
}

GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:!?."


def glyph(ch):
    return svg(12, 18, text(6, 15, ch, 16) if ch != " " else '<rect width="12" height="18" fill="none"/>')


def costumes():
    """sprite name -> list of (costume name, svg, rotation center x, y)."""
    cat = {f: pixels(cat_grid(f), CAT_PALETTE, 1.2) for f in (1, 2)}
    c = {
        "Stage": [(f"{s} space", space(s), 240, 180) for s in STYLES],
        "Asteroid": [(f"classic rock {i}", classic_rock(i), 45, 45) for i in (1, 2, 3)]
        # hand-drawn by Daniel; 32px art x2.8 keeps the old 90px rock size so the split sizes stay the same
        + [(f"nyan rock {i}", *pixel_art(f"{color}-yarn.aseprite", 2.8))
           for i, color in enumerate(("Pink", "Blue", "Green"), start=1)],
        "Particle": [("classic spark", svg(4, 4, '<circle cx="2" cy="2" r="1.6" fill="#fff"/>'), 2, 2),
                     ("classic shard", svg(12, 2, '<rect width="12" height="2" fill="#fff"/>'), 6, 1),
                     ("nyan spark", heart(), 5, 5),
                     ("nyan shard", svg(6, 6, '<rect width="6" height="6" fill="#ffcc99"/>'
                                              '<rect x="1.5" y="1.5" width="3" height="3" fill="#ff99ff"/>'), 3, 3)],
        "Trail": [("rainbow", rainbow_segment(), 5, 9)],
        "Bullet": [("classic bullet", svg(5, 5, '<circle cx="2.5" cy="2.5" r="2.2" fill="#fff"/>'), 2.5, 2.5),
                   ("nyan bullet", star(10, "#ffe14d", "#ff5fa2"), 5, 5)],
        "UfoShot": [("classic ufo shot", svg(5, 5, '<circle cx="2.5" cy="2.5" r="2.2" fill="#fff"/>'), 2.5, 2.5),
                    ("nyan ufo shot", bone(), 7, 3.5)],
        "UFO": [("classic ufo", classic_ufo(), 32, 16), ("nyan ufo", *pixel_art("Dog-OVNI.aseprite", 2))],
        "Ship": [("classic ship 1", classic_ship(False), 15, 12), ("classic ship 2", classic_ship(True), 15, 12),
                 ("nyan ship 1", svg(41, 27, cat[1]), 20, 12), ("nyan ship 2", svg(41, 27, cat[2]), 20, 12)],
        "Popup": [(f"{s} pop {v}", svg(50, 20, text(25, 15, f"+{v}", 14, "#fff" if s == "classic" else "#ff99ff")),
                   25, 15) for s in STYLES for v in (20, 50, 100, 200, 1000)],
        "SafeZone": [("zone", svg(150, 150, '<circle cx="75" cy="75" r="74" fill="#fff"/>'), 75, 75)],
        "Flash": [("flash", svg(480, 360, '<rect width="480" height="360" fill="#fff"/>'), 240, 180)],
        "Panel": [(f"{s} gameover", svg(480, 120, text(240, 60, "GAME OVER", 48, color)
                                         + (text(240, 95, "meow...", 18, "#fff") if s == "nyan" else "")), 240, 60)
                  for s, color in (("classic", "#fff"), ("nyan", "#ff99ff"))]
        + [("credits", lines_panel([
            (50, "CREDITS", 30, "#fff"),
            (100, "GAME DESIGN & PROGRAMMING", 14, "#aaa"),
            (125, "DANIEL GODRI NETO", 22, "#fff"),
            (170, "BASED ON ASTEROIDS", 14, "#aaa"),
            (190, "ATARI, 1979", 14, "#aaa"),
            (230, "NYAN CAT STYLE IS A FAN TRIBUTE", 12, "#aaa"),
            (248, "NYAN CAT CREATED BY CHRIS TORRES", 12, "#aaa"),
            (285, "MADE WITH SCRATCH", 14, "#fff")], [(50, 12, 380, 290)]), 240, 180)]
        + [(f"config {k}", lines_panel([(40, "CONFIG", 30, "#fff"), (250, "CONTROLS", 14, "#aaa"),
                                        (270, a, 12, "#ddd"), (288, b, 12, "#ddd")],
                                       [(160, 8, 160, 44), (70, 236, 340, 60)]), 240, 180)
           for k, (a, b) in CONTROL_HELP.items()],
        "Title": [(f"{s} title", title(s), 210, 70) for s in STYLES],
        "Button": [(f"btn {k}", button(v), 110, 15) for k, v in BUTTON_LABELS.items()],
        "HUD": [("c space", glyph(" "), 6, 9)]
        + [(f"c {ch}", glyph(ch), 6, 9) for ch in GLYPHS]
        + [(f"c {ch.lower()}", glyph(ch), 6, 9) for ch in GLYPHS if ch.isalpha()]
        + [("classic life", svg(12, 16, '<polygon points="6,1 11,15 6,11 1,15" fill="#000" stroke="#fff" '
                                        'stroke-width="1.5" stroke-linejoin="round"/>'), 6, 8),
           ("nyan life", svg(14.4, 12, pixels(cat_head_grid(), CAT_PALETTE, 1.2)), 7.2, 6)],
        "Sfx": [("blank", svg(2, 2, '<rect width="2" height="2" fill="none"/>'), 1, 1)],
    }
    return c


# =============================== sound synthesis ===============================

RATE = 22050


def _n(seconds):
    return int(RATE * seconds)


def osc(phase, shape):
    p = phase % 1
    if shape == "square":
        return 1.0 if p < 0.5 else -1.0
    if shape == "triangle":
        return 4 * abs(p - 0.5) - 1
    return math.sin(2 * math.pi * p)


def silence(seconds):
    return [0.0] * _n(seconds)


def noise(seconds, brightness, seed, decay=3.0):
    """Low-passed noise with a power decay; lower brightness = deeper."""
    rnd, n, y, out = random.Random(seed), _n(seconds), 0.0, []
    for i in range(n):
        y += brightness * (rnd.uniform(-1, 1) - y)
        fade = min(1.0, (n - i) / 300) if decay == 0 else (1 - i / n) ** decay
        out.append(y * fade * min(1.0, i / 100))
    return out


def sweep(seconds, f0, f1, shape="square", decay=2.0):
    n, phase, out = _n(seconds), 0.0, []
    for i in range(n):
        t = i / n
        phase += f0 * (f1 / f0) ** t / RATE
        out.append(osc(phase, shape) * (1 - t) ** decay)
    return out


def tone(seconds, f, shape="square", decay=2.0):
    return sweep(seconds, f, f, shape, decay)


def meow(seconds, f_start, f_peak, f_end):
    """Harmonic voice with a rising-then-falling pitch and a formant sliding from 'mee' to 'ow'."""
    n, phase, out = _n(seconds), 0.0, []
    for i in range(n):
        t = i / n
        if t < 0.35:
            f = f_start + (f_peak - f_start) * math.sin(t / 0.35 * math.pi / 2)
        else:
            f = f_peak + (f_end - f_peak) * (1 - math.cos((t - 0.35) / 0.65 * math.pi / 2))
        f *= 1 + 0.02 * math.sin(2 * math.pi * 6 * i / RATE)
        phase += f / RATE
        formant = 2600 - 1700 * t
        s = 0.0
        for k in range(1, 13):
            if k * f > 6000:
                break
            s += (math.exp(-((k * f - formant) / 800) ** 2) + 0.35 / k) * math.sin(2 * math.pi * k * phase)
        out.append(s * min(1.0, t / 0.08) * (1 - t) ** 0.6)
    return out


def purr(seconds, seed):
    rnd, n, y, out = random.Random(seed), _n(seconds), 0.0, []
    for i in range(n):
        y += 0.05 * (rnd.uniform(-1, 1) - y)
        am = (0.5 + 0.5 * math.sin(2 * math.pi * 23 * i / RATE)) ** 2
        out.append(y * am * min(1.0, i / 300, (n - i) / 300))
    return out


def notes(freqs, each, shape="triangle"):
    return [s for f in freqs for s in tone(each, f, shape, decay=1.5)]


# name -> (sample generator, loudness 0..1)
SOUNDS = {
    "classic fire": (lambda: sweep(0.14, 1600, 300), 0.35),
    "classic boom 3": (lambda: noise(0.7, 0.06, "b3"), 0.8),
    "classic boom 2": (lambda: noise(0.45, 0.18, "b2"), 0.8),
    "classic boom 1": (lambda: noise(0.25, 0.5, "b1"), 0.8),
    "classic ship boom": (lambda: noise(1.3, 0.04, "sb", decay=1.5), 0.9),
    "classic thrust": (lambda: noise(0.3, 0.08, "th", decay=0), 0.3),
    "classic life": (lambda: [s for _ in range(4) for s in tone(0.05, 1760) + silence(0.03)], 0.3),
    "classic click": (lambda: tone(0.04, 1200), 0.25),
    "nyan fire": (lambda: meow(0.14, 900, 1250, 1000), 0.3),
    "nyan boom 3": (lambda: meow(0.55, 330, 480, 300), 0.6),
    "nyan boom 2": (lambda: meow(0.4, 520, 760, 560), 0.6),
    "nyan boom 1": (lambda: meow(0.22, 950, 1300, 1100), 0.6),
    "nyan ship boom": (lambda: meow(1.0, 700, 820, 250), 0.7),
    "nyan thrust": (lambda: purr(0.4, "purr"), 0.4),
    "nyan life": (lambda: notes((1047, 1319, 1568, 2093), 0.07), 0.35),
    "nyan click": (lambda: meow(0.06, 1400, 1600, 1500), 0.25),
}


def wav_bytes(samples, loudness):
    peak = max(abs(s) for s in samples) or 1.0
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s / peak * loudness * 32767)) for s in samples))
    return buf.getvalue()
