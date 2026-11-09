#!/usr/bin/env python3
"""Check the shared question bank. Guards before content, on purpose.

The format rules are the same ones the self-tests use, and they exist because a
practice set on this site was once made worthless by always making the correct
option the longest: a 17 of 18 score meant the student was reading length, not
biochemistry.

New rules for this bank:
  - every question declares `type`, which is what it asks, and the label a
    person sees (Easy, Medium, Hard) is derived from it
  - `tool` must resolve to a page that exists, because a wrong link in an
    explanation is worse than no link
  - no duplicate stem anywhere in the bank, since subjects are now mixed
  - an explanation may not simply restate the correct option
"""
import collections, json, pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parent.parent
BANKS = SITE / "tools" / "questions"
TYPES = {"recall": "Easy", "apply": "Medium", "exam": "Hard"}
fails, checked = [], 0


def bad(where, msg):
    fails.append("%-26s %s" % (where, msg))


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main():
    if not BANKS.exists():
        print("no banks yet"); return 0
    global checked
    seen_stems, id_where = {}, collections.defaultdict(list)
    per_file_idx = {}

    for f in sorted(BANKS.glob("*.json")):
        data = json.loads(f.read_text())
        qs = data.get("questions") or []
        if not qs:
            bad(f.name, "no questions"); continue
        idx = collections.Counter()
        for n, q in enumerate(qs, 1):
            checked += 1
            where = "%s q%d" % (f.stem, n)
            for key in ("subject", "type", "q", "choices", "correct", "explain"):
                if key not in q or q[key] in ("", None):
                    bad(where, "missing %r" % key)
            if q.get("type") not in TYPES:
                bad(where, "type %r is not recall, apply or exam" % q.get("type"))
            ch = q.get("choices") or []
            if len(ch) != 4:
                bad(where, "%d choices, not 4" % len(ch)); continue
            if not isinstance(q.get("correct"), int) or not 0 <= q["correct"] < 4:
                bad(where, "correct index %r out of range" % q.get("correct")); continue
            idx[q["correct"]] += 1
            lo, hi = min(len(c) for c in ch), max(len(c) for c in ch)
            # Length is only a cue when the options are long enough to read as
            # explanations. Nobody picks "Lysine" over "His" because it has more
            # letters, so applying the rule to four one-word chemical names
            # would flag correct questions and teach everyone to ignore it.
            if hi >= 15:
                if lo / hi < 0.6:
                    bad(where, "choice lengths %d to %d, too uneven" % (lo, hi))
                if len(ch[q["correct"]]) == hi and hi != lo:
                    bad(where, "the correct choice is the longest one")
            if len(set(ch)) != 4:
                bad(where, "duplicate choice")
            for field in [q["q"], q["explain"], *ch]:
                if "—" in str(field) or "–" in str(field):
                    bad(where, "uses a banned dash")
            # an explanation that is only the answer again teaches nothing
            if norm(q["explain"]) == norm(ch[q["correct"]]):
                bad(where, "the explanation just restates the answer")
            if len(q["explain"]) < 25:
                bad(where, "explanation is %d chars, too short to teach"
                    % len(q["explain"]))
            tool = (q.get("tool") or "").strip()
            if tool:
                if not tool.endswith(".html"):
                    tool += ".html"
                if not (SITE / tool).exists():
                    bad(where, "tool link %s does not exist" % tool)
            stem = norm(q["q"])
            if stem in seen_stems:
                other_file, other_q = seen_stems[stem]
                # Name BOTH files. Reporting only against whichever sorts later
                # meant an agent grepping the output for its own filename saw
                # nothing and believed the rule had passed.
                bad(where, "duplicate stem, same question is %s %s"
                    % (other_file, other_q))
                bad("%s %s" % (other_file, other_q),
                    "duplicate stem, same question is %s" % where)
            else:
                seen_stems[stem] = (f.stem, "q%d" % n)
            if q.get("id"):
                id_where[q["id"]].append(f.stem)
        per_file_idx[f.stem] = idx
        for k, v in idx.items():
            if len(qs) >= 8 and v > len(qs) * 0.5:
                bad(f.stem, "answer index %d used %d of %d times" % (k, v, len(qs)))
        if len(qs) >= 8 and len(idx) < 3:
            bad(f.stem, "only %d distinct answer positions in %d questions"
                % (len(idx), len(qs)))

    for i, where_list in id_where.items():
        if len(where_list) > 1:
            # Report under each file that holds the id, not under a bare "ids"
            # label nobody greps for.
            for w in where_list:
                bad(w, "id %s is used %d times, in %s"
                    % (i, len(where_list), ", ".join(where_list)))

    files = sorted(BANKS.glob("*.json"))
    print("\nchecked %d questions across %d subject bank(s)" % (checked, len(files)))
    dist = collections.Counter()
    for f in files:
        for q in json.loads(f.read_text())["questions"]:
            dist[q.get("type")] += 1
    print("  Easy (recall) %d · Medium (apply) %d · Hard (exam) %d"
          % (dist["recall"], dist["apply"], dist["exam"]))
    if fails:
        print("\n%d PROBLEM(S):" % len(fails))
        for x in fails:
            print("  " + x)
        return 1
    print("no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
