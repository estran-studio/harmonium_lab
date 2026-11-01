"""Mesures de la marche de basse, en comptes et en parts, sur la Weimar Jazz Database.

    python -m harmonium_lab.backing.bass_measures              # écrit references/wjazzd-swing/measures-bass.json
    python -m harmonium_lab.backing.bass_measures --summary    # tableau lisible du JSON écrit

Sous-ensemble : `solo_info.rhythmfeel = 'SWING'`, mesures en 4/4 d'un chorus (`bar >= 1`),
à quatre temps, **basse complète** (quatre `bass_pitch`) et accord connu (`NC` ou symbole non
analysé : mesure écartée). Les mesures valides consécutives d'un solo forment une **suite**
(`BassRun`) : les intervalles et les approches ne franchissent jamais une mesure écartée.

## Structure commune : `BassBar` / `BassRun`

`Beat(chord, pitch)` : l'accord en vigueur et la hauteur MIDI de la basse au temps.
`BassBar(beats, prev_chord)` : quatre temps ; `prev_chord` est l'accord du temps qui précède la
mesure (`None` si inconnu : début de solo ; la mesure n'a alors pas de changement au 1ᵉʳ temps).
`BassRun(bars, key)` : mesures contiguës et tonique (classe de hauteur) si connue. Les mesures
de `bass_compare` (basse générée) passent par ces mêmes structures : `measure_runs` est l'unique
chemin de calcul des critères a–e et du rythme harmonique.

## Définitions (alignées sur le moteur, `harmonium_core/src/compose/walking.rs`)

- **Arrivée** : un temps qui ouvre une mesure ou où l'accord change. Le 1ᵉʳ temps de la mesure
  est toujours une arrivée pour le moteur ; on sépare donc `change` (l'accord change à ce temps,
  1ᵉʳ temps compris) de `bar_start_no_change` (1ᵉʳ temps d'une mesure sans changement).
  Classes de la note : `bass` (= basse de l'accord : fondamentale ou basse slash), `root`
  (la fondamentale d'un accord slash dont la basse est une autre note), `third` (3 ou ♭3),
  `fifth` (quinte juste), `seventh` (♭7 ou 7), `other`.
- **Approche** : le temps `i` qui précède une arrivée `i+1` sans être lui-même une arrivée.
  Contexte : `bar_change` (4ᵉ temps, l'accord change à la barre), `bar_same` (4ᵉ temps, même
  accord à la barre : arrivée du moteur sur la même basse), `mid_change` (avant un changement à
  mi-mesure), `all`. Cible : la basse de l'accord entrant, à la hauteur la plus proche de la
  note jouée à `i+1` ; `d` = note − cible. Classes, dans cet ordre : `same` (d = 0),
  `chromatic_below` (−1), `chromatic_above` (+1), `diatonic` (|d| = 2 ou 3 et note dans la gamme
  de l'accord ENTRANT ; `diatonic_nearest` compte ceux qui sont la première note de la gamme de ce
  côté, définition stricte du moteur), `fifth` (|d| = 7), `chord_tone` (note de l'accord SORTANT),
  `other`. Poids mappables sur le moteur : `none` (tout sauf chromatic/diatonic), `chromatic`
  (±1), `diatonic`. `above`/`below` : côté de la cible ; `rising`/`falling` : sens depuis la note
  précédente ; `same_side_as_arrival` : l'approche est du côté de l'arrivée qui ouvre l'étendue
  (règle du moteur : `from > goal` ⇒ approche par le haut).
- **Passage** : un temps qui n'est ni une arrivée ni un temps qui en précède une (`passage`,
  défini à la lettre) ; `passage_engine` ajoute les temps qui précèdent une arrivée sans en être
  une approche chromatique/diatonique (le moteur les tire comme notes de passage). Classes :
  `chord_tone` (classe ∈ notes de l'accord en vigueur), `scale_step` (dans la gamme, hors accord),
  `chromatic` (hors gamme). Gammes et notes d'accord : voir `chords`.
- **Intervalles** : |Δ| en demi-tons entre temps consécutifs d'une suite ; `repeat` : Δ = 0 ;
  `keep_direction` : parmi les triplets de deux intervalles non nuls, part où le second a le
  sens du premier ; `toward_target` : sur les passages, part des notes plus proches que la
  précédente de la prochaine arrivée de la ligne (hauteur jouée à cette arrivée).
- **Registre** : centiles de `bass_pitch` (MIDI), global et transposé en tonalité (hauteur −
  tonique) ; `walk_window` = centiles 2–98 ; `arrival_window` = centiles 10–90 des arrivées sur
  la basse de l'accord, et la meilleure fenêtre de 12 demi-tons (celle qui en contient le plus).
- **Rythme harmonique** : accords par mesure (1 à 4), durée des accords en temps (étendues
  bornées par deux changements dans la suite), temps de la mesure où l'accord change.

## Fiabilité de la basse (contrôle fait sur la base réelle)

`bass_pitch` est souvent peu cohérent avec la grille : sur tout le sous-ensemble swing, la basse de
l'accord n'est jouée qu'à 41 % des changements d'accord et 23 % des 1ᵉʳˢ temps de mesure sans changement ;
la part par solo des arrivées sur la basse de l'accord s'étale (centiles 10 / 50 / 90 : 17 % / 43 % /
70 %) sans mode séparé qui permettrait un tri net, et certains solos portent des suites chromatiques
montantes sur plusieurs mesures, qui ne suivent pas la grille (artéfact d'annotation probable). Aucune erreur d'octave ni décalage d'un
temps n'explique cela (voir `wjazzd`). Les mesures sont donc rapportées **telles quelles** (`all`)
et aussi sur un écran de fiabilité déclaré (`reliable`) : solos d'au moins 40 arrivées dont au
moins 80 % tombent sur une note de l'accord (basse, fondamentale, 3, 5 ou 7). L'écran ne mesure pas
la part sur la basse (celle qu'on veut estimer) mais la cohérence harmonique ; c'est un choix, pas
une vérité : l'arrivée sur la basse y reste plus basse que dans une marche idéale.

## Groupes et tranches de tempo

`all` (tout le sous-ensemble), `blues` (`composition_info.template = 'Blues'`), `other_forms`,
`reliable` (voir ci-dessous), puis quatre tranches contiguës de `solo_info.avgtempo` : `tempo_lt130` (< 130 BPM), `tempo_130_175`,
`tempo_175_235`, `tempo_ge235` (≥ 235). Bornes choisies sur la répartition réelle des 361 solos
(quartiles à 132 / 177,5 / 242,6 BPM) pour des nombres de solos voisins (85 / 86 / 84 / 106).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Sequence

from . import wjazzd
from ._util import counts_and_shares, percentiles, share, write_json
from .chords import Chord, ChordParseError, parse_wjazzd

OUTPUT = wjazzd.REPO / "references" / "wjazzd-swing" / "measures-bass.json"
BEATS = 4

ARRIVAL_CLASSES = ("bass", "root", "third", "fifth", "seventh", "other")
APPROACH_CLASSES = ("same", "chromatic_below", "chromatic_above", "diatonic", "fifth", "chord_tone", "other")
APPROACH_CONTEXTS = ("bar_change", "bar_same", "mid_change", "all")
PASSING_CLASSES = ("chord_tone", "scale_step", "chromatic")
INTERVAL_KEYS = tuple(str(i) for i in range(13)) + (">12",)
CHORDS_PER_BAR = ("1", "2", "3", "4")
DURATION_KEYS = tuple(str(i) for i in range(1, 9)) + (">8",)
INTERVAL_PERCENTILES = (50, 75, 90, 95, 99)
REGISTER_PERCENTILES = (1, 5, 25, 50, 75, 95, 99)
TEMPO_PERCENTILES = (10, 25, 50, 75, 90)

# Écran de fiabilité de `bass_pitch` (groupe `reliable`) : voir le docstring, « Fiabilité de la basse ».
RELIABLE_MIN_ARRIVALS = 40
RELIABLE_MIN_CHORD_TONE_SHARE = 0.8

# Tranches de tempo (BPM, borne haute exclue) : voir le docstring.
TEMPO_BINS: tuple[tuple[str, float, float], ...] = (
    ("tempo_lt130", 0.0, 130.0),
    ("tempo_130_175", 130.0, 175.0),
    ("tempo_175_235", 175.0, 235.0),
    ("tempo_ge235", 235.0, float("inf")),
)


# ── Structures communes ──────────────────────────────────────────────────

class Beat(NamedTuple):
    """Un temps : l'accord en vigueur et la hauteur MIDI de la basse."""
    chord: Chord
    pitch: int


@dataclass
class BassBar:
    """Une mesure de quatre temps ; `prev_chord` : accord du temps précédent (`None` si inconnu)."""
    beats: list[Beat]
    prev_chord: Chord | None = None


@dataclass
class BassRun:
    """Mesures contiguës d'une même pièce ; `key` : tonique (classe de hauteur) si connue."""
    bars: list[BassBar]
    key: int | None = None


# ── Classification d'une note (fonctions pures) ──────────────────────────

def arrival_class(pitch: int, chord: Chord) -> str:
    """Rôle de la note `pitch` d'une arrivée sous `chord` (voir `ARRIVAL_CLASSES`)."""
    pc = pitch % 12
    if pc == chord.bass:
        return "bass"
    rel = chord.relative(pc)
    if pc == chord.root:
        return "root"
    if rel in (3, 4):
        return "third"
    if rel == 7:
        return "fifth"
    if rel in (10, 11):
        return "seventh"
    return "other"


def nearest_with_pc(pitch: int, pc: int) -> int:
    """Hauteur de classe `pc` la plus proche de `pitch` (à l'égalité, la plus grave)."""
    delta = (pc - pitch + 6) % 12 - 6
    return pitch + delta


def approach_class(pitch: int, target: int, entering: Chord, outgoing: Chord) -> str:
    """Classe de la note d'approche `pitch` d'une arrivée sur `target` (hauteur de la cible)."""
    d = pitch - target
    if d == 0:
        return "same"
    if d == -1:
        return "chromatic_below"
    if d == 1:
        return "chromatic_above"
    if abs(d) in (2, 3) and pitch % 12 in entering.scale:
        return "diatonic"
    if abs(d) == 7:
        return "fifth"
    if pitch % 12 in outgoing.tones:
        return "chord_tone"
    return "other"


def is_nearest_scale_note(pitch: int, target: int, entering: Chord) -> bool:
    """`True` si aucune note de la gamme n'est entre `pitch` et `target` (définition du moteur)."""
    step = 1 if pitch > target else -1
    return all((target + k * step) % 12 not in entering.scale for k in range(1, abs(pitch - target)))


def passing_class(pitch: int, chord: Chord) -> str:
    """`chord_tone`, `scale_step` (dans la gamme hors accord) ou `chromatic`."""
    pc = pitch % 12
    if pc in chord.tones:
        return "chord_tone"
    return "scale_step" if pc in chord.scale else "chromatic"


# ── Accumulateur ─────────────────────────────────────────────────────────

@dataclass
class _Acc:
    """Comptes bruts accumulés suite après suite ; `summary()` en tire le JSON."""
    bars: int = 0
    runs: int = 0
    arrival: dict[str, Counter] = field(default_factory=lambda: {k: Counter() for k in (
        "change", "change_bar_start", "change_mid_bar", "bar_start_no_change")})
    approach: dict[str, Counter] = field(default_factory=lambda: {c: Counter() for c in APPROACH_CONTEXTS})
    approach_extra: dict[str, Counter] = field(default_factory=lambda: {c: Counter() for c in APPROACH_CONTEXTS})
    approach_distance: dict[str, Counter] = field(default_factory=lambda: {c: Counter() for c in APPROACH_CONTEXTS})
    passing: Counter = field(default_factory=Counter)
    passing_by_beat: dict[int, Counter] = field(default_factory=lambda: {b: Counter() for b in (2, 3, 4)})
    passing_engine: Counter = field(default_factory=Counter)
    passing_engine_by_beat: dict[int, Counter] = field(default_factory=lambda: {b: Counter() for b in (2, 3, 4)})
    intervals: Counter = field(default_factory=Counter)
    interval_values: list[int] = field(default_factory=list)
    direction: Counter = field(default_factory=Counter)
    keep: Counter = field(default_factory=Counter)
    toward: Counter = field(default_factory=Counter)
    pitches: list[int] = field(default_factory=list)
    transposed: list[int] = field(default_factory=list)
    arrival_pitches: list[int] = field(default_factory=list)
    chords_per_bar: Counter = field(default_factory=Counter)
    durations: Counter = field(default_factory=Counter)
    duration_total: int = 0
    change_beat: Counter = field(default_factory=Counter)

    def add_run(self, run: BassRun) -> None:
        line = [beat for bar in run.bars for beat in bar.beats]
        n = len(line)
        self.runs += 1
        self.bars += len(run.bars)
        chords = [b.chord for b in line]
        pitches = [b.pitch for b in line]
        prev = [run.bars[0].prev_chord] + chords[:-1]
        changed = [prev[i] is not None and chords[i] != prev[i] for i in range(n)]
        arrival = [i % BEATS == 0 or changed[i] for i in range(n)]

        self.pitches.extend(pitches)
        if run.key is not None:
            self.transposed.extend(p - run.key for p in pitches)

        # Rythme harmonique : accords par mesure, temps des changements, durées d'accord.
        for b in range(len(run.bars)):
            segments = 1 + sum(chords[i] != chords[i - 1] for i in range(b * BEATS + 1, b * BEATS + BEATS))
            self.chords_per_bar[str(segments)] += 1
        for i in range(n):
            if changed[i]:
                self.change_beat[str(i % BEATS + 1)] += 1
        starts = [i for i in range(n) if changed[i]]
        for a, b in zip(starts, starts[1:]):
            length = b - a
            self.durations[str(length) if length <= 8 else ">8"] += 1
            self.duration_total += length

        # Arrivées.
        for i in range(n):
            if not arrival[i]:
                continue
            cls = arrival_class(pitches[i], chords[i])
            if changed[i]:
                self.arrival["change"][cls] += 1
                self.arrival["change_bar_start" if i % BEATS == 0 else "change_mid_bar"][cls] += 1
            else:
                self.arrival["bar_start_no_change"][cls] += 1
            if cls == "bass":
                self.arrival_pitches.append(pitches[i])

        # Approches (le temps `i` précède l'arrivée `i+1` sans être une arrivée).
        approach_notes = set()
        for i in range(n - 1):
            if arrival[i] or not arrival[i + 1]:
                continue
            context = ("bar_change" if changed[i + 1] else "bar_same") if (i + 1) % BEATS == 0 else "mid_change"
            target = nearest_with_pc(pitches[i + 1], chords[i + 1].bass)
            cls = approach_class(pitches[i], target, chords[i + 1], chords[i])
            d = pitches[i] - target
            start = max(j for j in range(i + 1) if arrival[j])
            for ctx in (context, "all"):
                self.approach[ctx][cls] += 1
                self.approach_distance[ctx][str(abs(d)) if abs(d) <= 12 else ">12"] += 1
                extra = self.approach_extra[ctx]
                if cls in ("chromatic_below", "chromatic_above") and pitches[i] % 12 in chords[i + 1].scale:
                    extra["chromatic_in_scale"] += 1
                if cls == "diatonic" and is_nearest_scale_note(pitches[i], target, chords[i + 1]):
                    extra["diatonic_nearest"] += 1
                if cls in ("chromatic_below", "chromatic_above", "diatonic"):
                    approach_notes.add(i)
                    extra["above" if d > 0 else "below"] += 1
                    extra["rising" if pitches[i] > pitches[i - 1] else "falling" if pitches[i] < pitches[i - 1]
                          else "level"] += 1
                    extra["same_side_as_arrival" if (pitches[start] > target) == (d > 0) else "other_side"] += 1

        # Passages : ni arrivée ni temps qui précède une arrivée.
        for i in range(1, n - 1):
            if arrival[i]:
                continue
            if not arrival[i + 1]:
                cls = passing_class(pitches[i], chords[i])
                self.passing[cls] += 1
                self.passing_by_beat[i % BEATS + 1][cls] += 1
                self.passing_engine[cls] += 1
                self.passing_engine_by_beat[i % BEATS + 1][cls] += 1
                goal_index = next((j for j in range(i + 1, n) if arrival[j]), None)
                if goal_index is not None:
                    goal = pitches[goal_index]
                    toward = abs(pitches[i] - goal) < abs(pitches[i - 1] - goal)
                    self.toward["toward" if toward else "not_toward"] += 1
            elif i not in approach_notes:
                cls = passing_class(pitches[i], chords[i])
                self.passing_engine[cls] += 1
                self.passing_engine_by_beat[i % BEATS + 1][cls] += 1

        # Intervalles et sens.
        deltas = [pitches[i + 1] - pitches[i] for i in range(n - 1)]
        for dlt in deltas:
            size = abs(dlt)
            self.intervals[str(size) if size <= 12 else ">12"] += 1
            self.interval_values.append(size)
            if dlt:
                self.direction["up" if dlt > 0 else "down"] += 1
        for a, b in zip(deltas, deltas[1:]):
            if a and b:
                self.keep["keep" if (a > 0) == (b > 0) else "reverse"] += 1

    def summary(self) -> dict[str, Any]:
        """JSON de la mesure : comptes `n` et parts partout."""
        approach: dict[str, Any] = {}
        for ctx in APPROACH_CONTEXTS:
            block = counts_and_shares(self.approach[ctx], APPROACH_CLASSES)
            counts = self.approach[ctx]
            chromatic = counts["chromatic_below"] + counts["chromatic_above"]
            diatonic = counts["diatonic"]
            none = block["n"] - chromatic - diatonic
            block["weights"] = {"n": block["n"],
                                "counts": {"none": none, "chromatic": chromatic, "diatonic": diatonic},
                                "shares": {"none": share(none, block["n"]), "chromatic": share(chromatic, block["n"]),
                                           "diatonic": share(diatonic, block["n"])}}
            extra = self.approach_extra[ctx]
            moving = chromatic + diatonic
            block["moving"] = {
                "n": moving,
                "above_below": counts_and_shares(extra, ("above", "below")),
                "rising_falling": counts_and_shares(extra, ("rising", "falling", "level")),
                "side": counts_and_shares(extra, ("same_side_as_arrival", "other_side")),
                "chromatic_in_scale": extra["chromatic_in_scale"],
                "diatonic_nearest": extra["diatonic_nearest"],
            }
            block["distance"] = counts_and_shares(self.approach_distance[ctx], INTERVAL_KEYS)
            block["semitone_share"] = share(self.approach_distance[ctx]["1"], block["n"])
            block["whole_tone_share"] = share(self.approach_distance[ctx]["2"], block["n"])
            approach[ctx] = block
        intervals = counts_and_shares(self.intervals, INTERVAL_KEYS)
        intervals["percentiles"] = percentiles(self.interval_values, INTERVAL_PERCENTILES)
        intervals["repeat_share"] = share(self.intervals["0"], intervals["n"])
        intervals["up_down"] = counts_and_shares(self.direction, ("up", "down"))
        intervals["keep_direction"] = counts_and_shares(self.keep, ("keep", "reverse"))
        intervals["keep_direction"]["share"] = share(self.keep["keep"], sum(self.keep.values()))
        intervals["toward_target"] = counts_and_shares(self.toward, ("toward", "not_toward"))
        intervals["toward_target"]["share"] = share(self.toward["toward"], sum(self.toward.values()))
        arrival = {k: counts_and_shares(v, ARRIVAL_CLASSES) for k, v in self.arrival.items()}
        passing = counts_and_shares(self.passing, PASSING_CLASSES)
        passing["by_beat"] = {str(b): counts_and_shares(c, PASSING_CLASSES) for b, c in self.passing_by_beat.items()}
        window = best_window(self.arrival_pitches, 12)
        register = {
            "n": len(self.pitches),
            "pitch": percentiles(self.pitches, REGISTER_PERCENTILES),
            "pitch_range": [min(self.pitches), max(self.pitches)] if self.pitches else None,
            "relative_to_tonic": {"n": len(self.transposed),
                                  **percentiles(self.transposed, REGISTER_PERCENTILES)},
            "walk_window": {"low": percentiles(self.pitches, (2,))["p2"],
                            "high": percentiles(self.pitches, (98,))["p98"]},
            "arrival_window": {
                "n": len(self.arrival_pitches),
                "low": percentiles(self.arrival_pitches, (10,))["p10"],
                "high": percentiles(self.arrival_pitches, (90,))["p90"],
                "best_window_12": window,
            },
        }
        n_durations = sum(self.durations.values())
        rhythm = {
            "chords_per_bar": counts_and_shares(self.chords_per_bar, CHORDS_PER_BAR),
            "chord_duration_beats": {**counts_and_shares(self.durations, DURATION_KEYS),
                                     "mean": round(self.duration_total / n_durations, 3) if n_durations else None},
            "change_beat": counts_and_shares(self.change_beat, ("1", "2", "3", "4")),
        }
        n_changes = rhythm["change_beat"]["n"]
        rhythm["change_beat"]["share_beat1"] = share(self.change_beat["1"], n_changes)
        rhythm["change_beat"]["share_beat3"] = share(self.change_beat["3"], n_changes)
        rhythm["change_beat"]["share_other"] = share(self.change_beat["2"] + self.change_beat["4"], n_changes)
        return {
            "bars": self.bars,
            "runs": self.runs,
            "arrival": arrival,
            "approach": approach,
            "passage": passing,
            "passage_engine": {**counts_and_shares(self.passing_engine, PASSING_CLASSES),
                               "by_beat": {str(b): counts_and_shares(c, PASSING_CLASSES)
                                           for b, c in self.passing_engine_by_beat.items()}},
            "intervals": intervals,
            "register": register,
            "harmonic_rhythm": rhythm,
        }


def best_window(pitches: Sequence[int], span: int) -> dict[str, Any] | None:
    """Fenêtre de `span` demi-tons (`low..low+span-1`) qui contient le plus de `pitches`
    (à égalité, la plus grave) ; `None` si la série est vide."""
    if not pitches:
        return None
    counts = Counter(pitches)
    best = max(range(min(pitches), max(pitches) + 1),
               key=lambda low: (sum(counts[p] for p in range(low, low + span)), -low))
    inside = sum(counts[p] for p in range(best, best + span))
    return {"low": best, "high": best + span - 1, "n_inside": inside, "share_inside": share(inside, len(pitches))}


def measure_runs(runs: Iterable[BassRun]) -> dict[str, Any]:
    """Critères a–e et rythme harmonique sur des suites de mesures (corpus ou généré)."""
    acc = _Acc()
    for run in runs:
        if run.bars:
            acc.add_run(run)
    return acc.summary()


# ── Lecture de la base : solos → suites ──────────────────────────────────

@dataclass
class SoloData:
    """Un solo lu : faits, suites de mesures valides, structure des chorus."""
    info: wjazzd.SoloInfo
    runs: list[BassRun]
    beats_total: int = 0
    bars_total: int = 0
    bars_valid: int = 0
    bars_incomplete: int = 0
    bars_no_bass: int = 0
    bars_no_chord: int = 0
    chorus_bars: dict[int, int] = field(default_factory=dict)
    chorus_forms: dict[int, list[str]] = field(default_factory=dict)
    arrivals: int = 0  # arrivées (changements d'accord et 1ᵉʳ temps de mesure) de ses mesures valides
    arrivals_chord_tone: int = 0  # dont la note est une note de l'accord (basse, fondamentale, 3, 5, 7)

    @property
    def reliable(self) -> bool:
        """Solo à basse cohérente avec la grille : assez d'arrivées et part sur l'accord ≥ seuil."""
        return (self.arrivals >= RELIABLE_MIN_ARRIVALS
                and self.arrivals_chord_tone >= RELIABLE_MIN_CHORD_TONE_SHARE * self.arrivals)


@dataclass
class ParseStats:
    """Comptes d'analyse des symboles d'accord (sur les temps en 4/4 d'un chorus)."""
    beats_with_symbol: int = 0
    beats_nc: int = 0
    beats_no_symbol: int = 0
    beats_unparsed: int = 0
    symbols: Counter = field(default_factory=Counter)
    unparsed: Counter = field(default_factory=Counter)

    def summary(self) -> dict[str, Any]:
        analysed = self.beats_with_symbol - self.beats_unparsed
        return {
            "beats_with_symbol": self.beats_with_symbol,
            "beats_analysed": analysed,
            "beats_nc": self.beats_nc,
            "beats_no_symbol": self.beats_no_symbol,
            "beats_unparsed": self.beats_unparsed,
            "share_unparsed": share(self.beats_unparsed, self.beats_with_symbol),
            "distinct_symbols": len(self.symbols),
            "unparsed_symbols": dict(sorted(self.unparsed.items())),
        }


def read_solo_data(con: Any, info: wjazzd.SoloInfo, cache: dict[str, tuple[Chord | None, bool]],
                   parse: ParseStats) -> SoloData:
    """Lit un solo et le découpe en suites de mesures valides (4/4, basse complète, accord connu)."""
    data = SoloData(info=info, runs=[])
    beats = wjazzd.read_solo(con, info.melid, info.signature)
    data.beats_total = len(beats)
    run: BassRun | None = None
    last_bar: int | None = None
    last_chord: Chord | None = None
    for rows in wjazzd.bars_of(beats):
        bar_no = rows[0].bar
        data.bars_total += 1
        data.chorus_bars[rows[0].chorus_id] = data.chorus_bars.get(rows[0].chorus_id, 0) + 1
        labels = data.chorus_forms.setdefault(rows[0].chorus_id, [])
        if rows[0].form and (not labels or labels[-1] != rows[0].form):
            labels.append(rows[0].form)
        parsed: list[Chord | None] = []
        for row in rows:
            symbol = row.chord
            if symbol is None:
                parse.beats_no_symbol += 1
                parsed.append(None)
                continue
            parse.beats_with_symbol += 1
            parse.symbols[symbol] += 1
            if symbol not in cache:
                try:
                    cache[symbol] = (parse_wjazzd(symbol), True)
                except ChordParseError:
                    cache[symbol] = (None, False)
            chord, ok = cache[symbol]
            if symbol == "NC":
                parse.beats_nc += 1
            elif not ok:
                parse.beats_unparsed += 1
                parse.unparsed[symbol] += 1
            parsed.append(chord)
        valid = False
        if [r.beat for r in rows] != [1, 2, 3, 4]:
            data.bars_incomplete += 1
        elif any(r.bass_pitch is None for r in rows):
            data.bars_no_bass += 1
        elif any(c is None for c in parsed):
            data.bars_no_chord += 1
        else:
            valid = True
        if valid:
            bar = BassBar([Beat(c, r.bass_pitch) for c, r in zip(parsed, rows)],  # type: ignore[arg-type]
                          prev_chord=last_chord)
            if run is None or last_bar is None or bar_no != last_bar + 1:
                run = BassRun([], key=info.tonic)
                data.runs.append(run)
            run.bars.append(bar)
            data.bars_valid += 1
        else:
            run = None
        last_bar = bar_no
        last_chord = parsed[-1]
    acc = _Acc()
    for r in data.runs:
        acc.add_run(r)
    for key in ("change", "bar_start_no_change"):
        data.arrivals += sum(acc.arrival[key].values())
        data.arrivals_chord_tone += sum(v for k, v in acc.arrival[key].items() if k != "other")
    return data


def tempo_bin(tempo: float | None) -> str | None:
    """Identifiant de la tranche de tempo (`None` si le tempo est inconnu)."""
    if tempo is None:
        return None
    return next((name for name, lo, hi in TEMPO_BINS if lo <= tempo < hi), None)


def solo_structure(solos: Sequence[SoloData]) -> dict[str, Any]:
    """Tempos, formes et longueurs de chorus d'un groupe de solos (critères f, g, h)."""
    tempos = [s.info.avgtempo for s in solos if s.info.avgtempo is not None]
    lengths: Counter = Counter()
    sequences: Counter = Counter()
    for s in solos:
        # Le dernier chorus d'un solo peut être tronqué : on ne garde que les chorus qui le précèdent
        # (le seul chorus d'un solo d'un chorus est conservé).
        ids = sorted(s.chorus_bars)
        kept = ids[:-1] if len(ids) > 1 else ids
        for cid in kept:
            length = s.chorus_bars[cid]
            lengths[str(length)] += 1
            if length == 32:
                sequences[" ".join(s.chorus_forms[cid])] += 1
    top = {"12": lengths["12"], "16": lengths["16"], "32": lengths["32"]}
    top["other"] = sum(lengths.values()) - sum(top.values())
    n_choruses = sum(lengths.values())
    return {
        "solos": len(solos),
        "tempo": {"n": len(tempos), **percentiles(tempos, TEMPO_PERCENTILES),
                  "min": min(tempos) if tempos else None, "max": max(tempos) if tempos else None},
        "templates": dict(sorted(Counter(s.info.template or "(aucun)" for s in solos).items())),
        "composition_forms": dict(sorted(Counter(s.info.comp_form or "(aucune)" for s in solos).items())),
        "chorus_length": {"n": n_choruses, "counts": top,
                          "shares": {k: share(v, n_choruses) for k, v in top.items()},
                          "histogram": dict(sorted(lengths.items(), key=lambda kv: int(kv[0])))},
        "form_sequences_32": {"n": sum(sequences.values()),
                              "counts": dict(sequences.most_common(12))},
    }


def groups_of(solos: Sequence[SoloData]) -> dict[str, list[SoloData]]:
    """Groupes de solos : `all`, `blues`, `other_forms`, tranches de tempo."""
    groups: dict[str, list[SoloData]] = {
        "all": list(solos),
        "blues": [s for s in solos if s.info.is_blues],
        "other_forms": [s for s in solos if not s.info.is_blues],
        "reliable": [s for s in solos if s.reliable],
    }
    for name, _, _ in TEMPO_BINS:
        groups[name] = [s for s in solos if tempo_bin(s.info.avgtempo) == name]
    return groups


def group_summary(solos: Sequence[SoloData]) -> dict[str, Any]:
    """Mesures d'un groupe : comptes de solos/temps/mesures, critères a–h."""
    result = measure_runs(run for s in solos for run in s.runs)
    result["counts"] = {
        "solos": len(solos),
        "solos_with_bars": sum(1 for s in solos if s.bars_valid),
        "beats": sum(s.beats_total for s in solos),
        "bars": sum(s.bars_total for s in solos),
        "bars_valid": sum(s.bars_valid for s in solos),
        "bars_incomplete": sum(s.bars_incomplete for s in solos),
        "bars_no_bass": sum(s.bars_no_bass for s in solos),
        "bars_no_chord": sum(s.bars_no_chord for s in solos),
        "beats_valid": 4 * sum(s.bars_valid for s in solos),
    }
    result["structure"] = solo_structure(solos)
    return result


def build(db: Path = wjazzd.RAW_DB, expected: str = wjazzd.SHA256, command: str = "") -> dict[str, Any]:
    """Calcule le document `measures-bass.json` (déterministe)."""
    con = wjazzd.open_db(db, expected)
    try:
        infos = wjazzd.list_solos(con, wjazzd.SWING)
        cache: dict[str, tuple[Chord | None, bool]] = {}
        parse = ParseStats()
        solos = [read_solo_data(con, info, cache, parse) for info in infos]
    finally:
        con.close()
    groups = {name: group_summary(members) for name, members in groups_of(solos).items()}
    total = groups["all"]["counts"]
    return {
        "command": command or "python -m harmonium_lab.backing.bass_measures",
        "provenance": {
            "source": "Weimar Jazz Database (WJazzD)",
            "version": wjazzd.VERSION_LABEL,
            "sha256": expected,
            "licence": wjazzd.LICENCE,
            "attribution": wjazzd.ATTRIBUTION,
            "subset": "solo_info.rhythmfeel = 'SWING'; mesures 4/4 de chorus (bar >= 1) à quatre temps, "
                      "basse complète et accord connu (NC et symboles non analysés écartés)",
            "n_solos": total["solos"],
            "n_beats": total["beats"],
            "n_bars": total["bars"],
            "n_bars_valid": total["bars_valid"],
            "n_beats_valid": total["beats_valid"],
        },
        "tempo_bins": [{"id": name, "min_bpm": lo, "max_bpm": None if hi == float("inf") else hi}
                       for name, lo, hi in TEMPO_BINS],
        "chord_parsing": parse.summary(),
        "groups": groups,
    }


# ── Tableau lisible ──────────────────────────────────────────────────────

def _pct(value: float) -> str:
    return f"{100 * value:5.1f}%"


def _row(label: str, block: dict[str, Any], keys: Sequence[str]) -> str:
    cells = "  ".join(f"{k}={_pct(block['shares'][k])}" for k in keys)
    return f"  {label:<22} n={block['n']:<6} {cells}"


def summary_text(doc: dict[str, Any], group_names: Sequence[str] | None = None) -> str:
    """Tableau lisible d'un document `measures-bass.json`."""
    out: list[str] = []
    prov = doc["provenance"]
    out.append(f"{prov['source']} — {prov['version']}")
    out.append(f"sous-ensemble : {prov['n_solos']} solos, {prov['n_beats']} temps, {prov['n_bars']} mesures "
               f"({prov['n_bars_valid']} valides)")
    parsing = doc["chord_parsing"]
    out.append(f"accords : {parsing['beats_with_symbol']} temps avec symbole, "
               f"{parsing['beats_unparsed']} non analysés ({_pct(parsing['share_unparsed']).strip()}), "
               f"{parsing['beats_nc']} NC, {parsing['distinct_symbols']} symboles distincts")
    for name in group_names or doc["groups"]:
        g = doc["groups"][name]
        c = g["counts"]
        out.append("")
        out.append(f"== {name} : {c['solos']} solos, {c['bars_valid']} mesures valides sur {c['bars']} ==")
        out.append("Arrivée")
        for key in ("change", "change_bar_start", "change_mid_bar", "bar_start_no_change"):
            out.append(_row(key, g["arrival"][key], ARRIVAL_CLASSES))
        out.append("Approche (poids moteur : none / chromatic / diatonic)")
        for ctx in APPROACH_CONTEXTS:
            blk = g["approach"][ctx]
            out.append(_row(ctx, blk["weights"], ("none", "chromatic", "diatonic"))
                       + f"   haut/bas={_pct(blk['moving']['above_below']['shares']['above']).strip()}"
                       f"  1/2 ton={_pct(blk['semitone_share']).strip()}/{_pct(blk['whole_tone_share']).strip()}")
        out.append(_row("classes (all)", g["approach"]["all"], APPROACH_CLASSES))
        out.append("Passage")
        out.append(_row("tous", g["passage"], PASSING_CLASSES))
        for beat, blk in g["passage"]["by_beat"].items():
            out.append(_row(f"temps {beat}", blk, PASSING_CLASSES))
        iv = g["intervals"]
        out.append("Intervalles")
        p = iv["percentiles"]
        out.append(f"  |Δ| centiles 50/75/90/95/99 = {p['p50']}/{p['p75']}/{p['p90']}/{p['p95']}/{p['p99']}"
                   f"   répétitions={_pct(iv['repeat_share']).strip()}"
                   f"   keep_direction={_pct(iv['keep_direction']['share']).strip()} (n={iv['keep_direction']['n']})"
                   f"   toward_target={_pct(iv['toward_target']['share']).strip()} (n={iv['toward_target']['n']})")
        r = g["register"]
        pr = r["pitch"]
        out.append("Registre")
        out.append(f"  centiles 1/5/25/50/75/95/99 = "
                   + "/".join(str(pr[f'p{q}']) for q in REGISTER_PERCENTILES)
                   + f"   walk={r['walk_window']['low']}..{r['walk_window']['high']}"
                   f"   arrivées p10..p90={r['arrival_window']['low']}..{r['arrival_window']['high']}"
                   + (f"   fenêtre12={r['arrival_window']['best_window_12']['low']}.."
                      f"{r['arrival_window']['best_window_12']['high']}" if r["arrival_window"]["best_window_12"] else ""))
        h = g["harmonic_rhythm"]
        out.append("Rythme harmonique")
        out.append(_row("accords/mesure", h["chords_per_bar"], CHORDS_PER_BAR))
        out.append(_row("temps du changement", h["change_beat"], ("1", "2", "3", "4")))
        out.append(f"  durée moyenne d'un accord = {h['chord_duration_beats']['mean']} temps")
        s = g["structure"]
        t = s["tempo"]
        out.append("Tempos / formes")
        out.append(f"  avgtempo min/10/25/50/75/90/max = {t['min']}/{t['p10']}/{t['p25']}/{t['p50']}/"
                   f"{t['p75']}/{t['p90']}/{t['max']}")
        cl = s["chorus_length"]
        out.append(f"  chorus : n={cl['n']}  12={cl['counts']['12']}  16={cl['counts']['16']}  "
                   f"32={cl['counts']['32']}  autres={cl['counts']['other']}")
        out.append("  templates : " + ", ".join(f"{k}={v}" for k, v in s["templates"].items()))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", type=Path, default=wjazzd.RAW_DB)
    ap.add_argument("-o", "--output", type=Path, default=OUTPUT)
    ap.add_argument("--summary", action="store_true", help="affiche un tableau lisible du JSON déjà écrit")
    ap.add_argument("--group", action="append", help="groupe(s) du tableau (défaut : tous)")
    args = ap.parse_args(argv)
    try:
        if args.summary:
            print(summary_text(json.loads(args.output.read_text(encoding="utf-8")), args.group))
            return 0
        command = "python -m harmonium_lab.backing.bass_measures"
        if args.output != OUTPUT:
            command += f" -o {args.output}"
        doc = build(args.db, command=command)
    except (wjazzd.IntegrityError, OSError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    write_json(args.output, doc)
    prov = doc["provenance"]
    print(f"{args.output} : {prov['n_solos']} solos, {prov['n_beats']} temps, {prov['n_bars']} mesures "
          f"({prov['n_bars_valid']} valides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
