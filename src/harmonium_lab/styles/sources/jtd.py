"""Jazz Trio Database v0.2 (MIT) : piano transcrit (MIDI), temps annotés — comping du swing.

`piano_midi.mid` est une transcription automatique du piano séparé de l'enregistrement : elle mêle
accompagnement et solo (limite portée au JSON). Les temps (`beats.csv`) fixent les coordonnées
(`metre_auto` 1 = premier temps). Aucune donnée de batterie ou de basse n'est lue ici (voir
`backing/swing_tempo.py` : swing et micro-timing relatifs par classe de tempo).
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Iterator

from ..core import Note, Piece, attacks, read_midi, swing_ratio_of
from .guitarset import to_beats

TEMPO_CLASSES = (
    (0, 120, "lt120"),
    (120, 180, "120_180"),
    (180, 240, "180_240"),
    (240, 1e9, "ge240"),
)


def tempo_class(bpm: float) -> str:
    for lo, hi, name in TEMPO_CLASSES:
        if lo <= bpm < hi:
            return name
    return "ge240"


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        dirs = sorted({n.split("/")[1] for n in names if n.count("/") >= 2})
        for d in dirs:
            base = f"jazz-trio-database-v02/{d}"
            if (
                f"{base}/piano_midi.mid" not in names
                or f"{base}/beats.csv" not in names
            ):
                continue
            meta = json.loads(
                z.read(f"{base}/metadata.json").decode().replace("NaN", "null")
            )
            if meta.get("time_signature") != 4:
                continue
            rows = list(
                csv.DictReader(io.StringIO(z.read(f"{base}/beats.csv").decode()))
            )
            times, pos = [], []
            for row in rows:
                try:
                    times.append(float(row["beats"]))
                    pos.append(float(row["metre_auto"]))
                except (KeyError, ValueError):
                    continue
            if len(times) < 16:
                continue
            first = next((i for i, p in enumerate(pos) if p == 1.0), 0)
            mid = read_midi(z.read(f"{base}/piano_midi.mid"))
            piano = [t for t in mid.tracks if not t.is_drums]
            notes = []
            for t in piano:
                for n in t.notes:
                    s0 = mid.beats_to_seconds(n.on)
                    s1 = mid.beats_to_seconds(n.on + n.dur)
                    on = to_beats(s0, times) - first
                    dur = to_beats(s1, times) - to_beats(s0, times)
                    notes.append(Note(on, dur, n.pitch, n.vel))
            tempo = float(meta.get("tempo") or 0) or None
            # Transcription automatique bruitée : le feel vient de la médiane des attaques de contretemps
            # dans [0,45 ; 0,85] (au moins 0,60 : ternaire), pas du décompte de doubles croches.
            ratio, _ = swing_ratio_of([g[0].on for g in attacks(notes)])
            feel = "ternary" if ratio is not None and ratio >= 0.60 else "straight"
            yield Piece(
                source="jtd",
                pid=d,
                styles=["swing"],
                bpm=tempo,
                beats_per_bar=4.0,
                comp=notes,
                comp_kind="piano",
                performer=meta.get("pianist") or None,
                quantized=False,
                feel=feel,
                groups=[tempo_class(tempo)] if tempo else [],
                notes={"mixed_comp_and_solo": "oui"},
            )
