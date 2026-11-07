"""Groove MIDI Dataset v1.0.0 (CC BY 4.0) : batterie par style, mêmes fichiers que L2.

Seuls les `beat` sont lus (les `fill` sont mesurés par L2). Table style GMD → style E1 :
`GMD_TO_E1`. Le GMD n'a ni basse ni comping : ces pièces ne nourrissent que la batterie et la
comparaison avec les batteries des autres sources. E-GMD (CC BY 4.0) réenregistre exactement ces
performances sur 43 kits : son CSV ajoute 0 style (vérifié : 1 059 séquences uniques, toutes dans
`info.csv` du GMD), il n'est donc pas relu.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterator

from ...backing import drums as gmd
from ..core import Piece, meter_of, read_midi

GMD_TO_E1 = {
    "jazz/swing": "swing",
    "jazz/mediumfast": "swing",
    "jazz/fast": "swing",
    "jazz/linear": "swing",
    "latin/brazilian-bossa": "bossa",
    "latin/brazilian-samba": "samba",
    "latin/samba": "samba",
    "latin/brazilian-baiao": "baiao",
    "afrocuban": "afrocuban",
    "afrocuban/bembe": "afrocuban",
    "afrocuban/rhumba": "afrocuban",
    "afrocuban/calypso": "afrocuban",
    "funk": "funk",
    "funk/groove1": "funk",
    "funk/groove2": "funk",
    "funk/groove5": "funk",
    "funk/fast": "funk",
    "funk/rock": "funk",
    "soul": "soul",
    "soul/groove3": "soul",
    "soul/groove4": "soul",
    "soul/groove9": "soul",
    "soul/groove10": "soul",
    "soul/motown": "soul",
    "reggae": "reggae",
    "reggae/slow": "reggae",
    "rock": "rock",
    "rock/groove8": "rock",
    "rock/indie": "rock",
    "rock/halftime": "rock",
    "pop": "pop",
    "pop/groove7": "pop",
    "pop/soft": "pop",
    "blues/shuffle": "blues_shuffle",
    "rock/shuffle": "blues_shuffle",
    "funk/purdieshuffle": "blues_shuffle",
    "neworleans/shuffle": "blues_shuffle",
}
"""Style GMD → style E1. `jazz` seul (mélange de feels et de figures) n'est pas pris pour le swing ;
un `jazz` en 3/4 l'est pour la valse."""


def pieces(archive: Path = gmd.ARCHIVE) -> Iterator[Piece]:
    from ...backing.corpus_cache import open_verified

    open_verified(archive, gmd.SOURCE_SHA256)
    with zipfile.ZipFile(archive) as z:
        for row in gmd.parse_rows(gmd.read_info_rows(z)):
            if row.beat_type != "beat":
                continue
            style = GMD_TO_E1.get(row.style)
            if row.style.startswith("jazz") and row.time_signature == "3-4":
                style = "jazz_waltz"
            if style is None:
                continue
            mid = read_midi(z.read(f"groove/{row.path}"))
            meter = meter_of(mid)
            if meter is None:
                continue
            drums = [n for t in mid.tracks for n in t.notes]
            yield Piece(
                source="gmd",
                pid=row.ident,
                styles=[style],
                bpm=float(row.bpm),
                beats_per_bar=meter[0],
                compound=meter[1],
                drums=drums,
                performer=row.drummer,
                quantized=False,
                notes={"gmd_style": row.style},
            )
