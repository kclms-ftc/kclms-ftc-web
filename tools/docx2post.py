#!/usr/bin/env python3
"""Turn a writer's .docx into a Volcanix update post.

The workflow this serves: a student writes the update in Word and sends the
file over. It gets approved as a document, then converted here. The text is
reproduced exactly as written -- this tool never rewrites, tidies or corrects
anybody's words, including their typos. What you approved in the docx is what
ships.

    python3 tools/docx2post.py drafts/september.docx \\
        --slug think-award-catch-up \\
        --date 2026-09-07 \\
        --author "Ansh Gupta" --role "Build Lead" \\
        --tag build

Writes:
    updates/<slug>.html          the post page
    media/updates/<slug>/*       every image in the document, resized

Then run `python3 tools/rebuild_updates.py` to fold the new post into the
index, the RSS feed and the sitemap.

Standard library only. Image resizing uses `sips`, which ships with macOS; on
anything else the originals are copied through untouched and a warning is
printed.
"""

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

MAX_IMAGE_WIDTH = 1600
TAGS = ("build", "outreach", "competition", "funding")


# ---------------------------------------------------------------- utilities

def slugify(text):
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or "update"


def esc(text):
    return html.escape(text, quote=False)


# ------------------------------------------------------------ docx reading

class Docx:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.rels = self._read_rels()

    def _read_rels(self):
        try:
            raw = self.zip.read("word/_rels/document.xml.rels")
        except KeyError:
            return {}
        rels = {}
        for node in ET.fromstring(raw):
            rels[node.get("Id")] = {
                "target": node.get("Target"),
                "type": node.get("Type", ""),
                "external": node.get("TargetMode") == "External",
            }
        return rels

    def body(self):
        root = ET.fromstring(self.zip.read("word/document.xml"))
        body = root.find(f"{W}body")
        return list(body) if body is not None else []

    def media(self, target):
        """Bytes for a relationship target such as 'media/image1.png'."""
        name = target.replace("\\", "/")
        if not name.startswith("word/"):
            name = "word/" + name.lstrip("/")
        return self.zip.read(name)


def paragraph_style(node):
    props = node.find(f"{W}pPr")
    if props is None:
        return None, False
    style_node = props.find(f"{W}pStyle")
    style = style_node.get(f"{W}val") if style_node is not None else None
    listed = props.find(f"{W}numPr") is not None
    return style, listed


def heading_level(style):
    """Word's own heading styles, plus the ones Google Docs exports."""
    if not style:
        return None
    match = re.match(r"(?:Heading|heading)(\d)", style)
    if match:
        return int(match.group(1))
    if style in ("Title", "Subtitle"):
        return 1 if style == "Title" else 2
    return None


def run_images(run):
    """Relationship ids for any images embedded in this run."""
    return [
        blip.get(f"{R}embed")
        for blip in run.iter(f"{A}blip")
        if blip.get(f"{R}embed")
    ]


def image_alt(run):
    """Word stores the image description on the drawing's docPr element."""
    for prop in run.iter(f"{W}drawing"):
        for doc_pr in prop.iter():
            if doc_pr.tag.endswith("}docPr"):
                return (doc_pr.get("descr") or "").strip()
    return ""


def inline_runs(parent, docx, images):
    """Render the inline content of a paragraph, preserving emphasis, links
    and image placement in document order."""
    out = []
    for child in parent:
        if child.tag == f"{W}r":
            for rel_id in run_images(child):
                images.append({"rel": rel_id, "alt": image_alt(child)})
                out.append({"image": rel_id})
            props = child.find(f"{W}rPr")
            bold = props is not None and props.find(f"{W}b") is not None
            italic = props is not None and props.find(f"{W}i") is not None
            text = "".join(t.text or "" for t in child.iter(f"{W}t"))
            if child.find(f"{W}br") is not None and not text:
                out.append({"text": "\n"})
            if not text:
                continue
            fragment = esc(text)
            if bold:
                fragment = f"<strong>{fragment}</strong>"
            if italic:
                fragment = f"<em>{fragment}</em>"
            out.append({"text": fragment})
        elif child.tag == f"{W}hyperlink":
            inner = inline_runs(child, docx, images)
            rel = docx.rels.get(child.get(f"{R}id"), {})
            href = rel.get("target")
            body = "".join(part.get("text", "") for part in inner)
            if href and body:
                external = rel.get("external") and href.startswith("http")
                extra = ' target="_blank" rel="noopener"' if external else ""
                out.append({"text": f'<a href="{esc(href)}"{extra}>{body}</a>'})
            else:
                out.extend(inner)
    return out


def read_blocks(docx):
    """Flatten the document into ordered blocks we know how to render."""
    blocks = []
    images = []
    for node in docx.body():
        if node.tag != f"{W}p":
            continue
        style, listed = paragraph_style(node)
        parts = inline_runs(node, docx, images)
        text = "".join(p["text"] for p in parts if "text" in p).strip()
        embedded = [p["image"] for p in parts if "image" in p]

        for rel_id in embedded:
            blocks.append({"kind": "image", "rel": rel_id})
        if not text:
            continue
        level = heading_level(style)
        if level:
            blocks.append({"kind": "heading", "level": level, "html": text})
        elif listed:
            blocks.append({"kind": "item", "html": text})
        else:
            blocks.append({"kind": "para", "html": text})
    return blocks, images


# --------------------------------------------------------------- image work

def image_size(path):
    """Pixel dimensions, via sips where available, else from the file header."""
    if shutil.which("sips"):
        try:
            out = subprocess.run(
                ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                capture_output=True, text=True, check=True,
            ).stdout
            width = re.search(r"pixelWidth:\s*(\d+)", out)
            height = re.search(r"pixelHeight:\s*(\d+)", out)
            if width and height:
                return int(width.group(1)), int(height.group(1))
        except subprocess.CalledProcessError:
            pass
    return header_size(path)


def header_size(path):
    """Minimal PNG/JPEG/GIF dimension reader so the tool still works, and stays
    testable, without sips."""
    with open(path, "rb") as handle:
        head = handle.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return (
                int.from_bytes(head[16:20], "big"),
                int.from_bytes(head[20:24], "big"),
            )
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return (
                int.from_bytes(head[6:8], "little"),
                int.from_bytes(head[8:10], "little"),
            )
        if head[:2] == b"\xff\xd8":
            handle.seek(2)
            while True:
                marker = handle.read(2)
                if len(marker) < 2 or marker[0] != 0xFF:
                    break
                size = int.from_bytes(handle.read(2), "big")
                if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                    block = handle.read(5)
                    return (
                        int.from_bytes(block[3:5], "big"),
                        int.from_bytes(block[1:3], "big"),
                    )
                handle.seek(size - 2, 1)
    return None, None


def shrink(path, max_width=MAX_IMAGE_WIDTH):
    """Resize in place and drop the camera metadata that came off the phone."""
    if not shutil.which("sips"):
        print(f"  ! sips unavailable, keeping {os.path.basename(path)} as-is")
        return
    subprocess.run(
        ["sips", "-Z", str(max_width), path],
        capture_output=True, check=False,
    )
    subprocess.run(
        ["sips", "--deleteColorManagementProperties", path],
        capture_output=True, check=False,
    )


def extract_images(docx, images, slug, dry_run=False):
    """Pull every referenced image out of the docx, resized, and return the
    render info keyed by relationship id."""
    out_dir = os.path.join(ROOT, "media", "updates", slug)
    if not dry_run:
        os.makedirs(out_dir, exist_ok=True)
    seen = {}
    for index, item in enumerate(images, start=1):
        rel_id = item["rel"]
        if rel_id in seen:
            continue
        rel = docx.rels.get(rel_id)
        if not rel:
            continue
        ext = os.path.splitext(rel["target"])[1].lower() or ".png"
        name = f"{slug}-{index}{ext}"
        rel_path = f"media/updates/{slug}/{name}"
        abs_path = os.path.join(out_dir, name)
        if not dry_run:
            with open(abs_path, "wb") as handle:
                handle.write(docx.media(rel["target"]))
            shrink(abs_path)
            width, height = image_size(abs_path)
        else:
            width, height = None, None
        seen[rel_id] = {
            "src": rel_path,
            "alt": item["alt"],
            "width": width,
            "height": height,
        }
    return seen


# ----------------------------------------------------------------- rendering

def normalise_headings(blocks):
    """Re-base the writer's heading depth so the page outline never skips.

    The document's first heading becomes the page h1, and whatever depth the
    writer used for their sections (Heading1, Heading2, or a mix) is shifted so
    the shallowest one lands on h2.
    """
    levels = [b["level"] for b in blocks if b["kind"] == "heading"]
    if not levels:
        return blocks
    shallowest = min(levels)
    for block in blocks:
        if block["kind"] == "heading":
            block["level"] = min(2 + (block["level"] - shallowest), 4)
    return blocks


def render_body(blocks, images):
    """Blocks to markup, in the site's existing component language."""
    out = []
    open_list = False
    photo_index = 0

    def close_list():
        nonlocal open_list
        if open_list:
            out.append("        </ul>")
            open_list = False

    for block in blocks:
        if block["kind"] == "item":
            if not open_list:
                out.append('        <ul class="post-list">')
                open_list = True
            out.append(f"            <li>{block['html']}</li>")
            continue
        close_list()

        if block["kind"] == "heading":
            level = block["level"]
            out.append(f"        <h{level}>{block['html']}</h{level}>")
        elif block["kind"] == "para":
            out.append(f"        <p>{block['html']}</p>")
        elif block["kind"] == "image":
            info = images.get(block["rel"])
            if not info:
                continue
            photo_index += 1
            alt = info["alt"] or f"TODO alt text for image {photo_index}"
            dims = ""
            if info["width"] and info["height"]:
                dims = f' width="{info["width"]}" height="{info["height"]}"'
            out.append('        <figure class="post-figure">')
            out.append(
                f'            <img src="{info["src"]}" alt="{esc(alt)}"{dims} loading="lazy">'
            )
            out.append("        </figure>")
    close_list()
    return "\n".join(out)


def render_page(meta, body):
    """The full post page, matching the chrome every other page carries."""
    title = meta["title"]
    slug = meta["slug"]
    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{esc(meta['summary'])}">
    <link rel="canonical" href="https://volcanixftc.com/updates/{slug}.html">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://volcanixftc.com/updates/{slug}.html">
    <meta property="og:title" content="{esc(title)} - KCLMS Volcanix">
    <meta property="og:description" content="{esc(meta['summary'])}">
    <meta property="og:image" content="https://volcanixftc.com/{meta['image']}">
    <meta property="og:site_name" content="KCLMS Volcanix">
    <meta property="og:locale" content="en_GB">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="https://volcanixftc.com/{meta['image']}">
    <meta name="robots" content="index, follow">
    <meta name="theme-color" content="#000000">
    <title>{esc(title)} - KCLMS Volcanix</title>
    <link rel="icon" href="/favicon.ico" sizes="48x48">
    <link rel="icon" type="image/png" sizes="96x96" href="/media/favicon-96.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/media/favicon-32.png">
    <link rel="apple-touch-icon" href="/media/apple-touch-icon.png">
    <link rel="alternate" type="application/rss+xml" title="Volcanix Updates" href="/updates.xml">
    <link rel="stylesheet" href="/styles.css">
</head>

<body>

    <!-- NAV:START -->
    <!-- NAV:END -->

    <article class="post" id="{slug}" data-tag="{meta['tag']}">
        <header class="post-head">
            <p class="post-date"><time datetime="{meta['date']}">{meta['date_label']}</time></p>
            <h1>{esc(title)}</h1>
            <p class="post-by">{esc(meta['author'])} &middot; {esc(meta['role'])}</p>
        </header>

{body}

        <div class="post-foot">
            <a href="/updates.html" class="btn ghost"><span>All Updates</span></a>
            <a href="/sponsors.html" class="btn ghost"><span>Our Sponsors</span></a>
        </div>
    </article>

    <div class="skyline">
        <span class="skyline-label">London &middot; UK</span>
        <div class="skyline-strip" role="img" aria-label="London skyline silhouette"></div>
    </div>

    <!-- FOOTER:START -->
    <!-- FOOTER:END -->

<script src="/script.js"></script>
</body>

</html>
"""


# ---------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", help="the writer's Word document")
    parser.add_argument("--slug", help="URL slug; defaults to the title")
    parser.add_argument("--title", help="override the title taken from the doc")
    parser.add_argument("--date", required=True, help="publication date, YYYY-MM-DD")
    parser.add_argument("--date-label", help="how the date reads on the page")
    parser.add_argument("--author", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--tag", required=True, choices=TAGS)
    parser.add_argument("--summary", help="one line for the index and the feed")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    docx = Docx(args.docx)
    blocks, images = read_blocks(docx)
    if not blocks:
        print("No readable content in that document.", file=sys.stderr)
        return 1

    headings = [b for b in blocks if b["kind"] == "heading"]
    paragraphs = [b for b in blocks if b["kind"] == "para"]
    title = args.title or re.sub(
        r"<[^>]+>", "", headings[0]["html"] if headings else "Team update"
    )
    if headings and not args.title:
        blocks.remove(headings[0])

    slug = args.slug or slugify(title)
    summary = args.summary or re.sub(
        r"<[^>]+>", "", paragraphs[0]["html"] if paragraphs else title
    )[:180]

    extracted = extract_images(docx, images, slug, dry_run=args.dry_run)
    body = render_body(normalise_headings(blocks), extracted)

    first_image = next(iter(extracted.values()), None)
    meta = {
        "title": title,
        "slug": slug,
        "date": args.date,
        "date_label": args.date_label or args.date,
        "author": args.author,
        "role": args.role,
        "tag": args.tag,
        "summary": summary,
        "image": first_image["src"] if first_image else "media/team-group.jpg",
    }
    page = render_page(meta, body)

    out_path = os.path.join(ROOT, "updates", f"{slug}.html")
    if args.dry_run:
        print(page)
        return 0

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(page)

    print(f"  wrote updates/{slug}.html")
    print(f"  {len(extracted)} image(s) -> media/updates/{slug}/")
    missing = [i for i in extracted.values() if not i["alt"]]
    if missing:
        print(f"  ! {len(missing)} image(s) need alt text writing before publish")
    print("  next: fill in the numbers band, what's next, spend line and thanks,")
    print("        then run tools/sync-nav.sh and tools/rebuild_updates.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
