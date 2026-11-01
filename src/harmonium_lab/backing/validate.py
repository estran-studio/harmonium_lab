"""Validation d'un profil d'accompagnement : vérité terrain du moteur → distance à WJazzD.

Rend N graines de chaque profil par le CLI du moteur (`--record-truth`, réutilisée si présente),
puis appelle `bass_compare` : mêmes mesures de basse sur le généré et sur la base, distance par
critère et agrégée, plusieurs profils dans un même rapport (le profil calibré et une ligne de
base non calibrée, par exemple).

    python -m harmonium_lab.backing.validate --engine-dir ../harmonium \\
        --profile wjazzd_swing=../harmonium/profiles/wjazzd_swing \\
        --profile grille_accompagnee=../harmonium/tests/fixtures/profiles/grille_accompagnee \\
        --seeds 8 --bars 56 --group all --group blues -o references/wjazzd-swing/validation-bass.json --markdown
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..seedvariety import export_truth
from . import bass_compare


def _label_dir(spec: str) -> tuple[str, Path]:
    label, sep, path = spec.partition("=")
    if not sep or not label or not path:
        raise argparse.ArgumentTypeError(f"profil invalide « {spec} » : attendu étiquette=dossier")
    return label, Path(path).expanduser().resolve()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--engine-dir", type=Path, default=Path("../harmonium"))
    ap.add_argument("--engine-bin", type=Path, help="binaire harmonium-cli déjà compilé")
    ap.add_argument("--profile", action="append", type=_label_dir, required=True,
                    help="étiquette=dossier du profil (répétable)")
    ap.add_argument("--seeds", type=int, default=8, help="nombre de graines")
    ap.add_argument("--seed-start", type=int, default=1, help="première graine (contrôle sur des graines non vues : 11)")
    ap.add_argument("--bars", type=int, default=56)
    ap.add_argument("--work-dir", type=Path, default=Path("target/backing_truth"))
    ap.add_argument("--reference", type=Path, default=bass_compare.REFERENCE)
    ap.add_argument("--group", action="append", help="groupe(s) de référence (défaut : all)")
    ap.add_argument("-o", "--output", type=Path, default=bass_compare.DEFAULT_OUTPUT)
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--force", action="store_true", help="re-rend les vérités terrain présentes")
    args = ap.parse_args(argv)
    engine_dir = args.engine_dir.expanduser().resolve()
    engine_bin = args.engine_bin.expanduser().resolve() if args.engine_bin else None
    compare: list[str] = []
    for label, profile_dir in args.profile:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            truth = export_truth(engine_dir, engine_bin, profile_dir, seed, args.bars,
                                 args.work_dir / f"{label}_b{args.bars}_s{seed}.json", args.force)
            compare += ["--truth", str(truth)]
        compare += ["--label", label]
    compare += ["--reference", str(args.reference), "-o", str(args.output)]
    for group in args.group or ["all"]:
        compare += ["--group", group]
    if args.markdown:
        compare.append("--markdown")
    return bass_compare.main(compare)


if __name__ == "__main__":
    sys.exit(main())
