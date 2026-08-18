#!/usr/bin/env python3
"""Draw the 20 amino acid structures used by the MCAT amino acid chart.

These used to come from a one-off script writing into a temp directory. The temp
directory was cleaned, so the chart could not be rebuilt, which meant a wrong
claim printed on it could not be corrected. This version lives in the repo.

Each SMILES is the zwitterion at pH 7.4: backbone NH3+ and COO-, side chain in
its dominant state at that pH. Proline is the exception the chart now calls out,
its nitrogen is a secondary amine inside the ring.

Run directly to (re)generate both themes:  python3 aastructures.py
"""
import os
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, Descriptors
from rdkit.Chem.Draw import rdMolDraw2D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aa_struct")
H = 250
W = 340

SMILES = {
    "Ala": "C[C@H]([NH3+])C(=O)[O-]",
    "Arg": "[NH3+][C@@H](CCCNC(=[NH2+])N)C(=O)[O-]",
    "Asn": "[NH3+][C@@H](CC(N)=O)C(=O)[O-]",
    "Asp": "[NH3+][C@@H](CC(=O)[O-])C(=O)[O-]",
    "Cys": "[NH3+][C@@H](CS)C(=O)[O-]",
    "Gln": "[NH3+][C@@H](CCC(N)=O)C(=O)[O-]",
    "Glu": "[NH3+][C@@H](CCC(=O)[O-])C(=O)[O-]",
    "Gly": "[NH3+]CC(=O)[O-]",
    "His": "[NH3+][C@@H](Cc1c[nH]cn1)C(=O)[O-]",
    "Ile": "CC[C@H](C)[C@H]([NH3+])C(=O)[O-]",
    "Leu": "CC(C)C[C@H]([NH3+])C(=O)[O-]",
    "Lys": "[NH3+][C@@H](CCCC[NH3+])C(=O)[O-]",
    "Met": "[NH3+][C@@H](CCSC)C(=O)[O-]",
    "Phe": "[NH3+][C@@H](Cc1ccccc1)C(=O)[O-]",
    "Pro": "[O-]C(=O)[C@@H]1CCC[NH2+]1",
    "Ser": "[NH3+][C@@H](CO)C(=O)[O-]",
    "Thr": "C[C@@H](O)[C@H]([NH3+])C(=O)[O-]",
    "Trp": "[NH3+][C@@H](Cc1c[nH]c2ccccc12)C(=O)[O-]",
    "Tyr": "[NH3+][C@@H](Cc1ccc(O)cc1)C(=O)[O-]",
    "Val": "CC(C)[C@H]([NH3+])C(=O)[O-]",
}

# Stereochemistry at the alpha carbon, which is the claim the chart prints in its
# footer. Every proteinogenic amino acid is L, and L is (S) at the alpha carbon for
# all of them except cysteine, where the sulfur outranks the carboxyl and flips the
# CIP letter without changing the actual geometry. Glycine has no stereocenter.
# This check caught alanine being drawn as the D-isomer.
ALPHA_CIP = {"Cys": "R", "Gly": None}

# Second stereocenters, which only isoleucine and threonine have.
BETA_CIP = {"Ile": "S", "Thr": "R"}

# Net charge on the whole zwitterion at pH 7.4. This is the number the chart
# prints in the corner chip, so it is asserted rather than trusted.
NET = {"Asp": -1, "Glu": -1, "Lys": +1, "Arg": +1}


def _alpha_carbon(m):
    """The carbon bonded to both the amine nitrogen and the carboxyl carbon."""
    for a in m.GetAtoms():
        if a.GetSymbol() != "C":
            continue
        nb = a.GetNeighbors()
        has_n = any(x.GetSymbol() == "N" for x in nb)
        has_coo = any(x.GetSymbol() == "C" and
                      sum(1 for y in x.GetNeighbors() if y.GetSymbol() == "O") == 2 for x in nb)
        if has_n and has_coo:
            return a.GetIdx()
    return None


def check():
    """Every structure must match the molecular weight the tool page publishes.

    This is the guard that matters. If a SMILES is wrong the drawing still looks
    plausible, but the weight will not match the page, and the build stops.
    """
    import chartdata
    page = {a["c3"]: a for a in chartdata.amino_acids()}
    assert set(page) == set(SMILES), "structure set does not match the page"
    for c3, smi in SMILES.items():
        m = Chem.MolFromSmiles(smi)
        assert m is not None, "%s: SMILES does not parse" % c3
        Chem.AssignStereochemistry(m, cleanIt=True, force=True)
        cips = {a.GetIdx(): a.GetProp("_CIPCode") for a in m.GetAtoms() if a.HasProp("_CIPCode")}
        alpha = _alpha_carbon(m)
        want_a = ALPHA_CIP.get(c3, "S")
        got_a = cips.get(alpha) if alpha is not None else None
        assert got_a == want_a, "%s: alpha carbon is %s, the chart says L which needs %s" % (c3, got_a, want_a)
        if c3 in BETA_CIP:
            other = [v for k, v in cips.items() if k != alpha]
            assert other == [BETA_CIP[c3]], "%s: second stereocenter is %s, expected %s" % (c3, other, BETA_CIP[c3])

        q = Chem.GetFormalCharge(m)
        assert q == NET.get(c3, 0), "%s: net charge is %+d, expected %+d" % (c3, q, NET.get(c3, 0))
        # The page lists the neutral free amino acid. A charged side chain has
        # gained or lost a proton relative to that, so back the protons out
        # before comparing, otherwise Arg and Lys read 1.01 heavy and Asp and
        # Glu read 1.01 light for a reason that has nothing to do with an error.
        mw = Descriptors.MolWt(m) - q * 1.008
        want = page[c3]["mw"]
        assert abs(mw - want) < 0.35, "%s: drawn structure is %.2f, page says %.2f" % (c3, mw, want)
    return page


def render(light):
    _, P = __import__("lightmode").theme(), None
    bg = (245, 246, 249) if light else (25, 28, 35)          # CARD in each theme
    fg = (0.09, 0.11, 0.14) if light else (0.94, 0.95, 0.96)
    sub = os.path.join(OUT, "png_light" if light else "png")
    os.makedirs(sub, exist_ok=True)
    for c3, smi in SMILES.items():
        m = Chem.MolFromSmiles(smi)
        AllChem.Compute2DCoords(m)
        d = rdMolDraw2D.MolDraw2DCairo(W, H)
        o = d.drawOptions()
        o.setBackgroundColour(tuple(c / 255 for c in bg))
        o.baseFontSize = 0.55
        o.bondLineWidth = 2
        # Without this each molecule is scaled to fill its own canvas, so glycine
        # came out twice the size of methionine on the same chart. A fixed bond
        # length draws them all at one scale, the way a textbook plate does.
        # 28 is the largest bond length at which no structure gets clamped down to
        # fit its canvas. Anything larger and arginine and tryptophan shrink while
        # alanine keeps growing, which is how the scale drifted in the first place.
        o.fixedBondLength = 28
        o.centreMoleculesBeforeDrawing = True
        if not light:
            o.setSymbolColour(fg)
            o.useBWAtomPalette()
            o.setAtomPalette({-1: fg})
            o.updateAtomPalette({7: (0.36, 0.62, 0.89), 8: (0.89, 0.39, 0.37),
                                 16: (0.89, 0.69, 0.23)})
        rdMolDraw2D.PrepareAndDrawMolecule(d, m)
        d.FinishDrawing()
        open(os.path.join(sub, c3 + ".png"), "wb").write(d.GetDrawingText())


if __name__ == "__main__":
    page = check()
    print("  all 20 structures: L-configuration, molecular weights and net charges match the page")
    for light in (False, True):
        render(light)
    print("  wrote 40 structure images to aa_struct/")
