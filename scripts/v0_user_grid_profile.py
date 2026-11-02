#!/usr/bin/env python3
"""Copie d'un profil `loop` sous une grille utilisateur de 8 mesures (V0, phase 019).

    python scripts/v0_user_grid_profile.py ~/Project/bascanada/harmonium/profiles/wjazzd_swing \
        /tmp/harmonium-019/v0/wjazzd_swing_grille8

Reproduit ce que fait training : le profil garde ses accompagnements (`[accompaniment]`,
`[instruments]`, `percussion.toml`, `arrangement.toml`…) et sa tonalité verrouillée ; `[form]` et
`[harmony.parts]` sont remplacés par UNE partie de 8 mesures répétée (`sequence = [0]` : un chorus =
une passe de la grille). Grille courte, standard : I6 | VI7 | ii7 | V7 | iii7 | VI7 | ii7 V7 | I6
(relative à la tonique, 4 pas par créneau, 128 pas). Le nombre de chorus se règle à l'export
(`--tours N`). Rien n'est écrit dans le dépôt du moteur.
"""

from __future__ import annotations

import shutil
import sys
import tomllib
from pathlib import Path

FORM = """\
[form]
sequence = [0]
[[form.parts]]
name = "Grille"
melody_center_offset = 0
phrase_ends = [8]
roles = ["Open", "Free", "Free", "Free", "Free", "Free", "Free", "Free"]

"""

HARMONY = """\
[harmony]
model = "loop"
steps_per_chord = 4

[harmony.parts.Grille]
kind = "chord_loop"
loops = [{ weight = 1, chords = [
  { semitones = 0, quality = "6", steps = 16 },
  { semitones = 9, quality = "7", steps = 16 },
  { semitones = 2, quality = "m7", steps = 16 },
  { semitones = 7, quality = "7", steps = 16 },
  { semitones = 4, quality = "m7", steps = 16 },
  { semitones = 9, quality = "7", steps = 16 },
  { semitones = 2, quality = "m7", steps = 8 },
  { semitones = 7, quality = "7", steps = 8 },
  { semitones = 0, quality = "6", steps = 16 },
] }]

"""


def _blocks(text: str) -> list[tuple[str, str]]:
    """Découpe en blocs `(en-tête, texte)` : les commentaires qui précèdent un en-tête lui appartiennent."""
    blocks: list[tuple[str, list[str]]] = [("", [])]
    pending: list[str] = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("#") or (not stripped and pending):
            pending.append(line)
        elif stripped.startswith("["):
            blocks.append((stripped.strip("[]").split(".")[0].split("]")[0], [*pending, line]))
            pending = []
        else:
            blocks[-1][1].extend([*pending, line])
            pending = []
    blocks[-1][1].extend(pending)
    return [(name, "".join(lines)) for name, lines in blocks]


def make_profile(src: Path, dst: Path) -> Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    out, replaced = [], False
    for name, body in _blocks((src / "profile.toml").read_text(encoding="utf-8")):
        if name in ("form", "harmony"):
            if not replaced:
                out.append(FORM + HARMONY)
                replaced = True
            continue
        out.append(body)
    (dst / "profile.toml").write_text("".join(out), encoding="utf-8")
    data = tomllib.loads((dst / "profile.toml").read_text(encoding="utf-8"))
    if [p["name"] for p in data["form"]["parts"]] != ["Grille"] or list(data["harmony"]["parts"]) != ["Grille"]:
        raise RuntimeError("profil réécrit incohérent")
    return dst


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    print(make_profile(Path(argv[1]).expanduser(), Path(argv[2]).expanduser()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
