"""Sous-ensembles WJazzD non swing (BALLAD, TWOBEAT, LATIN, FUNK) : mesures de la basse, rythme de la basse, IC.

    python -m harmonium_lab.backing.wjazzd_subsets                    # manifeste + les quatre sous-ensembles
    python -m harmonium_lab.backing.wjazzd_subsets --subset BALLAD    # un seul (option répétable), sans manifeste
    python -m harmonium_lab.backing.wjazzd_subsets --manifest         # manifeste seul (champ `l2_subset`)
    python -m harmonium_lab.backing.wjazzd_subsets --summary          # tableau lisible des JSON déjà écrits

Sorties : `references/wjazzd-<ballad|twobeat|latin|funk>/{measures-bass.json,README.md}`. Le README est
écrit par ce module à partir du JSON (mêmes nombres) ; `references/wjazzd-swing/` (E7) n'est jamais touché.

## Ce qui est réutilisé d'E7 (`bass_measures`), sans copie

Lecture solo par solo (`read_solo_data`), suites de mesures valides, accumulateur `_Acc` et
`group_summary` : arrivées, approches, passages, intervalles, registre, rythme harmonique, tempos,
formes, longueurs de chorus. Une mesure est valide si elle est en 4/4, à quatre temps, avec une
basse complète et un accord connu (`NC` et symboles non analysés : écartés). Les sorties d'E7 ne changent pas.

## Ce que ce module ajoute

- **Sous-ensemble** : `solo_info.rhythmfeel` EXACT (`BALLAD`, `TWOBEAT`, `LATIN`, `FUNK`). Les valeurs
  composées (`LATIN/FUNK`, `LATIN/SWING`, `FUNK/SWING`, `A:LATIN/B:SWING`) n'appartiennent à aucun sous-ensemble
  (comptées dans le README) ; le champ `l2_subset` du manifeste vaut le nom du sous-ensemble, ou `null`.
- **Mesures écartées** : parts de mesures (toutes signatures confondues) en signature autre que 4/4,
  incomplètes, sans basse, sans accord utilisable, valides. Les solos sans accord (`form = 'open'`) donnent
  des mesures « sans accord » : elles sont comptées, pas devinées.
- **Signatures** : solos par signature du solo, solos et mesures touchés par une autre signature que 4/4
  (le lecteur d'E7 les écarte : 6/8, 9/4, 5/4, 3/4…).
- **Rythme de la basse** (`bass_rhythm`) : `bass_pitch` n'a qu'**une valeur par temps** (noire). On mesure
  ce qui s'observe : motif des répétitions de hauteur d'un temps au suivant dans la mesure (`bar_pattern`),
  longueur des suites de temps à hauteur identique (`hold_beats`, 1 = noire, 2 = blanche, 3, 4+, à travers
  les barres de mesure), attache sur la barre de mesure (`bar_tie` : dernier temps = 1ᵉʳ temps de la mesure
  suivante). **Les croches ne sont pas observables** à cette résolution : rien n'en est déduit. Une hauteur
  répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les distingue pas.
  Les huit motifs sont les huit combinaisons d'égalités (t1=t2, t2=t3, t3=t4) : `quarters` aucune égalité,
  `quarters_half` t3=t4, `quarter_half_quarter` t2=t3, `quarter_dotted_half` t2=t3=t4, `half_quarters` t1=t2,
  `halves` t1=t2 et t3=t4, `dotted_half_quarter` t1=t2=t3, `whole` quatre temps égaux. Ils couvrent tous les cas
  (pas de classe `other`).
- **Classes de tempo** (`avgtempo`) : `tempo_lt120` (< 120), `tempo_120_180`, `tempo_180_240`, `tempo_ge240`
  (≥ 240 BPM), plus `all`. Chaque groupe porte ses effectifs de solos et de mesures.
- **Intervalles de confiance à 95 %** (`indicators`) : bootstrap **par solo** (on rééchantillonne les solos,
  jamais les mesures, corrélées au sein d'un solo), `BOOTSTRAP_RESAMPLES` = 2000 rééchantillons, graine fixe
  dérivée de `sous-ensemble/groupe/indicateur`, somme des numérateurs / somme des dénominateurs sur le
  rééchantillon (médiane et p90 : centile du pool des intervalles). On ne rééchantillonne que les solos qui
  ont au moins un événement de l'indicateur. 0 ou 1 tel solo : pas d'IC (`null` et `ci_reason`). Intervalle
  = centiles 2,5 et 97,5 des statistiques rééchantillonnées (méthode des percentiles : optimiste quand il y a
  peu de solos, voir `limits`).
- **Fiabilité** : verdict `assez` / `juste` / `trop peu` par groupe, à seuils écrits (`RELIABILITY`).
- **Durée** : minutes de mesures valides = somme sur les solos de `mesures valides × 4 temps / avgtempo`
  (BPM, la noire est le temps). Contrôle indépendant : étendue des `onset` (secondes) de toutes les mesures.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import random
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import wjazzd
from ._util import counts_and_shares, percentile, share, write_json
from .bass_measures import (BEATS, PASSING_CLASSES, BassRun, ParseStats, SoloData, group_summary, measure_runs,
                            read_solo_data)
from .chords import Chord

SUBSETS = wjazzd.L2_SUBSETS
SLUGS = {name: f"wjazzd-{name.lower()}" for name in SUBSETS}
REFERENCES = wjazzd.REPO / "references"
OUTPUT_NAME = "measures-bass.json"
README_NAME = "README.md"
COMMAND = "python -m harmonium_lab.backing.wjazzd_subsets"

# Classes de tempo (BPM, borne haute exclue) : celles de la phase 019.
TEMPO_CLASSES: tuple[tuple[str, float, float], ...] = (
    ("tempo_lt120", 0.0, 120.0),
    ("tempo_120_180", 120.0, 180.0),
    ("tempo_180_240", 180.0, 240.0),
    ("tempo_ge240", 240.0, float("inf")),
)

PATTERN_KEYS = ("quarters", "quarters_half", "quarter_half_quarter", "quarter_dotted_half",
                "half_quarters", "halves", "dotted_half_quarter", "whole")
# (t1=t2, t2=t3, t3=t4) → motif ; les huit cas sont couverts.
_PATTERN_OF = {
    (False, False, False): "quarters", (False, False, True): "quarters_half",
    (False, True, False): "quarter_half_quarter", (False, True, True): "quarter_dotted_half",
    (True, False, False): "half_quarters", (True, False, True): "halves",
    (True, True, False): "dotted_half_quarter", (True, True, True): "whole",
}
HOLD_KEYS = ("1", "2", "3", "4+")
DISTINCT_KEYS = ("1", "2", "3", "4")
TRANSITION_KEYS = ("1-2", "2-3", "3-4")

BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = "wjazzd-subsets-v1"
CI_LEVEL = 95

# Seuils de fiabilité : (solos AVEC mesures valides, mesures valides). Un solo est l'unité de rééchantillonnage
# (les mesures d'un solo sont corrélées) : la précision d'une part tient surtout au nombre de solos. Ordre de
# grandeur (E7 : la part d'arrivées sur la basse varie d'un solo à l'autre avec un écart-type d'environ 0,2) :
# demi-largeur de l'IC ≈ 1,96 × 0,2 / √n solos → n = 20 : ± 0,09 ; n = 8 : ± 0,14 ; n = 4 : ± 0,20.
# `assez` : part lisible à ± 9 points ou mieux ; `juste` : à ± 14 points (ordre de grandeur seulement) ; moins :
# `trop peu` (la part n'est pas distinguable d'une autre à l'œil). Les mesures évitent qu'une poignée de
# solos très courts passe pour assez.
RELIABILITY: dict[str, dict[str, int]] = {
    "assez": {"min_solos": 20, "min_bars": 1500},
    "juste": {"min_solos": 8, "min_bars": 500},
}
VERDICTS = ("assez", "juste", "trop peu")

LIMITS = (
    "Les croches ne sont PAS observables : `bass_pitch` n'a qu'une valeur par temps (une noire) ; aucune "
    "durée, aucune attaque, aucun silence de basse n'est dans la base. Le rythme de la basse se limite aux "
    "répétitions de hauteur d'un temps au suivant, aux suites de temps à hauteur identique et à l'attache sur "
    "la barre de mesure.",
    "Une hauteur répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les "
    "distingue pas. `halves` = deux blanches OU deux paires de noires répétées.",
    "Peu de solos par sous-ensemble (10 à 32) et par classe de tempo : les intervalles de confiance (bootstrap "
    "par solo, méthode des percentiles) sont larges et, avec moins de quelques solos, trop optimistes ; ils ne "
    "disent rien du biais de sélection de la base (choix des solos, solistes, morceaux).",
    "La basse annotée est peu cohérente avec la grille d'accords (voir E7, `bass_measures` : la basse de "
    "l'accord n'est jouée qu'à 41 % des changements d'accord en swing) : les parts d'arrivée sont celles de "
    "l'annotation, pas celles d'une marche idéale.",
    "Mesures hors 4/4, sans basse complète ou sans accord utilisable écartées (voir `discarded`) ; les "
    "intervalles et les approches ne franchissent jamais une mesure écartée. Les suites de temps à hauteur "
    "identique sont tronquées aux bords des suites de mesures valides.",
    "Aucune phrase de solo, aucune suite de notes n'est conservée : uniquement des comptes, parts et centiles.",
)


# ── Statistiques ─────────────────────────────────────────────────────────

def percentile_of_counts(counts: Mapping[int, int], q: float) -> float | None:
    """Centile `q` d'une série donnée en `{valeur: effectif}` (même interpolation que `_util.percentile`)."""
    total = sum(counts.values())
    if not total:
        return None
    keys = sorted(k for k, v in counts.items() if v)
    cum: list[int] = []
    running = 0
    for k in keys:
        running += counts[k]
        cum.append(running)
    pos = (total - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    a = keys[bisect.bisect_right(cum, lo)]
    b = keys[bisect.bisect_right(cum, hi)]
    return a + (b - a) * (pos - lo)


def bootstrap_ci(items: Sequence[Any], statistic: Any, seed: str, resamples: int = BOOTSTRAP_RESAMPLES,
                 level: int = CI_LEVEL) -> tuple[float, float]:
    """IC par les centiles du bootstrap : `items` = un élément par solo, `statistic(liste d'éléments)`.

    Déterministe : générateur propre à `seed` (chaîne), aucune autre source d'aléa. `items` non vide."""
    rng = random.Random(seed)
    n = len(items)
    values = []
    for _ in range(resamples):
        values.append(statistic([items[rng.randrange(n)] for _ in range(n)]))
    alpha = (100 - level) / 2
    return percentile(values, alpha), percentile(values, 100 - alpha)


def _ratio(items: Sequence[tuple[int, int]]) -> float:
    return sum(n for n, _ in items) / sum(d for _, d in items)


def _pooled_quantile(q: float):
    def statistic(items: Sequence[Counter]) -> float:
        pool: Counter = Counter()
        for c in items:
            pool.update(c)
        return percentile_of_counts(pool, q) or 0.0
    return statistic


# ── Rythme de la basse ───────────────────────────────────────────────────

@dataclass
class _Rhythm:
    """Comptes bruts du rythme de la basse (au temps seulement)."""
    bars: int = 0
    patterns: Counter = field(default_factory=Counter)
    distinct: Counter = field(default_factory=Counter)
    transitions: Counter = field(default_factory=Counter)  # répétitions par position : "1-2", "2-3", "3-4"
    holds: Counter = field(default_factory=Counter)  # longueurs des suites de temps à hauteur identique
    hold_beats: int = 0
    tie_boundaries: int = 0
    tied: int = 0

    def add_run(self, run: BassRun) -> None:
        line: list[int] = []
        for bar in run.bars:
            p = [b.pitch for b in bar.beats]
            eq = (p[0] == p[1], p[1] == p[2], p[2] == p[3])
            self.bars += 1
            self.patterns[_PATTERN_OF[eq]] += 1
            self.distinct[str(len(set(p)))] += 1
            for key, same in zip(TRANSITION_KEYS, eq):
                if same:
                    self.transitions[key] += 1
            line.extend(p)
        for a, b in zip(range(BEATS - 1, len(line) - 1, BEATS), range(BEATS, len(line), BEATS)):
            self.tie_boundaries += 1
            self.tied += line[a] == line[b]
        length = 0
        for i, pitch in enumerate(line):
            length += 1
            if i + 1 == len(line) or line[i + 1] != pitch:
                self.holds[str(length) if length < 4 else "4+"] += 1
                self.hold_beats += length
                length = 0

    def summary(self) -> dict[str, Any]:
        holds = counts_and_shares(self.holds, HOLD_KEYS)
        n_notes = holds["n"]
        held = self.hold_beats - self.holds["1"]
        return {
            "bars": self.bars,
            "bar_pattern": counts_and_shares(self.patterns, PATTERN_KEYS),
            "distinct_pitches_per_bar": counts_and_shares(self.distinct, DISTINCT_KEYS),
            "repeat_by_transition": {"n_bars": self.bars,
                                     "counts": {k: int(self.transitions[k]) for k in TRANSITION_KEYS},
                                     "shares": {k: share(self.transitions[k], self.bars) for k in TRANSITION_KEYS}},
            "hold_beats": {**holds, "mean": round(self.hold_beats / n_notes, 3) if n_notes else None,
                           "beats": self.hold_beats,
                           "share_beats_in_holds": share(held, self.hold_beats)},
            "bar_tie": {"n": self.tie_boundaries, "tied": self.tied, "share": share(self.tied, self.tie_boundaries)},
        }


def measure_rhythm(runs: Sequence[BassRun]) -> _Rhythm:
    """Rythme de la basse (au temps) sur des suites de mesures valides."""
    acc = _Rhythm()
    for run in runs:
        if run.bars:
            acc.add_run(run)
    return acc


def interval_counter(runs: Sequence[BassRun]) -> Counter:
    """Effectifs des |Δ| (demi-tons) entre temps consécutifs d'une suite, valeurs exactes."""
    counts: Counter = Counter()
    for run in runs:
        line = [b.pitch for bar in run.bars for b in bar.beats]
        counts.update(abs(b - a) for a, b in zip(line, line[1:]))
    return counts


# ── Faits d'un solo hors lecteur E7 ──────────────────────────────────────

_YEAR = re.compile(r"(?:19|20)\d\d")
NO_SIGNATURE = "(vide)"


@dataclass
class SoloFacts:
    """`SoloData` d'E7 et ce que le lecteur écarte ou ne lit pas : autres signatures, année, durée."""
    data: SoloData
    bars_other: dict[str, int]  # signature effective (≠ 4/4) → nombre de mesures
    beats_all: int  # temps des mesures ≥ 1 d'un chorus, toutes signatures
    onset_span: float  # secondes entre le premier et le dernier de ces temps
    year: int | None

    @property
    def bars_non_4_4(self) -> int:
        return sum(self.bars_other.values())

    @property
    def bars_all(self) -> int:
        return self.data.bars_total + self.bars_non_4_4


def scan_solo(con: sqlite3.Connection, info: wjazzd.SoloInfo) -> tuple[dict[str, int], int, float]:
    """Mesures par signature effective ≠ 4/4, temps et étendue des onsets (mêmes règles de propagation que
    `wjazzd.read_solo` : signature du solo avant la première écrite, puis la dernière écrite)."""
    signature = info.signature
    other: dict[str, set[int]] = {}
    beats = 0
    first = last = None
    for bar, onset, sig, chorus in con.execute(
            "select bar, onset, signature, chorus_id from beats where melid = ? order by beatid", (info.melid,)):
        if sig:
            signature = sig
        if bar <= 0 or chorus <= 0:
            continue
        beats += 1
        if onset is not None:
            first = onset if first is None else first
            last = onset
        if signature != wjazzd.SIGNATURE:
            other.setdefault(signature or NO_SIGNATURE, set()).add(bar)
    return {k: len(v) for k, v in sorted(other.items())}, beats, round(last - first, 3) if first is not None else 0.0


def recording_year(con: sqlite3.Connection, info: wjazzd.SoloInfo) -> int | None:
    """Année de `track_info.recordingdate` (formats divers : première année à quatre chiffres), sinon `None`."""
    if info.trackid is None:
        return None
    row = con.execute("select recordingdate from track_info where trackid = ?", (info.trackid,)).fetchone()
    match = _YEAR.search(row[0] or "") if row else None
    return int(match.group()) if match else None


def read_subset(con: sqlite3.Connection, subset: str, cache: dict[str, tuple[Chord | None, bool]],
                parse: ParseStats) -> list[SoloFacts]:
    """Tous les solos de `rhythmfeel = subset` (valeur exacte), triés par `melid`."""
    facts = []
    for info in wjazzd.list_solos(con, subset):
        data = read_solo_data(con, info, cache, parse)
        other, beats_all, span = scan_solo(con, info)
        facts.append(SoloFacts(data, other, beats_all, span, recording_year(con, info)))
    return facts


def tempo_class(tempo: float | None) -> str | None:
    """Classe de tempo (`None` si `avgtempo` est inconnu)."""
    if tempo is None:
        return None
    return next((name for name, lo, hi in TEMPO_CLASSES if lo <= tempo < hi), None)


# ── Indicateurs avec IC ──────────────────────────────────────────────────

def _ratio_parts(summary: Mapping[str, Any], rhythm: Mapping[str, Any]) -> dict[str, tuple[int, int]]:
    """(numérateur, dénominateur) de chaque indicateur-part d'un solo ou d'un groupe."""
    parts: dict[str, tuple[int, int]] = {}
    change = summary["arrival"]["change"]
    parts["arrival_bass_at_change"] = (change["counts"]["bass"], change["n"])
    for ctx in ("bar_change", "all"):
        weights = summary["approach"][ctx]["weights"]
        for key in ("none", "chromatic", "diatonic"):
            parts[f"approach_{key}_{ctx}"] = (weights["counts"][key], weights["n"])
    passage = summary["passage"]
    for key in PASSING_CLASSES:
        parts[f"passage_{key}"] = (passage["counts"][key], passage["n"])
    intervals = summary["intervals"]
    parts["repeat_share"] = (intervals["counts"]["0"], intervals["n"])
    patterns = rhythm["bar_pattern"]
    parts["bars_quarters"] = (patterns["counts"]["quarters"], patterns["n"])
    parts["bars_halves"] = (patterns["counts"]["halves"], patterns["n"])
    chords = summary["harmonic_rhythm"]["chords_per_bar"]
    parts["bars_one_chord"] = (chords["counts"]["1"], chords["n"])
    return parts


RATIO_INDICATORS = ("arrival_bass_at_change",
                    "approach_none_bar_change", "approach_chromatic_bar_change", "approach_diatonic_bar_change",
                    "approach_none_all", "approach_chromatic_all", "approach_diatonic_all",
                    "passage_chord_tone", "passage_scale_step", "passage_chromatic",
                    "repeat_share", "bars_quarters", "bars_halves", "bars_one_chord")
QUANTILE_INDICATORS = {"interval_median": 50, "interval_p90": 90}

INDICATOR_LABELS = {
    "arrival_bass_at_change": "arrivée sur la basse de l'accord au changement",
    "approach_none_bar_change": "approche 4ᵉ temps (changement à la barre) : aucune",
    "approach_chromatic_bar_change": "approche 4ᵉ temps (changement à la barre) : chromatique",
    "approach_diatonic_bar_change": "approche 4ᵉ temps (changement à la barre) : diatonique",
    "approach_none_all": "approche (tous contextes) : aucune",
    "approach_chromatic_all": "approche (tous contextes) : chromatique",
    "approach_diatonic_all": "approche (tous contextes) : diatonique",
    "passage_chord_tone": "note de passage : note d'accord",
    "passage_scale_step": "note de passage : degré de gamme",
    "passage_chromatic": "note de passage : chromatique",
    "repeat_share": "intervalles : répétitions (Δ = 0)",
    "interval_median": "intervalle médian (demi-tons, valeur absolue)",
    "interval_p90": "intervalle p90 (demi-tons, valeur absolue)",
    "bars_quarters": "mesures `quarters` (aucune répétition)",
    "bars_halves": "mesures `halves` (t1=t2, t3=t4)",
    "bars_one_chord": "mesures à un seul accord",
}


def indicators(subset: str, group: str, solos: Sequence[SoloData]) -> dict[str, Any]:
    """Indicateurs clés d'un groupe, estimation poolée + IC à 95 % (bootstrap par solo) et effectifs."""
    per_solo = []
    for s in solos:
        if not s.runs:
            continue
        summary = measure_runs(s.runs)
        per_solo.append((_ratio_parts(summary, measure_rhythm(s.runs).summary()), interval_counter(s.runs)))
    out: dict[str, Any] = {}

    def entry(name: str, estimate: float | None, items: list, statistic: Any, n_events: int) -> dict[str, Any]:
        block: dict[str, Any] = {"estimate": None if estimate is None else round(estimate, 4),
                                 "ci95": None, "ci_reason": None, "n_events": n_events, "n_solos": len(items)}
        if len(items) == 0:
            block["ci_reason"] = "aucun solo avec événement"
        elif len(items) == 1:
            block["ci_reason"] = "un seul solo avec événement : rééchantillonnage par solo impossible"
        else:
            lo, hi = bootstrap_ci(items, statistic, f"{BOOTSTRAP_SEED}/{subset}/{group}/{name}")
            block["ci95"] = [round(lo, 4), round(hi, 4)]
        return block

    for name in RATIO_INDICATORS:
        items = [parts[name] for parts, _ in per_solo if parts[name][1] > 0]
        den = sum(d for _, d in items)
        out[name] = entry(name, sum(n for n, _ in items) / den if den else None, items, _ratio, den)
    pooled: Counter = Counter()
    for _, counter in per_solo:
        pooled.update(counter)
    items_c = [counter for _, counter in per_solo if counter]
    for name, q in QUANTILE_INDICATORS.items():
        out[name] = entry(name, percentile_of_counts(pooled, q), items_c, _pooled_quantile(q), sum(pooled.values()))
    return out


# ── Fiabilité ────────────────────────────────────────────────────────────

def verdict(n_solos: int, n_bars: int) -> str:
    """`assez` / `juste` / `trop peu` selon `RELIABILITY` (solos avec mesures valides ET mesures valides)."""
    for name in ("assez", "juste"):
        rule = RELIABILITY[name]
        if n_solos >= rule["min_solos"] and n_bars >= rule["min_bars"]:
            return name
    return "trop peu"


def _median_ci_width(indicator_block: Mapping[str, Any]) -> float | None:
    widths = [b["ci95"][1] - b["ci95"][0] for k, b in indicator_block.items()
              if k in RATIO_INDICATORS and b["ci95"] is not None]
    return round(percentile(widths, 50), 4) if widths else None


# ── Un groupe, un sous-ensemble ──────────────────────────────────────────

def discarded(members: Sequence[SoloFacts]) -> dict[str, Any]:
    """Mesures (toutes signatures) : valides et écartées, par motif (un seul motif par mesure)."""
    counts = {
        "bars_all": sum(f.bars_all for f in members),
        "non_4_4": sum(f.bars_non_4_4 for f in members),
        "incomplete": sum(f.data.bars_incomplete for f in members),
        "no_bass": sum(f.data.bars_no_bass for f in members),
        "no_chord": sum(f.data.bars_no_chord for f in members),
        "valid": sum(f.data.bars_valid for f in members),
    }
    total = counts["bars_all"]
    return {"counts": counts,
            "shares": {k: share(v, total) for k, v in counts.items() if k != "bars_all"},
            "order_of_exclusion": "signature ≠ 4/4, puis mesure incomplète (≠ 4 temps), puis basse manquante, "
                                  "puis accord absent / NC / non analysé : un seul motif par mesure",
            "solos_without_valid_bar": sum(1 for f in members if not f.data.bars_valid)}


def duration(members: Sequence[SoloFacts]) -> dict[str, Any]:
    """Durée en minutes : mesures × 4 temps / avgtempo (BPM), plus le contrôle par les `onset`."""
    def minutes(bars: int, tempo: float | None) -> float:
        return bars * BEATS / tempo if tempo else 0.0

    valid = sum(minutes(f.data.bars_valid, f.data.info.avgtempo) for f in members)
    bars_4_4 = sum(minutes(f.data.bars_total, f.data.info.avgtempo) for f in members)
    beats = sum(f.beats_all / f.data.info.avgtempo for f in members if f.data.info.avgtempo)
    return {
        "method": "minutes = mesures × 4 temps / avgtempo du solo (BPM, la noire est le temps), sommées sur les solos",
        "minutes_valid_bars": round(valid, 2),
        "minutes_4_4_bars": round(bars_4_4, 2),
        "minutes_all_beats_at_avgtempo": round(beats, 2),
        "minutes_onset_span": round(sum(f.onset_span for f in members) / 60.0, 2),
        "check": "`minutes_onset_span` = étendue des onsets (s) du 1ᵉʳ au dernier temps de mesure ≥ 1 d'un chorus, "
                 "toutes signatures ; à comparer à `minutes_all_beats_at_avgtempo` (temps / avgtempo)",
    }


def choruses(members: Sequence[SoloFacts]) -> dict[str, Any]:
    """Chorus : identifiants vus dans les mesures 4/4 ; `kept` exclut le dernier chorus (peut être tronqué)."""
    counts = [len(f.data.chorus_bars) for f in members]
    return {"total_4_4": sum(counts), "complete_kept": sum(n - 1 if n > 1 else n for n in counts)}


def group_doc(subset: str, name: str, members: Sequence[SoloFacts]) -> dict[str, Any]:
    """Un groupe de solos : critères d'E7, rythme de la basse, rejets, durée, indicateurs avec IC, fiabilité."""
    solos = [f.data for f in members]
    doc = group_summary(solos)
    runs = [run for s in solos for run in s.runs]
    doc["bass_rhythm"] = measure_rhythm(runs).summary()
    doc["discarded"] = discarded(members)
    doc["duration"] = duration(members)
    doc["choruses"] = choruses(members)
    open_bars = sum(f.data.bars_valid for f in members if f.data.info.comp_form == "open")
    doc["open_form"] = {"solos": sum(1 for f in members if f.data.info.comp_form == "open"),
                        "bars_valid": open_bars, "share_of_valid_bars": share(open_bars, doc["counts"]["bars_valid"]),
                        "note": "`composition_info.form = 'open'` : improvisation sur vamp (peu de symboles d'accord, "
                                "propagés sur tout le solo) ; ses mesures sont valides et comptées"}
    doc["indicators"] = indicators(subset, name, solos)
    n_solos = doc["counts"]["solos_with_bars"]
    n_bars = doc["counts"]["bars_valid"]
    doc["reliability"] = {"verdict": verdict(n_solos, n_bars), "solos_with_valid_bars": n_solos,
                          "bars_valid": n_bars, "median_ci_width_shares": _median_ci_width(doc["indicators"])}
    return doc


def _signatures(members: Sequence[SoloFacts]) -> dict[str, Any]:
    by_solo = Counter(f.data.info.signature or NO_SIGNATURE for f in members)
    bars_other: Counter = Counter()
    solos_per_signature: Counter = Counter()
    for f in members:
        for sig, n in f.bars_other.items():
            bars_other[sig] += n
            solos_per_signature[sig] += 1
    return {
        "solo_signature": dict(sorted(by_solo.items())),
        "non_4_4": {"solos_touched": sum(1 for f in members if f.bars_other),
                    "solos_without_any_4_4_bar": sum(1 for f in members if not f.data.bars_total),
                    "bars": sum(bars_other.values()),
                    "bars_by_signature": dict(sorted(bars_other.items())),
                    "solos_by_signature": dict(sorted(solos_per_signature.items())),
                    "melids_touched": sorted(f.data.info.melid for f in members if f.bars_other)},
        "solo_label_overridden_by_beats": sorted(
            f.data.info.melid for f in members
            if f.data.info.signature not in ("", wjazzd.SIGNATURE) and f.data.bars_total),
        "rule": "signature effective d'un temps = dernière signature écrite (celle du solo avant la première) ; "
                "seules les mesures en 4/4 sont lues (voir `wjazzd`)",
    }


def _years(members: Sequence[SoloFacts]) -> dict[str, Any]:
    years = [f.year for f in members if f.year is not None]
    decades = Counter(f"{y // 10 * 10}s" for y in years)
    return {"known": len(years), "unknown": len(members) - len(years),
            "min": min(years) if years else None, "max": max(years) if years else None,
            "by_decade": dict(sorted(decades.items())),
            "source": "`track_info.recordingdate` (année extraite du texte)"}


def composite_count(con: sqlite3.Connection) -> dict[str, int]:
    """Solos de `rhythmfeel` composé (contenant `/`), hors de tous les sous-ensembles."""
    return {k: n for k, n in con.execute(
        "select rhythmfeel, count(*) from solo_info where rhythmfeel like '%/%' group by rhythmfeel order by 1")}


def build_subset(subset: str, db: Path = wjazzd.RAW_DB, expected: str = wjazzd.SHA256,
                 command: str | None = None) -> dict[str, Any]:
    """Document `measures-bass.json` d'un sous-ensemble (déterministe ; SHA256 vérifié avant lecture)."""
    con = wjazzd.open_db(db, expected)
    try:
        cache: dict[str, tuple[Chord | None, bool]] = {}
        parse = ParseStats()
        members = read_subset(con, subset, cache, parse)
        composite = composite_count(con)
        other_feel = {k: n for k, n in con.execute(
            "select rhythmfeel, count(*) from solo_info group by rhythmfeel order by 1")}
    finally:
        con.close()
    groups: dict[str, list[SoloFacts]] = {"all": list(members)}
    for cls, _, _ in TEMPO_CLASSES:
        groups[cls] = [f for f in members if tempo_class(f.data.info.avgtempo) == cls]
    docs = {name: group_doc(subset, name, g) for name, g in groups.items()}
    total = docs["all"]
    return {
        "command": command or f"{COMMAND} --subset {subset}",
        "provenance": {
            "source": "Weimar Jazz Database (WJazzD)",
            "version": wjazzd.VERSION_LABEL,
            "sha256": expected,
            "licence": wjazzd.LICENCE,
            "attribution": wjazzd.ATTRIBUTION,
            "subset": f"solo_info.rhythmfeel = '{subset}' (valeur exacte) ; mesures 4/4 de chorus (bar >= 1) à "
                      "quatre temps, basse complète et accord connu (NC et symboles non analysés écartés)",
            "rhythmfeel": subset,
            "n_solos": total["counts"]["solos"],
            "n_bars": total["discarded"]["counts"]["bars_all"],
            "n_bars_valid": total["counts"]["bars_valid"],
            "n_beats_valid": total["counts"]["beats_valid"],
            "rhythmfeel_values_in_db": other_feel,
            "composite_rhythmfeel_excluded": {"values": composite, "n_solos": sum(composite.values())},
        },
        "limits": list(LIMITS),
        "tempo_classes": [{"id": name, "min_bpm": lo, "max_bpm": None if hi == float("inf") else hi}
                          for name, lo, hi in TEMPO_CLASSES],
        "bootstrap": {"unit": "solo", "resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED,
                      "level": CI_LEVEL, "method": "centiles 2,5 / 97,5 de la statistique rééchantillonnée ; "
                      "ratio = somme des numérateurs / somme des dénominateurs ; n solos avec événement < 2 : "
                      "pas d'IC"},
        "signatures": _signatures(members),
        "recording_years": _years(members),
        "chord_parsing": parse.summary(),
        "reliability": {
            "thresholds": {**RELIABILITY, "unit": "solos avec au moins une mesure valide ET mesures valides ; "
                                                   "`trop peu` sous `juste`"},
            "verdict": total["reliability"]["verdict"],
            "by_group": {name: d["reliability"]["verdict"] for name, d in docs.items()},
            "solos_in_tempo_classes": sum(d["counts"]["solos"] for n, d in docs.items() if n != "all"),
            "solos_without_tempo": sum(1 for f in members if tempo_class(f.data.info.avgtempo) is None),
        },
        "groups": docs,
    }


# ── Manifeste ────────────────────────────────────────────────────────────

def write_manifest(db: Path = wjazzd.RAW_DB, corpus_dir: Path = wjazzd.CORPUS_DIR,
                   expected: str = wjazzd.SHA256) -> list[dict[str, Any]]:
    """`manifest.jsonl` (champ `l2_subset`) et `VERSION` : `wjazzd.write_manifest` sur `corpus_dir`."""
    return wjazzd.write_manifest(db, corpus_dir / "manifest.jsonl", corpus_dir / "VERSION", expected)


# ── Rendu lisible ────────────────────────────────────────────────────────

def fr(value: float | None, digits: int = 1) -> str:
    """Nombre à la française (virgule) ; `—` si absent."""
    return "—" if value is None else f"{value:.{digits}f}".replace(".", ",")


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.0f} %"


_GROUP_LABELS = {"all": "tous", "tempo_lt120": "< 120", "tempo_120_180": "120–180",
                 "tempo_180_240": "180–240", "tempo_ge240": "≥ 240"}


def group_label(name: str) -> str:
    """Libellé lisible d'un groupe (BPM pour les classes de tempo)."""
    return _GROUP_LABELS.get(name, name)


def cell(block: Mapping[str, Any], percent: bool = True) -> str:
    """`est [lo–hi]` d'un indicateur (`n/a` si aucun événement)."""
    if block["estimate"] is None:
        return "n/a"
    fmt = pct if percent else (lambda v: fr(v, 1))
    text = fmt(block["estimate"])
    if block["ci95"] is not None:
        text += f" [{fmt(block['ci95'][0]).replace(' %', '')}–{fmt(block['ci95'][1])}]"
    else:
        text += " [pas d'IC]"
    return text


def summary_text(doc: Mapping[str, Any], group_names: Sequence[str] | None = None) -> str:
    """Tableau lisible d'un `measures-bass.json` de sous-ensemble."""
    prov = doc["provenance"]
    out = [f"{prov['rhythmfeel']} — {prov['n_solos']} solos, {prov['n_bars']} mesures "
           f"({prov['n_bars_valid']} valides), verdict {doc['reliability']['verdict']}"]
    for name in group_names or doc["groups"]:
        g = doc["groups"][name]
        if not g["counts"]["solos"]:
            out.append("")
            out.append(f"== {name} : aucun solo ==")
            continue
        c, d = g["counts"], g["discarded"]["counts"]
        out.append("")
        out.append(f"== {name} : {c['solos']} solos ({c['solos_with_bars']} avec mesures), {c['bars_valid']} mesures "
                   f"valides sur {d['bars_all']}, {g['duration']['minutes_valid_bars']} min — "
                   f"{g['reliability']['verdict']} ==")
        for key in (*RATIO_INDICATORS, *QUANTILE_INDICATORS):
            block = g["indicators"][key]
            percent = key not in QUANTILE_INDICATORS
            out.append(f"  {INDICATOR_LABELS[key]:<62} {cell(block, percent):<22} n={block['n_events']} "
                       f"solos={block['n_solos']}")
        r = g["bass_rhythm"]
        out.append("  motifs de mesure : " + "  ".join(
            f"{k}={pct(r['bar_pattern']['shares'][k])}" for k in PATTERN_KEYS))
    return "\n".join(out)


# ── README ───────────────────────────────────────────────────────────────

# Constats propres à chaque sous-ensemble, relevés sur la base réelle (voir le JSON pour les nombres) ; les
# comparaisons au swing citent `references/wjazzd-swing/measures-bass.json` (E7) : arrivée sur la basse de
# l'accord au changement 41 %, répétitions 20 %, mesures à un accord 76 %, passages sur note d'accord 48 %.
SUBSET_NOTES: dict[str, dict[str, tuple[str, ...]]] = {
    "BALLAD": {
        "limits": (
            "Dix solos de 7 solistes (Murray ×3 et Pepper ×2 font la moitié), tous à 48,8–67,7 BPM : une seule "
            "classe de tempo (`< 120`) est peuplée, les trois autres sont vides ; rien sur les ballades à 70–100 BPM.",
            "Le solo `Sweet Sorrow` (melid 246) est étiqueté 6/8 au niveau du solo, mais ses temps écrivent 4/4 "
            "(quatre temps par mesure, à `avgtempo`) : le lecteur E7 le lit en 4/4 (36 mesures) ; il n'a AUCUNE basse "
            "annotée, donc aucune mesure valide (ses 36 mesures sont toutes les mesures « sans basse » du sous-ensemble). "
            "Il n'y a donc en pratique que 9 solos exploitables et aucune mesure réellement en 6/8. Un solo a "
            "2 mesures en 5/4 (écartées).",
            "Trop peu de mesures (294, 20 min) pour toute part conditionnelle (par contexte d'approche, par temps) ; "
            "les IC par solo sur 8–9 solos restent larges (arrivée sur la basse : 55 %, IC 42–70 %, compatible avec "
            "les 41 % du swing : on ne peut pas dire que la ballade diffère).",
            "Enregistrements de 1945 à 1994 et styles mêlés (post-bop 6, cool 2, bebop 1, swing 1) : pas un style "
            "de ballade homogène.",
        ),
        "usable": (
            "Ordre de grandeur de la marche de basse d'une ballade lente : parts d'approche aucune / chromatique / "
            "diatonique, notes de passage (note d'accord largement majoritaire), répétitions de hauteur (24 %), "
            "intervalle médian de 2 demi-tons, p90 de 8, registre de 31 à 51 (MIDI, p1–p99).",
            "Rythme harmonique : 61 % de mesures à un accord, 32 % à deux (le changement tombe surtout au 1ᵉʳ ou au "
            "3ᵉ temps).",
            "NON exploitable : les effectifs ne permettent aucun réglage par classe de tempo ni par forme ; les "
            "valeurs sont des indications, pas des cibles de test.",
        ),
    },
    "TWOBEAT": {
        "limits": (
            "Non représentatif d'un « 2 temps » moderne : les 32 solos sont tous de style `TRADITIONAL`, de 8 solistes "
            "(trompette/cornet, trombone, clarinette, saxophone soprano : Armstrong, Beiderbecke, Bechet, Dodds, Ory, "
            "Higginbotham, Allen, Shavers) ; 24 enregistrés en 1925–1928, 2 en 1938, 6 en 1941. `record_info.releasedate` "
            "(2007 pour 18 solos) date les publications, pas les enregistrements : on lit `track_info.recordingdate`.",
            "La basse d'enregistrements acoustiques/anciens (tuba, contrebasse, sax basse) est difficile à transcrire : "
            "la basse annotée suit peu la grille (arrivée sur la basse de l'accord au changement 25 %, IC 18–33 %, "
            "contre 41 % en swing ; passages chromatiques 39 % contre 27 %). Cela peut venir de l'annotation autant "
            "que du style : la donnée ne permet pas de trancher.",
            "Le « balancement à deux temps » ne se lit pas clairement au temps : seulement 10 % de mesures `halves` "
            "(t1=t2, t3=t4) et 11 % de `whole`, alors que 29 % de mesures sont sans aucune répétition. Une basse à "
            "deux temps jouée en noires piquées ou en blanches n'est pas distinguable ici.",
            "Tempos de 70,6 à 273,6 BPM (médiane 183,85) ; les classes `< 120` (3 solos) et `≥ 240` (2 solos, 1 avec "
            "mesures) sont inutilisables, `120–180` (11 solos) et `180–240` (16 solos, 15 avec mesures) sont « trop peu ».",
        ),
        "usable": (
            "Seul sous-ensemble à 30 solos avec mesures : les parts globales (approche, répétitions 37 %, mesures à un "
            "accord 76 %) ont des IC raisonnables ; ils décrivent le jazz traditionnel années 1920–40, pas un style "
            "à imiter tel quel.",
            "Utile comme contraste (basse plus statique : notes répétées plus fréquentes, 37 % contre 20 % en swing) avec le "
            "swing, à condition de garder à l'esprit l'incertitude d'annotation.",
            "NON exploitable : un réglage par tempo ; tout ce qui relève du caractère à deux temps (accent sur 1 et 3, "
            "notes piquées, ghost notes).",
        ),
    },
    "LATIN": {
        "limits": (
            "L'étiquette `LATIN` est celle du solo : la base ne distingue ni bossa nova, ni samba, ni afro-cubain ; "
            "14 solos post-bop, 8 cool, 4 hard bop, 1 bebop (1951–1997).",
            "4 solos sur 27 n'ont aucune mesure en 4/4 (trois en 3/4, un en 5/4) : 404 mesures, soit 20 % des mesures "
            "du sous-ensemble, sont écartées pour leur signature. Le groupe `< 120` ne compte donc qu'un solo "
            "avec mesures (39 mesures) et `≥ 240` un seul : inutilisables.",
            "Les figures caractéristiques de la basse latine (anticipations sur le « et » du 2 ou du 4, tumbao, "
            "clave) sont des CROCHES : non observables avec une note de basse par temps. Ce que l'on voit "
            "(repeat_share 38 %, mesures `whole` 16 %, `half_quarters` 19 %) est compatible avec des notes tenues "
            "ou répétées, mais n'établit pas un motif latin.",
            "Les 2 solos à forme `open` (vamp) sont en 3/4 : aucune mesure valide.",
        ),
        "usable": (
            "Plus gros sous-ensemble en mesures valides (1 639, environ 40 min) : parts globales exploitables comme "
            "cibles indicatives. La basse y est nettement plus alignée sur la grille qu'en swing : arrivée sur la "
            "basse de l'accord au changement 57 % (IC 46–68 %) contre 41 %, 87 % de mesures à un seul accord.",
            "Seule la classe `120–180` (14 solos, 887 mesures) atteint « juste » : à utiliser pour un latin "
            "mi-tempo ; `180–240` (7 solos) reste « trop peu ».",
            "NON exploitable : motifs rythmiques latins (croches), distinction bossa / samba, tempos lents ou "
            "très rapides.",
        ),
    },
    "FUNK": {
        "limits": (
            "8 solos sur 20 sont de forme `open` (improvisation sur vamp à 1–3 symboles d'accord pour tout le "
            "solo) : ils font 55 % des mesures valides. Leur accord est propagé, donc leurs mesures sont valides, "
            "mais ils gonflent la part de mesures à un seul accord (82 %) et ne donnent presque aucun changement "
            "d'accord : les parts « au changement » reposent sur 12 solos seulement.",
            "4 solos n'ont aucune mesure valide : 3 n'ont aucune mesure en 4/4 (deux en 9/4, un en 3/4 : 141 mesures "
            "non 4/4, 11,5 % du sous-ensemble) et `Pop Tune #1` (melid 82) n'a aucune basse annotée : ses 140 mesures "
            "sont toutes les mesures « sans basse » du sous-ensemble (11,5 %).",
            "Tempos de 84 à 159 BPM (médiane 117,8) : aucune mesure à 180 BPM ou plus, les deux classes hautes sont "
            "vides ; `< 120` (12 solos, 10 avec mesures) est « juste », `120–180` (8 solos dont 6 avec mesures) « trop peu ».",
            "Style `FUSION` pour les 20 solos, 1969–2009, de souffleurs (sax ténor 10, sax alto 5, trompette 5) sur des "
            "morceaux fusion/funk ; les syncopes d'une basse funk sont des croches ou doubles-croches : non observables ici.",
        ),
        "usable": (
            "Distribution globale des notes, intervalles (médiane 2, p90 10), registre et approches d'une basse "
            "jazz-fusion : indications avec IC larges (arrivée sur la basse au changement 45 %, IC 34–63 %).",
            "Les 12 solos à forme écrite et les 8 solos sur vamp peuvent être séparés au besoin à partir de "
            "`composition_form` du manifeste.",
            "NON exploitable : tout le caractère funk (syncopes en croches/doubles-croches, notes fantômes, "
            "répétitions rythmiques précises) ; un réglage par tempo.",
        ),
    },
}

GENERAL_USABLE = (
    "Exploitables : parts et centiles de la marche de basse au temps (arrivées, approches du 4ᵉ temps, notes de "
    "passage, intervalles, registre), rythme harmonique (accords par mesure), motifs de répétition de hauteur par "
    "mesure, tempos et formes, avec leurs IC par solo.",
    "Non exploitables : tout ce qui est plus fin que la noire (croches, anticipations, durées réelles des notes), "
    "les silences de basse, la dynamique et les timbres, les phrases ou suites de notes (non conservées).",
    "Un indicateur dont l'IC est absent ou très large (voir le tableau) ne sert pas de cible chiffrée.",
)


def _table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return lines


def readme_text(doc: Mapping[str, Any]) -> str:
    """README d'un dossier de sortie, écrit à partir du JSON (mêmes nombres)."""
    prov = doc["provenance"]
    subset = prov["rhythmfeel"]
    slug = SLUGS[subset]
    allg = doc["groups"]["all"]
    c, d = allg["counts"], allg["discarded"]
    sig = doc["signatures"]
    years = doc["recording_years"]
    notes = SUBSET_NOTES.get(subset, {})
    L: list[str] = []
    L.append(f"# {slug} : accompagnements `rhythmfeel = {subset}` de la Weimar Jazz Database (phase 019, L2)")
    L.append("")
    L.append("Mesures de la **marche de basse** et de son **rythme au temps** sur un sous-ensemble non swing de "
             "WJazzD, pour une bibliothèque de styles. Comptes, parts et centiles uniquement : aucune phrase de "
             "solo, aucune suite de notes n'est conservée (principe VII).")
    L.append("")
    L.append("## Provenance et licence")
    L.append("")
    L.append(f"- Source : {prov['source']}, {prov['version']}, SHA256 `{prov['sha256']}` (vérifié avant toute lecture).")
    L.append(f"- Licence : {prov['licence']}.")
    L.append(f"- Mention requise (ODbL §4.3) : « {prov['attribution']} »")
    L.append(f"- Sous-ensemble : {prov['subset']}.")
    L.append("- Les mesures dérivées sont des faits agrégés ; la base elle-même reste dans `corpus/wjazzd/raw/` "
             "(cache gitignoré). Manifeste des solos : `corpus/wjazzd/manifest.jsonl` (champ `l2_subset`).")
    L.append("")
    L.append("## Reproduction")
    L.append("")
    L.append("```bash")
    L.append(doc["command"])
    L.append("```")
    L.append("")
    L.append(f"Écrit `references/{slug}/{OUTPUT_NAME}` et ce `{README_NAME}` ; deux exécutions donnent des fichiers "
             f"identiques (clés triées, arrondis fixes, bootstrap à graine fixe `{doc['bootstrap']['seed']}`, "
             f"{doc['bootstrap']['resamples']} rééchantillons).")
    L.append("")
    L.append("## Effectifs")
    L.append("")
    comp = prov["composite_rhythmfeel_excluded"]
    L.append(f"- **{c['solos']} solos** `{subset}` (valeur exacte) ; {c['solos_with_bars']} ont au moins une mesure "
             f"valide. Hors sous-ensemble : {comp['n_solos']} solos à `rhythmfeel` composé "
             f"({', '.join(f'`{k}` {v}' for k, v in comp['values'].items())}).")
    L.append(f"- **{d['counts']['bars_all']} mesures** (chorus, toutes signatures) dont **{d['counts']['valid']} valides** "
             f"({c['beats_valid']} temps) ; **{fr(allg['duration']['minutes_valid_bars'])} min** de mesures valides "
             f"({fr(allg['duration']['minutes_4_4_bars'])} min de mesures 4/4). Méthode : {allg['duration']['method']}. "
             f"Contrôle sur tous les temps de chorus, toutes signatures : {fr(allg['duration']['minutes_all_beats_at_avgtempo'])} min à `avgtempo` contre "
             f"{fr(allg['duration']['minutes_onset_span'])} min (étendue des `onset`).")
    L.append(f"- **{allg['choruses']['total_4_4']} chorus** vus en 4/4 ({allg['choruses']['complete_kept']} sans le "
             f"dernier chorus de chaque solo, qui peut être tronqué) ; longueurs des chorus conservés (mesures×effectif) : "
             + (", ".join(f"{k}×{v}" for k, v in allg['structure']['chorus_length']['histogram'].items()) or "aucune")
             + ".")
    t = allg["structure"]["tempo"]
    L.append(f"- Tempos (`avgtempo`) : min {fr(t['min'])}, p25 {fr(t['p25'])}, médiane {fr(t['p50'])}, p75 {fr(t['p75'])}, "
             f"max {fr(t['max'])} BPM.")
    if years["known"]:
        L.append(f"- Enregistrements : {years['min']}–{years['max']} ({years['known']} dates lues, {years['unknown']} "
                 f"inconnues) ; par décennie : " + ", ".join(f"{k} ×{v}" for k, v in years["by_decade"].items()) + ".")
    L.append(f"- Signatures des solos : " + ", ".join(f"{k} ×{v}" for k, v in sig["solo_signature"].items())
             + f". Mesures non 4/4 (écartées par le lecteur E7) : {sig['non_4_4']['bars']} mesures dans "
             f"{sig['non_4_4']['solos_touched']} solo(s)"
             + (" (" + ", ".join(f"{k} : {v} mesures / {sig['non_4_4']['solos_by_signature'][k]} solo(s)"
                                 for k, v in sig["non_4_4"]["bars_by_signature"].items()) + ")"
                if sig["non_4_4"]["bars"] else "")
             + f" ; solos sans aucune mesure 4/4 : {sig['non_4_4']['solos_without_any_4_4_bar']}.")
    L.append("")
    L.append("### Mesures écartées (toutes signatures)")
    L.append("")
    names = [("non_4_4", "signature ≠ 4/4"), ("incomplete", "incomplète"), ("no_bass", "basse manquante"),
             ("no_chord", "accord absent / NC / non analysé"), ("valid", "valides")]
    L += _table(["motif", "mesures", "part"], [[label, str(d["counts"][k]), pct(d["shares"][k])] for k, label in names])
    L.append("")
    cp = doc["chord_parsing"]
    L.append(f"Accords (temps 4/4 d'un chorus) : {cp['beats_with_symbol']} avec symbole, {cp['beats_no_symbol']} sans "
             f"symbole, {cp['beats_nc']} `NC`, {cp['beats_unparsed']} non analysés. "
             f"{d['solos_without_valid_bar']} solo(s) n'ont aucune mesure valide.")
    L.append("")
    L.append("## Principales mesures (tous solos du sous-ensemble, IC à 95 % par bootstrap par solo)")
    L.append("")
    rows = []
    for key in (*RATIO_INDICATORS, *QUANTILE_INDICATORS):
        b = allg["indicators"][key]
        rows.append([INDICATOR_LABELS[key], cell(b, key not in QUANTILE_INDICATORS), str(b["n_events"]),
                     str(b["n_solos"]), b["ci_reason"] or ""])
    L += _table(["indicateur", "estimation [IC 95 %]", "n événements", "n solos", "IC absent car"], rows)
    L.append("")
    L.append("Le 1ᵉʳ temps de mesure sans changement et le détail des approches (haut/bas, distance) sont dans le "
             "JSON (`groups.all.arrival`, `.approach`, `.passage`, `.intervals`).")
    L.append("")
    L.append("## Rythme de la basse (au temps)")
    L.append("")
    r = allg["bass_rhythm"]
    L.append(f"Sur {r['bars']} mesures valides. `bar_pattern` : égalités de hauteur entre temps consécutifs de la "
             "mesure. **Une hauteur répétée est soit une noire rejouée, soit une note tenue : indiscernable.**")
    L.append("")
    L += _table(["motif", "mesures", "part"],
                [[k, str(r["bar_pattern"]["counts"][k]), pct(r["bar_pattern"]["shares"][k])] for k in PATTERN_KEYS])
    L.append("")
    h = r["hold_beats"]
    L.append("Longueur des suites de temps à hauteur identique (en temps, barres de mesure franchies) : "
             + ", ".join(f"{k} temps : {h['shares'][k] * 100:.0f} % ({h['counts'][k]})" for k in HOLD_KEYS)
             + f" ; moyenne {fr(h['mean'], 2)} temps ; {pct(h['share_beats_in_holds'])} des temps sont dans une suite "
             f"de 2 temps ou plus.")
    L.append(f"Attache sur la barre de mesure (dernier temps = 1ᵉʳ temps de la mesure suivante) : "
             f"{pct(r['bar_tie']['share'])} ({r['bar_tie']['tied']}/{r['bar_tie']['n']}). "
             f"Répétitions par position : " + ", ".join(f"{k} {pct(r['repeat_by_transition']['shares'][k])}"
                                                      for k in TRANSITION_KEYS) + ".")
    L.append(f"Hauteurs distinctes par mesure (1/2/3/4) : "
             + " / ".join(pct(r["distinct_pitches_per_bar"]["shares"][k]) for k in DISTINCT_KEYS) + ".")
    L.append("")
    L.append("**Les croches ne sont pas observables** (une note de basse par noire) : aucun motif de croches n'est "
             "déduit, et la longueur « 1 temps » ne dit pas si la note est brève ou répétée.")
    L.append("")
    L.append("## Classes de tempo et fiabilité")
    L.append("")
    rel = doc["reliability"]
    th = rel["thresholds"]
    L.append(f"Seuils (solos avec mesures valides ET mesures valides) : **assez** ≥ {th['assez']['min_solos']} solos et "
             f"≥ {th['assez']['min_bars']} mesures ; **juste** ≥ {th['juste']['min_solos']} solos et ≥ "
             f"{th['juste']['min_bars']} mesures ; sinon **trop peu**. Justification : le solo est l'unité de "
             "rééchantillonnage ; avec un écart-type d'environ 0,2 entre solos sur une part (ordre de grandeur relevé en "
             "E7), la demi-largeur de l'IC vaut ≈ 0,09 pour 20 solos, ≈ 0,14 pour 8, ≈ 0,20 pour 4.")
    L.append("")
    group_rows = []
    for name, g in doc["groups"].items():
        cc = g["counts"]
        label = group_label(name)
        group_rows.append([label, str(cc["solos"]), str(cc["solos_with_bars"]), str(cc["bars_valid"]),
                           fr(g["duration"]["minutes_valid_bars"]), str(g["choruses"]["total_4_4"]),
                           f"**{g['reliability']['verdict']}**", fr(g["reliability"]["median_ci_width_shares"], 2)])
    L += _table(["groupe (BPM)", "solos", "solos avec mesures", "mesures valides", "minutes", "chorus",
                 "fiabilité", "largeur médiane IC (parts)"], group_rows)
    L.append("")
    key_rows = []
    for key in ("arrival_bass_at_change", "approach_chromatic_bar_change", "repeat_share", "interval_median",
                "bars_quarters", "bars_halves", "bars_one_chord"):
        key_rows.append([INDICATOR_LABELS[key]] + [cell(doc["groups"][n]["indicators"][key], key not in QUANTILE_INDICATORS)
                                                  for n in doc["groups"]])
    L += _table(["indicateur"] + [group_label(n) for n in doc["groups"]], key_rows)
    L.append("")
    L.append("Chaque cellule : estimation [IC 95 %] ; effectifs par groupe dans le JSON (`groups.<groupe>.indicators`, "
             "`n_events`, `n_solos`).")
    L.append("")
    L.append(f"**Verdict du sous-ensemble : {doc['reliability']['verdict']}** "
             f"({c['solos_with_bars']} solos avec mesures valides, {c['bars_valid']} mesures valides).")
    L.append("")
    L.append("## Limites")
    L.append("")
    for lim in doc["limits"]:
        L.append(f"- {lim}")
    for lim in notes.get("limits", ()):
        L.append(f"- {lim}")
    L.append("")
    L.append("## Exploitable pour le moteur / non exploitable")
    L.append("")
    for line in (*notes.get("usable", ()), *GENERAL_USABLE):
        L.append(f"- {line}")
    L.append("")
    return "\n".join(L)


# ── CLI ──────────────────────────────────────────────────────────────────

def write_subset(subset: str, db: Path, out_dir: Path, expected: str = wjazzd.SHA256) -> dict[str, Any]:
    """Calcule un sous-ensemble et écrit `measures-bass.json` et `README.md` sous `out_dir/wjazzd-<nom>/`."""
    doc = build_subset(subset, db, expected)
    folder = out_dir / SLUGS[subset]
    write_json(folder / OUTPUT_NAME, doc)
    (folder / README_NAME).write_text(readme_text(doc), encoding="utf-8")
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--subset", action="append", choices=SUBSETS, help="sous-ensemble(s) (défaut : les quatre)")
    ap.add_argument("--manifest", action="store_true", help="écrit corpus/wjazzd/manifest.jsonl et VERSION")
    ap.add_argument("--summary", action="store_true", help="affiche un tableau lisible des JSON déjà écrits")
    ap.add_argument("--group", action="append", help="groupe(s) du tableau (défaut : tous)")
    ap.add_argument("--db", type=Path, default=wjazzd.RAW_DB)
    ap.add_argument("--out-dir", type=Path, default=REFERENCES, help="dossier contenant wjazzd-<sous-ensemble>/")
    ap.add_argument("--corpus-dir", type=Path, default=wjazzd.CORPUS_DIR, help="dossier du manifeste et de VERSION")
    args = ap.parse_args(argv)
    explicit = bool(args.subset)
    subsets = args.subset or list(SUBSETS)
    try:
        if args.summary:
            for subset in subsets:
                doc = json.loads((args.out_dir / SLUGS[subset] / OUTPUT_NAME).read_text(encoding="utf-8"))
                print(summary_text(doc, args.group))
                print()
            return 0
        if args.manifest or not explicit:
            rows = write_manifest(args.db, args.corpus_dir)
            n = Counter(r["l2_subset"] for r in rows if r["l2_subset"])
            print(f"{args.corpus_dir / 'manifest.jsonl'} : {len(rows)} solos ; l2_subset : "
                  + ", ".join(f"{k} {n[k]}" for k in SUBSETS))
        if explicit or not args.manifest:
            for subset in subsets:
                doc = write_subset(subset, args.db, args.out_dir)
                prov = doc["provenance"]
                print(f"{args.out_dir / SLUGS[subset]} : {prov['n_solos']} solos, {prov['n_bars']} mesures "
                      f"({prov['n_bars_valid']} valides), verdict {doc['reliability']['verdict']}")
    except (wjazzd.IntegrityError, OSError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
