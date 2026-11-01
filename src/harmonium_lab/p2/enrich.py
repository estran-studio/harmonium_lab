"""Copie d'un profil moteur enrichie des alternatives proposées par `p2.extract` (preuve P2).

La copie est écrite hors dépôt (`/tmp`) : le profil distribué n'est jamais modifié. Les
propositions (`harmony.parts.*.loops`, `accompaniment.bass.motifs`, `percussion.patterns`)
s'ajoutent aux alternatives écrites ; `[[provenance]]` et `[[gaps]]` sont écartés.

Poids : les poids de la proposition sont des effectifs (fréquence dans la transcription). Par
défaut ils sont **rééquilibrés** pour qu'une alternative extraite pèse comme une écrite : par
partie (boucles, motifs de basse) ou par densité (patterns), le poids total des ajouts est
ramené au poids total des alternatives écrites (arrondi, minimum 1), proportions des effectifs
conservées. `--raw-weights` garde les effectifs tels quels.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

from harmonium_lab.styledist.engine import resolve_profile

from . import emit


def balance(new_weights: list[int], existing_total: int) -> list[int]:
    """Poids des ajouts ramenés au poids total des alternatives écrites (minimum 1 chacun)."""
    total = sum(new_weights)
    if total <= 0 or existing_total <= 0:
        return [max(1, w) for w in new_weights]
    return [max(1, round(w / total * existing_total)) for w in new_weights]


def _replace_section(text: str, header: str, replacement: str) -> str:
    """Remplace la table `header` (de sa ligne `[..]` à la prochaine table en colonne 0)."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, ln in enumerate(lines) if ln.strip() == header), None)
    if start is None:
        raise ValueError(f"section {header} introuvable")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    return "".join(lines[:start]) + replacement + ("\n" if end < len(lines) else "") + "".join(lines[end:])


def enrich(profile_dir: Path, proposal: Path, out_dir: Path, raw_weights: bool = False) -> dict[str, int]:
    """Écrit la copie enrichie dans `out_dir` ; retourne les comptes d'ajouts par couche."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(profile_dir, out_dir)
    prop = tomllib.loads(proposal.read_text(encoding="utf-8"))
    profile_path = out_dir / "profile.toml"
    text = profile_path.read_text(encoding="utf-8")
    base = tomllib.loads(text)
    files = base.get("files", {})
    counts = {"loops": 0, "motifs": 0, "patterns": 0}

    # Boucles : section de la partie réécrite (écrites puis extraites).
    for part, section in prop.get("harmony", {}).get("parts", {}).items():
        written = base["harmony"]["parts"][part]
        if written.get("kind") != "chord_loop":
            raise ValueError(f"partie {part} : `chord_loop` requis pour porter des alternatives")
        existing = [{"weight": lp.get("weight", 1), "chords": lp["chords"]} for lp in written["loops"]]
        new = list(section["loops"])
        if not raw_weights:
            for lp, w in zip(new, balance([lp["weight"] for lp in new], sum(lp["weight"] for lp in existing))):
                lp["weight"] = w
        block = "# P2 : alternatives écrites puis extraites (copie temporaire).\n" + emit.part_block(part, existing + new)
        text = _replace_section(text, f"[harmony.parts.{part}]", block)
        counts["loops"] += len(new)

    # Motifs de basse : ajoutés en fin de profile.toml.
    motifs = prop.get("accompaniment", {}).get("bass", {}).get("motifs", [])
    if motifs:
        by_part: dict[str, list[dict[str, Any]]] = {}
        for m in motifs:
            by_part.setdefault(m["part"], []).append(dict(m))
        appended = ["\n# P2 : motifs de basse extraits (copie temporaire).\n"]
        for part, items in by_part.items():
            if not raw_weights:
                written = sum(int(m.get("weight", 1)) for m in base["accompaniment"]["bass"]["motifs"]
                              if m.get("part") == part)
                for m, w in zip(items, balance([m["weight"] for m in items], written)):
                    m["weight"] = w
            appended += [emit.motif_block(m) + "\n" for m in items]
        text = text.rstrip("\n") + "\n" + "".join(appended)
        counts["motifs"] = len(motifs)
    profile_path.write_text(text, encoding="utf-8")

    # Patterns de batterie : ajoutés à percussion.toml (`[[patterns]]` de premier niveau).
    patterns = prop.get("percussion", {}).get("patterns", [])
    if patterns:
        perc_path = out_dir / files["percussion"]
        perc = tomllib.loads(perc_path.read_text(encoding="utf-8"))
        by_density: dict[int, list[dict[str, Any]]] = {}
        for p in patterns:
            by_density.setdefault(int(p["density"]), []).append(dict(p))
        appended = ["\n# P2 : patterns extraits (copie temporaire).\n"]
        for density, items in by_density.items():
            if not raw_weights:
                written = sum(int(p.get("weight", 1)) for p in perc["patterns"] if p["density"] == density and "hits" in p)
                for p, w in zip(items, balance([p["weight"] for p in items], written)):
                    p["weight"] = w
            appended += [emit.pattern_block(p, table="patterns") + "\n" for p in items]
        perc_path.write_text(perc_path.read_text(encoding="utf-8").rstrip("\n") + "\n" + "".join(appended),
                             encoding="utf-8")
        counts["patterns"] = len(patterns)

    tomllib.loads(profile_path.read_text(encoding="utf-8"))  # la copie reste du TOML valide
    return counts


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="p2-enrich", description=__doc__.splitlines()[0], add_help=add_help)
    p.add_argument("--profile", required=True, help="Id d'un profil de <moteur>/profiles/ ou dossier de profil")
    p.add_argument("--proposal", required=True, help="TOML de proposition (p2-extract)")
    p.add_argument("--out", required=True, help="Dossier de la copie enrichie (hors dépôt, ex. /tmp/...)")
    p.add_argument("--engine-dir", default="../harmonium", help="Dépôt du moteur (profils)")
    p.add_argument("--raw-weights", action="store_true", help="Garde les effectifs comme poids (pas de rééquilibrage)")
    return p


def run(args: argparse.Namespace) -> int:
    src = resolve_profile(Path(args.engine_dir).expanduser().resolve(), args.profile)
    counts = enrich(src, Path(args.proposal), Path(args.out), args.raw_weights)
    print(f"{src.name} → {args.out} : {counts['loops']} boucles, {counts['motifs']} motifs de basse, "
          f"{counts['patterns']} patterns ajoutés")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
