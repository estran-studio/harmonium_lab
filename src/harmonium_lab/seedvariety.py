"""Variété par graine d'un profil : quelles couches changent d'une graine à l'autre ?

Mesure (phase 018, P1/P2, référence V1). Pour un profil et des graines 1..N, le
moteur écrit la vérité terrain (`harmonium-cli --export --record-truth`) : par
mesure, les accords publiés (`chord_changes`), les notes par piste
(`track` = canal MIDI : 0 Melody, 1 Chords, 2 Bass, 3 PercussionLow,
4 PercussionHigh ; le MIDI exporté regroupe les deux batteries sur le canal 9 GM,
la vérité terrain garde la séparation) et la position (partie, passe, tour). Seul le
premier air du set est lu (un air plus court que `--bars` laisse place à des mesures
vides). Trois couches sont comparées entre graines :

- **accords** : changements d'accord de la mesure (pas, fondamentale, qualité,
  basse), relatifs à la tonique de la mesure ;
- **basse** : notes de la piste 2 (pas, hauteur relative à la tonique, durée) ;
- **batterie** : coups des pistes 3 et 4 (piste, pas, note). Vélocités et
  décalages d'interprétation sont ignorés : l'humanisation dérive de la graine
  même quand le motif est identique, elle gonflerait la mesure.

Unités comparées : la **mesure** (même numéro dans toutes les graines) et la
**partie** (une occurrence de la forme : air, tour, rang dans la séquence ; sa
signature est la suite des signatures de ses mesures). Pour une couche et une
unité, les N graines donnent N signatures ; `distinct` en compte les valeurs :

- `varying` : `distinct > 1` (la couche change d'une graine à l'autre) ;
- `diversity` : `(distinct − 1) / (N − 1)` ; 0 si toutes les graines sont
  identiques, 1 si toutes sont différentes. Avec deux alternatives seulement elle plafonne
  à `1 / (N − 1)` : `distinct_mean` (nombre moyen de signatures distinctes) la complète.

Les parts sont des moyennes sur les unités : `share` (toutes les unités) et
`share_active` (unités où la couche joue dans au moins une graine : une basse
tue sur un pont n'y compte pas comme « stable »). `any` / `all` : part des
unités où au moins une / les trois couches varient.

Avec `--chorus N` (phase 019, V0), la commande mesure la variance **par chorus** (graines × chorus,
couches comping, orchestration, densité, intensité en plus) : voir `chorusvariety.py`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, NamedTuple

from .styledist.engine import resolve_profile

LAYERS = ("chords", "bass", "drums")
LAYER_LABELS = {"chords": "accords", "bass": "basse", "drums": "batterie"}
BASS_TRACK = 2
DRUM_TRACKS = (3, 4)

Signature = tuple


class Bar(NamedTuple):
    """Une mesure de la vérité terrain : unité de partie et signature par couche."""
    index: int
    part: int
    instance: tuple
    sigs: dict[str, Signature]


# ── Lecture de la vérité terrain ──────────────────────────────────────────

def bar_from_entry(entry: dict[str, Any]) -> Bar:
    """Entrée `measures[i]` de `--record-truth` → `Bar` (signatures relatives à la tonique)."""
    measure = entry["measure"]
    pos = measure["position"]
    key = int(pos["key"])
    changes = measure.get("chord_changes")
    if changes:
        chords = tuple(
            (int(c["start_step"]),
             (int(c["context"]["root_pc"]) - key) % 12,
             c["context"].get("quality") or "",
             bool(c["context"]["is_minor"]),
             (int(c["context"]["bass_pc"]) - key) % 12)
            for c in changes)
    else:  # mesure de clôture : pas de liste de changements, seulement l'accord de la mesure
        chords = ((0,
                   (int(measure["chord_root_pc"]) - key) % 12,
                   measure.get("chord_quality") or "",
                   bool(measure["chord_is_minor"]),
                   (int(measure["chord_bass_pc"]) - key) % 12),)
    bass, drums = [], []
    for n in measure["notes"]:
        if n["track"] == BASS_TRACK:
            bass.append((int(n["start_step"]), int(n["pitch"]) - key, int(n["duration_steps"])))
        elif n["track"] in DRUM_TRACKS:
            drums.append((int(n["track"]), int(n["start_step"]), int(n["pitch"])))
    return Bar(
        index=int(entry["bar"]),
        part=int(pos["part"]),
        instance=(int(pos["tune_index"]), int(pos["tour"]), int(pos["sequence_index"])),
        sigs={"chords": chords, "bass": tuple(sorted(bass)), "drums": tuple(sorted(drums))},
    )


def load_truth(path: Path, max_bars: int | None = None) -> list[Bar]:
    """Mesures du premier air d'un fichier `--record-truth` (les `max_bars` premières si borné) :
    après la fin d'un air plus court que `--bars`, le set suit sur des mesures vides."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [bar_from_entry(e) for e in data["measures"]
            if (max_bars is None or e["bar"] <= max_bars) and e["measure"]["position"]["tune_index"] == 0]


# ── Métrique ──────────────────────────────────────────────────────────────

class Unit(NamedTuple):
    """Une unité comparée (mesure ou partie) : varie, diversité, active, signatures distinctes."""
    varying: bool
    diversity: float
    active: bool
    distinct: int


def _unit_stats(sig_lists: list[list[Signature]]) -> list[tuple[bool, float, bool]]:
    """Par unité : (varie, diversité, active) pour la liste des signatures par graine."""
    out = []
    for sigs in sig_lists:
        n = len(sigs)
        distinct = len(set(sigs))
        active = any(s for s in sigs)
        out.append(Unit(distinct > 1, (distinct - 1) / (n - 1), active, distinct))
    return out


def _summary(stats: list[tuple[bool, float, bool]]) -> dict[str, Any]:
    total = len(stats)
    active = [s for s in stats if s[2]]
    varying = sum(1 for s in stats if s[0])
    return {
        "units": total,
        "active_units": len(active),
        "share": round(varying / total, 4) if total else 0.0,
        "share_active": round(sum(1 for s in active if s[0]) / len(active), 4) if active else 0.0,
        "diversity": round(sum(s[1] for s in stats) / total, 4) if total else 0.0,
        "distinct_mean": round(sum(s[3] for s in stats) / total, 3) if total else 0.0,
    }


def _part_signature(bars: list[Bar], layer: str | None) -> Signature:
    """Signature d'une partie : suite des signatures de ses mesures (`None` = les trois couches)."""
    if layer is None:
        return tuple(tuple(b.sigs[ly] for ly in LAYERS) for b in bars)
    return tuple(b.sigs[layer] for b in bars)


def seed_variety(runs: dict[int, list[Bar]], part_names: list[str] | None = None) -> dict[str, Any]:
    """Variété entre graines. `runs` : graine → mesures. Seules les mesures présentes
    dans toutes les graines sont comparées ; la structure en parties est lue sur la
    première graine."""
    if len(runs) < 2:
        raise ValueError("variété par graine : au moins deux graines requises")
    seeds = sorted(runs)
    by_bar = {s: {b.index: b for b in runs[s]} for s in seeds}
    common = sorted(set.intersection(*(set(m) for m in by_bar.values())))
    if not common:
        raise ValueError("variété par graine : aucune mesure commune aux graines")
    ref = by_bar[seeds[0]]

    # Parties : mesures communes regroupées par occurrence dans la graine de référence.
    instances: dict[tuple, list[int]] = {}
    for i in common:
        instances.setdefault(ref[i].instance, []).append(i)

    def names(part: int) -> str:
        return part_names[part] if part_names and part < len(part_names) else f"part{part}"

    result: dict[str, Any] = {"seeds": seeds, "bars_compared": len(common),
                              "part_occurrences": len(instances), "layers": {}}
    per_layer_bar: dict[str, list[tuple[bool, float, bool]]] = {}
    per_layer_part: dict[str, list[tuple[bool, float, bool]]] = {}
    for layer in (*LAYERS, None):
        label = layer or "any_signature"
        bar_stats = _unit_stats([[by_bar[s][i].sigs[layer] if layer else
                                  tuple(by_bar[s][i].sigs[ly] for ly in LAYERS)
                                  for s in seeds] for i in common])
        part_stats = _unit_stats([[_part_signature([by_bar[s][i] for i in idx], layer) for s in seeds]
                                  for idx in instances.values()])
        per_layer_bar[label], per_layer_part[label] = bar_stats, part_stats
        if layer is None:
            continue
        by_part_name: dict[str, list[tuple[bool, float, bool]]] = {}
        for idx, st in zip(instances.values(), part_stats):
            by_part_name.setdefault(names(ref[idx[0]].part), []).append(st)
        bar_by_name: dict[str, list[tuple[bool, float, bool]]] = {}
        for i, st in zip(common, bar_stats):
            bar_by_name.setdefault(names(ref[i].part), []).append(st)
        result["layers"][layer] = {
            "bars": _summary(bar_stats),
            "parts": _summary(part_stats),
            "by_part": {n: {"bars": _summary(bar_by_name[n]), "occurrences": _summary(by_part_name[n])}
                        for n in bar_by_name},
        }

    # Combinaisons de couches, mesure par mesure et partie par partie.
    def combo(per_layer: dict[str, list[tuple[bool, float, bool]]], mode: str) -> dict[str, Any]:
        cols = [per_layer[ly] for ly in LAYERS]
        flags = [(any(c[k][0] for c in cols) if mode == "any" else all(c[k][0] for c in cols))
                 for k in range(len(cols[0]))]
        total = len(flags)
        return {"units": total, "share": round(sum(flags) / total, 4) if total else 0.0}

    result["combined"] = {
        "any": {"bars": combo(per_layer_bar, "any"), "parts": combo(per_layer_part, "any")},
        "all": {"bars": combo(per_layer_bar, "all"), "parts": combo(per_layer_part, "all")},
    }
    result["distinct_runs"] = {
        ly: len({tuple(by_bar[s][i].sigs[ly] for i in common) for s in seeds}) for ly in LAYERS}
    return result


# ── Rendu moteur ──────────────────────────────────────────────────────────

def part_names_of(profile_dir: Path) -> list[str]:
    data = tomllib.loads((profile_dir / "profile.toml").read_text(encoding="utf-8"))
    return [p["name"] for p in data.get("form", {}).get("parts", [])]


def export_truth(engine_dir: Path, engine_bin: Path | None, profile_dir: Path, seed: int, bars: int,
                 out: Path, force: bool = False, tours: int | None = None, midi: Path | None = None) -> Path:
    """Vérité terrain d'une graine (réutilisée si présente) via `harmonium-cli --export --record-truth`.
    `tours` : `--tours N` (chorus de la phase 019) ; `midi` : écrit aussi `--record-midi` (programmes par piste)."""
    if out.is_file() and not force and (midi is None or midi.is_file()):
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    tail = ["--export", "--bars", str(bars), "--profile", str(profile_dir), "--seed", str(seed),
            "--record-truth", str(out)]
    if tours is not None:
        tail += ["--tours", str(tours)]
    if midi is not None:
        tail += ["--record-midi", str(midi)]
    cmd = ([str(engine_bin)] + tail if engine_bin else
           ["cargo", "run", "-q", "-p", "harmonium-cli", "--release",
            "--manifest-path", str(engine_dir / "Cargo.toml"), "--"] + tail)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=engine_dir)   # `assets/` du moteur
    if proc.returncode != 0 or not out.is_file():
        raise RuntimeError(f"export moteur en échec (graine {seed}) :\n{' '.join(cmd)}\n"
                           f"{proc.stdout[-600:]}{proc.stderr[-1200:]}")
    return out


def measure_profile(engine_dir: Path, engine_bin: Path | None, profile: str, seeds: list[int], bars: int,
                    work_dir: Path, force: bool = False, tag: str | None = None) -> dict[str, Any]:
    profile_dir = resolve_profile(engine_dir, profile)
    label = tag or profile_dir.name
    runs: dict[int, list[Bar]] = {}
    for seed in seeds:
        truth = export_truth(engine_dir, engine_bin, profile_dir, seed, bars,
                             work_dir / f"{label}_b{bars}_s{seed}.truth.json", force)
        runs[seed] = load_truth(truth, bars)
    result = seed_variety(runs, part_names_of(profile_dir))
    result["profile"] = profile_dir.name
    result["bars"] = bars
    return result


# ── Sortie ────────────────────────────────────────────────────────────────

def _pct(x: float) -> str:
    return f"{100 * x:.0f} %"


def markdown(results: list[dict[str, Any]]) -> str:
    lines = ["| Profil | Couche | Mesures qui varient | Parties qui varient | Signatures distinctes / mesure | Signatures distinctes / partie |",
             "|---|---|---:|---:|---:|---:|"]
    for r in results:
        name = r.get("label", r["profile"])
        for layer in LAYERS:
            ly = r["layers"][layer]
            lines.append(f"| `{name}` | {LAYER_LABELS[layer]} | {_pct(ly['bars']['share'])} "
                         f"({_pct(ly['bars']['share_active'])} actives) | {_pct(ly['parts']['share'])} "
                         f"({_pct(ly['parts']['share_active'])} actives) | {ly['bars']['distinct_mean']:.2f} | "
                         f"{ly['parts']['distinct_mean']:.2f} |")
        c = r["combined"]
        lines.append(f"| `{name}` | une couche au moins | {_pct(c['any']['bars']['share'])} | "
                     f"{_pct(c['any']['parts']['share'])} | | |")
        lines.append(f"| `{name}` | les trois | {_pct(c['all']['bars']['share'])} | "
                     f"{_pct(c['all']['parts']['share'])} | | |")
    return "\n".join(lines)


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="seed-variety", description=__doc__.splitlines()[0], add_help=add_help)
    p.add_argument("--profile", action="append", required=True,
                   help="Id d'un profil de <moteur>/profiles/ ou dossier de profil (répétable)")
    p.add_argument("--seeds", type=int, default=16, help="Graines 1..N (défaut : 16)")
    p.add_argument("--bars", type=int, default=64, help="Mesures par graine (défaut : 64 ; ignoré avec --chorus)")
    p.add_argument("--chorus", type=int, default=None, metavar="N",
                   help="Variance par chorus (phase 019, V0) : N chorus par graine (`--tours N` du moteur), "
                        "mesures calculées par une sonde d'un tour ; couches accords, comping, basse, batterie, "
                        "mélodie, orchestration, densité, intensité")
    p.add_argument("--steady-from", type=int, default=3,
                   help="Avec --chorus : rang du chorus à partir duquel les entrées de couches par tour sont passées (défaut : 3)")
    p.add_argument("--engine-dir", default="../harmonium", help="Dépôt du moteur (Cargo.toml)")
    p.add_argument("--engine-bin", default=None, help="Binaire harmonium-cli déjà compilé (évite cargo run)")
    p.add_argument("--work-dir", default="target/seed_variety", help="Vérités terrain (cache, hors dépôt)")
    p.add_argument("--force", action="store_true", help="Refait les exports moteur")
    p.add_argument("--label", default=None, help="Étiquette de la mesure (ex. V1, P2) ; sépare les caches")
    p.add_argument("--output", "-o", default=None, help="Fichier JSON de sortie")
    p.add_argument("--markdown", action="store_true", help="Affiche le tableau")
    return p


def run(args: argparse.Namespace) -> int:
    if args.chorus:
        from . import chorusvariety
        return chorusvariety.run(args)
    engine_dir = Path(args.engine_dir).expanduser().resolve()
    engine_bin = Path(args.engine_bin).expanduser().resolve() if args.engine_bin else None
    seeds = list(range(1, args.seeds + 1))
    results = []
    for profile in args.profile:
        print(f"[seed-variety] {profile} : {len(seeds)} graines × {args.bars} mesures", file=sys.stderr)
        tag = f"{args.label}_{Path(profile).name}" if args.label else None
        r = measure_profile(engine_dir, engine_bin, profile, seeds, args.bars,
                            Path(args.work_dir), args.force, tag)
        if args.label:
            r["label"] = f"{r['profile']}"
            r["measure"] = args.label
        results.append(r)
    payload = {"schema": 1, "seeds": seeds, "bars": args.bars, "profiles": results}
    if args.output:
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Variété publiée → {dest}", file=sys.stderr)
    if args.markdown or not args.output:
        print(markdown(results))
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
