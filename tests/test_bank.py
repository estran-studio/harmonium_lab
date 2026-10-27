"""Banques G6 : empreintes, zones MIDI et tenue réelle dans FluidSynth."""
from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from harmonium_lab.bank.build import build_bank
from harmonium_lab.bank.compare import load_window, measure_sustain, rms_buckets_db
from harmonium_lab.bank.prepare import prepare, read_manifest
from harmonium_lab.bank.sf2 import BankPreset, BankZone, SoundFontSpec, build_multi_sf2

ROOT = Path(__file__).resolve().parents[1]
needs_fluidsynth = pytest.mark.skipif(not shutil.which("fluidsynth"), reason="fluidsynth absent")


@pytest.fixture(scope="module")
def bank(tmp_path_factory):
    root = tmp_path_factory.mktemp("bank")
    for name in ("bank.json", "manifest.jsonl"):
        shutil.copyfile(ROOT / "samples" / "nt_desert" / name, root / name)
    prepare(root)
    output = build_bank(root, root / "bank.sf2")
    return root, output


@needs_fluidsynth
@pytest.mark.parametrize("program,note", [(38, 32), (81, 32), (38, 44), (81, 64)])
def test_saw_holds_across_loops_and_releases_on_note_off(bank, tmp_path, program, note):
    _, font = bank
    result = measure_sustain(font, program, note, 6.0, tmp_path)
    # Plusieurs passages de boucle ; moins de 3 dB entre toutes les tranches.
    assert result["holds"], result
    assert result["excursion_db"] < 3, result
    wav = Path(result["wav"])
    held = load_window(wav, 0.5, offset_s=3)
    released = load_window(wav, 0.5, offset_s=7)
    # Une banque qui ignorerait NoteOff satisferait la tenue, mais échoue ici.
    assert np.sqrt(np.mean(released**2)) < np.sqrt(np.mean(held**2)) * 0.04


def test_changed_recipe_cannot_be_hidden_by_prepared_cache(bank, tmp_path):
    root, _ = bank
    source = read_manifest(root)[0]
    altered = json.loads(json.dumps(source))
    altered["synth"]["drive"] = 4.5
    (tmp_path / "manifest.jsonl").write_text(json.dumps(altered) + "\n")
    (tmp_path / "prepared").mkdir()
    shutil.copyfile(root / "prepared" / f"{source['id']}.wav",
                    tmp_path / "prepared" / f"{source['id']}.wav")
    with pytest.raises(ValueError, match="empreinte"):
        prepare(tmp_path)


def test_builder_rejects_tampered_prepared_audio(bank, tmp_path):
    root, _ = bank
    source = read_manifest(root)[0]
    (tmp_path / "manifest.jsonl").write_text(json.dumps(source) + "\n")
    (tmp_path / "prepared").mkdir()
    sf.write(tmp_path / "prepared" / f"{source['id']}.wav", np.zeros(44100), 44100)
    with pytest.raises(ValueError, match="empreinte"):
        build_bank(tmp_path, tmp_path / "bad.sf2")


def test_overlapping_velocity_layers_are_rejected_at_inclusive_boundary():
    t = np.arange(4410) / 44100
    zone = BankZone("tone", np.sin(2 * np.pi * 440 * t), 69, 60, 72,
                    vel_lo=0, vel_hi=63)
    def encode(other):
        return build_multi_sf2(SoundFontSpec("fixture", [BankPreset("tone", 0, 12, [zone, other])]))
    with pytest.raises(ValueError, match="recouvrent"):
        encode(replace(zone, vel_lo=63, vel_hi=127))


def test_invalid_loop_window_is_rejected():
    zone = BankZone("tone", np.ones(4410) * 0.2, 69, 0, 127,
                    loop=True, loop_start=100, loop_end=4408)
    with pytest.raises(ValueError, match="boucle"):
        build_multi_sf2(SoundFontSpec("fixture", [BankPreset("tone", 0, 12, [zone])]))


def test_half_second_buckets_reveal_decay_without_release_tail():
    sr = 22050
    t = np.arange(3 * sr) / sr
    y = np.sin(2 * np.pi * 110 * t) * np.exp(-t)
    buckets = rms_buckets_db(y, sr, skip_s=0)
    assert buckets[0] - buckets[-1] == pytest.approx(21.71, abs=0.1)
