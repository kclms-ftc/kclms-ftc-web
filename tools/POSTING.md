# Publishing a team update

The route is: **a writer sends a .docx → it gets approved → it gets converted →
it goes live.** No CMS, no logins, no build step. The document is the draft and
the approval; the tools below just turn it into a page.

## For writers

Write the update in Word or Google Docs and send the `.docx`.

- **Use real headings.** Heading 1 for the title, Heading 2 for sections. Not
  bold text pretending to be a heading — the converter reads the actual styles.
- **The first heading becomes the post title.**
- **Paste photos straight into the document.** They get pulled out, resized and
  placed where you put them.
- **Add alt text to each image** if you can. In Word: right-click the image →
  View Alt Text. If you skip it, someone writes it later.
- **Your words ship exactly as written**, typos included. Nothing gets tidied,
  reworded or spell-checked on the way through. Proofread the document, because
  the document is what goes on the site.

Every post must end up with all five of these, so include what you can:

1. Photos from the period
2. Numbers — hours, students reached, matches, whatever is real
3. Where the money went
4. Thanks to the sponsors who paid for it
5. What's next

The tests refuse a post that is missing 1, 2, 3, 4 or 5.

## For whoever publishes it

```sh
python3 tools/docx2post.py drafts/the-update.docx \
    --slug autonomous-consistency \
    --date 2026-11-02 --date-label "2 November 2026" \
    --author "Their Name" --role "Build Lead" \
    --tag build          # build | outreach | competition | funding

tools/sync-nav.sh              # gives the new page its nav and footer
python3 tools/rebuild_eruptions.py   # index, RSS feed and sitemap
python3 tests/run.py           # must be green before pushing
```

The converter prints a warning naming any image that still needs alt text.

Then open `eruptions/<slug>.html` and fill in the numbers band, the spend line,
the thanks and the what's next, unless the writer already covered them in the
document.

## Why it is built this way

The site is hand-written static HTML on GitHub Pages. A CMS would mean a
backend, accounts and a build step for a team that publishes a few times a
season, and it would rot the first time nobody logged in for two months. A Word
document is a thing every writer on the team already knows how to produce, and
approving one is just reading it.

The cost of that choice is that publishing is a manual step someone has to run.
`tools/rebuild_eruptions.py --check` is wired into the test suite so a forgotten
rebuild fails loudly rather than quietly leaving the index out of date.
