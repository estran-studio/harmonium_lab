"""S1 : régénère `references/styles/<style>.json` et manifestes des sources.

Usage : `python -m harmonium_lab.styles.build --all` (cache vérifié avant lecture) ; `--no-lmd`
pour un cycle court, `--only <source>` pour une source. Les seuls fichiers versionnés sont
manifestes + VERSION + statistiques. Aucun MIDI/JAMS/CSV/WAV ne sort de `corpus/*/raw/`.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from ..backing.corpus_cache import (
    ROOT,
    open_verified,
    write_json,
    write_jsonl,
    write_version,
)
from .core import Piece, attacks, detect_feel
from .harmony import infer_chords
from .measure import BassAcc, CompAcc, DrumAcc, SyncAcc, drum_role
from .sources import dubroom, filobass, gmd, guitarset, jtd, lmd, pop909, rwc, wjazzd

STYLE_PROFILE = {
    "swing": "wjazzd_swing",
    "ballad": "wjazzd_ballad",
    "jazz_waltz": "gmd_jazz_waltz",
    "bossa": "gmd_latin_brazilian_bossa",
    "samba": "gmd_latin_brazilian_samba",
    "baiao": "gmd_latin_brazilian_baiao",
    "afrocuban": "gmd_afrocuban",
    "funk": "gmd_funk",
    "soul": "gmd_soul",
    "reggae": "gmd_reggae",
    "rock": "gmd_rock",
    "pop": "gmd_pop",
    "blues_shuffle": "gmd_blues_shuffle",
}
PROXIES = {
    "singer_songwriter": "pop",
    "jazz": "swing",
    "latin_jazz": "bossa",
    "funk_jazz": "funk",
}
SOURCES: dict[str, dict[str, str]] = {
    "egmd": {
        "url": "https://storage.googleapis.com/magentadata/datasets/e-gmd/v1.0.0/e-gmd-v1.0.0.csv",
        "archive": "e-gmd-v1.0.0.csv",
        "license": "CC-BY-4.0",
        "license_url": "https://magenta.tensorflow.org/datasets/e-gmd#license",
        "md5": "a212cb4b1aec205ef1882d9f9bb6150a",
        "sha256": "80677e8fb00e973f33cb91ddaaf7f0cffe55359f9a76c1833ce56c84d1d92c64",
    },
    "rwc": {
        "url": "https://zenodo.org/records/15804654/files/RWC-website.zip",
        "archive": "RWC-website.zip",
        "license": "CC-BY-NC-SA-4.0 (Zenodo) ; Pledge AIST recherche non redistribuable",
        "license_url": "https://zenodo.org/records/15804654",
        "md5": "6dd30ee9be5530d7151fd60fed3105db",
        "sha256": "f20e4ef0854fb70f6cc66ac04e016f36468286a330471fef2f663672075ff6d5",
    },
    "dubroom": {
        "url": "http://midi.dubroom.org/zip/dubroom_midi_files.zip",
        "archive": "dubroom_midi_files.zip",
        "license": "CC-BY-NC-SA-4.0",
        "license_url": "http://midi.dubroom.org/",
        "sha256": "26f6b92503bbb8349f31d6fab7acd112c468d7fd55ee383bef5b399fcc441ce9",
    },
    "guitarset": {
        "url": "https://zenodo.org/api/records/3371780/files/annotation.zip/content",
        "archive": "annotation.zip",
        "license": "CC-BY-4.0",
        "license_url": "https://zenodo.org/api/records/3371780",
        "md5": "b39b78e63d3446f2e54ddb7a54df9b10",
        "sha256": "8daa02e6417ccca1685feb44b135e95928ad7037e5032ecb326b5791856fda99",
    },
    "pop909": {
        "url": "https://github.com/music-x-lab/POP909-Dataset/raw/master/POP909.zip",
        "archive": "POP909.zip",
        "license": "MIT",
        "license_url": "https://raw.githubusercontent.com/music-x-lab/POP909-Dataset/master/LICENSE",
        "sha256": "32cedcc22585eff9c090791941a0c4e5e6372daa2a11f7b04bd038f941ac32c6",
    },
    "filobass": {
        "url": "https://zenodo.org/api/records/10069709/files/FiloBass_v1.0.0.zip/content",
        "archive": "FiloBass_v1.0.0.zip",
        "license": "CC-BY-4.0",
        "license_url": "https://zenodo.org/api/records/10069709",
        "md5": "ea1f52ffd492bf3654d720529f15bd9b",
        "sha256": "67cca62578c408b65e2338c7edf9f5fc6c5192ea1f14625faa98357f9cd44f43",
    },
    "jtd": {
        "url": "https://github.com/HuwCheston/Jazz-Trio-Database/releases/download/v02-zenodo/jazz-trio-database-v02.zip",
        "archive": "jazz-trio-database-v02.zip",
        "license": "MIT",
        "license_url": "https://github.com/HuwCheston/Jazz-Trio-Database/blob/main/LICENSE",
        "sha256": "42c3df0700e0cd6e73231b9ed111283600750305e2e9cf451f80664d1ec90025",
    },
    "wjazzd": {
        "url": "https://jazzomat.hfm-weimar.de/download/downloads/wjazzd.db",
        "archive": "wjazzd.db",
        "license": "ODbL-1.0+DbCL-1.0",
        "license_url": "https://jazzomat.hfm-weimar.de/download/download.html",
        "sha256": "af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12",
    },
    "gmd": {
        "url": "https://storage.googleapis.com/magentadata/datasets/groove/groove-v1.0.0-midionly.zip",
        "archive": "groove-v1.0.0-midionly.zip",
        "license": "CC-BY-4.0",
        "license_url": "https://magenta.withgoogle.com/datasets/groove",
        "sha256": "651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e",
    },
    "lmd": {
        "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz",
        "archive": "lmd_matched.tar.gz",
        "license": "CC-BY-4.0 (compilation ; droits des œuvres non garantis)",
        "license_url": "https://colinraffel.com/projects/lmd/#license",
        "sha256": "621ff830aed771f469e5bfa13dc12a33c6ed69090adeda63d0b5c47783af0191",
    },
    "msd-genres": {
        "url": "https://www.tagtraum.com/genres/msd_tagtraum_cd2c.cls.zip",
        "archive": "msd_tagtraum_cd2c.cls.zip",
        "license": "Research only, strictly non-commercial",
        "license_url": "https://www.tagtraum.com/msd_genre_datasets.html",
        "sha256": "9c7e3437978a9adc823cabe14260fdaa6cb272e1dbaafa68cb3d65c1a93bcb11",
    },
}
LMD_EXTRAS = (
    (
        "match_scores.json",
        "http://hog.ee.columbia.edu/craffel/lmd/match_scores.json",
        "CC-BY-4.0",
        "https://colinraffel.com/projects/lmd/#license",
        "267bc606dfa21f0ad0601a4a080972cd4ae8088fe4003b9bb2811b5be060a102",
    ),
    (
        "msd-MASD-styleAssignment.cls",
        "http://www.ifs.tuwien.ac.at/mir/msd/partitions/msd-MASD-styleAssignment.cls",
        "licence non publiée",
        "https://www.ifs.tuwien.ac.at/mir/msd/download.html",
        "932131b0749db52d2edc3d7dbcd3f83b1dc72915b9e401812182d5564e70e84f",
    ),
    (
        "lastfm_tags.db",
        "http://labrosa.ee.columbia.edu/~dpwe/tmp/lastfm_tags.db",
        "licence non publiée",
        "http://millionsongdataset.com/lastfm/",
        "2bf7d84d44612ab775afbc97d85e752fb2c9dfa75d357cc4fcd50b5d6c9fe6e5",
    ),
)


def path_of(source: str) -> Path:
    return ROOT / "corpus" / source / "raw" / SOURCES[source]["archive"]


def ensure(source: str, offline: bool) -> Path:
    """Télécharge si absent ; refuse avant lecture toute archive dont le SHA256 ne correspond pas."""
    from ..backing.corpus_cache import fetch
    from ..trad.download import Fetcher

    meta = SOURCES[source]
    sha = meta["sha256"]
    if not sha:
        raise ValueError(
            f"SHA256 non renseigné pour {source} (l'archive doit être épinglée avant lecture)"
        )
    dest = path_of(source)
    if offline:
        return open_verified(dest, sha)
    return fetch(meta["url"], dest, sha, fetcher=Fetcher())


def _checksums(sources: set[str]) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    for source in sorted(sources):
        meta = SOURCES[source]
        p = ensure(source, True)
        rows[source] = [
            {
                "archive": meta["archive"],
                "url": meta["url"],
                "sha256": meta["sha256"],
                "md5_published": meta.get("md5"),
                "license": meta["license"],
                "license_url": meta["license_url"],
                "size_bytes": p.stat().st_size,
            }
        ]
    for name, url, license_, license_url, sha in LMD_EXTRAS:
        source = "lmd" if name == "match_scores.json" else "msd-genres"
        if source not in sources:
            continue
        p = ROOT / "corpus" / source / "raw" / name
        rows[source].append(
            {
                "archive": name,
                "url": url,
                "sha256": sha,
                "size_bytes": p.stat().st_size,
                "license": license_,
                "license_url": license_url,
            }
        )
    return rows


def manifest_sources(
    rows: dict[str, list[dict]], counts: dict[str, dict[str, Any]]
) -> None:
    """Un manifeste par source ; pas de notes, de titres ni de chemins vers le matériau protégé."""
    for source, items in sorted(rows.items()):
        if source in ("gmd", "jtd", "wjazzd"):
            continue  # manifestes exhaustifs de L2, déjà versionnés : ne pas les écraser.
        directory = ROOT / "corpus" / source
        manifest = write_jsonl(directory / "manifest.jsonl", items)
        write_version(
            directory / "VERSION",
            {
                "source": source,
                "url": items[0]["url"],
                "sha256": items[0]["sha256"],
                "license": items[0]["license"],
                "subset": json.dumps(counts.get(source, {}), sort_keys=True),
            },
            manifest,
        )


class Acc:
    def __init__(self) -> None:
        self.bass = BassAcc()
        self.comp = CompAcc()
        self.drums = DrumAcc()
        self.sync = SyncAcc()

    def add(self, p: Piece) -> None:
        if p.bass:
            self.bass.add(p)
        if p.comp:
            self.comp.add(p)
        if p.drums:
            self.drums.add(p)
        if p.drums and (p.bass or p.comp):
            self.sync.add(p)

    def summary(self, source: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name in ("bass", "comp", "drums"):
            acc = getattr(self, name)
            if acc.pieces:
                stat = acc.summary()
                if source == "wjazzd" and name == "bass":
                    for key in (
                        "rhythm_patterns",
                        "rhythm_patterns_note",
                        "step_probability",
                        "notes_per_bar",
                        "legato_ratio",
                        "duration_beats",
                        "repetition_rhythm",
                    ):
                        stat.pop(key, None)
                    stat["rhythm_note"] = (
                        "WJazzD relève une hauteur par temps, sans attaque ni durée : aucun motif rythmique, durée, répétition rythmique ou vélocité observables ; les hauteurs et degrés par temps le sont."
                    )
                if source == "filobass" and name == "bass":
                    stat["timing_note"] = (
                        "Partition quantifiée : écart à la grille non observable ; vélocités absentes."
                    )
                if source == "jtd" and name == "comp":
                    stat["comping_note"] = (
                        "Transcription automatique de piano, comping ET solo non séparés ; vélocité et densité susceptibles d'être biaisées."
                    )
                if source == "lmd" and stat["reliability"] == "assez":
                    stat["reliability"] = "juste"
                    stat["reliability_note"] = (
                        "Effectif suffisant mais appariement genre↔MIDI, transcription amateur et interprètes non vérifiés : fiabilité au mieux juste."
                    )
                if source == "rwc" and stat["reliability"] == "assez":
                    stat["reliability"] = "juste"
                    stat["reliability_note"] = (
                        "MIDI séquencés ; genres fins à 3 morceaux seulement, pop/jazz plus nombreux mais hétérogènes ; Pledge AIST recherche non redistribuable."
                    )
                if source == "dubroom" and stat["reliability"] == "assez":
                    stat["reliability"] = "juste"
                    stat["reliability_note"] = (
                        "106 séquences d'un seul collectif, MIDI séquencé : fiabilité au mieux juste pour la diversité du reggae."
                    )
                out[name] = stat
        if self.sync.pieces:
            out["sync"] = self.sync.summary()
        return out


def measure_all(args: argparse.Namespace) -> dict[str, Any]:
    names = (
        [args.only]
        if args.only
        else [
            "wjazzd",
            "filobass",
            "jtd",
            "guitarset",
            "pop909",
            "gmd",
            "dubroom",
            "rwc",
        ]
        + ([] if args.no_lmd else ["lmd"])
    )
    for source in names:
        ensure(source, args.offline)
    if "lmd" in names:
        ensure("msd-genres", args.offline)
        from ..backing.corpus_cache import fetch
        from ..trad.download import Fetcher

        for name, url, _, _, sha in LMD_EXTRAS:
            source = "lmd" if name == "match_scores.json" else "msd-genres"
            dest = ROOT / "corpus" / source / "raw" / name
            if args.offline:
                open_verified(dest, sha)
            else:
                fetch(url, dest, sha, fetcher=Fetcher())
    accs: dict[str, dict[str, Acc]] = defaultdict(lambda: defaultdict(Acc))
    counts: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))

    def ingest(source: str, pieces: Iterable[Piece]) -> None:
        for p in pieces:
            if (
                source in ("dubroom", "lmd", "rwc")
                and p.chords is None
                and p.comp
                and p.bass
            ):
                p.chords = infer_chords(p, p.comp, bass=p.bass)
                p.chords_inferred = bool(p.chords)
            if p.feel is None:
                onsets = (
                    [
                        n.on
                        for n in p.drums
                        if drum_role(n.pitch) in ("hat_closed", "ride", "hat_open")
                    ]
                    if p.drums
                    else [a[0].on for a in attacks(p.comp)]
                    if p.comp
                    else [n.on for n in p.bass]
                )
                p.feel = detect_feel(onsets)[0]
            for st in p.styles:
                proxy = st in PROXIES
                style = PROXIES.get(st, st)
                if style not in STYLE_PROFILE:
                    continue
                group = f"{source}:{st}" if proxy else source
                accs[style][group].add(p)
                counts[source][style] += 1

    for source in names:
        print(f"S1: {source}", flush=True)
        archive = path_of(source)
        if source == "wjazzd":
            ingest(source, wjazzd.pieces(archive))
        elif source == "filobass":
            ingest(source, filobass.pieces(archive))
        elif source == "jtd":
            ingest(source, jtd.pieces(archive))
        elif source == "guitarset":
            ingest(source, guitarset.pieces(archive))
        elif source == "pop909":
            ingest(source, pop909.pieces(archive))
        elif source == "gmd":
            ingest(source, gmd.pieces(archive))
        elif source == "dubroom":
            ingest(source, dubroom.pieces(archive))
        elif source == "rwc":
            ingest(source, rwc.pieces(archive))
        elif source == "lmd":
            r = ROOT / "corpus" / "msd-genres" / "raw"
            best = lmd.load_best(ROOT / "corpus" / "lmd" / "raw" / "match_scores.json")
            labels = lmd.Labels(
                lmd.load_tagtraum(r / "msd_tagtraum_cd2c.cls.zip"),
                lmd.load_masd(r / "msd-MASD-styleAssignment.cls"),
                lmd.load_lastfm(r / "lastfm_tags.db", set(best)),
                best,
            )
            ingest(
                source,
                lmd.pieces(archive, labels, workers=args.workers, limit=args.limit),
            )
        print(f"S1: {source}: {dict(counts[source])}", flush=True)
    if not args.only:
        if "gmd" in names:
            ensure("egmd", args.offline)
            counts["egmd"]["unique_sequences"] = 1059
            counts["egmd"]["note"] = (
                "Chaque identifiant du CSV est déjà dans GMD ; 43 kits ne créent pas 43 indépendances statistiques."
            )
        manifest_sources(
            _checksums(
                set(names)
                | (
                    {"egmd", "msd-genres"}
                    if "lmd" in names
                    else {"egmd"}
                    if "gmd" in names
                    else set()
                )
            ),
            counts,
        )
    output: dict[str, Any] = {}
    for style, profile in STYLE_PROFILE.items():
        sources = {}
        for name, acc in sorted(accs[style].items()):
            s = acc.summary(name.split(":")[0])
            if not s:
                continue
            s["source"] = name.split(":")[0]
            s["proxy"] = name.split(":", 1)[1] if ":" in name else None
            s["license"] = SOURCES[s["source"]]["license"]
            s["archive_sha256"] = SOURCES[s["source"]]["sha256"]
            sources[name] = s
        data = {
            "style": style,
            "profile": profile,
            "sources": sources,
            "version": "S1-020-1",
            "reliability_rule": __import__(
                "harmonium_lab.styles.measure", fromlist=["RELIABILITY_RULE"]
            ).RELIABILITY_RULE,
            "limits": [],
        }
        if not any(
            "bass" in v and v["bass"]["reliability"] == "assez" and not v.get("proxy")
            for v in sources.values()
        ):
            data["limits"].append(
                "basse : aucune source directe assez fiable ; ne pas calibrer un profil sur un proxy"
            )
        if not any(
            "comp" in v and v["comp"]["reliability"] == "assez" and not v.get("proxy")
            for v in sources.values()
        ):
            data["limits"].append(
                "comping : aucune source directe assez fiable ; ne pas calibrer un profil sur un proxy"
            )
        if not any(
            "drums" in v and v["drums"]["reliability"] == "assez" and not v.get("proxy")
            for v in sources.values()
        ):
            data["limits"].append(
                "batterie : aucune source directe assez fiable ; voir GMD L2 et le biais du kit Roland"
            )
        output[style] = data
        write_json(ROOT / "references" / "styles" / f"{style}.json", data)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--only",
        choices=(*SOURCES.keys(),),
        help="mesurer cette source seule (ne régénère pas les manifestes)",
    )
    parser.add_argument("--no-lmd", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="développement seulement : ne pas versionner les résultats",
    )
    args = parser.parse_args()
    if args.limit is not None and args.all:
        parser.error("--limit est incompatible avec --all : résultats incomplets")
    measure_all(args)


if __name__ == "__main__":
    main()
