"""Mesures agrégées de la mélodie des solos swing de la Weimar Jazz Database (E12).

    python -m harmonium_lab.backing.melody_measures            # écrit references/wjazzd-melodie/measures-melody.json
    python -m harmonium_lab.backing.melody_measures --summary  # tableau lisible du JSON écrit

Sous-ensemble : `solo_info.rhythmfeel = 'SWING'`, mesures en 4/4 d'un chorus (`bar >= 1`) à quatre
temps. **Rien n'est copié** : le JSON ne porte que des comptes et des parts (ODbL 1.0, usage A :
*Produced Work*), jamais une suite de notes. L'index de suites de notes ne vit qu'en mémoire
(`NGramIndex`) et ne sert qu'à refuser une cellule qui le recopierait (`melody_cells`).

## Structure commune : `MBar`

Une mesure = huit croches (créneaux 0..7) ; `MNote(slot, pitch, dur)` une attaque sur un créneau,
`dur` la durée sonnante en croches (≥ 1, bornée à la fin de la mesure) ; `chords` l'accord à chacun des
quatre temps (`None` : `NC` ou symbole non analysé). Le corpus et le généré du moteur (`--record-truth`)
passent par les mêmes mesures (`measure`) : un seul chemin de calcul.

## Quantification (corpus)

Les temps sont ceux de la table `beats` (annotés à la main). Une attaque tombe à la fraction `f` de la
noire qui la contient : `f < 0,31` sur le temps, `0,31 ≤ f < 0,81` sur la croche d'après (la croche
swinguée est jouée vers `f` = 0,6 à 0,7), `f ≥ 0,81` sur le temps suivant. Seuils lus sur l'histogramme
de `f` (creux à 0,30 et à 0,85, 60 premiers solos). Deux attaques sur le même créneau (seizièmes) : la
plus longue reste, l'autre est comptée dans `dropped`. Durée sonnante : `round(durée / noire × 2)`, au
moins 1.

## Définitions

- **Phrase** : attaques consécutives séparées par moins d'une noire de silence ; un silence d'une noire
  ou plus (mesuré sur la fin sonnante de la note, pas sur la ligne de cellule) ou une mesure écartée
  ferme la phrase.
- **Cible** : une attaque sur un temps (créneaux pairs). Relation à l'accord en vigueur : `root`, `third`,
  `fifth`, `seventh`, `tone` (autre note de l'accord écrit : 6, 9, 11, 13 notés), `scale` (gamme de
  référence de `chords`, hors accord), `chromatic`. `strong` = temps 1 et 3, `beats` = les quatre.
- **Rôles de mesure** (pour ranger les statistiques sous les rôles de cellule du moteur) : `cad_half` /
  `cad_full` = mesure qui ferme une phrase (dernier accord dominant ou non), `open` = première mesure
  d'une phrase, sinon `arp` (la moitié des intervalles ≥ 3 demi-tons et les trois quarts des attaques
  dans l'accord), `run` (60 % des intervalles ≤ 2 demi-tons), `turn` (retour à une hauteur déjà jouée
  à ≤ 2 demi-tons), sinon `run` si 40 % d'intervalles conjoints, `arp` autrement. Les mesures de moins
  de trois attaques s'appellent `sparse` et ne servent qu'aux parts.
- **Intervalles** : demi-tons signés entre attaques consécutives d'une même phrase, dans une mesure
  (`in_bar`) ou d'une mesure à la suivante (`cross_bar`) ; classes de pas diatoniques par `steps_of`.
- **Anticipation** : attaque au créneau 7 ; `tied` = la mesure suivante ne rejoue pas de note au
  créneau 0 (liaison ou silence : irreprésentable dans une cellule, qui commence par une attaque).
"""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Sequence

from . import wjazzd
from ._util import ROUND, counts_and_shares, percentiles, share, write_json
from .chords import Chord, ChordParseError, from_engine, parse_wjazzd

SLOTS = 8
BEATS = 4
OUTPUT = wjazzd.REPO / "references" / "wjazzd-melodie" / "measures-melody.json"
MELODY_TRACK = 0
ROLES = ("open", "run", "arp", "turn", "cad_half", "cad_full")
RELATIONS = ("root", "third", "fifth", "seventh", "tone", "scale", "chromatic")
ON_BEAT, OFF_BEAT = 0.31, 0.81  # seuils de quantification de la fraction de noire
PHRASE_GAP_SLOTS = 2  # silence (en croches) qui ferme une phrase


class MNote(NamedTuple):
    slot: int
    pitch: int
    dur: int


@dataclass
class MBar:
    """Huit croches d'une mesure : attaques triées par créneau, accord de chaque temps."""
    bar: int
    notes: tuple[MNote, ...]
    chords: tuple[Chord | None, ...]
    gap_before: int = 0  # silence (croches) avant la première attaque, depuis la fin de la dernière note de la mesure précédente

    def chord_at(self, slot: int) -> Chord | None:
        return self.chords[slot // 2]


# ── Lecture du corpus ────────────────────────────────────────────────────

def _solo_bars(con, melid: int, solo_signature: str) -> tuple[list[MBar], int]:
    """Mesures d'un solo (en 4/4 d'un chorus, quatre temps) ; `dropped` = attaques sur créneau pris."""
    rows = wjazzd.read_solo(con, melid, solo_signature)
    chords: dict[tuple[int, int], Chord | None] = {}
    for row in rows:
        try:
            chords[(row.bar, row.beat)] = parse_wjazzd(row.chord) if row.chord else None
        except ChordParseError:
            chords[(row.bar, row.beat)] = None
    valid = sorted({b for b, _ in chords if all((b, k) in chords for k in range(1, BEATS + 1))})
    beat_rows = [(bar, beat, onset) for bar, beat, onset in
                 con.execute("select bar, beat, onset from beats where melid = ? order by beatid", (melid,))]
    onsets = [onset for _, _, onset in beat_rows]
    by_bar: dict[int, dict[int, tuple[int, int, int, float]]] = {}
    dropped = 0
    valid_set = set(valid)
    for onset, pitch, duration in con.execute(
            "select onset, pitch, duration from melody where melid = ? order by onset", (melid,)):
        i = bisect.bisect_right(onsets, onset) - 1
        if i < 0 or i + 1 >= len(onsets) or onsets[i + 1] <= onsets[i]:
            continue
        length = onsets[i + 1] - onsets[i]
        f = (onset - onsets[i]) / length
        bar, beat, _ = beat_rows[i]
        if f >= OFF_BEAT:
            if i + 1 >= len(beat_rows):
                continue
            bar, beat, _ = beat_rows[i + 1]
            slot_in_bar = (beat - 1) * 2
        else:
            slot_in_bar = (beat - 1) * 2 + (0 if f < ON_BEAT else 1)
        if bar not in valid_set or slot_in_bar >= SLOTS or bar < 1:
            continue
        dur = max(1, round(duration / length * 2))
        slots = by_bar.setdefault(bar, {})
        if slot_in_bar in slots:
            dropped += 1
            if slots[slot_in_bar][1] >= dur:
                continue
        slots[slot_in_bar] = (int(round(pitch)), dur, 0, 0.0)
    bars: list[MBar] = []
    for bar in valid:
        slots = by_bar.get(bar, {})
        notes = tuple(MNote(s, p, min(d, SLOTS - s)) for s, (p, d, _, _) in sorted(slots.items()))
        bars.append(MBar(bar, notes, tuple(chords[(bar, k)] for k in range(1, BEATS + 1))))
    _fill_gaps(bars)
    return bars, dropped


def _fill_gaps(bars: list[MBar]) -> None:
    """`gap_before` : silence (croches) entre la fin sonnante de la note précédente et la première
    attaque de la mesure, dans une suite de mesures contiguës (`SLOTS` au début d'une suite)."""
    last_end: int | None = None  # fin sonnante absolue de la dernière note, en croches
    base = 0
    previous: MBar | None = None
    for bar in bars:
        if previous is None or bar.bar != previous.bar + 1:
            last_end, base = None, 0
        else:
            base += SLOTS
        if bar.notes:
            bar.gap_before = SLOTS if last_end is None else max(0, base + bar.notes[0].slot - last_end)
            last_end = base + bar.notes[-1].slot + bar.notes[-1].dur
        previous = bar


def corpus_solos(db: Path = wjazzd.RAW_DB) -> tuple[list[list[MBar]], dict[str, int]]:
    """Mesures de tous les solos swing, une liste par solo, et les comptes de lecture."""
    con = wjazzd.open_db(db)
    solos: list[list[MBar]] = []
    stats = Counter()
    for solo in wjazzd.list_solos(con):
        bars, dropped = _solo_bars(con, solo.melid, solo.signature)
        if not bars:
            continue
        solos.append(bars)
        stats["solos"] += 1
        stats["bars"] += len(bars)
        stats["notes"] += sum(len(b.notes) for b in bars)
        stats["dropped"] += dropped
    return solos, dict(stats)


# ── Lecture du généré du moteur ──────────────────────────────────────────

def truth_solos(paths: Sequence[Path], track: int = MELODY_TRACK) -> tuple[list[list[MBar]], dict[str, int]]:
    """Mesures du premier air de fichiers `--record-truth` : une liste par fichier.

    Une attaque sur un pas impair (ornement) ou sur un créneau pris est comptée dans `dropped`.
    Les hauteurs sont absolues. L'accord d'un temps est le dernier changement dont le pas ≤ 4 × temps.
    """
    stats: Counter[str] = Counter()
    out: list[list[MBar]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        bars: list[MBar] = []
        for entry in data["measures"]:
            measure = entry["measure"]
            pos = measure["position"]
            if pos["tune_index"] != 0:
                continue
            changes = measure.get("chord_changes") or []
            try:
                timeline = [(int(c["start_step"]),
                             from_engine(int(c["context"]["root_pc"]), int(c["context"]["bass_pc"]),
                                         c["context"].get("quality") or "", bool(c["context"]["is_minor"])))
                            for c in changes]
                if not timeline:
                    timeline = [(0, from_engine(int(measure["chord_root_pc"]), int(measure["chord_bass_pc"]),
                                                measure.get("chord_quality") or "",
                                                bool(measure["chord_is_minor"])))]
            except ChordParseError:
                timeline = []
            beat_chords = tuple(
                ([c for s, c in timeline if s <= 4 * beat] or [None])[-1] if timeline else None
                for beat in range(BEATS))
            slots: dict[int, tuple[int, int]] = {}
            for n in measure["notes"]:
                if n["track"] != track:
                    continue
                start = int(n["start_step"])
                if start % 2:
                    stats["dropped"] += 1
                    continue
                slot = start // 2
                dur = max(1, round(int(n["duration_steps"]) / 2))
                if slot in slots:
                    stats["dropped"] += 1
                    if slots[slot][1] >= dur:
                        continue
                slots[slot] = (int(n["pitch"]), dur)
            notes = tuple(MNote(s, p, min(d, SLOTS - s)) for s, (p, d) in sorted(slots.items()))
            bars.append(MBar(int(entry["bar"]), notes, beat_chords))
        _fill_gaps(bars)
        out.append(bars)
        stats["files"] += 1
        stats["bars"] += len(bars)
        stats["notes"] += sum(len(b.notes) for b in bars)
    return out, dict(stats)


# ── Primitives de mesure ─────────────────────────────────────────────────

def steps_of(semitones: int) -> int:
    """Intervalle en demi-tons → pas diatoniques de la gamme majeure (signé, octave = 7)."""
    s = abs(semitones)
    table = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6, 12: 7}
    steps = table[s] if s in table else 7 + steps_of(s - 12) if s > 12 else 7
    return steps if semitones >= 0 else -steps


def relation(chord: Chord, pitch: int) -> str:
    """Relation de `pitch` à l'accord : note d'accord nommée, `tone`, `scale` ou `chromatic`."""
    rel = chord.relative(pitch % 12)
    if rel == 0:
        return "root"
    if chord.root != chord.bass and pitch % 12 == chord.bass:
        return "root"
    if pitch % 12 in chord.tones:
        if rel in (3, 4):
            return "third"
        if rel in (6, 7, 8) and chord.quality in ("dim", "hdim", "aug") or rel == 7:
            return "fifth"
        if rel in (10, 11):
            return "seventh"
        return "tone"
    if pitch % 12 in chord.scale:
        return "scale"
    return "chromatic"


def in_chord(chord: Chord, pitch: int) -> bool:
    return pitch % 12 in chord.tones or pitch % 12 == chord.bass


def phrase_runs(solo: Sequence[MBar]) -> Iterable[list[tuple[MBar, MNote]]]:
    """Phrases d'un solo : suites d'attaques sans silence d'une noire, dans des mesures contiguës."""
    run: list[tuple[MBar, MNote]] = []
    previous: MBar | None = None
    last_end = 0
    base = 0
    for bar in solo:
        if previous is not None and bar.bar != previous.bar + 1:
            if run:
                yield run
            run, last_end, base = [], 0, 0
        elif previous is not None:
            base += SLOTS
        for note in bar.notes:
            start = base + note.slot
            if run and start - last_end >= PHRASE_GAP_SLOTS:
                yield run
                run = []
            run.append((bar, note))
            last_end = start + note.dur
        previous = bar
    if run:
        yield run


def _classify(bar: MBar, first: bool, last: bool) -> str:
    """Rôle de cellule d'une mesure (voir la docstring du module)."""
    notes = bar.notes
    if len(notes) < 3:
        return "sparse"
    if last:
        chord = bar.chords[-1]
        return "cad_half" if chord is not None and chord.quality == "dom" else "cad_full"
    if first:
        return "open"
    pitches = [n.pitch for n in notes]
    ints = [b - a for a, b in zip(pitches, pitches[1:])]
    conj = share(sum(1 for i in ints if abs(i) <= 2), len(ints))
    leaps = share(sum(1 for i in ints if abs(i) >= 3), len(ints))
    tones = [in_chord(bar.chord_at(n.slot), n.pitch) for n in notes if bar.chord_at(n.slot) is not None]
    ct = share(sum(tones), len(tones)) if tones else 0.0
    if conj >= 0.6:
        return "run"
    if leaps >= 0.5 and ct >= 0.75:
        return "arp"
    for k, p in enumerate(pitches):
        for q in pitches[k + 2:k + 4]:
            if abs(p - q) <= 2 and (pitches[k + 1] - p) * (q - pitches[k + 1]) < 0 or p == q:
                return "turn"
    return "run" if conj >= 0.4 else "arp"


def _slot_context(bar: MBar, slot: int) -> int:
    """Contexte de la chaîne rythmique : états (attaque ou non) des deux créneaux qui précèdent."""
    attacks = {n.slot for n in bar.notes}
    return (slot - 1 in attacks) * 2 + (slot - 2 in attacks)


@dataclass
class _Acc:
    """Comptes d'un rôle (ou du total)."""
    bars: int = 0
    attacks: Counter = field(default_factory=Counter)  # attaques par mesure
    first_slot: Counter = field(default_factory=Counter)  # créneau de la première attaque
    rhythm: Counter = field(default_factory=Counter)  # (créneau, contexte) → [pas d'attaque, attaque]
    rhythm_start: Counter = field(default_factory=Counter)  # idem, mesures dont le créneau 0 est attaqué
    dur: Counter = field(default_factory=Counter)  # durée légato (jusqu'à l'attaque suivante) en croches
    in_bar: Counter = field(default_factory=Counter)  # intervalles en demi-tons dans la mesure
    steps: Counter = field(default_factory=Counter)  # idem en pas diatoniques
    bigram: Counter = field(default_factory=Counter)  # (pas précédent, pas suivant)
    first_rel: Counter = field(default_factory=Counter)  # relation de la première attaque
    ambitus: Counter = field(default_factory=Counter)  # ambitus de la mesure (demi-tons)
    biggest_leap: Counter = field(default_factory=Counter)  # plus grand saut de la mesure
    last_dur: Counter = field(default_factory=Counter)  # durée de la dernière attaque
    last_rel: Counter = field(default_factory=Counter)  # relation de la dernière attaque
    beat_chord: Counter = field(default_factory=Counter)  # attaques sur un temps : dans l'accord ou non
    off_chord: Counter = field(default_factory=Counter)  # attaques sur une croche : dans l'accord ou non

    def add(self, bar: MBar) -> None:
        self.bars += 1
        notes = bar.notes
        self.attacks[len(notes)] += 1
        if not notes:
            return
        self.first_slot[notes[0].slot] += 1
        attacks = {n.slot for n in notes}
        for slot in range(SLOTS):
            key = f"{slot}:{_slot_context(bar, slot)}"
            self.rhythm[(key, slot in attacks)] += 1
            if 0 in attacks:
                self.rhythm_start[(key, slot in attacks)] += 1
        for k, n in enumerate(notes):
            end = notes[k + 1].slot if k + 1 < len(notes) else SLOTS
            self.dur[end - n.slot] += 1
        pitches = [n.pitch for n in notes]
        ints = [b - a for a, b in zip(pitches, pitches[1:])]
        self.in_bar.update(ints)
        stp = [steps_of(i) for i in ints]
        self.steps.update(stp)
        self.bigram.update(zip(stp, stp[1:]))
        c0 = bar.chord_at(notes[0].slot)
        if c0 is not None:
            self.first_rel[relation(c0, notes[0].pitch)] += 1
        self.ambitus[max(pitches) - min(pitches)] += 1
        if ints:
            self.biggest_leap[max(abs(i) for i in ints)] += 1
        self.last_dur[SLOTS - notes[-1].slot] += 1
        c1 = bar.chord_at(notes[-1].slot)
        if c1 is not None:
            self.last_rel[relation(c1, notes[-1].pitch)] += 1
        for n in notes:
            chord = bar.chord_at(n.slot)
            if chord is not None:
                (self.off_chord if n.slot % 2 else self.beat_chord)[in_chord(chord, n.pitch)] += 1


def _rhythm_table(counter: Counter) -> dict[str, Any]:
    """`{"créneau:contexte": {"n", "attack"}}` (probabilité d'attaque sachant les deux créneaux précédents)."""
    table = {}
    for slot in range(SLOTS):
        for ctx in range(4):
            key = f"{slot}:{ctx}"
            no, yes = counter.get((key, False), 0), counter.get((key, True), 0)
            if no + yes:
                table[key] = {"n": no + yes, "attack": share(yes, no + yes)}
    return table


def _dist(counter: Counter, keys: Sequence[Any] | None = None) -> dict[str, Any]:
    keys = list(keys) if keys is not None else sorted(counter)
    named = Counter({str(k): v for k, v in counter.items()})
    return counts_and_shares(named, [str(k) for k in keys])


def _acc_doc(acc: _Acc) -> dict[str, Any]:
    n_attacks = sum(k * v for k, v in acc.attacks.items())
    return {
        "bars": acc.bars,
        "attacks_per_bar": {**_dist(acc.attacks, range(0, SLOTS + 1)),
                            "mean": round(n_attacks / acc.bars, ROUND) if acc.bars else 0.0},
        "first_slot": _dist(acc.first_slot, range(SLOTS)),
        "rhythm_markov": _rhythm_table(acc.rhythm),
        "rhythm_markov_from_downbeat": _rhythm_table(acc.rhythm_start),
        "legato_duration": _dist(acc.dur, range(1, SLOTS + 1)),
        "intervals_semitones": _dist(acc.in_bar, range(-12, 13)),
        "steps": _dist(acc.steps, range(-7, 8)),
        "step_bigram": {f"{a},{b}": v for (a, b), v in sorted(acc.bigram.items())},
        "beats_chord_share": share(acc.beat_chord[True], sum(acc.beat_chord.values())),
        "offbeat_chord_share": share(acc.off_chord[True], sum(acc.off_chord.values())),
        "first_relation": counts_and_shares(Counter(acc.first_rel), RELATIONS),
        "last_relation": counts_and_shares(Counter(acc.last_rel), RELATIONS),
        "last_duration": _dist(acc.last_dur, range(1, SLOTS + 1)),
        "ambitus": percentiles([k for k, v in acc.ambitus.items() for _ in range(v)], (10, 50, 90, 99)),
        "biggest_leap": percentiles([k for k, v in acc.biggest_leap.items() for _ in range(v)], (10, 50, 90, 99)),
    }


def measure(solos: Sequence[Sequence[MBar]]) -> dict[str, Any]:
    """Mesures agrégées de listes de mesures (corpus ou généré) : l'unique chemin de calcul."""
    total = _Acc()
    roles = {r: _Acc() for r in (*ROLES, "sparse")}
    slot_attack: Counter[int] = Counter()
    slot_all = 0
    anticipation = Counter()
    targets: dict[str, Counter] = {k: Counter() for k in ("beat1", "beat2", "beat3", "beat4", "strong", "beats",
                                                          "offbeat", "phrase_end")}
    phrase_beats: list[float] = []
    gaps: list[float] = []
    empty = nonempty = 0
    beats_silent = beats_total = 0
    cross: Counter[int] = Counter()
    pitches_all: list[int] = []
    keep_direction = Counter()
    for solo in solos:
        ends: set[tuple[int, int]] = set()
        starts: set[tuple[int, int]] = set()
        for run in phrase_runs(solo):
            first_bar, first_note = run[0]
            last_bar, last_note = run[-1]
            starts.add((first_bar.bar, first_note.slot))
            ends.add((last_bar.bar, last_note.slot))
            phrase_beats.append(round(((last_bar.bar - first_bar.bar) * SLOTS + last_note.slot + last_note.dur
                                       - first_note.slot) / 2, 1))
            for (ba, a), (bb, b) in zip(run, run[1:]):
                if ba is not bb:
                    cross[b.pitch - a.pitch] += 1
            ints = [b.pitch - a.pitch for (_, a), (_, b) in zip(run, run[1:])]
            for i, j in zip(ints, ints[1:]):
                if i and j:
                    keep_direction["same" if (i > 0) == (j > 0) else "reverse"] += 1
        for idx, bar in enumerate(solo):
            if not bar.notes:
                empty += 1
            else:
                nonempty += 1
                gaps.append(bar.gap_before / 2)
            beats_total += BEATS
            sounding = set()
            for n in bar.notes:
                sounding.update(range(n.slot // 2, min(BEATS, (n.slot + n.dur - 1) // 2 + 1)))
            beats_silent += BEATS - len(sounding)
            first = bool(bar.notes) and (bar.bar, bar.notes[0].slot) in starts
            last = bool(bar.notes) and (bar.bar, bar.notes[-1].slot) in ends
            role = _classify(bar, first, last) if bar.notes else "sparse"
            total.add(bar)
            roles[role].add(bar)
            pitches_all.extend(n.pitch for n in bar.notes)
            nxt = solo[idx + 1] if idx + 1 < len(solo) and solo[idx + 1].bar == bar.bar + 1 else None
            attacks = {n.slot for n in bar.notes}
            slot_all += 1
            slot_attack.update(attacks)
            if 7 in attacks:
                anticipation["bars_with_attack_7"] += 1
                if nxt is not None and 0 not in {n.slot for n in nxt.notes}:
                    anticipation["tied"] += 1
            if bar.notes and 0 not in attacks:
                anticipation["bars_without_downbeat"] += 1
            for n in bar.notes:
                chord = bar.chord_at(n.slot)
                if chord is None:
                    continue
                rel = relation(chord, n.pitch)
                if n.slot % 2 == 0:
                    beat = n.slot // 2
                    targets[f"beat{beat + 1}"][rel] += 1
                    targets["beats"][rel] += 1
                    if beat in (0, 2):
                        targets["strong"][rel] += 1
                else:
                    targets["offbeat"][rel] += 1
                if (bar.bar, n.slot) in ends:
                    targets["phrase_end"][rel] += 1
    doc = {
        "bars": {"n": total.bars, "empty": empty, "empty_share": share(empty, empty + nonempty)},
        "total": _acc_doc(total),
        "roles": {r: _acc_doc(a) for r, a in roles.items()},
        "role_shares": counts_and_shares(Counter({r: a.bars for r, a in roles.items()}), (*ROLES, "sparse")),
        "slot_attack_share": {str(s): share(slot_attack[s], slot_all) for s in range(SLOTS)},
        "anticipation": {
            "bars_with_attack_7": anticipation["bars_with_attack_7"],
            "bars_with_attack_7_share": share(anticipation["bars_with_attack_7"], total.bars),
            "tied": anticipation["tied"],
            "bars_without_downbeat": anticipation["bars_without_downbeat"],
            "bars_without_downbeat_share": share(anticipation["bars_without_downbeat"], nonempty),
        },
        "targets": {k: counts_and_shares(v, RELATIONS) for k, v in targets.items()},
        "strong_chord_share": share(sum(targets["strong"][r] for r in RELATIONS[:5]), sum(targets["strong"].values())),
        "beats_chord_share": share(sum(targets["beats"][r] for r in RELATIONS[:5]), sum(targets["beats"].values())),
        "offbeat_chord_share": share(sum(targets["offbeat"][r] for r in RELATIONS[:5]), sum(targets["offbeat"].values())),
        "register": percentiles(pitches_all, (1, 5, 10, 25, 50, 75, 90, 95, 99)),
        "cross_bar_intervals": _dist(cross, range(-12, 13)),
        "keep_direction": share(keep_direction["same"], keep_direction["same"] + keep_direction["reverse"]),
        "phrases": {"n": len(phrase_beats), "length_beats": percentiles(phrase_beats, (10, 25, 50, 75, 90)),
                    "bars_start_after_silence_beats": percentiles(gaps, (10, 25, 50, 75, 90))},
        "silence": {"beats_without_sound_share": share(beats_silent, beats_total)},
    }
    return doc


# ── Index de suites de notes (mémoire seulement) ─────────────────────────

class NGramIndex:
    """Suites de `n` attaques de tous les solos : `(intervalle, durée)` de chaque pas, en mémoire.

    L'intervalle est compté en **pas diatoniques** (`diatonic`, `steps_of` : une tierce mineure et une
    majeure sont la même suite ; c'est le grain d'une cellule, qui n'a pas de chromatisme) ou en demi-tons.
    `with_rhythm = False` retire les durées : le critère est alors celui du seul contour, plus sévère.
    La suite compte `n` notes, donc `n − 1` intervalles et les durées des `n − 1` premières notes (celle
    de la dernière dépend de la note suivante). Les suites ne franchissent pas un silence d'une noire.
    L'index n'est jamais écrit.
    """

    def __init__(self, solos: Sequence[Sequence[MBar]], n: int, *, diatonic: bool = True,
                 with_rhythm: bool = True) -> None:
        self.n, self.diatonic, self.with_rhythm = n, diatonic, with_rhythm
        self.keys: dict[tuple, set[int]] = {}
        for sid, solo in enumerate(solos):
            for run in phrase_runs(solo):
                pitches = [note.pitch for _, note in run]
                ints = [steps_of(b - a) if diatonic else b - a for a, b in zip(pitches, pitches[1:])]
                durs = [_legato(run, k) for k in range(len(run))]
                for key in ngrams(ints, durs, n, with_rhythm):
                    self.keys.setdefault(key, set()).add(sid)

    def __contains__(self, key: tuple) -> bool:
        return key in self.keys


def _legato(run: Sequence[tuple[MBar, MNote]], k: int) -> int:
    """Durée en croches d'une attaque de la phrase, jusqu'à l'attaque suivante (au plus 8)."""
    bar, note = run[k]
    if k + 1 < len(run):
        nbar, nnote = run[k + 1]
        return max(1, min(SLOTS, (nbar.bar - bar.bar) * SLOTS + nnote.slot - note.slot))
    return note.dur


def ngrams(intervals: Sequence[int], durs: Sequence[int], n: int, with_rhythm: bool = True) -> Iterable[tuple]:
    """Clés des suites de `n` notes : `intervals` (n − 1 par fenêtre) et `durs` de leurs notes de départ."""
    for i in range(len(intervals) - n + 2):
        yield tuple((intervals[i + k], durs[i + k] if with_rhythm else 0) for k in range(n - 1))


# ── Construction du JSON, CLI ────────────────────────────────────────────

NGRAM_SIZES = (4, 5, 6, 7, 8, 9, 10)


def ngram_sharing(solos: Sequence[Sequence[MBar]]) -> dict[str, Any]:
    """Pour chaque taille `n` et chaque critère : part des suites distinctes présentes dans ≥ 2 solos.

    Une suite courte est un idiome partagé (gamme, arpège) ; la taille à partir de laquelle presque
    toute suite n'appartient plus qu'à un solo fonde le `N` de `melody_cells` (voir son README).
    `steps_rhythm` : pas diatoniques et durées ; `steps` : pas seuls (le plus sévère) ;
    `semitones_rhythm` : demi-tons et durées.
    """
    criteria = {"steps_rhythm": dict(diatonic=True, with_rhythm=True),
                "steps": dict(diatonic=True, with_rhythm=False),
                "semitones_rhythm": dict(diatonic=False, with_rhythm=True)}
    out: dict[str, Any] = {}
    for n in NGRAM_SIZES:
        row = {}
        for name, kwargs in criteria.items():
            index = NGramIndex(solos, n, **kwargs)
            total = len(index.keys)
            shared = sum(1 for v in index.keys.values() if len(v) >= 2)
            row[name] = {"distinct": total, "in_two_solos_or_more": shared, "shared_share": share(shared, total)}
        out[str(n)] = row
    return out


def build(db: Path = wjazzd.RAW_DB, command: str = "python -m harmonium_lab.backing.melody_measures") -> dict[str, Any]:
    solos, stats = corpus_solos(db)
    doc = measure(solos)
    doc["provenance"] = {
        "source": wjazzd.VERSION_LABEL, "licence": wjazzd.LICENCE, "attribution": wjazzd.ATTRIBUTION,
        "subset": "rhythmfeel = SWING, mesures en 4/4 d'un chorus à quatre temps",
        "n_solos": stats["solos"], "n_bars": stats["bars"], "n_notes": stats["notes"],
        "dropped_notes": stats["dropped"], "command": command,
        "usage": "statistiques agrégées seulement ; aucune suite de notes n'est écrite",
    }
    doc["ngram_sharing"] = ngram_sharing(solos)
    return doc


def _row(label: str, dist: dict[str, Any], keys: Sequence[Any]) -> str:
    return f"  {label:<16}" + " ".join(f"{k}:{dist['shares'][str(k)]:.2f}" for k in keys)


def summary_text(doc: dict[str, Any]) -> str:
    p = doc["provenance"]
    out = [f"{p['n_solos']} solos, {p['n_bars']} mesures, {p['n_notes']} attaques "
           f"({p['dropped_notes']} écartées) ; mesures vides {doc['bars']['empty_share']}"]
    t = doc["total"]
    out.append(_row("attaques/mesure", t["attacks_per_bar"], range(0, 9)) + f"  moy {t['attacks_per_bar']['mean']}")
    out.append("  créneau d'attaque " + " ".join(f"{s}:{v}" for s, v in doc["slot_attack_share"].items()))
    out.append(f"  parts d'accord : temps forts {doc['strong_chord_share']}  quatre temps {doc['beats_chord_share']}  "
               f"croches {doc['offbeat_chord_share']}")
    out.append("  anticipation (créneau 7) " + str(doc["anticipation"]["bars_with_attack_7_share"])
               + "  sans note sur le temps 1 " + str(doc["anticipation"]["bars_without_downbeat_share"]))
    out.append("  rôles " + " ".join(f"{k}:{v}" for k, v in doc["role_shares"]["shares"].items()))
    out.append("  phrases (temps) " + str(doc["phrases"]["length_beats"]))
    for name in ("steps_rhythm", "steps", "semitones_rhythm"):
        out.append(f"  suites partagées par ≥ 2 solos ({name}) " + " ".join(
            f"n={n}:{v[name]['shared_share']}" for n, v in doc["ngram_sharing"].items()))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", type=Path, default=wjazzd.RAW_DB)
    ap.add_argument("-o", "--output", type=Path, default=OUTPUT)
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.summary:
            print(summary_text(json.loads(args.output.read_text(encoding="utf-8"))))
            return 0
        command = "python -m harmonium_lab.backing.melody_measures"
        if args.output != OUTPUT:
            command += f" -o {args.output}"
        doc = build(args.db, command)
    except (wjazzd.IntegrityError, OSError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    write_json(args.output, doc)
    print(f"{args.output} : {doc['provenance']['n_solos']} solos, {doc['provenance']['n_bars']} mesures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
