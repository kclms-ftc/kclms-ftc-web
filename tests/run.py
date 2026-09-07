#!/usr/bin/env python3
"""Run the Volcanix site checks.

Two suites, reported separately:

  REGRESSION (test_*.py)  invariants the site already satisfies. These must stay
                          green -- they are what protects the parts that are
                          good right now.

  SPEC (spec_*.py)        contracts for the pages that are planned but not built
                          (updates, events, reworked resources). These are red
                          until the build lands. That is the point.

    python3 tests/run.py            both suites
    python3 tests/run.py regression only the green-now suite
    python3 tests/run.py spec       only the not-built-yet suite
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def build(pattern):
    return unittest.defaultTestLoader.discover(HERE, pattern=pattern, top_level_dir=HERE)


def run(label, pattern, blurb):
    print(f"\n\033[1m=== {label} ===\033[0m  {blurb}")
    result = unittest.TextTestRunner(verbosity=2).run(build(pattern))
    return result


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = {}

    if which in ("all", "regression"):
        results["regression"] = run(
            "REGRESSION", "test_*.py", "must be green"
        )
    if which in ("all", "spec"):
        results["spec"] = run(
            "SPEC", "spec_*.py", "red until the new pages are built"
        )

    print("\n\033[1m=== SUMMARY ===\033[0m")
    for label, result in results.items():
        total = result.testsRun
        bad = len(result.failures) + len(result.errors)
        state = "PASS" if bad == 0 else f"{bad} failing"
        print(f"  {label:<11} {total - bad}/{total} passing   {state}")

    # Only the regression suite gates the exit code. A red spec suite is the
    # expected state before the build, so it must not look like a broken repo.
    regression = results.get("regression")
    if regression is not None and not regression.wasSuccessful():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
