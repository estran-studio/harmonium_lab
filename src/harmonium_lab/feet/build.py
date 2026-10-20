"""Assemblage de `harmonium_trad.sf2` depuis `prepared/` (chantier SK1).

`prepared/{heel,toe}/NN.wav` (16 bits mono 44,1 kHz) → preset banque 0
programme 0 « Podorythmie », touche 36 = talon, 37 = pointe, variantes
en couches de vélocité. Écrit la SF2 (défaut :
`../harmonium/assets/harmonium_trad.sf2` si le repo moteur est à côté,
sinon `target/harmonium_trad.sf2`) et affiche les échantillons retenus
(rôle, licence, auteur) + la taille du fichier.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import soundfile as sf

from harmonium_lab.feet import (KEY_HEEL, KEY_TOE, SAMPLE_RATE, default_sf2_path,
                                feet_dir, repo_root)
from harmonium_lab.feet.sf2 import FeetBank, VoiceSample, build_sf2, velocity_layers

ROLE_KEY = {"heel": KEY_HEEL, "toe": KEY_TOE}
ROLE_LABEL = {"heel": "talon", "toe": "pointe"}


def resolve_output(explicit: str | None) -> Path:
    """`--output`, sinon assets du moteur s'il est à côté, sinon target/."""
    if explicit:
        return Path(explicit)
    candidate = default_sf2_path()
    if (candidate.parent / "GeneralUser-GS.sf2").is_file() or candidate.parent.is_dir() \
            and (candidate.parent.parent / "Cargo.toml").is_file():
        return candidate
    return repo_root() / "target" / "harmonium_trad.sf2"


def load_voice(wav: Path, key: int, vel_lo: int, vel_hi: int) -> VoiceSample:
    data, sr = sf.read(str(wav), dtype="int16", always_2d=True)
    if sr != SAMPLE_RATE or data.shape[1] != 1:
        raise ValueError(f"{wav.name} : {sr} Hz/{data.shape[1]} canaux, "
                         f"44,1 kHz mono exigé (relance feet-prepare)")
    return VoiceSample(wav.stem, data[:, 0].tobytes(), key, vel_lo, vel_hi)


def build_from_prepared(root: Path) -> FeetBank:
    bank = FeetBank()
    for role, key in ROLE_KEY.items():
        wavs = sorted((root / "prepared" / role).glob("*.wav"))
        if not wavs:
            raise ValueError(f"aucun échantillon dans prepared/{role}/ "
                             f"(lance feet-fetch puis feet-prepare)")
        layers = velocity_layers(len(wavs))
        voices = [load_voice(w, key, lo, hi) for w, (lo, hi) in zip(wavs, layers)]
        setattr(bank, role, voices)
    return bank


def retained_table(root: Path) -> list[dict]:
    """Échantillons retenus : rôle ← prepared, licence/auteur ← manifeste."""
    manifest = {e["id"]: e for e in
                (json.loads(line) for line in (root / "manifest.jsonl")
                 .read_text(encoding="utf-8").splitlines() if line.strip())}
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    rows = []
    for role in ROLE_KEY:
        owndir = root / "own" / role
        own = sorted(owndir.glob("*.wav")) if owndir.is_dir() else []
        if own:
            for wav in own:
                rows.append({"role": ROLE_LABEL[role], "fichier": wav.name,
                             "licence": "enregistrement du propriétaire",
                             "auteur": "propriétaire"})
        else:
            for h in selection.get(role, []):
                e = manifest[h["src"]]
                rows.append({"role": ROLE_LABEL[role], "fichier": e["title"],
                             "licence": e["license"], "auteur": e["author"],
                             "src": h["src"], "t": h["t"]})
    return rows


def build_sf2_file(root: Path, output: Path) -> tuple[Path, list[dict]]:
    bank = build_from_prepared(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build_sf2(bank))
    return output, retained_table(root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feet-sf2",
                                 description="Assemble harmonium_trad.sf2 (prepared/ → .sf2)")
    ap.add_argument("--root", type=Path, default=feet_dir(), help="dossier samples/feet")
    ap.add_argument("--output", "-o", default=None, help="chemin .sf2 (défaut auto)")
    args = ap.parse_args(argv)
    try:
        output = resolve_output(args.output)
        path, rows = build_sf2_file(args.root, output)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    print("échantillons retenus :")
    for r in rows:
        print(f"  {r['role']:>6} | {r['licence']:<32} | {r['auteur']:<20} | {r['fichier']}")
    print(f"\n{path} : {path.stat().st_size} octets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
