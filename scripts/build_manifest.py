#!/usr/bin/env python3
"""Quarto pre-render hook.

Scans `posts/*/index.qmd`, and:
  1. writes `_manifest.lua` (ordered, drafts excluded) for the prev/next filter;
  2. lints that every non-draft post has a 1..200 char `description`.

Run from the project root: `python3 scripts/build_manifest.py`.
Exit code 1 (which fails `quarto render`) if the lint finds a problem.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

MAX_DESCRIPTION = 200


def parse_frontmatter(text: str) -> dict:
    """Return the YAML front-matter block of a .qmd file as a dict, or {}."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_draft(fm: dict) -> bool:
    v = fm.get("draft", False)
    return str(v).strip().lower() == "true"


def collect_posts(root: Path) -> list[dict]:
    """Ordered list of non-draft posts under `root/posts/*/index.qmd`.

    Each entry: {path, href, title, date, dirname, description}.
    Sorted by (date, dirname) ascending.
    """
    posts: list[dict] = []
    for index in sorted((root / "posts").glob("*/index.qmd")):
        fm = parse_frontmatter(index.read_text(encoding="utf-8"))
        if not fm or _is_draft(fm):
            continue
        slug = index.parent.name
        posts.append(
            {
                "path": f"posts/{slug}/index.qmd",
                "href": f"/posts/{slug}/",
                "title": str(fm.get("title", slug)),
                "date": str(fm.get("date", "")),
                "dirname": slug,
                "description": str(fm.get("description", "")).strip(),
            }
        )
    posts.sort(key=lambda p: (p["date"], p["dirname"]))
    return posts


def _lua_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def render_manifest(posts: list[dict]) -> str:
    lines = ["return {"]
    for p in posts:
        lines.append(
            "  { path = %s, href = %s, title = %s },"
            % (_lua_str(p["path"]), _lua_str(p["href"]), _lua_str(p["title"]))
        )
    lines.append("}\n")
    return "\n".join(lines)


def lint_descriptions(posts: list[dict]) -> list[str]:
    problems: list[str] = []
    for p in posts:
        d = p["description"]
        if not d:
            problems.append(f"{p['path']}: missing `description` front-matter field")
        elif len(d) > MAX_DESCRIPTION:
            problems.append(
                f"{p['path']}: `description` is {len(d)} chars (max {MAX_DESCRIPTION})"
            )
    return problems


def main() -> int:
    root = Path.cwd()
    posts = collect_posts(root)
    (root / "_manifest.lua").write_text(render_manifest(posts), encoding="utf-8")
    problems = lint_descriptions(posts)
    if problems:
        print("build_manifest: description lint failed:", file=sys.stderr)
        for line in problems:
            print(f"  - {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
