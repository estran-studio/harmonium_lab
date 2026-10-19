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
    # trad-profile: build a trad type profile from corpus ABC/MIDI files
    p_trad = subparsers.add_parser("trad-profile", help="Build trad type profile from corpus tunes")
    p_trad.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_trad.add_argument("--corpus", default="corpus/trad", help="Corpus root (tunes/<type>/*.abc)")
    p_trad.add_argument("--output", "-o", required=True, help="Output profile JSON path")

    # trad-form-report: coverage of form analysis for a tune type
    p_form = subparsers.add_parser("trad-form-report", help="Form coverage report for a trad tune type")
    p_form.add_argument("--type", required=True, help="Tune type (reel, jig, waltz, ...)")
    p_form.add_argument("--corpus", default="corpus/trad", help="Corpus root")

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
        elif args.command == "trad-profile":
            return cmd_trad_profile(args)
        elif args.command == "trad-form-report":
            return cmd_trad_form_report(args)
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


if __name__ == "__main__":
    sys.exit(main())
