# 3F Book Scrivener

This repository contains the manuscript and its supporting Scrivener-derived
material as Markdown files.

## File naming is structure

The names of the files are part of the book's source data. They use this
pattern:

```text
<display order> <document title> [<Scrivener item index>].md
```

For example, `Draft/1 The Blade [0].md` is the first displayed manuscript
document, named *The Blade*, and carries Scrivener item index `0`.

- The leading number preserves the intended ordering of sibling documents.
- The title is the human-readable document name used when locating and linking
  material.
- The bracketed index preserves the stable Scrivener item reference that
  supports links and the nested binder structure when the project is moved
  between Scrivener and this file-based representation.
- The `Draft/` and `Notes/` directories distinguish manuscript chapters from
  front matter, reference material, and production notes.

## Editing rules

Both filenames and file contents are significant. Do not rename, reorder, or
remove the numeric and bracketed parts of a filename unless the corresponding
Scrivener structure and any affected links are intentionally updated. Likewise,
preserve each document's content when performing structural changes.

When adding a document, follow the existing naming pattern and use the
appropriate directory so it can be placed and linked correctly in Scrivener.

## Published book site

The GitHub Pages site is generated afresh from `Draft/` on every build with
[mdBook](https://github.com/rust-lang/mdBook). The generator reads the display
order and title from each filename, then creates the chapter pages and
`SUMMARY.md` navigation. No chapter list is maintained by hand.

To preview the same generated book locally:

```powershell
python scripts\build_mdbook.py
mdbook serve
```

This requires Python for the source generator and mdBook installed locally.

Pushing to `main` runs `.github/workflows/publish-book.yml`, which installs
mdBook, rebuilds the site, and deploys it to GitHub Pages.
