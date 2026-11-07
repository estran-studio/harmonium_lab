"""Weimar Jazz Database (ODbL 1.0 + DbCL 1.0) : basse au temps, accords de tous les solos.

La base donne une hauteur de basse **par temps de noire** (pas de croches, pas de durée) et l'accord
au temps. Les pièces sont les solos ; seule la basse est lue (jamais la mélodie du soliste).
Style E1 : `rhythmfeel` SWING → `swing`, BALLAD → `ballad`, LATIN → `latin_jazz`, FUNK → `funk_jazz`
(hard bop sur rythme latin ou funk : proxy de bossa/afro-cubain/funk, pas le style lui-même), TWOBEAT →
`twobeat` ; tout solo en 3/4 → `jazz_waltz` (le temps effectif d'une mesure est celui de la signature).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from ...backing import wjazzd as base
from ...backing.chords import ChordParseError, parse_wjazzd
from ..core import ChordSpan, Note, Piece

FEEL_STYLE = {
    "SWING": "swing",
    "BALLAD": "ballad",
    "LATIN": "latin_jazz",
    "FUNK": "funk_jazz",
    "TWOBEAT": "twobeat",
}
TERNARY = {"SWING", "BALLAD", "TWOBEAT"}


def pieces(db: Path = base.RAW_DB) -> Iterator[Piece]:
    con = base.open_db(db)
    try:
        cache: dict[str, object] = {}
        for info in base.list_solos(con, None):
            rows = list(
                con.execute(
                    "select bar, beat, chord, signature, bass_pitch, chorus_id from beats where melid = ? order by beatid",
                    (info.melid,),
                )
            )
            signature = info.signature or "4/4"
            chord_sym = None
            notes: list[Note] = []
            spans: list[ChordSpan] = []
            bars_seen: dict[int, int] = {}
            bar_index = -1
            last_bar = None
            sig_changed = False
            for bar, beat, chord, sig, bass, chorus in rows:
                if sig and sig != signature:
                    signature = sig
                    sig_changed = True
                if chord:
                    chord_sym = chord
                if bar <= 0 or chorus <= 0:
                    continue
                if bar != last_bar:
                    bar_index += 1
                    last_bar = bar
                    bars_seen[bar_index] = 0
                bars_seen[bar_index] += 1
            if sig_changed or not bars_seen:
                continue
            num = signature.split("/")
            if len(num) != 2 or num[1] != "4" or int(num[0]) not in (3, 4):
                continue
            bpb = int(num[0])
            bar_index, last_bar, chord_sym = -1, None, None
            for bar, beat, chord, sig, bass, chorus in rows:
                if chord:
                    chord_sym = chord
                if bar <= 0 or chorus <= 0 or not 1 <= beat <= bpb:
                    continue
                if bar != last_bar:
                    bar_index += 1
                    last_bar = bar
                t = bar_index * bpb + (beat - 1)
                if chord_sym and chord_sym != "NC":
                    if chord_sym not in cache:
                        try:
                            cache[chord_sym] = parse_wjazzd(chord_sym)
                        except ChordParseError:
                            cache[chord_sym] = None
                    c = cache[chord_sym]
                    if c is not None:
                        if (
                            spans
                            and spans[-1].chord is c
                            and abs(spans[-1].end - t) < 1e-6
                        ):
                            spans[-1].end = t + 1
                        else:
                            spans.append(ChordSpan(t, t + 1, c))  # type: ignore[arg-type]
                if bass is not None:
                    notes.append(Note(float(t), 1.0, int(bass), None))
            if len(notes) < 32:
                continue
            style = "jazz_waltz" if bpb == 3 else FEEL_STYLE.get(info.rhythmfeel)
            if style is None:
                continue
            yield Piece(
                source="wjazzd",
                pid=str(info.melid),
                styles=[style],
                bpm=info.avgtempo,
                beats_per_bar=float(bpb),
                bass=notes,
                chords=spans or None,
                performer=info.performer or None,
                quantized=True,
                feel="ternary" if info.rhythmfeel in TERNARY else "straight",
                notes={
                    "rhythmfeel": info.rhythmfeel,
                    "granularity": "une note par temps de noire",
                },
                groups=[f"feel_{info.rhythmfeel.lower()}"],
            )
    finally:
        con.close()
