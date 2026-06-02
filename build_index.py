#!/usr/bin/env python3
"""Build index.json — the consolidated kit catalog CAT consumes in ONE fetch.

    python build_index.py            # write ./index.json from the kits
    python build_index.py -          # print to stdout

A data product: a single JSON file of kit SUMMARIES (name/title/description/
maintainers/applies_to) regenerated whenever a kit changes (the public repo's
build-index workflow runs this on merge to main).  CAT reads it instead of
walking the tree (N+1 fetches -> 1); it falls back to the live walk if the index
is missing, so the index is an optimization, never a dependency.

Only the SUMMARY fields go in the index (what list_kits / search_kits need); the
full kit body (context/skills/resources) is fetched by bbot's render_kit.py at
spawn time, by name, straight from the YAML.  Deterministic output (sorted) so
an unchanged catalog produces an identical file (no spurious commits).

stdlib + PyYAML only -- matches validate.py so it runs in the public repo's CI.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_VERSION = 1


def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def summarize(k: dict) -> dict:
    """The compact view CAT reasons over -- must match partner.kits.summarize."""
    a = k.get("applies_to") or {}
    if not isinstance(a, dict):
        a = {}
    return {
        "name": k.get("name", ""),
        "title": k.get("title") or k.get("name", ""),
        "description": k.get("description", ""),
        "maintainers": _as_list(k.get("maintainers")),
        "applies_to": {
            "profile": _as_list(a.get("profile")),
            "deliverable": _as_list(a.get("deliverable")),
            "topics": _as_list(a.get("topics")),
        },
    }


def _discover() -> list[str]:
    """kits/*.yaml (public-repo layout) if present, else *.yaml here (ops seed)."""
    sub = sorted(glob.glob(os.path.join(_HERE, "kits", "*.yaml")))
    return sub or sorted(glob.glob(os.path.join(_HERE, "*.yaml")))


def build() -> dict:
    kits: list[dict] = []
    for path in _discover():
        try:
            with open(path) as f:
                k = yaml.safe_load(f) or {}
        except Exception as e:
            sys.stderr.write(f"skip {path}: parse error ({e})\n")
            continue
        if isinstance(k, dict) and k.get("name"):
            kits.append(summarize(k))
        else:
            sys.stderr.write(f"skip {path}: not a valid kit\n")
    kits.sort(key=lambda s: s["name"])
    return {"version": INDEX_VERSION, "kits": kits}


def main(argv: list[str]) -> int:
    index = build()
    text = json.dumps(index, indent=2, sort_keys=True) + "\n"
    if len(argv) > 1 and argv[1] == "-":
        sys.stdout.write(text)
    else:
        out = os.path.join(_HERE, "index.json")
        with open(out, "w") as f:
            f.write(text)
        sys.stderr.write(f"wrote {out} ({len(index['kits'])} kit(s))\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
