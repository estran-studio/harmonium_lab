"""Corpus trad québécois : sources → airs normalisés → manifeste (specs/001-trad-dataset D1-D3).

Pipeline : téléchargement (cache `raw/`) → séparation des airs → typage →
normalisation + analyse → rejets comptés → dédoublonnage entre sources →
`tunes/<type>/<id>.abc`, `manifest.jsonl` (trié, déterministe) et `VERSION`.
Les fichiers téléchargés ne sont jamais versionnés ; seuls `manifest.jsonl`
et `VERSION` le sont.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from .abcnorm import (
    REJECT_NO_KEY,
    REJECT_NO_MELODY,
    REJECT_PARSE,
    TYPES,
    AbcError,
    Tune,
    analyse,
    decode_abc_text,
    fold,
    intervals,
    parse_tune,
    slugify,
    split_tunes,
    title_key,
    type_from_text,
)
from .download import Fetcher, list_abc_files

CHAMBERS = "chambers"
SESSION = "thesession"
NOTTINGHAM = "nottingham"
CAHUSAC = "cahusac"
AMREV = "amrev"
SOURCE_RANK = {CHAMBERS: 0, NOTTINGHAM: 1, CAHUSAC: 2, AMREV: 3, SESSION: 4}
LICENSES = {
    CHAMBERS: "non précisée (usage interne, attribution John Chambers)",
    SESSION: "ODbL",
    NOTTINGHAM: "Domaine public (NMD) / GPL-3.0 (édition jukedeck)",
    CAHUSAC: "Domaine public (Londres, 1809)",
    AMREV: "non précisée (usage interne, domaine public / attribution John Chambers)",
}

TRADITION_QUEBECOISE = "quebecoise"
TRADITION_ACADIENNE = "acadienne"
TRADITION_BRITANNIQUE_COLONIALE = "britannique_coloniale"
TRADITIONS = (TRADITION_QUEBECOISE, TRADITION_ACADIENNE, TRADITION_BRITANNIQUE_COLONIALE)

CHAMBERS_BASE = "http://trillian.mit.edu/~jc/music/abc/Quebec/"
CHAMBERS_TYPED_DIRS = {"reel": "reel", "jig": "jig", "waltz": "waltz", "march": "march"}
CHAMBERS_OTHER_DIRS = ("", "misc", "montrealsession")  # "" = racine
SESSION_RAW = "https://raw.githubusercontent.com/adactio/TheSession-data/main/json/{}.json"
SESSION_FILES = ("tunes", "recordings", "aliases")
SESSION_TYPES = {"reel": "reel", "jig": "jig", "waltz": "waltz", "march": "march", "hornpipe": "hornpipe"}

# Mètre par défaut quand `M:` manque (garantit l'en-tête M: de l'ABC normalisé).
DEFAULT_METER = {
    "reel": "4/4", "jig": "6/8", "waltz": "3/4", "march": "2/4", "quadrille": "6/8", "cotillon": "6/8",
    "hornpipe": "4/4",
}

# Motifs français, par mots entiers, sur texte replié (sans accents, minuscules).
# Formes admises : `reel de|du|des|d'|à`, `gigue`, `valse`, `quadrille`, `cotillon`
# (pas `cotillion`), `québec`/`québécois(e)`, `canadien(ne)(s)`. Pluriels, suédois
# (« valsen », « vals ») et anglais (« cotillion », « quadrilles ») exclus.
FRENCH_TITLE = re.compile(
    r"\b(reel (?:de|du|des|d'|a)|gigue|valse|quadrille|cotillon"
    r"|quebec(?:ois(?:e|s|es)?)?|canadien(?:ne(?:s)?|s)?)\b"
)
# Mots de contenu français fréquents dans les titres (texte replié : sans accents,
# minuscules). Complètent les mots-outils pour la preuve de français : « Valse Triste »…
_FRENCH_CONTENT = (
    "triste|petit|petite|grand|grande|vieux|vieille|beau|belle|bon|bonne|nouveau|nouvelle|"
    "premier|premiere|dernier|derniere|joyeux|joyeuse|mariage|noel|printemps|automne|hiver|"
    "ete|matin|soir|nuit|jour|fete|danse|chanson|souvenir|adieu|bonjour|fille|garcon|"
    "madame|monsieur|amour|coeur|village|forgeron|meunier|ronde|sucre|sucres|eboulements|"
    "faubourg|faubourgs|pendu|pendus|diable|sorcier|sorciere|chasse|galope|reveillon|"
    "pays|rois|reine|cloches|messe|minuit|berceuse|complainte|rigodon|croche|pied|pieds|"
    "turlute|violon|accordeon|gigueur|danseur|chanteur|quebecois|canadien"
)
# Le titre/alias qui correspond doit être en français : mot-outil, élision, accent
# ou mot de contenu français.
FRENCH_MARKER = re.compile(
    r"[àâäéèêëîïôöùûüçœæ]|\b(?:de|du|des|la|le|les|au|aux|en|sur|dans|pour|chez|avec|"
    r"sans|sous|mon|ma|mes|ton|ta|tes|son|sa|ses|un|une|est|et|qui|notre|votre|leur|leurs)\b"
    r"|\b[dlcs]'(?=[a-z])"
    r"|\b(?:" + _FRENCH_CONTENT + r")\b"
)


ARTISTS_FILE = Path(__file__).with_name("quebec_artists.json")
ACADIAN_ARTISTS_FILE = Path(__file__).with_name("acadian_artists.json")

def load_quebec_artists(path: Path = ARTISTS_FILE) -> dict[str, str]:
    """`QUEBEC_ARTISTS` : nom d'artiste replié (tel que `recordings[].artist`) → nom québécois.

    `recordings.json` donne l'artiste en clair, pas son identifiant numérique ;
    la jointure se fait donc sur le nom (`session_names`), comparé après `fold`.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for entry in data["artists"]:
        for name in entry["session_names"]:
            out.setdefault(fold(name), entry["name"])
    return out


def quebec_artist_names(path: Path = ARTISTS_FILE) -> list[str]:
    return [e["name"] for e in json.loads(path.read_text(encoding="utf-8"))["artists"]]

def load_acadian_artists(path: Path = ACADIAN_ARTISTS_FILE) -> dict[str, str]:
    """`ACADIAN_ARTISTS` : nom d'artiste replié → nom acadien."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for entry in data["artists"]:
        for name in entry["session_names"]:
            out.setdefault(fold(name), entry["name"])
    return out


def acadian_artist_names(path: Path = ACADIAN_ARTISTS_FILE) -> list[str]:
    return [e["name"] for e in json.loads(path.read_text(encoding="utf-8"))["artists"]]


ACADIAN_TITLE_PATTERN = re.compile(r"\b(acadien(?:ne)?(?:s)?|acadie|acadian)\b", re.I)


def acadian_match(text: str) -> str | None:
    m = ACADIAN_TITLE_PATTERN.search(fold(text))
    return m.group(0) if m else None


def french_match(text: str) -> str | None:
    """Motif français d'un titre/alias, ou None.

    Mots entiers, formes françaises uniquement (`reel de|du|des|d'|à`, `gigue`,
    `valse`, `quadrille`, `cotillon`, `québec(ois)`, `canadien(ne)` ; ni pluriels
    anglais, ni `cotillion`, ni suédois `vals(en)`). Le texte doit en plus être en
    français : accent français, mot-outil/élision/mot de contenu, `reel …` (la
    construction porte elle-même le français), deux motifs, ou forme
    québécoise/canadienne. Un « å/ø » scandinave disqualifie (« Sångshytt ») ;
    un « a » non accentué seul ne prouve rien (« A Christmas Gigue » exclu).
    """
    if re.search(r"[åøÅØ]", text):
        return None
    if re.search(r"\b[Rr]éel\b", text):
        return "réel"  # avant le repli : `fold` efface l'accent
    found = FRENCH_TITLE.findall(fold(text))
    if not found:
        return None
    first = found[0]
    if first.startswith("reel ") or len(found) >= 2 or "quebec" in first or "canadien" in first:
        return first
    if FRENCH_MARKER.search(fold(text)) or re.search(r"[àâäéèêëîïôöùûüçÿœæ]", text):
        return first
    return None


# ── Données ──────────────────────────────────────────────────────────


@dataclass
class RawTune:
    source: str
    origin: str  # chemin lisible pour les logs de rejet
    url: str
    block: str  # texte ABC d'un seul air
    type_hint: str | None  # dossier JC typé ou type The Session
    because: str
    fallback_title: str
    extra_aliases: list[str] = field(default_factory=list)
    because_kinds: tuple = field(default=(), kw_only=True)  # ("artist", "title", "alias")
    tradition: str = TRADITION_QUEBECOISE
    epoque: str | None = None

@dataclass
class Candidate:
    id: str
    title: str
    aliases: list[str]
    type: str
    meter: str
    key: str
    mode: str
    bars: int
    source: str
    url: str
    license: str
    sha256: str
    included_because: str
    because_kinds: tuple = field(default=(), kw_only=True)
    incipit: list[int]
    abc: str
    also_in: list[dict] = field(default_factory=list)
    tradition: str = TRADITION_QUEBECOISE
    epoque: str | None = None

    def manifest_row(self) -> dict:
        row = {
            "id": self.id, "title": self.title, "aliases": sorted(set(self.aliases)),
            "tradition": self.tradition,
            "type": self.type, "meter": self.meter, "key": self.key, "mode": self.mode,
            "bars": self.bars, "source": self.source, "url": self.url, "license": self.license,
            "sha256": self.sha256, "included_because": self.included_because,
            "incipit": self.incipit,
        }
        if self.epoque:
            row["epoque"] = self.epoque
        if self.also_in:
            row["also_in"] = sorted(self.also_in, key=lambda a: (a["source"], a["url"]))
        return row


@dataclass
class Stats:
    kept: Counter = field(default_factory=Counter)  # (type, source)
    rejected: Counter = field(default_factory=Counter)  # (type, source)
    merged: Counter = field(default_factory=Counter)  # (type, source du doublon écarté)
    ignored: Counter = field(default_factory=Counter)  # source
    reject_reasons: Counter = field(default_factory=Counter)  # (source, raison)
    reasons: Counter = field(default_factory=Counter)  # (type, kind) : artiste / titre FR / alias FR
    inferred_meter: int = 0
    rejects: list[dict] = field(default_factory=list)


# ── Sources ──────────────────────────────────────────────────────────


def _decode_bytes(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def chambers_tunes(raw_dir: Path, fetcher: Fetcher) -> Iterator[RawTune]:
    """Airs de John Chambers : sous-dossiers typés + racine, `misc/`, `montrealsession/`."""
    dirs = [*CHAMBERS_TYPED_DIRS, *CHAMBERS_OTHER_DIRS]
    for d in dirs:
        label = d or "_racine"
        url_dir = CHAMBERS_BASE + (d + "/" if d else "")
        index = fetcher.get(url_dir, raw_dir / "chambers" / "_index" / f"{label}.html")
        for name in list_abc_files(_decode_bytes(index.read_bytes())):
            url = url_dir + urllib.parse.quote(name, safe=",")
            path = fetcher.get(url, raw_dir / "chambers" / label / name)
            blocks = split_tunes(_decode_bytes(path.read_bytes()))
            where = f"Quebec/{d + '/' if d else ''}{name}"
            for i, block in enumerate(blocks, 1):
                yield RawTune(
                    source=CHAMBERS,
                    origin=f"{where}#X{i}",
                    url=url if len(blocks) == 1 else f"{url}#{i}",
                    block=block,
                    type_hint=CHAMBERS_TYPED_DIRS.get(d),
                    because=f"John Chambers, collection Québec ({d or 'racine'}/{name})",
                    fallback_title=Path(name).stem.replace("_", " "),
                )


_SESSION_MODE = re.compile(r"^([A-G][#b]?)(major|minor|dorian|mixolydian|lydian|phrygian|locrian|ionian|aeolian)$")


def _session_key(mode: str) -> str:
    m = _SESSION_MODE.match(mode.strip())
    if not m:
        raise AbcError(REJECT_PARSE, f"mode The Session inconnu {mode!r}")
    suffix = {"major": "", "minor": "m", "dorian": " dor", "mixolydian": " mix", "lydian": " lyd",
              "phrygian": " phr", "locrian": " loc", "ionian": "", "aeolian": " aeo"}[m.group(2)]
    return m.group(1) + suffix


def session_tunes(raw_dir: Path, fetcher: Fetcher, artists_file: Path = ARTISTS_FILE) -> Iterator[RawTune]:
    """Airs The Session qualifiés québécois (artiste enregistré, ou titre/alias français)."""
    base = raw_dir / "thesession"
    paths = {n: fetcher.get(SESSION_RAW.format(n), base / f"{n}.json") for n in SESSION_FILES}
    tunes = json.loads(paths["tunes"].read_text(encoding="utf-8"))
    recordings = json.loads(paths["recordings"].read_text(encoding="utf-8"))
    aliases_rows = json.loads(paths["aliases"].read_text(encoding="utf-8"))
    quebec = load_quebec_artists(artists_file)

    recorded: dict[str, list[tuple[str, str]]] = defaultdict(list)  # tune_id → (artiste, album)
    for row in recordings:
        tid = row.get("tune_id")
        artist = quebec.get(fold(row.get("artist") or ""))
        if tid and artist:
            recorded[tid].append((artist, row["recording"]))
    aliases: dict[str, list[str]] = defaultdict(list)
    for row in aliases_rows:
        aliases[row["tune_id"]].append(row["alias"])

    first_setting: dict[str, dict] = {}
    for t in tunes:  # un seul réglage par air : le plus ancien (setting_id minimal)
        if t["type"] not in SESSION_TYPES:
            continue
        cur = first_setting.get(t["tune_id"])
        if cur is None or int(t["setting_id"]) < int(cur["setting_id"]):
            first_setting[t["tune_id"]] = t

    for tid in sorted(first_setting, key=int):
        t = first_setting[tid]
        reasons: list[str] = []
        kinds: list[str] = []
        if tid in recorded:
            artist, album = sorted(set(recorded[tid]))[0]
            more = len(set(recorded[tid])) - 1
            reasons.append(f"enregistré par {artist} (« {album} »)" + (f" et {more} autre(s) enregistrement(s)" if more else ""))
            kinds.append("artist")
        title_hit = french_match(t["name"])
        if title_hit:
            reasons.append(f"titre français (« {title_hit} »)")
            kinds.append("title")
        alias_hit: str | None = None
        for alias in aliases.get(tid, []):
            if alias != t["name"] and french_match(alias):
                alias_hit = alias
                break
        if alias_hit:
            reasons.append(f"alias français « {alias_hit} »")
            kinds.append("alias")
        if not reasons:
            continue
        key_abc = None
        try:
            key_abc = _session_key(t["mode"])
        except AbcError:
            pass
        lines = [
            "X:1", f"T:{t['name']}", f"R:{t['type']}", f"M:{t['meter']}", "L:1/8",
            f"K:{key_abc}" if key_abc else "K:",
        ]
        block = "\n".join(lines) + "\n" + t["abc"].replace("\r\n", "\n").replace("\r", "\n")
        yield RawTune(
            source=SESSION, origin=f"thesession/tunes/{tid}#setting{t['setting_id']}",
            url=f"https://thesession.org/tunes/{tid}#setting{t['setting_id']}",
            block=block, type_hint=SESSION_TYPES[t["type"]],
            because=" ; ".join(reasons), because_kinds=tuple(kinds), fallback_title=t["name"],
            extra_aliases=[a for a in aliases.get(tid, []) if a != t["name"]],
        )


def acadian_session_tunes(raw_dir: Path, fetcher: Fetcher, artists_file: Path = ACADIAN_ARTISTS_FILE) -> Iterator[RawTune]:
    """Airs The Session qualifiés acadiens (enregistrés par artiste acadien ou titre acadien)."""
    base = raw_dir / "thesession"
    paths = {n: fetcher.get(SESSION_RAW.format(n), base / f"{n}.json") for n in SESSION_FILES}
    tunes = json.loads(paths["tunes"].read_text(encoding="utf-8"))
    recordings = json.loads(paths["recordings"].read_text(encoding="utf-8"))
    aliases_rows = json.loads(paths["aliases"].read_text(encoding="utf-8"))
    acadian_artists = load_acadian_artists(artists_file)

    recorded: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in recordings:
        tid = row.get("tune_id")
        artist = acadian_artists.get(fold(row.get("artist") or ""))
        if tid and artist:
            recorded[tid].append((artist, row["recording"]))
    aliases: dict[str, list[str]] = defaultdict(list)
    for row in aliases_rows:
        aliases[row["tune_id"]].append(row["alias"])

    first_setting: dict[str, dict] = {}
    for t in tunes:
        if t["type"] not in SESSION_TYPES:
            continue
        cur = first_setting.get(t["tune_id"])
        if cur is None or int(t["setting_id"]) < int(cur["setting_id"]):
            first_setting[t["tune_id"]] = t

    for tid in sorted(first_setting, key=int):
        t = first_setting[tid]
        reasons: list[str] = []
        kinds: list[str] = []
        if tid in recorded:
            artist, album = sorted(set(recorded[tid]))[0]
            more = len(set(recorded[tid])) - 1
            reasons.append(f"enregistré par {artist} (« {album} »)" + (f" et {more} autre(s) enregistrement(s)" if more else ""))
            kinds.append("artist")
        title_hit = acadian_match(t["name"])
        if title_hit:
            reasons.append(f"titre acadien (« {title_hit} »)")
            kinds.append("title")
        alias_hit: str | None = None
        for alias in aliases.get(tid, []):
            if alias != t["name"] and acadian_match(alias):
                alias_hit = alias
                break
        if alias_hit:
            reasons.append(f"alias acadien « {alias_hit} »")
            kinds.append("alias")
        if not reasons:
            continue
        key_abc = None
        try:
            key_abc = _session_key(t["mode"])
        except AbcError:
            pass
        lines = [
            "X:1", f"T:{t['name']}", f"R:{t['type']}", f"M:{t['meter']}", "L:1/8",
            f"K:{key_abc}" if key_abc else "K:",
        ]
        block = "\n".join(lines) + "\n" + t["abc"].replace("\r\n", "\n").replace("\r", "\n")
        yield RawTune(
            source=SESSION, origin=f"thesession/tunes/{tid}#setting{t['setting_id']}",
            url=f"https://thesession.org/tunes/{tid}#setting{t['setting_id']}",
            block=block, type_hint=SESSION_TYPES[t["type"]],
            because=" ; ".join(reasons), because_kinds=tuple(kinds), fallback_title=t["name"],
            extra_aliases=[a for a in aliases.get(tid, []) if a != t["name"]],
            tradition=TRADITION_ACADIENNE,
        )


def acadian_chambers_tunes(raw_dir: Path, fetcher: Fetcher) -> Iterator[RawTune]:
    """Airs acadiens chez John Chambers (ex: collection Canada, Avila LeBlanc)."""
    base = raw_dir / "chambers_acadian"
    base_url = "http://trillian.mit.edu/~jc/music/abc/Canada/reel/"
    index_file = base / "_index.html"
    index = fetcher.get(base_url, index_file)
    for name in list_abc_files(_decode_bytes(index.read_bytes())):
        if "leblanc" in name.lower() or "acad" in name.lower():
            url = base_url + urllib.parse.quote(name, safe=",")
            path = fetcher.get(url, base / name)
            blocks = split_tunes(_decode_bytes(path.read_bytes()))
            for i, block in enumerate(blocks, 1):
                yield RawTune(
                    source=CHAMBERS,
                    origin=f"Canada/reel/{name}#X{i}",
                    url=url if len(blocks) == 1 else f"{url}#{i}",
                    block=block,
                    type_hint="reel",
                    because=f"John Chambers, collection Canada ({name})",
                    fallback_title=Path(name).stem.replace("_", " "),
                    tradition=TRADITION_ACADIENNE,
                )


NMD_RAW = "https://raw.githubusercontent.com/jukedeck/nottingham-dataset/master/ABC_original/{}"
NMD_FILES = [
    ("ashover.abc", None, "c. 1764", "Ashover Book (David Wall's MS, Derbyshire c. 1764)"),
    ("playford.abc", "reel", "1651-1728", "The English Dancing Master (Playford)"),
    ("hpps.abc", "hornpipe", "XVIIIe-XIXe s.", "Hornpipes traditionnels britanniques (NMD)"),
    ("jigs.abc", "jig", "XVIIIe-XIXe s.", "Jigs traditionnelles britanniques (NMD)"),
    ("reelsa-c.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques A-C (NMD)"),
    ("reelsd-g.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques D-G (NMD)"),
    ("reelsh-l.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques H-L (NMD)"),
    ("reelsm-q.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques M-Q (NMD)"),
    ("reelsr-t.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques R-T (NMD)"),
    ("reelsu-z.abc", "reel", "XVIIIe-XIXe s.", "Reels et contredanses britanniques U-Z (NMD)"),
    ("waltzes.abc", "waltz", "c. 1790-1840", "Valses traditionnelles britanniques (NMD)"),
]


def british_colonial_nmd_tunes(raw_dir: Path, fetcher: Fetcher) -> Iterator[RawTune]:
    """Airs britanniques de la Nottingham Music Database (Ashover, Playford, hornpipes, etc.)."""
    base = raw_dir / "nottingham"
    for filename, type_hint, epoque, because in NMD_FILES:
        url = NMD_RAW.format(filename)
        path = fetcher.get(url, base / filename)
        blocks = split_tunes(_decode_bytes(path.read_bytes()))
        for i, block in enumerate(blocks, 1):
            yield RawTune(
                source=NOTTINGHAM,
                origin=f"nottingham/{filename}#X{i}",
                url=f"{url}#{i}",
                block=block,
                type_hint=type_hint,
                because=because,
                fallback_title=Path(filename).stem,
                tradition=TRADITION_BRITANNIQUE_COLONIALE,
                epoque=epoque,
            )


CAHUSAC_URL = "http://trillian.mit.edu/~jc/music/abc/Vintage/24CountryDances_1809_Cahusac.abc"


def british_colonial_cahusac_tunes(raw_dir: Path, fetcher: Fetcher) -> Iterator[RawTune]:
    """24 contredanses pour l'année 1809 (Thomas Cahusac, Londres)."""
    base = raw_dir / "cahusac"
    path = fetcher.get(CAHUSAC_URL, base / "24CountryDances_1809_Cahusac.abc")
    blocks = split_tunes(_decode_bytes(path.read_bytes()))
    for i, block in enumerate(blocks, 1):
        yield RawTune(
            source=CAHUSAC,
            origin=f"cahusac/1809#X{i}",
            url=f"{CAHUSAC_URL}#{i}",
            block=block,
            type_hint=None,
            because="24 Country Dances for the Year 1809 (Cahusac, Londres)",
            fallback_title=f"Cahusac 1809 #{i}",
            tradition=TRADITION_BRITANNIQUE_COLONIALE,
            epoque="1809",
        )


AMREV_BASE = "http://trillian.mit.edu/~jc/music/abc/AmRev/"
AMREV_DIRS = {"march": "march", "jig": "jig", "reel": "reel"}
ENGLAND_MARCH_BASE = "http://trillian.mit.edu/~jc/music/abc/England/march/"
GARRISON_KEYWORDS = ("grenadier", "british", "duke", "york", "king", "queen", "fife", "royal", "garrison", "field", "camp", "hampshire", "holborn", "monk")


def british_colonial_amrev_tunes(raw_dir: Path, fetcher: Fetcher) -> Iterator[RawTune]:
    """Marches militaires de garnison, fifre et tambour, contredanses du XVIIIe s. (AmRev JC)."""
    base = raw_dir / "amrev"
    for subdir, typ in AMREV_DIRS.items():
        url_dir = AMREV_BASE + subdir + "/"
        index = fetcher.get(url_dir, base / "_index" / f"{subdir}.html")
        for name in list_abc_files(_decode_bytes(index.read_bytes())):
            url = url_dir + urllib.parse.quote(name, safe=",")
            path = fetcher.get(url, base / subdir / name)
            blocks = split_tunes(_decode_bytes(path.read_bytes()))
            for i, block in enumerate(blocks, 1):
                yield RawTune(
                    source=AMREV,
                    origin=f"amrev/{subdir}/{name}#X{i}",
                    url=url if len(blocks) == 1 else f"{url}#{i}",
                    block=block,
                    type_hint=typ,
                    because=f"John Chambers AmRev, garnison et fifre XVIIIe s. ({subdir}/{name})",
                    fallback_title=Path(name).stem.replace("_", " "),
                    tradition=TRADITION_BRITANNIQUE_COLONIALE,
                    epoque="c. 1775-1783",
                )
    # Marches de garnison et régimentaires britanniques XVIIIe s.
    index_england = fetcher.get(ENGLAND_MARCH_BASE, base / "_index" / "england_march.html")
    for name in list_abc_files(_decode_bytes(index_england.read_bytes())):
        if any(k in name.lower() for k in GARRISON_KEYWORDS):
            url = ENGLAND_MARCH_BASE + urllib.parse.quote(name, safe=",")
            path = fetcher.get(url, base / "garrison_marches" / name)
            blocks = split_tunes(_decode_bytes(path.read_bytes()))
            for i, block in enumerate(blocks, 1):
                yield RawTune(
                    source=AMREV,
                    origin=f"england/march/{name}#X{i}",
                    url=url if len(blocks) == 1 else f"{url}#{i}",
                    block=block,
                    type_hint="march",
                    because=f"John Chambers England, marche de garnison XVIIIe s. ({name})",
                    fallback_title=Path(name).stem.replace("_", " "),
                    tradition=TRADITION_BRITANNIQUE_COLONIALE,
                    epoque="c. 1760-1820",
                )

# ── Normalisation ────────────────────────────────────────────────────


def _classify(raw: RawTune, tune: Tune) -> str | None:
    """Type retenu : dossier/type source, sauf quadrille/cotillon/hornpipe annoncés par `R:` ou le titre ;
    sans type source : `R:`, puis titre, puis inférence depuis le mètre M:."""
    r_type = type_from_text(tune.first("R"))
    title = tune.first("T") or raw.fallback_title
    if raw.type_hint:
        for special in ("quadrille", "cotillon", "hornpipe"):
            if r_type == special or type_from_text(title) == special:
                return special
        return raw.type_hint
    if tune.first("R"):
        return r_type
    t_type = type_from_text(title)
    if t_type:
        return t_type
    m = tune.first("M")
    if m in ("6/8", "9/8"):
        return "jig"
    if m in ("3/4", "3/8"):
        return "waltz"
    if m in ("4/4", "2/2", "C", "C|", "2/4"):
        return "reel"
    return None


def _normalised_abc(tune: Tune, title: str, type_: str, analysis) -> str:
    lines = ["X:1", f"T:{title}"]
    lines += [f"T:{t}" for t in tune.all("T")[1:]]
    skip = {"X", "T", "R", "M", "L", "K"}
    lines += [f"{k}:{v}" for k, v in tune.headers if k not in skip]
    lines.append(f"R:{type_}")
    lines.append(f"M:{tune.first('M') if 'M' not in analysis.inferred else analysis.meter}")
    unit = analysis.unit
    lines.append(f"L:{unit.numerator}/{unit.denominator}")
    lines.append(f"K:{tune.first('K')}")
    body = [ln.rstrip() for ln in tune.body if ln.strip()]
    return "\n".join(lines + body) + "\n"


def process(raw: RawTune, stats: Stats) -> Candidate | None:
    """Un air brut → Candidat, ou None (rejeté ou hors types ; compté dans `stats`)."""
    tune = parse_tune(raw.block)
    type_ = _classify(raw, tune)
    if type_ is None:
        stats.ignored[raw.source] += 1
        return None

    def reject(reason: str, detail: str = "") -> None:
        stats.rejected[(type_, raw.source)] += 1
        stats.reject_reasons[(raw.source, reason)] += 1
        stats.rejects.append({"source": raw.source, "type": type_, "origin": raw.origin,
                              "reason": reason, "detail": detail})

    if not tune.has_key or not (tune.first("K") or "").strip():
        reject(REJECT_NO_KEY)
        return None
    try:
        analysis = analyse(tune, DEFAULT_METER[type_])
    except AbcError as exc:
        reject(exc.reason, exc.detail)
        return None
    except Exception as exc:  # parse inattendu : rejeté, jamais silencieux
        reject(REJECT_PARSE, f"{type(exc).__name__}: {exc}")
        return None
    if "M" in analysis.inferred:
        stats.inferred_meter += 1

    title_raw = (tune.first("T") or tune.first("P") or raw.fallback_title).strip()
    title = decode_abc_text(title_raw)
    abc = _normalised_abc(tune, title_raw, type_, analysis)
    sha = hashlib.sha256(abc.encode("utf-8")).hexdigest()
    aliases = [decode_abc_text(t) for t in tune.all("T")[1:]] + [decode_abc_text(a) for a in raw.extra_aliases]
    return Candidate(
        id=f"{slugify(title)}-{sha[:8]}", title=title,
        aliases=[a for a in aliases if a and a != title],
        tradition=raw.tradition,
        type=type_,
        meter=analysis.meter, key=analysis.key, mode=analysis.mode, bars=analysis.bars,
        source=raw.source, url=raw.url, license=LICENSES.get(raw.source, raw.source),
        sha256=sha,
        included_because=raw.because, because_kinds=raw.because_kinds,
        incipit=analysis.incipit, abc=abc,
        epoque=raw.epoque,
    )


# ── Dédoublonnage ────────────────────────────────────────────────────


def deduplicate(candidates: Iterable[Candidate], stats: Stats) -> list[Candidate]:
    """Fusionne les doublons : même titre normalisé ET même incipit transposé (intervalles).

    Le gardé est le JC (accords présents), puis la version la plus riche en accords, puis
    l'identifiant ; les autres sont notés dans `also_in` (et leur titre dans `aliases`).
    Un air sans incipit exploitable (< 2 notes) ne fusionne que s'il est strictement identique.
    """
    ordered = sorted(
        candidates,
        key=lambda c: (SOURCE_RANK[c.source], -c.abc.count('"'), c.id, c.url),
    )
    kept: list[Candidate] = []
    index: dict[tuple, Candidate] = {}
    for cand in ordered:
        ivs = intervals(cand.incipit)
        key = (title_key(cand.title), ivs if ivs else cand.sha256)
        keeper = index.get(key)
        if keeper is None:
            index[key] = cand
            kept.append(cand)
            continue
        stats.merged[(cand.type, cand.source)] += 1
        keeper.also_in.append({"source": cand.source, "url": cand.url, "title": cand.title,
                               "sha256": cand.sha256})
        if cand.title != keeper.title and cand.title not in keeper.aliases:
            keeper.aliases.append(cand.title)
    return kept


# ── Écriture ─────────────────────────────────────────────────────────


def write_corpus(root: Path, kept: list[Candidate], stats: Stats, today: dt.date) -> str:
    tunes_dir = root / "tunes"
    if not tunes_dir.is_symlink() and tunes_dir.exists():
        shutil.rmtree(tunes_dir)
    seen: set[str] = set()
    for c in kept:
        if c.id in seen:
            raise RuntimeError(f"identifiant dupliqué : {c.id}")
        seen.add(c.id)
        path = tunes_dir / c.type / f"{c.id}.abc"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(c.abc, encoding="utf-8")

    rows = sorted((c.manifest_row() for c in kept), key=lambda r: r["id"])
    manifest = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.jsonl"
    manifest_path.write_text(manifest, encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest.encode("utf-8")).hexdigest()

    rejects = sorted(stats.rejects, key=lambda r: (r["source"], r["origin"]))
    (root / "rejects.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rejects), encoding="utf-8"
    )

    # VERSION = date + compte ; la date ne bouge que si le manifeste change (reproductibilité).
    version_path = root / "VERSION"
    new_tail = f"manifest_sha256: {manifest_sha}\n"
    if not (version_path.exists() and version_path.read_text(encoding="utf-8").split("\n", 1)[1:] == [new_tail]):
        version_path.write_text(f"{today.isoformat()}+{len(rows)}\n{new_tail}", encoding="utf-8")
    return manifest_sha


def migrate_manifest(manifest_path: Path, tradition: str = TRADITION_QUEBECOISE) -> str:
    """Migre un manifest.jsonl existant vers le nouveau schéma avec tradition (DS-T6)."""
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifeste introuvable : {manifest_path}")
    lines = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    migrated = []
    for row in lines:
        t_row = {
            "id": row["id"],
            "title": row["title"],
            "aliases": sorted(set(row.get("aliases", []))),
            "tradition": row.get("tradition", tradition),
            "type": row["type"],
            "meter": row["meter"],
            "key": row["key"],
            "mode": row["mode"],
            "bars": row["bars"],
            "source": row["source"],
            "url": row["url"],
            "license": row["license"],
            "sha256": row["sha256"],
            "included_because": row["included_because"],
            "incipit": row["incipit"],
        }
        if "epoque" in row and row["epoque"]:
            t_row["epoque"] = row["epoque"]
        if "also_in" in row and row["also_in"]:
            t_row["also_in"] = sorted(row["also_in"], key=lambda a: (a["source"], a["url"]))
        migrated.append(t_row)
    serialized = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in migrated)
    manifest_path.write_text(serialized, encoding="utf-8")
    new_sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    version_path = manifest_path.parent / "VERSION"
    if version_path.exists():
        v_lines = version_path.read_text(encoding="utf-8").splitlines()
        first_line = v_lines[0] if v_lines else f"{dt.date.today().isoformat()}+{len(migrated)}"
        version_path.write_text(f"{first_line}\nmanifest_sha256: {new_sha}\n", encoding="utf-8")
    return new_sha


def format_table(stats: Stats) -> str:
    sources = sorted(set(s for (_, s) in stats.kept) | set(s for (_, s) in stats.rejected))
    head = f"{'type':<10} {'source':<14} {'retenus':>8} {'rejetés':>8} {'fusionnés':>9}"
    lines = [head, "-" * len(head)]
    total = Counter()
    for t in TYPES:
        for s in sources:
            k, r, m = stats.kept[(t, s)], stats.rejected[(t, s)], stats.merged[(t, s)]
            if k or r or m:
                lines.append(f"{t:<10} {s:<14} {k:>8} {r:>8} {m:>9}")
                total["k"] += k; total["r"] += r; total["m"] += m
        tk = sum(stats.kept[(t, s)] for s in sources)
        if tk:
            lines.append(f"{t:<10} {'TOTAL':<14} {tk:>8}")
    lines.append("-" * len(head))
    lines.append(f"{'tous':<10} {'':<14} {total['k']:>8} {total['r']:>8} {total['m']:>9}")
    if stats.reasons:
        rl = [f"{'raison':<22}", f"{'artiste':>8}", f"{'titre FR':>9}", f"{'alias FR':>9}"]
        lines += ["", " ".join(rl), "-" * len(" ".join(rl))]
        for t in TYPES:
            a, ti, al = (stats.reasons[(t, k)] for k in ("artist", "title", "alias"))
            if a or ti or al:
                lines.append(f"{t:<22} {a:>8} {ti:>9} {al:>9}")
    return "\n".join(lines)


DEFAULT_ROOTS: dict[str, Path] = {
    TRADITION_QUEBECOISE: Path("corpus/trad"),
    TRADITION_ACADIENNE: Path("corpus/acadienne"),
    TRADITION_BRITANNIQUE_COLONIALE: Path("corpus/britannique_coloniale"),
}


def build(
    root: Path,
    fetcher: Fetcher,
    tradition: str = TRADITION_QUEBECOISE,
    today: dt.date | None = None,
    raw_tunes: Iterable[RawTune] | None = None,
) -> tuple[list[Candidate], Stats, str]:
    stats = Stats()
    if raw_tunes is None:
        raw_dir = root / "raw"
        if tradition == TRADITION_QUEBECOISE:
            raw_tunes = [*chambers_tunes(raw_dir, fetcher), *session_tunes(raw_dir, fetcher)]
        elif tradition == TRADITION_ACADIENNE:
            session_raw_dir = raw_dir if (raw_dir / "thesession").exists() or not (Path("corpus/trad/raw/thesession")).exists() else Path("corpus/trad/raw")
            raw_tunes = [*acadian_chambers_tunes(raw_dir, fetcher), *acadian_session_tunes(session_raw_dir, fetcher)]
        elif tradition == TRADITION_BRITANNIQUE_COLONIALE:
            raw_tunes = [
                *british_colonial_nmd_tunes(raw_dir, fetcher),
                *british_colonial_cahusac_tunes(raw_dir, fetcher),
                *british_colonial_amrev_tunes(raw_dir, fetcher),
            ]
        else:
            raise ValueError(f"tradition inconnue : {tradition}")
    candidates = [c for r in raw_tunes if (c := process(r, stats)) is not None]
    kept = deduplicate(candidates, stats)
    for c in kept:
        stats.kept[(c.type, c.source)] += 1
        for kind in c.because_kinds:
            stats.reasons[(c.type, kind)] += 1
    sha = write_corpus(root, kept, stats, today or dt.date.today())
    return kept, stats, sha


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trad-corpus", description="Télécharge et normalise les corpus trad")
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--tradition", choices=[*TRADITIONS, "all"], default="all")
    ap.add_argument("--delay", type=float, default=0.3, help="secondes entre deux requêtes réseau")
    ap.add_argument("--offline", action="store_true", help="n'utiliser que le cache raw/")
    ap.add_argument("--migrate-only", action="store_true", help="migrer uniquement le manifeste existant")
    args = ap.parse_args(argv)

    if args.migrate_only:
        root = args.root or DEFAULT_ROOTS[TRADITION_QUEBECOISE]
        sha = migrate_manifest(root / "manifest.jsonl", tradition=TRADITION_QUEBECOISE)
        print(f"Manifeste migré : {root}/manifest.jsonl (sha256 {sha[:16]}…)")
        return 0

    fetcher = Fetcher(delay_s=args.delay, offline=args.offline)
    if args.root is not None:
        if args.tradition == "all":
            trad = args.root.name if args.root.name in TRADITIONS else TRADITION_QUEBECOISE
            traditions = [trad]
        else:
            traditions = [args.tradition]
    else:
        traditions = list(TRADITIONS) if args.tradition == "all" else [args.tradition]

    for trad in traditions:
        root = args.root or DEFAULT_ROOTS[trad]
        print(f"\n=== Corpus trad : {trad} ({root}) ===")
        if trad == TRADITION_QUEBECOISE and (root / "manifest.jsonl").exists() and not (root / "raw").exists() and args.offline:
            sha = migrate_manifest(root / "manifest.jsonl", tradition=TRADITION_QUEBECOISE)
            print(f"Corpus québécois existant conservé et migré ({root}/manifest.jsonl, sha256 {sha[:16]}…)")
            continue
        kept, stats, sha = build(root, fetcher, tradition=trad)
        print(f"téléchargements : {fetcher.network_requests} requêtes réseau, {fetcher.cache_hits} fichiers en cache")
        print(format_table(stats))
        print(f"\nairs hors types ignorés : {dict(stats.ignored)} ; M: déduit du type : {stats.inferred_meter}")
        print("raisons de rejet :")
        for (source, reason), n in sorted(stats.reject_reasons.items()):
            print(f"  {source:<14} {reason:<20} {n}")
        print(f"\n{len(kept)} airs → {root}/manifest.jsonl (sha256 {sha[:16]}…)")
        if (root / "VERSION").exists():
            print((root / "VERSION").read_text(encoding="utf-8").splitlines()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
