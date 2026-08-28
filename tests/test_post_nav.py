import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "nav"

pytestmark = pytest.mark.skipif(
    shutil.which("quarto") is None, reason="quarto not on PATH"
)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    """Copy the fixture project plus the repo's scripts/ and filters/ into a
    temp dir, render it, and return the `_site/posts` path."""
    out = tmp_path_factory.mktemp("navsite")
    shutil.copytree(FIXTURE, out, dirs_exist_ok=True)
    shutil.copytree(REPO / "scripts", out / "scripts", dirs_exist_ok=True)
    shutil.copytree(REPO / "filters", out / "filters", dirs_exist_ok=True)
    subprocess.run(["quarto", "render"], cwd=out, check=True)
    return out / "_site" / "posts"


def _nav(rendered, slug):
    """The <nav class="post-nav"> ... </nav> substring for a post, or ''."""
    html = (rendered / slug / "index.html").read_text(encoding="utf-8")
    start = html.find('<nav class="post-nav">')
    if start == -1:
        return ""
    return html[start : html.find("</nav>", start) + len("</nav>")]


# Quarto localizes site-internal links (e.g. "/posts/01-first/" may render as
# "../../posts/01-first/"), so assertions match the slug tail, not an exact href.


def test_middle_post_has_both_prev_and_next(rendered):
    nav = _nav(rendered, "02-middle")
    assert "post-nav__prev" in nav and "post-nav__next" in nav
    assert "Previous" in nav and "Next" in nav
    assert '01-first/">First post</a>' in nav
    assert '03-last/">Last post</a>' in nav


def test_first_post_has_only_next(rendered):
    nav = _nav(rendered, "01-first")
    assert nav != ""
    assert "post-nav__prev" not in nav
    assert "post-nav__next" in nav
    assert '02-middle/">Middle post</a>' in nav


def test_last_post_has_only_prev(rendered):
    nav = _nav(rendered, "03-last")
    assert nav != ""
    assert "post-nav__next" not in nav
    assert "post-nav__prev" in nav
    assert '02-middle/">Middle post</a>' in nav
