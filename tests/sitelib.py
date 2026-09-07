"""Shared helpers for the Volcanix site tests.

Zero dependencies: the site is plain static HTML served by GitHub Pages, so the
tests stay on the Python standard library. `html.parser` gives us enough of a
tree to assert on structure without pulling a parser into the repo.
"""

import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_ORIGIN = "https://volcanixftc.com"

# Pages that carry the full chrome: fixed nav, skyline, footer, script.js.
# Add a page here the moment it is built and the whole suite starts covering it.
CONTENT_PAGES = [
    "index.html",
    "team.html",
    "sponsors.html",
    "resources.html",
    "portfolio.html",
    "eruptions.html",
    "events.html",
]

# Pages already built. Regression tests run over these; the difference between
# this and CONTENT_PAGES is exactly the work still to do.
BUILT_PAGES = [p for p in CONTENT_PAGES if os.path.exists(os.path.join(ROOT, p))]

# Old URLs kept alive as meta-refresh stubs so inbound links never break.
REDIRECT_STUBS = {
    "about.html": "index.html",
    "contact.html": "sponsors.html",
    "outreach.html": "index.html",
    "robot.html": "portfolio.html",
    "season.html": "portfolio.html",
    "updates.html": "eruptions.html",
}

# Not part of the browsable site: 404 is served by Pages on miss, the Google
# file is a search-console token.
UNLISTED_PAGES = ["404.html", "google8b7aa737005bf562.html"]

# The canonical top nav, in order. One place to change when a page is added --
# test_pages asserts every page agrees with it, which is what stops the nav
# drifting across the eight files that now carry it.
NAV = [
    ("Home", "index.html"),
    ("Team", "team.html"),
    ("Eruptions", "eruptions.html"),
    ("Resources", "resources.html"),
    ("Sponsors", "sponsors.html"),
]

# Footer "Explore" column, same deal.
FOOTER_EXPLORE = [
    ("The Team", "team.html"),
    ("Eruptions", "eruptions.html"),
    ("Events", "events.html"),
    ("Sponsors & Finances", "sponsors.html"),
    ("Engineering Portfolio", "portfolio.html"),
    ("Resources", "resources.html"),
]

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Tags inside <svg> that self-close without a slash in some hand-written markup.
SVG_TAGS = {
    "path", "circle", "rect", "line", "polyline", "polygon", "ellipse",
    "stop", "use",
}


class Node:
    def __init__(self, tag, attrs, line, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.line = line
        self.parent = parent
        self.children = []
        self.data = []

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def has_class(self, name):
        return name in self.classes

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()

    def find_all(self, tag=None, cls=None):
        out = []
        for node in self.walk():
            if tag is not None and node.tag != tag:
                continue
            if cls is not None and not node.has_class(cls):
                continue
            out.append(node)
        return out

    def find(self, tag=None, cls=None):
        found = self.find_all(tag=tag, cls=cls)
        return found[0] if found else None

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def text(self):
        parts = list(self.data)
        for child in self.children:
            parts.append(child.text())
        return " ".join(p for p in parts if p)

    def stripped_text(self):
        return re.sub(r"\s+", " ", self.text()).strip()

    def __repr__(self):
        cls = " ".join(sorted(self.classes))
        return f"<{self.tag}{' .' + cls if cls else ''} line {self.line}>"


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, 0)
        self.stack = [self.root]
        self.comments = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.getpos()[0], self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID and tag not in SVG_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.getpos()[0], self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].data.append(data.strip())

    def handle_comment(self, data):
        self.comments.append(data)


class Page:
    """One parsed HTML file."""

    _cache = {}

    def __init__(self, name):
        self.name = name
        self.path = os.path.join(ROOT, name)
        with open(self.path, encoding="utf-8") as handle:
            self.source = handle.read()
        builder = _Builder()
        builder.feed(self.source)
        self.root = builder.root
        self.comments = builder.comments

    @classmethod
    def load(cls, name):
        if name not in cls._cache:
            cls._cache[name] = cls(name)
        return cls._cache[name]

    # -- lookups -------------------------------------------------------
    def find_all(self, tag=None, cls=None):
        return self.root.find_all(tag=tag, cls=cls)

    def find(self, tag=None, cls=None):
        return self.root.find(tag=tag, cls=cls)

    @property
    def title(self):
        node = self.find("title")
        return node.stripped_text() if node else None

    def meta(self, name):
        for node in self.find_all("meta"):
            if node.get("name") == name:
                return node.get("content")
        return None

    def prop(self, prop):
        for node in self.find_all("meta"):
            if node.get("property") == prop:
                return node.get("content")
        return None

    def link_rel(self, rel):
        for node in self.find_all("link"):
            rels = (node.get("rel") or "").split()
            if rel in rels:
                return node.get("href")
        return None

    def ids(self):
        return [n.get("id") for n in self.find_all() if n.get("id")]

    def json_ld(self):
        """Every application/ld+json block, parsed. Raises on invalid JSON."""
        blocks = []
        for node in self.find_all("script"):
            if node.get("type") == "application/ld+json":
                blocks.append(json.loads(node.text()))
        return blocks

    def nav_items(self):
        nav = self.find("ul", cls="nav-links")
        if nav is None:
            return []
        items = []
        for anchor in nav.find_all("a"):
            items.append((anchor.stripped_text(), normalise_href(anchor.get("href"))))
        return items

    def footer_explore(self):
        footer = self.find("footer")
        if footer is None:
            return []
        for column in footer.find_all("div"):
            # the heading must be a direct child, or footer-inner (which wraps
            # everything, social links included) matches first
            heading = next(
                (c for c in column.children if c.tag in ("h3", "h4")), None
            )
            if heading is not None and heading.stripped_text() == "Explore":
                return [
                    (a.stripped_text(), normalise_href(a.get("href")))
                    for a in column.find_all("a")
                ]
        return []


def normalise_href(href):
    """Reduce a link to the page it targets.

    404.html links with root-absolute paths (`/team.html`) because it is served
    from arbitrary URLs; every other page uses relative ones. Both mean the
    same page, so compare normalised.
    """
    if href is None:
        return None
    href = href.split("#")[0].split("?")[0]
    # Canonical and og:url are written absolute; reduce our own origin away so
    # they compare against a filename like every other link.
    if href.startswith(SITE_ORIGIN):
        href = href[len(SITE_ORIGIN) :]
    elif href.startswith(("http://", "https://", "mailto:", "tel:")):
        return href
    href = href.lstrip("/")
    if href in ("", "."):
        href = "index.html"
    return href


def is_external(href):
    return href.startswith(("http://", "https://", "mailto:", "tel:", "data:"))


def local_target(href):
    """Filesystem path a local href resolves to, or None if not local."""
    if href is None or is_external(href) or href.startswith("#"):
        return None
    path = href.split("#")[0].split("?")[0]
    if not path:
        return None
    if path.startswith("/"):
        path = path[1:]
    return os.path.join(ROOT, path)


def read_css():
    with open(os.path.join(ROOT, "styles.css"), encoding="utf-8") as handle:
        return handle.read()


def read_js():
    with open(os.path.join(ROOT, "script.js"), encoding="utf-8") as handle:
        return handle.read()


def built(name):
    return os.path.exists(os.path.join(ROOT, name))


def human_size(num_bytes):
    """Render a byte count the way the resource cards are expected to."""
    mb = num_bytes / (1024 * 1024)
    if mb >= 1:
        return f"{mb:.1f} MB"
    return f"{num_bytes / 1024:.0f} KB"
