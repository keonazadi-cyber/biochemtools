#!/usr/bin/env python3
"""Lift the 80 daily questions into one shared bank, with a level on each.

Two systems existed and neither could feed the other. quiz.html generated recall
drills from the 20-row amino acid table, which is finite: learn twenty codes and
it is over, which is exactly why it reads as too easy. daily-question.html had
the real asset, an 80-question bank with explanations and tool links, served at
random with no notion of difficulty.

Merging them is what makes a level picker, a subject picker, a mixed mode and a
practice test possible at all.

THE ANTI-DRIFT RULE, in the data model rather than in a comment:

  Each question stores `type`, which is what it ASKS of you. The label a person
  sees is DERIVED from it.

      recall -> Easy      a single lookup, no arithmetic, no scenario
      apply  -> Medium    apply a rule or do a calculation on given values
      exam   -> Hard      a stem with a scenario, distractors from real errors

  Storing both would let them disagree the first time someone edited one. Plain
  Easy/Medium/Hard with nothing behind it rots as a bank grows, because nobody
  can say where the boundary is. This way the boundary is the definition.

  Known limit, accepted on purpose: an obscure fact cannot be Hard under this
  model, because recall is Easy by construction. If that need turns up, add an
  explicit `level` override WITH a reason field, so the exception is visible.

Classification here is by stated signal, not by feel, and anything the signals
cannot decide is printed for a human rather than silently assigned.
"""
import json, os, re, subprocess, sys, tempfile, pathlib, collections

SITE = pathlib.Path(__file__).resolve().parent.parent
OUT = SITE / "tools" / "questions"

SCENARIO = re.compile(
    r"\b(a patient|a student|a researcher|you (?:have|are|run|measure|add|prepare|dilute)|"
    r"in (?:a|the) lab|a sample|a culture|suppose|during|after (?:adding|running)|"
    r"best explains|most likely|which of the following best)\b", re.I)
# "what's the concentration in tube 3" and "if you set a Tris buffer to pH 8.00
# at 25C" are both calculations and both slipped the first version: one used the
# apostrophe form, the other states the task as a conditional rather than a verb.
CALC = re.compile(
    r"(?:\b(?:calculate|how much|how many|what volume|what fraction|"
    r"what percent|odds of)\b"
    r"|what(?:'|\u2019)?s? the (?:net charge|concentration|pH|pI|ratio|yield|total)"
    r"|\bif you (?:set|have|add|dilute|run|measure)\b)", re.I)
NUMERIC = re.compile(r"\d")
UNITS = re.compile(r"\b(mL|µL|uL|mg|µg|ng|mM|µM|nM|M\b|g/mol|mmHg|kJ|ATP|%)\b")


def classify(q):
    """Return (type, why). Signals only; no judgement calls."""
    text = q["q"]
    if SCENARIO.search(text):
        return "exam", "scenario marker in the stem"
    if CALC.search(text) and (NUMERIC.search(text) or UNITS.search(text)):
        return "apply", "calculation verb plus a number or a unit"
    if CALC.search(text):
        return "apply", "calculation verb"
    if NUMERIC.search(text) and UNITS.search(text):
        return "apply", "numbers with units in the stem"
    return "recall", "no calculation and no scenario"


def run_js(literal):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + literal + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        return json.loads(r.stdout) if not r.returncode else None
    finally:
        os.unlink(p)


SLUG = {"Biochemistry": "biochemistry", "Chemistry": "chemistry",
        "Metabolism": "metabolism", "Molecular biology": "molecular-biology",
        "Genetics": "genetics", "Physiology": "physiology",
        "Solutions": "solutions"}


def main():
    h = (SITE / "daily-question.html").read_text()
    m = re.search(r"const\s+BANK\s*=\s*(\[[\s\S]*?\n\s*\]);", h)
    if not m:
        print("  FAIL could not find BANK in daily-question.html"); return 1
    bank = run_js(m.group(1))
    if not bank:
        print("  FAIL BANK did not parse"); return 1
    print("  read %d questions from daily-question.html" % len(bank))

    OUT.mkdir(parents=True, exist_ok=True)
    by_subject, why_counts, borderline = collections.defaultdict(list), collections.Counter(), []
    for i, q in enumerate(bank):
        subj = q.get("topic") or "Biochemistry"
        slug = SLUG.get(subj)
        if slug is None:
            print("  FAIL unknown topic %r, add it to SLUG" % subj); return 1
        t, why = classify(q)
        why_counts[why] += 1
        # the daily bank stores a slug, sometimes with the extension and
        # sometimes without; normalise to the filename and prove it resolves
        tool = (q.get("tool") or "").strip()
        if tool:
            if not tool.endswith(".html"):
                tool += ".html"
            if not (SITE / tool).exists():
                print("  FAIL q%d links tool %r which does not exist" % (i, tool))
                return 1
        rec = {"id": "%s-%03d" % (slug[:4], len(by_subject[slug]) + 1),
               "subject": subj, "type": t, "q": q["q"], "choices": q["choices"],
               "correct": q["correct"], "explain": q["explain"],
               "tool": tool, "origin": "daily-question bank, migrated 2026-11-09",
               "classified_by": why}
        by_subject[slug].append(rec)
        # a short stem with a number but no verb is the ambiguous case
        if t == "recall" and NUMERIC.search(q["q"]):
            borderline.append((subj, q["q"][:88]))

    total = 0
    for slug, rows in sorted(by_subject.items()):
        (OUT / (slug + ".json")).write_text(
            json.dumps({"subject": rows[0]["subject"], "questions": rows},
                       indent=1, ensure_ascii=False))
        total += len(rows)
        dist = collections.Counter(r["type"] for r in rows)
        print("  %-20s %2d questions  recall %-2d apply %-2d exam %-2d"
              % (slug, len(rows), dist["recall"], dist["apply"], dist["exam"]))
    if total != len(bank):
        print("  FAIL migrated %d of %d" % (total, len(bank))); return 1
    print("\n  all %d carried over, nothing lost" % total)
    print("  classified by: %s" % dict(why_counts))
    if borderline:
        print("\n  %d call for a human look (recall, but the stem has a number):"
              % len(borderline))
        for s, q in borderline[:12]:
            print("     [%s] %s" % (s, q))
    return 0


if __name__ == "__main__":
    sys.exit(main())
