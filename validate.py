#!/usr/bin/env python3
"""Validate kit YAML files against the kit format (see README.md).

    python validate.py <kit.yaml> ...     # specific files
    python validate.py                    # all *.yaml in this dir

Exit 0 if every kit is valid, 1 otherwise. stdlib + PyYAML only.

CANONICAL contract: the LinkML `Kit` class in `prototype/schema/bbot.yaml`
(generated -> Pydantic + JSON Schema, vendored to partner/_schema.py). Validate
formally with `linkml-validate --schema bbot.yaml --target-class Kit <kit>`.
This script is a lightweight, dependency-free mirror for authoring + the offline
tier (no linkml install needed); keep it in sync with the Kit class.
"""
from __future__ import annotations

import glob
import os
import sys

import yaml

_REQUIRED = ("name", "description")
_LIST_FIELDS = ("skills", "libraries", "resources", "maintainers")
_PROFILES = {"developer", "researcher"}


def validate(path: str) -> list[str]:
    errs: list[str] = []
    try:
        with open(path) as f:
            k = yaml.safe_load(f) or {}
    except Exception as e:
        return [f"parse error: {e}"]
    if not isinstance(k, dict):
        return ["top level must be a mapping"]

    for r in _REQUIRED:
        if not k.get(r):
            errs.append(f"missing required field '{r}'")

    name = k.get("name", "")
    if name and not all(c.islower() or c.isdigit() or c == "-" for c in name):
        errs.append(f"name '{name}' must be kebab-case (lowercase / digits / hyphen)")

    a = k.get("applies_to")
    if a is not None:
        if not isinstance(a, dict):
            errs.append("applies_to must be a mapping")
        else:
            prof = a.get("profile") or []
            prof = [prof] if isinstance(prof, str) else prof
            for p in prof:
                if p not in _PROFILES:
                    errs.append(f"applies_to.profile '{p}' not in {sorted(_PROFILES)}")

    for lf in _LIST_FIELDS:
        if lf in k and not isinstance(k[lf], list):
            errs.append(f"'{lf}' must be a list")
    return errs


def main(argv: list[str]) -> int:
    here = os.path.dirname(__file__) or "."
    paths = argv[1:] or sorted(glob.glob(os.path.join(here, "*.yaml")))
    total = 0
    for p in paths:
        errs = validate(p)
        total += len(errs)
        print(("FAIL " if errs else "ok   ") + p)
        for line in errs:
            print("   " + line)
    if total:
        sys.stderr.write(f"\n{total} problem(s) across {len(paths)} kit(s)\n")
        return 1
    print(f"\nall {len(paths)} kit(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
