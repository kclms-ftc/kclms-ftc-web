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
HOME_PAGE = os.path.join(ROOT, "index.html")
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


def render_latest(posts):
    """The newest eruption, reproduced in full on the index page.

    The post file stays the canonical copy; this lifts its body so a reader
    landing on eruptions.html gets the whole thing without a click. Headings
    are demoted two levels because the page already spends h1 on "Eruptions"
    and h2 on the section banner.
    """
    if not posts:
        return (
            '        <p class="resource-empty">The first eruption goes up after '
            "our next milestone.</p>"
        )
    post = posts[0]
    with open(os.path.join(ROOT, "eruptions", f"{post['slug']}.html"),
              encoding="utf-8") as handle:
        source = handle.read()

    match = re.search(r'<article class="post"[^>]*>(.*?)</article>', source, re.S)
    if not match:
        raise SystemExit(f"{post['slug']}.html has no post article to lift")
    body = match.group(1)

    # the post page's own footer buttons do not belong on the index
    body = re.sub(r'\s*<div class="post-foot">.*?</div>\s*', "\n", body, flags=re.S)
    # h1 -> h3, h2 -> h4, and anything deeper is already fine
    body = re.sub(r"<(/?)h2>", r"<\1h4>", body)
    body = re.sub(r"<(/?)h1>", r"<\1h3>", body)

    permalink = f"eruptions/{post['slug']}.html"
    return "\n".join([
        f'        <article class="post post-inline" id="{post["slug"]}" '
        f'data-tag="{post["tag"]}">',
        body.rstrip(),
        '            <p class="post-permalink">',
        f'                <a href="{permalink}">Open this eruption on its own page '
        "&rarr;</a>",
        "            </p>",
        "        </article>",
    ])


def render_index(posts):
    """Everything older than the latest, as cards rather than a thin list."""
    posts = posts[1:]
    if not posts:
        return (
            '        <p class="resource-empty">Nothing older yet. This is the '
            "first eruption.</p>"
        )
    out = ['        <div class="eruption-cards">']
    for post in posts:
        width, height = image_size(os.path.join(ROOT, post["image"]))
        dims = f' width="{width}" height="{height}"' if width and height else ""
        link = f"eruptions/{post['slug']}.html"
        out.extend([
            f'            <article class="eruption-card" data-tag="{post["tag"]}">',
            f'                <a class="eruption-media" href="{link}" tabindex="-1" '
            'aria-hidden="true">',
            f'                    <img src="{post["image"]}" alt="" aria-hidden="true"'
            f'{dims} loading="lazy">',
            "                </a>",
            '                <div class="eruption-body">',
            f'                    <p class="post-date"><time datetime="{post["date"]}">'
            f'{short_month(post["date"])}</time></p>',
            f'                    <h3><a href="{link}">{post["title"]}</a></h3>',
            f'                    <p>{html.escape(post["summary"], quote=False)}</p>',
            f'                    <a href="{link}" class="btn ghost">'
            "<span>Read the Full Post</span></a>",
            "                </div>",
            "            </article>",
        ])
    out.append("        </div>")
    return "\n".join(out)


def render_teaser(posts):
    """The homepage card pointing at the newest eruption.

    Generated rather than hand-written: it went stale the first time a post
    was replaced, and a dead link on the homepage is the worst place to have
    one.
    """
    if not posts:
        return (
            '        <div class="teaser latest-update">\n'
            '            <p class="teaser-kicker">Latest eruption</p>\n'
            "            <h3>Nothing published yet</h3>\n"
            "        </div>"
        )
    post = posts[0]
    link = f"eruptions/{post['slug']}.html"
    return "\n".join([
        '        <div class="teaser latest-update">',
        f'            <p class="teaser-kicker"><time datetime="{post["date"]}">'
        f'{post["date_label"]}</time> &middot; Latest eruption</p>',
        f'            <h3><a href="{link}">{post["title"]}</a></h3>',
        f'            <p>{html.escape(post["summary"], quote=False)}</p>',
        '            <a href="eruptions.html" class="btn ghost"><span>All Eruptions</span></a>',
        "        </div>",
    ])


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
        raise SystemExit(f"missing the {name} markers")
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
    page = replace_marked(page, "ERUPTIONS:LATEST", render_latest(posts))
    page = replace_marked(page, "ERUPTIONS:INDEX", render_index(posts))
    page = replace_marked(page, "ERUPTIONS:CHIPS", render_chips(posts))
    write(INDEX_PAGE, page, args.check, stale)

    with open(HOME_PAGE, encoding="utf-8") as handle:
        home = handle.read()
    home = replace_marked(home, "ERUPTIONS:TEASER", render_teaser(posts))
    write(HOME_PAGE, home, args.check, stale)
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
