#!/usr/bin/env python3
"""Fail the build if Quarto/Pandoc did not convert a post's math.

Usage: python scripts/check_math.py _site

MathJax v4 typesets client-side, so rendered HTML still holds TeX *inside*
`\\(...\\)` / `\\[...\\]` wrappers that Pandoc emits as `<span class="math ...">`
and `<div class="math ...">`. This script strips <script>/<style> and every
`math` wrapper, then fails if TeX tokens remain in the visible text of any file
under `_site/posts/`. It also checks the MathJax v4 loader is present.

This is a *structural* check (did Pandoc recognize the math), not a rendering
check. Whether MathJax v4 actually typesets the macros and `align` numbering is
verified manually in a browser at deploy time.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
_MACROS = re.compile(
    r'<div\b[^>]*\bid="mathjax-macros"[^>]*>.*?</div>', re.I | re.S
)
_MATH_WRAP = re.compile(
    r'<(span|div)[^>]*class="[^"]*\bmath\b[^"]*"[^>]*>.*?</\1>', re.I | re.S
)
_TAG = re.compile(r"<[^>]+>")
_TEX_TOKENS = [
    r"\$\$", r"\\\[", r"\\\]", r"\\begin\{", r"\\end\{", r"\\newcommand",
    r"\\frac", r"\\sum", r"\\int", r"\\hat\{", r"\\tilde\{", r"\\mathbb",
    r"\\mathcal", r"\\operatorname", r"\\lfloor", r"\\underbrace",
]
_TEX_RE = re.compile("|".join(_TEX_TOKENS))
_V4 = re.compile(r"<script[^>]+src=[\"'][^\"']*mathjax@4[^\"']*[\"']", re.I)


def has_mathjax_v4(html: str) -> bool:
    return bool(_V4.search(html))


def _visible_text(html: str) -> str:
    html = _SCRIPT_STYLE.sub(" ", html)
    html = _MACROS.sub(" ", html)
    html = _MATH_WRAP.sub(" ", html)
    html = _TAG.sub(" ", html)
    return html


def find_leaked_tex(html: str) -> list[str]:
    text = _visible_text(html)
    hits = []
    for m in _TEX_RE.finditer(text):
        start = max(0, m.start() - 40)
        hits.append(text[start : m.end() + 40].strip())
    return hits


def check_tree(site: Path) -> int:
    posts_dir = site / "posts"
    html_files = sorted(posts_dir.rglob("*.html")) if posts_dir.is_dir() else []
    if not html_files:
        print(f"check_math: no post HTML under {posts_dir}", file=sys.stderr)
        return 1

    any_v4 = False
    failed = False
    for f in html_files:
        html = f.read_text(encoding="utf-8", errors="replace")
        any_v4 = any_v4 or has_mathjax_v4(html)
        leaks = find_leaked_tex(html)
        if leaks:
            failed = True
            rel = f.relative_to(site)
            print(f"check_math: unconverted TeX in {rel}:", file=sys.stderr)
            for snip in leaks[:5]:
                print(f"    ...{snip}...", file=sys.stderr)

    if not any_v4:
        print("check_math: MathJax v4 loader not found in any post", file=sys.stderr)
        failed = True

    return 1 if failed else 0


def main(argv: list[str]) -> int:
    site = Path(argv[1]) if len(argv) > 1 else Path("_site")
    return check_tree(site)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
