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
