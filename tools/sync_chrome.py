#!/usr/bin/env python3
"""Copy the shared nav and footer into every page.

There is no templating here and no build step, so the nav and footer are
duplicated into every HTML file by hand. The issue-5 notes already flagged the
cost: "every nav change costs six files", and it is about to be nine. This
script makes the duplication mechanical instead of manual.

    tools/nav.html      the one true nav
    tools/footer.html   the one true footer

Both partials use root-absolute links (/team.html), so a single identical block
works on every page including 404.html, which is served from arbitrary URLs.
The active-link highlight in script.js compares basenames, so it still works.

First run replaces each page's existing <nav>/<footer> and leaves markers
behind. Later runs just replace what is between the markers.

    python3 tools/sync_chrome.py            write the changes
    python3 tools/sync_chrome.py --check    exit 1 if anything is out of date
"""

import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "index.html",
    "team.html",
    "eruptions.html",
    "events.html",
    "resources.html",
    "sponsors.html",
    "portfolio.html",
    "404.html",
] + sorted(
    os.path.relpath(p, ROOT)
    for p in glob.glob(os.path.join(ROOT, "eruptions", "*.html"))
)

BLOCKS = [
    {
        "name": "NAV",
        "partial": "tools/nav.html",
        "element": re.compile(r"[ \t]*<nav class=\"topnav\">.*?</nav>\n", re.S),
    },
    {
        "name": "FOOTER",
        "partial": "tools/footer.html",
        "element": re.compile(r"[ \t]*<footer class=\"footer\">.*?</footer>\n", re.S),
    },
]


def marker_pattern(name):
    return re.compile(
        rf"[ \t]*<!-- {name}:START -->.*?<!-- {name}:END -->\n", re.S
    )


def wrap(name, partial):
    return (
        f"    <!-- {name}:START -->\n"
        f"{partial.rstrip(chr(10))}\n"
        f"    <!-- {name}:END -->\n"
    )


def sync_page(name, partials, check=False):
    path = os.path.join(ROOT, name)
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    original = source

    for block in BLOCKS:
        replacement = wrap(block["name"], partials[block["name"]])
        markers = marker_pattern(block["name"])
        if markers.search(source):
            source = markers.sub(lambda _: replacement, source, count=1)
        elif block["element"].search(source):
            source = block["element"].sub(lambda _: replacement, source, count=1)
        else:
            print(f"  ! {name}: no {block['name']} block found, skipped")

    if source == original:
        return False
    if not check:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="report drift without writing"
    )
    args = parser.parse_args(argv)

    partials = {}
    for block in BLOCKS:
        with open(os.path.join(ROOT, block["partial"]), encoding="utf-8") as handle:
            partials[block["name"]] = handle.read()

    changed = []
    for name in PAGES:
        if sync_page(name, partials, check=args.check):
            changed.append(name)

    if args.check:
        if changed:
            print("Out of date: " + ", ".join(changed))
            print("Run tools/sync-nav.sh to fix.")
            return 1
        print("All pages match the shared nav and footer.")
        return 0

    if changed:
        print("Updated: " + ", ".join(changed))
    else:
        print("Already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
