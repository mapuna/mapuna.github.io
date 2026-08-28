# Bits and Priors

Source for <https://mapuna.github.io/>. Quarto website, deployed by GitHub Actions
on every push to `main`.

This file is the authoring guide. It is excluded from the rendered site.

---

## TL;DR — publish a new post

```bash
cd ~/src/web/mapuna.github.io
git pull

mkdir posts/my-post-slug
$EDITOR posts/my-post-slug/index.qmd     # write it (template below)

. .venv/bin/activate
quarto preview                            # live preview at localhost:port

git add posts/my-post-slug _freeze/       # _freeze only if the post runs code
git commit -m "post: my post title"
git push
```

Push to `main` → CI renders, runs the checks, deploys. Live in ~1 minute.
Watch it: `gh run watch --repo mapuna/mapuna.github.io`.

---

## One-time machine setup

Already done on this machine. Needed only on a fresh clone:

```bash
git clone https://github.com/mapuna/mapuna.github.io.git
cd mapuna.github.io

# commit as yourself, not the machine's global git identity
git config user.name  "mapuna"
git config user.email "mapuna_@outlook.com"

# push over HTTPS using the gh CLI's credentials (SSH on this machine
# resolves to the wrong GitHub account)
git config credential.helper ""
git config --add credential.helper '!gh auth git-credential'

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

`gh` must be logged in as `mapuna` (`gh auth status`) with the `workflow` scope
(`gh auth refresh -h github.com -s workflow` if a push ever complains about it).

Every working session: `. .venv/bin/activate` first.

---

## Writing a post

One post = one directory under `posts/`. The directory name is the URL slug
(`posts/jpeg-ai-neural-image-compression/` → `/posts/jpeg-ai-neural-image-compression/`).
No date in the directory name. The file is always `index.qmd`. Images and data
sit next to it in the same directory.

### Front-matter template

```yaml
---
title: "Post Title in Title Case"
description: >
  One sentence, 150 chars or so, hard cap 200. Shows on the home listing, in
  the RSS feed, and as the search-engine and social-card snippet.
author: "Anupam Gupta"
date: "2026-06-15"            # ISO 8601, YYYY-MM-DD
categories: [machine-learning, information-theory]
# optional:
image: cover.webp            # listing thumbnail + social card (put file in this dir)
image-alt: "Plain description of the cover image."
number-sections: true        # numbered headings + Section N cross-refs (long/technical posts)
draft: true                  # exclude from listing, feed, prev/next until removed
---
```

`toc: true` and `freeze: auto` are already set for all posts in
`posts/_metadata.yml`; don't repeat them.

### Categories

Pick from this set (a post can have several). Add a new one only if it will
recur.

`machine-learning` · `information-theory` · `compression` · `computer-vision` ·
`nlp` · `llm` · `conversational-ai` · `multimodal-ai` · `systems` · `ai-safety` ·
`notes`

Each category auto-generates a hub page at `/#category=<slug>`.

### House rules (enforced by review, some by the build)

- **Headings: Title Case, compact noun phrases.** "Task-Aware Coding for Machine
  Vision", never "Baby-steps to the Ludicrous Idea" or a full sentence.
- **Prose is justified automatically** by the theme. Nothing to do.
- **Style:** direct, first person, derive rather than assert, verbosity is fine
  when it explains. No em dashes, no `leverage`/`utilize`/`robust`, no
  `somewhat`/`arguably` hedges. American spelling.
- **`description` is required** and must be ≤ 200 characters. The build fails
  otherwise (see Troubleshooting).

---

## Math

Inline `$…$`, display `$$…$$`. Typeset in the browser by MathJax v4.

**Shared macros** (defined in `styles/_macros.tex`, available everywhere):

| Macro | Renders |
|-------|---------|
| `\R` | ℝ |
| `\E` | 𝔼 |
| `\KL{q}{p}` | D_KL(q ‖ p) |
| `\argmin` | arg min (with subscript support: `\argmin_x`) |
| `\ind` | 𝟏 (indicator) |

Add a macro by editing `styles/_macros.tex` (keep it inside the hidden
`\(...\)` block).

**Numbered equations and cross-references** (needs `number-sections: true` for
section refs; equation refs work regardless):

```markdown
$$
\mathcal{L} = D(x, \hat{x}) + \lambda R
$$ {#eq-cost}

...as @eq-cost shows...      <!-- renders "as Equation 1 shows" -->
```

Multi-line alignment:

```markdown
$$
\begin{align}
  a &= b + c \\
    &= d
\end{align}
$$
```

The build has a check (`scripts/check_math.py`) that **fails the deploy** if
Quarto ever stops recognizing an equation and leaves raw TeX on the page.

---

## Code cells (Python)

````markdown
```{python}
#| label: fig-example
#| fig-cap: "What the figure shows."
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(np.linspace(0, 1), np.linspace(0, 1) ** 2)
fig.tight_layout()
```
````

- Cells run at build time. Their output (figures, tables) is generated, not
  pasted.
- `freeze: auto` means a post re-executes only when its own `.qmd` changes. The
  cache lives in `_freeze/` and **must be committed** alongside the post:
  `git add posts/<slug> _freeze/`.
- If a cell imports a library not in `requirements.txt`, add it there in the
  same commit, or CI can't run the cell.
- A cell that raises fails the deploy.

Run `quarto render posts/<slug>/index.qmd` once locally before committing so the
`_freeze/` cache is fresh.

---

## Images

- Put the file in the post's directory; reference it by bare name:
  `![Alt text.](cover.webp)`.
- **Photos / gradients → WebP**, quality ~82. PNGs of that kind are 10× larger.
  ```bash
  python -c "from PIL import Image; im=Image.open('in.png').convert('RGB'); \
  im.thumbnail((1400,1400)); im.save('cover.webp','WEBP',quality=82,method=6)"
  ```
- Diagrams / screenshots with flat color → PNG is fine.
- Always write real alt text. For the social card, also set `image:` /
  `image-alt:` in the front matter.

---

## Prev/next

Automatic. `scripts/build_manifest.py` runs before every render, sorts
non-draft posts by `date`, and a Lua filter appends the "← Previous" (older) /
"Next →" (newer) block to each post. Nothing to add to the post itself.
`draft: true` posts are skipped.

---

## Preview and publish

```bash
. .venv/bin/activate
quarto preview          # rebuilds on save; open the printed localhost URL
```

When it looks right:

```bash
git add posts/<slug> _freeze/          # _freeze/ only if the post has code cells
git commit -m "post: <title>"
git push
gh run watch --repo mapuna/mapuna.github.io --exit-status \
  "$(gh run list --repo mapuna/mapuna.github.io --workflow=publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

CI does: install deps → `pytest` → `quarto render` → `check_math.py` →
prev/next sanity check → deploy to Pages. A red run does not deploy; fix and
push again.

Never commit `_site/`, `.quarto/`, or `_manifest.lua` (all gitignored).

---

## Editing an existing post

Edit the file, `quarto preview`, and if it has code cells,
`quarto render posts/<slug>/index.qmd` to refresh `_freeze/`. Commit the `.qmd`
and any changed `_freeze/` files. Changing a post's `date` reorders the whole
prev/next chain.

---

## Troubleshooting

**`build_manifest: description lint failed`** — a post has no `description`, or
one longer than 200 characters. Fix the front matter. (Cap is `MAX_DESCRIPTION`
in `scripts/build_manifest.py`.)

**`check_math: unconverted TeX in …`** — Quarto did not parse an equation
(usually an unbalanced `$$` or a `$` in prose that should be `\$`). Find it in
that file and fix the delimiters.

**MathJax renders raw TeX or a macro doesn't expand in the browser** — likely a
v4 incompatibility. Open `_quarto.yml` and delete the line
`url: "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js"` under
`html-math-method`. That reverts to Quarto's bundled MathJax v3. Commit, push.

**`refusing to allow an OAuth App to … workflow … without workflow scope`** on
push — run `gh auth refresh -h github.com -s workflow`, then push again.

**`Permission to mapuna/… denied to <other-account>`** on push — the credential
helper isn't set for this repo. Re-run the two `git config … credential.helper`
lines from *One-time machine setup*.

**CI warns about Node 20 deprecation** — cosmetic. Bump the action majors in
`.github/workflows/publish.yml` when convenient.

---

## Repo layout

```
_quarto.yml                 site config
index.qmd                   home = post listing + RSS
about.qmd                   about page
posts/<slug>/index.qmd      a post (+ its images/data)
posts/_metadata.yml         shared post defaults (toc, freeze)
styles/                     themes, fonts, MathJax macros
filters/post-nav.lua        prev/next injector
filters/jsonld.lua          canonical link + JSON-LD
scripts/build_manifest.py   pre-render: post manifest + description lint
scripts/check_math.py       CI: fails on unconverted math
scripts/fetch-fonts.sh      one-shot: refresh self-hosted woff2
fonts/                      self-hosted woff2 (committed)
tests/                      pytest suite for the scripts + a nav integration test
docs/design/                the design spec
docs/plans/                 the build plan
.github/workflows/publish.yml   CI
```
