#!/usr/bin/env python3
"""Valide un TOML CellBank contre les règles de `harmonium_core::trad::cells`.

Réplique Python auditée de `Cell::validate` + `CellBank::from_toml`
(nombre, première note, degrés, ambitus ionien, sauts > quinte).
Usage : `python3 scripts/check_cells.py target/mined/reel_cells.toml`.

NOTE (DS-T5) : le moteur n'offre aucun point d'entrée Rust qui parse un
fichier CellBank arbitraire (`CellBank::from_toml` prend une chaîne et
n'est appelé que sur la banque embarquée / l'overlay TuningParams).
Cette validation Python est donc le seul garde-fou croisé disponible ;
le coordinateur ajoutera un test Rust chargeant un fichier au moteur.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from harmonium_lab.trad.mine import ROLES, validate_cell  # noqa: E402

_CELL = re.compile(r'\{\s*role\s*=\s*"([^"]+)"\s*,\s*notes\s*=\s*"([^"]+)"\s*\}')


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <cellbank.toml>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    text = path.read_text(encoding="utf-8")
    cells = _CELL.findall(text)
    if not cells:
        print(f"{path}: aucune cellule trouvée")
        return 1
    errors = 0
    for i, (role, notes) in enumerate(cells):
        if role not in ROLES:
            print(f"cellule {i}: rôle inconnu {role!r}")
            errors += 1
            continue
        reason = validate_cell(notes, expected=8)
        if reason is not None:
            print(f"cellule {i} ({role} {notes!r}): {reason}")
            errors += 1
    print(f"{path}: {len(cells)} cellules, {errors} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
