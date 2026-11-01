"""Swing et placement basse / batterie / piano : Jazz Trio Database (JTD) v0.2.

Source : Cheston, Schlichting, Cross, Harrison, « Jazz Trio Database: Automated Annotation of
Jazz Piano Trio Recordings Processed Using Audio Source Separation », TISMIR 2024,
DOI 10.5334/tismir.186 ; annotations sous licence MIT
(https://github.com/HuwCheston/Jazz-Trio-Database). L'audio et `piano_midi.mid` (transcription
automatique d'improvisations sous droits) ne sont JAMAIS lus : seuls `metadata.json`,
`beats.csv`, `*_onsets.csv` entrent dans les mesures, lus directement dans l'archive ZIP (rien
n'est extrait dans le dépôt).

Fichiers lus par piste (`jazz-trio-database-v02/<fname>/`) :
- `beats.csv` : `beats` (instant du temps, s), `piano` / `bass` / `drums` (attaque appariée au
  temps, vide si manquante), `metre_auto` (1 = premier temps) ;
- `bass_onsets.csv`, `drums_onsets.csv`, `piano_onsets.csv` : instants d'attaque, sans en-tête ;
- `metadata.json` : tempo (BPM, à la noire), `time_signature`, musiciens, année, notes de
  qualité. Il contient `NaN` (non standard) : lu avec le `json` tolérant de Python.

Filtre : `time_signature == 4`, tempo entre 60 et 330 BPM, et part de temps où basse ET batterie
sont appariées d'au moins 60 %. Tranches de tempo : 25 BPM de 100 à 275, puis 275–330 (au moins
30 pistes par tranche, vérifié et déclaré dans le JSON).

Limites à garder en tête (reprises dans le JSON) :
- les CSV sont arrondis au centième de seconde : résolution 10 ms (¼ de pas environ à 200 BPM) ;
  les médianes sur des milliers d'attaques la dépassent, pas les écarts-types d'une piste courte ;
- les écarts ABSOLUS à un temps dépendent de la détection des temps de la piste ; les écarts
  RELATIFS entre instruments (basse − batterie, piano − batterie) sont la mesure fiable ;
- le piano mêle comping et solo : son rythme est indicatif ;
- les agrégats « poolés » comptent chaque attaque / mesure une fois : les longues pistes pèsent plus ;
  les distributions « par piste » donnent un poids égal à chaque piste.

Usage : `python -m harmonium_lab.backing.timing [--fetch] [--manifest] [--measures] [--summary]`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import trim_mean

from . import drums as drums_module
from .corpus_cache import (
    REFERENCES,
    ROOT,
    DigestError,
    describe,
    fetch,
    open_verified,
    percentiles,
    write_json,
    write_jsonl,
    write_version,
)

SOURCE_NAME = "Jazz Trio Database"
SOURCE_VERSION = "v0.2 (jazz-trio-database-v02.zip)"
SOURCE_URL = "https://github.com/HuwCheston/Jazz-Trio-Database/releases/download/v02-zenodo/jazz-trio-database-v02.zip"
SOURCE_SHA256 = "42c3df0700e0cd6e73231b9ed111283600750305e2e9cf451f80664d1ec90025"
SOURCE_MD5 = "43f543fb286c6222ae1f52bcf7561f37"
SOURCE_LICENCE = "MIT"
ATTRIBUTION = (
    "Cheston, Schlichting, Cross, Harrison, Jazz Trio Database: Automated Annotation of Jazz Piano Trio "
    "Recordings Processed Using Audio Source Separation, TISMIR 2024, DOI 10.5334/tismir.186 ; "
    "annotations © les auteurs, licence MIT (https://github.com/HuwCheston/Jazz-Trio-Database)"
)
ARCHIVE = ROOT / "corpus" / "jtd" / "raw" / "jazz-trio-database-v02.zip"
MANIFEST = ROOT / "corpus" / "jtd" / "manifest.jsonl"
VERSION_FILE = ROOT / "corpus" / "jtd" / "VERSION"
OUTPUT = REFERENCES / "measures-timing.json"
COMMAND = "python -m harmonium_lab.backing.timing --measures"
PREFIX = "jazz-trio-database-v02/"

TEMPO_RANGE = (60.0, 330.0)
MIN_PAIRED_SHARE = 0.6
TEMPO_BIN_EDGES = (100, 125, 150, 175, 200, 225, 250, 275, 330)
MIN_TRACKS_PER_BIN = 30
SWING_WINDOW = (0.45, 0.85)
INTERVAL_TOLERANCE = 0.3
MIN_SWING_OBSERVATIONS = 20
MIN_JITTER_PAIRS = 30
OFF_BEAT_THRESHOLD = 0.2
MAX_ENGINE_JITTER_STEPS = 0.1
STEPS_PER_BEAT = 4
RATING_FIELDS = ("rating_bass_audio", "rating_bass_detection", "rating_drums_audio", "rating_drums_detection",
                 "rating_mix", "rating_piano_audio", "rating_piano_detection")
INSTRUMENTS = ("bass", "piano", "drums")
ENGINE_TRACK = {"bass": "Bass", "piano": "Chords", "drums": "Drums"}
"""Rôle de l'instrument JTD → nom de piste du moteur."""


# --------------------------------------------------------------------------------------
# Lecture


def bin_label(lo: int, hi: int) -> str:
    return f"{lo}-{hi}"


BIN_LABELS = tuple(bin_label(lo, hi) for lo, hi in zip(TEMPO_BIN_EDGES[:-1], TEMPO_BIN_EDGES[1:]))


def tempo_bin(tempo: float) -> str | None:
    """Tranche de tempo (`"150-175"`…) ; `None` hors de [100, 330)."""
    for lo, hi in zip(TEMPO_BIN_EDGES[:-1], TEMPO_BIN_EDGES[1:]):
        if lo <= tempo < hi:
            return bin_label(lo, hi)
    return None


def parse_metadata(text: str) -> dict[str, Any]:
    """Lit `metadata.json` : le `NaN` non standard devient `None`."""
    return json.loads(text, parse_constant=lambda _: None)


def open_archive(path: Path = ARCHIVE) -> zipfile.ZipFile:
    """Ouvre l'archive JTD après vérification du SHA256 et du MD5 publiés."""
    verified = open_verified(path, SOURCE_SHA256)
    with verified.open("rb") as stream:
        md5 = hashlib.file_digest(stream, "md5").hexdigest()
    if md5 != SOURCE_MD5:
        raise DigestError(f"MD5 différent pour {path} : attendu {SOURCE_MD5}, obtenu {md5}. Fichier refusé.")
    return zipfile.ZipFile(verified)


def track_names(archive: zipfile.ZipFile) -> list[str]:
    """Identifiants de piste (`fname`) de l'archive, triés."""
    names = {n[len(PREFIX):].split("/", 1)[0] for n in archive.namelist()
             if n.startswith(PREFIX) and n.endswith("/metadata.json")}
    return sorted(names)


def parse_beats(text: str) -> dict[str, np.ndarray]:
    """`beats.csv` → tableaux `beats`, `piano`, `bass`, `drums` (NaN si vide), `metre` (NaN si absent)."""
    columns: dict[str, list[float]] = {k: [] for k in ("beats", "piano", "bass", "drums", "metre_auto")}
    for row in csv.DictReader(io.StringIO(text)):
        for key, values in columns.items():
            raw = (row.get(key) or "").strip()
            values.append(float(raw) if raw else float("nan"))
    out = {k: np.asarray(v, dtype=float) for k, v in columns.items()}
    out["metre"] = out.pop("metre_auto")
    return out


def parse_onsets(text: str) -> np.ndarray:
    """Fichier d'attaques (une colonne sans en-tête) → instants triés, en secondes."""
    values = [float(line.strip().split(",")[-1]) for line in text.splitlines() if line.strip()]
    return np.sort(np.asarray(values, dtype=float))


@dataclass
class Track:
    """Piste JTD : métadonnées, temps, attaques appariées et attaques brutes de chaque instrument."""
    fname: str
    meta: dict[str, Any]
    beats: np.ndarray
    metre: np.ndarray
    paired: dict[str, np.ndarray]
    onsets: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def tempo(self) -> float:
        return float(self.meta["tempo"])

    @property
    def step_s(self) -> float:
        """Durée d'un pas du profil (¼ de temps) au tempo de la piste, en secondes."""
        return 60.0 / self.tempo / STEPS_PER_BEAT

    def paired_share(self) -> float:
        """Part des temps où basse ET batterie sont appariées."""
        if not len(self.beats):
            return 0.0
        both = ~np.isnan(self.paired["bass"]) & ~np.isnan(self.paired["drums"])
        return float(both.mean())


def read_track(archive: zipfile.ZipFile, fname: str, *, with_onsets: bool = True) -> Track:
    """Lit une piste (jamais `piano_midi.mid`)."""
    def text(name: str) -> str:
        return archive.read(f"{PREFIX}{fname}/{name}").decode("utf-8")

    meta = parse_metadata(text("metadata.json"))
    beats = parse_beats(text("beats.csv"))
    onsets = ({inst: parse_onsets(text(f"{inst}_onsets.csv")) for inst in INSTRUMENTS} if with_onsets else {})
    return Track(fname, meta, beats["beats"], beats["metre"],
                 {inst: beats[inst] for inst in INSTRUMENTS}, onsets)


def keep_track(meta: Mapping[str, Any]) -> bool:
    """Filtre de métadonnées : 4 temps par mesure et tempo dans la plage."""
    tempo = meta.get("tempo")
    return (meta.get("time_signature") == 4 and tempo is not None
            and TEMPO_RANGE[0] <= float(tempo) <= TEMPO_RANGE[1])


def manifest_row(meta: Mapping[str, Any], paired_share: float, n_beats: int) -> dict[str, Any]:
    """Ligne de manifeste d'une piste : faits de `metadata.json` et du pointage (aucune attaque)."""
    musicians = meta.get("musicians") or {}
    year = meta.get("recording_year")
    return {
        "fname": meta["fname"],
        "pianist": musicians.get("pianist"), "bassist": musicians.get("bassist"),
        "drummer": musicians.get("drummer"),
        "year": int(year) if str(year).isdigit() else None,
        "tempo": meta.get("tempo"),
        "time_signature": meta.get("time_signature"),
        "n_beats": n_beats,
        "bass_drums_paired_share": paired_share,
        "ratings": {k[len("rating_"):]: meta[k] for k in RATING_FIELDS if meta.get(k) is not None},
        "licence": SOURCE_LICENCE,
    }


def write_manifest(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    """Écrit `corpus/jtd/manifest.jsonl` (toutes les pistes) et `VERSION`."""
    rows = []
    for fname in track_names(archive):
        track = read_track(archive, fname, with_onsets=False)
        rows.append(manifest_row(track.meta, track.paired_share(), len(track.beats)))
    text = write_jsonl(MANIFEST, rows)
    write_version(VERSION_FILE, {
        "version": SOURCE_VERSION,
        "source": SOURCE_NAME,
        "url": SOURCE_URL,
        "sha256": SOURCE_SHA256,
        "md5": SOURCE_MD5,
        "licence": SOURCE_LICENCE,
        "attribution": ATTRIBUTION,
        "date_source": "2024-05-21",
        "subset": f"{len(rows)} pistes (metadata.json, beats.csv, *_onsets.csv) ; piano_midi.mid jamais lu",
    }, text)
    return rows


# --------------------------------------------------------------------------------------
# Intervalles entre temps


def valid_intervals(beats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Durées des intervalles entre temps consécutifs et masque des intervalles réguliers
    (durée à ±`INTERVAL_TOLERANCE` de la médiane de la piste : écarte les temps manquants)."""
    if len(beats) < 3:
        return np.diff(beats), np.zeros(max(len(beats) - 1, 0), dtype=bool)
    intervals = np.diff(beats)
    median = float(np.median(intervals))
    valid = (intervals > 0) & (np.abs(intervals / median - 1.0) <= INTERVAL_TOLERANCE)
    return intervals, valid


def locate(beats: np.ndarray, onsets: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Attaques → `(indices k, fractions, masque)` : `b_k ≤ attaque < b_{k+1}`, fraction de
    l'intervalle ; le masque retient les attaques d'un intervalle régulier."""
    intervals, valid = valid_intervals(beats)
    k = np.searchsorted(beats, onsets, side="right") - 1
    inside = (k >= 0) & (k < len(intervals))
    k = np.clip(k, 0, max(len(intervals) - 1, 0))
    if len(intervals) == 0:
        return k, np.zeros(len(onsets)), np.zeros(len(onsets), dtype=bool)
    mask = inside & valid[k]
    fractions = np.where(mask, (onsets - beats[k]) / np.where(intervals[k] > 0, intervals[k], 1.0), 0.0)
    return k, fractions, mask


def swing_observations(beats: np.ndarray, onsets: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Rapports de swing d'une piste : fraction de l'intervalle des attaques comprises entre 0,45
    et 0,85. Renvoie `(rapports, intervalles réguliers, intervalles avec une telle attaque)`."""
    _, valid = valid_intervals(beats)
    k, fractions, mask = locate(beats, onsets)
    low, high = SWING_WINDOW
    hit = mask & (fractions >= low) & (fractions <= high)
    return fractions[hit], int(valid.sum()), int(len(np.unique(k[hit])))


def long_short(ratio: float) -> float:
    """Rapport de durées long/court d'un rapport de swing : r / (1 − r)."""
    return ratio / (1.0 - ratio)


# --------------------------------------------------------------------------------------
# Statistiques par piste


@dataclass
class TrackStats:
    """Mesures d'une piste retenue (tout en pas du profil ou en secondes)."""
    track: Track
    bin: str
    swing: dict[str, dict[str, Any]]
    drums_ratio: float | None
    placements: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]
    """Clé → `(écarts en pas, écarts en ms, temps de la mesure 1..4)`."""


def placements_of(track: Track) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Écarts d'une piste : absolus (`abs_<instrument>` = attaque − temps) et relatifs
    (`rel_<a>_<b>` = a − b, attaques appariées au même temps). Négatif = en avance."""
    def pack(delta_s: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return delta_s[mask] / track.step_s, delta_s[mask] * 1000.0, track.metre[mask]

    out = {}
    for inst in INSTRUMENTS:
        delta = track.paired[inst] - track.beats
        out[f"abs_{inst}"] = pack(delta, ~np.isnan(delta))
    for a, b in (("bass", "drums"), ("piano", "drums"), ("bass", "piano")):
        delta = track.paired[a] - track.paired[b]
        out[f"rel_{a}_{b}"] = pack(delta, ~np.isnan(delta))
    return out


def track_stats(track: Track) -> TrackStats | None:
    """Mesures d'une piste, ou `None` si elle sort du filtre (tempo hors tranches)."""
    label = tempo_bin(track.tempo)
    if label is None:
        return None
    swing = {}
    for inst in INSTRUMENTS:
        ratios, n_intervals, n_with = swing_observations(track.beats, track.onsets[inst])
        swing[inst] = {"ratios": ratios, "n_intervals": n_intervals, "n_intervals_with_attack": n_with}
    drums_ratio = None
    if len(swing["drums"]["ratios"]) >= MIN_SWING_OBSERVATIONS:
        drums_ratio = float(np.median(swing["drums"]["ratios"]))
    return TrackStats(track, label, swing, drums_ratio, placements_of(track))


def retained_stats(archive: zipfile.ZipFile) -> tuple[list[TrackStats], dict[str, int]]:
    """Pistes retenues et comptes du filtre (`total`, `time_signature_4`, `tempo_in_range`,
    `paired_ok`, `in_bins`)."""
    counts = {"total": 0, "time_signature_4": 0, "tempo_in_range": 0, "paired_ok": 0, "in_bins": 0}
    kept = []
    for fname in track_names(archive):
        counts["total"] += 1
        track = read_track(archive, fname)
        if track.meta.get("time_signature") != 4:
            continue
        counts["time_signature_4"] += 1
        if not keep_track(track.meta):
            continue
        counts["tempo_in_range"] += 1
        if track.paired_share() < MIN_PAIRED_SHARE:
            continue
        counts["paired_ok"] += 1
        stats = track_stats(track)
        if stats is None:
            continue
        counts["in_bins"] += 1
        kept.append(stats)
    return kept, counts


# --------------------------------------------------------------------------------------
# Agrégats par tranche


def _by_bin(stats: Sequence[TrackStats]) -> dict[str, list[TrackStats]]:
    out: dict[str, list[TrackStats]] = {label: [] for label in BIN_LABELS}
    for s in stats:
        out[s.bin].append(s)
    return out


def swing_block(stats: Sequence[TrackStats], inst: str) -> dict[str, Any]:
    """Rapport de swing d'un instrument sur un ensemble de pistes : médiane par piste (au moins
    `MIN_SWING_OBSERVATIONS` attaques de contretemps), puis centiles sur les pistes."""
    medians, shares, n_obs = [], [], 0
    for s in stats:
        block = s.swing[inst]
        ratios = block["ratios"]
        n_obs += len(ratios)
        if block["n_intervals"]:
            shares.append(block["n_intervals_with_attack"] / block["n_intervals"])
        if len(ratios) >= MIN_SWING_OBSERVATIONS:
            medians.append(float(np.median(ratios)))
    return {
        "n_tracks": len(stats),
        "n_tracks_measured": len(medians),
        "n_observations": n_obs,
        "ratio": describe(medians),
        "long_short": describe([long_short(r) for r in medians]),
        "share_intervals_with_attack": describe(shares),
    }


def _pct(values: np.ndarray) -> dict[str, Any]:
    """Effectif, centiles 10/25/50/75/90 et moyenne tronquée à 10 % de chaque côté (les CSV étant à
    10 ms, la médiane d'un écart proche de 0 tombe sur une valeur discrète ; la moyenne tronquée
    la complète)."""
    trimmed = float(trim_mean(values, 0.1)) if len(values) else None
    return {"n": int(len(values)), "trimmed_mean": trimmed, **percentiles(values)}


def placement_block(stats: Sequence[TrackStats], key: str, metres: Sequence[int] | None,
                    per_track: bool) -> dict[str, Any]:
    """Écarts d'un jeu de pistes : centiles « poolés » (chaque attaque une fois) en pas et en ms,
    et, si demandé, centiles des médianes par piste. `metres` restreint aux temps 1..4 donnés."""
    steps, ms, medians_steps, medians_ms = [], [], [], []
    for s in stats:
        d_steps, d_ms, metre = s.placements[key]
        if metres is not None:
            keep = np.isin(metre, metres)
            d_steps, d_ms = d_steps[keep], d_ms[keep]
        if len(d_steps):
            steps.append(d_steps)
            ms.append(d_ms)
            medians_steps.append(float(np.median(d_steps)))
            medians_ms.append(float(np.median(d_ms)))
    all_steps = np.concatenate(steps) if steps else np.array([])
    all_ms = np.concatenate(ms) if ms else np.array([])
    block = {"pooled_steps": _pct(all_steps), "pooled_ms": _pct(all_ms)}
    if per_track:
        block["per_track_median_steps"] = describe(medians_steps)
        block["per_track_median_ms"] = describe(medians_ms)
    return block


METRE_GROUPS: dict[str, Sequence[int] | None] = {
    "all": None, "beats_1_3": (1, 3), "beats_2_4": (2, 4), "beat_1": (1,), "beat_2": (2,), "beat_3": (3,), "beat_4": (4,),
}
ABSOLUTE_GROUPS = ("all", "beats_1_3", "beats_2_4")


def placement_section(stats: Sequence[TrackStats]) -> dict[str, Any]:
    """Placement par tranche : absolu (écart au temps) et relatif (entre instruments)."""
    groups = {"all": list(stats), **_by_bin(stats)}
    out: dict[str, Any] = {"absolute_vs_beat": {}, "relative": {}}
    for inst in INSTRUMENTS:
        key = f"abs_{inst}"
        out["absolute_vs_beat"][inst] = {
            label: {g: placement_block(members, key, METRE_GROUPS[g], per_track=(g == "all"))
                    for g in ABSOLUTE_GROUPS}
            for label, members in groups.items()}
    for a, b in (("bass", "drums"), ("piano", "drums"), ("bass", "piano")):
        key = f"rel_{a}_{b}"
        out["relative"][f"{a}_minus_{b}"] = {
            label: {g: placement_block(members, key, metres, per_track=(g == "all"))
                    for g, metres in METRE_GROUPS.items()}
            for label, members in groups.items()}
    return out


def jitter_block(stats: Sequence[TrackStats], key: str) -> dict[str, Any]:
    """Dispersion par piste de l'écart `key` : écart-type (pas et ms) et écart-type robuste
    (1,4826 × MAD), puis centiles sur les pistes (au moins `MIN_JITTER_PAIRS` paires)."""
    std_steps, std_ms, robust_steps = [], [], []
    for s in stats:
        d_steps, d_ms, _ = s.placements[key]
        if len(d_steps) < MIN_JITTER_PAIRS:
            continue
        std_steps.append(float(np.std(d_steps, ddof=1)))
        std_ms.append(float(np.std(d_ms, ddof=1)))
        robust_steps.append(float(1.4826 * np.median(np.abs(d_steps - np.median(d_steps)))))
    return {"n_tracks": len(std_steps), "std_steps": describe(std_steps), "std_ms": describe(std_ms),
            "robust_std_steps": describe(robust_steps)}


def jitter_section(stats: Sequence[TrackStats]) -> dict[str, Any]:
    groups = {"all": list(stats), **_by_bin(stats)}
    return {f"{a}_minus_{b}": {label: jitter_block(members, f"rel_{a}_{b}") for label, members in groups.items()}
            for a, b in (("bass", "drums"), ("piano", "drums"))}


def swing_section(stats: Sequence[TrackStats]) -> dict[str, Any]:
    groups = {"all": list(stats), **_by_bin(stats)}
    return {inst: {label: swing_block(members, inst) for label, members in groups.items()} for inst in INSTRUMENTS}


# --------------------------------------------------------------------------------------
# Rythme du piano par mesure et basse hors pulsation


def measure_rows(track: Track) -> np.ndarray:
    """Pour chaque temps, l'indice de la mesure (départ au temps `metre_auto == 1`) ou −1.

    Une mesure est retenue si ses 4 temps se suivent (`metre_auto` 1, 2, 3, 4) et si ses 4
    intervalles (jusqu'au temps suivant) sont réguliers."""
    n = len(track.beats)
    rows = np.full(n, -1, dtype=int)
    _, valid = valid_intervals(track.beats)
    for i in range(n - 4):
        if (track.metre[i:i + 4] == np.array([1, 2, 3, 4])).all() and valid[i:i + 4].all():
            rows[i:i + 4] = i
    return rows


def piano_measures(track: Track, ratio: float) -> list[tuple[int, int]]:
    """Attaques du piano → `[(mesure, pas 0..15)]` : chaque attaque va au pas swingué le plus
    proche (`drums.quantize`, rapport `ratio`), le pas 0 d'un temps suivant pouvant être celui
    de la mesure suivante ; les attaques hors mesure retenue sont écartées. La liste des mesures
    (y compris silencieuses) est donnée par `measure_rows`."""
    rows = measure_rows(track)
    k, fractions, mask = locate(track.beats, track.onsets["piano"])
    out = []
    for kk, frac, ok in zip(k, fractions, mask):
        if not ok:
            continue
        shift, sub = drums_module.quantize(float(frac), ratio)
        row = int(kk) + shift
        if row >= len(rows) or rows[row] < 0:
            continue
        out.append((int(rows[row]), int(track.metre[row] - 1) * STEPS_PER_BEAT + sub))
    return out


def piano_rhythm_block(stats: Sequence[TrackStats], ratios: Mapping[str, float]) -> dict[str, Any]:
    """Rythme du piano d'un ensemble de pistes : probabilité par pas (part des mesures avec une
    attaque à ce pas), attaques par mesure, parts des mesures avec attaque aux pas 6, 10, 14,
    part des mesures sans attaque. `ratios` : rapport de swing employé par piste (`fname`)."""
    n_measures = 0
    with_step = np.zeros(16, dtype=int)
    counts: list[int] = []
    for s in stats:
        track = s.track
        starts = np.unique(measure_rows(track)[measure_rows(track) >= 0])
        attacks = piano_measures(track, ratios[track.fname])
        per_measure: dict[int, list[int]] = {int(m): [] for m in starts}
        for measure, step in attacks:
            if measure in per_measure:
                per_measure[measure].append(step)
        for steps in per_measure.values():
            n_measures += 1
            counts.append(len(steps))
            for step in set(steps):
                with_step[step] += 1
    counts_arr = np.asarray(counts)

    def share(mask: np.ndarray | int) -> float:
        return float(np.sum(mask) / n_measures) if n_measures else 0.0

    return {
        "n_tracks": len(stats),
        "n_measures": n_measures,
        "n_attacks": int(counts_arr.sum()) if n_measures else 0,
        "prob_by_step": [{"step": i, "n": int(with_step[i]), "prob": float(with_step[i] / n_measures) if n_measures else 0.0}
                         for i in range(16)],
        "attacks_per_measure": describe(counts_arr) if n_measures else describe([]),
        "share_step_14": share(with_step[14]),
        "share_step_6": share(with_step[6]),
        "share_step_10": share(with_step[10]),
        "share_silent_measures": share(counts_arr == 0) if n_measures else 0.0,
        "n_silent_measures": int((counts_arr == 0).sum()) if n_measures else 0,
    }


def swing_ratios_for_grid(stats: Sequence[TrackStats]) -> dict[str, float]:
    """Rapport de swing employé pour quantifier les attaques d'une piste : celui de sa batterie ;
    à défaut, la médiane de sa tranche de tempo ; à défaut, le repli triolet. Borné comme `drums`."""
    by_bin: dict[str, list[float]] = {}
    for s in stats:
        if s.drums_ratio is not None:
            by_bin.setdefault(s.bin, []).append(s.drums_ratio)
    medians = {label: float(np.median(v)) for label, v in by_bin.items()}
    out = {}
    for s in stats:
        ratio = s.drums_ratio if s.drums_ratio is not None else medians.get(s.bin)
        out[s.track.fname] = drums_module.effective_ratio(ratio)
    return out


def piano_rhythm_section(stats: Sequence[TrackStats]) -> dict[str, Any]:
    ratios = swing_ratios_for_grid(stats)
    groups = {"all": list(stats), **_by_bin(stats)}
    return {label: piano_rhythm_block(members, ratios) for label, members in groups.items()}


def bass_offbeat_block(stats: Sequence[TrackStats]) -> dict[str, Any]:
    """Part des attaques de basse à plus de `OFF_BEAT_THRESHOLD` temps du temps le plus proche
    (notes en plus de la noire) et attaques de basse par temps."""
    total = off = 0
    per_track_share, per_beat = [], []
    for s in stats:
        track = s.track
        k, fractions, mask = locate(track.beats, track.onsets["bass"])
        if not mask.any():
            continue
        distance = np.minimum(fractions[mask], 1.0 - fractions[mask])
        n_off = int((distance > OFF_BEAT_THRESHOLD).sum())
        total += int(mask.sum())
        off += n_off
        per_track_share.append(n_off / int(mask.sum()))
        _, valid = valid_intervals(track.beats)
        if valid.sum():
            per_beat.append(int(mask.sum()) / int(valid.sum()))
    return {
        "n_tracks": len(stats), "n_onsets": total, "n_off_beat": off,
        "share_off_beat": (off / total) if total else None,
        "share_off_beat_per_track": describe(per_track_share),
        "onsets_per_beat_per_track": describe(per_beat),
    }


def bass_offbeat_section(stats: Sequence[TrackStats]) -> dict[str, Any]:
    groups = {"all": list(stats), **_by_bin(stats)}
    return {"threshold_beats": OFF_BEAT_THRESHOLD,
            "definition": "attaque de basse à plus de 0,2 temps du temps le plus proche (distance / durée de "
                          "l'intervalle) ; les attaques d'un intervalle irrégulier sont écartées",
            "by_bin": {label: bass_offbeat_block(members) for label, members in groups.items()}}


# --------------------------------------------------------------------------------------
# Mappage moteur


def _pooled_steps(stats: Sequence[TrackStats], key: str, metres: Sequence[int] | None = None) -> np.ndarray:
    pooled = []
    for s in stats:
        d_steps, _, metre = s.placements[key]
        pooled.append(d_steps if metres is None else d_steps[np.isin(metre, metres)])
    return np.concatenate(pooled) if pooled else np.array([])


def _median_steps(stats: Sequence[TrackStats], key: str, metres: Sequence[int] | None = None) -> float | None:
    values = _pooled_steps(stats, key, metres)
    return float(np.median(values)) if len(values) else None


def _trimmed_mean_steps(stats: Sequence[TrackStats], key: str) -> float | None:
    values = _pooled_steps(stats, key)
    return float(trim_mean(values, 0.1)) if len(values) else None


def engine_mapping(stats: Sequence[TrackStats]) -> dict[str, Any]:
    """Valeurs à reporter dans un profil moteur.

    - `swing_ratio_by_tempo` : tranche → rapport de swing médian de la batterie (médiane des
      médianes par piste) ;
    - `micro_timing` : par piste du moteur (`Bass`, `Chords` = piano, `Drums`), décalage médian
      par rapport à la batterie (`offsets`, pas, négatif = en avance ; `offsets_trimmed_mean` : moyenne
      tronquée, plus fine que la médiane à la résolution de 10 ms), par temps 1..4
      (`offsets_by_beat`), et `jitter` conseillé = médiane sur les pistes de l'écart-type de
      l'écart à la batterie (pas), borné à 0..0,1 comme le moteur (`jitter_raw` : non borné).
    """
    groups = {"all": list(stats), **_by_bin(stats)}
    ratio_by_tempo = {}
    for label, members in groups.items():
        medians = [s.drums_ratio for s in members if s.drums_ratio is not None]
        ratio_by_tempo[label] = {"ratio": float(np.median(medians)) if medians else None, "n_tracks": len(medians)}
    micro: dict[str, Any] = {}
    for inst in ("bass", "piano"):
        key = f"rel_{inst}_drums"
        entry: dict[str, Any] = {"offsets": {}, "offsets_trimmed_mean": {}, "offsets_by_beat": {}, "jitter": {},
                                 "jitter_raw": {}, "n_tracks": {}}
        for label, members in groups.items():
            entry["offsets"][label] = _median_steps(members, key)
            entry["offsets_trimmed_mean"][label] = _trimmed_mean_steps(members, key)
            entry["offsets_by_beat"][label] = [_median_steps(members, key, (b,)) for b in (1, 2, 3, 4)]
            jitter = jitter_block(members, key)
            raw = jitter["std_steps"]["p50"]
            entry["jitter_raw"][label] = raw
            entry["jitter"][label] = None if raw is None else min(max(raw, 0.0), MAX_ENGINE_JITTER_STEPS)
            entry["n_tracks"][label] = jitter["n_tracks"]
        micro[ENGINE_TRACK[inst]] = entry
    micro[ENGINE_TRACK["drums"]] = {
        "offsets": {label: 0.0 for label in groups},
        "reference": "la batterie est la référence des décalages relatifs (0 par définition)",
        "offset_vs_beat_steps": {label: _median_steps(members, "abs_drums") for label, members in groups.items()},
    }
    return {
        "swing_ratio_by_tempo": ratio_by_tempo,
        "micro_timing": micro,
        "units": "pas du profil (1 pas = ¼ de temps) ; négatif = en avance sur la batterie",
        "engine_jitter_bounds_steps": [0.0, MAX_ENGINE_JITTER_STEPS],
    }


# --------------------------------------------------------------------------------------
# Sortie


CAVEATS = [
    "Résolution des CSV : 10 ms (arrondi au centième de seconde) ; ¼ de pas ≈ 19 ms à 200 BPM.",
    "Les écarts ABSOLUS à un temps dépendent de la détection des temps de la piste (automatique) : "
    "seuls les écarts RELATIFS entre instruments (basse − batterie, piano − batterie, basse − piano) sont fiables.",
    "Le rapport de swing de la batterie est dominé par le ride ; basse et piano sont donnés pour information.",
    "Le rythme du piano mêle comping et solo (indicatif) ; agrégats poolés : les longues pistes pèsent plus.",
    "Écarts en pas calculés au tempo de `metadata.json` de chaque piste.",
]


def build_measures(archive: zipfile.ZipFile) -> dict[str, Any]:
    """JSON complet de `references/wjazzd-swing/measures-timing.json`."""
    stats, counts = retained_stats(archive)
    per_bin = {label: len(members) for label, members in _by_bin(stats).items()}
    n_beats = int(sum(len(s.track.beats) for s in stats))
    piano = piano_rhythm_section(stats)
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
            "subset": f"time_signature == 4 ; tempo {TEMPO_RANGE[0]:.0f}–{TEMPO_RANGE[1]:.0f} BPM ; au moins "
                      f"{MIN_PAIRED_SHARE:.0%} des temps avec basse ET batterie appariées ; tranches de 25 BPM "
                      "de 100 à 275 puis 275–330",
            "counts": {
                "n_tracks_archive": counts["total"],
                "n_tracks_time_signature_4": counts["time_signature_4"],
                "n_tracks_tempo_in_range": counts["tempo_in_range"],
                "n_tracks_retained": len(stats),
                "n_tracks_dropped_paired_share": counts["tempo_in_range"] - counts["paired_ok"],
                "n_beats": n_beats,
                "n_measures_piano_rhythm": piano["all"]["n_measures"],
            },
        },
        "filter": {
            "min_paired_share_bass_and_drums": MIN_PAIRED_SHARE,
            "tempo_range_bpm": list(TEMPO_RANGE),
            "bins": list(BIN_LABELS),
            "tracks_per_bin": per_bin,
            "min_tracks_per_bin": MIN_TRACKS_PER_BIN,
            "bins_below_min": [b for b, n in per_bin.items() if n < MIN_TRACKS_PER_BIN],
            "swing_window": list(SWING_WINDOW),
            "interval_tolerance": INTERVAL_TOLERANCE,
            "min_swing_observations_per_track": MIN_SWING_OBSERVATIONS,
            "min_jitter_pairs_per_track": MIN_JITTER_PAIRS,
        },
        "caveats": CAVEATS,
        "swing_ratio": swing_section(stats),
        "placement": placement_section(stats),
        "jitter": jitter_section(stats),
        "piano_rhythm": {
            "note": "attaques de piano_onsets.csv rapportées à la mesure (temps `metre_auto` == 1) et au pas "
                    "swingué le plus proche ; rapport de swing = celui de la batterie de la piste (repli : "
                    "médiane de la tranche) ; comping et solo mêlés (indicatif)",
            "by_bin": piano,
        },
        "bass_off_beat": bass_offbeat_section(stats),
        "engine_mapping": engine_mapping(stats),
    }


def summary(data: Mapping[str, Any]) -> str:
    """Résumé texte du JSON de mesures."""
    prov = data["provenance"]
    c = prov["counts"]
    out = [f"{prov['source']} {prov['version']} — {prov['licence']}",
           f"pistes : archive {c['n_tracks_archive']}, 4 temps {c['n_tracks_time_signature_4']}, "
           f"tempo ok {c['n_tracks_tempo_in_range']}, retenues {c['n_tracks_retained']} "
           f"(écartées : appariement {c['n_tracks_dropped_paired_share']}) ; {c['n_beats']} temps",
           f"pistes par tranche : {data['filter']['tracks_per_bin']}",
           "\nRapport de swing de la batterie par tranche (n pistes, p10 p50 p90 ; long/court p50)"]
    for label, b in data["swing_ratio"]["drums"].items():
        r = b["ratio"]
        if r["n"]:
            out.append(f"  {label:>8} {r['n']:>4}  {r['p10']:.3f} {r['p50']:.3f} {r['p90']:.3f}   "
                       f"{b['long_short']['p50']:.2f}  attaque/intervalle {b['share_intervals_with_attack']['p50']:.2f}")
    out.append("\nMapping moteur : rapport médian par tranche")
    for label, v in data["engine_mapping"]["swing_ratio_by_tempo"].items():
        out.append(f"  {label:>8} {v['ratio']:.3f}  (n {v['n_tracks']})")
    out.append("\nMicro-timing relatif à la batterie (pas ; négatif = en avance)")
    for track in ("Bass", "Chords"):
        m = data["engine_mapping"]["micro_timing"][track]
        out.append(f"  {track:<7} offset {m['offsets']['all']:+.3f} (moy. tronquée {m['offsets_trimmed_mean']['all']:+.3f})  par temps "
                   f"{[round(x, 3) for x in m['offsets_by_beat']['all']]}  jitter {m['jitter']['all']} "
                   f"(brut {m['jitter_raw']['all']:.3f})")
    out.append("\nRythme du piano (toutes tranches)")
    p = data["piano_rhythm"]["by_bin"]["all"]
    out.append(f"  {p['n_measures']} mesures ; attaques/mesure p50 {p['attacks_per_measure']['p50']}, "
               f"silence {p['share_silent_measures']:.2f}, pas 14 {p['share_step_14']:.2f}, "
               f"pas 6 {p['share_step_6']:.2f}, pas 10 {p['share_step_10']:.2f}")
    out.append("  P(pas) " + " ".join(f"{s['prob']:.2f}" for s in p["prob_by_step"]))
    b = data["bass_off_beat"]["by_bin"]["all"]
    out.append(f"\nBasse hors pulsation : {b['share_off_beat']:.3f} des attaques ({b['n_off_beat']}/{b['n_onsets']}), "
               f"attaques par temps p50 {b['onsets_per_beat_per_track']['p50']:.2f}")
    return "\n".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fetch", action="store_true", help="télécharge l'archive (SHA256 et MD5 vérifiés)")
    parser.add_argument("--manifest", action="store_true", help="écrit corpus/jtd/manifest.jsonl et VERSION")
    parser.add_argument("--measures", action="store_true", help="écrit references/wjazzd-swing/measures-timing.json")
    parser.add_argument("--summary", action="store_true", help="affiche un résumé lisible")
    parser.add_argument("--out", type=Path, default=OUTPUT, help="sortie JSON des mesures")
    args = parser.parse_args(argv)
    steps = args.fetch or args.manifest or args.measures or args.summary
    try:
        if args.fetch or not steps:
            fetch(SOURCE_URL, ARCHIVE, SOURCE_SHA256)
            print(f"archive vérifiée : {ARCHIVE}")
        if args.manifest or args.measures or not steps:
            archive = open_archive()
            if args.manifest or not steps:
                rows = write_manifest(archive)
                print(f"manifeste : {len(rows)} pistes → {MANIFEST}")
            if args.measures or not steps:
                write_json(args.out, build_measures(archive))
                print(f"mesures → {args.out}")
        if args.summary:
            if not args.out.is_file():
                print(f"{args.out} absent : lancer --measures", file=sys.stderr)
                return 1
            print(summary(json.loads(args.out.read_text(encoding="utf-8"))))
    except (ValueError, FileNotFoundError, RuntimeError) as err:
        print(f"erreur : {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
