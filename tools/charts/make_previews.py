#!/usr/bin/env python3
"""Card-sized preview crops, cut from the 18 chart plates the site already owns.

The homepage is a wall of text. These give every tool card a picture instead of
a sentence, without generating a single new image: each preview is a TIGHT crop
of the plate that belongs to that tool's topic.

**The rule that makes or breaks this.** A whole chart shrunk to card size reads
as grey noise, which is exactly how the existing gallery thumbnails read. So a
preview is a small region blown up, never a big region shrunk down.
`MAX_DOWNSCALE` enforces it: a crop may be at most 1.5x wider than the card it
lands in, so chart text stays at least two thirds of its native size.

Crops are chosen by ink density rather than by hand, so a region that is mostly
background can never be picked, and the choice is reproducible.

    python3 make_previews.py              # write previews + a contact sheet
    python3 make_previews.py --sheet-only # just re-make the contact sheet
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "..")
PLATES = os.path.join(SITE, "downloads")
OUT = os.path.join(SITE, "previews")

CARD_W, CARD_H = 760, 440           # 2x the rendered card, for retina
BANNER_W, BANNER_H = 1600, 460      # the band that opens each section

# The plate that leads each section. Banners take the plate's TOP band on
# purpose: the chart's own title and first rows are the most legible and the
# most obviously designed part of it, so the band reads as a plate rather
# than as a crop of something.
BANNERS = {
    "biochemistry": "amino-acid-chart",
    "molecular-biology": "genetic-code-chart",
    "genetics": "genetics-chart",
    "chemistry": "buffer-selection-chart",
    "solutions": "dilution-chart",
    "physiology": "physiology-chart",
}
ASPECT = CARD_W / CARD_H
MAX_DOWNSCALE = 1.5                 # see the docstring: this is the whole trick
MAX_BYTES = 40_000

# Which plates serve which section. A tool gets a crop from one of its
# section's plates; sections are listed in the order the crops are handed out.
SECTION_PLATES = {
    "biochemistry": ["amino-acid-chart", "amino-acid-structures-chart",
                     "titration-curves-chart", "biochem-equation-chart",
                     "enzyme-inhibition-chart", "mcat-biochem-chart"],
    "molecular-biology": ["genetic-code-chart", "amino-acid-structures-chart",
                          "mcat-biochem-chart"],
    "genetics": ["genetics-chart", "blood-type-inheritance-chart",
                 "genetic-code-chart"],
    "chemistry": ["buffer-selection-chart", "biochem-equation-chart",
                  "titration-curves-chart", "dilution-chart"],
    "solutions": ["dilution-chart", "buffer-selection-chart"],
    "physiology": ["physiology-chart", "atp-yield-chart",
                   "glycolysis-steps-chart", "citric-acid-cycle-chart",
                   "urea-cycle-chart", "membrane-transport-chart",
                   "amino-acid-catabolism-chart"],
}

# A tool whose own plate is obvious gets it outright.
PREFERRED = {
    "amino-acid-chart.html": "amino-acid-chart",
    "amino-acid-structures.html": "amino-acid-structures-chart",
    "codon-chart.html": "genetic-code-chart",
    "biochem-equation-sheet.html": "biochem-equation-chart",
    "punnett-square-calculator.html": "genetics-chart",
    "blood-type-punnett-square-calculator.html": "blood-type-inheritance-chart",
    "amino-acid-titration-curve.html": "titration-curves-chart",
    "dilution-calculator.html": "dilution-chart",
    "antibody-dilution-calculator.html": "dilution-chart",
    "buffer-pka-table.html": "buffer-selection-chart",
    "henderson-hasselbalch-buffer-calculator.html": "buffer-selection-chart",
    "michaelis-menten-vs-lineweaver-burk.html": "enzyme-inhibition-chart",
    "atp-yield-calculator.html": "atp-yield-chart",
    "glycolysis-pathway-explorer.html": "glycolysis-steps-chart",
    "citric-acid-cycle-explorer.html": "citric-acid-cycle-chart",
    "urea-cycle-explorer.html": "urea-cycle-chart",
    "membrane-transport-explorer.html": "membrane-transport-chart",
    "amino-acid-catabolism-explorer.html": "amino-acid-catabolism-chart",
    "oxygen-dissociation-curve-calculator.html": "physiology-chart",
    "mcat-buffer-questions-explained.html": "mcat-biochem-chart",
}

# Everything else is matched on subject words, because a round-robin put a
# codon table on the glycolysis ATP card, and a picture of the wrong thing is
# worse than no picture. Earlier entries win ties.
TOPIC = [
    (("beta-oxidation", "fatty acid", "lipid"), "amino-acid-catabolism-chart"),
    (("glycolysis",), "glycolysis-steps-chart"),
    (("citric", "krebs", "tca"), "citric-acid-cycle-chart"),
    (("urea", "ammonia"), "urea-cycle-chart"),
    (("transport", "membrane", "osmo", "tonicity"), "membrane-transport-chart"),
    (("atp", "electron transport", "oxidative"), "atp-yield-chart"),
    (("catabolism", "ketogenic", "glucogenic"), "amino-acid-catabolism-chart"),
    (("a260", "nucleic acid concentration", "concentration", "dilution",
      "molarity", "solution", "percent", "ppm", "normality"), "dilution-chart"),
    (("codon", "translation", "transcription", "rna", "dna", "melting",
      "gc content", "orf", "reading frame", "primer"), "genetic-code-chart"),
    (("punnett", "hardy", "weinberg", "pedigree", "x-linked", "allele",
      "dihybrid", "inheritance"), "genetics-chart"),
    (("blood type", "abo", "rh"), "blood-type-inheritance-chart"),
    (("titration", "isoelectric", "pi ", "peptide charge"), "titration-curves-chart"),
    (("enzyme", "michaelis", "lineweaver", "inhibit", "km", "vmax", "kinetic"),
     "enzyme-inhibition-chart"),
    (("buffer", "henderson", "pka", "ph "), "buffer-selection-chart"),
    (("dilution", "molarity", "concentration", "a260", "nucleic acid",
      "solution", "percent", "ppm", "normality"), "dilution-chart"),
    (("equation", "formula", "unit convert"), "biochem-equation-chart"),
    (("mcat",), "mcat-biochem-chart"),
    (("amino acid", "protein", "peptide", "residue", "hydropathy"),
     "amino-acid-chart"),
    (("structure", "draw"), "amino-acid-structures-chart"),
    (("cardiac", "renal", "clearance", "oxygen", "hemoglobin", "physiolog"),
     "physiology-chart"),
    (("quiz", "practice", "question", "test"), "mcat-biochem-chart"),
]


def pick_plate(href, title, section):
    """The plate whose subject matches this tool, never a round-robin."""
    if href in PREFERRED:
        return PREFERRED[href]
    hay = (href + " " + title).lower().replace("-", " ")
    for words, plate in TOPIC:
        if any(w in hay for w in words):
            return plate
    return SECTION_PLATES[section][0]


def load(name):
    return Image.open(os.path.join(PLATES, name + ".png")).convert("RGB")


def candidates(img, want):
    """The `want` densest non-overlapping windows, by ink density.

    Density is measured on a small grayscale copy, so this is cheap and the
    result does not depend on the plate's size.
    """
    cw = int(min(img.width, CARD_W * MAX_DOWNSCALE))
    ch = int(cw / ASPECT)
    if ch > img.height:
        ch = img.height
        cw = int(ch * ASPECT)
    small = img.convert("L").resize((img.width // 8, img.height // 8))
    px = small.load()
    sw, sh = small.size
    bw, bh = max(1, cw // 8), max(1, ch // 8)

    scored = []
    step = max(1, bh // 3)
    for sy in range(0, max(1, sh - bh + 1), step):
        for sx in range(0, max(1, sw - bw + 1), max(1, bw // 3)):
            vals = [px[x, y] for y in range(sy, min(sy + bh, sh), 2)
                    for x in range(sx, min(sx + bw, sw), 2)]
            if not vals:
                continue
            m = sum(vals) / len(vals)
            var = sum((v - m) ** 2 for v in vals) / len(vals)
            scored.append((var, sx * 8, sy * 8))
    scored.sort(reverse=True)

    picked = []
    for var, x, y in scored:
        if len(picked) >= want:
            break
        if any(abs(x - px0) < cw * .3 and abs(y - py0) < ch * .3
               for px0, py0 in picked):
            continue
        picked.append((x, y))
    return [(x, y, cw, ch) for x, y in picked]


def crop_to_card(img, box):
    x, y, cw, ch = box
    x = max(0, min(x, img.width - cw))
    y = max(0, min(y, img.height - ch))
    region = img.crop((x, y, x + cw, y + ch))
    downscale = region.width / CARD_W
    assert downscale <= MAX_DOWNSCALE + 1e-6, (
        "crop is %.2fx wider than the card; chart text would shrink past "
        "legibility (max %.2fx). Use a tighter region."
        % (downscale, MAX_DOWNSCALE))
    return region.resize((CARD_W, CARD_H), Image.LANCZOS)


def save(img, path):
    for colours in (96, 64, 48, 32):
        img.convert("P", palette=Image.ADAPTIVE, colors=colours).save(
            path, optimize=True)
        if os.path.getsize(path) <= MAX_BYTES:
            return os.path.getsize(path)
    return os.path.getsize(path)


def main(argv):
    tools = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "preview_tools.json")))
    os.makedirs(OUT, exist_ok=True)

    plate_cache, box_pool, made, sizes = {}, {}, [], []
    used_boxes = {}
    for section, entries in tools.items():
        for href, title in entries:
            plate = pick_plate(href, title, section)
            if plate not in plate_cache:
                plate_cache[plate] = load(plate)
            img = plate_cache[plate]
            if plate not in box_pool:
                box_pool[plate] = candidates(img, 24)
            pool = box_pool[plate]
            # A card must never repeat its own section's band. The band is the
            # plate's top strip, so a card drawing on that same plate skips any
            # window overlapping it; side by side they read as a mistake.
            if BANNERS.get(section) == plate:
                band_h = int(img.width * BANNER_H / BANNER_W)
                lower = [b for b in pool if b[1] >= band_h * .8]
                if lower:
                    pool = lower
            assert pool, "no usable crop found on " + plate
            used = used_boxes.setdefault(plate, 0)
            box = pool[used % len(pool)]
            if used >= len(pool):          # exhausted: shift rather than repeat
                lap = used // len(pool)
                x, y, cw, ch = box
                box = (max(0, x + int(cw * .18) * lap),
                       max(0, y + int(ch * .22) * lap), cw, ch)
            used_boxes[plate] = used + 1
            card = crop_to_card(img, box)
            name = href.replace(".html", "") + ".png"
            n = save(card, os.path.join(OUT, name))
            sizes.append(n)
            made.append((section, href, title, plate, name))

    for section, plate in sorted(BANNERS.items()):
        img = plate_cache.get(plate) or load(plate)
        # Full plate width, never a horizontal slice: cutting the band
        # narrower chopped words mid-letter and read as a broken image.
        bw = img.width
        bh = int(bw * BANNER_H / BANNER_W)
        region = img.crop((0, 0, bw, min(bh, img.height)))
        band = region.resize((BANNER_W, BANNER_H), Image.LANCZOS)
        n = save(band, os.path.join(OUT, "banner-" + section + ".png"))
        sizes.append(n)
    print("  %d section banners written" % len(BANNERS))

    print("  %d previews written to previews/" % len(made))
    print("  largest %.1f KB, median %.1f KB"
          % (max(sizes) / 1000., sorted(sizes)[len(sizes) // 2] / 1000.))
    over = [s for s in sizes if s > MAX_BYTES]
    if over:
        print("  WARNING %d over %d bytes" % (len(over), MAX_BYTES))

    cols = 6
    rows = (len(made) + cols - 1) // cols
    tw, th = 300, 174
    sheet = Image.new("RGB", (cols * tw, rows * (th + 26)), (14, 12, 10))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except Exception:
        f = ImageFont.load_default()
    for i, (section, href, title, plate, name) in enumerate(made):
        t = Image.open(os.path.join(OUT, name)).convert("RGB").resize((tw - 8, th - 8))
        x, y = (i % cols) * tw, (i // cols) * (th + 26)
        sheet.paste(t, (x + 4, y + 4))
        d.text((x + 6, y + th), title[:36], font=f, fill=(210, 205, 198))
    sheet.save(os.path.join(HERE, "build", "preview-sheet.png"))
    print("  contact sheet: tools/charts/build/preview-sheet.png")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
