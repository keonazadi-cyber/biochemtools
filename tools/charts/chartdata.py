#!/usr/bin/env python3
"""Pull chart data straight out of the live tool pages.

Six chart scripts used to load cached JSON from a temp scratch directory. That
directory gets cleaned, so five of the six datasets vanished and those charts
could not be rebuilt at all, which is a bad place to be when a claim on one of
them turns out to be wrong.

Everything now comes from the HTML that ships. The chart cannot drift from the
page, and the build works on any machine with the repo checked out.
"""
import json, os, re, subprocess, tempfile

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def _js(literal):
    """Evaluate a JS array/object literal and return it as Python."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const X=" + literal.rstrip().rstrip(";") + ";console.log(JSON.stringify(X))")
        path = f.name
    try:
        r = subprocess.run(["node", path], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("could not evaluate JS literal: " + r.stderr[:300])
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def _grab(page, name, opener="["):
    """Find `name = [...]` or `name = {...}` in a page and return the value.

    Brace-matched rather than regex-terminated. An earlier regex version needed a
    newline before the closing brace and silently failed on the codon table,
    which puts its closer at the end of the last data line.
    """
    closer = "]" if opener == "[" else "}"
    h = open(os.path.join(SITE, page), encoding="utf-8").read()
    m = re.search(r"\b%s\s*=\s*\%s" % (re.escape(name), opener), h)
    if not m:
        raise RuntimeError("%s not found in %s" % (name, page))
    i = m.end() - 1
    depth, j, instr, esc = 0, i, None, False
    while j < len(h):
        c = h[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == instr:
                instr = None
        elif c in "'\"":
            instr = c
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return _js(h[i:j + 1])
        j += 1
    raise RuntimeError("%s in %s is never closed" % (name, page))


SUP = {"0":"\u2070","1":"\u00b9","2":"\u00b2","3":"\u00b3","4":"\u2074","5":"\u2075",
       "6":"\u2076","7":"\u2077","8":"\u2078","9":"\u2079","+":"\u207a","-":"\u207b",
       "\u2212":"\u207b","(":"\u207d",")":"\u207e","n":"\u207f","i":"\u2071"}


def plain(t):
    """Turn a page's inline HTML into the plain text a Pillow chart can draw.

    Superscripts become real Unicode superscripts, so H<sup>+</sup> reads H+ with a
    raised plus the way it does on the page. Subscripts are flattened instead,
    because the Unicode subscript letters are missing from the chart font and would
    render as empty boxes. Ka stays Ka rather than becoming a blank.
    """
    import html as H

    def sup(m):
        inner = H.unescape(m.group(1))
        if all(c in SUP for c in inner):
            return "".join(SUP[c] for c in inner)
        return "^" + inner

    t = re.sub(r"<sup>(.*?)</sup>", sup, t)
    t = re.sub(r"<sub>(.*?)</sub>", lambda m: H.unescape(m.group(1)), t)
    t = re.sub(r"<[^>]+>", "", t)
    return H.unescape(t)


def _clean(rows):
    """Apply plain() to every string in a nested list/dict structure.

    Every extractor runs through this. A chart draws with Pillow, which has no idea
    what an HTML tag is, so anything left as markup prints literally: the equation
    sheet briefly shipped reading "K<sub>a</sub> &times; K<sub>b</sub>". The assert
    below is what makes that impossible rather than merely unlikely.
    """
    if isinstance(rows, str):
        out = plain(rows)
        # A bare "<" is fine, some notes legitimately say "Q < K". What must not
        # survive is an actual tag or an undecoded entity.
        assert not re.search(r"</?[a-zA-Z][^>]*>|&[a-zA-Z]+;|&#\d+;", out), \
            "markup survived into chart text: %r" % out
        return out
    if isinstance(rows, list):
        return [_clean(r) for r in rows]
    if isinstance(rows, dict):
        return {k: _clean(v) for k, v in rows.items()}
    return rows


def tca():
    return _clean(_grab("citric-acid-cycle-explorer.html", "STEPS"))


def transport():
    return _clean(_grab("membrane-transport-explorer.html", "MODES", opener="{"))


def catabolism():
    return _clean(_grab("amino-acid-catabolism-explorer.html", "AA"))


def amino_acids():
    return _clean(_grab("amino-acid-chart.html", "AA"))


def equations():
    return _clean(_grab("biochem-equation-sheet.html", "EQ"))


def codons():
    return _clean(_grab("codon-chart.html", "CODON", opener="{"))


def buffers():
    """Buffer rows, with a family tag appended for the polyprotic ones.

    The chart draws polyprotic buffers as a single row with one segment per pKa,
    so it needs to know which rows belong together. The page already encodes
    that in the names ("Citric acid (pKa1)", "Citrate (pKa2)"), so the family is
    derived from the name rather than kept in a second list that could drift.
    """
    ALIAS = {"phosphoric acid": "phosphate", "citric acid": "citrate"}
    rows, fams = [], {}
    for r in _grab("buffer-pka-table.html", "BUF"):
        m = re.match(r"^(.*?)\s*\(pKa\d\)$", r[0])
        fam = ""
        if m:
            base = m.group(1).strip().lower()
            fam = ALIAS.get(base, base)
            fams[fam] = fams.get(fam, 0) + 1
        rows.append(_clean(list(r)) + [fam])
    assert fams == {"phosphate": 3, "citrate": 3, "glycine": 2, "succinate": 2,
                    "piperazine": 2, "carbonate": 2}, \
        "polyprotic grouping changed on the page: %r" % (fams,)
    return rows


def blood_grid():
    """Derived, not extracted. The ABO model is the source of truth."""
    from itertools import product
    GENO = {"A": ["AA", "AO"], "B": ["BB", "BO"], "AB": ["AB"], "O": ["OO"]}
    order = ["A", "B", "AB", "O"]

    def pheno(g):
        s = set(g)
        if s == {"A"} or s == {"A", "O"}: return "A"
        if s == {"B"} or s == {"B", "O"}: return "B"
        if s == {"A", "B"}: return "AB"
        return "O"

    grid = {}
    for p1 in order:
        for p2 in order:
            poss = set()
            for g1 in GENO[p1]:
                for g2 in GENO[p2]:
                    poss |= {pheno("".join(sorted(c, key="ABO".index))) for c in product(g1, g2)}
            grid[p1 + "x" + p2] = sorted(poss, key=order.index)
    return grid


if __name__ == "__main__":
    for name, fn in [("tca", tca), ("transport", transport), ("catabolism", catabolism),
                     ("amino_acids", amino_acids), ("equations", equations),
                     ("codons", codons), ("buffers", buffers), ("blood_grid", blood_grid)]:
        try:
            d = fn()
            print("  ok    %-12s %d entries" % (name, len(d)))
        except Exception as e:
            print("  FAIL  %-12s %s" % (name, e))
