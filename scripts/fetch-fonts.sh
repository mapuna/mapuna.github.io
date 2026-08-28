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
