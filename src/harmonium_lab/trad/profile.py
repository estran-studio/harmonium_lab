"""Profils par type : distributions D5 sur un corpus d'airs (D3/D5).

``build_profile`` agrège les ``features()`` : moyenne, écart-type (population),
quantiles 10/50/90 des scalaires, histogrammes moyens, fréquences des
cellules et des bigrammes d'accords. Sortie JSON-sérialisable, versionnée
(``references/trad-<type>/profile.json``).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from .features import (
    DURATION_BUCKETS,
    FEATURE_SCALARS,
    INTERVAL_CLASSES,
    features,
)
from .model import TradTune

PROFILE_VERSION = 1


def _get_path(feat: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = feat
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _scalar_stats(values: list[float]) -> dict[str, Any]:
    arr = np.asarray(values, dtype=float)
    q10, q50, q90 = np.percentile(arr, [10, 50, 90])
    return {
        "mean": round(float(np.mean(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "q10": round(float(q10), 4),
        "q50": round(float(q50), 4),
        "q90": round(float(q90), 4),
        "count": len(values),
    }


def build_profile(tunes: list[TradTune], tune_type: str) -> dict[str, Any]:
    """Construit le profil d'un type depuis des airs (pur, déterministe)."""
    feats = [features(t) for t in tunes]

    scalars: dict[str, Any] = {}
    for path in FEATURE_SCALARS:
        name = "__".join(path)
        values = [
            v for f in feats if (v := _get_path(f, path)) is not None
        ]
        if values:
            scalars[name] = _scalar_stats([float(v) for v in values])

    histograms: dict[str, Any] = {}
    interval_hists = [
        [f["intervals"]["hist"][c] for c in INTERVAL_CLASSES] for f in feats
    ]
    if interval_hists:
        histograms["interval_hist"] = {
            "bins": list(INTERVAL_CLASSES),
            "mean": [round(v, 4) for v in np.mean(np.asarray(interval_hists), axis=0)],
            "count": len(interval_hists),
        }
    duration_hists = [
        [f["rhythm"]["duration_hist"][b] for b in DURATION_BUCKETS] for f in feats
    ]
    if duration_hists:
        histograms["duration_hist"] = {
            "bins": list(DURATION_BUCKETS),
            "mean": [round(v, 4) for v in np.mean(np.asarray(duration_hists), axis=0)],
            "count": len(duration_hists),
        }
    # Positions d'attaque : moyenne sur la longueur majoritaire (types homogènes).
    onset_hists = [f["rhythm"]["onset_hist"] for f in feats]
    if onset_hists:
        top_len = Counter(len(h) for h in onset_hists).most_common(1)[0][0]
        kept = [h for h in onset_hists if len(h) == top_len]
        histograms["onset_hist"] = {
            "bins": [str(s) for s in range(top_len)],
            "mean": [round(v, 4) for v in np.mean(np.asarray(kept), axis=0)],
            "count": len(kept),
            "slots": top_len,
        }

    cell_counts: Counter[str] = Counter()
    for f in feats:
        cell_counts.update(f["cells"]["vocabulary"])
    total_cells = sum(cell_counts.values())
    bigram_counts: Counter[str] = Counter()
    degree_counts: Counter[str] = Counter()
    for f in feats:
        bigram_counts.update(f["harmony"]["chord_bigrams"])
        degree_counts.update(f["harmony"]["chord_degree_counts"])
    total_bigrams = sum(bigram_counts.values())
    total_degrees = sum(degree_counts.values())

    return {
        "tune_type": tune_type,
        "tune_count": len(tunes),
        "version": PROFILE_VERSION,
        "scalars": scalars,
        "histograms": histograms,
        "cell_frequencies": {
            c: round(n / total_cells, 6) for c, n in sorted(cell_counts.items())
        }
        if total_cells
        else {},
        "chord_bigram_frequencies": {
            b: round(n / total_bigrams, 6) for b, n in sorted(bigram_counts.items())
        }
        if total_bigrams
        else {},
        "chord_degree_frequencies": {
            d: round(n / total_degrees, 6) for d, n in sorted(degree_counts.items())
        }
        if total_degrees
        else {},
    }


def save_profile(profile: dict[str, Any], path: Path | str) -> None:
    """Sauvegarde un profil trad en JSON."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n")


def load_profile(path: Path | str) -> dict[str, Any]:
    """Charge un profil trad depuis JSON."""
    return json.loads(Path(path).read_text())
