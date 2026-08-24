#!/usr/bin/env python3
"""Roll the warm palette and typography across every page.

Colour lives in two different places on this site and they need different
treatment. CSS and inline styles are chrome, and follow the new palette exactly.
Canvas drawing colours inside <script> are data: the titration curve draws its pKa
lines in amber and its pI line in teal, so mapping teal to amber there would
collide two lines that exist to be told apart.
"""
import glob, re, os, sys

# chrome: everything outside <script>
CHROME = {
    "#0f1115": "#0e0c0a", "#1a1d24": "#171310", "#20232c": "#1d1815",
    "#2a2e38": "#2c2620", "#e8eaed": "#f4efe7", "#9aa0aa": "#a2968a",
    "#5dcaa5": "#e8b04b",   # accent: mint becomes amber
    "#378add": "#6fb59f",   # secondary: blue becomes the retired teal
    "#7f77dd": "#cf9366",   # headings: purple becomes warm clay
    "#e0a93b": "#e8b04b",
    "#0b0d11": "#17120c",   # text on accent buttons
}
# data: inside <script>. Neutrals follow so canvases sit on the right ground,
# but hues that encode meaning keep their separation.
DATA = {
    "#0f1115": "#0e0c0a", "#1a1d24": "#171310", "#20232c": "#1d1815",
    "#2a2e38": "#2c2620", "#1c1f27": "#1a1512",
    "#e8eaed": "#f4efe7", "#9aa0aa": "#a2968a",
    "#5dcaa5": "#6fb59f",   # stays a teal so it never collides with the amber
    "#e0a93b": "#e8b04b",
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK'
         '@9..144,300..700,0..100,0..1&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">\n')

LAYER = """
 /* --- direction D --- */
 body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:9;opacity:.13;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)'/%3E%3C/svg%3E")}
 .brand,h1,h2{font-family:Fraunces,Georgia,serif;font-weight:400}
 .brand{font-variation-settings:"SOFT" 40,"WONK" 1,"opsz" 40;font-weight:600}
 h1{letter-spacing:-.03em;font-weight:300}
 h2{letter-spacing:-.015em}
 .btn,.navcta{border-radius:100px!important}
 input[type=range]{-webkit-appearance:none;appearance:none;height:6px;border-radius:100px;
   background:var(--line);outline:none}
 input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:20px;height:20px;
   border-radius:50%;background:var(--accent);cursor:pointer;border:none;
   box-shadow:0 2px 8px rgba(0,0,0,.45)}
 input[type=range]::-moz-range-thumb{width:20px;height:20px;border-radius:50%;background:var(--accent);
   cursor:pointer;border:none}
 input[type=range]::-moz-range-track{height:6px;border-radius:100px;background:var(--line)}
 @media print{body::after{display:none}}
</style>"""


def split_scripts(h):
    """Yield (text, is_script) runs so the two maps never touch each other's text."""
    out, i = [], 0
    for m in re.finditer(r"<script\b[\s\S]*?</script>", h, re.I):
        out.append((h[i:m.start()], False))
        out.append((m.group(0), True))
        i = m.end()
    out.append((h[i:], False))
    return out


def convert(path):
    h = open(path, encoding="utf-8").read()
    if "Fraunces" in h:
        return "skipped (already themed)"
    parts = []
    for text, is_script in split_scripts(h):
        table = DATA if is_script else CHROME
        for old, new in table.items():
            text = re.sub(old, new, text, flags=re.I)
        parts.append(text)
    h = "".join(parts)

    if "fonts.googleapis" not in h:
        anchor = '<link rel="icon"'
        if anchor in h:
            h = h.replace(anchor, FONTS + anchor, 1)
        else:
            h = h.replace("</title>", "</title>\n" + FONTS, 1)
    h = h.replace('font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif',
                  'font-family:"Inter Tight",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif')
    if "--- direction D ---" not in h:
        h = h.replace("</style>", LAYER, 1)
    open(path, "w", encoding="utf-8").write(h)
    return "themed"


def _selfcheck():
    """The tables map OLD to NEW. A pass of the site-wide colour migration over
    this file once rewrote its own keys, turning every entry into a no-op."""
    for name, t in (("CHROME", CHROME), ("DATA", DATA)):
        for k, v in t.items():
            assert k != v, "%s has a no-op mapping for %s, the table has been clobbered" % (name, k)


if __name__ == "__main__":
    _selfcheck()
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    n = collections = 0
    done, skipped = [], []
    for f in sorted(glob.glob("*.html")):
        r = convert(f)
        (done if r == "themed" else skipped).append(f)
    print("  themed %d pages, skipped %d already done" % (len(done), len(skipped)))
    if skipped:
        print("  skipped: " + ", ".join(skipped))
