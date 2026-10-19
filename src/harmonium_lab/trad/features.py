"""Statistiques trad D5 : les mêmes fonctions pour corpus et moteur.

``features(tune)`` est pure et déterministe : dict JSON-sérialisable avec
forme, cadences, registre, intervalles, rythme, cellules et harmonie.
``FEATURE_SCALARS`` liste les scalaires repris par ``build_profile``.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .cells import bar_to_cell, pitch_to_degree
from .model import TradTune, mode_intervals, normalize_mode

PART_BARS = 8  # une partie = 8 mesures

INTERVAL_CLASSES = ["unison", "second", "third", "fourth", "fifth", "larger"]

DURATION_BUCKETS = ["1", "2", "3", "4+"]

_ROMAN_MAJOR = ["I", "II", "III", "IV", "V", "VI", "VII"]
_ROMAN_MINOR = ["i", "ii", "iii", "iv", "v", "vi", "vii"]

_CHORD_RE = re.compile(r"^([A-G])([#b]?)(.*)$")
_PC_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

#: Chemins des scalaires exploités par les profils par type.
FEATURE_SCALARS: list[tuple[str, ...]] = [
    ("n_bars",),
    ("register", "ambitus"),
    ("register", "mean_pitch_part0"),
    ("register", "mean_pitch_part1"),
    ("register", "b_minus_a_mean_pitch"),
    ("intervals", "stepwise_ratio"),
    ("harmony", "chords_per_bar"),
    ("form", "repeat_identity"),
    ("form", "share_identical_bars_5_6_vs_1_2"),
]


def parse_chord_symbol(symbol: str) -> tuple[int | None, str]:
    """Symbole (``"D"``, ``"Am"``, ``"G7"``) -> (pc fondamentale, qualité).

    Qualité parmi ``major`` / ``minor`` / ``diminished`` ; ``"?"`` ou
    illisible -> ``(None, "major")``. Triades d'accompagnement : la septième
    (``"G7"``) ne change pas la qualité de base.
    """
    m = _CHORD_RE.match(symbol.strip())
    if not m:
        return None, "major"
    letter, acc, rest = m.groups()
    pc = _PC_BASE[letter] + (1 if acc == "#" else -1 if acc == "b" else 0)
    rest = rest.lower()
    if rest.startswith("dim"):
        quality = "diminished"
    elif rest.startswith("aug"):
        quality = "major"
    elif rest.startswith("m") and not rest.startswith("maj"):
        quality = "minor"
    else:
        quality = "major"
    return pc % 12, quality


def chord_degree_label(symbol: str, tonic_pc: int, mode: str) -> str:
    """Degré d'accord en chiffres romains (``"I"``, ``"vi"``, ``"V"``).

    Fondamentale hors mode (chromatisme) -> ``"?"`` (documenté).
    """
    root_pc, quality = parse_chord_symbol(symbol)
    if root_pc is None:
        return "?"
    intervals = mode_intervals(mode)
    semis = (root_pc - tonic_pc) % 12
    if semis not in intervals:
        return "?"
    degree = intervals.index(semis) + 1
    if quality == "major":
        return _ROMAN_MAJOR[degree - 1]
    if quality == "diminished":
        return _ROMAN_MINOR[degree - 1] + "dim"
    return _ROMAN_MINOR[degree - 1]


def beat_eighths(meter: str) -> int:
    """Pas de la grille des temps forts, en croches (reel 2, gigue 3)."""
    try:
        _, den = meter.split("/")
        den = int(den)
    except ValueError:
        return 2
    if den == 2:
        return 4  # 2/2 : temps = blanche
    if den == 8:
        return 3  # 6/8, 9/8 : temps = noire pointée
    return 2  # 4/4, 3/4, 2/4 : temps = noire


def _bar_signature(bar) -> tuple:
    """Signature comparable d'une mesure (hauteurs, attaques, durées)."""
    return tuple((n.pitch, round(n.onset, 3), round(n.duration, 3)) for n in bar)


def _form_features(tune: TradTune) -> dict[str, Any]:
    n = len(tune.bars)
    sigs = [_bar_signature(b) for b in tune.bars]
    if n >= 32:
        a1, a2, b1, b2 = sigs[0:8], sigs[8:16], sigs[16:24], sigs[24:32]
        repeat_identity = (sum(x == y for x, y in zip(a1, a2)) + sum(x == y for x, y in zip(b1, b2))) / 16.0
    elif n % 2 == 0 and n >= 2:
        half = n // 2
        repeat_identity = sum(x == y for x, y in zip(sigs[:half], sigs[half:])) / half
    else:
        repeat_identity = 0.0
    # Mesures 5-6 vs 1-2 (index 4:6 vs 0:2) dans chaque partie de 8.
    chunks = [sigs[i : i + PART_BARS] for i in range(0, n, PART_BARS) if len(sigs[i : i + PART_BARS]) == PART_BARS]
    if chunks:
        share = sum(1 for p in chunks if p[4:6] == p[0:2]) / len(chunks)
    else:
        share = 0.0
    if tune.form:
        # Plan ABC : scheme/parts/is_aabb/pickup/cause/source analysés du texte.
        return {
            "scheme": tune.form.get("scheme", "?"),
            "parts": list(tune.form.get("parts", [])),
            "is_aabb": bool(tune.form.get("is_aabb", False)),
            "pickup": float(tune.form.get("pickup", 0.0)),
            "cause": tune.form.get("cause"),
            "source": tune.form.get("source", "abc"),
            "repeat_identity": round(repeat_identity, 4),
            "share_identical_bars_5_6_vs_1_2": round(share, 4),
            "n_parts": len(tune.form.get("parts", [])),
        }
    # Sans plan (MIDI moteur) : scheme par contenu, mesures de 8.
    from .form import describe_form

    letters: dict[tuple, str] = {}
    scheme_chars = []
    for c in chunks:
        key = tuple(c)
        if key not in letters:
            letters[key] = chr(ord("A") + len(letters))
        scheme_chars.append(letters[key])
    scheme = "".join(scheme_chars)
    spans = [_bar_span(b) for b in tune.bars]
    frag_ids = [i for i, s in enumerate(spans) if abs(s - tune.eighths_per_bar) > 0.01]
    if frag_ids:
        scheme = "croche"
    part_lens = [PART_BARS] * len(chunks)
    is_aabb, cause = describe_form(scheme, part_lens, frag_ids)
    return {
        "scheme": scheme,
        "parts": part_lens,
        "is_aabb": is_aabb,
        "pickup": 0.0,
        "cause": cause,
        "source": tune.source or "bars",
        "repeat_identity": round(repeat_identity, 4),
        "share_identical_bars_5_6_vs_1_2": round(share, 4),
        "n_parts": len(chunks),
    }


def _scale_degree(degree: int) -> int:
    """Replie un degré moteur (``8`` -> ``1``, ``-3`` -> ``5``) sur 1..7."""
    step = degree - 1 if degree >= 1 else degree
    return step % 7 + 1


def _sounding_at(bar, slot: float):
    """Notes sonnant sur la position (croches) : attaque <= slot < fin."""
    return [n for n in bar if n.onset <= slot < n.onset + n.duration]


def _bar_span(bar) -> float:
    """Fin de la dernière note (croches) ; 0.0 si mesure vide."""
    return max([n.onset + n.duration for n in bar] + [0.0])


def _cadence_degree(
    bar, tonic_pc: int, mode: str, step: int, eighths_per_bar: int
) -> int | None:
    """Degré d'échelle (1..7) de la note sonnant sur le dernier temps fort.

    Repli : dernière attaque de la mesure ; mesure vide : None.
    """
    if not bar:
        return None
    slots = list(range(0, eighths_per_bar, step))
    for slot in reversed(slots):
        sounding = _sounding_at(bar, float(slot))
        if sounding:
            chosen = max(sounding, key=lambda n: n.onset)
            return _scale_degree(pitch_to_degree(chosen.pitch, tonic_pc, mode))
    chosen = max(bar, key=lambda n: n.onset)
    return _scale_degree(pitch_to_degree(chosen.pitch, tonic_pc, mode))


def _register_features(tune: TradTune) -> dict[str, Any]:
    pitches = [n.pitch for bar in tune.bars for n in bar]
    out: dict[str, Any] = {
        "ambitus": (max(pitches) - min(pitches)) if pitches else 0,
        "mean_pitch_part0": None,
        "mean_pitch_part1": None,
        "b_minus_a_mean_pitch": 0.0,
    }
    means = []
    for i in range(2):
        part = [n.pitch for bar in tune.bars[i * PART_BARS : (i + 1) * PART_BARS] for n in bar]
        if part:
            means.append(sum(part) / len(part))
    if len(means) > 0:
        out["mean_pitch_part0"] = round(means[0], 3)
    if len(means) > 1:
        out["mean_pitch_part1"] = round(means[1], 3)
    # Registre A vs B : en AABB développé (32+ mesures) la partie 1 est la
    # reprise de A ; on compare donc les strains (A = mesures 0-15, B = 16-31).
    n = len(tune.bars)
    if n >= 32:
        a = [n_.pitch for bar in tune.bars[0:16] for n_ in bar]
        b = [n_.pitch for bar in tune.bars[16:32] for n_ in bar]
    elif n >= 16:
        a = [n_.pitch for bar in tune.bars[0:8] for n_ in bar]
        b = [n_.pitch for bar in tune.bars[8:16] for n_ in bar]
    else:
        a, b = [], []
    if a and b:
        out["b_minus_a_mean_pitch"] = round(sum(b) / len(b) - sum(a) / len(a), 3)
    return out


def _interval_class(semitones: int) -> str:
    s = abs(semitones)
    if s == 0:
        return "unison"
    if s <= 2:
        return "second"
    if s <= 4:
        return "third"
    if s == 5:
        return "fourth"
    if s <= 7:
        return "fifth"
    return "larger"


def _interval_features(tune: TradTune) -> dict[str, Any]:
    melody = [n.pitch for bar in tune.bars for n in bar]
    counts = Counter(_interval_class(b - a) for a, b in zip(melody, melody[1:]))
    total = sum(counts.values())
    hist = {c: (counts[c] / total if total else 0.0) for c in INTERVAL_CLASSES}
    stepwise = hist["unison"] + hist["second"]
    return {
        "hist": {c: round(hist[c], 4) for c in INTERVAL_CLASSES},
        "stepwise_ratio": round(stepwise, 4),
        "n_intervals": total,
    }


def _rhythm_features(tune: TradTune) -> dict[str, Any]:
    k = tune.eighths_per_bar
    onsets = Counter()
    durations = Counter()
    n_notes = 0
    for bar in tune.bars:
        for n in bar:
            n_notes += 1
            slot = int(round(n.onset))
            if 0 <= slot < k:
                onsets[slot] += 1
            dur = max(int(round(n.duration)), 1)
            durations["4+" if dur >= 4 else str(dur)] += 1
    onset_hist = [onsets[s] / n_notes if n_notes else 0.0 for s in range(k)]
    duration_hist = {b: (durations[b] / n_notes if n_notes else 0.0) for b in DURATION_BUCKETS}
    return {
        "duration_hist": {b: round(duration_hist[b], 4) for b in DURATION_BUCKETS},
        "onset_hist": [round(v, 4) for v in onset_hist],
        "n_notes": n_notes,
    }


def _harmony_features(tune: TradTune) -> dict[str, Any]:
    labels: list[str] = []
    for bar_chords in tune.chords:
        for _, symbol in sorted(bar_chords):
            labels.append(chord_degree_label(symbol, tune.key_tonic_pc, tune.mode))
    counts = Counter(labels)
    bigrams = Counter(f"{a}->{b}" for a, b in zip(labels, labels[1:]))
    n_bars = len(tune.bars)
    return {
        "chord_degree_counts": dict(sorted(counts.items())),
        "chord_bigrams": dict(sorted(bigrams.items())),
        "chords_per_bar": round(len(labels) / n_bars, 4) if n_bars else 0.0,
        "n_chords": len(labels),
    }


def features(tune: TradTune) -> dict[str, Any]:
    """Calcule les statistiques D5 d'un air (pur, déterministe, robuste).

    Les mesures en trop (« croches ») sont marquées dans ``flags``,
    jamais une erreur.
    """
    mode = normalize_mode(tune.mode)
    step = beat_eighths(tune.meter)

    form = _form_features(tune)
    cadences: dict[str, int | None] = {}
    for i in range(len(tune.bars) // PART_BARS):
        part = tune.bars[i * PART_BARS : (i + 1) * PART_BARS]
        cadences[f"part{i}_m4"] = _cadence_degree(part[3], tune.key_tonic_pc, mode, step, tune.eighths_per_bar)
        cadences[f"part{i}_m8"] = _cadence_degree(part[7], tune.key_tonic_pc, mode, step, tune.eighths_per_bar)

    cells = [
        bar_to_cell(bar, tune.key_tonic_pc, mode, tune.eighths_per_bar)
        for bar in tune.bars
    ]
    spans = [_bar_span(bar) for bar in tune.bars]
    croche_bars = [
        i
        for i, (cell, span) in enumerate(zip(cells, spans))
        # Cellule plus longue que la grille, ou contenu != grille (fragments
        # de mesures « croches » rebarrées par le parseur, levées, etc.).
        if len(cell.split()) != tune.eighths_per_bar
        or abs(span - tune.eighths_per_bar) > 0.01
    ]

    return {
        "tune_id": tune.tune_id,
        "key_tonic_pc": tune.key_tonic_pc,
        "key_name": tune.key_name,
        "mode": mode,
        "meter": tune.meter,
        "eighths_per_bar": tune.eighths_per_bar,
        "n_bars": len(tune.bars),
        "source": tune.source,
        "form": form,
        "cadences": cadences,
        "register": _register_features(tune),
        "intervals": _interval_features(tune),
        "rhythm": _rhythm_features(tune),
        "cells": {
            "per_bar": cells,
            "vocabulary": dict(sorted(Counter(cells).items())),
        },
        "harmony": _harmony_features(tune),
        "flags": {
            "has_croche_bars": bool(croche_bars),
            "croche_bars": croche_bars,
            "n_croche_bars": len(croche_bars),
        },
    }
