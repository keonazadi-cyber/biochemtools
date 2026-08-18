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
    return False, dict(
        BG=(17, 19, 24), CARD=(25, 28, 35), LINE=(46, 50, 60),
        WHITE=(240, 242, 245), GRAY=(158, 164, 174), DIM=(120, 128, 140),
        GREEN=(95, 204, 167), AMBER=(228, 169, 59), RED=(226, 100, 94),
        BLUE=(93, 157, 226), PURPLE=(171, 144, 224),
        NONPOLAR=(140, 149, 170), AROMATIC=(171, 144, 224), POLAR=(95, 204, 167),
        ACIDIC=(228, 106, 97), BASIC=(93, 157, 226),
        BAND=(22, 24, 30), CHIP=(38, 42, 52), PANEL=(22, 34, 30),
        WARM=(30, 28, 22),
    )


def suffix():
    return "-light" if LIGHT else ""
