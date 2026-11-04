"""V2 : distance au corpus des profils, avec les outils des comptes rendus R2 et B.

    python -m harmonium_lab.v2distance trad --engine-dir ~/workspace/harmonium --engine-bin <harmonium-cli> \\
        --corpus-root ~/workspace/harmonium_lab/corpus --work-dir /tmp/h019-v2t1/trad --out references/v2-variance/distance-trad.json
    python -m harmonium_lab.v2distance drums --dist-dir <sorties de scripts/v2_distance_batterie.sh> --b8 <sortie de b8> \\
        --out references/v2-variance/distance-batterie-gmd.json

`trad` : 16 graines × 32 mesures exportées en MIDI par profil, comparées au `profile.json` du type dans `references/`
(`harmonium-lab trad-compare`) ; sortie : écart moyen |z| des écarts signalés (plus petit = plus proche ; bruit de tirage
± 0,07, R2-trad). `drums` : réunit les distances de batterie au Groove MIDI Dataset des profils `gmd_*` et `wjazzd_ballad`
(Bray-Curtis des fréquences d'attaque par pas, scripts de `specs/019-bibliotheque-accompagnements/` du moteur). Corpus et
audio hors dépôt (principe VII). Les profils de jeu ont `make style-distance` (R2-jeux § 4), voir `references/v2-variance/README.md`.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

# profil distribué → (type d'air, corpus sous `corpus/`, profil de référence sous `references/`)
TRAD = {
    "reel_quebecois": ("reel", "trad", "trad-reel"),
    "reel_acadien": ("reel", "acadienne", "trad-acadienne-reel"),
    "reel_britannique_coloniale": ("reel", "britannique_coloniale", "trad-britannique_coloniale-reel"),
    "gigue_quebecoise": ("jig", "trad", "trad-jig"),
    "gigue_acadienne": ("jig", "acadienne", "trad-acadienne-jig"),
    "gigue_britannique_coloniale": ("jig", "britannique_coloniale", "trad-britannique_coloniale-jig"),
    "marche_britannique_coloniale": ("march", "britannique_coloniale", "trad-britannique_coloniale-march"),
    "valse_quebecoise": ("waltz", "trad", "trad-waltz"),
    "valse_britannique_coloniale": ("waltz", "britannique_coloniale", "trad-britannique_coloniale-waltz"),
}


def mean_abs_z(report: Path) -> tuple[float, int]:
    deviations = json.loads(report.read_text(encoding="utf-8"))["deviations"]
    return statistics.mean(abs(d["z"]) for d in deviations), len(deviations)


def export_midis(engine_dir: Path, engine_bin: Path, profile: str, seeds: int, bars: int, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for seed in range(1, seeds + 1):
        out = dest / f"s{seed}.mid"
        if out.is_file():
            continue
        subprocess.run([str(engine_bin), "--export", "--bars", str(bars), "--style", profile, "--seed", str(seed),
                        "--record-midi", str(out)], cwd=engine_dir, capture_output=True, text=True, check=True)


def trad(args: argparse.Namespace) -> int:
    engine_dir, engine_bin = Path(args.engine_dir).expanduser(), Path(args.engine_bin).expanduser()
    corpus_root, work = Path(args.corpus_root).expanduser(), Path(args.work_dir)
    table: dict[str, dict] = {}
    for profile, (kind, corpus, ref) in TRAD.items():
        mids = work / profile
        export_midis(engine_dir, engine_bin, profile, args.seeds, args.bars, mids)
        row: dict = {"reference": ref, "type": kind, "corpus": corpus}
        # `corpus` : celui de la tradition (airs réels et profil de la même source) ; `trad` : le corpus québécois par
        # défaut de `trad-compare`, avec lequel R2-trad a mesuré les profils acadiens et britanniques (chiffres comparables).
        for label, root in (("mean_abs_z", corpus), ("mean_abs_z_corpus_trad", "trad")):
            if label.endswith("trad") and corpus == "trad":
                continue
            out_dir = work / f"out_{profile}_{root}"
            proc = subprocess.run(
                [sys.executable, "-m", "harmonium_lab.cli", "trad-compare", "--generated", str(mids), "--type", kind,
                 "--corpus", str(corpus_root / root), "--profile", str(Path("references") / ref / "profile.json"),
                 "-o", str(out_dir)], capture_output=True, text=True)
            if proc.returncode != 0:
                row["error"] = (proc.stdout + proc.stderr).strip()[-300:]
                break
            z, n = mean_abs_z(out_dir / "report.json")
            row[label], row["deviations"] = round(z, 3), n
        table[profile] = row
        print(f"{profile:34} {row}", file=sys.stderr)
    payload = {"schema": 1, "seeds": args.seeds, "bars": args.bars, "profiles": table}
    Path(args.out).write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


# ── Batterie contre le Groove MIDI Dataset (scripts des comptes rendus B) ─────

# profil → (script du dépôt moteur, sortie de `scripts/v2_distance_batterie.sh`)
DRUMS = {
    **{p: ("b8/distance_gmd.py", "b8") for p in ("gmd_rock", "gmd_pop", "gmd_hiphop", "gmd_soul", "gmd_reggae",
                                                 "gmd_dance_disco", "gmd_afrobeat")},
    "gmd_blues_shuffle": ("b6/distance_gmd.py", "b6"),
    "wjazzd_ballad": ("b25_distance.py", "b25"),
    "gmd_jazz_waltz": ("b25_distance.py", "b25"),
    "gmd_latin_brazilian_bossa": ("b3/gmd_latin_brazilian_bossa_distance.py", "bossa"),
    "gmd_latin_brazilian_samba": ("b3/gmd_latin_brazilian_samba_distance.py", "samba"),
    "gmd_latin_brazilian_baiao": ("b3/gmd_latin_brazilian_baiao_distance.py", "baiao"),
    "gmd_afrocuban": ("b3/gmd_afrocuban_distance.py", "afrocuban"),
}


def drums_row(profile: str, raw: dict) -> dict:
    """Moyenne des quatre métriques (tout, grosse caisse, caisse claire, charleston) : profil, copie sans arc (ou
    témoin), copie non calibrée ; 0 = identique au GMD (Bray-Curtis des fréquences d'attaque par pas)."""
    if profile == "gmd_latin_brazilian_samba":        # un bloc par copie, pas par métrique
        mean = {k: raw[k]["moyenne"] for k in ("profil", "sans_arc_ni_session", "non_calibre")}
        return {"profil": mean["profil"], "sans_arc": mean["sans_arc_ni_session"], "non_calibre": mean["non_calibre"]}
    if profile == "gmd_afrocuban":
        raw = raw["afrocuban + rhumba"]               # les deux styles du GMD, comme le compte rendu B3
    elif profile == "gmd_latin_brazilian_baiao":
        raw = raw["distances"]
    elif DRUMS[profile][1] in ("b8", "b25"):
        raw = raw[profile]
    m = raw["moyenne"]
    row = {"profil": m["profil"]}
    for key in ("sans_arc", "temoin", "non_calibre"):       # copie sans arc / témoin (B2, B5) / copie non calibrée
        if key in m:
            row[key] = m[key]
    return row


def drums(args: argparse.Namespace) -> int:
    dist, b8 = Path(args.dist_dir), Path(args.b8)
    sources = {"b8": json.loads(b8.read_text(encoding="utf-8"))}
    for name in {v[1] for v in DRUMS.values() if v[1] != "b8"}:
        sources[name] = json.loads((dist / f"{name}.json").read_text(encoding="utf-8"))
    table = {}
    for profile, (script, key) in DRUMS.items():
        row = drums_row(profile, sources[key])
        table[profile] = {"script": script, **row}
        print(f"{profile:32} {row}", file=sys.stderr)
    payload = {"schema": 1, "metrique": "Bray-Curtis des fréquences d'attaque par pas, moyenne de any/kick/snare/hat ; 0 = identique au GMD",
               "profiles": table}
    Path(args.out).write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trad", help="profils trad : trad-compare, écart moyen |z|")
    t.add_argument("--engine-dir", required=True)
    t.add_argument("--engine-bin", required=True)
    t.add_argument("--corpus-root", required=True, help="dossier `corpus/` du labo (trad, acadienne, britannique_coloniale)")
    t.add_argument("--work-dir", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--seeds", type=int, default=16)
    t.add_argument("--bars", type=int, default=32)
    t.set_defaults(func=trad)
    d = sub.add_parser("drums", help="réunit les sorties de `scripts/v2_distance_batterie.sh` en un JSON")
    d.add_argument("--dist-dir", required=True, help="dossier des sorties (b6.json, b25.json, bossa.json, …)")
    d.add_argument("--b8", required=True, help="sortie de b8/distance_gmd.py")
    d.add_argument("--out", required=True)
    d.set_defaults(func=drums)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
