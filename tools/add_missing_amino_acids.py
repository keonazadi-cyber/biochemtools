#!/usr/bin/env python3
"""Put the other eight amino acids into the titration tool.

The tool shipped with 12 of 20. Nobody noticed, because the eight missing ones
all have an unionizable side chain and look boring, but `serine titration curve`
is a real thing people search for and the tool silently had no answer. The
titration pages are also the only part of the site converting properly in Search
(positions 6.0 to 11.1, CTR 1.7 to 3.1%), so the eight gaps are the cheapest
clicks available.

pKa values are read from amino-acid-chart.html, never retyped: the chart and the
tool already agree to the decimal on all twelve existing entries, and this asserts
that before touching anything.

Idempotent. Run it twice and the second run reports nothing to do.
"""
import json, re, subprocess, sys, tempfile, os, pathlib

SITE = pathlib.Path(__file__).resolve().parent.parent
TOOL = SITE / "amino-acid-titration-curve.html"
CHART = SITE / "amino-acid-chart.html"

# The order the select offers them in: unionizable side chains first, grouped the
# way a textbook introduces them, then acidic, basic, and the two odd ones out.
ORDER = ["Gly", "Ala", "Val", "Leu", "Ile", "Met", "Pro", "Phe", "Trp",
         "Ser", "Thr", "Asn", "Gln", "Asp", "Glu", "His", "Lys", "Arg",
         "Cys", "Tyr"]

LABEL = {
    "Gly": "Glycine (Gly), no ionizable side chain",
    "Ala": "Alanine (Ala), no ionizable side chain",
    "Val": "Valine (Val), no ionizable side chain",
    "Leu": "Leucine (Leu), no ionizable side chain",
    "Ile": "Isoleucine (Ile), no ionizable side chain",
    "Met": "Methionine (Met), no ionizable side chain",
    "Pro": "Proline (Pro), secondary amine, no ionizable side chain",
    "Phe": "Phenylalanine (Phe), no ionizable side chain",
    "Trp": "Tryptophan (Trp), no ionizable side chain",
    "Ser": "Serine (Ser), hydroxyl side chain, not ionizable",
    "Thr": "Threonine (Thr), hydroxyl side chain, not ionizable",
    "Asn": "Asparagine (Asn), amide side chain, not ionizable",
    "Gln": "Glutamine (Gln), amide side chain, not ionizable",
    "Asp": "Aspartate (Asp), acidic side chain",
    "Glu": "Glutamate (Glu), acidic side chain",
    "His": "Histidine (His), basic side chain",
    "Lys": "Lysine (Lys), basic side chain",
    "Arg": "Arginine (Arg), basic side chain",
    "Cys": "Cysteine (Cys), thiol side chain",
    "Tyr": "Tyrosine (Tyr), phenol side chain",
}


def run_js(literal):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + literal + ";console.log(JSON.stringify(A))")
        path = f.name
    try:
        r = subprocess.run(["node", path], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:300])
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def chart_rows():
    m = re.search(r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", CHART.read_text())
    return {r["c3"]: r for r in run_js(m.group(1))}


def main():
    html = TOOL.read_text()
    chart = chart_rows()
    m = re.search(r"const AA=(\{[\s\S]*?\});", html)
    if not m:
        print("FAIL could not find the AA table in the tool"); return 1
    tool = run_js(m.group(1))

    # The tool and the chart are two hand-maintained copies of the same numbers.
    # If they have drifted, stop: adding eight more rows to a table that already
    # disagrees with itself would bake the disagreement in.
    for code, groups in tool.items():
        row = chart[code]
        want = sorted(v for v in (row["pk1"], row["pk2"], row["pkr"]) if v is not None)
        got = sorted(g["pka"] for g in groups)
        if want != got:
            print("FAIL %s: tool says %s, chart says %s" % (code, got, want))
            return 1

    missing = [c for c in ORDER if c not in tool]
    if not missing:
        print("all 20 amino acids are already in the tool, nothing to do")
        return 0
    print("adding: " + ", ".join(missing))

    for code in missing:
        row = chart[code]
        if row["pkr"] is not None:
            # Every one of the eight is a plain two-group case. If that ever stops
            # being true the prose and the pI maths below would both need thought.
            print("FAIL %s has an ionizable side chain, not a drop-in" % code)
            return 1
        tool[code] = [{"pka": row["pk1"], "t": "a"}, {"pka": row["pk2"], "t": "b"}]

    body = "\n".join(
        " %s:[%s]," % (c, ",".join(
            '{pka:%.2f,t:"%s"}' % (g["pka"], g["t"]) for g in tool[c]))
        for c in ORDER)
    table = "const AA={\n" + body.rstrip(",") + "}"
    html = html[:m.start()] + table + html[m.end() - 1:]

    options = "\n".join('   <option value="%s">%s</option>' % (c, LABEL[c])
                        for c in ORDER)
    html, n = re.subn(r'(<select id="aa">)[\s\S]*?(\s*</select>)',
                      lambda mm: mm.group(1) + "\n" + options + mm.group(2),
                      html, count=1)
    if n != 1:
        print("FAIL could not rewrite the <select>"); return 1

    TOOL.write_text(html)

    # Prove it, by re-reading what was written rather than trusting the edit.
    back = run_js(re.search(r"const AA=(\{[\s\S]*?\});", TOOL.read_text()).group(1))
    assert len(back) == 20, "wrote %d amino acids, not 20" % len(back)
    opts = re.findall(r'<option value="(\w+)"', TOOL.read_text())
    assert opts == ORDER, "the select is out of order: %s" % opts
    print("tool now offers all 20, select and data agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
