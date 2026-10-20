"""CLI entry point for harmonium_lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="harmonium-lab",
        description="Music quality evaluation pipeline for harmonium",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command")

    # analyze: single scenario
    p_analyze = subparsers.add_parser("analyze", help="Analyze a single MIDI file")
    p_analyze.add_argument("midi", help="Path to .mid file")
    p_analyze.add_argument("--profile", help="Path to reference profile JSON")
    p_analyze.add_argument("--output", "-o", help="Output JSON path (default: stdout)")

    # suite: analyze all scenarios in a directory
    p_suite = subparsers.add_parser("suite", help="Analyze all lab scenarios")
    p_suite.add_argument("--input", "-i", required=True, help="Directory with lab_*.mid files")
    p_suite.add_argument("--output", "-o", required=True, help="Output directory for reports")
    p_suite.add_argument("--profile", help="Reference profile JSON (optional)")

    # profile: build reference profile from MIDI files
    p_profile = subparsers.add_parser("profile", help="Build reference profile from MIDI files")
    p_profile.add_argument("--input", "-i", required=True, help="Directory with .mid files")
    p_profile.add_argument("--category", required=True, help="Category name")
    p_profile.add_argument("--output", "-o", required=True, help="Output profile JSON path")

    # compare: before/after
    p_compare = subparsers.add_parser("compare", help="Compare two quality reports")
    p_compare.add_argument("--before", required=True, help="Baseline report JSON")
    p_compare.add_argument("--after", required=True, help="Current report JSON")

    # gate: CI quality check
    p_gate = subparsers.add_parser("gate", help="CI quality gate check")
    p_gate.add_argument("--report", required=True, help="Quality report JSON")
    p_gate.add_argument("--baseline", help="Baseline report JSON (optional)")
    p_gate.add_argument("--min-composite", type=float, default=40.0)
    p_gate.add_argument("--max-concern-drop", type=float, default=15.0)
    p_gate.add_argument("--max-z-score", type=float, default=3.0)

    # save-baseline
    p_baseline = subparsers.add_parser("save-baseline", help="Save current reports as baseline")
    p_baseline.add_argument("--reports", required=True, help="Directory with report JSONs")
    p_baseline.add_argument("--output", "-o", required=True, help="Baseline JSON path")

    # trad-corpus: download + normalise the Québec trad corpus
    p_trad = subparsers.add_parser("trad-corpus", help="Build the trad québécois corpus (corpus/trad)")
    p_trad.add_argument("--root", default="corpus/trad", help="Corpus directory")
    p_trad.add_argument("--delay", type=float, default=0.3, help="Seconds between network requests")
    p_trad.add_argument("--offline", action="store_true", help="Use the raw/ cache only")
    # trad-render: render the trad corpus at parity (MIDI + WAV)
    p_render = subparsers.add_parser("trad-render", help="Render trad corpus tunes (MIDI+WAV)")
    p_render.add_argument("--root", default="corpus/trad", help="Corpus directory")
    p_render.add_argument("--out", default="target/trad_render", help="Output directory")
    p_render.add_argument("--type", default=None, help="Tune type (reel, jig, waltz, …; default: all)")
    p_render.add_argument("--limit", type=int, default=None, help="Reproducible sample of N tunes")
    p_render.add_argument("--seed", type=int, default=20261019, help="Sampling seed")
    p_render.add_argument("--ids", nargs="*", default=None, help="Tune ids (ignores --limit/--seed)")
    p_render.add_argument("--soundfont", default=None, help="SoundFont .sf2 path")
    p_render.add_argument("--feet-soundfont", default=None, help="Feet bank .sf2 path (default: auto)")
    p_render.add_argument("--feet-gain", type=float, default=None, help="Feet velocity gain")
    p_render.add_argument("--feet-humanize", type=int, default=None, help="Feet velocity humanize ±")
    p_render.add_argument("--feet-seed", type=int, default=None, help="Feet humanize seed")
    p_render.add_argument("--musicxml", action="store_true", help="Also emit .musicxml via music21")
    # trad-profile: build a trad type profile from corpus ABC/MIDI files
    p_trad = subparsers.add_parser("trad-profile", help="Build trad type profile from corpus tunes")
    p_trad.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_trad.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc)")
    p_trad.add_argument("--output", "-o", required=True, help="Output profile JSON path")
    # trad-compare: generated engine MIDIs vs type profile (D6)
    p_cmp = subparsers.add_parser("trad-compare", help="Compare generated MIDIs to a trad type profile")
    p_cmp.add_argument("--generated", nargs="+", required=True, help="Engine .mid dir or files")
    p_cmp.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_cmp.add_argument("-o", "--output", default=None, help="Output dir (default: target/trad_compare/<horodatage>/)")
    p_cmp.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc + manifest.jsonl)")
    p_cmp.add_argument("--profile", default=None, help="Type profile JSON (default: references/trad-<type>/profile.json)")
    p_cmp.add_argument("--render-dir", default="target/trad_render", help="Rendered WAVs root (<type>/<id>.wav)")
    # blindtest: shuffle real + generated WAVs into an anonymous kit (D6)
    p_bt = subparsers.add_parser("blindtest", help="Build a blind listening kit (real + generated WAVs)")
    p_bt.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_bt.add_argument("--real", type=int, default=10, help="Number of real WAVs")
    p_bt.add_argument("--generated", required=True, help="Dir with engine .wav files")
    p_bt.add_argument("--count", type=int, default=10, help="Number of generated WAVs")
    p_bt.add_argument("--seed", type=int, default=20261019, help="Sampling seed (deterministic)")
    p_bt.add_argument("--duration", type=float, default=33.0, help="Common duration in seconds (cut or padded)")
    p_bt.add_argument("--fade", type=float, default=0.5, help="Fade in/out in seconds")
    p_bt.add_argument("-o", "--output", default=None, help="Output dir (default: target/blindtest/<horodatage>/)")
    p_bt.add_argument("--render-dir", default="target/trad_render", help="Rendered real WAVs root")
    # blindtest-play: interactively play WAVs and fill feuille.md (D6)
    p_btp = subparsers.add_parser("blindtest-play", help="Play WAVs, fill feuille.md interactively, and score")
    p_btp.add_argument("kit", help="Kit dir (target/blindtest/<horodatage>/)")
    p_btp.add_argument("--compare", default=None, help="trad-compare report.json (top deviations of unmasked)")
    # blindtest-score: grade a filled answer sheet (D6)
    p_bts = subparsers.add_parser("blindtest-score", help="Score a filled blindtest feuille.md")
    p_bts.add_argument("kit", help="Kit dir (target/blindtest/<horodatage>/)")
    p_bts.add_argument("--compare", default=None, help="trad-compare report.json (top deviations of unmasked)")

    # trad-form-report: coverage of form analysis for a tune type
    p_form = subparsers.add_parser("trad-form-report", help="Form coverage report for a trad tune type")
    p_form.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_form.add_argument("--corpus", default="corpus/trad", help="Corpus root")
    # mine-cells: cell bank mined from the corpus for the engine (D7)
    p_mine = subparsers.add_parser("mine-cells", help="Mine a CellBank TOML from trad corpus tunes")
    p_mine.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_mine.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc)")
    p_mine.add_argument("--output", "-o", required=True, help="Output CellBank TOML path")
    p_mine.add_argument("--top", type=int, default=10, help="Kept cells per role (default: 10)")
    # mine-harmony: chord degrees, bigrams and per-mode tables (D7)
    p_mharm = subparsers.add_parser("mine-harmony", help="Mine chord tables from trad corpus tunes")
    p_mharm.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_mharm.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc)")
    p_mharm.add_argument("--output", "-o", required=True, help="Output harmony JSON path")
    # mine-tempo: Q: tempos and time signatures per type (D7)
    p_mtempo = subparsers.add_parser("mine-tempo", help="Mine tempo ranges and meters from trad corpus")
    p_mtempo.add_argument("--type", default=None, help="Tune type (default: all types)")
    p_mtempo.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc)")
    p_mtempo.add_argument("--output", "-o", default=None, help="Output tempo JSON path (default: stdout only)")

    # pieds SK1 : échantillons, préparation, banque, écoute de contrôle
    p_ff = subparsers.add_parser("feet-fetch", help="Download feet samples (manifest.jsonl → raw/)")
    p_ff.add_argument("--root", default="samples/feet", help="samples/feet dir")
    p_ff.add_argument("--delay", type=float, default=0.3, help="Seconds between requests")
    p_ff.add_argument("--offline", action="store_true", help="Cache only")
    p_fp = subparsers.add_parser("feet-prepare", help="Cut/normalise feet hits (raw/ → prepared/)")
    p_fp.add_argument("--root", default="samples/feet", help="samples/feet dir")
    p_fs = subparsers.add_parser("feet-sf2", help="Build harmonium_trad.sf2 (prepared/ → .sf2)")
    p_fs.add_argument("--root", default="samples/feet", help="samples/feet dir")
    p_fs.add_argument("--output", "-o", default=None, help="Output .sf2 path (default: auto)")
    p_fv = subparsers.add_parser("feet-preview", help="Feet check listen (pieds seuls + reel complet)")
    p_fv.add_argument("--out", default="target/feet_preview", help="Output dir")
    p_fv.add_argument("--root", default="corpus/trad", help="Corpus root")
    p_fv.add_argument("--soundfont", default=None, help="GeneralUser-GS.sf2 path")
    p_fv.add_argument("--feet-soundfont", default=None, help="harmonium_trad.sf2 path (default: auto)")
    p_fv.add_argument("--feet-gain", type=float, default=None, help="Feet velocity gain (default: render.FEET_VEL_SCALE)")
    p_fv.add_argument("--feet-humanize", type=int, default=None, help="Feet velocity humanize ± (default: render.FEET_HUMANIZE)")
    p_fv.add_argument("--feet-seed", type=int, default=None, help="Feet humanize seed (default: render.FEET_SEED)")
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "analyze":
            return cmd_analyze(args)
        elif args.command == "suite":
            return cmd_suite(args)
        elif args.command == "profile":
            return cmd_profile(args)
        elif args.command == "compare":
            return cmd_compare(args)
        elif args.command == "gate":
            return cmd_gate(args)
        elif args.command == "save-baseline":
            return cmd_save_baseline(args)
        elif args.command == "trad-corpus":
            return cmd_trad_corpus(args)
        elif args.command == "trad-render":
            return cmd_trad_render(args)
        elif args.command == "trad-profile":
            return cmd_trad_profile(args)
        elif args.command == "trad-compare":
            return cmd_trad_compare(args)
        elif args.command == "blindtest":
            return cmd_blindtest(args)
        elif args.command == "blindtest-score":
            return cmd_blindtest_score(args)
        elif args.command == "trad-form-report":
            return cmd_trad_form_report(args)
        elif args.command == "mine-cells":
            return cmd_mine_cells(args)
        elif args.command == "mine-harmony":
            return cmd_mine_harmony(args)
        elif args.command == "mine-tempo":
            return cmd_mine_tempo(args)
        elif args.command == "blindtest-play":
            return cmd_blindtest_play(args)
        elif args.command == "feet-fetch":
            return cmd_feet_fetch(args)
        elif args.command == "feet-prepare":
            return cmd_feet_prepare(args)
        elif args.command == "feet-sf2":
            return cmd_feet_sf2(args)
        elif args.command == "feet-preview":
            return cmd_feet_preview(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def cmd_trad_corpus(args: argparse.Namespace) -> int:
    """Download + normalise the trad québécois corpus."""
    from .trad.corpus import main as trad_main

    argv = ["--root", args.root, "--delay", str(args.delay)]
    if args.offline:
        argv.append("--offline")
    return trad_main(argv)


def cmd_trad_render(args: argparse.Namespace) -> int:
    """Render trad corpus tunes at parity (MIDI + WAV)."""
    from .trad.render import main as render_main

    argv = ["--root", args.root, "--out", args.out, "--seed", str(args.seed)]
    if args.type:
        argv += ["--type", args.type]
    if args.limit is not None:
        argv += ["--limit", str(args.limit)]
    if args.ids:
        argv += ["--ids", *args.ids]
    if args.soundfont:
        argv += ["--soundfont", args.soundfont]
    if args.feet_soundfont:
        argv += ["--feet-soundfont", args.feet_soundfont]
    if args.feet_gain is not None:
        argv += ["--feet-gain", str(args.feet_gain)]
    if args.feet_humanize is not None:
        argv += ["--feet-humanize", str(args.feet_humanize)]
    if args.feet_seed is not None:
        argv += ["--feet-seed", str(args.feet_seed)]
    if args.musicxml:
        argv.append("--musicxml")
    return render_main(argv)


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze a single MIDI file."""
    from .muspy_metrics import compute_muspy_metrics
    from .scorer import flatten_metrics, quality_report, ReferenceProfile
    from .profiles import load_profile, build_profile_from_midis
    from .symbolic import full_symbolic_analysis

    midi_path = Path(args.midi)
    print(f"Analyzing {midi_path.name}...")

    symbolic = full_symbolic_analysis(midi_path)
    muspy = compute_muspy_metrics(midi_path)
    flat = flatten_metrics(symbolic=symbolic, muspy=muspy)

    if args.profile:
        profile = load_profile(args.profile)
    else:
        # Self-reference: build a trivial profile from this file
        profile = build_profile_from_midis([midi_path], category="self")

    report = quality_report(flat, profile)

    output = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Report saved to {args.output}")
    else:
        print(output)

    print(f"\nComposite score: {report['composite_score']:.1f}/100")
    return 0


def cmd_suite(args: argparse.Namespace) -> int:
    """Analyze all lab scenarios in a directory."""
    from .muspy_metrics import compute_muspy_metrics
    from .scorer import flatten_metrics, quality_report
    from .profiles import load_profile, build_profile_from_midis
    from .symbolic import full_symbolic_analysis

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    midi_files = sorted(input_dir.glob("lab_*.mid"))
    if not midi_files:
        print(f"No lab_*.mid files found in {input_dir}")
        return 1

    # Build self-reference profile if no profile provided
    if args.profile:
        profile = load_profile(args.profile)
    else:
        print(f"Building self-reference profile from {len(midi_files)} files...")
        profile = build_profile_from_midis(midi_files, category="self-reference")
        profile_path = output_dir / "self_profile.json"
        from .profiles import save_profile
        save_profile(profile, profile_path)
        print(f"Profile saved to {profile_path}")

    all_reports = {}
    for midi_path in midi_files:
        name = midi_path.stem
        print(f"  Analyzing {name}...", end=" ", flush=True)

        symbolic = full_symbolic_analysis(midi_path)
        muspy = compute_muspy_metrics(midi_path)
        flat = flatten_metrics(symbolic=symbolic, muspy=muspy)
        report = quality_report(flat, profile)

        report_path = output_dir / f"{name}_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        all_reports[name] = report

        print(f"score={report['composite_score']:.1f}")

    # Summary
    scores = [r["composite_score"] for r in all_reports.values()]
    print(f"\nSuite complete: {len(scores)} scenarios")
    print(f"  Average composite: {sum(scores)/len(scores):.1f}")
    print(f"  Min: {min(scores):.1f}  Max: {max(scores):.1f}")

    # Save combined report
    combined_path = output_dir / "suite_report.json"
    combined_path.write_text(json.dumps(all_reports, indent=2))
    print(f"Combined report: {combined_path}")

    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    """Build a reference profile from MIDI files."""
    from .profiles import build_profile_from_midis, save_profile

    input_dir = Path(args.input)
    midi_files = sorted(input_dir.glob("*.mid")) + sorted(input_dir.glob("*.midi"))

    if not midi_files:
        print(f"No MIDI files found in {input_dir}")
        return 1

    print(f"Building profile '{args.category}' from {len(midi_files)} files...")
    profile = build_profile_from_midis(midi_files, category=args.category)

    save_profile(profile, args.output)
    print(f"Profile saved to {args.output} ({len(profile.metrics)} metrics)")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two quality reports."""
    from .ci import compare_runs, format_comparison

    with open(args.before) as f:
        before = json.load(f)
    with open(args.after) as f:
        after = json.load(f)

    comparison = compare_runs(before, after)
    print(format_comparison(comparison))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    """Run quality gate check."""
    from .ci import check_quality_gate, format_gate_result

    with open(args.report) as f:
        report = json.load(f)

    baseline = None
    if args.baseline:
        with open(args.baseline) as f:
            baseline = json.load(f)

    result = check_quality_gate(
        report,
        baseline=baseline,
        min_composite=args.min_composite,
        max_concern_drop=args.max_concern_drop,
        max_z_score=args.max_z_score,
    )

    print(format_gate_result(result))
    return 0 if result.passed else 1


def cmd_save_baseline(args: argparse.Namespace) -> int:
    """Save current reports as baseline."""
    from .ci import save_baseline

    reports_dir = Path(args.reports)
    report_files = sorted(reports_dir.glob("*_report.json"))

    if not report_files:
        print(f"No *_report.json files found in {reports_dir}")
        return 1

    combined = {}
    for path in report_files:
        name = path.stem.replace("_report", "")
        with path.open() as f:
            combined[name] = json.load(f)

    save_baseline(combined, args.output)
    print(f"Baseline saved to {args.output} ({len(combined)} scenarios)")
    return 0


def cmd_trad_profile(args: argparse.Namespace) -> int:
    """Build a trad type profile from corpus tunes (ABC + engine MIDI)."""
    from .trad import build_profile, load_abc, load_engine_midi, save_profile

    tunes_dir = Path(args.corpus) / "tunes" / args.type
    abc_files = sorted(tunes_dir.glob("*.abc"))
    midi_files = sorted(tunes_dir.glob("*.mid")) + sorted(tunes_dir.glob("*.midi"))
    if not abc_files and not midi_files:
        print(f"No tunes found in {tunes_dir}")
        return 1

    tunes = []
    for path in abc_files:
        try:
            tunes.append(load_abc(path))
        except Exception as e:
            print(f"Skipping {path.name}: {e}")
    for path in midi_files:
        try:
            tunes.append(load_engine_midi(path))
        except Exception as e:
            print(f"Skipping {path.name}: {e}")
    if not tunes:
        print(f"No loadable tunes in {tunes_dir}")
        return 1

    print(f"Building trad profile '{args.type}' from {len(tunes)} tunes...")
    profile = build_profile(tunes, tune_type=args.type)
    save_profile(profile, args.output)
    print(f"Profile saved to {args.output} ({profile['tune_count']} tunes)")
    return 0


def _timestamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _load_manifest_titles(corpus: Path) -> dict[str, str]:
    import json as _json

    manifest = corpus / "manifest.jsonl"
    if not manifest.exists():
        return {}
    titles = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = _json.loads(line)
            titles[row["id"]] = row.get("title", row["id"])
    return titles


def cmd_trad_compare(args: argparse.Namespace) -> int:
    """Compare generated engine MIDIs to a trad type profile (D6)."""
    import json as _json

    from .trad import (
        compare_to_profile,
        deviations_for_file,
        feature_vector,
        features,
        load_abc,
        load_engine_midi,
        load_profile,
        nearest_reals,
        reference_stats,
    )

    midis: list[Path] = []
    for raw in args.generated:
        p = Path(raw)
        if p.is_dir():
            midis += sorted(p.glob("*.mid")) + sorted(p.glob("*.midi"))
        elif p.exists():
            midis.append(p)
        else:
            print(f"Not found: {raw}")
            return 1
    if not midis:
        print("No generated .mid files")
        return 1

    corpus = Path(args.corpus)
    abc_files = sorted((corpus / "tunes" / args.type).glob("*.abc"))
    if not abc_files:
        print(f"No real tunes in {corpus / 'tunes' / args.type}")
        return 1

    profile_path = args.profile or f"references/trad-{args.type}/profile.json"
    profile = load_profile(profile_path)
    titles = _load_manifest_titles(corpus)
    render_dir = Path(args.render_dir) / args.type

    reals: list[tuple[str, dict[str, float]]] = []
    skipped = 0
    for path in abc_files:
        try:
            tune = load_abc(path)
        except Exception as e:
            skipped += 1
            print(f"Skipping {path.name}: {e}")
            continue
        reals.append((tune.tune_id, feature_vector(features(tune))))
    if not reals:
        print("No loadable real tunes")
        return 1

    generated: dict[str, dict[str, Any]] = {}
    for path in midis:
        try:
            generated[path.name] = features(load_engine_midi(path))
        except Exception as e:
            print(f"Skipping {path.name}: {e}")
    if not generated:
        print("No loadable generated MIDIs")
        return 1

    ref = reference_stats(profile, [v for _, v in reals])
    deviations = compare_to_profile(generated, ref, args.type)
    per_file = []
    for name in sorted(generated):
        nearest = [
            {
                "id": rid,
                "title": titles.get(rid, rid),
                "wav": str(render_dir / f"{rid}.wav"),
                "distance": dist,
            }
            for rid, dist in nearest_reals(generated[name], reals, ref)
        ]
        per_file.append(
            {"file": name, "deviations": deviations_for_file(generated[name], ref, args.type), "nearest": nearest}
        )

    report: dict[str, Any] = {
        "type": args.type,
        "profile": str(profile_path),
        "profile_tunes": profile.get("tune_count"),
        "real_tunes_loaded": len(reals),
        "real_tunes_skipped": skipped,
        "generated": sorted(generated),
        "deviations": deviations,
        "per_file": per_file,
    }
    out = Path(args.output) if args.output else Path("target/trad_compare") / _timestamp()
    out.mkdir(parents=True, exist_ok=False)
    (out / "report.json").write_text(
        _json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        f"# Comparaison moteur vs {args.type}s réels",
        "",
        f"{len(generated)} généré(s) vs profil `{profile_path}` "
        f"({profile.get('tune_count')} airs, {len(reals)} rechargés).",
        "",
        "## Écarts (triés par |z|)",
        "",
    ]
    for d in deviations:
        lines += [
            f"### {d['key']} — z = {d['z']} (réel {d['real_value']}, moteur {d['generated_value']})",
            "",
            d["sentence"],
            "",
        ]
    lines += ["## Plus proches réels", ""]
    for entry in per_file:
        lines.append(f"### {entry['file']}")
        lines.append("")
        for n in entry["nearest"]:
            lines.append(f"- {n['title']} (`{n['wav']}`, distance {n['distance']})")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report in {out}/ ({len(deviations)} écarts, {len(per_file)} générés)")
    for d in deviations[:5]:
        print(f"  z={d['z']:>7}: {d['sentence']}")
    return 0


def cmd_blindtest(args: argparse.Namespace) -> int:
    """Build a blind listening kit from real + generated WAVs (D6)."""
    from .trad import build_kit

    real_pool = sorted((Path(args.render_dir) / args.type).glob("*.wav"))
    gen_pool = sorted(Path(args.generated).glob("*.wav"))
    out = Path(args.output) if args.output else Path("target/blindtest") / _timestamp()
    kit = build_kit(
        real_pool, gen_pool, out,
        n_real=args.real, n_gen=args.count, seed=args.seed,
        duration=args.duration, fade=args.fade,
    )
    print(f"Kit in {out}/ ({len(kit['files'])} fichiers, seed {args.seed})")
    for n in kit["files"]:
        print(f"  {n}")
    print(f"Pour écouter et répondre : harmonium-lab blindtest-play {out}")
    return 0


def cmd_blindtest_play(args: argparse.Namespace) -> int:
    """Play WAVs, fill feuille.md interactively, and score (D6)."""
    import json as _json

    from .trad import play_kit

    kit = Path(args.kit)
    compare_report = None
    if args.compare:
        compare_report = _json.loads(Path(args.compare).read_text(encoding="utf-8"))
    return play_kit(kit, compare_report=compare_report)


def cmd_blindtest_score(args: argparse.Namespace) -> int:
    """Score a filled blindtest feuille.md (D6)."""
    import json as _json

    from .trad import print_score, score_feuille

    kit = Path(args.kit)
    compare_report = None
    if args.compare:
        compare_report = _json.loads(Path(args.compare).read_text(encoding="utf-8"))
    score = score_feuille(kit, compare_report)
    print_score(score, kit_dir=kit)
    return 0


def cmd_trad_form_report(args: argparse.Namespace) -> int:
    """Coverage report: scheme distribution, AABB rate, examples per cause."""
    import json
    from collections import Counter

    from .trad import features, load_abc

    tunes_dir = Path(args.corpus) / "tunes" / args.type
    abc_files = sorted(tunes_dir.glob("*.abc"))
    if not abc_files:
        print(f"No tunes found in {tunes_dir}")
        return 1

    titles: dict[str, str] = {}
    manifest = Path(args.corpus) / "manifest.jsonl"
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                row = json.loads(line)
                titles[row["id"]] = row.get("title", "")

    schemes: Counter[str] = Counter()
    causes: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    errors = 0
    strict_aabb = 0
    for path in abc_files:
        tune_id = path.stem
        try:
            form = features(load_abc(path))["form"]
            scheme, cause = form["scheme"], str(form["cause"])
            if form["is_aabb"]:
                strict_aabb += 1
        except Exception as e:  # 0 air perdu : marqué, jamais d'exception
            errors += 1
            scheme, cause = "erreur-analyse", f"erreur-analyse:{type(e).__name__}"
        schemes[scheme] += 1
        causes[(scheme, cause)] += 1
        key = f"{scheme} :: {cause}"
        examples.setdefault(key, [])
        if len(examples[key]) < 10:
            examples[key].append(f"{tune_id} — {titles.get(tune_id, '?')}")

    n = len(abc_files)
    aabb = schemes.get("AABB", 0)
    print(f"type={args.type} airs={n} AABB-8-strict={strict_aabb} ({strict_aabb / n:.0%}) "
          f"AABB-scheme={aabb} ({aabb / n:.0%}) erreurs={errors}")
    print("\nschemes :")
    for scheme, count in schemes.most_common():
        print(f"  {count:4d} {scheme}")
    print("\ncauses :")
    for (scheme, cause), count in causes.most_common():
        print(f"  {count:4d} [{scheme}] {cause}")
    print("\nexemples par cause (10 max) :")
    for key in sorted(examples):
        print(f"  {key}")
        for ex in examples[key]:
            print(f"    - {ex}")
    return 0


def cmd_mine_cells(args: argparse.Namespace) -> int:
    """Mine a CellBank TOML (+ weights companion) from corpus tunes (D7)."""
    import json
    from collections import Counter

    from .trad import mine as trad_mine

    cells, stats = trad_mine.mine_cells(args.corpus, args.type, top_per_role=args.top)
    version = trad_mine.corpus_version(args.corpus)
    toml_text = trad_mine.render_bank(
        cells, args.type, version, stats["airs_lus"], trad_mine.today()
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(toml_text, encoding="utf-8")
    weights = [{"role": c["role"], "notes": c["notes"], "count": c["count"]} for c in cells]
    out.with_suffix("").with_suffix(".weights.json").write_text(
        json.dumps(weights, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    roles = Counter(c["role"] for c in cells)
    print(f"Miné {len(cells)} cellules ({stats['airs_lus']} airs, {stats['airs_erreur']} erreurs) -> {out}")
    print(f"Rôles : {dict(sorted(roles.items()))}")
    print(f"Rejets validation moteur : {stats['rejets']}")
    print(f"Unités 8 : {stats['unites_8']}, 4+4 notées : {stats['unites_4plus4_notees']}, "
          f"16 scindées notées : {stats['unites_16_scindees_notees']}, "
          f"croche hors positionnel : {stats['airs_croche_positionnel_ignore']}")
    print("Poids : le parseur moteur ignore tout champ inconnu (RawCell = role+notes) ; "
          "fréquences dans le compagnon .weights.json.")
    return 0


def cmd_mine_harmony(args: argparse.Namespace) -> int:
    """Mine chord degree tables from corpus tunes (D7)."""
    import json

    from .trad import mine as trad_mine

    harmony = trad_mine.mine_harmony(args.corpus, args.type)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(harmony, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Harmonie '{args.type}' ({harmony['airs']} airs) -> {out}")
    print(f"Top accords : {harmony['top_accords'][:6]}")
    print(f"Mesure 4 : {harmony['mesure_4']}")
    print(f"Mesure 8 : {harmony['mesure_8']}")
    return 0


def cmd_mine_tempo(args: argparse.Namespace) -> int:
    """Mine Q: tempos and meters from corpus tunes (D7)."""
    import json

    from .trad import mine as trad_mine

    tempo = trad_mine.mine_tempo(args.corpus, args.type)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tempo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Tempos -> {out}")
    for t, entry in sorted(tempo["types"].items()):
        q = entry["tempo_q"]
        q_txt = f"Q: n={q['n']} [{q['min']}-{q['max']}] méd={q['mediane']}" if q else "Q: MANQUANT"
        print(f"  {t}: {entry['airs']} airs, {entry['signatures']}, {q_txt}")
    if tempo["q_manquant"]:
        print(f"Tempo Q: absent de : {', '.join(tempo['q_manquant'])}")
    return 0


def cmd_feet_fetch(args: argparse.Namespace) -> int:
    """Download feet samples (SK1)."""
    from .feet.fetch import main as feet_main

    argv = ["--root", args.root, "--delay", str(args.delay)]
    if args.offline:
        argv.append("--offline")
    return feet_main(argv)


def cmd_feet_prepare(args: argparse.Namespace) -> int:
    """Cut/normalise feet hits (SK1)."""
    from .feet.prepare import main as feet_main

    return feet_main(["--root", args.root])


def cmd_feet_sf2(args: argparse.Namespace) -> int:
    """Build harmonium_trad.sf2 (SK1)."""
    from .feet.build import main as feet_main

    argv = ["--root", args.root]
    if args.output:
        argv += ["--output", args.output]
    return feet_main(argv)


def cmd_feet_preview(args: argparse.Namespace) -> int:
    """Feet check listen (SK1)."""
    from .feet.preview import main as feet_main

    argv = ["--out", args.out, "--root", args.root]
    if args.soundfont:
        argv += ["--soundfont", args.soundfont]
    if args.feet_soundfont:
        argv += ["--feet-soundfont", args.feet_soundfont]
    if args.feet_gain is not None:
        argv += ["--feet-gain", str(args.feet_gain)]
    if args.feet_humanize is not None:
        argv += ["--feet-humanize", str(args.feet_humanize)]
    if args.feet_seed is not None:
        argv += ["--feet-seed", str(args.feet_seed)]
    return feet_main(argv)


if __name__ == "__main__":
    sys.exit(main())
