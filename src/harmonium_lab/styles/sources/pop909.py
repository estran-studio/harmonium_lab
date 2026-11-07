"""POP909 (MIT) : accompagnement piano de 909 chansons pop, accords et temps annotés.

On lit la piste `PIANO` (accompagnement) de `POP909/<n>/<n>.mid` ; les accords de `chord_midi.txt`
(secondes, convertis en temps de noire par la carte de tempo du MIDI). Les mélodies (`MELODY`,
`BRIDGE`) ne sont pas lues. Style : `pop` pour tout le corpus (aucune étiquette de style).
"""

from __future__ import annotations

import re
from collections import Counter
import zipfile
from pathlib import Path
from typing import Iterator

from ..core import ChordSpan, Note, Piece, read_midi
from ..harmony import parse_harte

ID = re.compile(r"^POP909/(\d{3})/\1\.mid$")


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        for name in sorted(names):
            m = ID.match(name)
            if not m:
                continue
            pid = m.group(1)
            mid = read_midi(z.read(name))
            # Le MIDI contient souvent une signature 1/4 ou 2/4 alors que `beat_midi.txt` annote
            # le premier temps de vraies mesures de 4 temps. On croit les temps annotés, pas le MIDI.
            beat_file = f"POP909/{pid}/beat_midi.txt"
            if beat_file not in names:
                continue
            beat_rows = []
            for line in z.read(beat_file).decode().splitlines():
                fields = line.split()
                if len(fields) == 3:
                    beat_rows.append((float(fields[0]), fields[2] == "1.0"))
            downbeats = [i for i, (_, down) in enumerate(beat_rows) if down]
            if len(downbeats) < 8:
                continue
            gaps = Counter(b - a for a, b in zip(downbeats, downbeats[1:]))
            bpb = gaps.most_common(1)[0][0]
            if bpb not in (3, 4):
                continue
            origin = mid.seconds_to_beats(beat_rows[downbeats[0]][0])
            piano = next((t for t in mid.tracks if t.name.upper() == "PIANO"), None)
            if piano is None or len(piano.notes) < 16:
                continue
            notes = [
                Note(n.on - origin, n.dur, n.pitch, n.vel)
                for n in piano.notes
                if n.on >= origin
            ]
            spans = []
            chord_file = f"POP909/{pid}/chord_midi.txt"
            if chord_file in names:
                for line in z.read(chord_file).decode().splitlines():
                    parts = line.split("\t")
                    if len(parts) != 3:
                        continue
                    chord = parse_harte(parts[2])
                    if chord is not None:
                        spans.append(
                            ChordSpan(
                                mid.seconds_to_beats(float(parts[0])) - origin,
                                mid.seconds_to_beats(float(parts[1])) - origin,
                                chord,
                            )
                        )
            yield Piece(
                source="pop909",
                pid=pid,
                styles=["pop"],
                bpm=mid.bpm,
                beats_per_bar=float(bpb),
                compound=False,
                comp=notes,
                comp_kind="piano",
                chords=spans or None,
                performer=None,
                quantized=False,
                notes={"tempo_changes": str(mid.tempo_changes())},
            )
