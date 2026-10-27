"""Structure d'un enregistrement : matrice d'auto-similarité, boucles, sections.

Méthode générique (aucun style supposé) :

- chroma synchronisé à la mesure (moyenne par mesure sur la grille) ;
- auto-similarité cosinus entre mesures ;
- score de chaque longueur de boucle : similarité moyenne des paires de
  mesures séparées d'un multiple de cette longueur (diagonales) ;
- sections : pics de nouveauté du chroma (1 − cos entre moitiés
  avant/après une fenêtre glissante), fusionnés à l'échelle d'au moins
  4 mesures.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .grid import Grid


def bar_chroma(y: np.ndarray, grid: Grid, sr: int = 22050,
               hop: int = 512) -> tuple[np.ndarray, list[float]]:
    """Chroma moyen par mesure + instants de début de mesure (s)."""
    import librosa

    ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    times = librosa.times_like(np.arange(ch.shape[1]), sr=sr, hop_length=hop)
    starts = [grid.bar_start(b) for b in range(grid.n_bars)]
    mat = np.zeros((12, len(starts)))
    for b, t0 in enumerate(starts):
        m = (times >= t0) & (times < t0 + grid.bar_s)
        if m.any():
            mat[:, b] = ch[:, m].mean(axis=1)
    return mat, starts

def self_similarity(mat: np.ndarray) -> np.ndarray:
    """Matrice cosinus entre colonnes (mesures)."""
    n = mat / (np.linalg.norm(mat, axis=0, keepdims=True) + 1e-12)
    return n.T @ n


def loop_scores(sim: np.ndarray, lengths: range | list[int]) -> dict[int, dict[str, float]]:
    """Score de chaque longueur de boucle L (en mesures) : similarité moyenne
    des blocs adjacents sim[i, i+L], moins la moyenne hors-diagonale
    (hasard). Une boucle réelle dépasse ~0.15."""
    n = sim.shape[0]
    off = sim[~np.eye(n, dtype=bool)].mean()
    out = {}
    for L in lengths:
        if L < 1 or L >= n:
            continue
        vals = [sim[i, i + L] for i in range(n - L)]
        out[L] = {"score": round(float(np.mean(vals) - off), 4), "pairs": len(vals)} \
            if vals else {"score": 0.0, "pairs": 0}
    return out


def novelty_sections(mat: np.ndarray, starts: list[float],
                     min_bars: int = 4) -> list[dict[str, Any]]:
    """Frontières de sections par nouveauté harmonique. Retourne des
    sections {start_bar, start_s, end_s, label} numérotées ; l'étiquetage
    musical (intro, boucle, pont) reste manuel, à valider à l'oreille."""
    n = mat.shape[1]
    norm = mat / (np.linalg.norm(mat, axis=0, keepdims=True) + 1e-12)
    w = 2
    nov = np.zeros(n)
    for i in range(w, n - w):
        nov[i] = 1.0 - float(norm[:, i - w:i].mean(1) @ norm[:, i:i + w].mean(1))
    import librosa

    peaks = librosa.util.peak_pick(nov, pre_max=2, post_max=2, pre_avg=4,
                                   post_avg=4, delta=0.08, wait=min_bars)
    bounds = [0] + [p for p in sorted(peaks) if p >= min_bars] + [n]
    bounds = [b for i, b in enumerate(bounds)
              if i == 0 or b - bounds[i - 1] >= min_bars or i == len(bounds) - 1]
    secs = []
    for k in range(len(bounds) - 1):
        secs.append({"section": k, "start_bar": int(bounds[k]),
                     "end_bar": int(bounds[k + 1]),
                     "start_s": round(starts[bounds[k]], 2),
                     "end_s": round(starts[bounds[k + 1] - 1]
                                    + (starts[1] - starts[0]), 2)
                     if len(starts) > 1 else round(starts[bounds[k]], 2)})
    return secs


def analyze_structure(y: np.ndarray, grid: Grid, sr: int = 22050,
                      max_loop_bars: int = 16) -> dict[str, Any]:
    """Chaîne complète : chroma par mesure, auto-similarité, scores de
    boucle (1..`max_loop_bars`), sections."""
    mat, starts = bar_chroma(y, grid, sr)
    sim = self_similarity(mat)
    loops = loop_scores(sim, range(1, min(max_loop_bars, grid.n_bars - 1) + 1))
    best = max(loops, key=lambda L: loops[L]["score"]) if loops else None
    return {
        "n_bars": grid.n_bars,
        "loop_scores": {str(L): v for L, v in loops.items()},
        "best_loop_bars": best,
        "sections": novelty_sections(mat, starts),
        "bar_starts_s": [round(s, 3) for s in starts],
    }
