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
