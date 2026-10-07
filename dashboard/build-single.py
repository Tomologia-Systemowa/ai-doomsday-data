#!/usr/bin/env python3
"""Build a single-file copy of the dashboard for static hosting.

Inlines styles.css and app.js into index.html and writes dist/AIdoomsday.html
(in the repo root, ignored by git). Upload that one file anywhere; outside localhost
and GitHub Pages it reads the data from raw.githubusercontent.com.

Usage: python3 dashboard/build-single.py [output path]
"""
import pathlib
import shutil
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "dist" / "AIdoomsday.html"

# Refresh the social-share meta tags (score, band) from data/latest.json first.
subprocess.run([sys.executable, str(here / "update-meta.py")], check=True, stdout=subprocess.DEVNULL)

html = (here / "index.html").read_text(encoding="utf-8")
css = (here / "styles.css").read_text(encoding="utf-8")
js = (here / "app.js").read_text(encoding="utf-8")

if "</script" in js.lower() or "</style" in css.lower():
    sys.exit("app.js or styles.css contains a closing tag that would break inlining")

link_tag = '<link rel="stylesheet" href="styles.css">'
script_tag = '<script defer src="app.js"></script>'
for tag in (link_tag, script_tag):
    if html.count(tag) != 1:
        sys.exit(f"expected exactly one {tag!r} in index.html")

html = html.replace(link_tag, "<style>\n" + css + "</style>")
# A module script is deferred like the CDN scripts before it, so it still runs after htmx
# and Mustache and before DOMContentLoaded – the same order as the separate app.js.
html = html.replace(script_tag, '<script type="module">\n' + js + "</script>")

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
shutil.copyfile(here / "og-image.png", out.parent / "og-image.png")  # upload next to the page
print(f"Written {out} ({out.stat().st_size // 1024} KB)")
