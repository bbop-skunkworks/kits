#!/usr/bin/env python3
"""Validate kit YAML files against the kit format.

    python validate.py <kit.yaml> ...     # specific files
    python validate.py                    # all kits (kits/*.yaml, else *.yaml here)

Exit 0 if every kit is valid, 1 otherwise.

CANONICAL contract: the LinkML `Kit` class in operations
(`prototype/schema/bbot.yaml`).  Its generated JSON Schema is shipped here as
`kit.schema.json` -- when `jsonschema` is installed (CI does `pip install pyyaml
jsonschema`), this validates each kit against that REAL contract.  Without
`jsonschema` (e.g. a quick local run), it falls back to lightweight structural
checks so authoring still gets fast feedback.  Either way it stays a thin shell
over the generated schema -- regenerate with `make -C prototype/schema gen`.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_PATH = os.path.join(_HERE, "kit.schema.json")

# Fallback structural checks (used only when jsonschema isn't importable).
_REQUIRED = ("name", "description")
_LIST_FIELDS = ("skills", "libraries", "resources", "maintainers")
_PROFILES = {"developer", "researcher"}


def _load_schema() -> dict | None:
    try:
        with open(_SCHEMA_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def _validator():
    """Return a (mode, fn) pair: jsonschema against the real contract if
    available, else the lightweight structural checker."""
    schema = _load_schema()
    try:
        import jsonschema  # noqa: F401
    except Exception:
        schema = None
    if schema is not None:
        import jsonschema

        def _check(doc: dict) -> list[str]:
            v = jsonschema.Draft7Validator(schema)
            return [
                f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))
            ]

        return "schema", _check
    return "structural", _structural_check


def _structural_check(k: dict) -> list[str]:
    errs: list[str] = []
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


def validate(path: str, check) -> list[str]:
    try:
        with open(path) as f:
            k = yaml.safe_load(f) or {}
    except Exception as e:
        return [f"parse error: {e}"]
    if not isinstance(k, dict):
        return ["top level must be a mapping"]
    return check(k)


def _discover() -> list[str]:
    """Kit files: kits/*.yaml (public-repo layout) if present, else *.yaml here
    (operations seed layout)."""
    sub = sorted(glob.glob(os.path.join(_HERE, "kits", "*.yaml")))
    if sub:
        return sub
    return sorted(glob.glob(os.path.join(_HERE, "*.yaml")))


def main(argv: list[str]) -> int:
    mode, check = _validator()
    paths = argv[1:] or _discover()
    print(f"(validating in '{mode}' mode against kit.schema.json)" if mode == "schema"
          else "(jsonschema not installed -> lightweight structural checks)")
    total = 0
    for p in paths:
        errs = validate(p, check)
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
