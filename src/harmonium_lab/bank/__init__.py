"""Construction générique de banques SoundFont 2.01 pilotée par manifeste (G6).

Aucun nom de jeu ou de style n'est codé en dur : les timbres, licences,
provenances et affectations General MIDI (banque 0 mélodique/harmonique,
banque 128 percussions) sont lus depuis `samples/<banque>/manifest.jsonl`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

#: Fréquence d'échantillonnage standard des banques construites (Hz, mono 16 bits).
SAMPLE_RATE = 44100


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_bank_dir(name_or_path: str | Path) -> Path:
    """Résout un nom de banque (`samples/<nom>`) ou un chemin explicite."""
    p = Path(name_or_path)
    if p.is_dir() or (p / "manifest.jsonl").is_file():
        return p
    candidate = repo_root() / "samples" / p.name
    if candidate.is_dir() or (candidate / "manifest.jsonl").is_file():
        return candidate
    return p


def _engine_assets_dir() -> Path | None:
    """Dossier `../harmonium/assets` (direct ou via le dépôt principal d'un worktree)."""
    root = repo_root()
    direct = root.parent / "harmonium" / "assets"
    if direct.is_dir():
        return direct
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
    )
    if common.returncode == 0:
        main_root = Path(common.stdout.strip()).resolve().parent
        alt = main_root.parent / "harmonium" / "assets"
        if alt.is_dir():
            return alt
    return None


def default_sf2_output(bank_root: Path) -> Path:
    """Sortie par défaut : `../harmonium/assets/<banque>.sf2` si le moteur est voisin."""
    bank_id = bank_root.resolve().name
    assets = _engine_assets_dir()
    if assets is not None:
        return assets / f"{bank_id}.sf2"
    return repo_root() / "target" / f"{bank_id}.sf2"
