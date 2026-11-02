"""Lecteur de la Weimar Jazz Database (WJazzD v2.1) : vérification, téléchargement, manifeste.

Source : `https://jazzomat.hfm-weimar.de/download/downloads/wjazzd.db` (base SQLite, 42 512 384
octets, SHA256 `af6a0d9d…bf12`). Licence : ODbL 1.0 pour la base, DbCL 1.0 pour les contenus.
Les œuvres et les improvisations restent la propriété de leurs ayants droit : seuls des faits
agrégés et un manifeste sans note sont versionnés (principe VII).

    python -m harmonium_lab.backing.wjazzd --fetch      # télécharge et vérifie le SHA256
    python -m harmonium_lab.backing.wjazzd --manifest   # corpus/wjazzd/{manifest.jsonl,VERSION}

Tout accès à la base passe par `open_db`, qui vérifie le SHA256 avant la première lecture.

## Ce que contient la base (étudié sur le fichier réel, 456 solos, 132 329 temps)

- `solo_info` : un solo par `melid`. `rhythmfeel` : SWING 361, TWOBEAT 32, LATIN 27, FUNK 20,
  BALLAD 10, plus quelques étiquettes mixtes. `tempoclass` est vide pour 219 solos : le
  tempo se lit sur `avgtempo` (36,8–361,3 BPM ; swing : médiane 177,5). `key` est vide
  pour 23 solos du sous-ensemble swing ; sinon `<tonique>-<mode>` (`Bb-maj`, `D-chrom`,
  `C-min`, `Bb-blues`, `D-dor`) : seule la tonique sert (hauteur de référence des mesures
  « transposées en tonalité »).
- `beats` : un temps (une noire) par ligne, dans l'ordre de `beatid` ; `bar` (numéro continu
  sur tout le solo, sans trou), `beat` (1..4), `chorus_id`. `chord`, `form` et `signature`
  ne sont écrits qu'à leur changement : le lecteur les propage. `bar <= 0` ⇔ `chorus_id = 0` :
  levée ou introduction (la mesure 0 est une levée incomplète), ignorées. `form` : `I1` (intro),
  `A1`, `A2`, `B1`, `C1`… ; `chord` : 419 symboles distincts (voir `chords`), `NC` = silence.
- `bass_pitch` : hauteur MIDI de la basse à ce temps, NULL sur 9 789 temps de la base entière
  (18 solos ont des trous) ; swing : 103 901 temps sur 112 571 avec basse, plage 28–53
  (E♭1–F3), médiane 42, centile 1 = 31, centile 99 = 52. La basse est une note par temps :
  la base n'a ni durée ni attaque de basse.
- Signature : la signature du solo (`solo_info.signature`) manque pour 8 solos swing ; celle
  des temps change en cours de solo dans quelques-uns (5/4 isolées dans 2 solos, 3/4 dans 2
  autres). Les solos en 3/4, 6/4 et 1/4 (les 1/4 sont des solos libres : un seul temps
  par « mesure ») donnent zéro mesure en 4/4. Règle du lecteur : la signature effective
  d'un temps est la dernière signature écrite (celle du solo avant la première) et seules
  les mesures en `4/4` à quatre temps sont gardées.
- Octaves : aucune trace d'erreur d'octave systématique. Contrôle sur les 101 643 paires de temps
  consécutifs (mesures ≥ 1) des solos swing : l'histogramme des intervalles |Δ| est lisse
  (… 10 : 1 803, 11 : 1 837, 12 : 1 857, 13 : 866 …), sans pic à 12 ; 1,8 % des intervalles valent
  une octave exacte et 2,2 % la dépassent, surtout dans quelques solos (melids 228, 227, 225, 300,
  105 : 572 des 4 052 paires ≥ 12). Aucune correction n'est appliquée ; les mesures d'intervalles
  sont données avec leurs comptes pour en juger. Environ 20 % des intervalles sont des
  répétitions (même note deux temps de suite).
- Cohérence avec la grille : faible (voir `bass_measures`, « Fiabilité de la basse »). La basse
  de l'accord n'est jouée qu'à 41 % des changements d'accord ; la part par solo va de 17 % (centile
  10) à 70 % (centile 90). Ni octave ni décalage d'un temps ne l'explique (la fondamentale
  est à 35 % au 1ᵉʳ temps, 13 à 15 % ailleurs, que l'on décale la lecture de −1, 0 ou +1 temps).
- Hauteurs aberrantes : aucune (aucun `bass_pitch` hors 28–53 dans toute la base).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterator, NamedTuple

from ..trad.download import Fetcher
from ._util import sha256_file
from .chords import note_pc

URL = "https://jazzomat.hfm-weimar.de/download/downloads/wjazzd.db"
SHA256 = "af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12"
SIZE = 42_512_384
VERSION_LABEL = "WJazzD 2.1 (base 2.2, publiée le 2018-02-08)"
LICENCE = "ODbL-1.0 (base) + DbCL-1.0 (contenus)"
ATTRIBUTION = ("Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), "
               "which is made available here under the Open Database License (ODbL); "
               "individual contents under the Database Contents License (DbCL 1.0).")

REPO = Path(__file__).resolve().parents[3]
CORPUS_DIR = REPO / "corpus" / "wjazzd"
RAW_DB = CORPUS_DIR / "raw" / "wjazzd.db"
MANIFEST = CORPUS_DIR / "manifest.jsonl"
VERSION_FILE = CORPUS_DIR / "VERSION"

SWING = "SWING"
BEATS_PER_BAR = 4
SIGNATURE = "4/4"
# Sous-ensembles non swing de la phase 019 (L2) : `rhythmfeel` EXACT ; les valeurs composées
# (`LATIN/FUNK`, `A:LATIN/B:SWING`…) n'en font partie d'aucun.
L2_SUBSETS = ("BALLAD", "TWOBEAT", "LATIN", "FUNK")


class IntegrityError(RuntimeError):
    """Le fichier lu n'a pas le SHA256 attendu : il n'est pas lu."""


def verify(path: Path, expected: str = SHA256) -> str:
    """Vérifie le SHA256 de `path` ; `IntegrityError` explicite sinon. Renvoie le SHA256."""
    if not path.is_file():
        raise IntegrityError(f"{path} absent : `python -m harmonium_lab.backing.wjazzd --fetch`")
    actual = sha256_file(path)
    if actual != expected:
        raise IntegrityError(
            f"SHA256 non conforme pour {path} : {actual} (attendu {expected}). "
            "Fichier ni lu ni utilisé ; supprimez-le puis relancez --fetch.")
    return actual


def fetch(dest: Path = RAW_DB, url: str = URL, expected: str = SHA256, offline: bool = False) -> Path:
    """Télécharge la base si absente (cache gitignoré) puis vérifie son SHA256."""
    existed = dest.is_file()
    Fetcher(offline=offline).get(url, dest)
    try:
        verify(dest, expected)
    except IntegrityError:
        if not existed:
            dest.unlink(missing_ok=True)  # téléchargement corrompu : on ne garde rien
        raise
    return dest


def open_db(path: Path = RAW_DB, expected: str = SHA256) -> sqlite3.Connection:
    """Ouvre la base en lecture seule après vérification du SHA256."""
    verify(path, expected)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


# ── Solos ─────────────────────────────────────────────────────────────────

class SoloInfo(NamedTuple):
    """Une ligne de `solo_info` jointe à `composition_info` (faits, aucune note)."""
    melid: int
    trackid: int | None
    compid: int | None
    performer: str
    title: str
    instrument: str
    style: str
    avgtempo: float | None
    tempoclass: str
    rhythmfeel: str
    key: str
    signature: str
    chorus_count: int | None
    template: str
    comp_form: str

    @property
    def tonic(self) -> int | None:
        """Classe de hauteur de la tonique (`Bb-maj` → 10) ; `None` si la tonalité est vide."""
        letter = self.key.split("-")[0]
        return note_pc(letter) if letter else None

    @property
    def is_blues(self) -> bool:
        """Forme `Blues` selon `composition_info.template`."""
        return self.template == "Blues"


_SOLO_SQL = """
select s.melid, s.trackid, s.compid, s.performer, s.title, s.instrument, s.style, s.avgtempo,
       s.tempoclass, s.rhythmfeel, s.key, s.signature, s.chorus_count, c.template, c.form
from solo_info s left join composition_info c on c.compid = s.compid
{where} order by s.melid
"""


def list_solos(con: sqlite3.Connection, rhythmfeel: str | None = SWING) -> list[SoloInfo]:
    """Solos (tous si `rhythmfeel` est `None`), triés par `melid`."""
    where, args = ("where s.rhythmfeel = ?", (rhythmfeel,)) if rhythmfeel is not None else ("", ())
    solos = []
    for row in con.execute(_SOLO_SQL.format(where=where), args):
        (melid, trackid, compid, performer, title, instrument, style, avgtempo, tempoclass,
         rhythmfeel_, key, signature, chorus_count, template, comp_form) = tuple(row)
        solos.append(SoloInfo(melid, trackid, compid, performer or "", title or "", instrument or "",
                              style or "", avgtempo, tempoclass or "", rhythmfeel_ or "", key or "",
                              signature or "", chorus_count, template or "", comp_form or ""))
    return solos


class BeatRow(NamedTuple):
    """Un temps (une noire) d'une mesure en 4/4 d'un chorus : `chord`/`form` propagés."""
    bar: int
    beat: int
    chord: str | None
    form: str
    bass_pitch: int | None
    chorus_id: int


def read_solo(con: sqlite3.Connection, melid: int, solo_signature: str = "") -> list[BeatRow]:
    """Temps d'un solo : `chord` et `form` propagés, levées et intro (`bar <= 0`) ignorées,
    mesures hors 4/4 ou à moins de quatre temps écartées. L'ordre est celui de `beatid`.
    Un temps sans `bass_pitch` garde `bass_pitch = None`."""
    out: list[BeatRow] = []
    chord: str | None = None
    form = ""
    signature = solo_signature
    for bar, beat, c, f, sig, bass, chorus in con.execute(
            "select bar, beat, chord, form, signature, bass_pitch, chorus_id "
            "from beats where melid = ? order by beatid", (melid,)):
        if c:
            chord = c
        if f:
            form = f
        if sig:
            signature = sig
        if bar <= 0 or chorus <= 0 or signature != SIGNATURE or not 1 <= beat <= BEATS_PER_BAR:
            continue
        out.append(BeatRow(bar, beat, chord, form, bass, chorus))
    return out


def bars_of(beats: list[BeatRow]) -> Iterator[list[BeatRow]]:
    """Mesures consécutives d'un solo (un groupe par numéro de mesure, dans l'ordre)."""
    current: list[BeatRow] = []
    for row in beats:
        if current and row.bar != current[0].bar:
            yield current
            current = []
        current.append(row)
    if current:
        yield current


# ── Manifeste ─────────────────────────────────────────────────────────────

def manifest_rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """Une ligne par solo (tous les solos portent leur `rhythmfeel`) : identifiants et faits."""
    counts = {r[0]: (r[1], r[2]) for r in con.execute(
        "select melid, count(*), count(bass_pitch) from beats group by melid")}
    rows = []
    for s in list_solos(con, None):
        n_beats, n_bass = counts.get(s.melid, (0, 0))
        rows.append({
            "avgtempo": s.avgtempo, "chorus_count": s.chorus_count, "compid": s.compid,
            "composition_form": s.comp_form, "composition_template": s.template,
            "instrument": s.instrument, "key": s.key, "licence": LICENCE, "melid": s.melid,
            "n_beats": n_beats, "n_beats_bass": n_bass, "performer": s.performer,
            "rhythmfeel": s.rhythmfeel, "signature": s.signature, "style": s.style,
            "l2_subset": s.rhythmfeel if s.rhythmfeel in L2_SUBSETS else None,
            "swing_subset": s.rhythmfeel == SWING, "tempoclass": s.tempoclass,
            "title": s.title, "trackid": s.trackid,
        })
    return rows


def _manifest_text(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)


def write_manifest(db: Path = RAW_DB, manifest: Path = MANIFEST, version: Path = VERSION_FILE,
                   expected: str = SHA256, today: str | None = None) -> list[dict[str, Any]]:
    """Écrit `manifest.jsonl` (une ligne par solo, sans note) et `VERSION`.

    La date de `VERSION` est celle du premier relevé : elle est conservée tant que le
    SHA256 et la version ne changent pas (même entrée → mêmes fichiers)."""
    con = open_db(db, expected)
    try:
        rows = manifest_rows(con)
    finally:
        con.close()
    text = _manifest_text(rows)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(text, encoding="utf-8")
    manifest_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    retrieved = today or date.today().isoformat()
    if version.is_file():
        previous = dict(line.split(": ", 1) for line in version.read_text(encoding="utf-8").splitlines()
                        if ": " in line)
        if previous.get("sha256") == expected:
            retrieved = previous.get("retrieved", retrieved)
    n_swing = sum(1 for r in rows if r["swing_subset"])
    n_l2 = ", ".join(f"{name} {sum(1 for r in rows if r['l2_subset'] == name)}" for name in L2_SUBSETS)
    version.write_text(
        f"version: {VERSION_LABEL}\n"
        f"sha256: {expected}\n"
        f"retrieved: {retrieved}\n"
        f"url: {URL}\n"
        f"licence: {LICENCE}\n"
        f"attribution: {ATTRIBUTION}\n"
        f"solos: {len(rows)} (swing : {n_swing})\n"
        f"l2_subsets: {n_l2}\n"
        f"manifest_sha256: {manifest_sha}\n", encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fetch", action="store_true", help="télécharge wjazzd.db et vérifie son SHA256")
    ap.add_argument("--manifest", action="store_true", help="écrit corpus/wjazzd/manifest.jsonl et VERSION")
    ap.add_argument("--db", type=Path, default=RAW_DB)
    args = ap.parse_args(argv)
    if not (args.fetch or args.manifest):
        ap.error("--fetch et/ou --manifest requis")
    try:
        if args.fetch:
            fetch(args.db)
            print(f"{args.db} : SHA256 conforme ({SHA256[:12]}…)")
        if args.manifest:
            rows = write_manifest(args.db)
            swing = sum(1 for r in rows if r["swing_subset"])
            print(f"{MANIFEST.relative_to(REPO)} : {len(rows)} solos (swing : {swing}) ; VERSION écrit")
    except (IntegrityError, RuntimeError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
