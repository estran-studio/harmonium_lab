"""Écoute de contrôle des pieds (chantier SK1) : `feet-preview`.

Produit dans `target/feet_preview/` :
- `reel_pieds_seuls.wav` : 8 mesures de reel (talon sur les noires,
  pointe sur les contretemps de croche, 230 BPM) ;
- `reel_complet.wav` : un vrai reel (corpus si présent, sinon un reel
  de contrôle embarqué) rendu avec violon + accords + basse + pieds ;
- `pieds_stem.wav`, `violon_stem.wav` : tiges non normalisées + niveaux
  (pic RMS par fenêtre de 100 ms) pour vérifier que les pieds restent
  sous le violon.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

from harmonium_lab.feet import FEET_PROG, repo_root
from harmonium_lab.trad import render
from harmonium_lab.trad.render import (DRUM_HEEL, DRUM_TOE, FEET_BANK, FEET_CHANNEL,
                                       PROG_MELODY, VEL_HEEL, VEL_TOE)

#: Reel de contrôle (AABB, 32 mesures jouées) si le corpus est absent.
FALLBACK_REEL_ABC = """X:1
T:Reel de controle (pieds)
R:reel
M:4/4
L:1/8
K:D
|: "D" d2dA BcdB | "D" AFDF AFDF | "G" G2GB eGBd | "A" egfe dBAF |
"D" D2DA BdAF | "G" GBGB edBd | "A" egfe dBAF |1 "D" EDEF D4 :|2 "D" EDEF D2D2 ||
|: "D" f2fa dfaf | "D" dfaf dfaf | "G" g2gb egbg | "A" agfe dBAF |
"D" F2FA dFAF | "G" GBGB edBd | "A" egfe dBAF | "D" EDEF D4 :|
"""

TPB = 480


def resolve_gu(explicit: str | None) -> Path:
    if explicit:
        return render.resolve_soundfont(explicit)
    try:
        return render.resolve_soundfont(None)
    except render.RenderError:
        fallback = Path.home() / ".harmonium-orch" / "sf" / "GeneralUser-GS.sf2"
        if fallback.is_file():
            print(f"banque : repli sur {fallback}")
            return fallback
        raise


def feet_pattern_mid(out: Path, bars: int = 8, bpm: int = 230,
                     vel_scale: float = render.FEET_VEL_SCALE,
                     humanize: int = render.FEET_HUMANIZE,
                     seed: int = render.FEET_SEED) -> None:
    """8 mesures : talon noires, pointe contretemps (gain + humanisation, graine fixe)."""
    mid = mido.MidiFile(ticks_per_beat=TPB)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(mido.Message("control_change", channel=FEET_CHANNEL, control=0, value=0, time=0))
    track.append(mido.Message("control_change", channel=FEET_CHANNEL, control=32,
                              value=FEET_BANK, time=0))
    track.append(mido.Message("program_change", channel=FEET_CHANNEL, program=FEET_PROG, time=0))
    import random
    rng = random.Random(seed)
    events: list[tuple[int, mido.Message]] = []
    for bar in range(bars):
        for beat in range(4):
            t = (bar * 4 + beat) * TPB
            events.append((t, mido.Message("note_on", channel=FEET_CHANNEL, note=DRUM_HEEL,
                                           velocity=render.feet_velocity(VEL_HEEL, rng, vel_scale, humanize),
                                           time=0)))
            events.append((t + TPB - 40, mido.Message("note_off", channel=FEET_CHANNEL,
                                                      note=DRUM_HEEL, velocity=0, time=0)))
            to = t + TPB // 2
            events.append((to, mido.Message("note_on", channel=FEET_CHANNEL, note=DRUM_TOE,
                                            velocity=render.feet_velocity(VEL_TOE, rng, vel_scale, humanize),
                                            time=0)))
            events.append((to + TPB // 2 - 40, mido.Message("note_off", channel=FEET_CHANNEL,
                                                            note=DRUM_TOE, velocity=0, time=0)))
    events.sort(key=lambda e: e[0])
    last = 0
    for tick, msg in events:
        msg.time = tick - last
        last = tick
        track.append(msg)
    mid.save(str(out))


def pick_reel_abc(root: Path, out_dir: Path) -> tuple[Path, dict]:
    """Premier reel du corpus, sinon le reel de contrôle embarqué."""
    manifest = root / "manifest.jsonl"
    if manifest.is_file():
        rows = [r for r in (json.loads(line) for line in
                            manifest.read_text(encoding="utf-8").splitlines() if line.strip())
                if r.get("type") == "reel"]
        rows.sort(key=lambda r: r["id"])
        for row in rows:
            abc = root / "tunes" / "reel" / f"{row['id']}.abc"
            if abc.is_file():
                return abc, row
    abc = out_dir / "reel_controle.abc"
    abc.write_text(FALLBACK_REEL_ABC, encoding="utf-8")
    print("corpus absent : reel de contrôle embarqué")
    return abc, {"id": "reel_controle", "type": "reel", "meter": "4/4"}


def split_stems(full_mid: Path, out_dir: Path) -> tuple[Path, Path | None]:
    """Tiges pieds seuls / violon seul (canaux filtrés, méta conservées)."""
    import copy
    mid = mido.MidiFile(str(full_mid))
    prog: dict[int, int] = {}
    for track in mid.tracks:
        for msg in track:
            if msg.type == "program_change":
                prog[msg.channel] = msg.program
    violin_ch = {ch for ch, p in prog.items() if p == PROG_MELODY} or {0}

    def keep(channels: set[int], dest: Path) -> Path:
        out = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
        for track in mid.tracks:
            kept = mido.MidiTrack()
            for msg in track:
                if msg.type in ("note_on", "note_off"):
                    if msg.channel not in channels:
                        continue
                kept.append(copy.copy(msg))
            out.tracks.append(kept)
        out.save(str(dest))
        return dest

    feet = keep({FEET_CHANNEL}, out_dir / "pieds_stem.mid")
    violin = keep(violin_ch, out_dir / "violon_stem.mid") if violin_ch != {FEET_CHANNEL} else None
    return feet, violin


def max_rms_100ms(wav: Path) -> tuple[float, float]:
    """Pic RMS sur fenêtres de 100 ms (linéaire, dBFS)."""
    data, sr = sf.read(str(wav), always_2d=True)
    mono = data.mean(axis=1)
    n = max(1, int(0.1 * sr))
    if len(mono) < n:
        return 0.0, float("-inf")
    frames = mono[:len(mono) // n * n].reshape(-1, n)
    peak = float(np.sqrt((frames ** 2).mean(axis=1)).max())
    return peak, 20 * np.log10(peak) if peak > 0 else float("-inf")


def overall_rms_db(wav: Path) -> float:
    """RMS global de la tige (dBFS) : la métrique de niveau pieds/violon."""
    data, _ = sf.read(str(wav), always_2d=True)
    rms = float(np.sqrt((data.mean(axis=1) ** 2).mean()))
    return 20 * np.log10(rms) if rms > 0 else float("-inf")


def preview(out: Path, root: Path, soundfont: Path, feet_soundfont: Path,
            vel_scale: float = render.FEET_VEL_SCALE,
            humanize: int = render.FEET_HUMANIZE,
            feet_seed: int = render.FEET_SEED) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    fonts = [soundfont, feet_soundfont]

    seuls_mid = out / "reel_pieds_seuls.mid"
    feet_pattern_mid(seuls_mid, vel_scale=vel_scale, humanize=humanize, seed=feet_seed)
    seuls_wav = out / "reel_pieds_seuls.wav"
    render.render_wav(seuls_mid, seuls_wav, soundfont, feet_soundfont)

    abc, row = pick_reel_abc(root, out)
    meter = render.parse_meter_value(row.get("meter"), "reel")
    full_mid = out / "reel_complet.mid"
    render.render_midi(abc, full_mid, "reel", meter, remap_feet=True,
                       vel_scale=vel_scale, humanize=humanize, seed=feet_seed)

    feet_mid, violin_mid = split_stems(full_mid, out)
    feet_wav = out / "pieds_stem.wav"
    render.render_wav(feet_mid, feet_wav, soundfont, feet_soundfont, normalize=False)
    levels = {"pieds": (*max_rms_100ms(feet_wav), overall_rms_db(feet_wav))}
    violin_wav = None
    if violin_mid is not None:
        violin_wav = out / "violon_stem.wav"
        render.render_wav(violin_mid, violin_wav, soundfont, feet_soundfont, normalize=False)
        levels["violon"] = (*max_rms_100ms(violin_wav), overall_rms_db(violin_wav))

    print(f"\n{seuls_wav.name} : pic {render.wav_peak(seuls_wav):.3f}")
    print(f"{full_wav.name} ({row['id']}) : pic {render.wav_peak(full_wav):.3f}")
    print("niveaux : pic RMS / 100 ms et RMS global (dBFS) :")
    for src, (lin, db, rms_db) in levels.items():
        print(f"  {src:>6} : {lin:.4f} ({db:.1f} dBFS pic) / {rms_db:.1f} dBFS global")
    if "violon" in levels:
        margin = levels["violon"][2] - levels["pieds"][2]
        print(f"  marge pieds sous violon : {margin:.1f} dB (cible ≥ 8 dB) "
              f"{'OK' if margin >= 8 else 'INSUFFISANT'}")
    return {"seuls": str(seuls_wav), "complet": str(full_wav), "levels": levels}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feet-preview",
                                 description="Écoute de contrôle des pieds (pieds seuls + reel complet)")
    ap.add_argument("--out", type=Path, default=repo_root() / "target" / "feet_preview")
    ap.add_argument("--root", type=Path, default=repo_root() / "corpus" / "trad")
    ap.add_argument("--soundfont", default=None, help="GeneralUser-GS.sf2")
    ap.add_argument("--feet-soundfont", default=None, help="harmonium_trad.sf2 (défaut auto)")
    ap.add_argument("--feet-gain", type=float, default=render.FEET_VEL_SCALE)
    ap.add_argument("--feet-humanize", type=int, default=render.FEET_HUMANIZE)
    ap.add_argument("--feet-seed", type=int, default=render.FEET_SEED)
    args = ap.parse_args(argv)
    try:
        gu = resolve_gu(args.soundfont)
        feet_sf = render.resolve_feet_soundfont(args.feet_soundfont)
        if feet_sf is None:
            raise render.RenderError("banque des pieds absente : lance `make trad-sf2`")
        preview(args.out, args.root, gu, feet_sf, args.feet_gain, args.feet_humanize,
                args.feet_seed)
    except render.RenderError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
