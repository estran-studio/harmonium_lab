"""Tests mono-frappe des pieds (SK1b) : aucun accès réseau.

`validate_hit` est le garde-fou permanent : un seul transitoire > 30 %,
pic < 20 ms, durée ≤ 250 ms. Il s'applique aux libres (`feet-prepare`
lève sinon), aux `prepared/` présents (sautés s'ils sont absents) et
aux enregistrements du propriétaire (`own/`, échec explicite nommant
le fichier).
"""

from __future__ import annotations

import random
from pathlib import Path

import mido
import numpy as np
import pytest
import soundfile as sf

from harmonium_lab.feet import SAMPLE_RATE
from harmonium_lab.feet.prepare import (cut_hit, late_transients, prepare_own,
                                        validate_hit)
from harmonium_lab.feet.sf2 import velocity_layers
from harmonium_lab.trad import render as R

SR = SAMPLE_RATE
PREPARED = Path(__file__).resolve().parent.parent / "samples" / "feet" / "prepared"

needs_prepared = pytest.mark.skipif(
    not (PREPARED / "heel").is_dir(),
    reason="samples/feet/prepared absent (lance `make trad-sf2`)",
)


def _decay(freq: float, n: int, decay: float = 12.0, amp: float = 0.8) -> np.ndarray:
    t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)


def test_frappe_propre_passe():
    hit = _decay(90, int(0.25 * SR))
    assert late_transients(hit) == []
    info = validate_hit(hit, "frappe-propre")
    assert info["peak_ms"] < 20.0 and info["dur_ms"] <= 250.0


def test_double_frappe_rejetee():
    hit = _decay(90, int(0.25 * SR))
    echo = _decay(90, int(0.16 * SR))
    hit[int(0.09 * SR):] += 0.8 * echo[:len(hit) - int(0.09 * SR)]
    late = late_transients(hit)
    assert late and abs(late[0] - 90) < 15
    with pytest.raises(ValueError, match="2ᵉ transitoire"):
        validate_hit(hit, "double-frappe")


def test_attaque_tardive_rejetee():
    n = int(0.25 * SR)
    swell = 0.8 * np.sin(2 * np.pi * 90 * np.arange(n) / SR) * (np.arange(n) / n) ** 2
    with pytest.raises(ValueError, match="pic à .* ms"):
        validate_hit(swell, "attaque-tardive")


def test_silence_rejete():
    with pytest.raises(ValueError, match="silence"):
        cut_hit(np.zeros(SR), 0.3)


def test_cut_borne_fin_avant_frappe_suivante():
    audio = np.zeros(2 * SR)
    audio[int(0.3 * SR):int(0.5 * SR)] = _decay(90, int(0.2 * SR))
    audio[int(0.45 * SR):int(0.65 * SR)] += _decay(90, int(0.2 * SR))
    hit = cut_hit(audio, 0.3, end_limit=0.445)
    assert len(hit) / SR <= 0.25
    validate_hit(hit, "bornee")  # ne lève pas : 2ᵉ frappe exclue


def test_cut_plafond_250ms():
    audio = np.zeros(2 * SR)
    audio[int(0.3 * SR):] = 0.5  # nappe qui ne s'éteint pas
    hit = cut_hit(audio, 0.3)
    assert len(hit) / SR <= 0.2501


@needs_prepared
def test_prepared_monofrappe():
    wavs = sorted(PREPARED.glob("*/*.wav"))
    assert len(wavs) >= 6, "≥ 3 variantes par rôle exigées"
    for wav in wavs:
        data, sr = sf.read(str(wav))
        assert sr == SR
        mono = data.mean(axis=1) if data.ndim > 1 else data
        validate_hit(mono.astype(float) / 32768.0, f"prepared/{wav.parent.name}/{wav.name}")


def test_own_fichier_invalide_erreur_explicite(tmp_path: Path):
    own = tmp_path / "own" / "heel"
    own.mkdir(parents=True)
    n = int(0.5 * SR)
    swell = np.zeros(n + int(0.05 * SR))
    swell[int(0.05 * SR):] = 0.8 * np.sin(2 * np.pi * 90 * np.arange(n) / SR) \
        * (np.arange(n) / n) ** 2  # montée lente, pas d'attaque
    sf.write(str(own / "gonfle.wav"), (swell * 32767).astype(np.int16), SR)
    with pytest.raises(ValueError, match="own/heel/gonfle.wav.*pic à"):
        prepare_own(tmp_path)


def test_own_fichier_silencieux_erreur_explicite(tmp_path: Path):
    own = tmp_path / "own" / "toe"
    own.mkdir(parents=True)
    sf.write(str(own / "vide.wav"), np.zeros(int(0.5 * SR)), SR)
    with pytest.raises(ValueError, match="own/toe/vide.wav.*silencieux"):
        prepare_own(tmp_path)


def test_own_fichier_propre_passe(tmp_path: Path):
    own = tmp_path / "own" / "toe"
    own.mkdir(parents=True)
    sf.write(str(own / "bon.wav"), (_decay(3000, int(0.1 * SR)) * 32767).astype(np.int16), SR)
    assert prepare_own(tmp_path) == {"toe": ["bon.wav"]}
    assert (tmp_path / "prepared" / "toe" / "01.wav").is_file()


def test_humanisation_deterministe_et_variee(tmp_path: Path):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for i in range(8):
        track.append(mido.Message("note_on", note=36, velocity=100, channel=9, time=240))
        track.append(mido.Message("note_off", note=36, channel=9, time=240))
    a, b = tmp_path / "a.mid", tmp_path / "b.mid"
    mid.save(str(a))
    mid.save(str(b))
    assert R.remap_feet_channel(a) == 8
    assert R.remap_feet_channel(b) == 8
    va = [m.velocity for tr in mido.MidiFile(str(a)).tracks for m in tr
          if m.type == "note_on" and m.channel == 10]
    vb = [m.velocity for tr in mido.MidiFile(str(b)).tracks for m in tr
          if m.type == "note_on" and m.channel == 10]
    assert va == vb  # déterministe (graine fixe)
    assert len(set(va)) > 1  # humanisé (pas mitraillette)
    assert all(1 <= v <= 127 for v in va)
    assert abs(sum(va) / len(va) - 100 * R.FEET_VEL_SCALE) < 12  # gain appliqué


def test_couches_couvrent_1_a_127_sans_trou():
    covered = set()
    for n in (1, 2, 3, 4, 5, 8):
        for lo, hi in velocity_layers(n):
            covered.update(range(lo, hi + 1))
    assert covered >= set(range(1, 128))
    for lo, hi in velocity_layers(4):
        assert 0 <= lo <= hi <= 127


def test_feet_velocity_borne():
    rng = random.Random(0)
    assert R.feet_velocity(100, rng, 0.55, 12) <= 100 * 0.55 + 12
    assert R.feet_velocity(1, random.Random(0), 0.1, 12) >= 1
    assert R.feet_velocity(127, random.Random(0), 2.0, 0) == 127
