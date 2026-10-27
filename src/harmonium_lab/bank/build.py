"""Assemblage d'une banque SoundFont 2.01 depuis `manifest.jsonl` + `prepared/` (G6).

Générique et piloté par données : les presets (banque 0 mélodique/harmonique,
banque 128 percussions GM), tessitures, fenêtres de boucle et enveloppes viennent
du manifeste ; le nom de la banque vient du dossier (`samples/<nom>/`). Aucun
nom de jeu ou de style dans le code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from harmonium_lab.bank import SAMPLE_RATE, default_sf2_output, resolve_bank_dir
from harmonium_lab.bank.sf2 import (
    POST_LOOP_PAD,
    BankPreset,
    BankZone,
    SoundFontSpec,
    build_multi_sf2,
    inspect_sf2,
)

#: Métadonnées de la banque (nom affiché, copyright SF2, commentaire).
BANK_META = "bank.json"


def load_bank_meta(root: Path) -> dict[str, Any]:
    meta_path = root / BANK_META
    if meta_path.is_file():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "name": root.name,
        "copyright": "harmonium_lab",
        "comment": f"{root.name} — construite par harmonium_lab.bank",
    }


def zone_from_entry(root: Path, entry: dict[str, Any]) -> BankZone:
    """Une ligne du manifeste → une zone SF2 (échantillon + tessiture + enveloppe)."""
    prepared = root / "prepared" / f"{entry['id']}.wav"
    if not prepared.is_file():
        raise RuntimeError(
            f"{entry['id']} : échantillon préparé introuvable ({prepared}) — "
            f"lance `python -m harmonium_lab.bank.prepare --root {root}`"
        )
    from .prepare import sha256_of

    if sha256_of(prepared) != entry.get("sha256"):
        raise ValueError(f"{entry['id']} : empreinte WAV différente du manifeste")
    data, sr = sf.read(str(prepared), always_2d=True)
    if data.shape[1] != 1:
        raise RuntimeError(f"{entry['id']} : échantillon préparé non mono")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"{entry['id']} : fréquence {sr} Hz ≠ {SAMPLE_RATE} Hz")
    audio = np.asarray(data[:, 0], dtype=np.float64)

    root_key = int(entry["root_key"])
    key_range = entry.get("key_range") or [root_key, root_key]
    vel_range = entry.get("vel_range") or [0, 127]
    envelope = dict(entry.get("envelope", {}))

    loop = bool(entry.get("loop", False))
    loop_start, loop_end = 0, 0
    if loop:
        window = entry.get("loop_window")
        if not window or len(window) != 2:
            raise RuntimeError(f"{entry['id']} : bouclée sans loop_window (lance --inventory)")
        loop_start, loop_end = int(window[0]), int(window[1])
        if not (POST_LOOP_PAD <= loop_start < loop_end <= len(audio) - POST_LOOP_PAD):
            raise RuntimeError(
                f"{entry['id']} : loop_window [{loop_start}, {loop_end}] "
                f"invalide pour {len(audio)} points"
            )

    return BankZone(
        sample_name=str(entry["id"]),
        audio=audio,
        root_key=root_key,
        key_lo=int(key_range[0]),
        key_hi=int(key_range[1]),
        vel_lo=int(vel_range[0]),
        vel_hi=int(vel_range[1]),
        loop=loop,
        loop_start=loop_start,
        loop_end=loop_end,
        attack_s=float(envelope.get("attack_s", 0.002)),
        decay_s=(float(envelope["decay_s"]) if envelope.get("decay_s") is not None else None),
        sustain_cb=(int(envelope["sustain_cb"]) if envelope.get("sustain_cb") is not None else None),
        release_s=float(envelope.get("release_s", 0.25)),
        attenuation_cb=int(envelope.get("attenuation_cb", 0)),
        exclusive_class=int(entry.get("exclusive_class", envelope.get("exclusive_class", 0))),
        sample_rate=sr,
    )


def spec_from_manifest(root: Path, entries: list[dict[str, Any]]) -> SoundFontSpec:
    """Regroupe les entrées par preset (banque, programme) dans l'ordre du manifeste."""
    meta = load_bank_meta(root)
    presets: dict[tuple[int, int], BankPreset] = {}
    order: list[tuple[int, int]] = []
    names: dict[tuple[int, int], str] = {}
    for entry in entries:
        preset = entry["preset"]
        key = (int(preset["bank"]), int(preset["program"]))
        name = str(preset.get("name") or f"Preset {key[1]}")
        if key not in presets:
            presets[key] = BankPreset(name=name, bank=key[0], program=key[1], zones=[])
            order.append(key)
            names[key] = name
        elif names[key] != name:
            raise RuntimeError(f"preset {key} : noms incohérents ({names[key]!r} vs {name!r})")
        presets[key].zones.append(zone_from_entry(root, entry))
    return SoundFontSpec(
        name=str(meta.get("name", root.name)),
        presets=[presets[key] for key in order],
        copyright=str(meta.get("copyright", "harmonium_lab")),
        comment=str(meta.get("comment", "")),
    )


def build_bank(root: Path, output: Path | None = None) -> Path:
    """Construit la banque, l'auto-vérifie et l'écrit ; retourne le chemin écrit."""
    from harmonium_lab.bank.prepare import read_manifest

    entries = read_manifest(root)
    spec = spec_from_manifest(root, entries)
    data = build_multi_sf2(spec)

    got = inspect_sf2(data)
    n_zones = sum(len(p.zones) for p in spec.presets)
    if len(got["presets"]) != len(spec.presets) or not (0 < len(got["samples"]) <= n_zones):
        raise RuntimeError("auto-vérification : tables phdr/shdr incohérentes")

    out = output or default_sf2_output(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"Banque : {out} ({len(data)} octets, {len(spec.presets)} presets, "
          f"{len(got['samples'])} échantillons)")
    for preset in spec.presets:
        zones = ", ".join(
            f"{z.sample_name}[{z.key_lo}-{z.key_hi}]" + ("~boucle" if z.loop else "")
            for z in preset.zones
        )
        print(f"  {preset.bank}/{preset.program:3d} {preset.name:<20} {zones}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bank-sf2",
        description="Assemble la banque SoundFont (manifeste + prepared/ → .sf2)",
    )
    ap.add_argument("--root", type=Path, required=True,
                    help="dossier de la banque (samples/<nom>)")
    ap.add_argument("--output", "-o", type=Path, default=None,
                    help="sortie .sf2 (défaut : assets du moteur, sinon target/)")
    args = ap.parse_args(argv)
    try:
        root = resolve_bank_dir(args.root)
        build_bank(root, args.output)
    except RuntimeError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())