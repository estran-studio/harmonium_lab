"""Banque « pieds » de podorythmie (chantier SK1).

Un preset banque 0 programme 0 « Podorythmie » : touche 36 = talon,
touche 37 = pointe (variantes en couches de vélocité). Les pieds sont
joués sur un canal mélodique dédié (canal 11), pas sur le canal
percussion GM : voir `trad.render.remap_feet_channel`.
"""

from __future__ import annotations

from pathlib import Path

#: Touches MIDI des pieds (mêmes hauteurs que les notes GM 36/37,
#: mais sur un canal mélodique : ce sont des échantillons, pas du GM).
KEY_HEEL = 36
KEY_TOE = 37

#: Canal mélodique dédié aux pieds (0-based 10 = « canal 11 »).
FEET_CHANNEL = 10

#: Preset « Podorythmie » : banque 0, programme 0 de `harmonium_trad.sf2`.
FEET_BANK = 0
FEET_PROG = 0

#: Rôles (aussi noms des sous-dossiers `prepared/` et `own/`).
ROLE_HEEL = "heel"
ROLE_TOE = "toe"
ROLES = (ROLE_HEEL, ROLE_TOE)

#: Fréquence d'échantillonnage de la banque (Hz, mono 16 bits).
SAMPLE_RATE = 44100


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def feet_dir() -> Path:
    """Dossier versionné des échantillons (`samples/feet/`)."""
    return repo_root() / "samples" / "feet"


def default_sf2_path() -> Path:
    """Sortie `make trad-sf2` : `../harmonium/assets/harmonium_trad.sf2`."""
    return repo_root().parent / "harmonium" / "assets" / "harmonium_trad.sf2"
