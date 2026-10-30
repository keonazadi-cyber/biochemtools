#!/usr/bin/env python3
"""Check every self-test question against the page's own data.

The question banks are written by agents. An agent reporting that it verified
its own answers is the agent's word for it, which is the weakest evidence
available, so every factual answer is recomputed here from the page's data and
every format rule is enforced independently of whoever wrote the bank.

Format rules exist because a practice set on this site was once made worthless
by always making the correct option the longest one: a 17 of 18 score meant
nothing, because the student was reading length, not biochemistry.
"""
import json, pathlib, re, subprocess, sys, tempfile, os

SITE = pathlib.Path(__file__).resolve().parent.parent
BANKS = SITE / "tools" / "selftest"
fails, checked = [], 0


def bad(slug, msg):
    fails.append("%-38s %s" % (slug, msg))


def run_js(literal):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + literal + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        return json.loads(r.stdout) if not r.returncode else None
    finally:
        os.unlink(p)


def aa_rows():
    h = (SITE / "amino-acid-chart.html").read_text()
    m = re.search(r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", h)
    return {r["c3"]: r for r in run_js(m.group(1))}


def check_format(slug, bank):
    global checked
    qs = bank["questions"]
    idx = {}
    for n, q in enumerate(qs, 1):
        checked += 1
        opts = q["options"]
        if len(opts) != 4:
            bad(slug, "Q%d has %d options, not 4" % (n, len(opts)))
            continue
        if not (0 <= q["answer"] < 4):
            bad(slug, "Q%d answer index %r out of range" % (n, q["answer"]))
            continue
        idx[q["answer"]] = idx.get(q["answer"], 0) + 1
        lo, hi = min(len(o) for o in opts), max(len(o) for o in opts)
        if hi and lo / hi < 0.6:
            bad(slug, "Q%d option lengths %d to %d, too uneven" % (n, lo, hi))
        if len(opts[q["answer"]]) == hi and hi != lo:
            bad(slug, "Q%d the correct option is the longest one" % n)
        if len(set(opts)) != 4:
            bad(slug, "Q%d has a duplicate option" % n)
        for field in (q["q"], q["why"], *opts):
            if "—" in field or "–" in field:
                bad(slug, "Q%d uses a banned dash" % n)
        if not q.get("why", "").strip():
            bad(slug, "Q%d has no explanation" % n)
        if not q.get("source", "").strip():
            bad(slug, "Q%d has no source, so it cannot be verified" % n)
    for k, v in idx.items():
        if v > 3:
            bad(slug, "answer index %d used %d times, cap is 3" % (k, v))
    if len(idx) < 3:
        bad(slug, "only %d distinct answer positions used" % len(idx))
    # The whole point of the change is that the search result promises something
    # the result itself cannot contain. A page that gains a test and does not say
    # so in its title or description is carrying the cost and none of the benefit,
    # and worse, it makes the experiment unreadable: a flat result there cannot
    # tell "promising a test does not work" from "no test was promised".
    # nucleic-acid-concentration-calculator shipped exactly that way, because the
    # brief for it said to improve its calculator title rather than replace it.
    PROMISE = ("test", "quiz", "question", "check yourself", "self-test")
    blurb = (bank["title"] + " " + bank["description"]).lower()
    if not any(w in blurb for w in PROMISE):
        bad(bank["slug"], "has a self-test but neither the title nor the "
                          "description promises one, so the click never happens")
    t, d = bank["title"], bank["description"]
    if len(t) > 60:
        bad(slug, "title is %d chars" % len(t))
    if not (130 <= len(d) <= 160):
        bad(slug, "description is %d chars, want 130 to 160" % len(d))


def check_amino(bank):
    """Recompute the amino acid answers from the chart's own AA array."""
    aa = aa_rows()
    by_name = {r["name"].lower(): r for r in aa.values()}

    def row(text):
        t = text.strip().lower()
        for key, r in by_name.items():
            if key == t or r["c3"].lower() == t:
                return r
        return None

    for n, q in enumerate(bank["questions"], 1):
        src, correct = q.get("source", ""), q["options"][q["answer"]]
        # one-letter code questions
        m = re.search(r"one-letter code for (\w+)", q["q"], re.I)
        if m:
            r = row(m.group(1))
            if r and r["c1"] != correct.strip():
                bad("amino-acid-chart", "Q%d says %s for %s, chart says %s"
                    % (n, correct, r["name"], r["c1"]))
            continue
        # "which has a side chain pKa"
        if "side chain pka" in q["q"].lower():
            have = [o for o in q["options"] if (row(o) or {}).get("pkr")]
            if len(have) != 1 or have[0] != correct:
                bad("amino-acid-chart",
                    "Q%d: options with a side-chain pKa are %s, answer is %s"
                    % (n, have, correct))
            continue
        # "highest pI"
        if "highest pi" in q["q"].lower():
            rows = [(row(o), o) for o in q["options"]]
            if all(r for r, _ in rows):
                top = max(rows, key=lambda x: x[0]["pI"])[1]
                if top != correct:
                    bad("amino-acid-chart",
                        "Q%d: highest pI among the options is %s, answer is %s"
                        % (n, top, correct))
            continue
        # "most hydrophobic"
        if "hydrophobic" in q["q"].lower():
            rows = [(row(o), o) for o in q["options"]]
            if all(r for r, _ in rows):
                top = max(rows, key=lambda x: x[0]["hyd"])[1]
                if top != correct:
                    bad("amino-acid-chart",
                        "Q%d: highest hydropathy is %s, answer is %s"
                        % (n, top, correct))
            continue
        # essential, which is three-valued on this site
        if "essential" in q["q"].lower():
            yes = [o for o in q["options"] if (row(o) or {}).get("ess") == "Yes"]
            if len(yes) != 1 or yes[0] != correct:
                bad("amino-acid-chart",
                    "Q%d: options with ess=Yes are %s, answer is %s"
                    % (n, yes, correct))
            continue
        # "<Name>'s one-letter code is which of these?"
        m = re.search(r"(\w+)'s one-letter code", q["q"], re.I)
        if m:
            r = row(m.group(1))
            if r and r["c1"] != correct.strip():
                bad("amino-acid-chart", "Q%d says %s for %s, chart says %s"
                    % (n, correct, r["name"], r["c1"]))
            continue
        # "Which set does the chart list as the <Class> class?"
        m = re.search(r"as the (\w+) class", q["q"], re.I)
        if m:
            want = m.group(1).lower()
            ok = []
            for o in q["options"]:
                members = [row(x) for x in o.split(",")]
                if all(members) and all(
                        x["cls"].lower() == want for x in members):
                    ok.append(o)
            if ok != [correct]:
                bad("amino-acid-chart",
                    "Q%d: sets entirely in class %r are %s, answer is %s"
                    % (n, want, ok, correct))
            continue
        # "Three of these sit in the <Class> class. Which one does not?"
        m = re.search(r"sit in the (\w+) class.*does not", q["q"], re.I | re.S)
        if m:
            want = m.group(1).lower()
            out = [o for o in q["options"]
                   if (row(o) or {}).get("cls", "").lower() != want]
            if out != [correct]:
                bad("amino-acid-chart",
                    "Q%d: options outside class %r are %s, answer is %s"
                    % (n, want, out, correct))
            continue
        bad("amino-acid-chart",
            "Q%d could not be verified against the data (source: %s)"
            % (n, src[:60]))


# Three-letter uppercase tokens that are words, not codon attempts.
ALLOWED_TRIPLETS = {"DNA", "RNA", "ATP", "GTP", "ADP", "NAD", "FAD", "AND",
                    "THE", "ONE", "TWO", "SIX", "ALL", "NOT", "ITS", "CAN",
                    "USE", "PER", "WHY", "HOW", "ARE", "FOR", "YOU", "OUT"}


def codon_table():
    h = (SITE / "codon-chart.html").read_text()
    m = re.search(r"(?:const|var|let)\s+CODON\s*=\s*(\{[\s\S]*?\});", h)
    return run_js(m.group(1)) if m else None


def codon_info():
    """One-letter code to [three-letter, full name, class], off the same page."""
    h = (SITE / "codon-chart.html").read_text()
    m = re.search(r"(?:const|var|let)\s+INFO\s*=\s*(\{[\s\S]*?\});", h)
    return run_js(m.group(1)) if m else None


def page_start_codon():
    """The codon the page itself badges START, not the one the bank assumes."""
    h = (SITE / "codon-chart.html").read_text()
    m = re.search(r"isStart\s*=\s*cod\s*===\s*['\"]([ACGU]{3})['\"]", h)
    return m.group(1) if m else None


def check_codon(bank):
    """Recompute the codon answers from the chart's own CODON and INFO tables.

    Until now this function only checked that every triplet named in the bank
    existed somewhere on the page, which an answer pointing at the wrong option
    passes without complaint: six of the seven answers were never recomputed.
    """
    tab, info = codon_table(), codon_info()
    if not tab or not info:
        bad("codon-chart", "could not read the CODON and INFO tables off the page")
        return
    norm = {k.upper().replace("T", "U"): v for k, v in tab.items()}
    if len(norm) != 64:
        bad("codon-chart", "the page's table holds %d codons, not 64" % len(norm))

    # "Leucine (Leu)" and "Tyr, from UAC" both have to resolve to a one-letter
    # code, so build the lookup from the page's own INFO rather than a literal.
    code_of = {}
    for c1, row in info.items():
        code_of[str(row[0]).lower()] = c1
        code_of[str(row[1]).lower()] = c1
    family = {}
    for cod, aa in norm.items():
        family.setdefault(aa, []).append(cod)

    def named_aa(text):
        for tok in re.findall(r"[A-Za-z]+", text):
            if tok.lower() in code_of:
                return code_of[tok.lower()]
        return None

    def three(aa):
        return str(info[aa][0]) if aa in info else "?"

    def codons_in(text):
        return [c for c in re.findall(r"\b([ACGU]{3})\b", text.upper())]

    # The claims the stems and explanations rest on, taken from the table
    # instead of on trust: if the page's table ever changes under the bank,
    # these are the sentences that quietly stop being true.
    stops = sorted(c for c, aa in norm.items() if aa == "*")
    if stops != ["UAA", "UAG", "UGA"]:
        bad("codon-chart", "the table's stop codons are %s, the bank says "
                           "UAA, UAG, UGA" % (", ".join(stops) or "none"))
    six = sorted(three(a) for a, cs in family.items() if len(cs) == 6)
    if six != ["Arg", "Leu", "Ser"]:
        bad("codon-chart", "the table gives six codons to %s, the bank says "
                           "Leu, Ser, Arg" % (", ".join(six) or "nothing"))
    lone = sorted(three(a) for a, cs in family.items() if len(cs) == 1)
    if lone != ["Met", "Trp"]:
        bad("codon-chart", "the table gives one codon to %s, the bank says "
                           "Met, Trp" % (", ".join(lone) or "nothing"))

    for n, q in enumerate(bank["questions"], 1):
        src, correct = q.get("source", ""), q["options"][q["answer"]]
        stem = q["q"]
        text = " ".join([stem, q["why"], src, *q["options"]])

        # Match ANY three-letter uppercase token, not just [ACGU]{3}. Matching
        # only well-formed codons meant an invented one like UXG was never
        # extracted, so it was never checked: the guard silently passed it.
        for tok in sorted(set(re.findall(r"\b([A-Z]{3})\b", text))):
            if tok in ALLOWED_TRIPLETS:
                continue
            if tok.replace("T", "U") not in norm:
                bad("codon-chart", "Q%d names %s, which is neither a codon on "
                                   "the page nor an allowed word" % (n, tok))

        # every "CODON -> AA" lookup the source claims, including the shape
        # "UUA, UUG, CUU, CUC, CUA, CUG -> L (Leu)" where one arrow covers six
        for lst, aa, c3 in re.findall(
                r"((?:[ACGUT]{3}\s*,\s*)*[ACGUT]{3})\s*->\s*([A-Z*])"
                r"(?:\s*\(([A-Za-z]+)\))?", src):
            for cod in re.findall(r"[ACGUT]{3}", lst):
                rna = cod.replace("T", "U")
                if norm.get(rna) != aa:
                    bad("codon-chart", "Q%d source says %s -> %s, the table "
                        "says %s -> %s" % (n, cod, aa, rna, norm.get(rna)))
            if c3 and aa in info and c3.lower() != three(aa).lower():
                bad("codon-chart", "Q%d source calls %s %r, the table calls "
                    "it %s" % (n, aa, c3, three(aa)))

        done = False

        # "Which set lists all three stop codons?"
        if re.search(r"all three stop codons", stem, re.I):
            done = True
            for i, o in enumerate(q["options"]):
                hit = sorted(set(codons_in(o))) == stops
                if hit and i != q["answer"]:
                    bad("codon-chart", "Q%d option %r is also exactly the "
                        "table's stop set" % (n, o))
                if not hit and i == q["answer"]:
                    bad("codon-chart", "Q%d answer is %r, the table's stops "
                        "are %s" % (n, o, ", ".join(stops)))

        # "Which of these ends translation?", one codon per option
        elif re.search(r"ends translation|which .{0,20}is a stop codon",
                       stem, re.I):
            done = True
            halt = [o for o in q["options"]
                    if norm.get(o.strip().upper().replace("T", "U")) == "*"]
            if halt != [correct]:
                bad("codon-chart", "Q%d: options the table stops on are %s, "
                    "answer is %s" % (n, halt, correct))

        # "Which codon is both the start signal and the codon for methionine?"
        elif re.search(r"start (?:signal|codon)", stem, re.I):
            done = True
            start = page_start_codon()
            want = named_aa(re.sub(r".*codon for", "", stem, flags=re.I | re.S))
            if not start:
                bad("codon-chart", "Q%d asks for the start codon but the page "
                                   "badges none" % n)
            else:
                if correct.strip().upper().replace("T", "U") != start:
                    bad("codon-chart", "Q%d answers %s, the page badges %s as "
                        "START" % (n, correct, start))
                if want and norm.get(start) != want:
                    bad("codon-chart", "Q%d has the start codon giving %s, the "
                        "table gives %s -> %s" % (n, three(want), start,
                                                  three(norm.get(start))))

        # "ACU, ACC, ACA and ACG all give threonine. Which base can change?"
        elif re.search(r"which base can change", stem, re.I):
            done = True
            cods = codons_in(stem)
            m = re.search(r"all give (\w+)", stem, re.I)
            want = code_of.get(m.group(1).lower()) if m else None
            got = sorted({norm.get(c) for c in cods})
            if len(cods) < 2:
                bad("codon-chart", "Q%d names %d codons, too few to show a "
                    "wobble position" % (n, len(cods)))
            elif len(got) != 1 or (want and got != [want]):
                bad("codon-chart", "Q%d says %s all give %s, the table gives "
                    "them %s" % (n, ", ".join(cods),
                                 three(want) if want else "one amino acid",
                                 ", ".join(three(g) for g in got)))
            else:
                ORD = ["the first base", "the second base", "the third base"]
                varies = [i for i in range(3) if len({c[i] for c in cods}) > 1]
                if len(varies) != 1:
                    bad("codon-chart", "Q%d: %s vary at %d positions, so no "
                        "single base is the answer"
                        % (n, ", ".join(cods), len(varies)))
                elif correct.strip().lower() != ORD[varies[0]]:
                    bad("codon-chart", "Q%d answers %r, but %s differ only at "
                        "%s" % (n, correct, ", ".join(cods), ORD[varies[0]]))

        # "Which of these amino acids has six of them?"
        elif re.search(r"has (one|two|three|four|five|six|\d+) of them",
                       stem, re.I):
            done = True
            WORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "six": 6}
            w = re.search(r"has (one|two|three|four|five|six|\d+) of them",
                          stem, re.I).group(1).lower()
            want = WORD.get(w) or int(w)
            hits = [o for o in q["options"]
                    if len(family.get(named_aa(o) or "", [])) == want]
            if hits != [correct]:
                bad("codon-chart", "Q%d: options the table gives %d codons are "
                    "%s, answer is %s" % (n, want, hits, correct))

        # "A DNA coding-strand triplet reads TAC. Rewrite it as RNA."
        elif re.search(r"DNA.{0,30}(?:triplet|codon).{0,20}reads\s+([ACGT]{3})",
                       stem, re.I):
            done = True
            dna = re.search(
                r"DNA.{0,30}(?:triplet|codon).{0,20}reads\s+([ACGT]{3})",
                stem, re.I).group(1).upper()
            rna = dna.replace("T", "U")
            mo = re.search(r"([A-Za-z]+),\s*from\s+([ACGU]{3})", correct)
            if not mo:
                bad("codon-chart", "Q%d answer %r names no amino acid and "
                    "codon to check" % (n, correct))
            else:
                if mo.group(2).upper() != rna:
                    bad("codon-chart", "Q%d answer looks up %s, but DNA %s is "
                        "RNA %s" % (n, mo.group(2), dna, rna))
                if code_of.get(mo.group(1).lower()) != norm.get(rna):
                    bad("codon-chart", "Q%d answer calls %s %s, the table says "
                        "%s" % (n, rna, mo.group(1), three(norm.get(rna))))

        # "reads CAG from 5-prime to 3-prime. Read backwards as GAC."
        elif re.search(r"reads\s+([ACGU]{3})\s+from\s+5", stem, re.I):
            done = True
            fwd = re.search(r"reads\s+([ACGU]{3})\s+from\s+5",
                            stem, re.I).group(1).upper()
            mb = re.search(r"backwards as\s+([ACGU]{3})", stem, re.I)
            if not mb:
                bad("codon-chart", "Q%d reads %s backwards but names no "
                    "reversed codon" % (n, fwd))
            else:
                rev = mb.group(1).upper()
                if rev != fwd[::-1]:
                    bad("codon-chart", "Q%d says %s backwards is %s, it is %s"
                        % (n, fwd, rev, fwd[::-1]))
                if named_aa(correct) != norm.get(rev):
                    bad("codon-chart", "Q%d answers %s for %s, the table says "
                        "%s" % (n, correct, rev, three(norm.get(rev))))

        if not done:
            bad("codon-chart",
                "Q%d could not be verified against the data (source: %s)"
                % (n, src[:60]))

def check_nucleic(bank):
    """Recompute the A260 arithmetic from the factors the page actually uses."""
    h = (SITE / "nucleic-acid-concentration-calculator.html").read_text()
    m = re.search(r"FACTOR\s*=\s*(\{[^}]*\})", h)
    if not m:
        bad("nucleic-acid-concentration-calculator", "no FACTOR table on the page")
        return
    fac = run_js(m.group(1))
    if not fac:
        bad("nucleic-acid-concentration-calculator", "FACTOR did not parse")
        return
    for n, q in enumerate(bank["questions"], 1):
        src = q.get("source", "")
        for a, f, d, want in re.findall(
                r"([\d.]+)\s*[x\u00d7*]\s*(\d+)\s*[x\u00d7*]\s*(\d+)\s*=\s*([\d.]+)",
                src):
            got = float(a) * float(f) * float(d)
            if abs(got - float(want)) > 0.51:
                bad("nucleic-acid-concentration-calculator",
                    "Q%d source says %s x %s x %s = %s, actually %g"
                    % (n, a, f, d, want, got))
            if int(f) not in [int(v) for v in fac.values()]:
                bad("nucleic-acid-concentration-calculator",
                    "Q%d uses factor %s, page's factors are %s"
                    % (n, f, sorted(fac.values())))


def check_numbers_exist(slug, bank, page):
    """Weakest check, applied where nothing stronger exists: a number stated in
    the correct option must appear on the page, unless the question marks itself
    as derived. Catches an invented figure, which is the failure that matters."""
    h = page.read_text()
    text = re.sub(r"<[^>]+>", " ", h)
    for n, q in enumerate(bank["questions"], 1):
        if q.get("derived"):
            continue
        for num in set(re.findall(r"\b\d+(?:\.\d+)?\b",
                                  q["options"][q["answer"]])):
            if len(num) < 2:
                continue                      # single digits match everything
            if not re.search(r"(?<![\d.])" + re.escape(num) + r"(?![\d])", text):
                bad(slug, "Q%d answer states %s, which is not on the page "
                          "(mark the question \"derived\": true if computed)"
                    % (n, num))


def main():
    if not BANKS.exists():
        print("no banks yet"); return 0
    for f in sorted(BANKS.glob("*.json")):
        bank = json.loads(f.read_text())
        check_format(bank["slug"], bank)
        slug = bank["slug"]
        page = SITE / (slug + ".html")
        if slug == "amino-acid-chart":
            check_amino(bank)
        elif slug == "codon-chart":
            check_codon(bank)
        elif slug == "nucleic-acid-concentration-calculator":
            check_nucleic(bank)
            check_numbers_exist(slug, bank, page)
        else:
            # No bespoke recompute for these yet, so at minimum no invented
            # numbers. Building a checker around one page and calling the job
            # done is how two holes got through earlier today.
            check_numbers_exist(slug, bank, page)
    print("\nchecked %d questions across %d bank(s)"
          % (checked, len(list(BANKS.glob('*.json')))))
    if fails:
        print("\n%d PROBLEM(S):" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
