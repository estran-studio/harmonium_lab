"""Preuve d'écoute et de mesure d'une banque construite (G6).

Rend chaque MIDI donné avec la banque (fluidsynth, pic normalisé comme
`trad-render`), à côté de son rendu avec la banque de référence (GeneralUser),
mesure la brillance (centroïde/rolloff spectraux) et la dynamique (RMS) des
trois versions (original, référence, banque) sur la fenêtre temporelle de la
boucle source, puis vérifie la tenue des notes soutenues : RMS par tranches de
0,5 s, chute maximale en dB (exigence : moins de 3 dB tant que la note dure).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from harmonium_lab.audioref.measures import measure_track
from harmonium_lab.audioref.render import default_soundfont, render_loop_wav

#: Fréquence d'échantillonnage d'analyse (Hz, comme `audioref.measures`).
ANALYSIS_SR = 22050
#: Tranche de mesure de tenue (s).
SUSTAIN_BUCKET_S = 0.5
#: Marge d'attaque écartée avant les tranches de tenue (s).
SUSTAIN_SKIP_S = 0.25
#: Chute maximale admise pendant une note tenue (dB).
SUSTAIN_MAX_DROP_DB = 3.0


def load_window(path: Path, duration_s: float | None = None, offset_s: float = 0.0,
                sr: int = ANALYSIS_SR) -> np.ndarray:
    import librosa

    y, _ = librosa.load(str(path), sr=sr, mono=True,
                        offset=offset_s, duration=duration_s)
    return y


def _spectral_dynamics(y: np.ndarray, sr: int = ANALYSIS_SR) -> dict[str, Any]:
    out = measure_track(y, sr=sr)
    peak = max(float(np.max(np.abs(y))), 1e-9)
    mean = out["dynamics"]["rms_mean"]
    return {
        "spectral_centroid_mean": out["spectral"]["spectral_centroid_mean"],
        "spectral_rolloff_mean": out["spectral"]["spectral_rolloff_mean"],
        "spectral_flatness_mean": out["spectral"]["spectral_flatness_mean"],
        "rms_mean": out["dynamics"]["rms_mean"],
        "rms_std": out["dynamics"]["rms_std"],
        "dynamic_range_db": out["dynamics"]["dynamic_range_db"],
        "rms_mean_peak_0125": round(mean * 0.125 / peak, 6),
        "rms_cv": round(out["dynamics"]["rms_std"] / max(mean, 1e-9), 4),
    }


def sustain_midi(program: int, note: int, seconds: float, path: Path) -> Path:
    """Écrit un MIDI d'une seule note tenue (program `program`, touche `note`)."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(initial_tempo=120.0)
    inst = pretty_midi.Instrument(program=int(program), name="tenue")
    inst.notes.append(
        pretty_midi.Note(velocity=100, pitch=int(note), start=0.05, end=float(seconds))
    )
    pm.instruments.append(inst)
    path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(path))
    return path


def rms_buckets_db(y: np.ndarray, sr: int = ANALYSIS_SR,
                   bucket_s: float = SUSTAIN_BUCKET_S,
                   skip_s: float = SUSTAIN_SKIP_S) -> list[float]:
    """RMS par tranches de `bucket_s` (dB), en écartant `skip_s` d'attaque."""
    step = int(bucket_s * sr)
    start = int(skip_s * sr)
    return [
        round(20.0 * float(np.log10(max(float(np.sqrt(np.mean(y[i : i + step] ** 2))), 1e-9))), 2)
        for i in range(start, len(y) - step + 1, step)
    ]


def measure_sustain(bank: Path, program: int, note: int, seconds: float,
                    workdir: Path) -> dict[str, Any]:
    """Rend une note tenue avec la banque et mesure la chute de RMS."""
    midi = sustain_midi(program, note, seconds, workdir / f"tenue_{program}_{note}.mid")
    wav = workdir / f"tenue_{program}_{note}.wav"
    render_loop_wav(midi, wav, soundfont=bank)
    y = load_window(wav, seconds)
    buckets = rms_buckets_db(y)
    if len(buckets) < 2:
        raise RuntimeError(f"tenue {program}/{note} : rendu trop court pour mesurer")
    start_drop = max(0.0, max(buckets[0] - b for b in buckets[1:]))
    # Toutes les tranches : une montée initiale ne masque pas un creux ultérieur.
    excursion = max(buckets) - min(buckets)
    adjacent_drop = max(0.0, max(a - b for a, b in zip(buckets, buckets[1:])))
    return {
        "program": program,
        "note": note,
        "seconds": seconds,
        "buckets_db": buckets,
        "max_drop_db": round(start_drop, 2),
        "max_adjacent_drop_db": round(adjacent_drop, 2),
        "excursion_db": round(excursion, 2),
        "holds": excursion < SUSTAIN_MAX_DROP_DB and min(buckets) > -80,
        "max_drop_target_db": SUSTAIN_MAX_DROP_DB,
        "wav": str(wav),
    }


def compare_loop(bank: Path, bank_id: str, midi_path: Path, tracks: Path,
                  out_dir: Path, reference_bank: Path | None = None) -> dict[str, Any]:
    """Rend + mesure une boucle : original / banque de référence / banque construite."""
    sidecar_path = midi_path.with_suffix(".json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    t0 = float(sidecar["source_start_s"])
    t1 = float(sidecar["source_end_s"])
    duration = t1 - t0
    if duration <= 0:
        raise ValueError(f"{sidecar_path} : fenêtre source vide")

    stem = midi_path.stem
    report: dict[str, Any] = {"loop": stem, "midi": str(midi_path)}

    original = tracks / f"{sidecar['track_id']}.flac"
    report["original"] = _spectral_dynamics(load_window(original, duration, offset_s=t0))
    report["source_window_s"] = [t0, t1]

    reference = midi_path.with_name(f"{stem}_GeneralUser.wav")
    render_loop_wav(midi_path, reference, soundfont=reference_bank or default_soundfont())
    report["reference_wav"] = str(reference)
    report["reference"] = _spectral_dynamics(load_window(reference, duration))

    bank_wav = midi_path.with_name(f"{stem}_{bank_id}.wav")
    render_loop_wav(midi_path, bank_wav, soundfont=bank)
    report["bank_wav"] = str(bank_wav)
    report["bank"] = _spectral_dynamics(load_window(bank_wav, duration))
    return report


def run_compare(bank: Path, midis: list[Path], tracks: Path, out_dir: Path,
                sustain: list[tuple[int, int, float]],
                reference_bank: Path | None = None) -> dict[str, Any]:
    """Rend toutes les boucles + tenues, écrit `report.json`, le retourne."""
    out_dir.mkdir(parents=True, exist_ok=True)
    bank_id = bank.stem
    report: dict[str, Any] = {"bank": str(bank), "bank_id": bank_id, "loops": [], "sustain": []}
    for midi_path in midis:
        report["loops"].append(
            compare_loop(bank, bank_id, midi_path, tracks, out_dir, reference_bank)
        )
    for program, note, seconds in sustain:
        report["sustain"].append(measure_sustain(bank, program, note, seconds, out_dir))
    (out_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"Banque : {report['bank']}")
    for loop in report["loops"]:
        print(f"\n=== {loop['loop']} ===")
        for version, label in (("original", "original"), ("reference", "reference"), ("bank", "banque")):
            m = loop.get(version)
            if not m:
                print(f"  {label:<9} : (absent)")
                continue
            print(
                f"  {label:<9} : centroïde {m['spectral_centroid_mean']:>7.0f} Hz, "
                f"rolloff {m['spectral_rolloff_mean']:>7.0f} Hz, "
                f"platitude {m['spectral_flatness_mean']:.4f}, "
                f"RMS {m['rms_mean']:.3f} ± {m['rms_std']:.3f}, "
                f"plage dyn. {m['dynamic_range_db']:.1f} dB"
            )
    for s in report.get("sustain", []):
        verdict = "TIENT" if s["holds"] else "DÉCROÎT"
        print(
            f"\nTenue {s['program']}/{s['note']} ({s['seconds']} s) : {verdict} — "
            f"chute depuis la première tranche {s['max_drop_db']:.2f} dB, "
            f"excursion {s['excursion_db']:.2f} dB (tranches {s['buckets_db']})"
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bank-compare",
        description="Rend des MIDI avec la banque et mesure brillance/dynamique vs original",
    )
    ap.add_argument("--bank", type=Path, required=True, help="banque .sf2 à évaluer")
    ap.add_argument("--midis", nargs="+", type=Path, required=True,
                    help="MIDI de boucles (sidecar .json du même stem pour l'original)")
    ap.add_argument("--tracks", type=Path, required=True,
                    help="dossier des originaux (<track_id>.flac)")
    ap.add_argument("--out", type=Path, default=Path("target/bank_compare"),
                    help="dossier du rapport JSON")
    ap.add_argument("--sustain", action="append", default=[],
                    help="tenue à vérifier 'program:note[:secondes]' (répétable)")
    ap.add_argument("--reference-soundfont", type=Path, default=None,
                    help="banque de référence (défaut : banque du moteur)")
    args = ap.parse_args(argv)

    sustain: list[tuple[int, int, float]] = []
    for spec in args.sustain:
        parts = spec.split(":")
        if len(parts) < 2:
            print(f"--sustain : format 'program:note[:secondes]' ({spec!r})", file=sys.stderr)
            return 2
        sustain.append((int(parts[0]), int(parts[1]), float(parts[2]) if len(parts) > 2 else 3.0))

    try:
        report = run_compare(
            args.bank, args.midis, args.tracks, args.out, sustain,
            args.reference_soundfont,
        )
    except RuntimeError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    print_report(report)
    failed = [s for s in report.get("sustain", []) if not s["holds"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())