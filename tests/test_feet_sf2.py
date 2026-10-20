"""Tests de la banque « pieds » : aucun accès réseau.

L'écrivain SF2 est testé sur des fixtures générées (structure RIFF,
tailles, terminaux) ; le rendu fluidsynth est sauté proprement si
l'outil est absent. Idem pour la réassignation des pieds (pur mido) et
la découpe/normalisation (pur numpy).
"""

from __future__ import annotations

import math
import shutil
import struct
from pathlib import Path

import mido
import numpy as np
import pytest
import soundfile as sf

from harmonium_lab.feet import KEY_HEEL, KEY_TOE
from harmonium_lab.feet.prepare import cut_hit, suggest_role
from harmonium_lab.feet.sf2 import FeetBank, VoiceSample, build_sf2, velocity_layers
from harmonium_lab.trad import render as R

SR = 44100
FLUIDSYNTH = shutil.which("fluidsynth")

needs_fluidsynth = pytest.mark.skipif(not FLUIDSYNTH, reason="fluidsynth absent")


def _thump(freq: float, n: int = 4000, decay: float = 600.0) -> bytes:
    return struct.pack("<" + "h" * n,
                       *[int(20000 * math.exp(-i / decay)
                             * math.sin(2 * math.pi * freq * i / SR))
                         for i in range(n)])


def _bank() -> FeetBank:
    hl, tl = velocity_layers(2), velocity_layers(2)
    return FeetBank(
        heel=[VoiceSample("talon01", _thump(90), KEY_HEEL, *hl[0]),
              VoiceSample("talon02", _thump(70), KEY_HEEL, *hl[1])],
        toe=[VoiceSample("pointe01", _thump(900, 2000), KEY_TOE, *tl[0]),
             VoiceSample("pointe02", _thump(1200, 2000), KEY_TOE, *tl[1])],
    )


def _chunks(data: bytes):
    """Itère (id, taille, payload) sans le pad (avec vérification d'alignement)."""
    off = 0
    while off + 8 <= len(data):
        cid, size = data[off:off + 4], struct.unpack("<I", data[off + 4:off + 8])[0]
        assert size % 2 == 0, f"{cid} : taille impaire {size}"
        yield cid, size, data[off + 8:off + 8 + size]
        off += 8 + size


def test_velocity_layers_partition():
    assert velocity_layers(1) == [(0, 127)]
    layers = velocity_layers(4)
    assert layers[0][0] == 0 and layers[-1][1] == 127
    assert all(hi + 1 == layers[i + 1][0] for i, (lo, hi) in enumerate(layers[:-1]))
    with pytest.raises(ValueError):
        velocity_layers(0)


def test_sf2_structure():
    bank = _bank()
    data = build_sf2(bank)
    assert data[:4] == b"RIFF" and data[8:12] == b"sfbk"
    assert struct.unpack("<I", data[4:8])[0] == len(data) - 8

    top = {}
    for cid, _, pay in _chunks(data[12:]):
        assert cid == b"LIST"
        top[pay[:4]] = pay[4:]
    assert set(top) == {b"INFO", b"sdta", b"pdta"}
    pdta = {cid: pay for cid, _, pay in _chunks(top[b"pdta"])}
    assert [c for c, _, _ in _chunks(top[b"pdta"])] == \
        [b"phdr", b"pbag", b"pmod", b"pgen", b"inst", b"ibag", b"imod", b"igen", b"shdr"]

    zones = bank.zones()
    n = len(zones)

    phdr = pdta[b"phdr"]
    assert len(phdr) == 2 * 38  # preset + EOP
    _, _, _, eop_bag, _, _, _ = struct.unpack("<20sHHHIII", phdr[38:])
    assert eop_bag == 1  # une zone : pas de terminal intermédiaire

    assert len(pdta[b"pbag"]) == 2 * 4  # zone + terminal global
    assert len(pdta[b"pmod"]) == 10 and pdta[b"pmod"] == b"\x00" * 10
    pgen = pdta[b"pgen"]
    assert len(pgen) == 2 * 4 and pgen[4:] == b"\x00" * 4
    assert struct.unpack("<Hh", pgen[:4]) == (41, 0)  # instrument 0

    inst = pdta[b"inst"]
    assert len(inst) == 2 * 22
    _, eoi_bag = struct.unpack("<20sH", inst[22:])
    assert eoi_bag == n

    ibag = pdta[b"ibag"]
    assert len(ibag) == (n + 1) * 4
    n_igen = (len(pdta[b"igen"]) - 4) // 4
    assert struct.unpack("<HH", ibag[-4:]) == (n_igen, 0)  # terminal global

    assert pdta[b"imod"] == b"\x00" * 10
    igen = pdta[b"igen"]
    assert len(igen) == (n * 7 + 1) * 4 and igen[-4:] == b"\x00" * 4
    opers = [struct.unpack("<Hh", igen[i:i + 4])[0] for i in range(0, len(igen) - 4, 4)]
    per_zone = [opers[i:i + 7] for i in range(0, len(opers), 7)]
    for z_opers in per_zone:
        assert z_opers[:2] == [43, 44]  # keyRange, velRange d'abord
        assert z_opers[-1] == 53  # sampleID en dernier (§8.1.2)
    # zone 2 = pointe, couche haute : valeurs exactes des générateurs
    assert per_zone[2] == [43, 44, 54, 58, 34, 38, 53]
    raw = igen[2 * 7 * 4:3 * 7 * 4]
    vals = [struct.unpack("<Hh", raw[i:i + 4])[1] for i in range(0, 28, 4)]
    assert vals[0] == 37 | (37 << 8)  # keyRange 37
    assert vals[1] == 0 | (63 << 8)  # 1ʳᵉ couche (chaque rôle partage 0–127)
    assert vals[2] == 0 and vals[6] == 2  # sans boucle, sampleID 2

    shdr = pdta[b"shdr"]
    assert len(shdr) == (n + 1) * 46 and shdr[-46:] == b"\x00" * 46
    starts = [struct.unpack("<20sIIIIIBbHH", shdr[i:i + 46])[1:3]
              for i in range(0, len(shdr) - 46, 46)]
    smpl = {cid: pay for cid, _, pay in _chunks(top[b"sdta"])}[b"smpl"]
    assert len(smpl) // 2 == sum(e - s for s, e in starts) + 46 * n

    with pytest.raises(ValueError):
        build_sf2(FeetBank())


@needs_fluidsynth
def test_sf2_renders_in_fluidsynth(tmp_path: Path):
    sf2 = tmp_path / "pieds.sf2"
    sf2.write_bytes(build_sf2(_bank()))
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("program_change", program=0, channel=0, time=0))
    for i, (note, vel) in enumerate([(36, 40), (36, 110), (37, 60), (37, 120)]):
        track.append(mido.Message("note_on", note=note, velocity=vel, channel=0,
                                  time=480 if i else 0))
        track.append(mido.Message("note_off", note=note, channel=0, time=480))
    midi = tmp_path / "pieds.mid"
    mid.save(str(midi))
    wav = tmp_path / "pieds.wav"
    import subprocess
    proc = subprocess.run([FLUIDSYNTH, "-ni", "-r", "44100", "-F", str(wav),
                           str(sf2), str(midi)], capture_output=True, text=True, timeout=120)
    assert wav.is_file() and wav.stat().st_size > 0, proc.stderr[-500:]
    assert "Couldn't parse" not in proc.stderr and "Failed to load" not in proc.stderr
    data, _ = sf.read(str(wav))
    assert float(np.abs(data).max()) > 0.005  # non silencieux


def test_remap_feet_channel(tmp_path: Path):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("program_change", program=40, channel=0, time=0))
    track.append(mido.Message("note_on", note=69, velocity=90, channel=0, time=0))
    track.append(mido.Message("note_on", note=36, velocity=100, channel=9, time=480))
    track.append(mido.Message("note_off", note=36, channel=9, time=240))
    track.append(mido.Message("note_on", note=37, velocity=70, channel=9, time=0))
    track.append(mido.Message("note_off", note=37, channel=9, time=240))
    track.append(mido.Message("note_on", note=60, velocity=80, channel=9, time=0))
    track.append(mido.Message("note_off", note=60, channel=9, time=240))
    path = tmp_path / "drums.mid"
    mid.save(str(path))

    assert R.remap_feet_channel(path) == 2

    out = mido.MidiFile(str(path))
    notes: dict[int, set[int]] = {}
    for track in out.tracks:
        for msg in track:
            if msg.type == "note_on" and msg.velocity > 0:
                notes.setdefault(msg.channel, set()).add(msg.note)
    assert notes.get(10) == {36, 37}  # canal 11
    assert 60 in notes.get(9, set()) and 36 not in notes.get(9, set())
    assert 69 in notes.get(0, set())  # violon intact
    head = out.tracks[0][:3]
    assert [(m.type, m.channel) for m in head] == \
        [("control_change", 10), ("control_change", 10), ("program_change", 10)]
    assert head[1].control == 32 and head[1].value == R.FEET_BANK
    assert head[2].program == R.FEET_PROG


def test_remap_no_feet_leaves_file_untouched(tmp_path: Path):
    mid = mido.MidiFile()
    mid.tracks.append(mido.MidiTrack([mido.Message("note_on", note=69, velocity=90,
                                                   channel=0, time=0)]))
    path = tmp_path / "plain.mid"
    mid.save(str(path))
    before = path.read_bytes()
    assert R.remap_feet_channel(path) == 0
    assert path.read_bytes() == before


def test_cut_hit_trims_fades_normalizes():
    sr = 44100
    audio = np.zeros(sr)
    t0 = int(0.3 * sr)
    body = np.sin(2 * np.pi * 90 * np.arange(int(0.3 * sr)) / sr) * np.exp(
        -np.arange(int(0.3 * sr)) / 2000)
    audio[t0:t0 + len(body)] = 0.5 * body
    hit = cut_hit(audio, 0.3)
    assert len(hit) <= int(0.25 * sr) + 1  # plafond 250 ms
    assert abs(float(np.abs(hit).max()) - 0.89) < 1e-6  # normalisé
    assert abs(hit[-1]) < 0.05  # fondu de sortie
    loud = np.nonzero(np.abs(hit) >= 0.01 * np.abs(hit).max())[0]
    assert loud[0] <= int(0.008 * sr)  # pré-attaque ≤ 5 ms (+ passage par zéro)


def test_suggest_role_by_spectrum():
    sr = 44100
    t = np.arange(sr // 4) / sr
    heel = 0.8 * np.sin(2 * np.pi * 90 * t) * np.exp(-t * 8)
    toe = 0.5 * np.sin(2 * np.pi * 3500 * t) * np.exp(-t * 60)
    assert suggest_role(heel) == "heel"
    assert suggest_role(toe) == "toe"


def test_build_from_prepared_keys_and_layers(tmp_path: Path):
    from harmonium_lab.feet.build import build_from_prepared
    sr = 44100
    for role in ("heel", "toe"):
        (tmp_path / "prepared" / role).mkdir(parents=True)
        for i in range(1, 4 if role == "heel" else 3):
            n = int(0.1 * sr)
            pcm = (0.5 * np.sin(2 * np.pi * 150 * np.arange(n) / sr) * 32767).astype(np.int16)
            sf.write(str(tmp_path / "prepared" / role / f"{i:02d}.wav"), pcm, sr)
    import json as _json
    (tmp_path / "manifest.jsonl").write_text("")
    (tmp_path / "selection.json").write_text(_json.dumps({"heel": [], "toe": []}))
    bank = build_from_prepared(tmp_path)
    assert [v.key for v in bank.heel] == [KEY_HEEL] * 3
    assert [v.key for v in bank.toe] == [KEY_TOE] * 2
    assert (bank.heel[0].vel_lo, bank.heel[-1].vel_hi) == (0, 127)
    assert (bank.toe[0].vel_lo, bank.toe[-1].vel_hi) == (0, 127)
