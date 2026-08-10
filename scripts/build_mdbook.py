#!/usr/bin/env python3
"""Generate the mdBook source and summary from the Scrivener manuscript."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "Draft"
BOOK_SRC_DIR = ROOT / "book-src"
FILENAME = re.compile(r"^(?P<order>\d+)\s+(?P<title>.+)\s+\[(?P<index>\d+)\]\.md$")


@dataclass(frozen=True)
class Chapter:
    order: int
    title: str
    index: int
    source: Path

    @property
    def page_path(self) -> str:
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
        order
        for order in {chapter.order for chapter in chapters}
        if sum(chapter.order == order for chapter in chapters) > 1
    ]
    if duplicate_orders:
        raise ValueError(f"Chapter display order must be unique: {sorted(duplicate_orders)}")
    return chapters


def markdown_link(title: str, path: str) -> str:
    return f"[{title.replace(']', r'\\]')}]({path})"


def write_book(chapters: list[Chapter]) -> None:
    if BOOK_SRC_DIR.exists():
        shutil.rmtree(BOOK_SRC_DIR)
    (BOOK_SRC_DIR / "chapters").mkdir(parents=True)

    summary = ["# Summary", "", "- [Table of Contents](index.md)"]
    toc = [
        "# Table of Contents",
        "",
        "The chapters below are generated from the `Draft/` filenames at build time.",
        "",
    ]
    for chapter in chapters:
        link = markdown_link(chapter.title, chapter.page_path)
        summary.append(f"- {link}")
        toc.append(f"{chapter.order}. {link}")
        content = chapter.source.read_text(encoding="utf-8")
        page = f"# {chapter.title}\n\n{content.rstrip()}\n"
        (BOOK_SRC_DIR / chapter.page_path).write_text(page, encoding="utf-8")

    (BOOK_SRC_DIR / "index.md").write_text("\n".join(toc) + "\n", encoding="utf-8")
    (BOOK_SRC_DIR / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    chapters = discover_chapters()
    if not chapters:
        raise ValueError("No chapters found in Draft/.")
    write_book(chapters)
    print(f"Generated mdBook source for {len(chapters)} chapters.")


if __name__ == "__main__":
    main()
