#!/usr/bin/env python3
"""Run the generators in the one order that works, then audit.

The order is not cosmetic. build_titration_pages.py rewrites each curve page from
the tool's own markup, which throws away anything added to the page afterwards.
On 2026-10-29 that silently stripped the suggestions ask line off all twenty curve
pages; the audit caught it, but only because someone happened to run the audit.
Encoding the order here means it cannot be got wrong by remembering it wrong.

Generators first, decorations second, schema last, audit at the end.
"""
import subprocess, sys, os, pathlib

HERE = pathlib.Path(__file__).resolve().parent

STEPS = [
    # page content, which rewrites pages wholesale
    ("add_missing_amino_acids.py", "all 20 amino acids are in the tool"),
    ("render_titration_png.py", "a real PNG per curve, for image search"),
    ("build_titration_pages.py", "the curve pages themselves"),
    ("prerender_chart_rows.py", "the chart's rows exist without JavaScript"),
    # the self-test goes in before the decorations, because it injects at the
    # top of <main> while they append at the bottom of it
    ("build_selftest.py", "a test on the pages that rank but get no clicks"),
    ("check_selftest.py", "every answer recomputed from the page's own data"),
    # things added on top of a finished page, so they must come after it
    ("add_feedback_line.py", "the ask line"),
    ("add_suggest_footer_link.py", "the footer link"),
    # discovery and schema, which read the finished pages
    ("sitemap_images.py", "declare each image on the page that shows it"),
    ("normalize_schema.py", "each page claims its own image, and only its own identity"),
]


def main():
    argv = sys.argv[1:]
    failed = []
    for script, why in STEPS:
        path = HERE / script
        if not path.exists():
            print("SKIP  %-32s (not in tools/)" % script)
            continue
        print("\n--- %s  (%s)" % (script, why))
        r = subprocess.run([sys.executable, str(path)], cwd=str(HERE.parent))
        if r.returncode:
            failed.append(script)
            print("FAILED: %s exited %d" % (script, r.returncode))
            break
    if failed:
        print("\nbuild stopped at %s, audit not run" % failed[0])
        return 1
    print("\n--- audit.py")
    r = subprocess.run([sys.executable, str(HERE / "audit.py")],
                       cwd=str(HERE.parent))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
