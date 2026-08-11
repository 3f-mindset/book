#!/usr/bin/env python3
"""Generate the mdBook source and summary from the Scrivener manuscript."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "Draft"
NOTES_DIR = ROOT / "Notes"
MENU_FILE = ROOT / "book-menu.yml"
BOOK_SRC_DIR = ROOT / "book-src"
FILENAME = re.compile(r"^(?P<order>\d+)\s+(?P<title>.+)\s+\[(?P<index>\d+)\]\.md$")
FRONT_MATTER_FILES = (
    "5 Dedication [70].md",
    "6 Epigraph [71].md",
    "8 Preface [73].md",
    "9 Introduction [74].md",
)


@dataclass(frozen=True)
class Chapter:
    order: int
    title: str
    scrivener_id: int
    source: Path
    page_prefix: str = "chapters"

    @property
    def page_path(self) -> str:
        return f"{self.page_prefix}/{self.order:03d}-{self.scrivener_id:03d}.md"


def discover_documents(sources: list[Path], page_prefix: str) -> list[Chapter]:
    chapters: list[Chapter] = []
    for source in sources:
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
                scrivener_id=int(match["index"]),
                source=source,
                page_prefix=page_prefix,
            )
        )

    chapters.sort(key=lambda chapter: (chapter.order, chapter.scrivener_id, chapter.title))
    duplicate_orders = [
        order
        for order in {chapter.order for chapter in chapters}
        if sum(chapter.order == order for chapter in chapters) > 1
    ]
    if duplicate_orders:
        raise ValueError(f"Chapter display order must be unique: {sorted(duplicate_orders)}")
    return chapters


def load_parent_map(documents: list[Chapter]) -> dict[int, int | None]:
    if not MENU_FILE.is_file():
        raise ValueError(f"Missing navigation map: {MENU_FILE.name}")

    config = yaml.safe_load(MENU_FILE.read_text(encoding="utf-8")) or {}
    raw_parents = config.get("parents")
    if not isinstance(raw_parents, dict):
        raise ValueError(f"{MENU_FILE.name} must define a 'parents' mapping.")

    parent_map: dict[int, int | None] = {}
    for raw_child, raw_parent in raw_parents.items():
        child_id = int(raw_child)
        parent_map[child_id] = None if raw_parent is None else int(raw_parent)

    document_ids = {document.scrivener_id for document in documents}
    duplicate_ids = [
        scrivener_id
        for scrivener_id in document_ids
        if sum(document.scrivener_id == scrivener_id for document in documents) > 1
    ]
    if duplicate_ids:
        raise ValueError(f"Scrivener IDs must be unique: {sorted(duplicate_ids)}")

    missing_entries = sorted(document_ids - parent_map.keys())
    if missing_entries:
        raise ValueError(
            f"Navigation map is missing Scrivener IDs: {missing_entries}"
        )

    missing_parents = sorted(
        {
            parent_id
            for parent_id in parent_map.values()
            if parent_id is not None and parent_id not in document_ids
        }
    )
    if missing_parents:
        raise ValueError(f"Navigation map refers to unknown parent IDs: {missing_parents}")

    documents_by_id = {document.scrivener_id: document for document in documents}
    for document in documents:
        seen: set[int] = set()
        parent_id = parent_map[document.scrivener_id]
        while parent_id is not None:
            if parent_id in seen:
                raise ValueError(
                    f"Navigation map contains a cycle involving Scrivener ID "
                    f"{document.scrivener_id}"
                )
            seen.add(parent_id)
            parent_id = parent_map[documents_by_id[parent_id].scrivener_id]

    return parent_map


def discover_chapters() -> list[Chapter]:
    return discover_documents(sorted(DRAFT_DIR.glob("*.md")), "chapters")


def discover_front_matter() -> list[Chapter]:
    sources = [NOTES_DIR / filename for filename in FRONT_MATTER_FILES]
    missing = [source.name for source in sources if not source.is_file()]
    if missing:
        raise ValueError(f"Missing front matter files: {missing}")
    return discover_documents(sources, "front-matter")


def markdown_link(title: str, path: str) -> str:
    escaped_title = title.replace("]", "\\]")
    return f"[{escaped_title}]({path})"


def menu_lines(
    chapters: list[Chapter], parent_map: dict[int, int | None]
) -> list[str]:
    children: dict[int | None, list[Chapter]] = {}
    for chapter in chapters:
        children.setdefault(parent_map[chapter.scrivener_id], []).append(chapter)

    lines: list[str] = []

    def append_children(parent_id: int | None, indent: str = "") -> None:
        for chapter in sorted(children.get(parent_id, []), key=lambda item: item.order):
            lines.append(f"{indent}- {markdown_link(chapter.title, chapter.page_path)}")
            append_children(chapter.scrivener_id, indent + "  ")

    append_children(None)
    return lines


def write_book(
    chapters: list[Chapter],
    front_matter: list[Chapter],
    parent_map: dict[int, int | None],
) -> None:
    if BOOK_SRC_DIR.exists():
        shutil.rmtree(BOOK_SRC_DIR)
    (BOOK_SRC_DIR / "chapters").mkdir(parents=True)
    (BOOK_SRC_DIR / "front-matter").mkdir()

    summary = [
        "# Summary",
        "",
        "- [Table of Contents](index.md)",
        "- [Front Matter](front-matter.md)",
    ]
    summary.extend(
        f"  - {markdown_link(document.title, document.page_path)}"
        for document in front_matter
    )
    summary.extend(menu_lines(chapters, parent_map))
    toc = [
        "# Table of Contents",
        "",
        "- [Front Matter](front-matter.md)",
    ]
    toc.extend(
        f"  - {markdown_link(document.title, document.page_path)}"
        for document in front_matter
    )
    toc.extend(menu_lines(chapters, parent_map))
    for document in [*front_matter, *chapters]:
        content = document.source.read_text(encoding="utf-8")
        page = f"# {document.title}\n\n{content.rstrip()}\n"
        (BOOK_SRC_DIR / document.page_path).write_text(page, encoding="utf-8")

    front_matter_page = "# Front Matter\n\nThe front matter documents are listed in the navigation.\n"
    (BOOK_SRC_DIR / "front-matter.md").write_text(front_matter_page, encoding="utf-8")

    (BOOK_SRC_DIR / "index.md").write_text("\n".join(toc) + "\n", encoding="utf-8")
    (BOOK_SRC_DIR / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    chapters = discover_chapters()
    front_matter = discover_front_matter()
    parent_map = load_parent_map([*chapters, *front_matter])
    if not chapters:
        raise ValueError("No chapters found in Draft/.")
    write_book(chapters, front_matter, parent_map)
    print(f"Generated mdBook source for {len(chapters)} chapters and {len(front_matter)} front matter documents.")


if __name__ == "__main__":
    main()
