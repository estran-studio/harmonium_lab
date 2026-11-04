"""Banque de cellules mélodiques swing **synthétisées** depuis les mesures de WJazzD (E12).

    python -m harmonium_lab.backing.melody_cells --generate -o references/wjazzd-melodie/cells.toml
    python -m harmonium_lab.backing.melody_cells --check FILE      # aucune suite de N notes d'un solo
    python -m harmonium_lab.backing.melody_cells --levels FILE     # cellules par rôle et par niveau E10

Aucune cellule n'est une phrase de solo : chacune est tirée d'un modèle statistique construit sur
`measures-melody.json` (comptes agrégés, voir `melody_measures`), puis **refusée** si l'une de ses suites de
notes figure dans un solo du corpus (ODbL 1.0 : usage A, aucun extrait substantiel). Le corpus n'entre
dans ce module que par `NGramIndex`, en mémoire.

## Le modèle (par rôle de cellule du moteur)

- **Rythme** : chaîne sur les huit croches ; probabilité d'attaque d'un créneau sachant les deux
  créneaux précédents, lue dans les mesures du rôle qui commencent sur le temps 1 (une cellule ne
  commence jamais par une tenue), lissée vers le total (`SMOOTH_RHYTHM`). Une cellule de cadence
  finit par une tenue d'au moins `last_duration` croches, selon la loi mesurée.
- **Contour** : pas diatoniques signés d'une attaque à la suivante, tirés de la chaîne d'ordre 2
  (`step_bigram`) du rôle, lissée vers sa loi simple. Les cibles sur les temps tombent dans l'accord de
  tonique (degrés 1 3 5 7) dans la proportion mesurée **pour le rôle** (`beats_chord_share`) : les poids
  des candidats d'un temps sont multipliés pour que cette part soit exacte ; l'accord réel est celui de
  la grille, rapproché par le moteur.
- **Première note** : relation à l'accord mesurée sur la première attaque (`first_relation`) → degré.
- **Cadences** : `cad_full` finit sur la tonique, `cad_half` sur 2, 5 ou 7 (contrainte du moteur,
  `Cell::respects_cadence`, pas une mesure).
- **Rôles** : un tirage n'est gardé que si sa forme répond à la définition du rôle (la même fonction de
  classement que pour le corpus, `melody_measures._classify`).

## Rendu par le moteur (boucle fermée)

Sous une grille, le moteur (modèle `loop`) rapproche **chaque** note de la note d'accord la plus proche
(`fit_planned_melody` : accord seul, les gammes ne modifient pas les notes). Une ligne conjointe s'y
effondre en notes répétées : le bouche-trou en jouait 39 %, les solos 7 % (mesures, `interval_repeat_share`).
Le module simule ce rapprochement (`realize`, sur la batterie d'accords de `CHORD_BATTERY`, les accords des
grilles du profil, pondérés par leur durée) et **refuse** toute cellule dont la part de notes répétées
après rapprochement dépasse `repeat_cap` = deux fois celle du corpus. La simulation reproduit le moteur :
part de notes répétées mesurée sur la vérité terrain 0,29 pour la banque sans ce filtre, simulée 0,27.

## Niveaux de difficulté (E10)

Les bornes de référence de `specs/019-…/e10-e11-melodie-qr.md` (4 niveaux, durée native 1 croche) :
saut, attaques, plus petite durée, ambitus. Chaque cellule est rangée au **plus bas niveau qu'elle
respecte**. La banque garde pour chaque rôle au moins `TIER_FLOOR` de cellules par niveau 1 à 3 ; le poids
d'une cellule est la part de son niveau dans les mesures du rôle du corpus, divisée par le nombre de
cellules du niveau.

## Refus de copie (`N`)

Une cellule est refusée si une suite de `N_RHYTHM` notes y a les mêmes pas diatoniques **et** les mêmes
durées qu'une suite d'un solo, ou si une suite de `N_CONTOUR` notes y a les mêmes pas (durées libres).
Les tailles sont lues dans `ngram_sharing` du JSON de mesures : à `N_RHYTHM = 6` (contour et rythme), 85 %
des suites distinctes du corpus n'apparaissent que dans un seul solo ; à `N_CONTOUR = 7` (contour seul, plus
sévère), 80 %. En dessous, ce sont des idiomes communs (gammes, arpèges) partagés par plusieurs solistes. Une
cellule ne compte que huit attaques au plus : `N` ne peut dépasser 8.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from . import wjazzd
from ._util import share
from .chords import parse_wjazzd
from .melody_measures import (
    MBar, MNote, NGramIndex, SLOTS, ngrams, corpus_solos, steps_of, _classify, OUTPUT as MEASURES_PATH,
)

CELLS_OUTPUT = wjazzd.REPO / "references" / "wjazzd-melodie" / "cells.toml"
N_RHYTHM = 6
N_CONTOUR = 7
SMOOTH_RHYTHM = 40.0
SMOOTH_STEPS = 20.0
TIER_FLOOR = 0.15
REPEAT_FACTOR = 2.0  # notes répétées après rapprochement : au plus ce multiple de la part du corpus
MAX_DEGREE = 14
MAX_AMBITUS_STEPS = 7
LEAP_STEPS = 4  # un saut au-delà (strictement) de la quinte est limité à un par cellule (D5)
IONIAN = (0, 2, 4, 5, 7, 9, 11)
TONIC_CHORD = frozenset({1, 3, 5, 0})  # degrés modulo 7 de l'accord de tonique (1 3 5 7)
CADENCE_TARGETS = {"cad_full": {1: 1.0}, "cad_half": {5: 0.45, 2: 0.30, 7: 0.25}}
ROLE_COUNTS = {"open": 36, "run": 48, "arp": 30, "turn": 36, "cad_half": 30, "cad_full": 30}
FIRST_DEGREES = {"root": (1, 8), "third": (3, 10), "fifth": (5, 12), "seventh": (7, 14),
                 "tone": (2, 6, 9, 13), "scale": (2, 4, 6, 9, 11, 13), "chromatic": (2, 4, 6, 9, 11, 13)}
# Accords des grilles de `wjazzd_swing` : (poids, fondamentale en demi-tons au-dessus de la tonique, notes de
# l'accord typé du moteur). Poids = durée dans le blues (I7 IV7 V7 ii7 VI7 …) et dans l'AABA (I6, VI7, ii7, V7,
# iii7), arrondis ; seules les classes de hauteur comptent pour le rapprochement.
CHORD_BATTERY = (
    (0.30, 0, (0, 4, 7, 10)),  # I7
    (0.13, 5, (0, 4, 7, 10)),  # IV7
    (0.12, 7, (0, 4, 7, 10)),  # V7
    (0.12, 2, (0, 3, 7, 10)),  # ii7
    (0.08, 9, (0, 4, 7, 10)),  # VI7
    (0.08, 0, (0, 4, 7, 9)),  # I6
    (0.05, 4, (0, 3, 7, 10)),  # iii7
    (0.12, 7, (0, 3, 7, 10)),  # v7
)
HOLD = 0  # jeton de prolongation dans les listes internes (degré 0 = « - »)
# Bornes de référence de E10 (niveau → saut, attaques, plus petite durée, ambitus), en demi-tons / croches.
LEVELS = {1: (4, 4, 2, 7), 2: (5, 6, 2, 9), 3: (7, 8, 1, 12)}
SEMITONES = {d + 1: IONIAN[d] for d in range(7)}


def semitone(degree: int) -> int:
    """Hauteur relative (demi-tons) d'un degré 1..14 de la gamme majeure."""
    octave, rest = divmod(degree - 1, 7)
    return 12 * octave + IONIAN[rest]


@dataclass(frozen=True)
class Cell:
    role: str
    tokens: tuple[int, ...]  # degré 1..14 ou HOLD, huit croches

    @property
    def notation(self) -> str:
        return " ".join("-" if t == HOLD else str(t) for t in self.tokens)

    @property
    def attacks(self) -> list[tuple[int, int, int]]:
        """(créneau, degré, durée légato) de chaque attaque."""
        starts = [i for i, t in enumerate(self.tokens) if t != HOLD]
        return [(s, self.tokens[s], (starts[k + 1] if k + 1 < len(starts) else SLOTS) - s)
                for k, s in enumerate(starts)]


@dataclass(frozen=True)
class CellStats:
    attacks: int
    min_dur: int
    ambitus: int  # demi-tons
    leap: int  # plus grand saut, demi-tons


def stats_of(cell: Cell) -> CellStats:
    att = cell.attacks
    pitches = [semitone(d) for _, d, _ in att]
    leaps = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
    return CellStats(len(att), min(d for _, _, d in att), max(pitches) - min(pitches), max(leaps, default=0))


def level_of(stats: CellStats) -> int:
    """Plus bas niveau E10 (1 à 3) dont les bornes sont respectées, 4 sinon (profil)."""
    for level, (leap, attacks, dur, ambitus) in LEVELS.items():
        if stats.leap <= leap and stats.attacks <= attacks and stats.min_dur >= dur and stats.ambitus <= ambitus:
            return level
    return 4


def valid_cell(cell: Cell) -> bool:
    """Invariants D5 du moteur : ambitus ≤ 7 pas, au plus un saut > quinte, première croche attaquée."""
    if len(cell.tokens) != SLOTS or cell.tokens[0] == HOLD:
        return False
    degrees = [d for _, d, _ in cell.attacks]
    if max(degrees) - min(degrees) > MAX_AMBITUS_STEPS or not all(1 <= d <= MAX_DEGREE for d in degrees):
        return False
    return sum(1 for a, b in zip(degrees, degrees[1:]) if abs(b - a) > LEAP_STEPS) <= 1


def snap(pitch: int, root: int, intervals: Sequence[int]) -> int:
    """Hauteur d'accord la plus proche de `pitch` (celle du moteur : `nearest_pitch`, premier minimum à égalité)."""
    best: int | None = None
    for interval in intervals:
        pc = (root + interval) % 12
        octave = (pitch - pc) // 12
        for o in (octave - 1, octave, octave + 1):
            candidate = o * 12 + pc
            if best is None or abs(candidate - pitch) < abs(best - pitch):
                best = candidate
    assert best is not None
    return best


def realize(cell: Cell, root: int, intervals: Sequence[int]) -> list[int]:
    """Hauteurs des attaques (demi-tons au-dessus de la tonique) après rapprochement de l'accord."""
    return [snap(semitone(d), root, intervals) for _, d, _ in cell.attacks]


def realized_repeat_share(cell: Cell) -> float:
    """Part de notes répétées (intervalle nul) dans la cellule rendue, moyenne pondérée sur `CHORD_BATTERY`."""
    total = weight = 0.0
    for w, root, intervals in CHORD_BATTERY:
        pitches = realize(cell, root, intervals)
        ints = [b - a for a, b in zip(pitches, pitches[1:])]
        if ints:
            total += w * sum(1 for i in ints if i == 0) / len(ints)
            weight += w
    return total / weight if weight else 0.0


def as_bar(cell: Cell) -> MBar:
    """La cellule vue comme une mesure sur un Imaj7 (pour le classement de rôle et les parts d'accord)."""
    chord = parse_wjazzd("Cj7")
    base = 60
    notes = tuple(MNote(s, base + semitone(d), dur) for s, d, dur in cell.attacks)
    return MBar(0, notes, (chord,) * 4)


# ── Modèle ───────────────────────────────────────────────────────────────

class Model:
    """Lois de rythme, de contour, de première note et de cadence d'un rôle, lues dans les mesures."""

    def __init__(self, measures: dict[str, Any]) -> None:
        self.doc = measures
        self.total = measures["total"]
        self._steps: dict[tuple[str, int | None], dict[int, float]] = {}
        self.repeat_cap = REPEAT_FACTOR * measures["total"]["intervals_semitones"]["shares"]["0"]

    def role(self, name: str) -> dict[str, Any]:
        return self.doc["roles"][name]

    def p_attack(self, role: str, slot: int, ctx: int) -> float:
        key = f"{slot}:{ctx}"
        total = self.total["rhythm_markov_from_downbeat"].get(key)
        mine = self.role(role)["rhythm_markov_from_downbeat"].get(key)
        base = total["attack"] if total else 0.5
        if not mine:
            return base
        n = mine["n"]
        return (n * mine["attack"] + SMOOTH_RHYTHM * base) / (n + SMOOTH_RHYTHM)

    def step_weights(self, role: str, previous: int | None) -> dict[int, float]:
        key = (role, previous)
        if key not in self._steps:
            self._steps[key] = self._step_weights(role, previous)
        return self._steps[key]

    def _step_weights(self, role: str, previous: int | None) -> dict[int, float]:
        mine = self.role(role)
        uni = mine["steps"]["shares"]
        out = {s: SMOOTH_STEPS * uni[str(s)] + 0.01 for s in range(-MAX_AMBITUS_STEPS, MAX_AMBITUS_STEPS + 1)}
        if previous is not None:
            for key, count in mine["step_bigram"].items():
                a, b = (int(x) for x in key.split(","))
                if a == previous and abs(b) <= MAX_AMBITUS_STEPS:
                    out[b] += count
        return out

    def last_duration(self, role: str) -> dict[int, float]:
        shares = self.role(role)["last_duration"]["shares"]
        return {d: shares[str(d)] for d in range(1, SLOTS + 1)}


def _choice(rng: random.Random, weights: dict[Any, float]) -> Any:
    total = sum(weights.values())
    x = rng.random() * total
    for key, w in weights.items():
        x -= w
        if x <= 0:
            return key
    return key


def _rhythm(model: Model, role: str, rng: random.Random) -> list[int] | None:
    """Créneaux d'attaque (le créneau 0 toujours) ; `None` si la cadence n'a pas sa tenue finale."""
    attacks = {0}
    for slot in range(1, SLOTS):
        ctx = (slot - 1 in attacks) * 2 + (slot - 2 in attacks)
        if rng.random() < model.p_attack(role, slot, ctx):
            attacks.add(slot)
    slots = sorted(attacks)
    if role in CADENCE_TARGETS:
        weights = model.last_duration(role)
        peak = max(weights.values())
        if rng.random() * peak > weights[SLOTS - slots[-1]] or SLOTS - slots[-1] < 2 or len(slots) < 2:
            return None
    return slots


def _walk(model: Model, role: str, slots: list[int], rng: random.Random) -> list[int] | None:
    """Degrés des attaques, ou `None` si le tirage ne tient pas dans les invariants."""
    mine = model.role(role)
    first = _choice(rng, {k: v for k, v in mine["first_relation"]["shares"].items() if v > 0} or {"root": 1.0})
    options = [d for d in FIRST_DEGREES[first] if 3 <= d <= 11]
    degrees = [rng.choice(options)]
    previous: int | None = None
    for slot in slots[1:]:
        weights = model.step_weights(role, previous)
        current = degrees[-1]
        viable = {}
        for s, w in weights.items():
            nd = current + s
            if not 1 <= nd <= MAX_DEGREE or max(degrees + [nd]) - min(degrees + [nd]) > MAX_AMBITUS_STEPS:
                continue
            if abs(s) > LEAP_STEPS and any(abs(b - a) > LEAP_STEPS for a, b in zip(degrees, degrees[1:])):
                continue
            viable[s] = w
        if not viable:
            return None
        if slot % 2 == 0:  # cible sur un temps : part d'accord de tonique mesurée pour le rôle
            target = min(max(mine["beats_chord_share"], 0.02), 0.98)
            on = sum(w for s, w in viable.items() if (current + s) % 7 in TONIC_CHORD)
            q = on / sum(viable.values())
            if 0 < q < 1:
                boost = target * (1 - q) / ((1 - target) * q)
                viable = {s: w * boost if (current + s) % 7 in TONIC_CHORD else w for s, w in viable.items()}
        step = _choice(rng, viable)
        degrees.append(current + step)
        previous = step
    if role in CADENCE_TARGETS:
        degrees = _cadence(degrees, role, rng)
        if degrees is None:
            return None
    return degrees


def _cadence(degrees: list[int], role: str, rng: random.Random) -> list[int] | None:
    """Remplace la dernière note par la cible de cadence la plus proche permise (poids de `CADENCE_TARGETS`)."""
    classes = _choice(rng, {c: w for c, w in CADENCE_TARGETS[role].items()})
    body = degrees[:-1]
    candidates = sorted((d for d in range(1, MAX_DEGREE + 1) if d % 7 == classes % 7),
                        key=lambda d: (abs(d - body[-1]), d))
    for d in candidates:
        trial = body + [d]
        if max(trial) - min(trial) <= MAX_AMBITUS_STEPS and \
                sum(1 for a, b in zip(trial, trial[1:]) if abs(b - a) > LEAP_STEPS) <= 1:
            return trial
    return None


def _shape_ok(cell: Cell) -> bool:
    """La forme répond au rôle (même classement que le corpus) ; pas une suite d'une seule hauteur."""
    degrees = [d for _, d, _ in cell.attacks]
    if len(degrees) >= 3 and len(set(degrees)) < 2:
        return False
    if cell.role in ("run", "arp", "turn"):
        return len(degrees) >= 3 and _classify(as_bar(cell), False, False) == cell.role
    return len(degrees) >= 2


def synthesize(model: Model, role: str, rng: random.Random) -> Cell | None:
    """Un tirage de cellule de rôle `role` (ou `None` : refusé avant tout contrôle de copie)."""
    slots = _rhythm(model, role, rng)
    if slots is None:
        return None
    degrees = _walk(model, role, slots, rng)
    if degrees is None:
        return None
    tokens = [HOLD] * SLOTS
    for s, d in zip(slots, degrees):
        tokens[s] = d
    cell = Cell(role, tuple(tokens))
    return cell if valid_cell(cell) and _shape_ok(cell) and realized_repeat_share(cell) <= model.repeat_cap else None


# ── Refus de copie ───────────────────────────────────────────────────────

class CopyGuard:
    """Index du corpus pour les deux critères de copie (`N_RHYTHM` avec durées, `N_CONTOUR` sans)."""

    def __init__(self, solos: Sequence[Sequence[MBar]]) -> None:
        self.rhythm = NGramIndex(solos, N_RHYTHM, diatonic=True, with_rhythm=True)
        self.contour = NGramIndex(solos, N_CONTOUR, diatonic=True, with_rhythm=False)

    def matches(self, cell: Cell) -> list[str]:
        """Critères pour lesquels une suite de la cellule est dans un solo (liste vide : originale)."""
        att = cell.attacks
        degrees = [d for _, d, _ in att]
        ints = [b - a for a, b in zip(degrees, degrees[1:])]
        durs = [d for _, _, d in att]
        found = []
        if any(k in self.rhythm for k in ngrams(ints, durs, N_RHYTHM, True)):
            found.append(f"{N_RHYTHM} notes, pas et durées")
        if any(k in self.contour for k in ngrams(ints, durs, N_CONTOUR, False)):
            found.append(f"{N_CONTOUR} notes, pas")
        return found


# ── Banque ───────────────────────────────────────────────────────────────

def tier_shares(solos: Sequence[Sequence[MBar]], model: Model) -> dict[str, dict[int, float]]:
    """Part de chaque niveau E10 (1 à 4) dans les mesures du corpus de chaque rôle (plancher `TIER_FLOOR`)."""
    counts: dict[str, Counter] = {r: Counter() for r in ROLE_COUNTS}
    for solo in solos:
        for run in _runs_by_bar(solo):
            for bar, role in run:
                if role not in counts or len(bar.notes) < 2:
                    continue
                pitches = [n.pitch for n in bar.notes]
                leaps = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
                ends = [n.slot for n in bar.notes[1:]] + [SLOTS]
                st = CellStats(len(bar.notes), min(e - n.slot for n, e in zip(bar.notes, ends)),
                               max(pitches) - min(pitches), max(leaps))
                counts[role][level_of(st)] += 1
    out: dict[str, dict[int, float]] = {}
    for role, c in counts.items():
        total = sum(c.values()) or 1
        raw = {t: c[t] / total for t in (1, 2, 3, 4)}
        floored = {t: max(v, TIER_FLOOR) if t < 4 else v for t, v in raw.items()}
        norm = sum(floored.values())
        out[role] = {t: v / norm for t, v in floored.items()}
    return out


def _runs_by_bar(solo: Sequence[MBar]):
    """(mesure, rôle) de chaque mesure d'un solo, rôles du classement de `melody_measures`."""
    from .melody_measures import phrase_runs
    starts, ends = set(), set()
    for run in phrase_runs(solo):
        starts.add((run[0][0].bar, run[0][1].slot))
        ends.add((run[-1][0].bar, run[-1][1].slot))
    yield [(bar, _classify(bar, bool(bar.notes) and (bar.bar, bar.notes[0].slot) in starts,
                           bool(bar.notes) and (bar.bar, bar.notes[-1].slot) in ends))
           for bar in solo if bar.notes]


def generate(model: Model, guard: CopyGuard, shares: dict[str, dict[int, float]], seed: int = 12,
             max_draws: int = 400_000) -> tuple[list[tuple[Cell, int]], dict[str, Any]]:
    """Banque `[(cellule, poids)]` et compte rendu (tirages, refus, par rôle et niveau)."""
    rng = random.Random(seed)
    bank: list[tuple[Cell, int]] = []
    report: dict[str, Any] = {"draws": 0, "refused_copy": 0, "refused_shape": 0, "by_role": {}}
    for role, count in ROLE_COUNTS.items():
        want = {t: max(3, round(count * share)) for t, share in shares[role].items()}
        weight_of = {t: max(1, round(1000 * shares[role][t] / want[t])) for t in want}
        have: dict[int, list[Cell]] = {t: [] for t in want}
        seen: set[tuple[int, ...]] = set()
        draws = 0
        while any(len(have[t]) < want[t] for t in want) and draws < max_draws:
            draws += 1
            cell = synthesize(model, role, rng)
            if cell is None:
                report["refused_shape"] += 1
                continue
            tier = level_of(stats_of(cell))
            if len(have[tier]) >= want[tier] or cell.tokens in seen:
                continue
            if guard.matches(cell):
                report["refused_copy"] += 1
                continue
            seen.add(cell.tokens)
            have[tier].append(cell)
        report["draws"] += draws
        report["by_role"][role] = {str(t): len(v) for t, v in have.items()}
        short = [t for t in want if len(have[t]) < want[t]]
        if short:
            raise RuntimeError(f"rôle {role} : niveaux {short} incomplets après {draws} tirages")
        for t, cells in have.items():
            bank.extend((c, weight_of[t]) for c in cells)
    return bank, report


HEADER = """\
# Banque de cellules mélodiques d'une mesure (8 croches) pour `wjazzd_swing` (phase 019, E12).
#
# Chaque cellule est SYNTHÉTISÉE depuis des statistiques agrégées des solos du sous-ensemble
# `rhythmfeel = SWING` de la Weimar Jazz Database v2.1 (rythmes en croches swing, anticipations, pas
# diatoniques, cibles sur les temps par rapport à l'accord, cadences) ; aucune phrase de solo n'est
# copiée (ODbL 1.0 §4.3 : Produced Work, usage A) : un tirage est refusé si l'une de ses suites de
# 6 notes (pas et durées) ou de 7 notes (pas) figure dans un solo. Génération :
# `python -m harmonium_lab.backing.melody_cells --generate` (graine {seed}), mesures :
# `references/wjazzd-melodie/measures-melody.json` du labo.
#
# Notation : voir `profiles/reel_quebecois/cells.toml` (degrés 1..14 de la gamme du mode, `-` = tenue).
# Rôles du moteur lus pour le swing : `open` (début de phrase, première mesure d'une partie), `run`
# (ligne conjointe), `arp` (arpège d'accord), `turn` (broderie, enclosure), `cad_half` (fin de phrase qui
# s'appuie sur 2, 5 ou 7), `cad_full` (fin de phrase sur la tonique). `weight` : part de la difficulté de
# la cellule (niveaux E10 1 à 3, 4 = profil) dans les mesures du rôle du corpus, divisée par le nombre de
# cellules du niveau ; le tirage d'un rôle est pondéré par ce poids.
#
# Niveaux E10 (bornes de référence, plus bas niveau respecté par la cellule) : 1 = saut ≤ 4 demi-tons,
# ≤ 4 attaques, durée ≥ 2 croches, ambitus ≤ 7 ; 2 = 5, ≤ 6 attaques, ≥ 2, 9 ; 3 = 7, ≤ 8, ≥ 1, 12 ;
# 4 = au-delà. Le niveau de chaque cellule est en commentaire de fin de ligne.
"""


def to_toml(bank: Sequence[tuple[Cell, int]], seed: int) -> str:
    lines = [HEADER.format(seed=seed), "cells = ["]
    for role in ROLE_COUNTS:
        for cell, weight in sorted((b for b in bank if b[0].role == role),
                                   key=lambda b: (level_of(stats_of(b[0])), b[0].tokens)):
            lines.append(f' {{ role = "{role}", notes = "{cell.notation}", weight = {weight} }}, '
                         f"# niveau {level_of(stats_of(cell))}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def parse_toml_cells(text: str) -> list[tuple[Cell, int]]:
    import tomllib
    out = []
    for raw in tomllib.loads(text)["cells"]:
        tokens = tuple(HOLD if t == "-" else int(t) for t in raw["notes"].split())
        out.append((Cell(raw["role"], tokens), int(raw.get("weight", 1))))
    return out


def level_table(bank: Sequence[tuple[Cell, int]]) -> dict[str, dict[str, int]]:
    """Cellules par rôle et par niveau E10 (cellule comptée à son plus bas niveau respecté)."""
    table: dict[str, Counter] = {}
    for cell, _ in bank:
        table.setdefault(cell.role, Counter())[level_of(stats_of(cell))] += 1
    return {r: {str(t): c[t] for t in (1, 2, 3, 4)} for r, c in table.items()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", type=Path, default=wjazzd.RAW_DB)
    ap.add_argument("--measures", type=Path, default=MEASURES_PATH)
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("-o", "--output", type=Path, default=CELLS_OUTPUT)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--check", type=Path, help="cells.toml à vérifier contre le corpus")
    ap.add_argument("--levels", type=Path, help="cells.toml dont on compte les cellules par rôle et niveau")
    args = ap.parse_args(argv)
    try:
        if args.levels:
            print(json.dumps(level_table(parse_toml_cells(args.levels.read_text(encoding="utf-8"))), indent=2))
            return 0
        solos, _ = corpus_solos(args.db)
        guard = CopyGuard(solos)
        if args.check:
            bank = parse_toml_cells(args.check.read_text(encoding="utf-8"))
            bad = [(c.notation, m) for c, _ in bank if (m := guard.matches(c))]
            for notation, m in bad:
                print(f"copie : {notation} ({', '.join(m)})", file=sys.stderr)
            print(f"{len(bank)} cellules, {len(bad)} présentes dans un solo")
            return 1 if bad else 0
        if not args.generate:
            ap.error("--generate, --check ou --levels")
        model = Model(json.loads(args.measures.read_text(encoding="utf-8")))
        bank, report = generate(model, guard, tier_shares(solos, model), seed=args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(to_toml(bank, args.seed), encoding="utf-8")
        print(f"{args.output} : {len(bank)} cellules ; tirages {report['draws']}, refus forme "
              f"{report['refused_shape']}, refus copie {report['refused_copy']}")
        print(json.dumps(report["by_role"]))
    except (wjazzd.IntegrityError, OSError, RuntimeError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
