# kits — the human customization surface for bbop-skunkworks runs

A **kit** is a reusable, human-authored bundle of *class-expertise* for an
autonomous run: domain context, skill/tool hints, libraries, resources, and
optional run hints. You attach a kit to a request and it gets merged into that
run's `BRIEF.md`, so it shapes what the build/research agent does — **without
anyone editing the agent, CAT, or BBOT.**

Kits are the **one surface the group customizes** directly. You author a kit by
adding a YAML file here (by pull request); you do **not** touch the agents'
internals. This repo is read by bbot's spawn flow at run time and by CAT when it
suggests a kit at intake.

## What goes in a kit (and what does NOT)

A kit holds what you'd otherwise **retype on every run of this class of job**.
It does **not** hold per-run specifics — the actual ask, who's asking, "build on
top of run #42". Those belong in the request itself.

> **Authoring test:** *Would I retype this on every run of this kind?* → kit.
> *Is it unique to this one request?* → the request, not the kit.

## Format

A kit is a YAML file named `<name>.yaml` at the repo root. `<name>` is the
stable `kit:<name>` handle.

```yaml
name: gene-ontology-prototype        # stable id, kebab-case (the kit:<name> handle)
title: "Gene Ontology software prototype"
description: "One line: what this kit is for."
maintainers: ["@your-handle"]        # who owns / curates it (GitHub handles)

applies_to:                          # how CAT decides this is a good default
  profile: [developer]               #   developer | researcher
  deliverable: [interactive_app, interactive_report]   # bbot deliverable kinds
  topics: ["gene ontology", "GO", "OBO", "term browser"]   # for CAT's semantic match

context: |                           # domain background injected into the BRIEF
  Prose the agent should know before it starts.

skills:                              # hints on approaches / tools to use
  - "Use X for Y."

libraries: [oaklib]                  # packages the agent may install / use (optional)

resources:                           # docs / APIs / data to consider
  - url: "https://..."
    note: "what it is / when to use it"
  - drive: "<drive-file-id>"         # a Drive doc shared with the bbot reader SA

run_hints:                           # OPTIONAL suggestions the agent MAY override
  stack: "..."                       # NOT hard config — kits inform; the engine
  output_target: "..."               #   still decides how to run (role boundary).
  keep_in_mind: "..."
```

Only `name` and `description` are required. Everything else is optional, but
`applies_to` + `context` are what make a kit actually useful. **`run_hints` are
suggestions only** — a kit informs *what to consider*; the agent still decides
*how to run*, so kits never hard-code brittle run mechanics.

The format is a **LinkML class** (`Kit` in
[`bbop-skunkworks/operations`](https://github.com/bbop-skunkworks/operations)
at `prototype/schema/bbot.yaml`) — that's the formal contract. You author plain
YAML; the class is what CAT and the spawn flow parse it into.

## Add a kit

1. Add `your-kit-name.yaml` at the repo root (copy the format above).
2. Fill `applies_to` honestly, so CAT suggests it for the right tasks (not noise).
3. Put **reusable** knowledge in `context` / `skills` / `resources`; leave
   per-run specifics out.
4. Validate locally: `python validate.py your-kit-name.yaml`
   (needs `pyyaml`: `pip install pyyaml`). CI runs the same check on your PR.
5. Open a pull request. A maintainer reviews and merges.

## How a kit gets used

- **At intake**, CAT may suggest a fitting kit for a request based on
  `applies_to` (profile / deliverable / topics).
- The request (a bbot issue) carries a `kit:<name>` label.
- **At spawn**, bbot fetches `https://raw.githubusercontent.com/bbop-skunkworks/kits/main/<name>.yaml`
  and merges the kit into the run's `BRIEF.md` (a `## Kit` section). The agent
  reads the BRIEF — it never sees this repo directly.

You can also attach a kit **without CAT** — add the `kit:<name>` label to a bbot
issue yourself. CAT is a convenience layer, not a gate.

## Relationship to `operations`

The **format/contract** (the LinkML `Kit` class + the canonical validator) lives
in `bbop-skunkworks/operations`. The **kit instances** (the `*.yaml` files) live
here and are curated by the group. Keep domain content here; the agents'
internals stay in `operations`.
