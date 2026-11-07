"""Accords des sources : Harte (GuitarSet, POP909), inférence par gabarits pour les MIDI sans annotation."""

from __future__ import annotations

import re
from typing import Sequence

from ..backing.chords import Chord, from_engine, note_pc
from .core import ChordSpan, Note, Piece

_HARTE = re.compile(
    r"^(?P<root>[A-G][b#]*)(?::(?P<q>[^/(]*))?(?P<ext>\([^)]*\))?(?:/(?P<bass>[^ ]+))?$"
)

_QUALITY = {
    "": "",
    "maj": "",
    "min": "m",
    "m": "m",
    "7": "7",
    "maj7": "maj7",
    "min7": "m7",
    "dim": "dim",
    "dim7": "dim7",
    "hdim7": "m7b5",
    "hdim": "m7b5",
    "aug": "aug",
    "sus4": "sus4",
    "sus2": "sus2",
    "maj6": "6",
    "min6": "m6",
    "9": "9",
    "maj9": "maj9",
    "min9": "m9",
    "11": "11",
    "13": "13",
    "min11": "m11",
    "min13": "m13",
    "minmaj7": "mMaj7",
    "sus": "sus4",
    "5": "",
}


def parse_harte(symbol: str) -> Chord | None:
    """Symbole Harte → `Chord` ; `N`, `X` et les symboles hors grammaire donnent `None` (jamais devinés)."""
    symbol = symbol.strip()
    if symbol in ("N", "X", "", "N.C."):
        return None
    match = _HARTE.match(symbol)
    if match is None:
        return None
    root = note_pc(match["root"])
    quality = match["q"] if match["q"] is not None else ""
    suffix = _QUALITY.get(quality)
    if suffix is None:
        return None
    ext = match["ext"] or ""
    bass = root
    if match["bass"] and re.fullmatch(r"[A-G][b#]*", match["bass"]):
        bass = note_pc(match["bass"])
    try:
        # Parenthèses : seules les altérations de quinte et de neuvième usuelles sont gardées.
        alts = "".join(re.findall(r"[b#](?:5|9|11|13)", ext))
        return from_engine(root, bass, suffix + alts, is_minor=False)
    except Exception:  # noqa: BLE001 — symbole non analysé : compté par l'appelant
        return None


# Gabarits : (suffixe moteur, intervalles). Ordre = préférence à score égal (triades avant septièmes).
TEMPLATES: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("", (0, 4, 7)),
    ("m", (0, 3, 7)),
    ("7", (0, 4, 7, 10)),
    ("m7", (0, 3, 7, 10)),
    ("maj7", (0, 4, 7, 11)),
    ("dim", (0, 3, 6)),
    ("sus4", (0, 5, 7)),
)
_NON_TONE = 0.55
_MIN_WEIGHT = 0.25
_SEVENTH_BONUS = 0.0


def infer_chords(
    piece: Piece,
    harmonic: Sequence[Note],
    window: float | None = None,
    bass: Sequence[Note] = (),
) -> list[ChordSpan] | None:
    """Accords par fenêtres (demi-mesure en 4/4, mesure sinon) d'après les notes harmoniques.

    Poids d'une note : durée plafonnée à 2 temps ; la basse compte pour moitié (elle désigne la
    fondamentale mais ne doit pas imposer sa propre analyse). Gabarit : somme des poids des notes
    d'accord moins `_NON_TONE` fois celle des autres. Aucune note : fenêtre sans accord (le
    précédent continue). Documenté comme **inféré** (`chords_inferred`).
    """
    bpb = piece.beats_per_bar
    window = window or (bpb / 2 if bpb == 4.0 else bpb)
    end = max((n.on + n.dur for n in list(harmonic) + list(bass)), default=0.0)
    n_win = int(end // window) + 1
    weights = [[0.0] * 12 for _ in range(n_win)]
    for note in harmonic:
        w = min(note.dur, 2.0) or 0.25
        idx = min(int(note.on // window), n_win - 1)
        weights[idx][note.pitch % 12] += w
    for note in bass:
        w = 0.5 * (min(note.dur, 2.0) or 0.25)
        idx = min(int(note.on // window), n_win - 1)
        weights[idx][note.pitch % 12] += w
    spans: list[ChordSpan] = []
    for i, wv in enumerate(weights):
        total = sum(wv)
        if total <= _MIN_WEIGHT:
            continue
        best, best_score = None, -1e9
        for root in range(12):
            for suffix, ivs in TEMPLATES:
                tones = {(root + iv) % 12 for iv in ivs}
                score = sum(wv[p] for p in tones) - _NON_TONE * sum(
                    wv[p] for p in range(12) if p not in tones
                )
                score -= (
                    0.02 * total * len(ivs)
                )  # préférence faible pour les accords simples
                if score > best_score:
                    best, best_score = (root, suffix), score
        if best is None:
            continue
        chord = from_engine(best[0], best[0], best[1])
        start, stop = i * window, (i + 1) * window
        if (
            spans
            and spans[-1].chord.root == chord.root
            and spans[-1].chord.quality == chord.quality
            and abs(spans[-1].end - start) < 1e-6
        ):
            spans[-1].end = stop
        else:
            spans.append(ChordSpan(start, stop, chord))
    # Remplit les trous : un accord continue jusqu'au suivant.
    for a, b in zip(spans, spans[1:]):
        a.end = b.start
    return spans or None
