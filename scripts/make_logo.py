#!/usr/bin/env python3
"""Draw the vian.cz logo and favicons from the Fraunces outlines (run once locally, the outputs are committed).

    python3 scripts/make_logo.py /path/to/Fraunces[SOFT,WONK,opsz,wght].ttf

Logo = the word "vian" as vector outlines (no <text>, renders the same everywhere) with a tape measure under it:
a thin rule with ticks, every 5th one longer. The dot of the "i" is a separate terracotta circle, the only accent.
Favicon = a lower-case "v" in linen on a fir-green rounded square; from 180 px up two tape ticks sit under it.
Fonts: Fraunces, SIL Open Font License (static/fonts/OFL-fraunces.txt).
"""
import io
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

APP = Path(__file__).resolve().parent.parent
ST = APP / "static"
FIR, FIR_D, CLAY, LINEN = "#2F5D50", "#24493F", "#B4532D", "#F6F3EE"


def instance(path):
    f = TTFont(path)
    f = instancer.instantiateVariableFont(f, {"opsz": 72, "wght": 640, "SOFT": 60, "WONK": 0})
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return TTFont(buf)


def word_paths(font, text, scale, x0, baseline):
    """SVG path data of `text` (glyph by glyph, with advance widths), y flipped; returns (d, right edge, bounds)."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    x = x0
    parts = []
    boxes = {}
    for ch in text:
        gname = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        tp = TransformPen(pen, (scale, 0, 0, -scale, x, baseline))
        gs[gname].draw(tp)
        parts.append(pen.getCommands())
        bp = BoundsPen(gs)
        gs[gname].draw(bp)
        if bp.bounds:
            xmin, ymin, xmax, ymax = bp.bounds
            boxes.setdefault(ch, []).append((x + xmin * scale, baseline - ymax * scale, x + xmax * scale, baseline - ymin * scale))
        x += hmtx[gname][0] * scale
    return " ".join(parts), x, boxes


def logo_svg(font, color, tape_color, dot_color):
    upm = font["head"].unitsPerEm
    scale = 64 / upm                  # cap height ~45 px at 64 px font size
    baseline = 52
    d, right, boxes = word_paths(font, "vıan", scale, 2, baseline)   # dotless i: the dot is drawn as an accent circle
    ib = boxes["ı"][0]
    cx = (ib[0] + ib[2]) / 2
    xh = ib[1]                         # top of the dotless i = x-height
    dot = f'<circle cx="{cx:.1f}" cy="{xh - 7.5:.1f}" r="4.7" fill="{dot_color}"/>'
    w = right + 2
    y = baseline + 9                   # the tape under the word
    ticks = []
    n = 0
    xx = 3.0
    while xx <= w - 3:
        long = n % 5 == 0
        ticks.append(f"M{xx:.1f} {y}v{7 if long else 4}")
        xx += 4.6
        n += 1
    tape = (f'<path d="M2 {y}H{w - 2:.1f}" stroke="{tape_color}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
            f'<path d="{" ".join(ticks)}" stroke="{tape_color}" stroke-width="1.2" fill="none"/>')
    h = y + 9
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="vian">'
            f'<path d="{d}" fill="{color}"/>{dot}{tape}</svg>'), (round(w), round(h))


def favicon_svg(font, ticks=True):
    upm = font["head"].unitsPerEm
    gs = font.getGlyphSet()
    g = font.getBestCmap()[ord("v")]
    bp = BoundsPen(gs)
    gs[g].draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    size = 64
    scale = 40 / upm * 1.55
    gw, gh = (xmax - xmin) * scale, (ymax - ymin) * scale
    x = (size - gw) / 2 - xmin * scale
    top = (size - gh) / 2 - (4 if ticks else 0)
    baseline = top + ymax * scale
    pen = SVGPathPen(gs)
    gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
    t = ""
    if ticks:
        y = baseline + 6
        t = (f'<path d="M18 {y:.1f}H46" stroke="{LINEN}" stroke-width="2" stroke-linecap="round"/>'
             f'<path d="M18 {y:.1f}v5M25 {y:.1f}v3M32 {y:.1f}v5M39 {y:.1f}v3M46 {y:.1f}v5" stroke="{LINEN}" stroke-width="1.6"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{FIR}"/>'
            f'<path d="{pen.getCommands()}" fill="{LINEN}"/>{t}</svg>')


def raster(svg, size):
    """SVG -> PNG via the Chromium already on the Pi would be overkill: draw the same shapes with Pillow at 4x and downsample."""
    import cairosvg   # optional; falls back below
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)))


def main():
    font = instance(sys.argv[1])
    dark, (w, h) = logo_svg(font, FIR_D, FIR, CLAY)
    light, _ = logo_svg(font, LINEN, "#C9C5BD", "#D8743C")
    (ST / "img/ui/logo.svg").write_text(dark)
    (ST / "img/ui/logo-light.svg").write_text(light)
    (ST / "favicon.svg").write_text(favicon_svg(font, ticks=True))
    (ST / "img/ui/favicon-small.svg").write_text(favicon_svg(font, ticks=False))
    print(f"logo {w}x{h}")


if __name__ == "__main__":
    main()
