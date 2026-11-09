"""One type scale, one grid, one footer, for every chart.

The palette already lived in lightmode.py and no generator hard-codes a colour.
What each of the 14 re-decided for itself was the part you notice: fonts (14 of
14 loaded their own), canvas size (14 of 14), and the footer (14 of 14 drew it
by hand). That is the difference between a set that is consistent because
someone was careful and a set that is consistent by construction.

This does not restyle anything. The scale below is the sizes the charts already
use, written down as a scale so the next chart inherits them instead of picking.

    XS 20   S 22   M 27   L 34   XL 42   XXL 56     (about 1.25 between steps)

THE TOFU TRAP, now enforced here rather than remembered. Arial has no glyph for
U+207B, the superscript minus, so "OH⁻" renders as a blank box and the chart
ships looking broken. Any text with characters outside Arial goes through
unicode_font(), and safe_text() refuses to draw a string the font cannot render.
"""
import os
from PIL import ImageFont

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
UNI = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

SCALE = {"xs": 20, "s": 22, "m": 27, "l": 34, "xl": 42, "xxl": 56}

# One canvas grid. Width is fixed so a set of charts stacks cleanly in an image
# pack and in a Drive folder; height is per chart because content differs.
WIDTH = 1560
MARGIN = 64
GUTTER = 24


def _f(path, size):
    if not os.path.exists(path):
        raise RuntimeError("font missing: %s" % path)
    return ImageFont.truetype(path, size)


def fonts():
    """The named roles. Ask for a role, never for a number."""
    return {
        "title":  _f(BOLD, SCALE["xxl"]),
        "big":    _f(BOLD, SCALE["xl"]),
        "sub":    _f(REG,  SCALE["m"]),
        "head":   _f(BOLD, SCALE["m"]),
        "label":  _f(BOLD, SCALE["s"]),
        "body":   _f(REG,  SCALE["s"]),
        "note":   _f(REG,  SCALE["s"]),
        "small":  _f(REG,  SCALE["xs"]),
        "foot":   _f(REG,  SCALE["s"]),
        "domain": _f(BOLD, SCALE["m"]),
    }


def unicode_font(size, bold=False):
    """For any string with characters Arial does not carry."""
    return _f(UNI if os.path.exists(UNI) else (BOLD if bold else REG), size)


def renders(font, s):
    """True if every visible character in s has a real glyph in font."""
    box = font.getmask("￿").size      # guaranteed absent, so this IS .notdef
    for ch in s:
        if ch.strip() and font.getmask(ch).size == box:
            return False
    return True


def safe_text(d, xy, s, font, fill, **kw):
    """Draw, or refuse. A tofu box in a published chart is worse than a crash."""
    if not renders(font, s):
        missing = [c for c in s if c.strip() and not renders(font, c)]
        raise RuntimeError(
            "font cannot render %r in %r; use chartkit.unicode_font()"
            % ("".join(missing), s[:60]))
    d.text(xy, s, font=font, fill=fill, **kw)


def footer(d, W, H, y, P, F, note=None):
    """The one footer. Domain left, licence right, optional note above.

    Every generator wrote its own version of this, which is exactly the kind of
    thing that drifts: three of them had already fallen out of step on spacing.
    """
    if note:
        safe_text(d, (MARGIN, y), note, F["small"], P["DIM"])
        y += SCALE["xs"] + 14
    assert y + SCALE["m"] + 8 <= H, (
        "footer overflows: needs %d, canvas is %d" % (y + SCALE["m"] + 8, H))
    safe_text(d, (MARGIN, y), "biochemtools.com", F["domain"], P["WHITE"])
    tail = "free, no signup  /  CC BY 4.0"
    w = d.textlength(tail, font=F["foot"])
    assert MARGIN + d.textlength("biochemtools.com", font=F["domain"]) < W - MARGIN - w, \
        "footer domain and licence collide at this width"
    safe_text(d, (W - MARGIN - w, y + 10), tail, F["foot"], P["DIM"])
    bottom = y + SCALE["m"] + 18
    d._bct_footer_bottom = bottom     # fit() reads this, so a caller who forgets
    return bottom                     # to capture the return still crops correctly


def legend(d, x, y, items, P, F, gap=34):
    """The one legend: a swatch, a label, repeated. items = [(label, colour)]."""
    for label, colour in items:
        d.rectangle([x, y + 4, x + 16, y + 20], fill=colour)
        safe_text(d, (x + 26, y), label, F["body"], P["GRAY"])
        x += 26 + d.textlength(label, font=F["body"]) + gap
    return y + SCALE["s"] + 12


_LAST_DRAW = []


def fit(img, y, pad=None, d=None):
    if d is not None:
        _LAST_DRAW[:] = [d]
    """Crop a chart down to the content it actually drew.

    Generators size the canvas by guessing a height, and a guess that is too
    generous ships a chart with a black void under it. The first chart built on
    this kit did exactly that: content ended at 1360 on a 1980 canvas, which in
    an image pack reads as a broken image. Draw onto a generous canvas, then
    call this.
    """
    pad = MARGIN if pad is None else pad
    h = int(y + pad)
    # If a footer was drawn below the y the caller passed, use the footer's own
    # bottom. Forgetting to capture footer()'s return clipped the licence line
    # off the first chart built on this kit, and a clipped licence on a CC BY
    # image is the one thing on a chart that must never be cut.
    fb = getattr(_LAST_DRAW[0], "_bct_footer_bottom", 0) if _LAST_DRAW else 0
    if fb and fb + pad > h:
        h = int(fb + pad)
    assert h <= img.height, (
        "content ran past the canvas: needs %d, canvas is %d" % (h, img.height))
    assert h > 200, "cropping to %d would produce an empty chart" % h
    return img.crop((0, 0, img.width, h))
