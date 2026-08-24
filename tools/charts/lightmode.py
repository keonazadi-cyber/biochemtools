"""Shared light-mode palette for the chart scripts.

Two people on r/Biochemistry asked for a white background within half an hour of
each other. These charts are meant to be printed, and a dark background wastes ink,
so every chart ships in both themes from one source.

Usage: from lightmode import theme;  BG, CARD, LINE, WHITE, GRAY, DIM, ... = theme()
"""
import sys

LIGHT = "--light" in sys.argv


def theme():
    """Return (LIGHT, palette dict). Dark values match what the charts already used."""
    if LIGHT:
        # Deliberately deeper than a typical light theme. Readers on r/Biochemistry
        # said the first pass washed out on paper, which defeats the point of a
        # print version, so these are dark enough for an average office printer.
        return True, dict(
            BG=(255, 255, 255), CARD=(245, 246, 249), LINE=(198, 204, 213),
            WHITE=(18, 20, 24), GRAY=(74, 80, 90), DIM=(116, 123, 134),
            GREEN=(6, 105, 74), AMBER=(146, 92, 4), RED=(170, 28, 24),
            BLUE=(17, 76, 152), PURPLE=(92, 56, 156),
            NONPOLAR=(64, 72, 92), AROMATIC=(92, 56, 156), POLAR=(6, 105, 74),
            ACIDIC=(170, 28, 24), BASIC=(17, 76, 152),
            BAND=(240, 242, 245), CHIP=(225, 229, 236), PANEL=(232, 244, 238),
            WARM=(252, 243, 222),
        )
    # Warm dark, matched to the site as of 2026-08-24. Only the neutrals moved.
    # The hues stay separated because they carry meaning: a chart that colours
    # acidic and basic side chains the same is a broken chart, not a restyled one.
    return False, dict(
        BG=(14, 12, 10), CARD=(23, 19, 16), LINE=(44, 38, 32),
        WHITE=(244, 239, 231), GRAY=(162, 150, 138), DIM=(128, 118, 108),
        GREEN=(111, 181, 159), AMBER=(232, 176, 75), RED=(224, 104, 96),
        BLUE=(96, 150, 224), PURPLE=(176, 148, 220),
        NONPOLAR=(150, 142, 130), AROMATIC=(176, 148, 220), POLAR=(111, 181, 159),
        ACIDIC=(224, 104, 96), BASIC=(96, 150, 224),
        BAND=(20, 16, 14), CHIP=(38, 32, 27), PANEL=(20, 30, 26),
        WARM=(32, 26, 18),
    )


def suffix():
    return "-light" if LIGHT else ""
