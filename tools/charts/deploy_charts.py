#!/usr/bin/env python3
"""Copy the built charts into the site's downloads folder under their public names.

The mapping used to live only in whoever's head ran the copy, which is how the
dark genetic-code chart ended up a palette revision behind its light twin.
"""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SITE = os.path.join(HERE, "..", "..", "downloads")
MAP = {
    "amino-acid-catabolism-chart": "catabolism-guide",
    "amino-acid-structures-chart": "mcat-amino-acid-guide",
    "atp-yield-chart": "atp-yield-guide",
    "biochem-equation-chart": "equation-guide",
    "blood-type-inheritance-chart": "bloodtype-guide",
    "buffer-selection-chart": "buffer-guide",
    "citric-acid-cycle-chart": "tca-guide",
    "enzyme-inhibition-chart": "inhibition-guide",
    "genetic-code-chart": "codon-chart-guide",
    "glycolysis-steps-chart": "glycolysis-guide",
    "membrane-transport-chart": "transport-guide",
    "urea-cycle-chart": "urea-guide",
}

changed = []
for public, built in sorted(MAP.items()):
    for suf in ("", "-light"):
        src, dst = os.path.join(BUILD, built + suf + ".png"), os.path.join(SITE, public + suf + ".png")
        assert os.path.exists(src), "missing build output: " + src
        same = os.path.exists(dst) and open(src, "rb").read() == open(dst, "rb").read()
        if not same:
            shutil.copy2(src, dst)
            changed.append(public + suf + ".png")

print("  %d of %d chart images updated" % (len(changed), len(MAP) * 2))
for c in changed:
    print("    " + c)
