"""Swing et micro-timing en fonction du tempo : Jazz Trio Database (JTD) v0.2 (phase 019, L2 → A6).

Prolonge `timing.py` (E7) sans le modifier : mêmes lecteurs (`read_track`, `swing_observations`,
`placements_of`, `valid_intervals`, `locate`), mêmes annotations CSV/JSON lues dans l'archive ZIP
(jamais `piano_midi.mid`, jamais d'audio), même vérification SHA256 + MD5 avant lecture. Ce que E7
ne donne pas et que ce module livre pour la tâche A6 du moteur (« swing selon le tempo ») :

1. des CLASSES de tempo (`< 120`, `120–180`, `180–240`, `≥ 240` BPM) dont la plage est celle de
   `keep_track` (60 à 330 BPM) et non les tranches de 100 à 330 BPM d'E7, qui écarteraient les pistes lentes ; en fait
   l'archive entière ne contient aucun tempo hors de 102–299 BPM : « < 120 » = 100–120 BPM, « ≥ 240 » = 240–300 BPM ;
   par classe et par instrument : rapport de swing (médiane par piste d'au moins
   `MIN_SWING_OBSERVATIONS` contretemps, puis centiles, moyenne et dispersion sur les pistes),
   rapport long/court, effectifs (pistes, musiciens distincts), intervalle de confiance à 95 % de
   la médiane par bootstrap, par piste ET par musicien (un même batteur pèse sur plusieurs pistes) ;
2. le MICRO-TIMING par classe et par instrument : écarts absolus au temps (peu fiables) et surtout
   relatifs basse−batterie, piano−batterie, basse−piano, en pas (¼ de temps) et en ms, aux temps 1-3
   et 2-4, avec intervalle de confiance de la médiane par piste, dispersion par piste et résolution
   (10 ms des CSV rapportés au pas de chaque classe) ;
3. une COURBE continue `swing_ratio(tempo)` : régression robuste (Huber) des médianes par piste sur
   le tempo, quatre formes comparées par validation croisée par musicien (constante, linéaire,
   linéaire en log du tempo, plateau puis décroissance linéaire), intervalle de confiance à 95 %
   par bootstrap (pistes et musiciens), monotonie, lissage par tranches de 20 BPM, résidu,
   bornes de validité : aucune valeur hors du tempo observé ;
4. la table à reprendre par A6 (`a6_table`), les limites et un verdict de fiabilité par classe.

Aucune phrase de solo ni suite de notes : seulement des comptes, des médianes et des centiles.
Écritures déterministes (clés triées, arrondis fixes, aucun horodatage, graine fixe).

Usage : `python -m harmonium_lab.backing.swing_tempo [--measures] [--summary] [--out-dir DOSSIER]`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr, trim_mean

from . import timing
from .corpus_cache import ROOT, DigestError, write_json
from .timing import (
    ATTRIBUTION,
    INSTRUMENTS,
    METRE_GROUPS,
    MIN_JITTER_PAIRS,
    MIN_PAIRED_SHARE,
    MIN_SWING_OBSERVATIONS,
    SOURCE_LICENCE,
    SOURCE_MD5,
    SOURCE_NAME,
    SOURCE_SHA256,
    SOURCE_URL,
    SOURCE_VERSION,
    STEPS_PER_BEAT,
    SWING_WINDOW,
    TEMPO_RANGE,
    TrackStats,
    jitter_block,
    keep_track,
    long_short,
    placement_block,
    placements_of,
    read_track,
    swing_block,
    swing_observations,
    track_names,
)

ARCHIVE = timing.ARCHIVE
OUTPUT_DIR = ROOT / "references" / "jtd-swing-tempo"
OUTPUT_NAME = "measures-swing-tempo.json"
COMMAND = "python -m harmonium_lab.backing.swing_tempo --measures"

ENGINE_DEFAULT_SWING_RATIO = 0.71
"""`meter.default_swing_ratio` du profil moteur `wjazzd_swing` (E7), pour l'écart par classe."""

# --------------------------------------------------------------------------------------
# Classes de tempo

TEMPO_CLASSES: tuple[tuple[str, str, float, float], ...] = (
    ("60-120", "< 120 BPM", 60.0, 120.0),
    ("120-180", "120–180 BPM", 120.0, 180.0),
    ("180-240", "180–240 BPM", 180.0, 240.0),
    ("240-330", "≥ 240 BPM", 240.0, 330.0),
)
"""`(identifiant, libellé, borne basse incluse, borne haute exclue)` ; la dernière borne est incluse
(`keep_track` accepte 330 BPM). Les bornes couvrent la plage `TEMPO_RANGE` de 60 à 330 BPM."""
CLASS_IDS = tuple(c[0] for c in TEMPO_CLASSES)
MIN_TRACKS_PER_CLASS = 30
"""Pistes mesurées minimales par classe (batterie) pour garder les bornes ci-dessus."""

INSTRUMENT_ROLE = {"drums": "drummer", "bass": "bassist", "piano": "pianist"}
"""Instrument → rôle dans `metadata.json["musicians"]` (le musicien d'un enregistrement)."""

PAIR_INSTRUMENTS = {"rel_bass_drums": ("bass", "drums"), "rel_piano_drums": ("piano", "drums"),
                    "rel_bass_piano": ("bass", "piano")}
ABSOLUTE_KEYS = ("abs_drums", "abs_bass", "abs_piano")
RELATIVE_KEYS = tuple(PAIR_INSTRUMENTS)
MICRO_GROUPS = ("all", "beats_1_3", "beats_2_4")
MIN_ASYMMETRY_PAIRS = 10
"""Paires par groupe de temps (1-3 et 2-4) pour qu'une piste entre dans l'écart 2-4 moins 1-3."""

CSV_RESOLUTION_MS = 10.0


def tempo_class(tempo: float) -> str | None:
    """Identifiant de classe d'un tempo ; `None` hors de 60–330 BPM (330 inclus)."""
    for ident, _, lo, hi in TEMPO_CLASSES:
        if lo <= tempo < hi:
            return ident
    if tempo == TEMPO_CLASSES[-1][3]:
        return TEMPO_CLASSES[-1][0]
    return None


# --------------------------------------------------------------------------------------
# Bootstrap (graine fixe, déterministe)

SEED = 20260211
BOOTSTRAP_MEDIAN = 2000
"""Rééchantillons des intervalles de confiance des médianes (≥ 1000 exigés)."""
BOOTSTRAP_CURVE = 1000
"""Rééchantillons des intervalles de confiance de la courbe (≥ 1000 exigés)."""
CI_LEVEL = (2.5, 97.5)
TRIM = 0.1
"""Proportion rognée de chaque côté par les moyennes tronquées (la même que `timing._pct`)."""


def _rng(*parts: Any) -> np.random.Generator:
    """Générateur déterministe propre à une mesure (indépendant de l'ordre de calcul)."""
    key = "|".join(str(p) for p in (SEED, *parts))
    return np.random.default_rng(zlib.crc32(key.encode()))


def _statistic(data: np.ndarray, stat: str) -> np.ndarray:
    """Statistique appliquée le long du dernier axe : médiane, ou moyenne tronquée à 10 % de chaque côté."""
    if stat == "trimmed_mean":
        return trim_mean(data, TRIM, axis=-1)
    return np.median(data, axis=-1)


def bootstrap_ci(values: Sequence[float], rng: np.random.Generator, n_resamples: int | None = None,
                 stat: str = "median") -> list[float] | None:
    """IC à 95 % (centiles 2,5 / 97,5) de la médiane (ou de la moyenne tronquée, `stat="trimmed_mean"`) par
    rééchantillonnage des valeurs ; `None` sous 2 valeurs."""
    data = np.asarray(values, dtype=float)
    n = len(data)
    if n < 2:
        return None
    idx = rng.integers(0, n, size=(n_resamples or BOOTSTRAP_MEDIAN, n))
    samples = _statistic(data[idx], stat)
    return [float(np.percentile(samples, CI_LEVEL[0])), float(np.percentile(samples, CI_LEVEL[1]))]


def bootstrap_ci_clustered(values: Sequence[float], groups: Sequence[str], rng: np.random.Generator,
                           n_resamples: int | None = None, stat: str = "median") -> list[float] | None:
    """IC à 95 % de la médiane (ou moyenne tronquée) en rééchantillonnant les GROUPES (musiciens) entiers :
    les pistes d'un même musicien ne sont pas indépendantes. `None` sous 2 groupes."""
    data = np.asarray(values, dtype=float)
    if len(data) == 0:
        return None
    _, codes = np.unique(np.asarray(groups), return_inverse=True)
    n_groups = int(codes.max()) + 1
    if n_groups < 2:
        return None
    members = [data[codes == g] for g in range(n_groups)]
    draws = rng.integers(0, n_groups, size=(n_resamples or BOOTSTRAP_MEDIAN, n_groups))
    samples = np.array([_statistic(np.concatenate([members[g] for g in row]), stat) for row in draws])
    return [float(np.percentile(samples, CI_LEVEL[0])), float(np.percentile(samples, CI_LEVEL[1]))]


def dispersion(values: Sequence[float]) -> dict[str, Any]:
    """Dispersion entre pistes : écart-type, écart interquartile, écart-type robuste (1,4826 × MAD)."""
    data = np.asarray(values, dtype=float)
    if len(data) == 0:
        return {"n": 0, "std": None, "iqr": None, "robust_std_mad": None}
    p25, p75 = np.percentile(data, [25, 75])
    return {"n": int(len(data)), "std": float(np.std(data, ddof=1)) if len(data) > 1 else None,
            "iqr": float(p75 - p25), "robust_std_mad": float(1.4826 * np.median(np.abs(data - np.median(data))))}


def _halfwidth(ci: Sequence[float] | None) -> float | None:
    return None if ci is None else (ci[1] - ci[0]) / 2.0


# --------------------------------------------------------------------------------------
# Lecture : pistes retenues (plage 60–330 BPM, pas seulement 100–330)


def musician(track: timing.Track, inst: str) -> str:
    """Musicien de l'instrument ; une piste sans nom forme son propre groupe (hypothèse prudente :
    indépendante des autres)."""
    name = (track.meta.get("musicians") or {}).get(INSTRUMENT_ROLE[inst])
    return str(name) if name else f"inconnu:{track.fname}"


def class_stats(track: timing.Track, label: str) -> TrackStats:
    """Mesures d'une piste classée : `TrackStats` de E7 avec la classe de tempo à la place de la tranche
    (réutilise `swing_observations` et `placements_of`)."""
    swing = {}
    for inst in INSTRUMENTS:
        ratios, n_intervals, n_with = swing_observations(track.beats, track.onsets[inst])
        swing[inst] = {"ratios": ratios, "n_intervals": n_intervals, "n_intervals_with_attack": n_with}
    drums_ratio = None
    if len(swing["drums"]["ratios"]) >= MIN_SWING_OBSERVATIONS:
        drums_ratio = float(np.median(swing["drums"]["ratios"]))
    return TrackStats(track, label, swing, drums_ratio, placements_of(track))


def read_stats(archive: zipfile.ZipFile) -> tuple[list[TrackStats], dict[str, Any]]:
    """Pistes retenues (4 temps, 60–330 BPM, ≥ `MIN_PAIRED_SHARE` de temps appariés basse ET batterie) et
    comptes du filtre. Les tempos extrêmes de l'archive entière sont relevés pour dire ce qui manque."""
    counts: dict[str, Any] = {"total": 0, "time_signature_4": 0, "tempo_in_range": 0, "paired_ok": 0,
                              "retained": 0, "tempo_min_archive": None, "tempo_max_archive": None}
    tempos: list[float] = []
    kept: list[TrackStats] = []
    for fname in track_names(archive):
        counts["total"] += 1
        track = read_track(archive, fname)
        tempo = track.meta.get("tempo")
        if tempo is not None:
            tempos.append(float(tempo))
        if track.meta.get("time_signature") != 4:
            continue
        counts["time_signature_4"] += 1
        if not keep_track(track.meta):
            continue
        counts["tempo_in_range"] += 1
        if track.paired_share() < MIN_PAIRED_SHARE:
            continue
        counts["paired_ok"] += 1
        label = tempo_class(track.tempo)
        if label is None:
            continue
        counts["retained"] += 1
        kept.append(class_stats(track, label))
    if tempos:
        counts["tempo_min_archive"], counts["tempo_max_archive"] = min(tempos), max(tempos)
    return kept, counts


def by_class(stats: Sequence[TrackStats]) -> dict[str, list[TrackStats]]:
    out: dict[str, list[TrackStats]] = {ident: [] for ident in CLASS_IDS}
    for s in stats:
        out[s.bin].append(s)
    return {"all": list(stats), **out}


def measured(stats: Sequence[TrackStats], inst: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Pistes mesurées d'un instrument : `(médianes de swing par piste, tempos, musiciens)` ; une piste
    compte à partir de `MIN_SWING_OBSERVATIONS` contretemps (comme `swing_block`)."""
    values, tempos, groups = [], [], []
    for s in stats:
        ratios = s.swing[inst]["ratios"]
        if len(ratios) >= MIN_SWING_OBSERVATIONS:
            values.append(float(np.median(ratios)))
            tempos.append(s.track.tempo)
            groups.append(musician(s.track, inst))
    return np.asarray(values, dtype=float), np.asarray(tempos, dtype=float), groups


# --------------------------------------------------------------------------------------
# Fiabilité : seuils écrits

VERDICT_ASSEZ = {"min_tracks": 60, "min_musicians": 8, "max_top_musician_share": 0.25, "max_ci_halfwidth_swing": 0.02}
VERDICT_JUSTE = {"min_tracks": 30, "min_musicians": 5}
VERDICT_RULES = {
    "assez": f"≥ {VERDICT_ASSEZ['min_tracks']} pistes mesurées, ≥ {VERDICT_ASSEZ['min_musicians']} musiciens distincts du "
             f"rôle, un musicien ≤ {VERDICT_ASSEZ['max_top_musician_share']:.0%} des pistes et, pour le swing, demi-largeur "
             f"de l'IC95 % par musicien ≤ {VERDICT_ASSEZ['max_ci_halfwidth_swing']} (≈ l'écart entre classes voisines)",
    "juste": f"≥ {VERDICT_JUSTE['min_tracks']} pistes mesurées et ≥ {VERDICT_JUSTE['min_musicians']} musiciens distincts",
    "trop peu": "en dessous de « juste » : ne pas reprendre la valeur sans autre source",
}


def verdict(n_tracks: int, n_musicians: int, top_share: float | None, ci_halfwidth: float | None = None) -> dict[str, Any]:
    """Verdict « assez » / « juste » / « trop peu » avec les critères manqués pour « assez »."""
    missed = []
    if n_tracks < VERDICT_ASSEZ["min_tracks"]:
        missed.append(f"pistes {n_tracks} < {VERDICT_ASSEZ['min_tracks']}")
    if n_musicians < VERDICT_ASSEZ["min_musicians"]:
        missed.append(f"musiciens {n_musicians} < {VERDICT_ASSEZ['min_musicians']}")
    if top_share is not None and top_share > VERDICT_ASSEZ["max_top_musician_share"]:
        missed.append(f"un musicien porte {top_share:.0%} des pistes")
    if ci_halfwidth is not None and ci_halfwidth > VERDICT_ASSEZ["max_ci_halfwidth_swing"]:
        missed.append(f"demi-largeur de l'IC {ci_halfwidth:.3f} > {VERDICT_ASSEZ['max_ci_halfwidth_swing']}")
    if not missed:
        level = "assez"
    elif n_tracks >= VERDICT_JUSTE["min_tracks"] and n_musicians >= VERDICT_JUSTE["min_musicians"]:
        level = "juste"
    else:
        level = "trop peu"
    return {"verdict": level, "n_tracks": n_tracks, "n_musicians": n_musicians,
            "top_musician_share": top_share, "ci_halfwidth": ci_halfwidth, "missed_for_assez": missed}


def _top_share(names: Sequence[str]) -> float | None:
    return max(Counter(names).values()) / len(names) if names else None


# --------------------------------------------------------------------------------------
# Classes : swing par instrument


def swing_class_block(members: Sequence[TrackStats], inst: str, label: str) -> dict[str, Any]:
    """Swing d'un instrument sur un ensemble de pistes (classe) : bloc `swing_block` de E7 (centiles,
    long/court, part d'intervalles avec attaque) + médiane, dispersion, effectifs de musiciens et IC95 %
    par bootstrap des pistes et des musiciens."""
    block = swing_block(members, inst)
    values, _, groups = measured(members, inst)
    n = len(values)
    median = float(np.median(values)) if n else None
    ci_tracks = bootstrap_ci(values, _rng("median", label, inst, "tracks"))
    ci_musicians = bootstrap_ci_clustered(values, groups, _rng("median", label, inst, "musicians"))
    ratio = None
    if ci_tracks and ci_musicians and ci_tracks[1] > ci_tracks[0]:
        ratio = _halfwidth(ci_musicians) / _halfwidth(ci_tracks)
    block.update({
        "median": median,
        "median_long_short": long_short(median) if median is not None else None,
        "dispersion": dispersion(values),
        "n_musicians": len({musician(s.track, inst) for s in members}),
        "n_musicians_measured": len(set(groups)),
        "top_musician_share": _top_share(groups),
        "ci95_tracks": ci_tracks,
        "ci95_musicians": ci_musicians,
        "ci95_musicians_long_short": [long_short(x) for x in ci_musicians] if ci_musicians else None,
        "design_effect": {
            "ci_width_ratio_musicians_over_tracks": ratio,
            "n_effective_tracks": (n / ratio ** 2) if ratio else None,
        },
    })
    return block


def tempo_summary(stats: Sequence[TrackStats]) -> dict[str, Any]:
    tempos = np.array([s.track.tempo for s in stats])
    if not len(tempos):
        return {"n": 0, "min": None, "median": None, "max": None, "p10": None, "p90": None}
    return {"n": int(len(tempos)), "min": float(tempos.min()), "p10": float(np.percentile(tempos, 10)),
            "median": float(np.median(tempos)), "p90": float(np.percentile(tempos, 90)), "max": float(tempos.max())}


def resolution_block(stats: Sequence[TrackStats]) -> dict[str, Any]:
    """Ce que la résolution de 10 ms des CSV représente au tempo médian de la classe."""
    if not stats:
        return {}
    median_tempo = float(np.median([s.track.tempo for s in stats]))
    beat_ms = 60000.0 / median_tempo
    step_ms = beat_ms / STEPS_PER_BEAT
    return {
        "median_tempo_bpm": median_tempo,
        "beat_ms": beat_ms,
        "step_ms": step_ms,
        "csv_resolution_ms": CSV_RESOLUTION_MS,
        "csv_resolution_steps": CSV_RESOLUTION_MS / step_ms,
        "swing_ratio_quantum_per_observation": CSV_RESOLUTION_MS / beat_ms,
        "quantization_noise_sd_ms": {"one_value": CSV_RESOLUTION_MS / math.sqrt(12.0),
                                     "difference_of_two_values": CSV_RESOLUTION_MS / math.sqrt(6.0)},
        "quantization_noise_sd_steps_difference": CSV_RESOLUTION_MS / math.sqrt(6.0) / step_ms,
    }


def class_block(label: str, members: Sequence[TrackStats]) -> dict[str, Any]:
    ident = next((c for c in TEMPO_CLASSES if c[0] == label), None)
    swing = {inst: swing_class_block(members, inst, label) for inst in INSTRUMENTS}
    drums = swing["drums"]
    gap = None
    if drums["median"] is not None:
        gap = {
            "engine_default_swing_ratio": ENGINE_DEFAULT_SWING_RATIO,
            "gap": drums["median"] - ENGINE_DEFAULT_SWING_RATIO,
            "default_inside_ci95_musicians": (drums["ci95_musicians"][0] <= ENGINE_DEFAULT_SWING_RATIO
                                               <= drums["ci95_musicians"][1]) if drums["ci95_musicians"] else None,
        }
    return {
        "label": ident[1] if ident else "toutes classes",
        "bpm_range": [ident[2], ident[3]] if ident else list(TEMPO_RANGE),
        "n_tracks": len(members),
        "tempo": tempo_summary(members),
        "swing": swing,
        "drums_vs_engine_default": gap,
        "resolution": resolution_block(members),
    }


# --------------------------------------------------------------------------------------
# Régression robuste de la médiane de swing sur le tempo

HUBER_C = 1.345
IRLS_ITERATIONS = 20
SCALE_FLOOR = 1e-4
HINGE_GRID = tuple(float(h) for h in range(110, 260, 10))
MIN_POINTS_EACH_SIDE_OF_HINGE = 5
CV_FOLDS = 10
MODELS = ("constant", "linear", "log", "plateau_linear")
"""Du plus simple au plus riche : à validation croisée égale (à `MODEL_TOLERANCE` près) on garde le premier."""
MODEL_TOLERANCE = 0.0
"""Tolérance relative sur l'écart de validation croisée : 0 = on retient le meilleur (à égalité, le plus simple).
Les écarts entre modèles sont de l'ordre de 1 % : la forme retenue n'est pas une preuve, la courbe est comparée aux tranches."""
MODEL_TIE = 1e-4
"""Égalité numérique : un écart de validation croisée inférieur à la précision des sorties (10⁻⁴ de rapport de swing) ne départage pas deux modèles."""
MIN_CURVE_TRACKS = 30
MIN_CURVE_SPREAD_BPM = 50.0
CURVE_GRID = tuple(float(t) for t in range(60, 331, 10))
SUPPORT_HALF_WINDOW = 15.0
MIN_SUPPORT_TRACKS = 20
BIN_WIDTH = 20.0
MIN_BIN_TRACKS = 10
EXPLOITABLE_MIN_CV_SKILL = 0.05


def _phi(model: str, t: np.ndarray, h: np.ndarray | float | None = None) -> np.ndarray:
    if model == "linear":
        return t
    if model == "log":
        return np.log(t)
    if model == "plateau_linear":
        return np.maximum(t - h, 0.0)
    return np.zeros_like(t)


def _wls(phi: np.ndarray, y: np.ndarray, w: np.ndarray, with_slope: bool) -> tuple[np.ndarray, np.ndarray]:
    """Droite `a + b·phi` aux moindres carrés pondérés, une droite par ligne de `w` (B, n)."""
    sw = w.sum(axis=1)
    sy = w @ y
    if not with_slope:
        return sy / sw, np.zeros_like(sw)
    sx = w @ phi
    sxx = w @ (phi * phi)
    sxy = w @ (phi * y)
    den = sw * sxx - sx * sx
    ok = den > 1e-12 * np.maximum(sw * sxx, 1e-300)
    b = np.where(ok, (sw * sxy - sx * sy) / np.where(ok, den, 1.0), 0.0)
    return (sy - b * sx) / sw, b


def _irls(phi: np.ndarray, y: np.ndarray, weights: np.ndarray, scale: float, with_slope: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """M-estimateur de Huber (échelle fixée) par moindres carrés repondérés itérés, une droite par
    ligne de `weights`. `phi` est centrée en interne (stabilité). Renvoie `(a, b, perte)`."""
    centre = float(phi.mean())
    pc = phi - centre
    a, b = _wls(pc, y, weights, with_slope)
    for _ in range(IRLS_ITERATIONS):
        u = np.abs(y - a[:, None] - b[:, None] * pc) / (HUBER_C * scale)
        a, b = _wls(pc, y, weights * np.where(u <= 1.0, 1.0, 1.0 / np.maximum(u, 1e-12)), with_slope)
    u = np.abs(y - a[:, None] - b[:, None] * pc) / scale
    rho = np.where(u <= HUBER_C, 0.5 * u * u, HUBER_C * u - 0.5 * HUBER_C ** 2)
    return a - b * centre, b, (weights * rho).sum(axis=1)


def hinge_candidates(x: np.ndarray) -> list[float]:
    """Charnières testées : au moins `MIN_POINTS_EACH_SIDE_OF_HINGE` pistes de chaque côté."""
    return [h for h in HINGE_GRID
            if (x > h).sum() >= MIN_POINTS_EACH_SIDE_OF_HINGE and (x <= h).sum() >= MIN_POINTS_EACH_SIDE_OF_HINGE]


def fit_model(model: str, x: np.ndarray, y: np.ndarray, weights: np.ndarray, scale: float):
    """Ajuste `model` pour chaque ligne de `weights` (B, n) : `(a, b, h, perte)` de forme (B,), ou
    `None` si le modèle est inapplicable (plateau sans charnière admissible). `weights` : poids de
    rééchantillonnage (comptes) ou 0/1 (validation croisée)."""
    rows = weights.shape[0]
    if model == "constant":
        a, b, loss = _irls(np.zeros_like(x), y, weights, scale, False)
        return a, b, np.full(rows, np.nan), loss
    if model in ("linear", "log"):
        a, b, loss = _irls(_phi(model, x), y, weights, scale, True)
        return a, b, np.full(rows, np.nan), loss
    best = None
    for h in hinge_candidates(x):
        a, b, loss = _irls(_phi(model, x, h), y, weights, scale, True)
        if best is None:
            best = [a, b, np.full(rows, h), loss]
        else:
            better = loss < best[3]
            best = [np.where(better, a, best[0]), np.where(better, b, best[1]),
                    np.where(better, h, best[2]), np.where(better, loss, best[3])]
    return None if best is None else tuple(best)


def predict(model: str, a: np.ndarray, b: np.ndarray, h: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Valeurs de la courbe aux tempos `t` (G,) pour chaque ajustement : (B, G)."""
    return a[:, None] + b[:, None] * _phi(model, t[None, :], h[:, None])


def robust_scale(model: str, x: np.ndarray, y: np.ndarray) -> float:
    """Échelle des résidus (1,4826 × MAD) du modèle ajusté, point fixe en cinq itérations."""
    ones = np.ones((1, len(y)))
    scale = max(1.4826 * float(np.median(np.abs(y - np.median(y)))), SCALE_FLOOR)
    for _ in range(5):
        a, b, h, _ = fit_model(model, x, y, ones, scale)
        resid = y - predict(model, a, b, h, x)[0]
        scale = max(1.4826 * float(np.median(np.abs(resid - np.median(resid)))), SCALE_FLOOR)
    return scale


def cross_validate(model: str, x: np.ndarray, y: np.ndarray, codes: np.ndarray, scale: float) -> dict[str, float] | None:
    """Validation croisée par blocs de musiciens (un musicien n'est jamais à la fois dans
    l'ajustement et dans le test) : écart robuste (1,4826 × médiane des |résidus|) et RMS hors échantillon."""
    n_groups = int(codes.max()) + 1
    k = min(CV_FOLDS, n_groups)
    if k < 2:
        return None
    fold_of_point = (codes % k)
    weights = (fold_of_point[None, :] != np.arange(k)[:, None]).astype(float)
    fit = fit_model(model, x, y, weights, scale)
    if fit is None:
        return None
    pred = predict(model, fit[0], fit[1], fit[2], x)[fold_of_point, np.arange(len(y))]
    resid = y - pred
    return {"cv_mad": float(1.4826 * np.median(np.abs(resid))), "cv_rmse": float(np.sqrt(np.mean(resid ** 2)))}


def _params(model: str, a: float, b: float, h: float) -> dict[str, Any]:
    """Paramètres lisibles d'un ajustement (pente par 100 BPM ; `log` : pente par unité de ln(BPM))."""
    if model == "constant":
        return {"value": a}
    if model == "linear":
        return {"intercept_at_0_bpm": a, "slope_per_100_bpm": b * 100.0}
    if model == "log":
        return {"intercept": a, "slope_per_ln_bpm": b}
    return {"plateau_ratio": a, "hinge_bpm": h, "slope_per_100_bpm_above_hinge": b * 100.0}


FORMULAS = {
    "constant": "swing = value",
    "linear": "swing = intercept_at_0_bpm + slope_per_100_bpm/100 · tempo",
    "log": "swing = intercept + slope_per_ln_bpm · ln(tempo)",
    "plateau_linear": "swing = plateau_ratio + slope_per_100_bpm_above_hinge/100 · max(tempo − hinge_bpm, 0)",
}


def _band(model: str, fits, t: np.ndarray) -> np.ndarray:
    return predict(model, fits[0], fits[1], fits[2], t)


def _ci(samples: np.ndarray) -> list[float]:
    return [float(np.percentile(samples, CI_LEVEL[0])), float(np.percentile(samples, CI_LEVEL[1]))]


def curve_block(inst: str, values: np.ndarray, tempos: np.ndarray, groups: Sequence[str]) -> dict[str, Any]:
    """Courbe `swing_ratio(tempo)` d'un instrument : sélection du modèle, ajustement, IC95 % par bootstrap
    des pistes et des musiciens, monotonie, lissage par tranches, résidus, bornes de validité."""
    n = len(values)
    spread = float(np.ptp(tempos)) if n else 0.0
    if n < MIN_CURVE_TRACKS or spread < MIN_CURVE_SPREAD_BPM:
        return {"available": False, "n_tracks": n,
                "reason": f"{n} pistes mesurées (min {MIN_CURVE_TRACKS}) sur {spread:.0f} BPM d'étendue (min {MIN_CURVE_SPREAD_BPM:.0f})"}
    x, y = tempos, values
    uniq, codes = np.unique(np.asarray(groups), return_inverse=True)
    n_groups = len(uniq)
    t_min, t_max = float(x.min()), float(x.max())
    ones = np.ones((1, n))

    models: dict[str, Any] = {}
    fitted: dict[str, tuple] = {}
    scales: dict[str, float] = {}
    for model in MODELS:
        scale = robust_scale(model, x, y)
        fit = fit_model(model, x, y, ones, scale)
        if fit is None:
            continue
        resid = y - predict(model, fit[0], fit[1], fit[2], x)[0]
        cv = cross_validate(model, x, y, codes, scale)
        scales[model], fitted[model] = scale, fit
        models[model] = {
            "params": _params(model, float(fit[0][0]), float(fit[1][0]), float(fit[2][0])),
            "formula": FORMULAS[model],
            "in_sample_robust_std": float(1.4826 * np.median(np.abs(resid - np.median(resid)))),
            "cv_robust_std": cv["cv_mad"] if cv else None,
            "cv_rmse": cv["cv_rmse"] if cv else None,
        }
    scored = {m: v["cv_robust_std"] if v["cv_robust_std"] is not None else v["in_sample_robust_std"] for m, v in models.items()}
    best = min(scored.values())
    chosen = next(m for m in MODELS if m in scored and scored[m] <= best * (1.0 + MODEL_TOLERANCE) + MODEL_TIE)
    for m, v in models.items():
        v["cv_skill_vs_constant"] = 1.0 - scored[m] / scored["constant"]
    fit, scale = fitted[chosen], scales[chosen]
    a0, b0, h0 = fit[0], fit[1], fit[2]

    # Bootstrap : rééchantillonnage des pistes, puis des musiciens (comptes comme poids).
    rng_tracks = _rng("curve", inst, "tracks")
    w_tracks = rng_tracks.multinomial(n, np.full(n, 1.0 / n), size=BOOTSTRAP_CURVE).astype(float)
    rng_groups = _rng("curve", inst, "musicians")
    draws = rng_groups.integers(0, n_groups, size=(BOOTSTRAP_CURVE, n_groups))
    group_counts = np.stack([np.bincount(row, minlength=n_groups) for row in draws]).astype(float)
    w_groups = group_counts[:, codes]
    boot = {"tracks": fit_model(chosen, x, y, w_tracks, scale), "musicians": fit_model(chosen, x, y, w_groups, scale)}

    def value_band(t: Sequence[float]) -> tuple[np.ndarray, dict[str, list[list[float]]]]:
        arr = np.asarray(t, dtype=float)
        point = _band(chosen, fit, arr)[0]
        cis = {}
        for kind, f in boot.items():
            pred = _band(chosen, f, arr)
            cis[kind] = np.percentile(pred, CI_LEVEL, axis=0)
        return point, cis

    # Points de la courbe : tempos ronds, jamais hors du tempo observé.
    support = {t: int(np.sum(np.abs(x - t) <= SUPPORT_HALF_WINDOW)) for t in CURVE_GRID}
    inside = [t for t in CURVE_GRID if t_min <= t <= t_max]
    point_v, point_ci = value_band(inside) if inside else (np.array([]), {"tracks": np.zeros((2, 0)), "musicians": np.zeros((2, 0))})
    by_t = {t: i for i, t in enumerate(inside)}
    points = []
    for t in CURVE_GRID:
        if t not in by_t:
            points.append({"tempo": t, "status": "hors_plage", "swing_ratio": None, "ci95_tracks": None,
                           "ci95_musicians": None, "long_short": None, "support_tracks_within_window": support[t],
                           "clamp_to_bpm": round(t_min if t < t_min else t_max, 1)})
            continue
        i = by_t[t]
        v = float(point_v[i])
        points.append({
            "tempo": t,
            "status": "ok" if support[t] >= MIN_SUPPORT_TRACKS else "mince",
            "swing_ratio": v,
            "ci95_tracks": [float(point_ci["tracks"][0, i]), float(point_ci["tracks"][1, i])],
            "ci95_musicians": [float(point_ci["musicians"][0, i]), float(point_ci["musicians"][1, i])],
            "long_short": long_short(v) if v < 1.0 else None,
            "support_tracks_within_window": support[t],
            "clamp_to_bpm": None,
        })
    bounds_t = [t_min, t_max]
    bv, bci = value_band(bounds_t)
    bounds = {"tempo_min_bpm": t_min, "tempo_max_bpm": t_max,
              "swing_ratio_at_min": float(bv[0]), "swing_ratio_at_max": float(bv[1]),
              "ci95_musicians_at_min": [float(bci["musicians"][0, 0]), float(bci["musicians"][1, 0])],
              "ci95_musicians_at_max": [float(bci["musicians"][0, 1]), float(bci["musicians"][1, 1])],
              "rule": "aucune valeur hors de [tempo_min_bpm, tempo_max_bpm] (tempos observés des pistes mesurées) ; "
                      "au-delà, A6 doit borner le tempo ou choisir un repli explicite",
              "support_window_bpm": SUPPORT_HALF_WINDOW, "min_support_tracks_for_ok": MIN_SUPPORT_TRACKS}

    # Pente et écart 120 → 240 BPM (valable pour toute forme de courbe).
    slope_key = {"linear": ("slope_per_100_bpm", 100.0), "log": ("slope_per_ln_bpm", 1.0),
                 "plateau_linear": ("slope_per_100_bpm_above_hinge", 100.0)}.get(chosen)
    slope = None
    if slope_key:
        slope = {"name": slope_key[0], "value": float(b0[0]) * slope_key[1],
                 "ci95_tracks": _ci(boot["tracks"][1] * slope_key[1]),
                 "ci95_musicians": _ci(boot["musicians"][1] * slope_key[1])}
    hinge = None
    if chosen == "plateau_linear":
        hinge = {"value": float(h0[0]), "ci95_tracks": _ci(boot["tracks"][2]), "ci95_musicians": _ci(boot["musicians"][2]),
                 "note": "charnière cherchée sur la grille `hinge_grid_bpm` à chaque rééchantillon : l'IC inclut son incertitude"}
    delta = None
    if t_min <= 120.0 and t_max >= 240.0:
        pair = np.array([120.0, 240.0])
        dp = _band(chosen, fit, pair)[0]
        d_t = np.diff(_band(chosen, boot["tracks"], pair), axis=1)[:, 0]
        d_m = np.diff(_band(chosen, boot["musicians"], pair), axis=1)[:, 0]
        delta = {"value": float(dp[1] - dp[0]), "ci95_tracks": _ci(d_t), "ci95_musicians": _ci(d_m),
                 "excludes_zero_musicians": bool(_ci(d_m)[1] < 0 or _ci(d_m)[0] > 0)}
    mono_grid = np.arange(math.ceil(t_min / 10.0) * 10.0, t_max, 10.0)
    monotone: dict[str, Any] = {"grid_bpm": [float(mono_grid[0]), float(mono_grid[-1])] if len(mono_grid) else None}
    if len(mono_grid) >= 2:
        monotone["point_non_increasing"] = bool((np.diff(_band(chosen, fit, mono_grid)[0]) <= 1e-9).all())
        for kind, f in boot.items():
            monotone[f"share_resamples_non_increasing_{kind}"] = float((np.diff(_band(chosen, f, mono_grid), axis=1) <= 1e-9).all(axis=1).mean())

    # Résidus et dispersion entre pistes à tempo égal.
    fitted_x = _band(chosen, fit, x)[0]
    resid = y - fitted_x
    class_of = np.array([tempo_class(t) for t in x])
    residual = {
        "robust_std": float(1.4826 * np.median(np.abs(resid - np.median(resid)))),
        "std": float(np.std(resid, ddof=1)),
        "p10": float(np.percentile(resid, 10)), "p90": float(np.percentile(resid, 90)),
        "by_class": {c: {"n": int((class_of == c).sum()),
                         "robust_std": float(1.4826 * np.median(np.abs(resid[class_of == c] - np.median(resid[class_of == c]))))
                         if (class_of == c).sum() > 1 else None} for c in CLASS_IDS},
        "note": "écart entre pistes au même tempo : une piste isolée s'écarte de la courbe de ± ce résidu",
    }

    # Lissage par tranches de 20 BPM : médiane des pistes de la tranche contre la courbe à son tempo médian.
    smoother = []
    lo = math.floor(t_min / BIN_WIDTH) * BIN_WIDTH
    edges = np.arange(lo, t_max + 2 * BIN_WIDTH, BIN_WIDTH)
    for e_lo, e_hi in zip(edges[:-1], edges[1:]):
        sel = (x >= e_lo) & (x < e_hi)
        if not sel.any():
            continue
        v_bin = y[sel]
        t_mid = float(np.median(x[sel]))
        curve_here = float(_band(chosen, fit, np.array([t_mid]))[0, 0])
        ci_bin = bootstrap_ci_clustered(v_bin, np.asarray(groups)[sel], _rng("bin", inst, e_lo), BOOTSTRAP_CURVE)
        smoother.append({
            "bpm_range": [float(e_lo), float(e_hi)], "n_tracks": int(sel.sum()), "median_tempo_bpm": t_mid,
            "median": float(np.median(v_bin)), "p25": float(np.percentile(v_bin, 25)), "p75": float(np.percentile(v_bin, 75)),
            "curve_at_median_tempo": curve_here, "gap_median_minus_curve": float(np.median(v_bin)) - curve_here,
            "median_ci95_musicians": ci_bin,
            "curve_inside_ci95_musicians": bool(ci_bin[0] <= curve_here <= ci_bin[1]) if ci_bin else None,
        })
    solid = [b for b in smoother if b["n_tracks"] >= MIN_BIN_TRACKS]
    rises = [solid[i + 1]["median"] - solid[i]["median"] for i in range(len(solid) - 1)]
    smoothing = {
        "bin_width_bpm": BIN_WIDTH, "min_tracks_for_bin": MIN_BIN_TRACKS, "bins": smoother,
        "n_rises_between_solid_bins": int(sum(r > 0 for r in rises)),
        "max_rise": float(max([r for r in rises if r > 0], default=0.0)),
        "max_abs_gap_solid_bins": float(max((abs(b["gap_median_minus_curve"]) for b in solid), default=0.0)),
        "n_solid_bins_curve_outside_ci95_musicians": int(sum(b["curve_inside_ci95_musicians"] is False for b in solid)),
    }
    rho = spearmanr(x, y).statistic
    exploitable = bool(chosen != "constant" and delta is not None and delta["excludes_zero_musicians"]
                       and models[chosen]["cv_skill_vs_constant"] >= EXPLOITABLE_MIN_CV_SKILL)
    return {
        "available": True,
        "n_tracks": n, "n_musicians": n_groups,
        "spearman_tempo_vs_swing": float(rho),
        "chosen_model": chosen,
        "model_choice_rule": f"validation croisée par musicien ({min(CV_FOLDS, n_groups)} blocs) : modèle de plus faible écart "
                             f"robuste (tolérance {MODEL_TOLERANCE:.0%}, à égalité le plus simple parmi {', '.join(MODELS)})",
        "models": models,
        "fit": {"model": chosen, "formula": FORMULAS[chosen], "params": models[chosen]["params"], "slope": slope, "hinge": hinge},
        "delta_120_to_240_bpm": delta,
        "exploitable": exploitable,
        "exploitable_rule": f"modèle ≠ constant, IC95 % (musiciens) de l'écart 120→240 BPM hors de 0 et gain de validation croisée "
                            f"≥ {EXPLOITABLE_MIN_CV_SKILL:.0%} sur la constante",
        "monotone": monotone,
        "residual": residual,
        "points": points,
        "bounds": bounds,
        "bin_smoother": smoothing,
        "bootstrap": {"n_resamples": BOOTSTRAP_CURVE, "seed": SEED, "method": "pistes rééchantillonnées / musiciens rééchantillonnés "
                      "(comptes comme poids), IC = centiles 2,5 et 97,5 des courbes ajustées",
                      "tempo_grid_bpm": list(CURVE_GRID)},
    }


def curve_section(classes: Mapping[str, Sequence[TrackStats]]) -> dict[str, Any]:
    stats = classes["all"]
    out = {}
    for inst in INSTRUMENTS:
        values, tempos, groups = measured(stats, inst)
        out[inst] = curve_block(inst, values, tempos, groups)
    return out


# --------------------------------------------------------------------------------------
# Micro-timing par classe


MICRO_CLUSTER_INSTRUMENT = {"abs_drums": "drums", "abs_bass": "bass", "abs_piano": "piano",
                            "rel_bass_drums": "drums", "rel_piano_drums": "drums", "rel_bass_piano": "bass"}
"""Musicien dont dépend un écart (rééchantillonné en bloc) : la batterie pour un écart à la batterie, la basse pour basse−piano."""


def track_values(stats: Sequence[TrackStats], key: str, metres: Sequence[int] | None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Valeur par piste de l'écart `key` aux temps `metres` : moyenne tronquée à 10 % de la piste (pas, ms) et
    musicien de référence. La médiane par piste tombe sur le pas de 10 ms des CSV (IC dégénérés), la moyenne
    tronquée est continue."""
    steps, ms, groups = [], [], []
    for s in stats:
        d_steps, d_ms, metre = s.placements[key]
        if metres is not None:
            keep = np.isin(metre, metres)
            d_steps, d_ms = d_steps[keep], d_ms[keep]
        if len(d_steps):
            steps.append(float(trim_mean(d_steps, TRIM)))
            ms.append(float(trim_mean(d_ms, TRIM)))
            groups.append(musician(s.track, MICRO_CLUSTER_INSTRUMENT[key]))
    return np.asarray(steps), np.asarray(ms), groups


def _mean_ci(values: np.ndarray, groups: Sequence[str], label: str, key: str, group: str, unit: str, clustered: bool) -> dict[str, Any]:
    """Moyenne tronquée (entre pistes) et IC95 % par piste (et par musicien si `clustered`)."""
    out: dict[str, Any] = {
        "value": float(trim_mean(values, TRIM)) if len(values) else None,
        "ci95_tracks": bootstrap_ci(values, _rng("micro", label, key, group, unit, "tracks"), BOOTSTRAP_CURVE, "trimmed_mean"),
    }
    if clustered:
        out["ci95_musicians"] = bootstrap_ci_clustered(values, groups, _rng("micro", label, key, group, unit, "musicians"),
                                                       BOOTSTRAP_CURVE, "trimmed_mean")
    return out


def asymmetry_block(stats: Sequence[TrackStats], key: str, label: str) -> dict[str, Any]:
    """Écart des temps 2-4 moins temps 1-3, par piste (pistes avec ≥ `MIN_ASYMMETRY_PAIRS` paires de
    chaque côté) : mesure appariée, plus fine que la différence des moyennes poolées. Moyenne tronquée
    entre pistes et IC95 % par piste."""
    d_steps, d_ms, groups = [], [], []
    for s in stats:
        steps, ms, metre = s.placements[key]
        odd, even = np.isin(metre, (1, 3)), np.isin(metre, (2, 4))
        if odd.sum() >= MIN_ASYMMETRY_PAIRS and even.sum() >= MIN_ASYMMETRY_PAIRS:
            d_steps.append(float(trim_mean(steps[even], TRIM) - trim_mean(steps[odd], TRIM)))
            d_ms.append(float(trim_mean(ms[even], TRIM) - trim_mean(ms[odd], TRIM)))
            groups.append(musician(s.track, MICRO_CLUSTER_INSTRUMENT[key]))
    steps_a, ms_a = np.asarray(d_steps), np.asarray(d_ms)
    return {"n_tracks": len(d_ms),
            "trimmed_mean_ms": _mean_ci(ms_a, groups, label, key, "asym", "ms", True),
            "trimmed_mean_steps": _mean_ci(steps_a, groups, label, key, "asym", "steps", True)}


def micro_block(stats: Sequence[TrackStats], key: str, group: str, label: str) -> dict[str, Any]:
    """Écart `key` d'un jeu de pistes aux temps du groupe : bloc `placement_block` de E7 (centiles poolés
    et par piste, moyenne tronquée) + moyenne tronquée entre pistes (de la moyenne tronquée de chaque piste)
    avec IC95 % par piste, et par musicien pour le groupe `all`."""
    block = placement_block(stats, key, METRE_GROUPS[group], per_track=True)
    steps, ms, groups = track_values(stats, key, METRE_GROUPS[group])
    clustered = group == "all"
    block["per_track_trimmed_mean_steps"] = _mean_ci(steps, groups, label, key, group, "steps", clustered)
    block["per_track_trimmed_mean_ms"] = _mean_ci(ms, groups, label, key, group, "ms", clustered)
    return block


def pair_reliability(stats: Sequence[TrackStats], key: str) -> dict[str, Any]:
    """Verdict d'un écart relatif : pistes ayant au moins `MIN_JITTER_PAIRS` paires ; musiciens distincts
    (le plus petit des deux rôles) ; part du musicien le plus présent (le plus grand des deux rôles)."""
    a, b = PAIR_INSTRUMENTS[key]
    usable = [s for s in stats if len(s.placements[key][0]) >= MIN_JITTER_PAIRS]
    names = {inst: [musician(s.track, inst) for s in usable] for inst in (a, b)}
    n_musicians = min(len(set(names[a])), len(set(names[b]))) if usable else 0
    top = max(_top_share(names[a]) or 0.0, _top_share(names[b]) or 0.0) if usable else None
    return verdict(len(usable), n_musicians, top)


def micro_section(classes: Mapping[str, Sequence[TrackStats]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, members in classes.items():
        entry: dict[str, Any] = {"n_tracks": len(members), "absolute_vs_beat": {}, "relative": {}, "jitter_per_track": {},
                                 "beats_2_4_minus_1_3": {}, "resolution": resolution_block(members)}
        for key in ABSOLUTE_KEYS:
            entry["absolute_vs_beat"][key[len("abs_"):]] = {g: micro_block(members, key, g, label) for g in MICRO_GROUPS}
        for key in RELATIVE_KEYS:
            name = "_minus_".join(PAIR_INSTRUMENTS[key])
            entry["relative"][name] = {g: micro_block(members, key, g, label) for g in MICRO_GROUPS}
            entry["jitter_per_track"][name] = jitter_block(members, key)
            entry["beats_2_4_minus_1_3"][name] = asymmetry_block(members, key, label)
        out[label] = entry
    return {
        "convention": "écart = attaque de a − attaque de b au même temps ; négatif = a en avance ; pas = ¼ de temps au tempo "
                      "de chaque piste ; absolus = attaque − temps détecté (détection automatique : peu fiable, "
                      "seuls les relatifs sont à reprendre)",
        "csv_resolution_ms": CSV_RESOLUTION_MS,
        "groups": {g: list(METRE_GROUPS[g]) if METRE_GROUPS[g] else "tous les temps" for g in MICRO_GROUPS},
        "min_jitter_pairs_per_track": MIN_JITTER_PAIRS,
        "classes": out,
    }


# --------------------------------------------------------------------------------------
# Fiabilité, limites, table pour A6

CAVEATS = [
    "Seules les annotations temporelles (beats.csv, *_onsets.csv, metadata.json) sont lues ; chaque piste est un enregistrement "
    "sous droits dont ni l'audio ni piano_midi.mid ne sont lus. Aucune phrase de solo n'est copiée.",
    "Temps et attaques sont détectés AUTOMATIQUEMENT sur des pistes séparées par séparation de sources (Cheston et al., "
    "TISMIR 2024) : le swing de la batterie reflète surtout le ride ; les écarts absolus au temps dépendent de la détection "
    "des temps et ne sont pas à reprendre, seuls les écarts relatifs entre instruments le sont.",
    "Résolution des CSV : 10 ms. Un rapport de swing individuel est quantifié par 10 ms / durée du temps (0,017 à 100 BPM, "
    "0,033 à 200 BPM, 0,05 à 300 BPM ; voir `resolution`) ; les médianes sur des centaines d'attaques puis sur des dizaines de pistes la dépassent, "
    "pas la dispersion d'une piste isolée.",
    "Musiciens répétés : un même batteur, bassiste ou pianiste signe plusieurs pistes ; les IC « par musicien » rééchantillonnent "
    "les musiciens entiers et sont les seuls à lire comme honnêtes ; les IC « par piste » les sous-estiment.",
    "Le swing du piano mêle comping et solo ; celui de la basse porte sur peu de contretemps (marche en noires) : les pistes "
    "mesurées sont moins nombreuses et la courbe est indicative.",
    "Plage observée : tempos de 102 à 299 BPM seulement (toute l'archive) : rien en dessous de 100 ni au-dessus de 300 BPM, "
    "malgré la plage 60–330 BPM du filtre ; la classe « < 120 » est en fait 100–120 BPM et « ≥ 240 » 240–300 BPM.",
    "Tempo de `metadata.json` supposé constant sur la piste (tempo moyen de l'extrait) ; les extraits ne durent que quelques minutes.",
    "Corpus de pianistes, batteurs et bassistes enregistrés (surtout 1950–2010, trios piano) : pas une mesure du « swing en général ».",
]


def dependence_summary(classes: Mapping[str, Any]) -> dict[str, Any]:
    """Effet de la dépendance entre pistes d'un même musicien : largeur de l'IC par musicien / par piste."""
    rows = []
    for label, block in classes.items():
        for inst in INSTRUMENTS:
            s = block["swing"][inst]
            ratio = s["design_effect"]["ci_width_ratio_musicians_over_tracks"]
            if ratio is not None:
                rows.append({"class": label, "instrument": inst, "ci_width_ratio": ratio,
                             "n_tracks_measured": s["n_tracks_measured"], "n_musicians_measured": s["n_musicians_measured"],
                             "n_effective_tracks": s["design_effect"]["n_effective_tracks"],
                             "top_musician_share": s["top_musician_share"]})
    worst = max((r for r in rows if r["class"] != "all"), key=lambda r: r["ci_width_ratio"], default=None)
    return {"rows": rows, "most_affected_tempo_class": worst,
            "reading": "ci_width_ratio > 1 : l'IC par piste sous-estime l'incertitude ; n_effective_tracks = nombre de pistes "
                       "indépendantes qui donneraient la même largeur d'IC"}


def reliability_section(classes: Mapping[str, Any], stats_by_class: Mapping[str, Sequence[TrackStats]]) -> dict[str, Any]:
    out: dict[str, Any] = {"thresholds": {"assez": VERDICT_ASSEZ, "juste": VERDICT_JUSTE}, "rules": VERDICT_RULES,
                           "swing": {}, "micro_timing": {}, "classes_below_min_tracks": []}
    for label, block in classes.items():
        out["swing"][label] = {}
        for inst in INSTRUMENTS:
            s = block["swing"][inst]
            out["swing"][label][inst] = verdict(s["n_tracks_measured"], s["n_musicians_measured"], s["top_musician_share"],
                                                _halfwidth(s["ci95_musicians"]))
        out["micro_timing"][label] = {"_minus_".join(PAIR_INSTRUMENTS[k]): pair_reliability(stats_by_class[label], k)
                                      for k in RELATIVE_KEYS}
        if label != "all" and block["swing"]["drums"]["n_tracks_measured"] < MIN_TRACKS_PER_CLASS:
            out["classes_below_min_tracks"].append(label)
    return out


def a6_table(classes: Mapping[str, Any], curves: Mapping[str, Any], reliability: Mapping[str, Any]) -> dict[str, Any]:
    """Table à reprendre par A6 : valeur centrale, IC, effectifs et verdict par classe ; points de la courbe."""
    rows = []
    for ident, label, lo, hi in TEMPO_CLASSES:
        block = classes[ident]
        row: dict[str, Any] = {"id": ident, "label": label, "bpm_range": [lo, hi],
                               "median_tempo_bpm": block["tempo"]["median"], "observed_tempo_bpm": [block["tempo"]["min"], block["tempo"]["max"]]}
        for inst in INSTRUMENTS:
            s = block["swing"][inst]
            row[inst] = {"swing_ratio": s["median"], "long_short": s["median_long_short"],
                         "ci95_musicians": s["ci95_musicians"], "ci95_tracks": s["ci95_tracks"],
                         "p10": s["ratio"]["p10"], "p90": s["ratio"]["p90"],
                         "n_tracks": s["n_tracks_measured"], "n_musicians": s["n_musicians_measured"],
                         "verdict": reliability["swing"][ident][inst]["verdict"]}
        drums_curve = curves["drums"]
        if drums_curve.get("available") and block["tempo"]["median"] is not None:
            tm = block["tempo"]["median"]
            pt = next((p for p in drums_curve["points"] if p["tempo"] == round(tm / 10) * 10), None)
            row["drums"]["curve_value_at_class_median_tempo_round10"] = pt["swing_ratio"] if pt else None
        row["drums"]["gap_vs_engine_default_0_71"] = (row["drums"]["swing_ratio"] - ENGINE_DEFAULT_SWING_RATIO
                                                      if row["drums"]["swing_ratio"] is not None else None)
        rows.append(row)
    table: dict[str, Any] = {
        "units": "rapport de swing = fraction de l'intervalle entre deux temps où tombe la croche de contretemps "
                 "(0,5 = droit ; 0,667 = triolet ; long/court = r / (1 − r))",
        "engine_default_swing_ratio": ENGINE_DEFAULT_SWING_RATIO,
        "classes": rows,
        "curve": {},
    }
    for inst in INSTRUMENTS:
        c = curves[inst]
        table["curve"][inst] = None if not c.get("available") else {
            "chosen_model": c["chosen_model"], "formula": c["fit"]["formula"], "params": c["fit"]["params"],
            "exploitable": c["exploitable"], "valid_range_bpm": [c["bounds"]["tempo_min_bpm"], c["bounds"]["tempo_max_bpm"]],
            "residual_robust_std": c["residual"]["robust_std"],
            "points": [{"tempo": p["tempo"], "swing_ratio": p["swing_ratio"], "ci95_musicians": p["ci95_musicians"],
                        "status": p["status"]} for p in c["points"] if p["swing_ratio"] is not None],
        }
    return table


# --------------------------------------------------------------------------------------
# Sortie


def build_measures(archive: zipfile.ZipFile) -> dict[str, Any]:
    """JSON complet de `references/jtd-swing-tempo/measures-swing-tempo.json`."""
    stats, counts = read_stats(archive)
    groups = by_class(stats)
    classes = {label: class_block(label, members) for label, members in groups.items()}
    curves = curve_section(groups)
    reliability = reliability_section(classes, groups)
    return {
        "command": COMMAND,
        "provenance": {
            "source": SOURCE_NAME,
            "version": SOURCE_VERSION,
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "md5": SOURCE_MD5,
            "licence": SOURCE_LICENCE,
            "attribution": ATTRIBUTION,
            "subset": f"time_signature == 4 ; tempo {TEMPO_RANGE[0]:.0f}–{TEMPO_RANGE[1]:.0f} BPM ; au moins {MIN_PAIRED_SHARE:.0%} "
                      "des temps avec basse ET batterie appariées (filtre E7 `timing.py`, sans les tranches de 100 à 330 BPM)",
            "counts": {
                "n_tracks_archive": counts["total"],
                "n_tracks_time_signature_4": counts["time_signature_4"],
                "n_tracks_tempo_in_range": counts["tempo_in_range"],
                "n_tracks_retained": counts["retained"],
                "n_tracks_dropped_paired_share": counts["tempo_in_range"] - counts["paired_ok"],
                "n_beats": int(sum(len(s.track.beats) for s in stats)),
                "tempo_min_archive_bpm": counts["tempo_min_archive"],
                "tempo_max_archive_bpm": counts["tempo_max_archive"],
                "tracks_per_class": {label: len(groups[label]) for label in CLASS_IDS},
            },
        },
        "parameters": {
            "tempo_classes": [{"id": i, "label": lab, "bpm_lo_included": lo, "bpm_hi_excluded": hi} for i, lab, lo, hi in TEMPO_CLASSES],
            "min_tracks_per_class": MIN_TRACKS_PER_CLASS,
            "min_swing_observations_per_track": MIN_SWING_OBSERVATIONS,
            "swing_window": list(SWING_WINDOW),
            "engine_default_swing_ratio": ENGINE_DEFAULT_SWING_RATIO,
            "bootstrap": {"seed": SEED, "n_resamples_medians": BOOTSTRAP_MEDIAN, "n_resamples_curve": BOOTSTRAP_CURVE,
                          "level": "IC95 % : centiles 2,5 et 97,5"},
            "regression": {"estimator": "Huber (échelle MAD fixée, moindres carrés repondérés itérés)", "huber_c": HUBER_C,
                           "models": list(MODELS), "hinge_grid_bpm": list(HINGE_GRID), "cv_folds": CV_FOLDS},
        },
        "classes": classes,
        "curve": curves,
        "micro_timing": micro_section(groups),
        "limits": {
            "tempo_coverage": {"observed_bpm": [counts["tempo_min_archive"], counts["tempo_max_archive"]],
                               "note": "aucune piste sous 100 ni au-dessus de 300 BPM dans l'archive : la classe « < 120 » "
                                       "est 100–120 BPM, « ≥ 240 » est 240–300 BPM ; pas d'extrapolation"},
            "dependence": dependence_summary(classes),
            "caveats": CAVEATS,
        },
        "reliability": reliability,
        "a6_table": a6_table(classes, curves, reliability),
    }


def summary(data: Mapping[str, Any]) -> str:
    """Résumé texte du JSON de mesures."""
    prov = data["provenance"]
    c = prov["counts"]
    out = [f"{prov['source']} {prov['version']} — {prov['licence']}",
           f"pistes : archive {c['n_tracks_archive']}, 4 temps {c['n_tracks_time_signature_4']}, tempo ok {c['n_tracks_tempo_in_range']}, "
           f"retenues {c['n_tracks_retained']} (écartées : appariement {c['n_tracks_dropped_paired_share']}) ; "
           f"tempos {c['tempo_min_archive_bpm']:.1f}–{c['tempo_max_archive_bpm']:.1f} BPM ; par classe {c['tracks_per_class']}",
           "\nSwing par classe (n pistes mesurées / musiciens ; médiane [IC95 % par musicien] ; verdict)"]
    for inst in INSTRUMENTS:
        out.append(f"  {inst}")
        for label, block in data["classes"].items():
            s = block["swing"][inst]
            if s["median"] is None:
                continue
            ci = s["ci95_musicians"]
            rel = data["reliability"]["swing"][label][inst]["verdict"]
            out.append(f"    {label:>8}  {s['n_tracks_measured']:>4}/{s['n_musicians_measured']:<3} {s['median']:.3f} "
                       f"[{ci[0]:.3f} ; {ci[1]:.3f}]  long/court {s['median_long_short']:.2f}  {rel}")
    for inst in INSTRUMENTS:
        cv = data["curve"][inst]
        if not cv.get("available"):
            out.append(f"\nCourbe {inst} : indisponible ({cv['reason']})")
            continue
        d = cv["delta_120_to_240_bpm"]
        out.append(f"\nCourbe {inst} : modèle {cv['chosen_model']} {cv['fit']['params']} ; exploitable {cv['exploitable']} ; "
                   f"résidu {cv['residual']['robust_std']:.3f} ; Δ120→240 {d['value']:+.3f} [{d['ci95_musicians'][0]:+.3f} ; {d['ci95_musicians'][1]:+.3f}]")
        if inst == "drums":
            for p in cv["points"]:
                if p["swing_ratio"] is not None:
                    out.append(f"  {p['tempo']:>5.0f} BPM  {p['swing_ratio']:.3f} [{p['ci95_musicians'][0]:.3f} ; {p['ci95_musicians'][1]:.3f}]  {p['status']}")
    return "\n".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--measures", action="store_true", help=f"écrit <out-dir>/{OUTPUT_NAME}")
    parser.add_argument("--summary", action="store_true", help="affiche un résumé lisible du JSON de sortie")
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DIR, help="dossier de sortie (défaut : references/jtd-swing-tempo)")
    args = parser.parse_args(argv)
    output = args.out_dir / OUTPUT_NAME
    try:
        if args.measures or not args.summary:
            archive = timing.open_archive(ARCHIVE)
            write_json(output, build_measures(archive))
            print(f"mesures → {output}")
        if args.summary:
            if not output.is_file():
                print(f"{output} absent : lancer --measures", file=sys.stderr)
                return 1
            print(summary(json.loads(output.read_text(encoding="utf-8"))))
    except (ValueError, FileNotFoundError, RuntimeError, DigestError) as err:
        print(f"erreur : {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
