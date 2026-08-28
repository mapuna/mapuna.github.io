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
    assert cm.has_mathjax_v4("<head><script src='x/mathjax@4.1.3/y.js'></script></head>")
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
