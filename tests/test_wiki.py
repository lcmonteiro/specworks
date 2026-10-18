"""The wiki pages in wiki/: copied files match their source, links between pages resolve, the sidebar lists every page.

Run as a script with --update to refresh every copied file after editing its source.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
PAGES = sorted(p for p in WIKI.glob("*.md") if not p.name.startswith("_"))
INCLUDE = re.compile(r'^<!-- include: (?P<path>\S+)(?: start-at="(?P<start>[^"]*)")? -->\n(?P<fence>`{3,})(?P<lang>\S*)\n(?P<body>.*?)\n(?P=fence)$', re.M | re.S)
LINK = re.compile(r"\]\((?P<page>[A-Za-z][\w-]*)(?:#(?P<anchor>[\w-]+))?\)")


def read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def source(path, start):
    text = read(ROOT / path).rstrip("\n")
    return text[text.index(start) :] if start else text


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def anchors(page):
    text = re.sub(r"^(`{3,}).*?^\1", "", read(page), flags=re.M | re.S)
    return {slug(line.lstrip("#")) for line in text.splitlines() if line.startswith("#")}


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_included_files_match_their_source(page):
    for m in INCLUDE.finditer(read(page)):
        assert m["body"] == source(m["path"], m["start"]), f"{page.name}: the copy of {m['path']} is stale; run `uv run python tests/test_wiki.py --update`"


@pytest.mark.parametrize("page", [*PAGES, WIKI / "_Sidebar.md"], ids=lambda p: p.stem)
def test_links_point_at_existing_pages(page):
    text = re.sub(r"^(`{3,}).*?^\1", "", read(page), flags=re.M | re.S)
    for m in LINK.finditer(text):
        target = WIKI / f"{m['page']}.md"
        assert target.exists(), f"{page.name}: link to missing page {m['page']}"
        if m["anchor"]:
            assert m["anchor"] in anchors(target), f"{page.name}: no heading #{m['anchor']} in {m['page']}"


def test_sidebar_lists_every_page():
    listed = set(LINK.findall(read(WIKI / "_Sidebar.md")))
    missing = {p.stem for p in PAGES} - {page for page, _ in listed}
    assert not missing, f"pages missing from _Sidebar.md: {sorted(missing)}"


def update():
    for page in PAGES:
        text = read(page)

        def refresh(m):
            body = source(m["path"], m["start"])
            fence = "`" * max([3, *(len(r) + 1 for r in re.findall(r"`{3,}", body))])
            start = f' start-at="{m["start"]}"' if m["start"] else ""
            return f"<!-- include: {m['path']}{start} -->\n{fence}{m['lang']}\n{body}\n{fence}"

        new = INCLUDE.sub(refresh, text)
        if new != text:
            page.write_text(new, encoding="utf-8")
            print(f"updated {page.relative_to(ROOT)}")


if __name__ == "__main__" and "--update" in sys.argv:
    update()
