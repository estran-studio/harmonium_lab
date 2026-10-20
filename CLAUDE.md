> **Chantier en cours** : dataset trad québécois — `specs/001-trad-dataset/plan.md`. Le corpus jazz/classique ci-dessous est l’ancienne référence.

> `make trad-corpus` (DS-T1) : télécharge Chambers + The Session dans `corpus/trad/raw/` (cache, gitignoré), normalise un air par fichier dans `corpus/trad/tunes/<type>/`, écrit `manifest.jsonl` + `VERSION` (seuls versionnés) et `rejects.jsonl`. Code : `src/harmonium_lab/trad/`; artistes québécois : `trad/quebec_artists.json`. Relance sans réseau : `--offline`.
> `make trad-render` (DS-T2) : ABC → MIDI (`abc2midi`, reprises AABB) → WAV (`fluidsynth`, GeneralUser GS) dans `target/trad_render/<type>/` (gitignoré). `make trad-profiles` (DS-T3) : `references/trad-<type>/profile.json` (versionnés).
> `make engine-reels N=10` (DS-T4) : exporte N reels du moteur (repo frère `../harmonium`, seeds 1..N, 32 mesures = AABB) vers `target/engine_reels/` via :
> `cargo run -q -p harmonium-cli --release --manifest-path ../harmonium/Cargo.toml -- --export --bars 32 --style reel --seed S --record-wav target/engine_reels/reel_seedS.wav --record-midi target/engine_reels/reel_seedS.mid`
> (binaire `harmonium-cli` : `--export --bars 32 --style reel --seed S --record-wav … --record-midi …`). Ensuite : `harmonium-lab trad-compare --generated target/engine_reels --type reel` puis `harmonium-lab blindtest --type reel --real 10 --generated target/engine_reels --count 10`. Pour écouter et juger : `harmonium-lab blindtest-play target/blindtest/<horodatage>` (ou `blindtest-score` après édition manuelle de `feuille.md`).

> `make fiddle-samples` (SK3) : télécharge les banques commercialement utilisables de `samples/fiddles/manifest.jsonl`, vérifie SHA256 et `phdr`, cache privé dans `samples/fiddles/raw/` (gitignoré). Réinventaire explicite : `.venv/bin/python -m harmonium_lab.trad.fiddle_samples --inventory --offline`.

## harmonium_lab — Music Quality Evaluation Pipeline

### Quick Start
```bash
cd harmonium_lab
make setup          # Create venv, install deps
make corpus         # Download reference MIDI corpus (28 files)
make profiles       # Build reference profiles from corpus
make lab-export     # Generate harmonium MIDI+JSON (Rust tests)
make suite          # Analyze all scenarios → quality reports
make test           # Run all tests (74 passing)
make pipeline       # Full: generate → analyze → report
```

### Project Structure
```
harmonium_lab/
  src/harmonium_lab/
    types.py           # NoteData, MeasureData, Scenario (mirrors Rust)
    loader.py          # JSON + MIDI loading
    symbolic.py        # music21 analysis (consonance, key, contour, voice leading)
    muspy_metrics.py   # MusPy metrics (PCE, scale consistency, groove, etc.)
    mgeval_metrics.py  # Histogram comparison (pitch class, note length, onset)
    audio.py           # librosa analysis (spectral, tonal, rhythm, dynamics, dissonance)
    scorer.py          # Z-scores, concern scores (0-100), composite scoring
    profiles.py        # Build/save/load reference profiles
    ci.py              # Regression detection, quality gate, baseline management
    cli.py             # CLI: analyze, suite, profile, compare, gate, save-baseline
  references/          # Corpus: 5 categories × ~5 MIDI files + meta.json + profile.json
  scripts/download_corpus.sh  # Re-download corpus MIDI files
```

### CLI Commands
```bash
harmonium-lab analyze path.mid [--profile ref.json] [-o report.json]
harmonium-lab suite -i dir/ -o reports/ [--profile ref.json]
harmonium-lab profile -i midis/ --category name -o profile.json
harmonium-lab compare --before a.json --after b.json
harmonium-lab gate --report r.json [--baseline b.json] [--min-composite 40]
harmonium-lab save-baseline --reports dir/ -o baseline.json
```

### Scoring System

**6 quality concerns** scored 0-100 (100 = identical to reference):

| Concern | What it measures | Key metrics |
|---------|-----------------|-------------|
| tonal | Key stability, scale adherence | music21 key correlation, MusPy scale consistency, audio key strength |
| consonance | Harmonic pleasantness | music21 consonance ratio, audio harmonic ratio |
| melodic | Melody shape & variety | Step/leap ratio, pitch class entropy, pitch range |
| rhythmic | Groove & timing regularity | Groove consistency, empty beat rate, tempo stability |
| dynamics | Volume variation | Dynamic range, RMS variation |
| voice_leading | Smooth chord transitions | Parallel fifths/octaves count |

**Composite score** = weighted average of concerns (0-100).

---

## Analyzing Quality Reports (for Claude Code)

When asked to interpret a harmonium_lab quality report, use this workflow:

### Step 1: Run the analysis
```bash
cd harmonium_lab
make lab-export                    # Generate fresh MIDI from engine
.venv/bin/harmonium-lab suite \
  -i ../harmonium/harmonium_core/target/generated_music/ \
  -o target/quality_reports/ \
  --profile references/ambient/profile.json
```

### Step 2: Read the report
Read `target/quality_reports/lab_*_report.json`. Focus on:
- `composite_score` — overall quality (aim for >70)
- `concern_scores` — which dimensions are weak
- `top_deviations` — worst z-scores with specific metric names

### Step 3: Map deviations to engine code
Use this reference to diagnose WHY a metric is off and WHAT to change:

#### Engine Architecture → Quality Metric Map

| Metric Problem | Root Cause Area | File to Modify | Parameter to Tune |
|---------------|----------------|----------------|-------------------|
| Low `music21_key_correlation` | Harmony strategy too chromatic | `harmony/driver.rs` | Lower `harmony_tension` or clamp LCC level |
| Low `muspy_scale_consistency` | LCC level too high for context | `harmony/lydian_chromatic.rs` | Tension→LCC mapping curve |
| Low `music21_consonance_ratio` | Too many dissonant intervals | `harmony/parsimonious.rs` | Lower `MAX_SEMITONE_MOVEMENT`, prefer triads |
| High `music21_parallel_errors` | Voice-leading not optimized | `harmony/voice_leading.rs` | Check `optimal_voice_assignment()` |
| Low `muspy_groove_consistency` | Irregular beat placement | `sequencer.rs` | Adjust density→pattern mapping |
| High `muspy_empty_beat_rate` | Too sparse rhythm | `sequencer.rs` | Increase `rhythm_pulses` or `rhythm_density` |
| Low `audio_tempo_stability` | Inconsistent inter-beat timing | `sequencer.rs` | Check pattern rotation stability |
| Low step_ratio (too many leaps) | Melody jumps too much | `harmony/melody.rs` | Increase `melody_smoothness` (Hurst exponent) |
| Narrow pitch_range | Melody confined to small register | `harmony/melody.rs` | Adjust octave folding / instrument range |
| Low dynamic_range | Flat velocity profile | `sequencer.rs` | Increase velocity variance in `StepTrigger` |

#### Harmony Strategy Selection (controlled by `harmony_tension`)
- **tension < 0.3** → Steedman (functional jazz harmony, tonal, consonant)
- **0.3 ≤ tension < 0.6** → Mixed Steedman + Parsimonious (7ths, extensions)
- **tension ≥ 0.6** → Neo-Riemannian + Parsimonious (chromatic, cinematic)

#### Lydian Chromatic Concept Levels (controlled by `harmony_tension`)
- **Levels 1-4** (tension 0.0-0.3): Consonant (Lydian, Lydian Aug, Lydian Dim, Lyd b7)
- **Levels 5-8** (tension 0.3-0.6): Moderate (Aux Aug, Aux Dim Blues, etc.)
- **Levels 9-12** (tension 0.6-1.0): Dissonant (Major Pentatonic→Chromatic)

### Step 4: Recommend specific changes
For each deviation, suggest:
1. **Which parameter** to change and in which direction
2. **Which file** contains the relevant code
3. **Expected tradeoff** — improving one metric may affect others
4. **Confidence** — high (direct parameter mapping) / medium (indirect) / low (speculative)

### Example Analysis Prompt
> Read the quality report at `target/quality_reports/lab_calm_ambient_report.json`.
> The reference profile is `ambient`. Identify the top 3 deviations and suggest
> specific engine parameter changes to improve the composite score.
> For each suggestion, name the file, the parameter, the direction of change,
> and any tradeoffs.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
