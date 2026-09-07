#!/usr/bin/env python3
"""Regenerate the updates index, the RSS feed and the sitemap from the posts.

The posts in eruptions/ are the single source of truth. This reads them and
rewrites everything that has to agree with them, so the index can never drift
from the files and the feed can never miss a post.

    python3 tools/rebuild_eruptions.py           write
    python3 tools/rebuild_eruptions.py --check   exit 1 if anything is stale

Run it after adding a post (by hand or via tools/docx2post.py).
"""

import argparse
import datetime
import email.utils
import glob
import html
import os
import re
import sys

from docx2post import image_size

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "https://volcanixftc.com"
INDEX_PAGE = os.path.join(ROOT, "eruptions.html")
FEED = os.path.join(ROOT, "eruptions.xml")
SITEMAP = os.path.join(ROOT, "sitemap.xml")

TAG_LABELS = {
    "build": "Build",
    "outreach": "Outreach",
    "competition": "Competition",
    "funding": "Funding",
}

# Pages that are not posts but still belong in the sitemap.
CORE_PAGES = [
    ("", "weekly", "1.0"),
    ("portfolio.html", "monthly", "0.9"),
    ("eruptions.html", "weekly", "0.9"),
    ("team.html", "monthly", "0.8"),
    ("resources.html", "monthly", "0.8"),
    ("events.html", "monthly", "0.7"),
    ("sponsors.html", "monthly", "0.7"),
]


def field(source, pattern, default=""):
    match = re.search(pattern, source, re.S)
    return match.group(1).strip() if match else default


def read_posts():
    posts = []
    for path in sorted(glob.glob(os.path.join(ROOT, "eruptions", "*.html"))):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        slug = os.path.splitext(os.path.basename(path))[0]
        date = field(source, r'<time datetime="(\d{4}-\d{2}-\d{2})"')
        if not date:
            print(f"  ! {slug}: no dated <time>, skipped")
            continue
        image = field(source, r'<meta property="og:image" content="([^"]+)"')
        posts.append(
            {
                "image": image.replace(ORIGIN + "/", ""),
                "alt": field(source, r'<figure class="post-figure">\s*<img src="[^"]*" alt="([^"]*)"'),
                "slug": slug,
                "date": date,
                "date_label": field(source, r"<time datetime=\"[^\"]+\">([^<]+)</time>"),
                "title": field(source, r"<h1>(.*?)</h1>"),
                "summary": field(source, r'<meta name="description" content="(.*?)"'),
                "tag": field(source, r'class="post" id="[^"]*" data-tag="([^"]+)"'),
                "url": f"{ORIGIN}/eruptions/{slug}.html",
            }
        )
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def short_month(date):
    return datetime.date.fromisoformat(date).strftime("%b %Y")


def render_featured(posts):
    """The newest post, shown large at the top of eruptions.html."""
    if not posts:
        return (
            '        <p class="resource-empty">The first update goes up after our '
            "next milestone.</p>"
        )
    post = posts[0]
    # The photo repeats a link the title already provides, so it is decorative
    # for anyone using a screen reader and hidden from the tab order.
    width, height = image_size(os.path.join(ROOT, post["image"]))
    dims = f' width="{width}" height="{height}"' if width and height else ""
    return "\n".join([
        '        <article class="featured-post">',
        f'            <a class="featured-media" href="eruptions/{post["slug"]}.html" tabindex="-1" aria-hidden="true">',
        f'                <img src="{post["image"]}" alt="" aria-hidden="true"{dims} loading="lazy">',
        "            </a>",
        '            <div class="featured-body">',
        f'                <p class="post-date"><time datetime="{post["date"]}">'
        f'{short_month(post["date"])}</time> &middot; Latest eruption</p>',
        f'                <h3><a href="eruptions/{post["slug"]}.html">{post["title"]}</a></h3>',
        f'                <p>{html.escape(post["summary"], quote=False)}</p>',
        f'                <a href="eruptions/{post["slug"]}.html" class="btn solid">'
        "<span>Read the Full Post</span></a>",
        "            </div>",
        "        </article>",
    ])


def render_index(posts):
    posts = posts[1:]
    if not posts:
        return (
            '        <p class="resource-empty">Nothing older yet. This is the '
            "first update.</p>"
        )
    rows = ['        <div class="rows update-index">']
    for post in posts:
        rows.append(f'            <div class="row-item" data-tag="{post["tag"]}">')
        rows.append(f'                <span class="row-label">{short_month(post["date"])}</span>')
        rows.append(
            f'                <h3><a href="eruptions/{post["slug"]}.html">{post["title"]}</a></h3>'
        )
        rows.append(
            f'                <p>{html.escape(post["summary"], quote=False)}'
            f'<span class="update-read">Read the full post &rarr;</span></p>'
        )
        rows.append("            </div>")
    rows.append("        </div>")
    return "\n".join(rows)


def render_chips(posts):
    used = []
    for post in posts:
        if post["tag"] and post["tag"] not in used:
            used.append(post["tag"])
    out = [
        '        <div class="chips" role="group" aria-label="Filter updates by topic">',
        '            <button type="button" class="chip" data-filter="all" aria-pressed="true"><span>All</span></button>',
    ]
    for tag in used:
        label = TAG_LABELS.get(tag, tag.title())
        out.append(
            f'            <button type="button" class="chip" data-filter="{tag}" '
            f'aria-pressed="false"><span>{label}</span></button>'
        )
    out.append("        </div>")
    return "\n".join(out)


def replace_marked(source, name, block):
    """Swap whatever sits between a pair of markers, empty markers included."""
    pattern = re.compile(
        rf"([ \t]*)(<!-- {name}:START -->).*?([ \t]*<!-- {name}:END -->)", re.S
    )
    match = pattern.search(source)
    if not match:
        raise SystemExit(f"eruptions.html is missing the {name} markers")
    indent = match.group(1)
    return pattern.sub(
        lambda m: f"{indent}{m.group(2)}\n{block}\n{indent}<!-- {name}:END -->",
        source, count=1,
    )


def render_feed(posts):
    built = email.utils.format_datetime(
        datetime.datetime.now(datetime.timezone.utc)
    )
    items = []
    for post in posts:
        stamp = datetime.datetime.fromisoformat(post["date"]).replace(
            tzinfo=datetime.timezone.utc
        )
        items.append(f"""        <item>
            <title>{html.escape(post["title"])}</title>
            <link>{post["url"]}</link>
            <guid isPermaLink="true">{post["url"]}</guid>
            <pubDate>{email.utils.format_datetime(stamp)}</pubDate>
            <category>{post["tag"]}</category>
            <description>{html.escape(post["summary"])}</description>
        </item>""")
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>KCLMS Volcanix Eruptions</title>
        <link>{ORIGIN}/eruptions.html</link>
        <atom:link href="{ORIGIN}/eruptions.xml" rel="self" type="application/rss+xml"/>
        <description>What the KCLMS Volcanix First Tech Challenge team has been building, written for our sponsors and mentors.</description>
        <language>en-GB</language>
        <lastBuildDate>{built}</lastBuildDate>
{body}
    </channel>
</rss>
"""


def render_sitemap(posts):
    today = datetime.date.today().isoformat()
    entries = []
    for page, freq, priority in CORE_PAGES:
        if page and not os.path.exists(os.path.join(ROOT, page)):
            continue
        entries.append((f"{ORIGIN}/{page}", today, freq, priority))
    for post in posts:
        entries.append((post["url"], post["date"], "yearly", "0.6"))
    body = "\n".join(
        f"""    <url>
        <loc>{loc}</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>{freq}</changefreq>
        <priority>{priority}</priority>
    </url>"""
        for loc, lastmod, freq, priority in entries
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""


def write(path, content, check, stale):
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read()
    # lastBuildDate changes every run; ignore it when deciding staleness.
    normalise = lambda text: re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", text)
    if normalise(existing) == normalise(content):
        return
    stale.append(os.path.relpath(path, ROOT))
    if not check:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    posts = read_posts()
    stale = []

    with open(INDEX_PAGE, encoding="utf-8") as handle:
        page = handle.read()
    page = replace_marked(page, "ERUPTIONS:FEATURED", render_featured(posts))
    page = replace_marked(page, "ERUPTIONS:INDEX", render_index(posts))
    page = replace_marked(page, "ERUPTIONS:CHIPS", render_chips(posts))
    write(INDEX_PAGE, page, args.check, stale)
    write(FEED, render_feed(posts), args.check, stale)
    write(SITEMAP, render_sitemap(posts), args.check, stale)

    if args.check:
        if stale:
            print("Stale: " + ", ".join(stale))
            print("Run tools/rebuild_eruptions.py to regenerate.")
            return 1
        print(f"{len(posts)} post(s); index, feed and sitemap all current.")
        return 0

    print(f"{len(posts)} post(s)")
    print("Updated: " + (", ".join(stale) if stale else "nothing, already current"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
