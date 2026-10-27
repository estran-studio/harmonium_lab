"""Rendu MIDI → WAV d'une boucle transcrite (fluidsynth + GeneralUser GS).

Même chaîne que `trad-render` : `fluidsynth -ni -r 44100`, banque du
moteur, normalisation du pic. Sert à comparer à l'oreille la boucle
transcrite avec l'original.
"""

from __future__ import annotations

import array
import shutil
import subprocess
import wave
from pathlib import Path

#: Pic cible des WAV (même convention que trad-render).
PEAK_TARGET = 0.125


def default_soundfont() -> Path:
    """Banque du moteur : `../harmonium/assets/GeneralUser-GS.sf2` (ou checkout principal)."""
    root = Path(__file__).resolve().parents[3]
    direct = root.parent / "harmonium" / "assets" / "GeneralUser-GS.sf2"
    if direct.is_file():
        return direct
    common = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-common-dir"],
                            capture_output=True, text=True)
    if common.returncode == 0:
        main_root = Path(common.stdout.strip()).resolve().parent
        alt = main_root.parent / "harmonium" / "assets" / "GeneralUser-GS.sf2"
        if alt.is_file():
            return alt
    return direct


def wav_peak(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        frames = w.readframes(w.getnframes())
    samples = array.array("h", frames)
    return (max(abs(s) for s in samples) / 32768.0) if samples else 0.0


def normalize_wav(path: Path, target: float = PEAK_TARGET) -> tuple[float, float]:
    """Ramène le pic à `target` par gain linéaire. Retourne (avant, après)."""
    with wave.open(str(path), "rb") as w:
        params, frames = w.getparams(), w.readframes(w.getnframes())
    samples = array.array("h", frames)
    peak = max((abs(s) for s in samples), default=0)
    before = peak / 32768.0
    if peak == 0:
        return before, before
    gain = target * 32768.0 / peak
    scaled = array.array("h", (max(-32768, min(32767, round(s * gain))) for s in samples))
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(scaled.tobytes())
    return before, min(1.0, before * gain)


def render_loop_wav(midi_path: Path, wav_path: Path,
                    soundfont: Path | None = None) -> tuple[float, float]:
    """Rend `midi_path` en WAV 44,1 kHz normalisé. Retourne (pic avant, après)."""
    fluidsynth = shutil.which("fluidsynth")
    if fluidsynth is None:
        raise RuntimeError("fluidsynth introuvable : `brew install fluidsynth`")
    sf = soundfont or default_soundfont()
    if not sf.is_file():
        raise RuntimeError(f"banque introuvable : {sf} (lance `make soundfont` dans le repo harmonium)")
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [fluidsynth, "-ni", "-r", "44100", "-F", str(wav_path), str(sf), str(midi_path)],
        capture_output=True, text=True, timeout=300)
    if not wav_path.is_file() or wav_path.stat().st_size == 0:
        raise RuntimeError(f"fluidsynth n'a produit aucun WAV pour {midi_path.name} : "
                           f"{(proc.stdout + proc.stderr).strip()}")
    return normalize_wav(wav_path)
