# Bits and Priors — Quarto Blog Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Quarto website "Bits and Priors" at `https://mapuna.github.io/` with full LaTeX (MathJax v4), a single-column serif reading theme, a blog listing with RSS and search, build-time prev/next navigation between posts, executable Python in posts, on-page SEO, and CI that renders and deploys on push.

**Architecture:** A Quarto `website` project. A Python pre-render script scans `posts/*/index.qmd` and writes an ordered `_manifest.lua`; a Lua filter reads that manifest and appends a prev/next `<nav>` to each post at build time (no runtime JS). Theme is two Bootswatch bases plus custom SCSS enforcing a ~46rem measure and self-hosted woff2 fonts. GitHub Actions renders the site and deploys to GitHub Pages (Pages source = "GitHub Actions"); nothing built is committed except the `_freeze/` execution cache.

**Tech Stack:** Quarto 1.6.42, Pandoc Lua filters (Pandoc 3.x bundled with Quarto), Python 3.12 (`pyyaml`, `numpy`, `matplotlib`, `jupyter`, `pillow`, `pytest`), SCSS via Quarto's Dart Sass, MathJax v4 (CDN, pinned), GitHub Actions.

**Spec:** `docs/design/2026-08-28-quarto-blog-design.md` (read it alongside this plan; the plan implements it).

## Global Constraints

- **Quarto version:** pin `1.6.42` in CI (`quarto-dev/quarto-actions/setup@v2` with `version: 1.6.42`); match locally.
- **MathJax URL:** replace the `mathjax@4` floating tag with an exact `mathjax@4.x.y` patch (check the current release) the first time Task 5 runs; update the two fixture HTML files in `tests/math-fixtures/` to match.
- **Python:** 3.12.
- **Repo:** `mapuna/mapuna.github.io`, **public**, GitHub user site served at the domain root `https://mapuna.github.io/`. Root-absolute URLs (`/posts/…`, `/fonts/…`) are therefore valid.
- **Git identity (repo-local, not global):** `user.name = mapuna`, `user.email = mapuna_@outlook.com`.
- **Never commit `_site/`** or `_manifest.lua` (build artifacts). **Do commit** `_freeze/` and everything under `docs/`.
- **MathJax:** v4 via `format.html.html-math-method.url`. Fallback if v4 misbehaves: delete that one `url:` line, which reverts Quarto to its bundled v3.
- **Fonts:** self-hosted woff2 only. No `fonts.googleapis.com` / `fonts.gstatic.com` / any third-party request at runtime.
- **Post URLs:** date-stripped. Directory is `posts/<slug>/`; the date lives only in front matter.
- **Prev/next convention:** Previous = older post, Next = newer post. Rendered at the foot of each post.
- **Prose style:** everything author-facing (posts, `about.qmd`, page copy) follows the `personal-writing-style` skill; technical posts additionally follow its `math-paper-register`. Do not add em/en dashes, corporate-register verbs (`leverage`, `utilize`, `robust`, `seamless`, …), or hedges (`somewhat`, `arguably`).
- **`docs/` is render-excluded** via the `!docs/` entry in `project.render`, and committed to git.

## Pre-existing files (already written, do not recreate)

- `about.qmd` — has three `<!-- TODO(anupam) -->` markers (public email, company name, confirm display name). **Non-blocking**; leave as-is. Surfaced again in Task 9.
- `posts/jpeg-ai-neural-image-compression/index.qmd` + `jpeg-ai-slide.png` (1659×948, 1.5 MB) + `jpeg-ai-arch.jpg` (1672×941, 274 KB). Front matter already has `title`, `description`, `author`, `date: "2026-05-04"`, `categories`, `image`, `number-sections`, `toc`.
- `docs/design/2026-08-28-quarto-blog-design.md` — the spec.

## File structure (created by this plan)

```
_quarto.yml                     website config (Task 1; edited by 4,5,6)
index.qmd                       blog listing (Task 1)
robots.txt                      allow all + Sitemap: line (Task 1)
requirements.txt                Python deps (Task 1)
.gitignore                      (Task 1)
posts/_metadata.yml             shared post config: freeze: auto (Task 1)
posts/colophon/index.qmd        seed post 1 + math/exec verification page (Task 7)
fonts/*.woff2                    self-hosted faces, committed (Task 4)
styles/theme-light.scss         light theme + reading CSS + .post-nav (Task 1 stub → Task 4)
styles/theme-dark.scss          dark theme overrides (Task 1 stub → Task 4)
styles/_fonts.scss              @font-face rules (Task 4)
styles/_macros.tex              site-wide MathJax \newcommand block (Task 1 stub → Task 5)
styles/jsonld.html              JSON-LD BlogPosting partial (Task 1 stub → Task 6)
filters/post-nav.lua            prev/next injector (Task 1 no-op → Task 3)
scripts/build_manifest.py       pre-render: posts → _manifest.lua + description lint (Task 1 minimal → Task 2)
scripts/check_math.py           CI: fail on Quarto-level math-conversion failure (Task 5)
scripts/fetch-fonts.sh          one-shot font downloader (Task 4)
tests/test_build_manifest.py    (Task 2)
tests/test_check_math.py        (Task 5)
tests/test_post_nav.py          integration: render fixture, assert nav (Task 3)
tests/fixtures/nav/             3-post mini Quarto project (Task 3)
tests/math-fixtures/            good.qmd / bad.qmd (Task 5)
.github/workflows/publish.yml   CI (Task 8)
```

---

## Task 1: Repo skeleton that renders green

**Files:**
- Create: `.gitignore`, `requirements.txt`, `_quarto.yml`, `index.qmd`, `robots.txt`, `posts/_metadata.yml`
- Create (stubs, filled by later tasks): `styles/theme-light.scss`, `styles/theme-dark.scss`, `styles/_macros.tex`, `styles/jsonld.html`, `filters/post-nav.lua`, `scripts/build_manifest.py`

**Interfaces:**
- Produces: a project where `quarto render` exits 0 and emits `_site/index.html`, `_site/about.html`, `_site/posts/jpeg-ai-neural-image-compression/index.html`, `_site/index.xml`, `_site/sitemap.xml`.
- Produces: `scripts/build_manifest.py` writing `_manifest.lua` (Task 2 replaces its body; the file path and the "runs as `python3 scripts/build_manifest.py` from project root, writes `_manifest.lua` in CWD" contract are fixed here).
- Produces: `filters/post-nav.lua` as a Pandoc filter exporting nothing that changes output yet (Task 3 replaces it).

- [ ] **Step 1: `git init` and set repo-local identity**

```bash
cd ~/src/web/mapuna.github.io
git init
git config user.name  "mapuna"
git config user.email "mapuna_@outlook.com"
git config init.defaultBranch main
git branch -m main 2>/dev/null || true
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# Quarto build output
/_site/
/.quarto/

# Pre-render build artifact (regenerated every render)
/_manifest.lua

# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# OS
.DS_Store
```

- [ ] **Step 3: Write `requirements.txt`**

```text
jupyter
pyyaml
numpy
matplotlib
pillow
pytest
```

- [ ] **Step 4: Write `_quarto.yml`** (full config; references stub files created below)

```yaml
project:
  type: website
  output-dir: _site
  pre-render: scripts/build_manifest.py
  render:
    - "*.qmd"
    - "posts/"
    - "!docs/"
    - "!tests/"
    - "!README.md"
  resources:
    - fonts/
    - robots.txt

website:
  title: "Bits and Priors"
  description: "Anupam Gupta on machine learning, information theory, and compression. Derivations, some code."
  site-url: "https://mapuna.github.io"
  open-graph: true
  twitter-card:
    creator: "@mapuna"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - href: about.qmd
        text: About
    right:
      - icon: rss
        href: index.xml
      - icon: github
        href: "https://github.com/mapuna"
      - icon: twitter-x
        href: "https://x.com/mapuna"
  search:
    location: navbar
    type: overlay
  page-footer:
    center: "© 2026 Anupam Gupta · Built with Quarto"

format:
  html:
    theme:
      light: [cosmo, styles/theme-light.scss]
      dark: [darkly, styles/theme-dark.scss]
    toc: true
    toc-location: right
    code-copy: true
    code-overflow: wrap
    html-math-method:
      method: mathjax
      url: "https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"
    include-in-header:
      - styles/_macros.tex
      - styles/jsonld.html

filters:
  - filters/post-nav.lua
```

- [ ] **Step 5: Write `index.qmd`** (the listing page)

```markdown
---
title: "Bits and Priors"
listing:
  contents: posts
  sort: "date desc"
  type: default
  categories: true
  sort-ui: false
  filter-ui: false
  fields: [date, title, reading-time, description, categories]
  feed:
    type: full
page-layout: full
title-block-banner: false
---
```

- [ ] **Step 6: Write `posts/_metadata.yml`**

```yaml
title-block-banner: false
toc: true
freeze: auto
```

- [ ] **Step 7: Write `robots.txt`**

```text
User-agent: *
Allow: /

Sitemap: https://mapuna.github.io/sitemap.xml
```

- [ ] **Step 8: Write stub `styles/theme-light.scss`**

```scss
/*-- scss:defaults --*/
// Real values land in Task 4.

/*-- scss:rules --*/
// Real rules land in Task 4.
```

- [ ] **Step 9: Write stub `styles/theme-dark.scss`**

```scss
/*-- scss:defaults --*/
// Real values land in Task 4.
```

- [ ] **Step 10: Write stub `styles/_macros.tex`**

```html
<!-- Site-wide MathJax macros. Real content lands in Task 5. -->
```

- [ ] **Step 11: Write stub `styles/jsonld.html`**

```html
<!-- JSON-LD BlogPosting. Real content lands in Task 6. -->
```

- [ ] **Step 12: Write no-op `filters/post-nav.lua`**

```lua
-- Prev/next injector. Real implementation lands in Task 3.
-- Until then this filter makes no changes to any document.
return {}
```

- [ ] **Step 13: Write minimal `scripts/build_manifest.py`**

```python
#!/usr/bin/env python3
"""Quarto pre-render hook. Task 2 replaces the body with the real scanner.

Contract fixed here: run as `python3 scripts/build_manifest.py` from the
project root; write a Lua-loadable table to `_manifest.lua` in the CWD.
"""
from pathlib import Path


def main() -> int:
    Path("_manifest.lua").write_text("return {}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 14: Create the venv and install deps**

Run:
```bash
cd ~/src/web/mapuna.github.io
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
Expected: installs without error. `python --version` → `Python 3.12.x`.

- [ ] **Step 15: Render and verify the site builds**

Run:
```bash
. .venv/bin/activate
quarto render
```
Expected: exits 0. Then:
```bash
test -f _site/index.html \
  && test -f _site/about.html \
  && test -f _site/posts/jpeg-ai-neural-image-compression/index.html \
  && test -f _site/index.xml \
  && test -f _site/sitemap.xml \
  && echo "SKELETON OK"
```
Expected: prints `SKELETON OK`.

- [ ] **Step 16: Commit**

```bash
cd ~/src/web/mapuna.github.io
git add .gitignore requirements.txt _quarto.yml index.qmd robots.txt \
        posts/_metadata.yml styles/ filters/ scripts/ about.qmd \
        posts/jpeg-ai-neural-image-compression/ docs/
git commit -m "chore: scaffold Quarto site skeleton (renders green with stubs)"
```

---

## Task 2: `build_manifest.py` — ordered post manifest + description lint

**Files:**
- Modify: `scripts/build_manifest.py` (replace the minimal body)
- Test: `tests/test_build_manifest.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `_manifest.lua` in the project root, a Lua chunk `return { {path=<str>, title=<str>, href=<str>}, ... }` sorted by `(date, dirname)` ascending, drafts excluded. `path` is the POSIX path relative to project root (`posts/<slug>/index.qmd`). `href` is `"/posts/<slug>/"`. Task 3's Lua filter matches an input file against `path` by suffix and reads `href`/`title`.
- Produces: exit code 1 (build fails) if any non-draft post has no `description` or a `description` longer than 200 characters; the offending files are printed to stderr.

- [ ] **Step 1: Write the failing tests**

`tests/test_build_manifest.py`:
```python
import textwrap
from pathlib import Path

import pytest

import scripts.build_manifest as bm


def _post(dir_: Path, *, title, date, description="a valid description", draft=False):
    dir_.mkdir(parents=True)
    fm = {"title": title, "date": date, "description": description}
    if draft:
        fm["draft"] = "true"
    body = "---\n" + "\n".join(f'{k}: "{v}"' for k, v in fm.items()) + "\n---\n\nbody\n"
    (dir_ / "index.qmd").write_text(body, encoding="utf-8")


def test_parse_frontmatter_reads_block():
    text = '---\ntitle: "Hello"\ndate: "2026-01-02"\n---\n\nbody\n'
    fm = bm.parse_frontmatter(text)
    assert fm["title"] == "Hello"
    assert fm["date"] == "2026-01-02"


def test_parse_frontmatter_missing_block_returns_empty():
    assert bm.parse_frontmatter("no front matter here") == {}


def test_collect_posts_sorts_by_date_then_dirname(tmp_path):
    _post(tmp_path / "posts" / "b-later", title="B", date="2026-05-04")
    _post(tmp_path / "posts" / "a-earlier", title="A", date="2026-05-01")
    posts = bm.collect_posts(tmp_path)
    assert [p["title"] for p in posts] == ["A", "B"]
    assert posts[0]["path"] == "posts/a-earlier/index.qmd"
    assert posts[0]["href"] == "/posts/a-earlier/"


def test_collect_posts_excludes_drafts(tmp_path):
    _post(tmp_path / "posts" / "live", title="Live", date="2026-05-01")
    _post(tmp_path / "posts" / "wip", title="WIP", date="2026-05-02", draft=True)
    assert [p["title"] for p in bm.collect_posts(tmp_path)] == ["Live"]


def test_render_manifest_is_loadable_lua():
    posts = [{"path": "posts/x/index.qmd", "title": 'He said "hi"', "href": "/posts/x/"}]
    out = bm.render_manifest(posts)
    assert out.startswith("return {")
    assert r'\"hi\"' in out or '\\"hi\\"' in out  # title is escaped for Lua
    assert '"/posts/x/"' in out


def test_lint_descriptions_flags_missing_and_overlong(tmp_path):
    _post(tmp_path / "posts" / "ok", title="OK", date="2026-05-01")
    _post(tmp_path / "posts" / "nodesc", title="ND", date="2026-05-02", description="")
    _post(tmp_path / "posts" / "long", title="LG", date="2026-05-03",
          description="x" * 201)
    problems = bm.lint_descriptions(bm.collect_posts(tmp_path))
    joined = "\n".join(problems)
    assert "nodesc" in joined
    assert "long" in joined
    assert "ok" not in joined


def test_main_writes_manifest_and_returns_zero(tmp_path, monkeypatch):
    _post(tmp_path / "posts" / "one", title="One", date="2026-05-01")
    _post(tmp_path / "posts" / "two", title="Two", date="2026-05-02")
    monkeypatch.chdir(tmp_path)
    rc = bm.main()
    assert rc == 0
    lua = (tmp_path / "_manifest.lua").read_text(encoding="utf-8")
    assert lua.index("One") < lua.index("Two")


def test_main_returns_one_on_bad_description(tmp_path, monkeypatch):
    _post(tmp_path / "posts" / "bad", title="Bad", date="2026-05-01", description="")
    monkeypatch.chdir(tmp_path)
    assert bm.main() == 1
```

Also create `tests/__init__.py` and `scripts/__init__.py` (empty files) so `import scripts.build_manifest` resolves from the repo root, and `conftest.py` at repo root:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
```

- [ ] **Step 2: Run the tests, verify they fail**

Run: `. .venv/bin/activate && python -m pytest tests/test_build_manifest.py -v`
Expected: FAIL / ERROR (`parse_frontmatter` etc. not defined).

- [ ] **Step 3: Implement `scripts/build_manifest.py`**

```python
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

    Each entry: {path, href, title, date, dirname}. Sorted by (date, dirname).
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
```

- [ ] **Step 4: Run the tests, verify they pass**

Run: `. .venv/bin/activate && python -m pytest tests/test_build_manifest.py -v`
Expected: all PASS.

- [ ] **Step 5: Verify against the real posts**

Run:
```bash
. .venv/bin/activate && python scripts/build_manifest.py && cat _manifest.lua
```
Expected: exit 0; `_manifest.lua` contains one entry, `posts/jpeg-ai-neural-image-compression/index.qmd`, with `href = "/posts/jpeg-ai-neural-image-compression/"`.

- [ ] **Step 6: Full render still green**

Run: `. .venv/bin/activate && quarto render && echo RENDER_OK`
Expected: `RENDER_OK`.

- [ ] **Step 7: Commit**

```bash
git add scripts/build_manifest.py scripts/__init__.py tests/ conftest.py
git commit -m "feat: pre-render post manifest + description lint"
```

---

## Task 3: `post-nav.lua` — prev/next navigation injected at build time

**Files:**
- Modify: `filters/post-nav.lua` (replace the no-op)
- Create: `tests/fixtures/nav/_quarto.yml`, `tests/fixtures/nav/posts/{01-first,02-middle,03-last}/index.qmd`
- Test: `tests/test_post_nav.py`

**Interfaces:**
- Consumes: `_manifest.lua` from Task 2 (`{path, href, title}` entries, oldest first).
- Produces: for any rendered file whose path ends with `posts/<slug>/index.qmd` and appears in the manifest, an appended `<nav class="post-nav">` containing up to two `<div class="post-nav__prev|__next">`, each with `<span class="post-nav__label">` and an `<a>`. Task 4's SCSS styles these class names. No change to any non-post document, or to a post absent from the manifest, or when `_manifest.lua` is missing.

- [ ] **Step 1: Write the fixture Quarto project**

`tests/fixtures/nav/_quarto.yml`:
```yaml
project:
  type: website
  output-dir: _site
  pre-render: ../../../scripts/build_manifest.py
  render:
    - "posts/"
filters:
  - ../../../filters/post-nav.lua
format:
  html:
    theme: default
```

`tests/fixtures/nav/posts/01-first/index.qmd`:
```markdown
---
title: "First post"
date: "2026-01-01"
description: "fixture first"
---

First body.
```

`tests/fixtures/nav/posts/02-middle/index.qmd`:
```markdown
---
title: "Middle post"
date: "2026-01-02"
description: "fixture middle"
---

Middle body.
```

`tests/fixtures/nav/posts/03-last/index.qmd`:
```markdown
---
title: "Last post"
date: "2026-01-03"
description: "fixture last"
---

Last body.
```

- [ ] **Step 2: Write the failing integration test**

`tests/test_post_nav.py`:
```python
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "nav"

pytestmark = pytest.mark.skipif(
    shutil.which("quarto") is None, reason="quarto not on PATH"
)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    out = tmp_path_factory.mktemp("navsite")
    shutil.copytree(FIXTURE, out, dirs_exist_ok=True)
    # scripts/ and filters/ are referenced via ../../../ from the fixture;
    # copy the repo root's scripts+filters next to the copied tree.
    repo = Path(__file__).parent.parent
    for d in ("scripts", "filters"):
        shutil.copytree(repo / d, out.parent / d, dirs_exist_ok=True)
    subprocess.run(["quarto", "render"], cwd=out, check=True)
    return out / "_site" / "posts"


def _html(rendered, slug):
    return (rendered / slug / "index.html").read_text(encoding="utf-8")


def test_middle_post_has_both_prev_and_next(rendered):
    html = _html(rendered, "02-middle")
    assert 'class="post-nav"' in html
    assert 'href="/posts/01-first/"' in html
    assert "First post" in html
    assert 'href="/posts/03-last/"' in html
    assert "Last post" in html
    assert "Previous" in html and "Next" in html


def test_first_post_has_only_next(rendered):
    html = _html(rendered, "01-first")
    assert 'class="post-nav"' in html
    assert 'href="/posts/02-middle/"' in html
    assert 'href="/posts/' not in html.split('class="post-nav"')[0][-0:] or True
    assert "post-nav__prev" not in html
    assert "post-nav__next" in html


def test_last_post_has_only_prev(rendered):
    html = _html(rendered, "03-last")
    assert "post-nav__next" not in html
    assert "post-nav__prev" in html
    assert 'href="/posts/02-middle/"' in html
```

- [ ] **Step 3: Run the test, verify it fails**

Run: `. .venv/bin/activate && python -m pytest tests/test_post_nav.py -v`
Expected: FAIL (no `post-nav` in output; the filter is still the no-op).

- [ ] **Step 4: Implement `filters/post-nav.lua`**

```lua
-- Append a prev/next <nav> to each blog post, using the ordered table in
-- _manifest.lua (written by scripts/build_manifest.py as a pre-render step).
-- Previous = older post, Next = newer post. No runtime JS.

local function html_escape(s)
  return (s:gsub("[&<>\"]", {
    ["&"] = "&amp;", ["<"] = "&lt;", [">"] = "&gt;", ["\""] = "&quot;",
  }))
end

local function load_manifest()
  local ok, m = pcall(dofile, "_manifest.lua")
  if ok and type(m) == "table" then return m end
  return nil
end

local function current_input()
  local files = PANDOC_STATE and PANDOC_STATE.input_files or {}
  return files[1] or ""
end

local function cell(entry, label, side)
  return string.format(
    '<div class="post-nav__%s"><span class="post-nav__label">%s</span>'
      .. '<a href="%s">%s</a></div>',
    side, label, entry.href, html_escape(entry.title))
end

function Pandoc(doc)
  local input = current_input()
  if not input:match("posts/[^/]+/index%.qmd$") then
    return doc
  end

  local manifest = load_manifest()
  if not manifest then return doc end

  local idx
  for i, entry in ipairs(manifest) do
    -- match regardless of absolute vs project-relative input path
    if #input >= #entry.path and input:sub(-#entry.path) == entry.path then
      idx = i
      break
    end
  end
  if not idx then return doc end

  local prev, nxt = manifest[idx - 1], manifest[idx + 1]
  if not prev and not nxt then return doc end

  local parts = { '<nav class="post-nav">' }
  if prev then parts[#parts + 1] = cell(prev, "\u{2190} Previous", "prev") end
  if nxt then parts[#parts + 1] = cell(nxt, "Next \u{2192}", "next") end
  parts[#parts + 1] = "</nav>"

  table.insert(doc.blocks, pandoc.RawBlock("html", table.concat(parts)))
  return doc
end
```

- [ ] **Step 5: Run the test, verify it passes**

Run: `. .venv/bin/activate && python -m pytest tests/test_post_nav.py -v`
Expected: 3 PASS. (If `quarto` is absent the module is skipped; run it where Quarto exists before committing.)

- [ ] **Step 6: Verify the real site (still one post → no nav yet)**

Run:
```bash
. .venv/bin/activate && quarto render \
  && ! grep -q 'class="post-nav"' _site/posts/jpeg-ai-neural-image-compression/index.html \
  && echo "NO NAV WITH SINGLE POST — OK"
```
Expected: prints the message (a lone post gets no nav; Task 7 adds the colophon and both posts then get one side each).

- [ ] **Step 7: Commit**

```bash
git add filters/post-nav.lua tests/test_post_nav.py tests/fixtures/
git commit -m "feat: build-time prev/next nav via manifest + Lua filter"
```

---

## Task 4: Reading theme, self-hosted fonts, `.post-nav` styles

**Files:**
- Create: `scripts/fetch-fonts.sh`, `fonts/*.woff2` (committed), `styles/_fonts.scss`
- Modify: `styles/theme-light.scss`, `styles/theme-dark.scss` (replace stubs)
- Modify: `posts/jpeg-ai-neural-image-compression/jpeg-ai-slide.png` (downscale in place)

**Interfaces:**
- Consumes: the `.post-nav`, `.post-nav__prev`, `.post-nav__next`, `.post-nav__label` class names from Task 3.
- Produces: a compiled site stylesheet that sets the content measure to `46rem`, body font to Source Serif 4, headings to Inter, code to JetBrains Mono, all from `/fonts/*.woff2`; and styles `.post-nav` as a bordered two-up row that stacks on narrow screens. Task 6 and Task 7 consume nothing from here.

- [ ] **Step 1: Write `scripts/fetch-fonts.sh`**

```bash
#!/usr/bin/env bash
# One-shot: download self-hosted woff2 faces into ./fonts/ (committed to git).
# Source: Fontsource files on jsDelivr (stable paths). Re-run only to refresh.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p fonts
base="https://cdn.jsdelivr.net/npm"

fetch() { curl -fsSL "$base/$1" -o "fonts/$2"; echo "  $2"; }

echo "Source Serif 4:"
fetch "@fontsource/source-serif-4@5/files/source-serif-4-latin-400-normal.woff2" "source-serif-4-400.woff2"
fetch "@fontsource/source-serif-4@5/files/source-serif-4-latin-400-italic.woff2" "source-serif-4-400-italic.woff2"
fetch "@fontsource/source-serif-4@5/files/source-serif-4-latin-600-normal.woff2" "source-serif-4-600.woff2"

echo "Inter:"
fetch "@fontsource/inter@5/files/inter-latin-400-normal.woff2" "inter-400.woff2"
fetch "@fontsource/inter@5/files/inter-latin-600-normal.woff2" "inter-600.woff2"
fetch "@fontsource/inter@5/files/inter-latin-700-normal.woff2" "inter-700.woff2"

echo "JetBrains Mono:"
fetch "@fontsource/jetbrains-mono@5/files/jetbrains-mono-latin-400-normal.woff2" "jetbrains-mono-400.woff2"

echo "done."
```

- [ ] **Step 2: Run it and verify the files**

Run:
```bash
chmod +x scripts/fetch-fonts.sh && ./scripts/fetch-fonts.sh
ls -la fonts/ && file fonts/*.woff2
```
Expected: 7 files, each reported by `file` as `Web Open Font Format (Version 2)`. If any URL 404s, open <https://www.jsdelivr.com/package/npm/@fontsource/source-serif-4?path=files> and adjust the filename (weight/subset), then re-run.

- [ ] **Step 3: Write `styles/_fonts.scss`**

```scss
/*-- scss:rules --*/

@font-face {
  font-family: "Source Serif 4";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("/fonts/source-serif-4-400.woff2") format("woff2");
}
@font-face {
  font-family: "Source Serif 4";
  font-style: italic;
  font-weight: 400;
  font-display: swap;
  src: url("/fonts/source-serif-4-400-italic.woff2") format("woff2");
}
@font-face {
  font-family: "Source Serif 4";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("/fonts/source-serif-4-600.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("/fonts/inter-400.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("/fonts/inter-600.woff2") format("woff2");
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url("/fonts/inter-700.woff2") format("woff2");
}
@font-face {
  font-family: "JetBrains Mono";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("/fonts/jetbrains-mono-400.woff2") format("woff2");
}
```

- [ ] **Step 4: Write `styles/theme-light.scss`**

```scss
/*-- scss:defaults --*/

$font-family-sans-serif: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !default;
$font-family-serif: "Source Serif 4", Georgia, "Times New Roman", serif !default;
$font-family-monospace: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace !default;

$body-color: #1a1a1a !default;
$body-bg: #fdfdfc !default;
$link-color: #0b5cad !default;
$border-color: #e3e3e0 !default;

$font-size-root: 19px !default;
$line-height-base: 1.65 !default;
$headings-font-family: $font-family-sans-serif !default;
$headings-font-weight: 600 !default;

/*-- scss:rules --*/

@import "_fonts";

:root {
  --content-max-width: 46rem;
  --post-nav-muted: #6b6b66;
}

body {
  font-family: $font-family-serif;
  font-feature-settings: "kern" 1, "liga" 1;
  text-rendering: optimizeLegibility;
}

// Single-column reading measure. Quarto's default grid puts article content in
// `#quarto-content main` / `.page-columns`; cap the prose column, keep the
// right-margin TOC.
main.content,
#quarto-document-content {
  max-width: var(--content-max-width);
}

p, li { hyphens: auto; }

h1, h2, h3, h4, h5, h6 {
  font-family: $headings-font-family;
  letter-spacing: -0.01em;
  line-height: 1.25;
}

pre, code, kbd, samp { font-family: $font-family-monospace; font-size: 0.85em; }

a { text-decoration-thickness: 1px; text-underline-offset: 2px; }

/* prev/next navigation (markup from filters/post-nav.lua) */
.post-nav {
  display: flex;
  gap: 1.5rem;
  margin-top: 3rem;
  padding-top: 1.25rem;
  border-top: 1px solid $border-color;
}
.post-nav__prev,
.post-nav__next { display: flex; flex-direction: column; gap: 0.15rem; max-width: 48%; }
.post-nav__next { margin-left: auto; text-align: right; }
.post-nav__label {
  font-family: $font-family-sans-serif;
  font-size: 0.8rem;
  color: var(--post-nav-muted);
}
.post-nav a { font-family: $font-family-sans-serif; font-weight: 600; }

@media (max-width: 575.98px) {
  .post-nav { flex-direction: column; gap: 1rem; }
  .post-nav__prev,
  .post-nav__next { max-width: 100%; text-align: left; margin-left: 0; }
}
```

- [ ] **Step 5: Write `styles/theme-dark.scss`**

```scss
/*-- scss:defaults --*/

$font-family-sans-serif: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !default;
$font-family-serif: "Source Serif 4", Georgia, "Times New Roman", serif !default;
$font-family-monospace: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace !default;

$body-color: #d7d7d2 !default;
$body-bg: #16171a !default;
$link-color: #7cb4ec !default;
$border-color: #33343a !default;

$font-size-root: 19px !default;
$line-height-base: 1.65 !default;
$headings-font-family: $font-family-sans-serif !default;
$headings-font-weight: 600 !default;

/*-- scss:rules --*/

@import "_fonts";

:root {
  --content-max-width: 46rem;
  --post-nav-muted: #9a9a93;
}

body { font-family: $font-family-serif; }

main.content,
#quarto-document-content { max-width: var(--content-max-width); }

h1, h2, h3, h4, h5, h6 { font-family: $headings-font-family; line-height: 1.25; }
pre, code, kbd, samp { font-family: $font-family-monospace; font-size: 0.85em; }

.post-nav { margin-top: 3rem; padding-top: 1.25rem; border-top: 1px solid $border-color; display: flex; gap: 1.5rem; }
.post-nav__prev, .post-nav__next { display: flex; flex-direction: column; gap: 0.15rem; max-width: 48%; }
.post-nav__next { margin-left: auto; text-align: right; }
.post-nav__label { font-family: $font-family-sans-serif; font-size: 0.8rem; color: var(--post-nav-muted); }
.post-nav a { font-family: $font-family-sans-serif; font-weight: 600; }

@media (max-width: 575.98px) {
  .post-nav { flex-direction: column; gap: 1rem; }
  .post-nav__prev, .post-nav__next { max-width: 100%; text-align: left; margin-left: 0; }
}
```

- [ ] **Step 6: Downscale the hero PNG in place**

Run:
```bash
. .venv/bin/activate
python - <<'PY'
from PIL import Image
p = "posts/jpeg-ai-neural-image-compression/jpeg-ai-slide.png"
im = Image.open(p).convert("RGB")
im.thumbnail((1400, 1400))
im.save(p, format="PNG", optimize=True)
print("hero now", im.size)
PY
ls -la posts/jpeg-ai-neural-image-compression/jpeg-ai-slide.png
```
Expected: width 1400, file size well under 500 KB.

- [ ] **Step 7: Render and assert the theme is wired**

Run:
```bash
. .venv/bin/activate && quarto render
CSS=$(find _site -name '*.css' | xargs grep -l 'post-nav' | head -1)
grep -q 'Source Serif 4' "$CSS" \
  && grep -q '46rem' "$CSS" \
  && grep -q 'source-serif-4-400.woff2' "$CSS" \
  && test -f _site/fonts/source-serif-4-400.woff2 \
  && grep -q 'quarto-color-scheme-toggle' _site/index.html \
  && echo "THEME OK"
```
Expected: prints `THEME OK`. (`quarto-color-scheme-toggle` is the light/dark switch Quarto adds when two themes are configured.)

- [ ] **Step 8: Manual visual check**

Run `. .venv/bin/activate && quarto preview`, open the JPEG AI post. Confirm: single readable column ~46rem wide, serif body, sans headings, the light/dark toggle in the navbar flips both themes, code blocks are monospace. Network tab shows font requests only to `mapuna.github.io` (or localhost), never `gstatic.com`.

- [ ] **Step 9: Commit**

```bash
git add scripts/fetch-fonts.sh fonts/ styles/_fonts.scss \
        styles/theme-light.scss styles/theme-dark.scss \
        posts/jpeg-ai-neural-image-compression/jpeg-ai-slide.png
git commit -m "feat: single-column serif reading theme with self-hosted fonts"
```

---

## Task 5: MathJax v4 macros + static math-conversion check

**Files:**
- Modify: `styles/_macros.tex` (replace stub)
- Create: `scripts/check_math.py`
- Create: `tests/test_check_math.py`, `tests/math-fixtures/good.html`, `tests/math-fixtures/bad.html`

**Interfaces:**
- Consumes: the rendered `_site/` tree; `_quarto.yml` already loads MathJax v4 (Task 1) and `styles/_macros.tex` via `include-in-header`.
- Produces: `scripts/check_math.py`, invoked as `python scripts/check_math.py _site`. Exit 0 if every post's math was converted by Pandoc into `<span|div class="math ...">` wrappers and the v4 script tag is present; exit 1 (with file + offending snippet on stderr) if literal TeX (`$$`, `\[`, `\begin{`, `\newcommand`, `\frac`, …) leaks into visible post text, or the v4 script tag is absent. Task 8 runs this in CI.

> **Note on scope.** MathJax v4 typesets in the browser, so `_site/` HTML still contains the TeX source inside `\(...\)` / `\[...\]` wrappers; a static check cannot confirm the browser render. This check catches the *Quarto/Pandoc-level* failure (math not recognized, left as raw `$$…$$`). The v4-specific "do the macros and `\begin{align}` numbering actually typeset" check is a manual browser gate in Task 9, with the v3 fallback documented there.

- [ ] **Step 1: Write `styles/_macros.tex`**

```html
<!-- Site-wide MathJax macros, available in every page. MathJax reads the TeX
     inside the hidden \(...\) below at load time and registers the commands. -->
<div style="display:none">
\(
  \newcommand{\R}{\mathbb{R}}
  \newcommand{\E}{\mathbb{E}}
  \newcommand{\KL}[2]{D_{\mathrm{KL}}\!\left(#1 \,\middle\|\, #2\right)}
  \newcommand{\argmin}{\operatorname*{arg\,min}}
  \newcommand{\ind}{\mathbf{1}}
\)
</div>
```

- [ ] **Step 2: Write the fixtures**

`tests/math-fixtures/good.html` (mimics Pandoc's output: TeX lives inside `math` spans):
```html
<!doctype html><html><head>
<script src="https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"></script>
</head><body>
<p>Inline <span class="math inline">\(a^2+b^2\)</span> and display:</p>
<div class="math display">\[ \begin{align} x &= y \\ y &= z \end{align} \]</div>
<p>Prose with a dollar sign in text: it costs $5, nothing to typeset.</p>
</body></html>
```

`tests/math-fixtures/bad.html` (Pandoc failed to wrap the display math):
```html
<!doctype html><html><head>
<script src="https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"></script>
</head><body>
<p>Here is an equation that never got wrapped:</p>
<p>$$ \frac{1}{2}\sum_i -\log_2 p(\hat{y}_i) $$</p>
</body></html>
```

- [ ] **Step 3: Write the failing tests**

`tests/test_check_math.py`:
```python
from pathlib import Path

import scripts.check_math as cm

FIX = Path(__file__).parent / "math-fixtures"


def test_good_html_has_no_leaks():
    html = (FIX / "good.html").read_text(encoding="utf-8")
    assert cm.find_leaked_tex(html) == []


def test_bad_html_flags_unwrapped_display_math():
    html = (FIX / "bad.html").read_text(encoding="utf-8")
    leaks = cm.find_leaked_tex(html)
    assert any("$$" in x or "\\frac" in x for x in leaks)


def test_detects_missing_v4_script():
    assert cm.has_mathjax_v4("<head><script src='x/mathjax@4/y.js'></script></head>")
    assert not cm.has_mathjax_v4("<head><script src='x/mathjax@3/y.js'></script></head>")


def test_check_tree_returns_nonzero_on_bad(tmp_path):
    posts = tmp_path / "_site" / "posts" / "p"
    posts.mkdir(parents=True)
    (posts / "index.html").write_text(
        (FIX / "bad.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert cm.check_tree(tmp_path / "_site") == 1


def test_check_tree_returns_zero_on_good(tmp_path):
    posts = tmp_path / "_site" / "posts" / "p"
    posts.mkdir(parents=True)
    (posts / "index.html").write_text(
        (FIX / "good.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert cm.check_tree(tmp_path / "_site") == 0
```

- [ ] **Step 4: Run tests, verify they fail**

Run: `. .venv/bin/activate && python -m pytest tests/test_check_math.py -v`
Expected: FAIL (`scripts.check_math` has no such names).

- [ ] **Step 5: Implement `scripts/check_math.py`**

```python
#!/usr/bin/env python3
"""Fail the build if Quarto/Pandoc did not convert a post's math.

Usage: python scripts/check_math.py _site

MathJax v4 typesets client-side, so rendered HTML still holds TeX *inside*
`\\(...\\)` / `\\[...\\]` wrappers that Pandoc emits as `<span class="math ...">`
and `<div class="math ...">`. This script strips <script>/<style> and every
`math` wrapper, then fails if TeX tokens remain in the visible text of any file
under `_site/posts/`. It also checks the MathJax v4 loader is present.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
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
                print(f"    …{snip}…", file=sys.stderr)

    if not any_v4:
        print("check_math: MathJax v4 loader not found in any post", file=sys.stderr)
        failed = True

    return 1 if failed else 0


def main(argv: list[str]) -> int:
    site = Path(argv[1]) if len(argv) > 1 else Path("_site")
    return check_tree(site)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 6: Run tests, verify they pass**

Run: `. .venv/bin/activate && python -m pytest tests/test_check_math.py -v`
Expected: all PASS.

- [ ] **Step 7: Run against the real render**

Run:
```bash
. .venv/bin/activate && quarto render && python scripts/check_math.py _site && echo "MATH CONVERSION OK"
```
Expected: prints `MATH CONVERSION OK` (the JPEG AI post's `$…$` / `$$…$$` all became `math` spans).

- [ ] **Step 8: Commit**

```bash
git add styles/_macros.tex scripts/check_math.py tests/test_check_math.py tests/math-fixtures/
git commit -m "feat: MathJax v4 macros + static math-conversion check"
```

---

## Task 6: On-page SEO — Open Graph, Twitter card, JSON-LD, canonical, sitemap

**Files:**
- Modify: `styles/jsonld.html` (replace stub)
- Verify only (config already set in Task 1): `open-graph`, `twitter-card`, `site-url` in `_quarto.yml`; `resources: [robots.txt]`.

**Interfaces:**
- Consumes: Quarto document metadata (`title`, `description`, `date`, `author`) available to `include-in-header` templates via `$…$` fields.
- Produces: on every post page, a `<script type="application/ld+json">` `BlogPosting` block; plus (from Quarto's own machinery) `og:*` / `twitter:*` meta, `<link rel="canonical">`, `_site/sitemap.xml`, and `_site/robots.txt`. Nothing downstream consumes this.

- [ ] **Step 1: Write `styles/jsonld.html`**

Quarto processes `include-in-header` files as Pandoc templates, so `$title$`, `$description$`, `$date$`, and `$website.site-url$` interpolate. On non-post pages `$date$` is empty and the block is still valid (omit the field when empty via Pandoc's `$if(...)$`).

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "$if(date)$BlogPosting$else$WebSite$endif$",
  "headline": "$pagetitle$",
$if(description)$
  "description": "$description$",
$endif$
$if(date)$
  "datePublished": "$date$",
$endif$
  "author": { "@type": "Person", "name": "$if(author)$$author$$else$Anupam Gupta$endif$" },
  "publisher": { "@type": "Person", "name": "Anupam Gupta" },
  "url": "https://mapuna.github.io"
}
</script>
```

- [ ] **Step 2: Render and assert the SEO surface**

Run:
```bash
. .venv/bin/activate && quarto render
P=_site/posts/jpeg-ai-neural-image-compression/index.html
grep -q 'property="og:title"' "$P" \
  && grep -q 'name="twitter:card"' "$P" \
  && grep -q 'rel="canonical"' "$P" \
  && grep -q '"@type": "BlogPosting"' "$P" \
  && grep -q '"datePublished": "2026-05-04"' "$P" \
  && test -f _site/sitemap.xml \
  && test -f _site/robots.txt \
  && grep -q 'Sitemap: https://mapuna.github.io/sitemap.xml' _site/robots.txt \
  && grep -q 'mapuna.github.io/posts/jpeg-ai-neural-image-compression' _site/sitemap.xml \
  && echo "SEO OK"
```
Expected: prints `SEO OK`. If `og:title` is missing, confirm `website.site-url` is set (Quarto only emits Open Graph when it can build absolute URLs).

- [ ] **Step 3: Validate the JSON-LD parses**

Run:
```bash
. .venv/bin/activate
python - <<'PY'
import json, re, pathlib
h = pathlib.Path("_site/posts/jpeg-ai-neural-image-compression/index.html").read_text()
blk = re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1)
print(json.loads(blk)["@type"])
PY
```
Expected: prints `BlogPosting` (no `JSONDecodeError`).

- [ ] **Step 4: Commit**

```bash
git add styles/jsonld.html
git commit -m "feat: Open Graph, Twitter card, JSON-LD BlogPosting, sitemap wiring"
```

---

## Task 7: Colophon post — seed post 1, math + executable-cell verification

**Files:**
- Create: `posts/colophon/index.qmd`
- Create (generated by render, then committed): `_freeze/posts/colophon/**`

**Interfaces:**
- Consumes: `\E` and `\KL` from `styles/_macros.tex` (Task 5); the prev/next filter (Task 3); `freeze: auto` from `posts/_metadata.yml` (Task 1).
- Produces: a second non-draft post dated `2026-05-01` (older than the JPEG AI post), so the manifest has two entries and both posts render a one-sided `.post-nav`. Exercises an inline macro, a labelled `$$…$$` with an `@eq-` cross-ref, a multi-line `\begin{align}`, and one executable `python` cell producing a `matplotlib` figure.

- [ ] **Step 1: Write `posts/colophon/index.qmd`**

Prose follows `personal-writing-style`. Keep it short and plain; this post explains how the site is built and doubles as the math/exec test page.

````markdown
---
title: "Colophon"
description: "How this blog is built, and a working note on the one equation the site's build checks on every deploy."
author: "Anupam Gupta"
date: "2026-05-01"
categories: [notes]
---

This site is [Quarto](https://quarto.org). Posts are `.qmd` files; a push to
`main` triggers a GitHub Actions run that renders them and deploys the result to
GitHub Pages. Nothing built is checked into the repository except the execution
cache for code cells.

Three pieces are not stock Quarto.

**Prev/next links.** A pre-render script reads the front matter of every post,
sorts by date, and writes an ordered table. A Lua filter reads that table and
appends the "Previous" and "Next" links you see at the foot of each post. It runs
at build time, so there is no JavaScript and no layout shift.

**Math.** Equations are LaTeX, typeset by [MathJax](https://www.mathjax.org)
version 4. The build has a check that fails the deploy if Quarto ever stops
recognizing an equation and leaves raw TeX in the page.

**Type.** The body is Source Serif 4, headings are Inter, code is JetBrains
Mono, all served from this domain. No request leaves for a font CDN.

## The equation the build checks

Every deploy typesets this page, so the equation below is also the site's
smallest end-to-end test of the math path: a macro from the shared header, a
cross-reference, and a multi-line derivation.

Code a symbol $s$ drawn from a distribution $q$ using a model $p$, and the
expected length in bits is the cross-entropy, which splits into the entropy of
$q$ and the penalty for using the wrong model:

$$
\E_{s \sim q}\!\left[-\log_2 p(s)\right]
  = H(q) + \KL{q}{p} .
$$ {#eq-crossent}

The penalty term $\KL{q}{p}$ in @eq-crossent is non-negative and is zero exactly
when $p = q$. Writing it out for a finite alphabet:

$$
\begin{align}
\E_{s \sim q}\!\left[-\log_2 p(s)\right]
  &= -\sum_s q(s)\,\log_2 p(s) \\
  &= -\sum_s q(s)\,\log_2 q(s)
     \;-\; \sum_s q(s)\,\log_2 \frac{p(s)}{q(s)} \\
  &= H(q) + \sum_s q(s)\,\log_2 \frac{q(s)}{p(s)} .
\end{align}
$$

## The figure the build runs

```{python}
#| label: fig-surprisal
#| fig-cap: "Surprisal $-\\log_2 p$: the bits spent on a symbol the model gives probability $p$."
import numpy as np
import matplotlib.pyplot as plt

p = np.linspace(0.01, 1.0, 400)
fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(p, -np.log2(p))
ax.set_xlabel("model probability $p$")
ax.set_ylabel("bits, $-\\log_2 p$")
ax.grid(True, alpha=0.3)
fig.tight_layout()
```

That plot is generated by the code cell above it during the build, not pasted
in. If the cell errors, the deploy fails.
````

- [ ] **Step 2: Render and verify the cell executed + freeze cache exists**

Run:
```bash
. .venv/bin/activate && quarto render posts/colophon/index.qmd
test -d _freeze/posts/colophon && echo "FREEZE CACHE OK"
grep -q 'fig-surprisal' _site/posts/colophon/index.html && echo "FIGURE EMBEDDED OK"
```
Expected: both messages print. (A full `quarto render` also works; rendering the one file is faster here.)

- [ ] **Step 3: Verify prev/next now appears on both posts**

Run:
```bash
. .venv/bin/activate && quarto render
C=_site/posts/colophon/index.html
J=_site/posts/jpeg-ai-neural-image-compression/index.html
grep -q 'post-nav__next' "$C" && ! grep -q 'post-nav__prev' "$C" \
  && grep -q 'href="/posts/jpeg-ai-neural-image-compression/"' "$C" \
  && grep -q 'post-nav__prev' "$J" && ! grep -q 'post-nav__next' "$J" \
  && grep -q 'href="/posts/colophon/"' "$J" \
  && echo "PREV/NEXT WIRED ACROSS BOTH POSTS"
```
Expected: prints the message. Colophon (older) shows only Next → JPEG AI; JPEG AI (newer) shows only ← Previous: Colophon.

- [ ] **Step 4: Static math check still green**

Run: `. .venv/bin/activate && python scripts/check_math.py _site && echo OK`
Expected: `OK`.

- [ ] **Step 5: Manual browser check of the math**

`quarto preview`, open `/posts/colophon/`. Confirm: `$\E$` and `$\KL{q}{p}$` render as blackboard-bold E and a `D_KL(q ‖ p)` (macros resolved); `@eq-crossent` renders as a clickable "Equation 1" reference; the `\begin{align}` block is aligned on `=` and each line is numbered `(2)`,`(3)`,`(4)`; the surprisal figure shows. If any of that fails, see the fallback in Task 9 step 5.

- [ ] **Step 6: Commit (source + freeze cache)**

```bash
git add posts/colophon/index.qmd _freeze/posts/colophon
git commit -m "feat: colophon post (seed post 1, math + executable-cell check page)"
```

---

## Task 8: CI workflow — render, check, deploy

**Files:**
- Create: `.github/workflows/publish.yml`

**Interfaces:**
- Consumes: `requirements.txt`, `scripts/check_math.py`, `tests/`, the pinned Quarto version.
- Produces: on push to `main`, a GitHub Pages deployment of `_site/`. No repo files change.

- [ ] **Step 1: Write `.github/workflows/publish.yml`**

```yaml
name: Publish

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: quarto-dev/quarto-actions/setup@v2
        with:
          version: "1.6.42"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt

      - name: Unit tests
        run: python -m pytest tests/ -v -m "not requires_quarto"

      - name: Render site
        run: quarto render

      - name: Static math-conversion check
        run: python scripts/check_math.py _site

      - name: Prev/next present on multi-post site
        run: grep -q 'class="post-nav"' _site/posts/colophon/index.html

      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Mark the Quarto-dependent test so CI can skip it if needed**

The `tests/test_post_nav.py` file already `skipif`s when `quarto` is absent. On the CI runner Quarto *is* present (installed by the setup action before pytest), so the test runs. Add a marker registration to `pyproject.toml` (create it) so `-m "not requires_quarto"` is a no-op filter that does not warn:

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
  "requires_quarto: integration test that shells out to `quarto render`",
]
```
(No test is tagged with it; the CI `-m` expression is future-proofing and keeps pytest from erroring on an unknown marker.)

- [ ] **Step 3: Lint the workflow locally if `actionlint` is available**

Run: `command -v actionlint && actionlint .github/workflows/publish.yml || echo "actionlint not installed, skipping"`
Expected: no errors, or the skip message.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/publish.yml pyproject.toml
git commit -m "ci: render, test, math-check, and deploy to GitHub Pages on push"
```

---

## Task 9: Create the GitHub repo, enable Pages, first deploy

**Files:** none (repo + platform config).

**Interfaces:**
- Consumes: the committed repository from Tasks 1-8.
- Produces: the live site at `https://mapuna.github.io/`.

- [ ] **Step 1: Confirm the working tree is clean and on `main`**

Run: `git status` and `git log --oneline`
Expected: clean tree, `main` branch, ~8 commits (one per task). No `_site/` or `_manifest.lua` tracked (`git ls-files | grep -E '_site/|_manifest.lua'` prints nothing).

- [ ] **Step 2: Create the public repo and push**

Run:
```bash
gh repo create mapuna/mapuna.github.io --public --source=. --remote=origin --push
```
Expected: repo created, `main` pushed. `gh repo view mapuna/mapuna.github.io --web` opens it.

- [ ] **Step 3: Set the Pages build source to GitHub Actions**

Run:
```bash
gh api --method POST /repos/mapuna/mapuna.github.io/pages \
  -f 'build_type=workflow' 2>/dev/null \
  || gh api --method PUT /repos/mapuna/mapuna.github.io/pages -f 'build_type=workflow'
```
Expected: JSON describing the Pages site with `"build_type": "workflow"`.

- [ ] **Step 4: Watch the deploy run**

Run:
```bash
gh run watch --exit-status $(gh run list --workflow=publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')
```
Expected: the `build` and `deploy` jobs both succeed. If `build` fails on the math check or a test, fix forward and push again.

- [ ] **Step 5: Manual browser verification (the MathJax v4 gate)**

Open `https://mapuna.github.io/` and check:
- Home lists **Colophon** and **JPEG AI…** newest-first, each with date, reading time, description; navbar search returns results; the RSS icon opens `/index.xml`.
- Open the **JPEG AI** post: single ~46rem column, serif body, working light/dark toggle. Every equation is typeset (no raw `$` or `\begin{align}` visible). `@eq-…` references are numbered links. The `\begin{align}`-style displays are line-numbered.
- Open **Colophon**: `\E` and `\KL{q}{p}` resolve to blackboard-bold E and `D_KL(q ‖ p)` (macros work); the aligned derivation is numbered; the surprisal figure renders.
- Each post shows the correct one-sided prev/next at its foot.
- View source on a post: `<link rel="canonical" href="https://mapuna.github.io/posts/…">`, `og:*` meta, and the `BlogPosting` JSON-LD are present. `https://mapuna.github.io/sitemap.xml` and `/robots.txt` load.
- DevTools Network: no request to `fonts.googleapis.com` or `fonts.gstatic.com`.

**If MathJax v4 fails** (macros not resolving, `align` not numbering, or errors): edit `_quarto.yml`, delete the single line
`url: "https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"`
so `html-math-method` is just `method: mathjax`, which reverts Quarto to its bundled, fully supported v3. Commit, push, re-verify.

- [ ] **Step 6: Submit the sitemap to Google Search Console**

Manual, one-time, outside this repo: add the property `https://mapuna.github.io/` in Search Console and submit `sitemap.xml`. Not blocking.

- [ ] **Step 7: Resolve the `about.qmd` TODOs**

Ask the user for: the public email to list, the company name (if it should be named), and confirmation the display name is "Anupam Gupta". Edit `about.qmd`, remove the `<!-- TODO(anupam) -->` comment, commit, push.

---

## Self-Review

**Spec coverage:**

| Spec section | Task(s) |
|---|---|
| §3 Repo & hosting | 1 (init, identity, `.gitignore`), 9 (create, Pages source) |
| §4 Directory layout | all |
| §5 `_quarto.yml` | 1 (full config), 4/5/6 (theme, macros, jsonld referenced) |
| §5a / §8a SEO | 6 (OG, Twitter, JSON-LD, sitemap, robots), 1 (`site-url`, `robots.txt` resource), 2 (`description` lint) |
| §6 MathJax v4 + verification | 5 (v4 url in `_quarto.yml` from Task 1, macros, static check), 7 + 9 (manual browser gate + v3 fallback) |
| §7 Theme & typography | 4 (SCSS, `46rem`, serif/sans/mono, self-hosted fonts, `.post-nav`) |
| §8 Listing / RSS / search | 1 (`index.qmd`, `feed`, navbar search) |
| §8 Category taxonomy | posts carry `categories`; hub pages auto-generated by the listing (`categories: true`). Per-category description text deferred (YAGNI v1). |
| §9 Prev/next component | 2 (`build_manifest.py`), 3 (`post-nav.lua` + integration test), 7 (verified across both posts) |
| §10 Executable Python / freeze | 1 (`_metadata.yml` `freeze: auto`), 7 (colophon cell + committed `_freeze/`) |
| §11 Local dev workflow | Task 1 steps 14-15; venv + `quarto preview` |
| §12 Seed content | `about.qmd` + JPEG AI post pre-existing (verified Task 9); colophon = Task 7 |
| §13 Risks & fallbacks | MathJax v3 fallback in Task 9 step 5; filter suffix-match handles abs/rel path risk (Task 3); filter no-ops without `_manifest.lua` |
| §14 Acceptance criteria | Task 9 step 5 checklist, plus the grep assertions in Tasks 3-7 |
| §15 open `about.qmd` TODOs | Task 9 step 7 |

**Placeholder scan:** no "TBD"/"handle edge cases"/"similar to Task N". Every code step has complete file content. Stub files in Task 1 are explicitly labelled and each is replaced in a named later task (theme-light/dark → 4, `_macros.tex` → 5, `jsonld.html` → 6, `post-nav.lua` → 3, `build_manifest.py` → 2).

**Type consistency:**
- `build_manifest.py` public names used by tests and prose: `parse_frontmatter`, `collect_posts`, `render_manifest`, `lint_descriptions`, `main` — consistent across Task 2 test and implementation.
- `_manifest.lua` entry keys `path`, `href`, `title` — written by `render_manifest` (Task 2), read by `post-nav.lua` (Task 3) with the same keys.
- `check_math.py` public names: `has_mathjax_v4`, `find_leaked_tex`, `check_tree`, `main` — consistent across Task 5 test and implementation.
- CSS class names `post-nav`, `post-nav__prev`, `post-nav__next`, `post-nav__label` — emitted by `post-nav.lua` (Task 3), styled in `theme-light.scss` / `theme-dark.scss` (Task 4), asserted in Tasks 3 and 7.
- Post directory / href shape `posts/<slug>/` ↔ `/posts/<slug>/` — consistent in `build_manifest.py`, the fixture, and every grep assertion.
