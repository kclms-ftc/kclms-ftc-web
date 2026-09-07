"""Classes in the markup are backed by something real.

There is no build step and no linter here, so a typo in a class name fails
silently: the element just renders unstyled. A class counts as real if
styles.css selects it or script.js touches it.
"""

import glob
import os
import re
import unittest

import sitelib as S

ALL_HTML = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(S.ROOT, "*.html"))
)

# Applied at runtime by the hunt/arcade code via string building, so they never
# appear as literals in either file.
DYNAMIC_PREFIXES = ("hunt-", "arcade-", "codex-", "rps-", "simon-", "whack-")


def css_classes():
    css = S.read_css()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return set(re.findall(r"\.(-?[_a-zA-Z][\w-]*)", css))


def js_classes():
    js = S.read_js()
    return set(re.findall(r"[\"'`]([-\w ]+)[\"'`]", js))


class TestCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.known = css_classes()
        for chunk in js_classes():
            cls.known.update(chunk.split())

    def test_every_class_is_backed_by_css_or_js(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for node in page.find_all():
                for token in node.classes:
                    if token.startswith(DYNAMIC_PREFIXES):
                        continue
                    with self.subTest(page=name, line=node.line, cls=token):
                        self.assertIn(
                            token,
                            self.known,
                            f"{name}:{node.line} class \"{token}\" is styled nowhere",
                        )

    def test_stylesheet_and_script_exist(self):
        self.assertTrue(os.path.exists(os.path.join(S.ROOT, "styles.css")))
        self.assertTrue(os.path.exists(os.path.join(S.ROOT, "script.js")))

    def test_design_tokens_are_defined(self):
        """The palette is the scheme. Every new page has to build from these,
        not from fresh hex codes."""
        css = S.read_css()
        for token in (
            "--black", "--coal", "--panel", "--line", "--cream", "--yellow",
            "--amber", "--orange", "--red", "--red-deep", "--maroon",
            "--display", "--body", "--serif", "--stamp",
        ):
            with self.subTest(token=token):
                self.assertIn(f"{token}:", css, f"{token} is no longer defined")

    def test_no_raw_hex_colours_in_markup(self):
        """Inline styles are used for sticker placement; they must not introduce
        colours outside the palette."""
        for name in ALL_HTML:
            page = S.Page.load(name)
            for node in page.find_all():
                style = node.get("style") or ""
                if not style:
                    continue
                with self.subTest(page=name, line=node.line):
                    self.assertNotRegex(
                        style,
                        r"#[0-9a-fA-F]{3,8}",
                        f"{name}:{node.line} hard-codes a colour; use a token",
                    )


if __name__ == "__main__":
    unittest.main()
