# harmonium_lab Constitution

This document extends the [meta constitution] in `harmonium_specs/.specify/memory/constitution.md`.
On conflict, the meta document wins. The principles below are repo-local additions
specific to the music quality evaluation pipeline.

[meta constitution]: https://github.com/estran-studio/harmonium_specs/blob/main/.specify/memory/constitution.md

## Repo-Local Principles

### I. Reproducibility Is the Deliverable

The lab exists to produce evidence: composite scores comparing engine
output to a reference corpus, per-style profile candidates, regression
deltas between engine versions. Every score in the output MUST be
reproducible from inputs (corpus snapshot, engine version, TuningParams
JSON). A score that cannot be reproduced has no value.

This means: pin engine commits, capture random seeds, version reference
corpora, and never silently fall back to "best available" data when an
expected input is missing.

### II. Reference Corpus Is Authoritative

The 28-file reference corpus in `references/` is the ground truth that
scoring compares against. Changes to the corpus require re-running historical
evaluations to avoid invalidating prior results. A new corpus version is a
versioned event, not a silent file replacement.

### III. The Scoring Map Is Normative

The "Engine Architecture → Quality Metric Map" in `CLAUDE.md` is normative
when interpreting reports — it links each quality metric to the engine
file and parameter most likely responsible for the deviation. Suggestions
from analysis runs MUST cite a specific file + parameter from this map (or
explain why the deviation falls outside it).

### IV. The LLM Is an Advisor, Not the Source of Truth

Claude API calls suggest TuningParams changes; they do not commit them.
Every Claude suggestion goes through the render-and-rate loop, with a
human rating before a profile ships. Prompt caching is mandatory for any
prompt that repeats across iterations.

### V. Multi-Language Boundaries Are Explicit

This repo crosses Python (analysis: music21, MusPy, MGEval, librosa,
FluidSynth) and Rust (engine integration via `make lab-export`). The
boundary is JSON over files or pipes — never shared memory, never FFI
without justification. Each side stays debuggable on its own.

## Tech Constraints (Repo-Specific)

- Python toolchain pinned in `pyproject.toml` / venv via `make setup`.
  Standard scientific stack: music21, MusPy, MGEval, librosa, FluidSynth.
- Rust integration is via the `harmonium_core` and `harmonium_host` crates,
  pinned to a specific commit for any published evaluation run.
- CLI commands (`harmonium-lab analyze|suite|profile|compare|gate|save-baseline`)
  are the stable interface; underlying module structure may change.
- Quality gate composite score: aim for >70; <40 fails the gate by default.

## Spec Scope

Per-repo specs cover: corpus curation, scoring pipeline changes, Claude
prompt engineering, CLI commands, CI integration. Specs that change the
`TuningParams` schema or the engine integration contract live in
`harmonium_specs/` and pull this repo in as a participant.

**Version**: 1.0.0 | **Ratified**: 2026-05-25 | **Last Amended**: 2026-05-25
