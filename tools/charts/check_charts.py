#!/usr/bin/env python3
"""Keep new chart generators on the shared kit.

The palette was already shared. Fonts, canvas and the footer were not: all 14
generators loaded their own font files and hand-drew the footer, and three had
already drifted apart on footer spacing. That is how a set stops looking
designed.

Scope on purpose: this enforces the kit on generators that have ADOPTED it, and
on every new one. The eleven older generators are grandfathered, listed below by
name, because rewriting working chart code buys nothing visible and risks a
regression in a chart that currently earns impressions. Remove a name from the
list when its generator is migrated, never to silence a failure.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent

GRANDFATHERED = {
    "make_aa_guide.py", "make_atp_guide.py", "make_bloodtype_guide.py",
    "make_buffer_guide.py", "make_catabolism_guide.py", "make_equation_guide.py",
    "make_glycolysis_guide.py", "make_inhibition_guide.py", "make_mcat_aa_guide.py",
    "make_pin_inhibition.py", "make_transport_guide.py", "make_urea_guide.py",
    "make_tca_guide.py", "make_codon_guide.py",
}

fails = []


def main():
    gens = sorted(p for p in HERE.glob("make_*.py"))
    checked = 0
    for p in gens:
        src = p.read_text()
        old = p.name in GRANDFATHERED
        uses_kit = "chartkit" in src
        if old and not uses_kit:
            continue                      # known, listed, deliberately untouched
        checked += 1
        if not uses_kit:
            fails.append("%s does not import chartkit; new generators must"
                         % p.name)
            continue
        # A generator on the kit must not reach around it.
        if re.search(r"ImageFont\.truetype\(", src):
            fails.append("%s calls ImageFont.truetype directly; use "
                         "chartkit.fonts() or chartkit.unicode_font()" % p.name)
        if re.search(r'd\.text\(\s*\([^)]*\)\s*,\s*"biochemtools\.com"', src):
            fails.append("%s hand-draws the footer; use chartkit.footer()"
                         % p.name)
        if "CC BY" in src and "chartkit.footer" not in src and "footer(" not in src:
            fails.append("%s writes its own licence line; use chartkit.footer()"
                         % p.name)
        if re.search(r"#[0-9a-fA-F]{6}", src):
            fails.append("%s hard-codes a hex colour; the palette lives in "
                         "lightmode.py" % p.name)

    print("  %d generator(s) on the kit checked, %d grandfathered"
          % (checked, len(gens) - checked))
    if fails:
        print("\n%d PROBLEM(S):" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("  no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
