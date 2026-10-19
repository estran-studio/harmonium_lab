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
SOURCE_RANK = {CHAMBERS: 0, SESSION: 1}  # priorité au dédoublonnage : accords présents chez JC
LICENSES = {
    CHAMBERS: "non précisée (usage interne, attribution John Chambers)",
    SESSION: "ODbL",
}

CHAMBERS_BASE = "http://trillian.mit.edu/~jc/music/abc/Quebec/"
CHAMBERS_TYPED_DIRS = {"reel": "reel", "jig": "jig", "waltz": "waltz", "march": "march"}
CHAMBERS_OTHER_DIRS = ("", "misc", "montrealsession")  # "" = racine
SESSION_RAW = "https://raw.githubusercontent.com/adactio/TheSession-data/main/json/{}.json"
SESSION_FILES = ("tunes", "recordings", "aliases")
SESSION_TYPES = {"reel": "reel", "jig": "jig", "waltz": "waltz", "march": "march"}

# Mètre par défaut quand `M:` manque (garantit l'en-tête M: de l'ABC normalisé).
DEFAULT_METER = {
    "reel": "4/4", "jig": "6/8", "waltz": "3/4", "march": "2/4", "quadrille": "6/8", "cotillon": "6/8",
}

# Titre/alias « français québécois » : motifs sur texte replié (sans accents, minuscules).
FRENCH_TITLE = re.compile(
    r"\b(gigues?|valses?|quadrilles?|cotillons?|cotillions?|quebec(?:ois(?:e|es)?)?"
    r"|reel (?:de|du|des|d|au|aux|pour))\b"
)
FRENCH_REEL_ACCENT = re.compile(r"\b[Rr]éel\b")  # « réel » accentué

ARTISTS_FILE = Path(__file__).with_name("quebec_artists.json")


def load_quebec_artists(path: Path = ARTISTS_FILE) -> dict[int, str]:
    """`QUEBEC_ARTISTS` : identifiant d'artiste The Session → nom de l'artiste québécois."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for entry in data["artists"]:
        for artist_id in entry["session_artist_ids"]:
            out.setdefault(int(artist_id), entry["name"])
    return out


def quebec_artist_names(path: Path = ARTISTS_FILE) -> list[str]:
    return [e["name"] for e in json.loads(path.read_text(encoding="utf-8"))["artists"]]


def french_title_match(*texts: str) -> str | None:
    """Premier motif français trouvé dans un titre ou alias, sinon None."""
    for text in texts:
        m = FRENCH_TITLE.search(fold(text)) or FRENCH_REEL_ACCENT.search(text)
        if m:
            return m.group(0)
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
    incipit: list[int]
    abc: str
    also_in: list[dict] = field(default_factory=list)

    def manifest_row(self) -> dict:
        row = {
            "id": self.id, "title": self.title, "aliases": sorted(set(self.aliases)),
            "type": self.type, "meter": self.meter, "key": self.key, "mode": self.mode,
            "bars": self.bars, "source": self.source, "url": self.url, "license": self.license,
            "sha256": self.sha256, "included_because": self.included_because,
            "incipit": self.incipit,
        }
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
        if tid and row["artist"].isdigit() and int(row["artist"]) in quebec:
            recorded[tid].append((quebec[int(row["artist"])], row["recording"]))
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
        names = [t["name"], *aliases.get(tid, [])]
        reasons: list[str] = []
        if tid in recorded:
            artist, album = sorted(set(recorded[tid]))[0]
            more = len(set(recorded[tid])) - 1
            reasons.append(f"enregistré par {artist} (« {album} »)" + (f" et {more} autre(s) enregistrement(s)" if more else ""))
        hit = french_title_match(*names)
        if hit:
            reasons.append(f"titre/alias français (« {hit} »)")
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
            because=" ; ".join(reasons), fallback_title=t["name"],
            extra_aliases=[a for a in aliases.get(tid, []) if a != t["name"]],
        )


# ── Normalisation ────────────────────────────────────────────────────


def _classify(raw: RawTune, tune: Tune) -> str | None:
    """Type retenu : dossier/type source, sauf quadrille/cotillon annoncés par `R:` ou le titre ;
    sans type source (racine, misc, montrealsession) : `R:` puis titre."""
    r_type = type_from_text(tune.first("R"))
    title = tune.first("T") or raw.fallback_title
    if raw.type_hint:
        for special in ("quadrille", "cotillon"):
            if r_type == special or type_from_text(title) == special:
                return special
        return raw.type_hint
    if tune.first("R"):
        return r_type
    return type_from_text(title)


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
        aliases=[a for a in aliases if a and a != title], type=type_,
        meter=analysis.meter, key=analysis.key, mode=analysis.mode, bars=analysis.bars,
        source=raw.source, url=raw.url, license=LICENSES[raw.source], sha256=sha,
        included_because=raw.because, incipit=analysis.incipit, abc=abc,
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
    if tunes_dir.exists():
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


def format_table(stats: Stats) -> str:
    sources = (CHAMBERS, SESSION)
    head = f"{'type':<10} {'source':<11} {'retenus':>8} {'rejetés':>8} {'fusionnés':>9}"
    lines = [head, "-" * len(head)]
    total = Counter()
    for t in TYPES:
        for s in sources:
            k, r, m = stats.kept[(t, s)], stats.rejected[(t, s)], stats.merged[(t, s)]
            if k or r or m:
                lines.append(f"{t:<10} {s:<11} {k:>8} {r:>8} {m:>9}")
                total["k"] += k; total["r"] += r; total["m"] += m
        tk = sum(stats.kept[(t, s)] for s in sources)
        if tk:
            lines.append(f"{t:<10} {'TOTAL':<11} {tk:>8}")
    lines.append("-" * len(head))
    lines.append(f"{'tous':<10} {'':<11} {total['k']:>8} {total['r']:>8} {total['m']:>9}")
    return "\n".join(lines)


# ── Orchestration ────────────────────────────────────────────────────


def build(root: Path, fetcher: Fetcher, today: dt.date | None = None,
          raw_tunes: Iterable[RawTune] | None = None) -> tuple[list[Candidate], Stats, str]:
    stats = Stats()
    if raw_tunes is None:
        raw_dir = root / "raw"
        raw_tunes = [*chambers_tunes(raw_dir, fetcher), *session_tunes(raw_dir, fetcher)]
    candidates = [c for r in raw_tunes if (c := process(r, stats)) is not None]
    kept = deduplicate(candidates, stats)
    for c in kept:
        stats.kept[(c.type, c.source)] += 1
    sha = write_corpus(root, kept, stats, today or dt.date.today())
    return kept, stats, sha


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trad-corpus", description="Télécharge et normalise le corpus trad québécois")
    ap.add_argument("--root", type=Path, default=Path("corpus/trad"))
    ap.add_argument("--delay", type=float, default=0.3, help="secondes entre deux requêtes réseau")
    ap.add_argument("--offline", action="store_true", help="n'utiliser que le cache raw/")
    args = ap.parse_args(argv)

    fetcher = Fetcher(delay_s=args.delay, offline=args.offline)
    kept, stats, sha = build(args.root, fetcher)

    print(f"téléchargements : {fetcher.network_requests} requêtes réseau, {fetcher.cache_hits} fichiers en cache")
    print(format_table(stats))
    print(f"\nairs hors types ignorés : {dict(stats.ignored)} ; M: déduit du type : {stats.inferred_meter}")
    print("raisons de rejet :")
    for (source, reason), n in sorted(stats.reject_reasons.items()):
        print(f"  {source:<11} {reason:<20} {n}")
    print(f"\n{len(kept)} airs → {args.root}/manifest.jsonl (sha256 {sha[:16]}…)")
    print((args.root / "VERSION").read_text(encoding="utf-8").splitlines()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
