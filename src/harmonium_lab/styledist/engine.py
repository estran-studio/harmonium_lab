"""Rendu d'un profil par le CLI du moteur (dépôt frère `harmonium`).

Commande, par graine et par banque :

    cargo run -q -p harmonium-cli --release --manifest-path <moteur>/Cargo.toml -- \\
        --export --bars M --profile <dossier> --seed S \\
        --soundfont <sf2> --feet-soundfont <sf2 des pieds> \\
        --record-wav <wav> --record-midi <mid>

Le MIDI ne dépend pas de la banque : il est écrit une fois par graine.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Bank:
    """Banque de rendu : `label` nomme la variante dans la sortie."""
    label: str
    soundfont: Path
    feet_soundfont: Path


def parse_bank(spec: str) -> Bank:
    """`label=chemin.sf2` ou `label=chemin.sf2,pieds.sf2` (pieds = banque principale par défaut :
    sans cela le moteur joue la batterie sur les pieds de podorythmie, pas sur le kit du profil)."""
    label, sep, rest = spec.partition("=")
    if not sep or not label or not rest:
        raise ValueError(f"banque invalide « {spec} » : attendu label=chemin.sf2[,pieds.sf2]")
    main, _, feet = rest.partition(",")
    return Bank(label, Path(main).expanduser().resolve(),
                Path(feet or main).expanduser().resolve())


def resolve_profile(engine_dir: Path, profile: str) -> Path:
    """`profile` : dossier existant, ou id d'un profil de `<moteur>/profiles/`."""
    for cand in (Path(profile), engine_dir / "profiles" / profile):
        if (cand / "profile.toml").is_file():
            return cand.resolve()
    raise FileNotFoundError(f"profil introuvable : {profile} (ni dossier, ni {engine_dir}/profiles/{profile})")


def engine_command(engine_dir: Path, profile_dir: Path, bank: Bank, seed: int, bars: int,
                   wav: Path, midi: Path) -> list[str]:
    return ["cargo", "run", "-q", "-p", "harmonium-cli", "--release",
            "--manifest-path", str(engine_dir / "Cargo.toml"), "--",
            "--export", "--bars", str(bars), "--profile", str(profile_dir),
            "--seed", str(seed), "--soundfont", str(bank.soundfont),
            "--feet-soundfont", str(bank.feet_soundfont),
            "--record-wav", str(wav), "--record-midi", str(midi)]


def render_seeds(engine_dir: Path, profile_dir: Path, banks: list[Bank], seeds: list[int],
                 bars: int, out_dir: Path, force: bool = False) -> dict[str, dict[int, tuple[Path, Path]]]:
    """Rend chaque graine pour chaque banque. Retourne `{label: {graine: (wav, midi)}}`.
    Un rendu déjà présent est réutilisé sauf `force` (le nom porte profil, banque, mesures)."""
    out: dict[str, dict[int, tuple[Path, Path]]] = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for bank in banks:
        for path in (bank.soundfont, bank.feet_soundfont):
            if not path.is_file():
                raise FileNotFoundError(f"banque introuvable : {path}")
        out[bank.label] = {}
        for seed in seeds:
            stem = f"{profile_dir.name}_{bank.label}_b{bars}_s{seed}"
            wav, midi = out_dir / f"{stem}.wav", out_dir / f"{stem}.mid"
            if force or not (wav.is_file() and midi.is_file()):
                cmd = engine_command(engine_dir, profile_dir, bank, seed, bars, wav, midi)
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                if proc.returncode != 0 or not (wav.is_file() and midi.is_file()):
                    raise RuntimeError(f"rendu moteur en échec (graine {seed}, banque {bank.label}) :\n"
                                       f"{' '.join(cmd)}\n{proc.stdout[-800:]}{proc.stderr[-1500:]}")
            out[bank.label][seed] = (wav, midi)
    return out
