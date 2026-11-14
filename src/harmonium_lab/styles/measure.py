"""Mesures par style : basse, comping, batterie, mise en place.

Un accumulateur par (style, source, rôle) ; `add(piece)` y verse une pièce, `summary()` rend un
JSON d'agrégats (comptes, parts, centiles) : **aucune suite de notes d'un enregistrement** n'en sort,
seulement des motifs rythmiques de une mesure vus dans au moins deux pièces (`MIN_PIECES_PATTERN`).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from ..backing._util import percentiles as _percentiles
from ..backing.chords import Chord
from ..backing.gmd_styles import fine_role
from .core import Note, Piece, attacks, monophonic_bass, swing_ratio_of

TOP_PATTERNS = 12
MIN_PIECES_PATTERN = 2
PCTS = (10, 25, 50, 75, 90)
REG_PCTS = (1, 5, 25, 50, 75, 95, 99)
ROUND = 4
GRID_TOLERANCE = (
    0.18  # pas : au-delà, l'attaque n'est pas « sur la grille » (jeu humain)
)
QUANTIZED_SHARE = 0.9  # part d'attaques à moins de 0,05 pas : source séquencée
MIN_BAR_NOTES_FOR_REPEAT = 1

# Seuils de fiabilité : `assez` / `juste` / `peu` (comme L2, mêmes ordres de grandeur).
RELIABILITY_RULE = {
    "assez": "≥ 8 pièces, ≥ 3 interprètes (ou interprète inconnu), ≥ 300 mesures non vides",
    "juste": "≥ 3 pièces et ≥ 60 mesures non vides",
    "peu": "en dessous",
}


def reliability(n_pieces: int, n_performers: int | None, n_bars: int) -> str:
    if n_pieces >= 8 and n_bars >= 300 and (n_performers is None or n_performers >= 3):
        return "assez"
    if n_pieces >= 3 and n_bars >= 60:
        return "juste"
    return "peu"


def r(x: float | None, d: int = ROUND) -> float | None:
    return None if x is None else round(float(x), d)


def share(a: int | float, b: int | float) -> float | None:
    return round(a / b, ROUND) if b else None


def pcts(values: Sequence[float], qs: Iterable[int] = PCTS) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(values)}
    out.update(_percentiles(values, qs))
    if values:
        mean = sum(values) / len(values)
        out["mean"] = round(mean, ROUND)
        out["sd"] = round(
            math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)), ROUND
        )
    return out


# --- Grille ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Grid:
    spb: int  # pas par temps de noire
    bpb: float
    steps: int
    label: str

    @property
    def step_beats(self) -> float:
        return 1.0 / self.spb


def grid_for(piece: Piece) -> Grid:
    ternary = piece.feel == "ternary" and not piece.compound
    spb = 3 if ternary else 4
    steps = int(round(spb * piece.beats_per_bar))
    meter = {4.0: "4/4", 3.0: "3/4" if not piece.compound else "6/8", 2.0: "2/4"}.get(
        piece.beats_per_bar, f"{piece.beats_per_bar}"
    )
    if piece.compound and piece.beats_per_bar == 6.0:
        meter = "12/8"
    return Grid(
        spb,
        piece.beats_per_bar,
        steps,
        f"{meter} {'ternaire' if ternary else 'droit'} ({steps} pas)",
    )


def place(note_on: float, grid: Grid) -> tuple[int, int, float]:
    """(mesure, pas, écart signé en pas)."""
    pos = note_on * grid.spb
    k = int(round(pos))
    dev = pos - k
    return k // grid.steps, k % grid.steps, dev


def ms_per_step(bpm: float | None, grid: Grid) -> float | None:
    return None if not bpm else 60000.0 / bpm / grid.spb


def bars_by_index(
    notes: Sequence[Note], grid: Grid
) -> dict[int, list[tuple[int, Note, float]]]:
    bars: dict[int, list[tuple[int, Note, float]]] = defaultdict(list)
    for n in notes:
        if n.on < -1e-6:
            continue
        b, step, dev = place(n.on, grid)
        bars[b].append((step, n, dev))
    return bars


def pattern_key(steps: Iterable[int], n_steps: int) -> str:
    on = set(steps)
    return "".join("x" if i in on else "." for i in range(n_steps))


# --- Poids d'un interprète / d'un fichier -------------------------------------------------------


class _Common:
    """Effectifs et micro-timing partagés par les accumulateurs."""

    def __init__(self) -> None:
        self.pieces: set[str] = set()
        self.performers: set[str] = set()
        self.unknown_performer = 0
        self.bars = 0
        self.empty_bars = 0
        self.tempos: list[float] = []
        self.grids: Counter[str] = Counter()
        self.devs_ms: list[float] = []
        self.devs_ms_on: list[float] = []
        self.devs_ms_off: list[float] = []
        self.grid_hits = 0
        self.grid_total = 0
        self.quantized_hits = 0
        self.swing_positions: list[float] = []
        self.chord_known_pieces = 0
        self.chord_inferred_pieces = 0

    def _piece(self, piece: Piece, grid: Grid, onsets: Sequence[float]) -> None:
        self.pieces.add(f"{piece.source}:{piece.pid}")
        if piece.performer:
            self.performers.add(piece.performer)
        else:
            self.unknown_performer += 1
        if piece.bpm:
            self.tempos.append(piece.bpm)
        self.grids[grid.label] += 1
        if piece.chords:
            if piece.chords_inferred:
                self.chord_inferred_pieces += 1
            else:
                self.chord_known_pieces += 1
        ratio, n = swing_ratio_of(onsets)
        if ratio is not None:
            self.swing_positions.append(ratio)

    def _timing(self, piece: Piece, grid: Grid, step: int, dev: float) -> None:
        self.grid_total += 1
        if abs(dev) <= GRID_TOLERANCE:
            self.grid_hits += 1
        if abs(dev) < 0.05:
            self.quantized_hits += 1
        ms = ms_per_step(piece.bpm, grid)
        if ms is not None:
            self.devs_ms.append(dev * ms)
            (self.devs_ms_on if step % grid.spb == 0 else self.devs_ms_off).append(
                dev * ms
            )

    def common_summary(self) -> dict[str, Any]:
        n_perf = len(self.performers) if not self.unknown_performer else None
        out = {
            "pieces": len(self.pieces),
            "performers": len(self.performers) if self.performers else None,
            "performers_note": None
            if not self.unknown_performer
            else f"{self.unknown_performer} pièces sans interprète connu",
            "bars_non_empty": self.bars,
            "bars_empty": self.empty_bars,
            "tempo_bpm": pcts(self.tempos),
            "grids": dict(sorted(self.grids.items())),
            "swing_offbeat_position": {
                **pcts(self.swing_positions),
                "note": "position médiane de la croche retardée dans la noire par pièce : 0,5 droit, 0,667 triolet",
            },
            "chords": {
                "annotated_pieces": self.chord_known_pieces,
                "inferred_pieces": self.chord_inferred_pieces,
            },
            "reliability": reliability(len(self.pieces), n_perf, self.bars),
        }
        out["timing_to_grid"] = {
            "n": self.grid_total,
            "within_tolerance_share": share(self.grid_hits, self.grid_total),
            "quantized_share": share(self.quantized_hits, self.grid_total),
            "quantized_source": (
                self.quantized_hits / self.grid_total > QUANTIZED_SHARE
            )
            if self.grid_total
            else None,
            "signed_ms": pcts(self.devs_ms),
            "signed_ms_on_beat": pcts(self.devs_ms_on),
            "signed_ms_off_beat": pcts(self.devs_ms_off),
            "tolerance_steps": GRID_TOLERANCE,
        }
        return out


def _top_patterns(
    counter: Counter[str],
    who: dict[str, set[str]],
    total_bars: int,
    n_steps_note: str = "",
) -> list[dict[str, Any]]:
    rows = []
    for key, count in counter.most_common():
        if len(who[key]) < MIN_PIECES_PATTERN:
            continue
        grid, pattern = key.split("|", 1)
        rows.append(
            {
                "grid": grid,
                "pattern": pattern,
                "bars": count,
                "share": share(count, total_bars),
                "pieces": len(who[key]),
            }
        )
        if len(rows) >= TOP_PATTERNS:
            break
    return rows


def _bar_repetition(per_piece_bars: list[dict[int, Any]]) -> dict[str, Any]:
    """Part de mesures identiques (clé donnée) à la précédente, à la 2ᵉ, 4ᵉ, 8ᵉ d'avant."""
    out: dict[str, Any] = {}
    for lag in (1, 2, 4, 8):
        same = total = 0
        for bars in per_piece_bars:
            for b, key in bars.items():
                prev = bars.get(b - lag)
                if prev is None:
                    continue
                total += 1
                same += key == prev
        out[f"lag_{lag}"] = {"n": total, "same_share": share(same, total)}
    return out


# --- Basse -------------------------------------------------------------------------------------

DEGREE_CLASSES = (
    "root",
    "fifth",
    "third",
    "seventh",
    "other_chord_tone",
    "scale_step",
    "chromatic",
)
APPROACH_CLASSES = (
    "same_root",
    "semitone_below",
    "semitone_above",
    "tone_below",
    "tone_above",
    "fifth",
    "other",
)
POSITION_CLASSES = ("downbeat", "beat", "offbeat")


def degree_class(pitch: int, chord: Chord) -> str:
    rel = chord.relative(pitch % 12)
    if rel == 0:
        return "root"
    q = chord.quality
    if rel == 7 or (rel == 6 and q in ("dim", "hdim")) or (rel == 8 and q == "aug"):
        return "fifth"
    if rel in (3, 4) and (pitch % 12) in chord.tones:
        return "third"
    if rel in (10, 11) and (pitch % 12) in chord.tones:
        return "seventh"
    if (pitch % 12) in chord.tones:
        return "other_chord_tone"
    if (pitch % 12) in chord.scale:
        return "scale_step"
    return "chromatic"


def approach_class(last: int, next_chord: Chord) -> str:
    d = (next_chord.root - last) % 12
    if d == 0:
        return "same_root"
    return {
        1: "semitone_below",
        11: "semitone_above",
        2: "tone_below",
        10: "tone_above",
        7: "fifth",
        5: "fifth",
    }.get(d, "other")


class BassAcc(_Common):
    def __init__(self) -> None:
        super().__init__()
        self.patterns: Counter[str] = Counter()
        self.pattern_who: dict[str, set[str]] = defaultdict(set)
        self.notes_per_bar: Counter[int] = Counter()
        self.step_hits: dict[str, list[int]] = {}
        self.step_bars: Counter[str] = Counter()
        self.degree_by_pos: dict[str, Counter[str]] = {
            p: Counter() for p in POSITION_CLASSES
        }
        self.rel_pc: Counter[int] = Counter()
        self.approach: Counter[str] = Counter()
        self.arrival: Counter[str] = (
            Counter()
        )  # première note d'une mesure qui change d'accord
        self.register: list[int] = []
        self.legato: list[float] = []
        self.dur_beats: list[float] = []
        self.vel: list[int] = []
        self.vel_step: dict[str, list[float]] = {}
        self.vel_step_n: dict[str, list[int]] = {}
        self.piece_bars: list[dict[int, str]] = []
        self.piece_bars_pitch: list[dict[int, str]] = []
        self.intervals: Counter[int] = Counter()
        self.repeated_pitch = 0
        self.consecutive = 0
        self.vel_present = False

    def add(self, piece: Piece) -> bool:
        notes = monophonic_bass(piece.bass)
        if len(notes) < 8:
            return False
        grid = grid_for(piece)
        self._piece(piece, grid, [n.on for n in notes])
        bars = bars_by_index(notes, grid)
        key = grid.label
        hits = self.step_hits.setdefault(key, [0] * grid.steps)
        vel_sum = self.vel_step.setdefault(key, [0.0] * grid.steps)
        vel_n = self.vel_step_n.setdefault(key, [0] * grid.steps)
        vels = [n.vel for n in notes if n.vel is not None]
        vmed = sorted(vels)[len(vels) // 2] if vels else None
        if vels and len(set(vels)) > 1:
            self.vel_present = True
        pat_bars: dict[int, str] = {}
        pitch_bars: dict[int, str] = {}
        last_note = None
        bar_ids = sorted(bars)
        for b in range(bar_ids[0], bar_ids[-1] + 1):
            items = bars.get(b)
            if not items:
                self.empty_bars += 1
                continue
            items.sort(key=lambda it: it[1].on)
            steps = [s for s, _, _ in items]
            pat = pattern_key(steps, grid.steps)
            self.bars += 1
            self.step_bars[key] += 1
            self.patterns[key + "|" + pat] += 1
            self.pattern_who[key + "|" + pat].add(f"{piece.source}:{piece.pid}")
            self.notes_per_bar[len(items)] += 1
            pat_bars[b] = pat
            first_pitch = items[0][1].pitch
            pitch_bars[b] = (
                pat
                + ":"
                + ",".join(str((n.pitch - first_pitch) % 12) for _, n, _ in items)
            )
            for i, (step, n, dev) in enumerate(items):
                hits[step] += 1
                self._timing(piece, grid, step, dev)
                self.register.append(n.pitch)
                if n.vel is not None and vmed:
                    vel_sum[step] += n.vel / vmed
                    vel_n[step] += 1
                    self.vel.append(n.vel)
                nxt = items[i + 1][1].on if i + 1 < len(items) else (b + 1) * grid.bpb
                gap = nxt - n.on
                if gap > 1e-6 and n.dur > 0:
                    self.legato.append(min(n.dur / gap, 2.0))
                    self.dur_beats.append(n.dur)
                if last_note is not None:
                    d = abs(n.pitch - last_note)
                    self.intervals[min(d, 13)] += 1
                    self.consecutive += 1
                    self.repeated_pitch += d == 0
                last_note = n.pitch
                chord = piece.chord_at(n.on)
                if chord is not None:
                    pos = (
                        "downbeat"
                        if step == 0
                        else ("beat" if step % grid.spb == 0 else "offbeat")
                    )
                    self.degree_by_pos[pos][degree_class(n.pitch, chord)] += 1
                    self.rel_pc[chord.relative(n.pitch % 12)] += 1
            # Approche : dernière note de la mesure vers l'accord de la mesure suivante.
            nxt_start, this_start = (b + 1) * grid.bpb, b * grid.bpb
            c_now, c_next = (
                piece.chord_at(this_start + 1e-3),
                piece.chord_at(nxt_start + 1e-3),
            )
            if (
                c_now is not None
                and c_next is not None
                and (c_now.root != c_next.root or c_now.quality != c_next.quality)
            ):
                last_n = items[-1][1]
                self.approach[approach_class(last_n.pitch, c_next)] += 1
            # Arrivée : première note d'une mesure qui change d'accord.
            c_prev = piece.chord_at(this_start - 1e-3)
            if (
                c_now is not None
                and c_prev is not None
                and (c_now.root != c_prev.root or c_now.quality != c_prev.quality)
            ):
                if items[0][0] == 0:
                    self.arrival[degree_class(items[0][1].pitch, c_now)] += 1
                else:
                    self.arrival["late"] += 1
        self.piece_bars.append(pat_bars)
        self.piece_bars_pitch.append(pitch_bars)
        return True

    def summary(self) -> dict[str, Any]:
        out = self.common_summary()
        total_notes = sum(k * v for k, v in self.notes_per_bar.items())
        out["notes"] = total_notes
        out["notes_per_bar"] = {
            "mean": r(total_notes / self.bars if self.bars else None),
            "distribution": {
                str(k): share(v, self.bars)
                for k, v in sorted(self.notes_per_bar.items())
            },
        }
        out["rhythm_patterns"] = _top_patterns(
            self.patterns, self.pattern_who, self.bars
        )
        out["rhythm_patterns_note"] = (
            f"un motif = une mesure ; vu dans ≥ {MIN_PIECES_PATTERN} pièces ; grilles : voir `grids`"
        )
        out["step_probability"] = {
            k: [share(h, self.step_bars[k]) for h in v]
            for k, v in sorted(self.step_hits.items())
        }
        deg: dict[str, Any] = {}
        for pos, counter in self.degree_by_pos.items():
            tot = sum(counter.values())
            deg[pos] = {
                "n": tot,
                **{c: share(counter.get(c, 0), tot) for c in DEGREE_CLASSES},
            }
        out["degrees"] = deg
        tot_rel = sum(self.rel_pc.values())
        out["interval_to_chord_root"] = {
            "n": tot_rel,
            "shares": {
                str(i): share(self.rel_pc.get(i, 0), tot_rel) for i in range(12)
            },
        }
        tot_ap = sum(self.approach.values())
        out["approach_to_next_chord"] = {
            "n": tot_ap,
            **{c: share(self.approach.get(c, 0), tot_ap) for c in APPROACH_CLASSES},
        }
        tot_ar = sum(self.arrival.values())
        out["arrival_on_chord_change"] = {
            "n": tot_ar,
            **{
                c: share(self.arrival.get(c, 0), tot_ar)
                for c in (*DEGREE_CLASSES, "late")
            },
        }
        out["register_midi"] = pcts(self.register, REG_PCTS)
        out["legato_ratio"] = {
            **pcts(self.legato),
            "staccato_share_lt_0_5": share(
                sum(1 for v in self.legato if v < 0.5), len(self.legato)
            ),
            "legato_share_ge_0_9": share(
                sum(1 for v in self.legato if v >= 0.9), len(self.legato)
            ),
        }
        out["duration_beats"] = pcts(self.dur_beats)
        iv_tot = sum(self.intervals.values())
        out["intervals"] = {
            "n": iv_tot,
            "repeated_pitch_share": share(self.repeated_pitch, self.consecutive),
            "shares": {
                ("13+" if k == 13 else str(k)): share(self.intervals.get(k, 0), iv_tot)
                for k in range(14)
            },
        }
        out["velocity"] = self._velocity()
        out["repetition_rhythm"] = _bar_repetition(self.piece_bars)
        out["repetition_rhythm_and_contour"] = _bar_repetition(self.piece_bars_pitch)
        return out

    def _velocity(self) -> dict[str, Any]:
        if not self.vel_present:
            return {
                "available": False,
                "note": "vélocités absentes ou constantes dans cette source",
            }
        mean = sum(self.vel) / len(self.vel)
        sd = math.sqrt(sum((v - mean) ** 2 for v in self.vel) / len(self.vel))
        rel = {}
        for k, sums in self.vel_step.items():
            rel[k] = [
                r(s / n) if n >= 10 else None for s, n in zip(sums, self.vel_step_n[k])
            ]
        return {
            "available": True,
            "mean": r(mean, 2),
            "sd": r(sd, 2),
            "n": len(self.vel),
            "relative_to_piece_median_by_step": rel,
        }


# --- Comping -----------------------------------------------------------------------------------


class CompAcc(_Common):
    def __init__(self) -> None:
        super().__init__()
        self.patterns: Counter[str] = Counter()
        self.pattern_who: dict[str, set[str]] = defaultdict(set)
        self.attacks_per_bar: Counter[int] = Counter()
        self.step_hits: dict[str, list[int]] = {}
        self.step_bars: Counter[str] = Counter()
        self.notes_per_attack: Counter[int] = Counter()
        self.span: list[int] = []
        self.low: list[int] = []
        self.high: list[int] = []
        self.mean_pitch: list[float] = []
        self.stacks: Counter[str] = Counter()
        self.rel_pc: Counter[int] = Counter()
        self.chord_attacks = 0
        self.has_third = self.has_seventh = self.has_root = (
            self.has_third_and_seventh
        ) = self.tension_attacks = 0
        self.dur_beats: list[float] = []
        self.dur_ratio: list[float] = []
        self.vel: list[int] = []
        self.vel_step: dict[str, list[float]] = {}
        self.vel_step_n: dict[str, list[int]] = {}
        self.ghost = 0
        self.vel_notes = 0
        self.offbeat = 0
        self.anticipation = 0
        self.attacks_total = 0
        self.piece_bars: list[dict[int, str]] = []
        self.piece_bars_set: list[dict[int, str]] = []
        self.kind: Counter[str] = Counter()
        self.vel_present = False

    def add(self, piece: Piece) -> bool:
        groups = attacks(piece.comp)
        if len(groups) < 8:
            return False
        grid = grid_for(piece)
        self.kind[piece.comp_kind] += 1
        self._piece(piece, grid, [g[0].on for g in groups])
        key = grid.label
        hits = self.step_hits.setdefault(key, [0] * grid.steps)
        vsum = self.vel_step.setdefault(key, [0.0] * grid.steps)
        vn = self.vel_step_n.setdefault(key, [0] * grid.steps)
        vels = [n.vel for n in piece.comp if n.vel is not None]
        vmed = sorted(vels)[len(vels) // 2] if vels else None
        if vels and len(set(vels)) > 1:
            self.vel_present = True
        by_bar: dict[int, list[tuple[int, list[Note], float]]] = defaultdict(list)
        for g in groups:
            b, step, dev = place(g[0].on, grid)
            if g[0].on >= 0:
                by_bar[b].append((step, g, dev))
        pat_bars: dict[int, str] = {}
        set_bars: dict[int, str] = {}
        ids = sorted(by_bar)
        for b in range(ids[0], ids[-1] + 1):
            items = by_bar.get(b)
            if not items:
                self.empty_bars += 1
                continue
            steps = sorted({s for s, _, _ in items})
            pat = pattern_key(steps, grid.steps)
            self.bars += 1
            self.step_bars[key] += 1
            self.patterns[key + "|" + pat] += 1
            self.pattern_who[key + "|" + pat].add(f"{piece.source}:{piece.pid}")
            self.attacks_per_bar[len(items)] += 1
            pat_bars[b] = pat
            set_bars[b] = (
                pat
                + ":"
                + "|".join(
                    ",".join(str(p % 12) for p in sorted({n.pitch for n in g}))
                    for _, g, _ in items
                )
            )
            for step, g, dev in items:
                hits[step] += 1
                self._timing(piece, grid, step, dev)
                self.attacks_total += 1
                pitches = sorted({n.pitch for n in g})
                self.notes_per_attack[min(len(pitches), 8)] += 1
                self.low.append(pitches[0])
                self.high.append(pitches[-1])
                self.span.append(pitches[-1] - pitches[0])
                self.mean_pitch.append(sum(pitches) / len(pitches))
                if len(pitches) > 1:
                    self.stacks[
                        ",".join(str(b2 - a2) for a2, b2 in zip(pitches, pitches[1:]))
                    ] += 1
                self.dur_beats.append(sorted(n.dur for n in g)[len(g) // 2])
                if step % grid.spb != 0:
                    self.offbeat += 1
                if step >= grid.steps - max(1, grid.spb // 2):
                    self.anticipation += 1
                for n in g:
                    if n.vel is not None and vmed:
                        self.vel.append(n.vel)
                        vsum[step] += n.vel / vmed
                        vn[step] += 1
                        self.vel_notes += 1
                        self.ghost += n.vel < 0.6 * vmed
                chord = piece.chord_at(g[0].on)
                if chord is not None:
                    self.chord_attacks += 1
                    pcs = {p % 12 for p in pitches}
                    rel = {chord.relative(p) for p in pcs}
                    for rl in rel:
                        self.rel_pc[rl] += 1
                    third = bool(rel & {3, 4}) and any(
                        chord.relative(p) in (3, 4) for p in pcs if p in chord.tones
                    )
                    seventh = bool(rel & {10, 11}) and any(
                        chord.relative(p) in (10, 11) for p in pcs if p in chord.tones
                    )
                    self.has_third += third
                    self.has_seventh += seventh
                    self.has_third_and_seventh += third and seventh
                    self.has_root += 0 in rel
                    self.tension_attacks += any(
                        p not in chord.tones and p in chord.scale for p in pcs
                    )
        self.piece_bars.append(pat_bars)
        self.piece_bars_set.append(set_bars)
        # Durée relative à l'intervalle jusqu'à l'attaque suivante.
        ordered = [(g[0].on, sorted(n.dur for n in g)[len(g) // 2]) for g in groups]
        for (t0, d), (t1, _) in zip(ordered, ordered[1:]):
            if t1 - t0 > 1e-6:
                self.dur_ratio.append(min(d / (t1 - t0), 2.0))
        return True

    def summary(self) -> dict[str, Any]:
        out = self.common_summary()
        out["voices"] = dict(self.kind)
        out["attacks"] = self.attacks_total
        out["attacks_per_bar"] = {
            "mean": r(self.attacks_total / self.bars if self.bars else None),
            "distribution": {
                str(k): share(v, self.bars)
                for k, v in sorted(self.attacks_per_bar.items())
            },
        }
        out["rhythm_patterns"] = _top_patterns(
            self.patterns, self.pattern_who, self.bars
        )
        out["rhythm_patterns_note"] = (
            f"un motif = les pas d'attaque d'une mesure ; vu dans ≥ {MIN_PIECES_PATTERN} pièces"
        )
        out["step_probability"] = {
            k: [share(h, self.step_bars[k]) for h in v]
            for k, v in sorted(self.step_hits.items())
        }
        out["offbeat_attack_share"] = share(self.offbeat, self.attacks_total)
        out["anticipation_share"] = {
            "value": share(self.anticipation, self.attacks_total),
            "definition": "attaques dans la dernière croche de la mesure (anticipation du temps 1 suivant)",
        }
        tot = sum(self.notes_per_attack.values())
        out["notes_per_attack"] = {
            "n": tot,
            "shares": {
                ("8+" if k == 8 else str(k)): share(
                    self.notes_per_attack.get(k, 0), tot
                )
                for k in range(1, 9)
            },
        }
        out["register_midi"] = {
            "lowest": pcts(self.low, REG_PCTS),
            "highest": pcts(self.high, REG_PCTS),
            "mean": pcts(self.mean_pitch, REG_PCTS),
        }
        out["span_semitones"] = pcts(self.span)
        stack_total = sum(self.stacks.values())
        out["voicing_stacks"] = {
            "n_multi_note_attacks": stack_total,
            "top": [
                {"gaps": k, "share": share(v, stack_total)}
                for k, v in self.stacks.most_common(15)
            ],
            "note": "écarts en demi-tons entre notes adjacentes, du grave à l'aigu",
        }
        ca = self.chord_attacks
        out["voicing_vs_chord"] = {
            "n": ca,
            "third_present": share(self.has_third, ca),
            "seventh_present": share(self.has_seventh, ca),
            "third_and_seventh": share(self.has_third_and_seventh, ca),
            "root_present": share(self.has_root, ca),
            "scale_tension_present": share(self.tension_attacks, ca),
            "interval_to_root_presence": {
                str(i): share(self.rel_pc.get(i, 0), ca) for i in range(12)
            },
        }
        out["duration_beats"] = pcts(self.dur_beats)
        out["duration_over_gap"] = {
            **pcts(self.dur_ratio),
            "staccato_share_lt_0_5": share(
                sum(1 for v in self.dur_ratio if v < 0.5), len(self.dur_ratio)
            ),
        }
        if not self.vel_present:
            out["velocity"] = {
                "available": False,
                "note": "vélocités absentes ou constantes dans cette source",
            }
        else:
            mean = sum(self.vel) / len(self.vel)
            sd = math.sqrt(sum((v - mean) ** 2 for v in self.vel) / len(self.vel))
            out["velocity"] = {
                "available": True,
                "mean": r(mean, 2),
                "sd": r(sd, 2),
                "n": len(self.vel),
                "ghost_note_share_lt_60pct_of_median": share(
                    self.ghost, self.vel_notes
                ),
                "relative_to_piece_median_by_step": {
                    k: [
                        r(s / n) if n >= 10 else None
                        for s, n in zip(sums, self.vel_step_n[k])
                    ]
                    for k, sums in self.vel_step.items()
                },
            }
        out["repetition_rhythm"] = _bar_repetition(self.piece_bars)
        out["repetition_rhythm_and_pitch_classes"] = _bar_repetition(
            self.piece_bars_set
        )
        return out


# --- Batterie ----------------------------------------------------------------------------------

DRUM_ROLES = (
    "kick",
    "snare",
    "sidestick",
    "hat_closed",
    "hat_open",
    "hat_pedal",
    "ride",
    "ride_bell",
    "crash",
    "tom",
)


def drum_role(pitch: int) -> str | None:
    role = fine_role(pitch)
    if role is None:
        return None
    return "tom" if role.startswith("tom") else role


class DrumAcc(_Common):
    def __init__(self) -> None:
        super().__init__()
        self.step_hits: dict[str, dict[str, list[int]]] = {}
        self.step_vel: dict[str, dict[str, list[float]]] = {}
        self.step_bars: Counter[str] = Counter()
        self.kick_pat: Counter[str] = Counter()
        self.snare_pat: Counter[str] = Counter()
        self.ks_pat: Counter[str] = Counter()
        self.who: dict[str, set[str]] = defaultdict(set)
        self.density: dict[str, list[int]] = defaultdict(list)
        self.keeper: Counter[str] = Counter()
        self.figure: Counter[str] = Counter()
        self.vel: dict[str, list[int]] = defaultdict(list)
        self.piece_bars: list[dict[int, str]] = []
        self.role_dev_ms: dict[str, list[float]] = defaultdict(list)
        self.vel_present = False

    def add(self, piece: Piece) -> bool:
        hits = [(n, drum_role(n.pitch)) for n in piece.drums]
        hits = [(n, role) for n, role in hits if role]
        if len(hits) < 16:
            return False
        grid = grid_for(piece)
        self._piece(
            piece,
            grid,
            [n.on for n, role in hits if role in ("hat_closed", "ride", "hat_open")],
        )
        key = grid.label
        sh = self.step_hits.setdefault(
            key, {role: [0] * grid.steps for role in DRUM_ROLES}
        )
        sv = self.step_vel.setdefault(
            key, {role: [0.0] * grid.steps for role in DRUM_ROLES}
        )
        by_bar: dict[int, list[tuple[int, Note, str, float]]] = defaultdict(list)
        for n, role in hits:
            if n.on < 0:
                continue
            b, step, dev = place(n.on, grid)
            by_bar[b].append((step, n, role, dev))
        meds: dict[str, float] = {}
        for role in DRUM_ROLES:
            vs = sorted(n.vel for n, ro in hits if ro == role and n.vel is not None)
            if vs:
                meds[role] = vs[len(vs) // 2]
        if any(len({n.vel for n, ro in hits if ro == role}) > 1 for role in meds):
            self.vel_present = True
        pat_bars: dict[int, str] = {}
        ids = sorted(by_bar)
        for b in range(ids[0], ids[-1] + 1):
            items = by_bar.get(b)
            if not items:
                self.empty_bars += 1
                continue
            self.bars += 1
            self.step_bars[key] += 1
            per_role: dict[str, set[int]] = defaultdict(set)
            for step, n, role, dev in items:
                sh[role][step] += 1
                if n.vel is not None and meds.get(role):
                    sv[role][step] += n.vel / meds[role]
                    self.vel[role].append(n.vel)
                per_role[role].add(step)
                self._timing(piece, grid, step, dev)
                ms = ms_per_step(piece.bpm, grid)
                if ms is not None:
                    self.role_dev_ms[role].append(dev * ms)
            for role in DRUM_ROLES:
                self.density[role].append(sum(1 for it in items if it[2] == role))
            kp, sp = (
                pattern_key(per_role.get("kick", ()), grid.steps),
                pattern_key(
                    per_role.get("snare", set()) | per_role.get("sidestick", set()),
                    grid.steps,
                ),
            )
            ks = kp + "/" + sp
            pid = f"{piece.source}:{piece.pid}"
            for counter, k in (
                (self.kick_pat, kp),
                (self.snare_pat, sp),
                (self.ks_pat, ks),
            ):
                counter[key + "|" + k] += 1
                self.who[key + "|" + k].add(pid)
            pat_bars[b] = ks
            counts = {
                role: len(per_role.get(role, ()))
                for role in ("ride", "hat_closed", "hat_open", "ride_bell")
            }
            keeper = max(counts, key=lambda k: counts[k])
            if counts[keeper] >= 2:
                self.keeper[keeper] += 1
                steps = per_role[keeper]
                if len(steps) <= 5 and all(s % grid.spb == 0 for s in steps):
                    fig = "quarters"
                elif (
                    all(s % max(1, grid.spb // 2) == 0 for s in steps)
                    and len(steps) <= grid.steps // grid.spb * 2 + 1
                ):
                    fig = "eighths"
                elif len(steps) > grid.steps // 2:
                    fig = "sixteenths_or_triplets"
                else:
                    fig = "other"
                self.figure[fig] += 1
        self.piece_bars.append(pat_bars)
        return True

    def summary(self) -> dict[str, Any]:
        out = self.common_summary()
        out["step_probability_by_role"] = {
            k: {
                role: [share(h, self.step_bars[k]) for h in hs]
                for role, hs in sorted(roles.items())
                if sum(hs) > 0
            }
            for k, roles in sorted(self.step_hits.items())
        }
        out["hits_per_bar_by_role"] = {
            role: r(sum(v) / len(v), 2)
            for role, v in sorted(self.density.items())
            if v and sum(v) > 0
        }
        tot = sum(self.keeper.values())
        out["timekeeper"] = {
            "n": tot,
            **{k: share(v, tot) for k, v in sorted(self.keeper.items())},
        }
        tf = sum(self.figure.values())
        out["timekeeper_figure"] = {
            "n": tf,
            **{k: share(v, tf) for k, v in sorted(self.figure.items())},
        }
        out["kick_patterns"] = _top_patterns(self.kick_pat, self.who, self.bars)
        out["snare_patterns"] = _top_patterns(self.snare_pat, self.who, self.bars)
        out["kick_snare_patterns"] = _top_patterns(self.ks_pat, self.who, self.bars)
        out["velocity_by_role"] = (
            {
                role: {"mean": r(sum(v) / len(v), 1), "n": len(v)}
                for role, v in sorted(self.vel.items())
                if v
            }
            if self.vel_present
            else {"available": False}
        )
        out["role_signed_ms_vs_grid"] = {
            role: {"median": r(sorted(v)[len(v) // 2], 1), "n": len(v)}
            for role, v in sorted(self.role_dev_ms.items())
            if len(v) >= 30
        }
        out["repetition_kick_snare"] = _bar_repetition(self.piece_bars)
        return out


# --- Mise en place -----------------------------------------------------------------------------


class SyncAcc:
    """Asynchronies basse ↔ grosse caisse et comping ↔ caisse claire (même pièce multipiste)."""

    WINDOW_BEATS = 0.125

    def __init__(self) -> None:
        self.bass_kick: list[float] = []
        self.comp_snare: list[float] = []
        self.pieces: set[str] = set()
        self.quantized = 0
        self.n_pieces = 0

    def add(self, piece: Piece) -> bool:
        if not piece.drums or not (piece.bass or piece.comp) or not piece.bpm:
            return False
        kicks = sorted(n.on for n in piece.drums if drum_role(n.pitch) == "kick")
        snares = sorted(
            n.on for n in piece.drums if drum_role(n.pitch) in ("snare", "sidestick")
        )
        ms = 60000.0 / piece.bpm
        before = len(self.bass_kick) + len(self.comp_snare)
        import bisect

        def pairs(src: Iterable[float], ref: list[float], out: list[float]) -> None:
            for t in src:
                i = bisect.bisect_left(ref, t)
                cands = [ref[j] for j in (i - 1, i) if 0 <= j < len(ref)]
                if not cands:
                    continue
                near = min(cands, key=lambda x: abs(x - t))
                if abs(near - t) <= self.WINDOW_BEATS:
                    out.append((t - near) * ms)

        pairs([n.on for n in monophonic_bass(piece.bass)], kicks, self.bass_kick)
        pairs([g[0].on for g in attacks(piece.comp)], snares, self.comp_snare)
        if len(self.bass_kick) + len(self.comp_snare) == before:
            return False
        self.pieces.add(f"{piece.source}:{piece.pid}")
        self.n_pieces += 1
        self.quantized += bool(piece.quantized)
        return True

    def summary(self) -> dict[str, Any]:
        exact = sum(1 for v in self.bass_kick + self.comp_snare if abs(v) < 1.0)
        total = len(self.bass_kick) + len(self.comp_snare)
        return {
            "pieces": self.n_pieces,
            "bass_minus_kick_ms": pcts(self.bass_kick),
            "comp_minus_snare_ms": pcts(self.comp_snare),
            "window_beats": self.WINDOW_BEATS,
            "exact_share_lt_1ms": share(exact, total),
            "informative": bool(total and exact / total < 0.5),
            "note": "positif = la basse (ou le comping) tombe après la grosse caisse (la caisse claire) ; sans valeur si presque toutes les paires sont à moins de 1 ms (séquencé)",
        }
