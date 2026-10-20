"""Préparation des frappes de pieds (chantier SK1).

Pour chaque frappe listée dans `samples/feet/selection.json`
(`{role: [{src, t}]}`) : découpe autour de l'attaque `t`, coupe le
silence, fondu de sortie court, normalisation ; écrit
`samples/feet/prepared/{heel,toe}/NN.wav` (16 bits mono 44,1 kHz).

Classification talon/pointe : rapport d'énergie grave/aigu calculé par
frappe (suggestion), rôle final fixé par la revue manuelle
(`samples/feet/review.md`, figé dans `selection.json`).

Point d'entrée des enregistrements du propriétaire : si
`samples/feet/own/{heel,toe}/*.wav` contient des fichiers, ils
remplacent les libres pour ce rôle (même normalisation, ordre
alphabétique).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample

from harmonium_lab.feet import SAMPLE_RATE, feet_dir

#: Pic cible après normalisation (−1 dBFS).
PEAK = 0.89
#: Fenêtre d'extraction après l'attaque (s).
WINDOW_S = 0.8
#: Durée min/max d'une frappe (s).
MIN_S, MAX_S = 0.05, 0.6
#: Fondu de sortie (s).
FADE_S = 0.015
#: Seuil de silence relatif au pic (−40 dB).
SILENCE = 0.01
#: Suggestion talon si énergie grave/aigu ≥ ce seuil.
HEEL_RATIO = 1.5


def load_mono_44k(path: Path) -> np.ndarray:
    """Décode (mp3/wav/…) en mono 44,1 kHz flottant."""
    data, sr = sf.read(str(path), always_2d=True)
    mono = data.mean(axis=1).astype(np.float64)
    if sr != SAMPLE_RATE:
        mono = resample(mono, int(len(mono) * SAMPLE_RATE / sr))
    return mono


def spectral_features(hit: np.ndarray) -> tuple[float, float]:
    """(centroïde spectral Hz, énergie 70–400 Hz / 2–9 kHz)."""
    if len(hit) < 16:
        return 0.0, 0.0
    spec = np.abs(np.fft.rfft(hit * np.hanning(len(hit))))
    freqs = np.fft.rfftfreq(len(hit), 1 / SAMPLE_RATE)
    total = spec.sum()
    centroid = float((spec * freqs).sum() / total) if total > 0 else 0.0
    low = spec[(freqs >= 70) & (freqs < 400)].sum()
    high = spec[(freqs >= 2000) & (freqs < 9000)].sum()
    return centroid, float(low / high) if high > 0 else float("inf")


def suggest_role(hit: np.ndarray) -> str:
    """talon si grave dominant, sinon pointe (revue manuelle : review.md)."""
    _, ratio = spectral_features(hit)
    return "heel" if ratio >= HEEL_RATIO else "toe"


def cut_hit(audio: np.ndarray, at: float) -> np.ndarray:
    """Découpe une frappe : attaque à `at` (s), silence coupé, fondu court."""
    sr = SAMPLE_RATE
    start = max(0, int((at - 0.005) * sr))
    window = audio[start:start + int(WINDOW_S * sr)]
    if window.size == 0:
        raise ValueError(f"attaque {at}s hors audio")
    peak = np.abs(window).max()
    if peak <= 0:
        raise ValueError(f"silence à {at}s")
    loud = np.nonzero(np.abs(window) >= SILENCE * peak)[0]
    end = min(loud[-1] + int(0.01 * sr), len(window))
    hit = window[loud[0]:end]
    if len(hit) > int(MAX_S * sr):
        hit = hit[:int(MAX_S * sr)]
    if len(hit) < int(MIN_S * sr):
        pad = np.zeros(int(MIN_S * sr) - len(hit))
        hit = np.concatenate([hit, pad])
    fade = min(int(FADE_S * sr), len(hit))
    ramp = 0.5 * (1 + np.cos(np.pi * np.arange(fade) / fade))
    hit[-fade:] *= ramp
    hit *= PEAK / np.abs(hit).max()
    return hit


def write_wav(path: Path, hit: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(hit, -1.0, 1.0)
    sf.write(str(path), (pcm * 32767).astype(np.int16), SAMPLE_RATE)


def prepare_libre(root: Path, selection: dict) -> list[dict]:
    """Applique `selection.json` → prepared/. Retourne la table de revue."""
    manifest = {e["id"]: e for e in
                (json.loads(line) for line in (root / "manifest.jsonl")
                 .read_text(encoding="utf-8").splitlines() if line.strip())}
    cache: dict[str, np.ndarray] = {}
    table = []
    for role, hits in selection.items():
        if role not in ("heel", "toe"):
            continue  # ex. "_comment"
        for i, h in enumerate(hits, start=1):
            src = h["src"]
            if src not in cache:
                cache[src] = load_mono_44k(root / "raw" / f"{src}.mp3")
            hit = cut_hit(cache[src], h["t"])
            centroid, ratio = spectral_features(hit)
            suggested = suggest_role(hit)
            dest = root / "prepared" / role / f"{i:02d}.wav"
            write_wav(dest, hit)
            table.append({"role": role, "file": dest.name, "src": src,
                          "title": manifest[src]["title"], "t": h["t"],
                          "centroid_hz": round(centroid),
                          "lowhi": round(ratio, 2) if ratio != float("inf") else None,
                          "suggested": suggested,
                          "avertissement": suggested != role})
    return table


def prepare_own(root: Path) -> dict[str, list[str]]:
    """Normalise `own/{heel,toe}/*.wav` → prepared/. Retourne les rôles remplacés."""
    replaced: dict[str, list[str]] = {}
    for role in ("heel", "toe"):
        wavs = sorted((root / "own" / role).glob("*.wav")) if (root / "own" / role).is_dir() else []
        if not wavs:
            continue
        outdir = root / "prepared" / role
        for old in outdir.glob("*.wav"):
            old.unlink()
        names = []
        for i, wav in enumerate(wavs, start=1):
            audio = load_mono_44k(wav)
            hit = cut_hit(audio, 0.0) if np.abs(audio).max() > 0 else audio
            dest = outdir / f"{i:02d}.wav"
            write_wav(dest, hit)
            names.append(wav.name)
        replaced[role] = names
    return replaced


def prepare(root: Path, selection: dict) -> tuple[list[dict], dict[str, list[str]]]:
    table = prepare_libre(root, selection)
    replaced = prepare_own(root)
    return table, replaced


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feet-prepare",
                                 description="Découpe/normalise les frappes (raw/ → prepared/)")
    ap.add_argument("--root", type=Path, default=feet_dir(), help="dossier samples/feet")
    args = ap.parse_args(argv)
    try:
        selection = json.loads((args.root / "selection.json").read_text(encoding="utf-8"))
        table, replaced = prepare(args.root, selection)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    for row in table:
        flag = "  ← SUGGESTION CONTRAIRE" if row["avertissement"] else ""
        print(f"{row['role']:>4} {row['file']} src={row['src']} t={row['t']}s "
              f"centroide={row['centroid_hz']}Hz grave/aigu={row['lowhi']}{flag}")
    for role, names in replaced.items():
        print(f"{role} : {len(names)} enregistrement(s) du propriétaire "
              f"remplacent les libres ({', '.join(names)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
