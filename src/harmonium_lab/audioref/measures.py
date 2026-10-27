"""Mesures audio dérivées d'un enregistrement de référence.

Enveloppe générique autour de `harmonium_lab.audio` (tempo, chroma,
brillance spectrale, dynamique) + identification tonalité/mode par gabarits
de classes de hauteurs. Aucun style supposé : les gabarits couvrent les
modes diatoniques et le mineur harmonique.

Sortie : dictionnaires JSON-sérialisables (voir `measure_track` et
`measure_corpus`). Les enregistrements restent hors dépôt (principe VII) ;
seuls ces dérivés sont versionnés.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

#: Intervalles (demi-tons depuis la tonique) de chaque mode/gamme candidate.
MODE_INTERVALS: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
}

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _template(intervals: tuple[int, ...]) -> np.ndarray:
    t = np.full(12, 0.15)  # plancher : bruit et notes de passage
    for i in intervals:
        t[i] = 1.0
    return t / np.linalg.norm(t)


_TEMPLATES = {m: _template(iv) for m, iv in MODE_INTERVALS.items()}


def match_mode(chroma: np.ndarray, tonic_pc: int | None = None) -> dict[str, Any]:
    """Mode le plus proche du chroma moyen, sur la tonique donnée ou, sans
    tonique, sur les 12 (les relatifs à égalité exacte sont départagés par
    ordre alphabétique : marge nulle = ambigu, à valider à l'oreille).

    Retourne aussi la marge sur le second candidat : une marge < 0.05
    signifie une tonalité ambiguë.
    """
    v = np.asarray(chroma, dtype=float)
    v = v / (np.linalg.norm(v) + 1e-12)
    roots = (tonic_pc,) if tonic_pc is not None else range(12)
    scored = []
    for root in roots:
        for mode, t in sorted(_TEMPLATES.items()):
            scored.append((float(v @ np.roll(t, root)), root, mode))
    scored.sort(key=lambda s: (-s[0], s[1], s[2]))
    (best, root, mode), (second, _r2, _m2) = scored[:2]
    return {
        "tonic": NAMES[root],
        "tonic_pc": root,
        "mode": mode,
        "score": round(best, 4),
        "margin": round(best - second, 4),
        "runner_up": {"tonic": NAMES[scored[1][1]], "mode": scored[1][2],
                      "score": round(second, 4)},
    }


def chroma_mean(y: np.ndarray, sr: int = 22050) -> np.ndarray:
    import librosa

    return librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)


def measure_track(y: np.ndarray, sr: int = 22050,
                  grid: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mesures dérivées d'un signal mono : rythme, tonalité/mode, spectre,
    dynamique, consonance. `grid` (optionnel) : grille rythmique déjà
    estimée, recopiée telle quelle."""
    from harmonium_lab import audio as _audio

    full = _audio.full_audio_analysis(y, sr)
    ch = chroma_mean(y, sr)
    out: dict[str, Any] = {
        "rhythm": full["rhythm"],
        "tonal": {**full["tonal"], "mode": match_mode(ch)},
        "chroma_mean": [round(float(v), 4) for v in ch],
        "spectral": full["spectral"],
        "dynamics": full["dynamics"],
        "dissonance": full["dissonance"],
    }
    if grid is not None:
        out["grid"] = grid
    return out


def _stats(values: list[float]) -> dict[str, float]:
    a = np.asarray(values, dtype=float)
    return {"n": len(a), "mean": round(float(a.mean()), 4),
            "std": round(float(a.std()), 4),
            "min": round(float(a.min()), 4), "max": round(float(a.max()), 4)}


_NUMERIC = (
    ("rhythm", "detected_tempo"), ("rhythm", "onset_rate"),
    ("rhythm", "tempo_stability"), ("tonal", "key_strength"),
    ("tonal", "tonal_power_ratio"), ("tonal", "chroma_entropy"),
    ("spectral", "spectral_centroid_mean"), ("spectral", "spectral_rolloff_mean"),
    ("spectral", "spectral_flatness_mean"), ("dynamics", "rms_mean"),
    ("dynamics", "dynamic_range_db"), ("dissonance", "harmonic_ratio"),
    ("dissonance", "percussive_ratio"),
)


def measure_corpus(tracks: dict[str, np.ndarray], sr: int = 22050,
                   grids: dict[str, dict[str, Any]] | None = None,
                   context_ids: list[str] | None = None,
                   meta: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Mesure chaque piste ; `context_ids` (optionnel) définit le sous-ensemble
    de mise en contexte (ex. toutes les pistes `zone`) dont les statistiques
    agrégées sont jointes sous `context`."""
    grids = grids or {}
    meta = meta or {}
    measured = {tid: measure_track(y, sr, grids.get(tid)) for tid, y in tracks.items()}
    out: dict[str, Any] = {"tracks": measured}
    if meta:
        out["meta"] = meta
    if context_ids:
        ctx = {tid: measured[tid] for tid in context_ids if tid in measured}
        stats = {}
        for section, key in _NUMERIC:
            vals = [t[section][key] for t in ctx.values()]
            stats[f"{section}.{key}"] = _stats(vals)
        pairs = [(t["tonal"]["mode"]["mode"], t["tonal"]["mode"]["tonic"]) for t in ctx.values()]
        out["context"] = {
            "track_ids": sorted(ctx),
            "stats": stats,
            "modes": {f"{m}@{t}": pairs.count((m, t)) for m, t in sorted(set(pairs))},
        }
    return out


def load_track_flac(path: Path, sr: int = 22050) -> np.ndarray:
    import librosa

    y, _ = librosa.load(str(path), sr=sr, mono=True)
    return y
