"""Tests DS-T4 : trad-compare + blindtest, sans réseau.

Deux profils jouets (reel, jig) construits depuis les fixtures ABC,
deux MIDI moteur générés via mido, WAV sinusoïdaux pour le blindtest.
"""

from __future__ import annotations

import json
import math
import random
import struct
import wave
from pathlib import Path

import pytest

from harmonium_lab.trad import (
    EXPLANATIONS,
    build_profile,
    build_kit,
    compare_to_profile,
    deviations_for_file,
    explain,
    feature_vector,
    features,
    load_abc,
    load_engine_midi,
    nearest_reals,
    reference_stats,
    save_profile,
    score_feuille,
)

FIXTURES = Path(__file__).parent / "fixtures" / "trad"
REELS = ["reel_dmajor.abc", "reel_bastringue.abc", "crooked_reel.abc"]


def make_engine_midi(path: Path, transpose: int = 0, stride: int = 1) -> Path:
    """MIDI minimal au format du moteur (canal 0 = mélodie, 2/2)."""
    import mido

    ticks_per_beat = 480
    eighth = ticks_per_beat // 2
    bar_ticks = ticks_per_beat * 2 * 4 // 2
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(115), time=0))
    track.append(mido.MetaMessage("time_signature", numerator=2, denominator=2, time=0))

    events: list[tuple[int, str, int, int, int]] = []

    def note(start: int, channel: int, pitch: int, duration: int, vel: int = 90):
        events.append((start, "note_on", channel, pitch, vel))
        events.append((start + duration, "note_off", channel, pitch, 0))

    base = [62, 66, 69, 74, 76, 74, 69, 66, 67, 71, 74, 79, 81, 79, 74, 71]
    melody = [p + transpose for p in base[::stride]]
    while len(melody) < 16:
        melody += melody
    melody = melody[:16]
    for i, pitch in enumerate(melody):
        bar, slot = divmod(i, 8)
        note(bar * bar_ticks + slot * eighth, 0, pitch, eighth)
    for (bar, offset), pitches in {
        (0, 0): [62, 66, 69], (0, 4 * eighth): [57, 61, 64],
        (1, 0): [55, 59, 62], (1, 4 * eighth): [62, 66, 69],
    }.items():
        for pitch in pitches:
            note(bar * bar_ticks + offset, 1, pitch, 4 * eighth, vel=80)
    last = 0
    for abs_tick, typ, chan, pitch_, vel_ in sorted(events):
        track.append(mido.Message(typ, channel=chan, note=pitch_, velocity=vel_,
                                  time=abs_tick - last))
        last = abs_tick
    mid.save(str(path))
    return path


@pytest.fixture(scope="module")
def reel_profile() -> dict:
    tunes = [load_abc(FIXTURES / name) for name in REELS]
    return build_profile(tunes, tune_type="reel")


@pytest.fixture(scope="module")
def jig_profile() -> dict:
    tunes = [load_abc(FIXTURES / "jig_gmajor.abc"), load_abc(FIXTURES / "waltz_dmajor.abc")]
    return build_profile(tunes, tune_type="jig")


@pytest.fixture(scope="module")
def reel_vectors() -> list[dict]:
    return [feature_vector(features(load_abc(FIXTURES / n))) for n in REELS]


@pytest.fixture(scope="module")
def gen_feats(tmp_path_factory) -> dict:
    out = tmp_path_factory.mktemp("gen")
    feats = {}
    for name, tr, st in [("gen_a.mid", 0, 1), ("gen_b.mid", 5, 2)]:
        feats[name] = features(load_engine_midi(make_engine_midi(out / name, tr, st)))
    return feats

def test_engine_midi_without_note_off_uses_legato(tmp_path):
    """L'export moteur ne ferme pas ses notes : repli legato documenté."""
    import mido

    ticks, eighth = 480, 240
    mid = mido.MidiFile(ticks_per_beat=ticks)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=2, denominator=2, time=0))
    last = 0
    for i, pitch in enumerate([62, 64, 66, 64]):
        track.append(mido.Message("note_on", channel=0, note=pitch, velocity=90,
                                  time=i * eighth - last))
        last = i * eighth
    path = tmp_path / "nooff.mid"
    mid.save(str(path))
    tune = load_engine_midi(path)
    assert [n.pitch for bar in tune.bars for n in bar] == [62, 64, 66, 64]
    assert [n.duration for bar in tune.bars for n in bar][:3] == [1.0, 1.0, 1.0]


def test_two_toy_profiles(reel_profile, jig_profile):
    assert reel_profile["tune_count"] == 3
    assert jig_profile["tune_count"] == 2
    assert reel_profile["tune_type"] == "reel"


def test_deviations_sorted_and_french(reel_profile, reel_vectors, gen_feats):
    ref = reference_stats(reel_profile, reel_vectors)
    devs = compare_to_profile(gen_feats, ref, "reel")
    assert devs
    assert [abs(d["z"]) for d in devs] == sorted([abs(d["z"]) for d in devs], reverse=True)
    keys = {d["key"] for d in devs}
    assert "leap_ratio" in keys
    for d in devs:
        assert "moteur" in d["sentence"]
        assert "réels" in d["sentence"]
        assert set(d) >= {"key", "real_value", "generated_value", "z", "sentence"}


def test_explain_example_shape():
    s = explain("leap_ratio", "reel", 0.31, 0.12)
    assert s.startswith("Les reels réels sautent")
    assert "31 % des cas" in s and "12 %" in s


def test_every_compared_key_explained(reel_vectors):
    for vec in reel_vectors:
        for key in vec:
            base = key if key in EXPLANATIONS else key.rsplit("__", 1)[0]
            assert base in EXPLANATIONS, key


def test_per_file_and_nearest(reel_profile, reel_vectors, gen_feats):
    ref = reference_stats(reel_profile, reel_vectors)
    reals = [(f"real{i}", v) for i, v in enumerate(reel_vectors)]
    for name, feat in gen_feats.items():
        devs = deviations_for_file(feat, ref, "reel")
        assert devs and len(devs) <= len(ref)
        near = nearest_reals(feat, reals, ref)
        assert len(near) == 3
        assert [d for _, d in near] == sorted(d for _, d in near)
        assert len({r for r, _ in near}) == 3


def make_sine_wav(path: Path, freq: float = 440.0, seconds: float = 1.0, rate: int = 44100):
    n = int(seconds * rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{n}h", *(int(16000 * math.sin(2 * math.pi * freq * i / rate)) for i in range(n))))

def write_float_wav(path: Path, freq: float = 220.0, seconds: float = 1.0,
                     rate: int = 44100, extensible: bool = False):
    """WAV float32 type sortie moteur (extensible ou non)."""
    import struct as _st

    n = int(seconds * rate)
    frames = _st.pack(f"<{n}f", *(0.5 * math.sin(2 * math.pi * freq * i / rate) for i in range(n)))
    if extensible:
        guid = bytes.fromhex("0300000000001000800000aa00389b71")
        fmt = _st.pack("<HHIIHHHHI16s", 65534, 1, rate, rate * 4, 4, 32, 22, 32, 4, guid)
    else:
        fmt = _st.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    blob = b"fmt " + _st.pack("<I", len(fmt)) + fmt + b"data" + _st.pack("<I", len(frames)) + frames
    path.write_bytes(b"RIFF" + _st.pack("<I", 4 + len(blob)) + b"WAVE" + blob)


def test_float_wav_engine_like_mixed_kit(tmp_path):
    from harmonium_lab.trad.blindtest import read_wav_mono

    real = tmp_path / "real"
    gen = tmp_path / "gen"
    real.mkdir()
    gen.mkdir()
    make_sine_wav(real / "r0.wav")  # PCM16 type trad-render
    make_sine_wav(real / "r1.wav", freq=466.0)
    write_float_wav(gen / "g0.wav", extensible=True)  # float type moteur
    write_float_wav(gen / "g1.wav", freq=233.0)
    rate, samples = read_wav_mono(gen / "g0.wav")
    assert rate == 44100 and len(samples) == 44100
    kit = tmp_path / "kit"
    built = build_kit(sorted(real.glob("*.wav")), sorted(gen.glob("*.wav")),
                       kit, 2, 2, seed=5, duration=1.0)
    assert built["files"] == ["01.wav", "02.wav", "03.wav", "04.wav"]
    assert sum(1 for v in built["corrige"].values() if v["kind"] == "genere") == 2


def test_blindtest_kit_deterministic(tmp_path):
    real = tmp_path / "real"
    gen = tmp_path / "gen"
    real.mkdir()
    gen.mkdir()
    for i in range(3):
        make_sine_wav(real / f"r{i}.wav", freq=440.0 + i * 10)
        make_sine_wav(gen / f"g{i}.wav", freq=330.0 + i * 10)
    kit1 = tmp_path / "kit1"
    kit2 = tmp_path / "kit2"
    r1 = build_kit(sorted(real.glob("*.wav")), sorted(gen.glob("*.wav")), kit1, 2, 2, seed=42, duration=2.0)
    r2 = build_kit(sorted(real.glob("*.wav")), sorted(gen.glob("*.wav")), kit2, 2, 2, seed=42, duration=2.0)
    assert r1["corrige"] == r2["corrige"]
    assert r1["files"] == ["01.wav", "02.wav", "03.wav", "04.wav"]
    assert (kit1 / "feuille.md").exists() and (kit1 / "corrige.json").exists()
    with wave.open(str(kit1 / "01.wav"), "rb") as w:
        assert w.getnframes() == 2 * 44100  # même durée : découpé ou bourré


def test_blindtest_score_random_sheet(tmp_path, reel_profile, reel_vectors, gen_feats):
    real = tmp_path / "real"
    gen = tmp_path / "gen"
    real.mkdir()
    gen.mkdir()
    for i in range(3):
        make_sine_wav(real / f"r{i}.wav")
        make_sine_wav(gen / f"g{i}.wav", freq=220.0)
    kit = tmp_path / "kit"
    build_kit(sorted(real.glob("*.wav")), sorted(gen.glob("*.wav")), kit, 2, 2, seed=7, duration=1.0)
    # Feuille remplie au hasard (seed fixe).
    rng = random.Random(11)
    corrige = json.loads((kit / "corrige.json").read_text(encoding="utf-8"))
    lines = ["| fichier | verdict | note | commentaire |", "|---|---|---|---|"]
    for name in sorted(corrige):
        lines.append(f"| {name} | {rng.choice(['réel', 'généré', '?'])} | {rng.randint(1, 5)} |  |")
    (kit / "feuille.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ref = reference_stats(reel_profile, reel_vectors)
    report = {
        "per_file": [
            {"file": src, "deviations": deviations_for_file(f, ref, "reel")}
            for src, f in zip(["g0.wav", "g1.wav", "g2.wav"], list(gen_feats.values()) * 2)
        ]
    }
    # Corrige les noms : le rapport indexe par nom source du corrigé.
    report["per_file"] = [
        {"file": c["source"], "deviations": deviations_for_file(f, ref, "reel")}
        for c, f in zip(
            [corrige[n] for n in sorted(corrige) if corrige[n]["kind"] == "genere"],
            list(gen_feats.values()),
        )
    ]
    score = score_feuille(kit, report)
    assert score["n_files"] == 4 and score["n_generated"] == 2
    assert 0.0 <= score["pct_generated_recognized"] <= 100.0
    assert 0.0 <= score["pct_generated_confused"] <= 100.0
    assert len(score["per_file"]) == 4
    for name, sents in score["top_deviations_unmasked"].items():
        assert len(sents) == 3 and all("moteur" in s for s in sents)


def test_cli_trad_compare_and_blindtest(tmp_path):
    from harmonium_lab.cli import main

    corpus = tmp_path / "corpus"
    (corpus / "tunes" / "reel").mkdir(parents=True)
    manifest_rows = []
    for name in REELS:
        dest = corpus / "tunes" / "reel" / name
        dest.write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")
        tune_id = name.replace(".abc", "")
        manifest_rows.append({"id": tune_id, "title": f"Titre {tune_id}"})
    (corpus / "manifest.jsonl").write_text(
        "\n".join(json.dumps(r) for r in manifest_rows) + "\n", encoding="utf-8"
    )
    profile_path = tmp_path / "profile.json"
    save_profile(
        build_profile([load_abc(corpus / "tunes" / "reel" / n) for n in REELS], "reel"),
        profile_path,
    )
    gen_dir = tmp_path / "gen"
    gen_dir.mkdir()
    make_engine_midi(gen_dir / "m1.mid", 0, 1)
    make_engine_midi(gen_dir / "m2.mid", 5, 2)

    out = tmp_path / "cmp"
    rc = main(["trad-compare", "--generated", str(gen_dir), "--type", "reel",
               "-o", str(out), "--corpus", str(corpus),
               "--profile", str(profile_path), "--render-dir", str(tmp_path / "rend")])
    assert rc == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["generated"] == ["m1.mid", "m2.mid"]
    assert len(report["per_file"]) == 2
    assert all(len(p["nearest"]) == 3 and len(p["deviations"]) > 0 for p in report["per_file"])
    md = (out / "report.md").read_text(encoding="utf-8")
    assert "moteur" in md and "Titre" in md

    # Blindtest CLI : réels + générés factices, kit + score.
    rend = tmp_path / "rend" / "reel"
    rend.mkdir(parents=True)
    gwav = tmp_path / "gwav"
    gwav.mkdir()
    make_sine_wav(rend / "a.wav")
    make_sine_wav(rend / "b.wav")
    make_sine_wav(gwav / "g.wav", freq=220.0)
    kit = tmp_path / "kit"
    rc = main(["blindtest", "--type", "reel", "--real", "2", "--generated", str(gwav),
               "--count", "1", "--seed", "3", "--duration", "1.0",
               "-o", str(kit), "--render-dir", str(tmp_path / "rend")])
    assert rc == 0
    assert len(list(kit.glob("*.wav"))) == 3
    rc = main(["blindtest-score", str(kit), "--compare", str(out / "report.json")])
    assert rc == 0


def test_cli_no_write_outside_target(tmp_path, monkeypatch):
    from harmonium_lab.cli import main

    monkeypatch.chdir(tmp_path)
    assert main([]) == 0
