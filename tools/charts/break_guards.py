#!/usr/bin/env python3
"""Break a chart generator's guards on purpose and prove the build dies.

Every generator on the kit reads its numbers out of the site's own pages and
asserts them. That is only worth anything if the asserts actually fire, and a
guard that never fires looks exactly like a guard that never runs.

This mutates one source page IN MEMORY (no file is touched), runs the generator,
and patches Image.save to raise, so a chart that gets drawn anyway is loud rather
than silent. Three outcomes:

    caught      the guard fired. What you want.
    NOT CAUGHT  the generator drew a chart from the mutated page. A real hole.
    no target   the mutation string is not on that page any more; fix the table.

Run every mutation:        python3 break_guards.py
One generator:             python3 break_guards.py physiology
An ad-hoc mutation:        python3 break_guards.py make_physiology_guide.py \
                               oxygen-dissociation-curve-calculator.html "26.6" "28.1"

Written after a guard added to deploy_charts.py resolved zero of fifteen
generators and reported "no problems found" for all of them. See
Vault/Biochemtools/Chart Kit 2026-11-09.md.
"""
import builtins
import io
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

# Mutations proven to be caught. Each is (generator, page, old, new).
# Pick a mutation that is WRONG rather than malformed where you can, and on a
# different shape from the one the guard was written around.
MUTATIONS = [
    # Adult hemoglobin's P50, which physiology asserts before it plots.
    ("make_physiology_guide.py", "oxygen-dissociation-curve-calculator.html",
     "p50:26.6", "p50:28.1"),
    # Tyrosine's side chain pKa. Curves solves every pI from these and checks
    # each against the published value, so one wrong pKa must fail.
    ("make_curves_guide.py", "amino-acid-chart.html",
     "pkr:10.07", "pkr:9.07"),
    # Arginine's, on the same page but reached by a different generator that
    # also fits acidic vs basic character from it.
    ("make_mcat_highyield_guide.py", "amino-acid-chart.html",
     "pkr:12.48", "pkr:11.48"),
]


def run(generator, target, old, new):
    """Run `generator` with `target` mutated in memory. Return the outcome."""
    gen_path = os.path.join(HERE, generator)
    if not os.path.exists(gen_path):
        return "no such generator: %s" % generator
    src = io.open(gen_path, encoding="utf-8").read()
    real_open = builtins.open
    seen = {"target": False}

    def fake_open(path, *a, **kw):
        f = real_open(path, *a, **kw)
        if isinstance(path, str) and path.endswith(target) and "b" not in kw.get("mode", ""):
            text = f.read()
            f.close()
            if old not in text:
                raise LookupError("mutation target %r is not on %s" % (old, target))
            seen["target"] = True
            return io.StringIO(text.replace(old, new, 1))
        return f

    def boom(*a, **k):
        raise RuntimeError("drew and saved a chart from the mutated page")

    saved_save = Image.Image.save
    builtins.open = fake_open
    Image.Image.save = boom
    try:
        exec(compile(src, gen_path, "exec"),
             {"__name__": "__break_guards__", "__file__": gen_path})
    except LookupError as e:
        return "no target: %s" % e
    except AssertionError as e:
        msg = str(e).replace("\n", " ")[:72]
        return "caught: %s" % (msg or "assert fired with no message")
    except RuntimeError as e:
        return "NOT CAUGHT, %s" % e
    except SystemExit:
        return "caught: generator exited"
    finally:
        builtins.open = real_open
        Image.Image.save = saved_save
    if not seen["target"]:
        return "no target: the generator never opened %s" % target
    return "NOT CAUGHT, generator finished without drawing or asserting"


def main(argv):
    if len(argv) == 5:
        rows = [(argv[1], argv[2], argv[3], argv[4])]
    else:
        want = argv[1] if len(argv) > 1 else None
        rows = [m for m in MUTATIONS if not want or want in m[0]]
        if not rows:
            print("no mutations match %r" % want)
            return 2
    bad = 0
    for generator, target, old, new in rows:
        out = run(generator, target, old, new)
        if not out.startswith("caught"):
            bad += 1
        print("  %-32s %s -> %s" % (generator, old, new))
        print("    %s" % out)
    print("\n  %d mutation(s), %d not caught" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
