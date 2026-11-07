"""Représentation commune : notes en temps de noire, mesures, feel, lecture MIDI.

Toutes les sources (MIDI, JAMS, CSV) sont ramenées à un `Piece` : notes de basse, de comping et de
batterie placées en **temps de noire depuis le début de la pièce** (indépendant du tempo), mètre,
tempo, accords. Les mesures (`measure.py`) ne voient que cette structure.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import mido

from ..backing.chords import Chord

ROLE_BASS, ROLE_COMP, ROLE_DRUMS = "bass", "comp", "drums"


@dataclass(frozen=True)
class Note:
    """Une note : début et durée en temps de noire, hauteur MIDI, vélocité (`None` si absente)."""

    on: float
    dur: float
    pitch: int
    vel: int | None = None


@dataclass
class ChordSpan:
    start: float
    end: float
    chord: Chord


@dataclass
class Piece:
    """Une pièce normalisée. `styles` : identifiants d'E1 auxquels elle contribue."""

    source: str
    pid: str
    styles: list[str]
    bpm: float | None
    beats_per_bar: float = 4.0  # temps de noire par mesure (3.0 en 3/4 et 6/8)
    compound: bool = False  # 6/8, 12/8 : pulsation pointée
    bass: list[Note] = field(default_factory=list)
    comp: list[Note] = field(default_factory=list)
    comp_kind: str = "comp"  # guitare, piano, clavier : nature de la voix de comping
    drums: list[Note] = field(default_factory=list)
    chords: list[ChordSpan] | None = None
    chords_inferred: bool = False
    performer: str | None = None  # musicien ou groupe, pour limiter le poids d'un seul
    quantized: bool | None = None  # source séquencée (écarts à la grille nuls)
    feel: str | None = (
        None  # "straight" | "ternary", calculé par `detect_feel` si absent
    )
    n_bars: int | None = None
    notes: dict[str, str] = field(default_factory=dict)
    groups: list[str] = field(
        default_factory=list
    )  # sous-groupes de mesure (ex. classe de tempo)

    def chord_at(self, t: float) -> Chord | None:
        if not self.chords:
            return None
        lo, hi = 0, len(self.chords) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            span = self.chords[mid]
            if t < span.start:
                hi = mid - 1
            elif t >= span.end:
                lo = mid + 1
            else:
                return span.chord
        return None


# --- Feel ------------------------------------------------------------------------------------

MIN_FEEL_EVIDENCE = 12


def detect_feel(onsets: Sequence[float]) -> tuple[str, dict[str, float]]:
    """`straight` ou `ternary` d'après la fraction de noire des attaques hors temps.

    Zones : double croche 1 [0,18 ; 0,29], triolet 1 [0,29 ; 0,40], croche droite [0,44 ; 0,56],
    triolet 2 ou croche swing [0,58 ; 0,72], zone ambiguë [0,72 ; 0,82] (double croche 3 ou swing
    appuyé). Droit = croche droite + 2 × double croche 1 (la double croche 3 suit la 1) ; ternaire =
    triolets ; la zone ambiguë compte pour le ternaire quand la double croche 1 y est rare (< 25 %).
    Ternaire si au moins `MIN_FEEL_EVIDENCE` attaques ternaires et plus que de droites.
    """
    z = {"q1": 0, "t1": 0, "e": 0, "t2": 0, "amb": 0}
    for t in onsets:
        f = t - math.floor(t)
        if 0.18 <= f < 0.29:
            z["q1"] += 1
        elif 0.29 <= f < 0.40:
            z["t1"] += 1
        elif 0.44 <= f <= 0.56:
            z["e"] += 1
        elif 0.58 <= f < 0.72:
            z["t2"] += 1
        elif 0.72 <= f <= 0.82:
            z["amb"] += 1
    ternary = z["t1"] + z["t2"] + (z["amb"] if z["q1"] < 0.25 * z["amb"] else 0)
    straight = z["e"] + 2 * z["q1"]
    evidence = {k: float(v) for k, v in z.items()}
    if ternary >= MIN_FEEL_EVIDENCE and ternary > straight:
        return "ternary", evidence
    return "straight", evidence


def swing_ratio_of(onsets: Sequence[float]) -> tuple[float | None, int]:
    """Position médiane de la croche retardée dans la noire (0,5 droit ; 0,667 triolet), et effectif."""
    values = []
    for t in onsets:
        frac = t - math.floor(t)
        if 0.45 <= frac <= 0.85:
            values.append(frac)
    if len(values) < 8:
        return None, len(values)
    values.sort()
    return values[len(values) // 2], len(values)


# --- Lecture MIDI ----------------------------------------------------------------------------


@dataclass
class MidiTrack:
    index: int
    name: str
    channel: int | None
    program: int | None
    notes: list[Note]
    is_drums: bool


@dataclass
class MidiFile:
    ppq: int
    numerator: int
    denominator: int
    signature_changes: int
    tempos: list[tuple[int, float]]  # (tick, bpm)
    tracks: list[MidiTrack]
    ticks_total: int

    @property
    def bpm(self) -> float | None:
        return self.tempos[0][1] if self.tempos else None

    def tempo_changes(self) -> int:
        return len({round(b, 1) for _, b in self.tempos})

    def beats_to_seconds(self, beats: float) -> float:
        """Instant (s) d'un temps de noire (carte de tempo du fichier)."""
        tempos = self.tempos or [(0, 120.0)]
        if tempos[0][0] > 0:
            tempos = [(0, tempos[0][1])] + tempos
        elapsed = 0.0
        for i, (tick, bpm) in enumerate(tempos):
            start_beat = tick / self.ppq
            nxt = tempos[i + 1][0] / self.ppq if i + 1 < len(tempos) else float("inf")
            if beats <= nxt:
                return elapsed + (beats - start_beat) * 60.0 / bpm
            elapsed += (nxt - start_beat) * 60.0 / bpm
        return elapsed

    def seconds_to_beats(self, seconds: float) -> float:
        """Temps de noire correspondant à un instant (carte de tempo du fichier)."""
        tempos = self.tempos or [(0, 120.0)]
        if tempos[0][0] > 0:
            tempos = [(0, tempos[0][1])] + tempos
        beats, elapsed = 0.0, 0.0
        for i, (tick, bpm) in enumerate(tempos):
            start_beat = tick / self.ppq
            nxt = tempos[i + 1][0] / self.ppq if i + 1 < len(tempos) else float("inf")
            span_s = (nxt - start_beat) * 60.0 / bpm
            if elapsed + span_s >= seconds:
                return start_beat + (seconds - elapsed) * bpm / 60.0
            elapsed += span_s
            beats = nxt
        return beats


def read_midi(data: bytes) -> MidiFile:
    """Lit un MIDI (type 0 ou 1) en notes à temps de noire ; la note sans note-off finit au dernier tick."""
    mid = mido.MidiFile(file=io.BytesIO(data), clip=True)
    ppq = mid.ticks_per_beat or 480
    numerator, denominator, sig_changes = 4, 4, 0
    seen_signature = False
    tempos: list[tuple[int, float]] = []
    tracks: list[MidiTrack] = []
    last_tick = 0
    for index, track in enumerate(mid.tracks):
        tick = 0
        name, program, channel = "", None, None
        on: dict[tuple[int, int], list[tuple[int, int]]] = {}
        raw: list[
            tuple[int, int, int, int | None, int]
        ] = []  # on_tick, off_tick, pitch, vel, channel
        drum_hits = 0
        melodic_hits = 0
        for msg in track:
            tick += msg.time
            if msg.type == "track_name" and not name:
                name = msg.name.strip()
            elif msg.type == "set_tempo":
                tempos.append((tick, 60_000_000 / msg.tempo))
            elif msg.type == "time_signature":
                if not seen_signature:
                    numerator, denominator, seen_signature = (
                        msg.numerator,
                        msg.denominator,
                        True,
                    )
                elif (msg.numerator, msg.denominator) != (numerator, denominator):
                    sig_changes += 1
            elif msg.type == "program_change" and program is None:
                program = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                on.setdefault((msg.channel, msg.note), []).append((tick, msg.velocity))
                channel = msg.channel if channel is None else channel
                if msg.channel == 9:
                    drum_hits += 1
                else:
                    melodic_hits += 1
            elif msg.type in ("note_off", "note_on"):
                stack = on.get((msg.channel, msg.note))
                if stack:
                    start, vel = stack.pop(0)
                    raw.append((start, tick, msg.note, vel, msg.channel))
        for (ch, pitch), stack in on.items():
            for start, vel in stack:
                raw.append((start, tick, pitch, vel, ch))
        last_tick = max(last_tick, tick)
        if not raw:
            continue
        is_drums = drum_hits > melodic_hits
        notes = [
            Note(s / ppq, max(e - s, 0) / ppq, p, v) for s, e, p, v, ch in sorted(raw)
        ]
        tracks.append(MidiTrack(index, name, channel, program, notes, is_drums))
    tempos.sort()
    return MidiFile(ppq, numerator, denominator, sig_changes, tempos, tracks, last_tick)


def meter_of(mid: MidiFile) -> tuple[float, bool] | None:
    """(temps de noire par mesure, composé) pour 2/4, 3/4, 4/4, 6/8, 12/8 ; `None` sinon."""
    n, d = mid.numerator, mid.denominator
    if d == 4 and n in (2, 3, 4):
        return float(n), False
    if d == 8 and n in (6, 12):
        return n / 2.0, True
    return None


def monophonic_bass(notes: Iterable[Note], window: float = 0.06) -> list[Note]:
    """Ne garde que la note la plus grave de chaque grappe d'attaques simultanées (basse polyphonique)."""
    out: list[Note] = []
    for note in sorted(notes, key=lambda n: (n.on, n.pitch)):
        if out and note.on - out[-1].on < window:
            continue
        out.append(note)
    return out


def attacks(notes: Sequence[Note], window: float = 0.06) -> list[list[Note]]:
    """Regroupe les notes de comping débutant à moins de `window` temps de la première de la grappe."""
    groups: list[list[Note]] = []
    for note in sorted(notes, key=lambda n: (n.on, n.pitch)):
        if groups and note.on - groups[-1][0].on < window:
            groups[-1].append(note)
        else:
            groups.append([note])
    return groups
