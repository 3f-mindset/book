#!/usr/bin/env python3
"""Generate the MkDocs source and navigation from the Scrivener manuscript."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "Draft"
DOCS_DIR = ROOT / ".mkdocs-docs"
CONFIG_PATH = ROOT / ".mkdocs.generated.yml"
FILENAME = re.compile(r"^(?P<order>\d+)\s+(?P<title>.+)\s+\[(?P<index>\d+)\]\.md$")


@dataclass(frozen=True)
class Chapter:
    order: int
    title: str
    index: int
    source: Path

    @property
    def page_path(self) -> str:
        # The stable Scrivener index keeps generated paths unique even if titles repeat.
        return f"chapters/{self.order:03d}-{self.index:03d}.md"


def discover_chapters() -> list[Chapter]:
    chapters: list[Chapter] = []
    for source in DRAFT_DIR.glob("*.md"):
        match = FILENAME.match(source.name)
        if not match:
            raise ValueError(
                f"Unexpected chapter filename: {source.name}. "
                "Expected '<order> <title> [<Scrivener index>].md'."
            )
        chapters.append(
            Chapter(
                order=int(match["order"]),
                title=match["title"],
                index=int(match["index"]),
                source=source,
            )
        )

    chapters.sort(key=lambda chapter: (chapter.order, chapter.index, chapter.title))
    duplicate_orders = [
        order for order in {chapter.order for chapter in chapters}
        if sum(chapter.order == order for chapter in chapters) > 1
    ]
    if duplicate_orders:
        raise ValueError(f"Chapter display order must be unique: {sorted(duplicate_orders)}")
    return chapters


def markdown_link(title: str, path: str) -> str:
    return f"[{title.replace(']', r'\\]')}]({path})"


def write_site(chapters: list[Chapter]) -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    (DOCS_DIR / "chapters").mkdir(parents=True)

    toc = ["# Table of Contents", "", "The chapters below are generated from the `Draft/` filenames at build time.", ""]
    for chapter in chapters:
        toc.append(f"{chapter.order}. {markdown_link(chapter.title, chapter.page_path)}")
        content = chapter.source.read_text(encoding="utf-8")
        page = f"# {chapter.title}\n\n{content.rstrip()}\n"
        (DOCS_DIR / chapter.page_path).write_text(page, encoding="utf-8")
    (DOCS_DIR / "index.md").write_text("\n".join(toc) + "\n", encoding="utf-8")


def write_config(chapters: list[Chapter]) -> None:
    lines = [
        "site_name: 3F Book",
        "site_description: A build-time view of the 3F manuscript.",
        "docs_dir: .mkdocs-docs",
        "site_dir: site",
        "theme:",
        "  name: readthedocs",
        "nav:",
        "  - Table of Contents: index.md",
        "  - Chapters:",
    ]
    for chapter in chapters:
        lines.append(f"      - {json.dumps(chapter.title)}: {chapter.page_path}")
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    chapters = discover_chapters()
    if not chapters:
        raise ValueError("No chapters found in Draft/.")
    write_site(chapters)
    write_config(chapters)
    print(f"Generated a {len(chapters)}-chapter MkDocs site.")


if __name__ == "__main__":
    main()
