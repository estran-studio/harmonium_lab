"""CLI : `python -m harmonium_lab.styledist --profile P --tracks ID[,ID] ... -o distance-P.json`.

Rend N graines × M mesures du profil (moteur frère), mesure la distance audio
aux pistes de référence et la distance symbolique à leurs transcriptions, écrit
un JSON versionnable (aucun audio, stem ni MIDI transcrit) et, avec
`--markdown`, les tableaux du compte rendu.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from harmonium_lab.audioref.manifest import load_manifest, parse_filters, select, track_path

from . import audio as aud
from . import symbolic as sym
from .engine import parse_bank, render_seeds, resolve_profile


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="styledist", description=__doc__.splitlines()[0])
    p.add_argument("--profile", required=True, help="Id d'un profil de <moteur>/profiles/ ou dossier de profil")
    p.add_argument("--tracks", required=True, help="Ids des pistes de référence (manifeste), séparés par des virgules")
    p.add_argument("--manifest", required=True, help="Manifeste JSONL du corpus")
    p.add_argument("--corpus-root", required=True, help="Dossier des fichiers audio (champ `file` relatif)")
    p.add_argument("--context", nargs="*", default=[], metavar="CHAMP=VALEUR",
                   help="Filtres du corpus de contexte pour les échelles (≥ 3 pistes avec les références)")
    p.add_argument("--transcriptions", default=None, help="Dossier des boucles transcrites (JSON) ; sans lui, pas de symbolique")
    p.add_argument("--grids", default=None, help="JSON des grilles {id: grille} (pas par mesure des transcriptions)")
    p.add_argument("--steps-per-bar", type=int, default=None, help="Pas par mesure si absent de --grids")
    p.add_argument("--engine-dir", default="../harmonium", help="Dépôt du moteur (Cargo.toml)")
    p.add_argument("--bank", action="append", required=True, metavar="LABEL=SF2[,PIEDS.SF2]",
                   help="Banque de rendu (répétable) ; banque des pieds = banque principale par défaut")
    p.add_argument("--seeds", type=int, default=10, help="Graines 1..N")
    p.add_argument("--bars", type=int, default=48, help="Mesures par rendu")
    p.add_argument("--work-dir", default="target/style_distance", help="Rendus et cache (hors dépôt)")
    p.add_argument("--force", action="store_true", help="Refait les rendus moteur")
    p.add_argument("--output", "-o", required=True, help="distance-<profil>.json")
    p.add_argument("--markdown", action="store_true", help="Affiche les tableaux du compte rendu")
    return p


def _git_rev(path: Path) -> str | None:
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def _spread(feats: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    out = {}
    for m in aud.SCALAR_METRICS:
        vals = [f["scalars"][m] for f in feats]
        out[m] = {"mean": round(float(np.mean(vals)), 3), "std": round(float(np.std(vals)), 3)}
    return out


def run(args: argparse.Namespace) -> dict[str, Any]:
    engine_dir = Path(args.engine_dir).resolve()
    work = Path(args.work_dir)
    profile_dir = resolve_profile(engine_dir, args.profile)
    banks = [parse_bank(b) for b in args.bank]
    seeds = list(range(1, args.seeds + 1))
    track_ids = [t for t in args.tracks.split(",") if t]

    rows = load_manifest(Path(args.manifest))
    by_id = {r["id"]: r for r in rows}
    missing = [t for t in track_ids if t not in by_id]
    if missing:
        raise SystemExit(f"pistes absentes du manifeste : {', '.join(missing)}")
    context_rows = select(rows, parse_filters(args.context)) if args.context else []
    ctx_ids = sorted({r["id"] for r in context_rows} | set(track_ids))
    root = Path(args.corpus_root)
    cache = work / "cache"

    print(f"[1/4] rendu moteur : {profile_dir.name}, {len(seeds)} graines × {args.bars} mesures × {len(banks)} banque(s)")
    renders = render_seeds(engine_dir, profile_dir, banks, seeds, args.bars, work / "renders", args.force)

    print(f"[2/4] mesures de {len(ctx_ids)} pistes (références + contexte)")
    grids = json.loads(Path(args.grids).read_text(encoding="utf-8")) if args.grids else {}
    ref_feats = {t: aud.features_for_file(track_path(by_id[t], root), cache) for t in ctx_ids}
    for t, grid in grids.items():  # pulsation G0 vérifiée plutôt que beat_track brut
        if t in ref_feats and grid.get("bpm"):
            ref_feats[t]["scalars"]["tempo_log2"] = round(float(np.log2(grid["bpm"])), 5)
    scales = aud.compute_scales([ref_feats[t] for t in ctx_ids])

    print("[3/4] distance audio")
    audio_out: dict[str, Any] = {}
    for bank in banks:
        gen = [aud.features_for_file(renders[bank.label][s][0], cache) for s in seeds]
        for g, _seed in zip(gen, seeds):  # pulsation du MIDI, vérité terrain
            g["scalars"]["tempo_log2"] = round(aud.midi_pulse_log2(renders[bank.label][_seed][1]), 5)
        refs_out = {}
        for t in track_ids:
            summary = aud.summarize([aud.compare(g, ref_feats[t], scales) for g in gen])
            summary["tonal"] = {"reference": ref_feats[t]["tonal"],
                                "generated_tonic_counts": _count(g["tonal"]["estimated_key"] for g in gen)}
            refs_out[t] = summary
        audio_out[bank.label] = {"soundfont": bank.soundfont.name, "percussion_soundfont": bank.percussion_soundfont.name,
                                 "generated": _spread(gen), "references": refs_out}

    symbolic_out: dict[str, Any] = {}
    if args.transcriptions:
        print("[4/4] distance symbolique")
        midis = [renders[banks[0].label][s][1] for s in seeds]
        for t in track_ids:
            files = sym.load_transcriptions(Path(args.transcriptions), t)
            if not files:
                symbolic_out[t] = {"error": "aucune transcription"}
                continue
            steps = sym.steps_per_bar(grids[t]) if t in grids else args.steps_per_bar
            if not steps:
                raise SystemExit(f"pas par mesure inconnu pour {t} : grille absente de --grids et pas de --steps-per-bar")
            ref, loops = sym.reference_voices(files, steps)
            per_seed = [sym.generated_metrics(sym.read_midi(m, steps), ref, loops) for m in midis]
            summary = sym.summarize([p["d"] for p in per_seed])
            summary["steps_per_bar"] = steps
            summary["transcriptions"] = [f["_file"] for f in files]
            summary["reference_values"] = sym.reference_values(ref, loops)
            summary["generated_values"] = per_seed[0]["values"]
            summary["generated_values_seed"] = seeds[0]
            symbolic_out[t] = summary
    else:
        print("[4/4] symbolique ignoré (pas de --transcriptions)")

    return {
        "schema": 1,
        "profile": profile_dir.name,
        "engine": {"rev": _git_rev(engine_dir), "export": "harmonium-cli --export --profile"},
        "settings": {"seeds": seeds, "bars": args.bars, "tracks": track_ids,
                     "context_filters": args.context, "context_tracks": ctx_ids,
                     "banks": {b.label: b.soundfont.name for b in banks}},
        "audio": {"scales": scales, "reference_features": {t: ref_feats[t]["scalars"] for t in track_ids},
                  "banks": audio_out},
        "symbolic": symbolic_out,
    }


def _count(items) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return dict(sorted(out.items()))


def markdown(result: dict[str, Any]) -> str:
    lines: list[str] = []
    for label, bank in result["audio"]["banks"].items():
        lines.append(f"\n**Audio — banque `{label}`** (score 0–100, moyenne sur {len(result['settings']['seeds'])} graines)\n")
        refs = list(bank["references"])
        lines.append("| Groupe / mesure | " + " | ".join(f"vs `{r}`" for r in refs) + " |")
        lines.append("|---|" + "---:|" * len(refs))
        lines.append("| **Score global** | " + " | ".join(f"**{bank['references'][r]['score']}**" for r in refs) + " |")
        for g, ms in aud.GROUPS.items():
            lines.append(f"| *{g}* | " + " | ".join(f"*{bank['references'][r]['groups'][g]}*" for r in refs) + " |")
            for m in ms:
                lines.append(f"| · `{m}` | " + " | ".join(
                    f"{bank['references'][r]['scores'][m]} (z={bank['references'][r]['z_mean'][m]})" for r in refs) + " |")
    for t, s in result["symbolic"].items():
        if "error" in s:
            continue
        lines.append(f"\n**Symbolique — vs `{t}`** (score 0–100, 100 = identique)\n")
        lines.append("| Groupe / mesure | Score | Distance |")
        lines.append("|---|---:|---:|")
        lines.append(f"| **Score global** | **{s['score']}** | |")
        for g, keys in sym.GROUPS.items():
            lines.append(f"| *{g}* | *{s['groups'][g]}* | |")
            for k in keys:
                lines.append(f"| · `{k}` | {s['scores'][k]} | {s['distance'][k]} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Distance publiée → {dest}")
    if args.markdown:
        print(markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
