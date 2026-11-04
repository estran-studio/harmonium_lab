"""Copie d'un profil `loop` sous une grille utilisateur de 8 mesures (phase 019, V2).

Reproduit ce que fait training : le profil distribué garde ses accompagnements (`[accompaniment]`,
`[instruments]`, `[session]`, `[arc]`, `percussion.toml`…) ; `[form]` et `[harmony]` sont remplacés par UNE
partie de 8 mesures répétée (`sequence = [0]` : un chorus = une passe de la grille) et la tonalité est
verrouillée par `[fixed_tonality]` (celle de la grille de l'hôte ; celle du profil si elle existe). Généralise
`scripts/v0_user_grid_profile.py` (V0, profil `wjazzd_swing` seul, 16 pas par mesure) à tout profil `loop` :
nombre de pas par mesure (12 pour les valses et les shuffles, 24 en 12/8), `steps_per_chord` du profil.

Grille standard, relative à la tonique : I6 | VI7 | ii7 | V7 | iii7 | VI7 | ii7 V7 | I6. Les durées d'accord
sont des multiples de `harmony.steps_per_chord` (règle du chargeur) : une mesure partagée en deux accords tombe sur
deux moitiés si la moitié est un multiple, sinon sur le plus petit créneau suivi du reste ; si la mesure n'a pas
deux créneaux (`steps_per_chord` = mesure), ii7 V7 devient un seul V7 (`GridReport.merged_bars`).
"""

from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

BARS = 8
# (demi-tons au-dessus de la tonique, qualité, fraction de mesure) : une entrée = un accord.
GRID: list[list[tuple[int, str]]] = [
    [(0, "6")], [(9, "7")], [(2, "m7")], [(7, "7")], [(4, "m7")], [(9, "7")], [(2, "m7"), (7, "7")], [(0, "6")],
]
FIXED_KEY, FIXED_MODE = 5, "ionian"   # fa ionien : la tonalité de l'hôte (n'importe laquelle, la grille est relative)


@dataclass
class GridReport:
    profile: str
    bars: int
    steps_per_bar: int
    steps_per_chord: int
    fixed_tonality: dict
    tonality_from_profile: bool
    merged_bars: int = 0
    notes: list[str] = field(default_factory=list)


def split_bar(steps_per_bar: int, steps_per_chord: int, n: int) -> list[int] | None:
    """Durées (en pas, multiples de `steps_per_chord`) de `n` accords dans une mesure, ou None si impossible."""
    if n == 1:
        return [steps_per_bar]
    half = steps_per_bar // 2
    if steps_per_bar % 2 == 0 and half % steps_per_chord == 0:
        return [half, half]
    if steps_per_bar % steps_per_chord == 0 and steps_per_bar >= 2 * steps_per_chord:
        return [steps_per_chord, steps_per_bar - steps_per_chord]
    return None


def _blocks(text: str) -> list[tuple[str, str]]:
    """Découpe en blocs `(table de tête, texte)` : les commentaires qui précèdent un en-tête lui appartiennent."""
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


def _form_and_harmony(spb: int, spc: int, bars: int, report: GridReport) -> str:
    chords = []
    for bar in GRID * (bars // BARS):
        durations = split_bar(spb, spc, len(bar))
        if durations is None:
            bar, durations = bar[-1:], [spb]
            report.merged_bars += 1
        chords += [f'  {{ semitones = {s}, quality = "{q}", steps = {d} }},' for (s, q), d in zip(bar, durations)]
    roles = ", ".join(['"Open"'] + ['"Free"'] * (bars - 1))
    return (
        "[form]\nsequence = [0]\n[[form.parts]]\nname = \"Grille\"\nmelody_center_offset = 0\n"
        f"phrase_ends = [{bars}]\nroles = [{roles}]\n\n"
        f"[harmony]\nmodel = \"loop\"\nsteps_per_chord = {spc}\n\n"
        "[harmony.parts.Grille]\nkind = \"chord_loop\"\nloops = [{ weight = 1, chords = [\n"
        + "\n".join(chords) + "\n] }]\n\n")


def is_loop(src: Path) -> bool:
    return tomllib.loads((src / "profile.toml").read_text(encoding="utf-8")).get("harmony", {}).get("model") == "loop"


def make_profile(src: Path, dst: Path, bars: int = BARS) -> GridReport:
    """Copie `src` (profil `loop`) dans `dst` sous la grille de `bars` mesures (multiple de 8 : la grille standard
    répétée) ; lève `ValueError` si `src` n'est pas `loop`."""
    if bars % BARS:
        raise ValueError(f"grille de {bars} mesures : multiple de {BARS} requis")
    src = src.expanduser()
    data = tomllib.loads((src / "profile.toml").read_text(encoding="utf-8"))
    if data.get("harmony", {}).get("model") != "loop":
        raise ValueError(f"{src.name} : harmonie {data.get('harmony', {}).get('model')!r}, pas `loop` : pas de grille utilisateur")
    spb = int(data["meter"]["steps_per_bar"])
    spc = int(data["harmony"]["steps_per_chord"])
    fixed = data.get("fixed_tonality")
    report = GridReport(src.name, bars, spb, spc, fixed or {"key": FIXED_KEY, "mode": FIXED_MODE}, fixed is not None)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    out, replaced = [], False
    for name, body in _blocks((src / "profile.toml").read_text(encoding="utf-8")):
        if name in ("form", "harmony"):
            if not replaced:
                out.append(_form_and_harmony(spb, spc, bars, report))
                replaced = True
            continue
        out.append(body)
    text = "".join(out)
    if fixed is None:
        text = text.rstrip("\n") + f'\n\n[fixed_tonality]\nkey = {FIXED_KEY}\nmode = "{FIXED_MODE}"\n'
    (dst / "profile.toml").write_text(text, encoding="utf-8")
    check = tomllib.loads((dst / "profile.toml").read_text(encoding="utf-8"))
    if [p["name"] for p in check["form"]["parts"]] != ["Grille"] or list(check["harmony"]["parts"]) != ["Grille"]:
        raise RuntimeError(f"{src.name} : profil réécrit incohérent")
    return report
