"""Lakh MIDI Dataset (LMD-matched, CC BY 4.0) : basse, comping, batterie de morceaux étiquetés par genre.

**Étiquetage.** LMD n'a aucune étiquette de style. Les morceaux de LMD-matched portent l'identifiant
MSD `TR…` dans leur chemin ; on joint (a) le genre tagtraum CD2C (texte, « Research only,
strictly non-commercial » : statistiques seulement), (b) le sous-style AllMusic MASD (TU Wien) et
(c) les tags sociaux Last.fm (`lastfm_tags.db`). Un MIDI par `TR…` : celui dont le score d'appariement
(`match_scores.json`) est le plus haut, à condition d'atteindre `MIN_MATCH_SCORE`.

**Rôles.** Batterie : canal 10. Basse : programmes GM 32-39 (ou nom de piste « bass ») ; la piste
la plus fournie et la plus grave. Comping : pistes de guitare (24-31), de piano et claviers (0-7,
16-20) **polyphoniques** (au moins `MIN_POLYPHONY` des attaques à ≥ 2 notes) ; la plus polyphonique.
**Style E1** : règles de `assign_styles`, documentées dans le README des mesures. Fichiers à
changement de mètre, de tempo > 25 % ou hors 2/4-12/8 écartés.
"""

from __future__ import annotations

import json
import re
import sqlite3
import tarfile
import zipfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..core import (
    Note,
    Piece,
    attacks,
    detect_feel,
    meter_of,
    monophonic_bass,
    read_midi,
)

MIN_MATCH_SCORE = 0.70
MIN_POLYPHONY = 0.25
MIN_BARS = 16
BASS_PROGRAMS = range(32, 40)
GUITAR_PROGRAMS = range(24, 32)
KEYS_PROGRAMS = (*range(0, 8), *range(16, 21))
MIN_NOTES = {"bass": 48, "comp": 48, "drums": 64}


@dataclass
class Labels:
    tagtraum: dict[str, set[str]]
    masd: dict[str, set[str]]
    lastfm: dict[str, dict[str, int]]
    best: dict[str, tuple[str, float]]


def load_tagtraum(path: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".cls"))
        for line in z.read(name).decode().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            out[parts[0]] = set(parts[1:])
    return out


def load_masd(path: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for line in path.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        out.setdefault(parts[0], set()).update(parts[1:])
    return out


def load_best(path: Path) -> dict[str, tuple[str, float]]:
    scores = json.loads(path.read_text())
    best = {}
    for tid, cands in scores.items():
        md5, score = max(cands.items(), key=lambda kv: kv[1])
        if score >= MIN_MATCH_SCORE:
            best[tid] = (md5, score)
    return best


def load_lastfm(path: Path, wanted: set[str]) -> dict[str, dict[str, int]]:
    """Tags Last.fm (nom → score 0-100) des morceaux demandés, depuis `lastfm_tags.db`."""
    out: dict[str, dict[str, int]] = {}
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tids = {row[1]: row[0] for row in con.execute("select rowid, tid from tids")}
        tags = {row[0]: row[1] for row in con.execute("select rowid, tag from tags")}
        rev = {v: k for k, v in tids.items() if k in wanted}
        for tid_id, tag_id, val in con.execute("select tid, tag, val from tid_tag"):
            tid = rev.get(tid_id)
            if tid is not None:
                out.setdefault(tid, {})[tags[tag_id].lower()] = int(val)
    finally:
        con.close()
    return out


# --- Style E1 d'après les étiquettes et le fichier --------------------------------------------

TAG_MIN = 40  # score Last.fm minimal d'un tag


def _has(tags: dict[str, int], *needles: str) -> bool:
    return any(
        v >= TAG_MIN and any(re.search(rf"(^|[^a-z]){n}([^a-z]|$)", t) for n in needles)
        for t, v in tags.items()
    )


def assign_style(
    genres: set[str],
    masd: set[str],
    tags: dict[str, int],
    meter: float,
    compound: bool,
    bpm: float | None,
    feel: str,
) -> str | None:
    """Style E1 d'un morceau étiqueté, ou `None` s'il n'en vaut aucun. Règles (par priorité) :

    - `bossa` : tag Last.fm « bossa » ; `samba` : « samba » (sans « bossa ») ; `baiao` : « baiao », « baião » ou « forro » ;
      `afrocuban` : « salsa », « afro-cuban », « mambo », « rumba », « son cubano », « cuban ».
    - `reggae` : genre Reggae (tagtraum ou MASD) ou tag « reggae » ; `funk` : tag « funk » (hors Rock, Metal, Rap) ;
      `soul` : genre RnB (tagtraum) ou MASD `RnB_Soul` ou tag « soul ».
    - Jazz (tagtraum Jazz ou MASD Jazz_*/Big_Band) : `jazz_waltz` si 3/4 ; sinon 4/4 : `ballad` si tempo < 80 BPM,
      `swing` si feel ternaire et tempo ≥ 80 ; autres : aucun.
    - `blues_shuffle` : genre Blues (tagtraum ou MASD Blues_*) à feel ternaire, 4/4 ou 12/8 ; Blues droit : aucun.
    - `rock` : Rock (tagtraum) 4/4 ; `pop` : Pop (tagtraum) 4/4, sans Reggae/RnB/Latin.
    """
    names = {g.lower() for g in genres} | {g.lower() for g in masd}
    four = meter == 4.0 and not compound
    if _has(tags, "bossa", "bossanova", "bossa nova"):
        return "bossa"
    if _has(tags, "samba"):
        return "samba"
    if _has(tags, "baiao", "baião", "forro", "forró"):
        return "baiao"
    if _has(
        tags,
        "salsa",
        "afro-cuban",
        "afrocuban",
        "mambo",
        "rumba",
        "son cubano",
        "cuban",
    ):
        return "afrocuban"
    if "reggae" in names or _has(tags, "reggae"):
        return "reggae" if four else None
    if (
        _has(tags, "funk")
        and not (names & {"rock", "metal", "rap", "hip_hop_rap"})
        and four
    ):
        return "funk"
    if "rnb" in names or "rnb_soul" in names or _has(tags, "soul"):
        return "soul" if four else None
    jazz = "jazz" in names or any(
        n.startswith("jazz_") or n == "big_band" for n in names
    )
    if jazz:
        if meter == 3.0 and not compound:
            return "jazz_waltz"
        if four and bpm is not None:
            if bpm < 80:
                return "ballad"
            if feel == "ternary":
                return "swing"
        return None
    blues = "blues" in names or any(n.startswith("blues_") for n in names)
    if blues and feel == "ternary" and (four or (compound and meter == 6.0)):
        return "blues_shuffle"
    if "rock" in names and four:
        return "rock"
    if "pop" in names and four and not (names & {"reggae", "rnb", "latin"}):
        return "pop"
    return None


# --- Extraction des rôles ---------------------------------------------------------------------


def _polyphony(notes: list[Note]) -> tuple[float, int]:
    groups = attacks(notes)
    if not groups:
        return 0.0, 0
    return sum(1 for g in groups if len({n.pitch for n in g}) >= 2) / len(groups), len(
        groups
    )


def extract(data: bytes, tid: str, md5: str, styles_for) -> Piece | None:
    """Un `Piece` depuis les octets d'un MIDI, ou `None` (hors mètre, sans rôle utile, style sans étiquette)."""
    try:
        mid = read_midi(data)
    except Exception:  # noqa: BLE001 — fichier corrompu : écarté
        return None
    meter = meter_of(mid)
    if meter is None or mid.signature_changes or mid.bpm is None:
        return None
    if mid.tempo_changes() > 3:
        return None
    drums = [n for t in mid.tracks if t.is_drums for n in t.notes]
    bass_tracks = [
        t
        for t in mid.tracks
        if not t.is_drums
        and (
            t.program in BASS_PROGRAMS
            or re.search(r"bass", t.name, re.I)
            and t.program is not None
            and t.program < 40
            and not re.search(r"drum", t.name, re.I)
        )
    ]
    bass, bass_track = [], None
    if bass_tracks:
        bass_track = max(bass_tracks, key=lambda t: len(t.notes))
        bass = monophonic_bass(bass_track.notes)
    comps = []
    for t in mid.tracks:
        if t.is_drums or t.program is None or t is bass_track:
            continue
        kind = (
            "guitar"
            if t.program in GUITAR_PROGRAMS
            else ("keys" if t.program in KEYS_PROGRAMS else None)
        )
        if kind is None:
            continue
        poly, n_att = _polyphony(t.notes)
        if poly >= MIN_POLYPHONY and n_att >= MIN_NOTES["comp"] // 2:
            comps.append((poly * n_att, kind, t.notes))
    comp, kind = ([], "comp")
    if comps:
        _, kind, comp = max(comps, key=lambda c: c[0])
    if not (
        len(bass) >= MIN_NOTES["bass"]
        or len(comp) >= MIN_NOTES["comp"]
        or len(drums) >= MIN_NOTES["drums"]
    ):
        return None
    onsets = (
        [n.on for n in drums if n.pitch in (42, 44, 46, 51, 53, 59)]
        or [n.on for n in bass]
        or [n.on for n in comp]
    )
    feel, _ = detect_feel(onsets)
    style = styles_for(meter[0], meter[1], mid.bpm, feel)
    if style is None:
        return None
    n_bars = int(
        max((n.on + n.dur for n in (bass or comp or drums)), default=0) // meter[0]
    )
    if n_bars < MIN_BARS:
        return None
    return Piece(
        source="lmd",
        pid=f"{tid}/{md5}",
        styles=[style],
        bpm=mid.bpm,
        beats_per_bar=meter[0],
        compound=meter[1],
        bass=bass if len(bass) >= MIN_NOTES["bass"] else [],
        comp=comp if len(comp) >= MIN_NOTES["comp"] else [],
        comp_kind=kind,
        drums=drums if len(drums) >= MIN_NOTES["drums"] else [],
        feel=feel,
        performer=None,
        quantized=None,
        n_bars=n_bars,
    )


def _work(args):
    name, data, tid, md5, genres, masd, tags = args
    return extract(
        data,
        tid,
        md5,
        lambda meter, compound, bpm, feel: assign_style(
            genres, masd, tags, meter, compound, bpm, feel
        ),
    )


def pieces(
    archive: Path, labels: Labels, workers: int = 3, limit: int | None = None
) -> Iterator[Piece]:
    """Parcourt l'archive une fois ; les MIDI candidats (genre ou tag utile) sont analysés en parallèle."""
    wanted = {tid: md5 for tid, (md5, _) in labels.best.items()}

    def candidates() -> Iterator[tuple]:
        with tarfile.open(archive, "r|gz") as tar:
            for member in tar:
                if not member.isfile() or not member.name.endswith(".mid"):
                    continue
                parts = member.name.split("/")
                tid, md5 = parts[-2], parts[-1][:-4]
                if wanted.get(tid) != md5:
                    continue
                genres = labels.tagtraum.get(tid, set())
                masd = labels.masd.get(tid, set())
                tags = labels.lastfm.get(tid, {})
                names = {v.lower() for v in genres} | {v.lower() for v in masd}
                relevant = names & {
                    "jazz",
                    "blues",
                    "rock",
                    "pop",
                    "reggae",
                    "rnb",
                    "rnb_soul",
                    "big_band",
                }
                relevant |= {v for v in names if v.startswith(("jazz_", "blues_"))}
                style_tags = (
                    "bossa",
                    "samba",
                    "baiao",
                    "baião",
                    "forro",
                    "forró",
                    "salsa",
                    "afro-cuban",
                    "afrocuban",
                    "mambo",
                    "rumba",
                    "cuban",
                    "reggae",
                    "funk",
                    "soul",
                )
                if not relevant and not any(
                    value >= TAG_MIN and any(k in tag for k in style_tags)
                    for tag, value in tags.items()
                ):
                    continue  # éviter l'analyse de MIDI Electronic/Rap/Metal/World sans style E1
                data = tar.extractfile(member).read()  # type: ignore[union-attr]
                yield (member.name, data, tid, md5, genres, masd, tags)

    count = 0
    with ProcessPoolExecutor(workers) as pool:
        for piece in pool.map(_work, candidates(), chunksize=8, buffersize=16):
            if piece is not None:
                yield piece
                count += 1
                if limit and count >= limit:
                    return
