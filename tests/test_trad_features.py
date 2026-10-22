"""Tests DS-T3 : statistiques trad (D5) sur fixtures, sans réseau.

Fixtures (tests/fixtures/trad/) : un reel AABB en ré majeur avec accords,
une gigue 6/8, une valse 3/4, un air « croche ». Le MIDI moteur (5 canaux)
est généré par le test via mido.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harmonium_lab.trad import (
    build_profile,
    features,
    load_abc,
    load_engine_midi,
    load_profile,
    save_profile,
)

FIXTURES = Path(__file__).parent / "fixtures" / "trad"


@pytest.fixture
def reel() -> dict:
    return features(load_abc(FIXTURES / "reel_dmajor.abc"))


@pytest.fixture
def jig() -> dict:
    return features(load_abc(FIXTURES / "jig_gmajor.abc"))


@pytest.fixture
def waltz() -> dict:
    return features(load_abc(FIXTURES / "waltz_dmajor.abc"))


@pytest.fixture
def crooked() -> dict:
    return features(load_abc(FIXTURES / "crooked_reel.abc"))


def make_engine_midi(path: Path) -> Path:
    """MIDI minimal au format du moteur : 5 canaux (0-4), 2/2, sans tonalité."""
    import mido

    ticks_per_beat = 480
    eighth = ticks_per_beat // 2
    bar_ticks = ticks_per_beat * 2 * 4 // 2  # 2/2 : 8 croches = 1920 ticks
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(115), time=0))
    track.append(
        mido.MetaMessage("time_signature", numerator=2, denominator=2, time=0)
    )

    events: list[tuple[int, str, int, int, int]] = []

    def note(start: int, channel: int, pitch: int, duration: int, vel: int = 90):
        events.append((start, "note_on", channel, pitch, vel))
        events.append((start + duration, "note_off", channel, pitch, 0))

    melody = [62, 66, 69, 66, 62, 66, 69, 66, 67, 69, 71, 69, 67, 69, 71, 73]
    for i, pitch in enumerate(melody):
        bar, slot = divmod(i, 8)
        note(bar * bar_ticks + slot * eighth, 0, pitch, eighth)
    triads = {(0, 0): [62, 66, 69], (0, 4 * eighth): [57, 61, 64],
              (1, 0): [55, 59, 62], (1, 4 * eighth): [62, 66, 69]}
    for (bar, offset), pitches in triads.items():
        for pitch in pitches:
            note(bar * bar_ticks + offset, 1, pitch, 4 * eighth, vel=80)
    for bar, offset, root in [(0, 0, 38), (0, 4 * eighth, 33),
                              (1, 0, 43), (1, 4 * eighth, 38)]:
        note(bar * bar_ticks + offset, 2, root, 4 * eighth, vel=85)
    for step in (0, 4, 8, 12):  # talon
        note(step * eighth, 3, 36, eighth // 2)
    for step in (2, 6, 10, 14):  # pointe
        note(step * eighth, 4, 37, eighth // 2)

    events.sort(key=lambda e: (e[0], e[1] == "note_off"))
    tick = 0
    for time, kind, channel, pitch, vel in events:
        track.append(
            mido.Message(kind, channel=channel, note=pitch,
                         velocity=vel, time=time - tick)
        )
        tick = time
    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(str(path))
    return path


# ---------------------------------------------------------------------------
# Reel fixture : AABB, cadences, cellule, registre
# ---------------------------------------------------------------------------


class TestReelFixture:
    def test_aabb_detected(self, reel: dict) -> None:
        assert reel["n_bars"] == 32
        assert reel["form"]["is_aabb"] is True
        assert reel["form"]["repeat_identity"] == 1.0
        assert reel["form"]["share_identical_bars_5_6_vs_1_2"] == 1.0

    def test_cadences(self, reel: dict) -> None:
        assert reel["cadences"]["part0_m4"] == 5  # demi-cadence sur la dominante
        assert reel["cadences"]["part0_m8"] == 1  # cadence sur la tonique

    def test_first_cell_exact(self, reel: dict) -> None:
        assert reel["cells"]["per_bar"][0] == "1 3 5 3 1 3 5 3"

    def test_register_b_above_a(self, reel: dict) -> None:
        assert reel["register"]["b_minus_a_mean_pitch"] > 0

    def test_no_crooked_flag(self, reel: dict) -> None:
        assert reel["flags"]["has_croche_bars"] is False

    def test_harmony_vocab(self, reel: dict) -> None:
        counts = reel["harmony"]["chord_degree_counts"]
        assert counts["I"] > 0 and counts["V"] > 0
        assert reel["harmony"]["chords_per_bar"] > 0
        assert any("I->" in b for b in reel["harmony"]["chord_bigrams"])


# ---------------------------------------------------------------------------
# Gigue / valse : quantisation 6 croches
# ---------------------------------------------------------------------------


class TestJigFixture:
    def test_six_eighths(self, jig: dict) -> None:
        assert jig["meter"] == "6/8"
        assert jig["eighths_per_bar"] == 6
        assert all(len(c.split()) == 6 for c in jig["cells"]["per_bar"])

    def test_cadences(self, jig: dict) -> None:
        assert jig["cadences"]["part0_m4"] == 5
        assert jig["cadences"]["part0_m8"] == 1


class TestWaltzFixture:
    def test_six_eighths(self, waltz: dict) -> None:
        assert waltz["meter"] == "3/4"
        assert waltz["eighths_per_bar"] == 6
        assert all(len(c.split()) == 6 for c in waltz["cells"]["per_bar"])

    def test_cadences(self, waltz: dict) -> None:
        assert waltz["cadences"]["part0_m4"] == 5
        assert waltz["cadences"]["part0_m8"] == 1


# ---------------------------------------------------------------------------
# Air croche : marqué, pas planté
# ---------------------------------------------------------------------------


class TestCrookedFixture:
    def test_flagged_not_crashed(self, crooked: dict) -> None:
        assert crooked["flags"]["has_croche_bars"] is True
        assert len(crooked["flags"]["croche_bars"]) > 0
        # Le reste des stats est calculé malgré tout.
        assert crooked["n_bars"] > 0
        assert crooked["cells"]["per_bar"][0] == "1 3 5 3 1 3 5 3"


# ---------------------------------------------------------------------------
# MIDI moteur : piste mélodique, accords, repli Krumhansl
# ---------------------------------------------------------------------------


class TestEngineMidi:
    def test_melody_channel(self, tmp_path: Path) -> None:
        tune = load_engine_midi(make_engine_midi(tmp_path / "engine.mid"))
        assert tune.meter == "2/2"
        assert tune.eighths_per_bar == 8
        assert [n.pitch for n in tune.bars[0]] == [62, 66, 69, 66, 62, 66, 69, 66]
        assert [n.pitch for n in tune.bars[1]][:4] == [67, 69, 71, 69]

    def test_chords_and_key_fallback(self, tmp_path: Path) -> None:
        tune = load_engine_midi(make_engine_midi(tmp_path / "engine.mid"))
        symbols = [s for bar in tune.chords for _, s in bar]
        assert symbols == ["D", "A", "G", "D"]
        # Sans méta-tonalité : estimation Krumhansl.
        assert (tune.key_name, tune.mode) == ("D", "ionian")

    def test_features_run(self, tmp_path: Path) -> None:
        feat = features(load_engine_midi(make_engine_midi(tmp_path / "engine.mid")))
        assert feat["n_bars"] == 2
        assert feat["cells"]["per_bar"][0] == "1 3 5 3 1 3 5 3"

    def test_voicing_change_without_chord_change_does_not_count_as_change(
        self, tmp_path: Path
    ) -> None:
        """Un voicing qui change sans changement d'accord ne compte pas comme changement."""
        import mido

        path = tmp_path / "voicing_test.mid"
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(
            mido.MetaMessage("time_signature", numerator=2, denominator=2, time=0)
        )
        bar_ticks = 480 * 2 * 4 // 2
        eighth = 240

        # Bar 0 : 3 voicings de D majeur (offset 0, 2, 4)
        # Bar 1 : 1 voicing de D majeur (offset 0), puis G majeur (offset 4)
        events = []
        def add_chord(t: int, pitches: list[int]):
            for p in pitches:
                events.append((t, "note_on", 1, p, 80))
                events.append((t + eighth, "note_off", 1, p, 0))

        add_chord(0, [62, 66, 69])  # D root
        add_chord(2 * eighth, [66, 69, 74])  # D 1st inv
        add_chord(4 * eighth, [57, 62, 66])  # D 2nd inv
        add_chord(bar_ticks, [50, 57, 66])  # D open
        add_chord(bar_ticks + 4 * eighth, [55, 59, 62])  # G root

        events.sort(key=lambda e: (e[0], e[1] == "note_off"))
        cur = 0
        for t, kind, ch, p, v in events:
            track.append(mido.Message(kind, channel=ch, note=p, velocity=v, time=t - cur))
            cur = t
        track.append(mido.MetaMessage("end_of_track", time=0))
        mid.save(str(path))

        tune = load_engine_midi(path)
        symbols = [s for bar in tune.chords for _, s in bar]
        assert symbols == ["D", "G"]
        feat = features(tune)
        assert feat["harmony"]["n_chords"] == 2
        assert feat["harmony"]["chords_per_bar"] == 1.0

    def test_load_engine_midi_with_record_truth(self, tmp_path: Path) -> None:
        """Quand le fichier de vérité (--record-truth) est présent, ses accords sont lus."""
        import json
        import mido

        mid_path = tmp_path / "truth_test.mid"
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("time_signature", numerator=2, denominator=2, time=0))
        track.append(mido.Message("note_on", channel=0, note=62, velocity=80, time=0))
        track.append(mido.Message("note_off", channel=0, note=62, velocity=0, time=1920 * 4))
        mid.save(str(mid_path))

        truth_path = tmp_path / "truth_test.json"
        truth_data = [
            {"bar": 1, "step": 0, "chord": "D"},
            {"bar": 1, "step": 8, "chord": "D"},
            {"bar": 2, "step": 0, "chord": "D"},
            {"bar": 3, "step": 0, "chord": "G"},
            {"bar": 4, "step": 0, "chord": "D"},
        ]
        truth_path.write_text(json.dumps(truth_data), encoding="utf-8")

        tune = load_engine_midi(mid_path)
        symbols = [s for bar in tune.chords for _, s in bar]
        assert symbols == ["D", "G", "D"]
        assert tune.chords[0] == [(0.0, "D")]
        assert tune.chords[1] == []
        assert tune.chords[2] == [(0.0, "G")]
        assert tune.chords[3] == [(0.0, "D")]

# ---------------------------------------------------------------------------
# Profil par type + CLI
# ---------------------------------------------------------------------------


class TestTradProfile:
    def test_build_profile(self, reel: dict, jig: dict) -> None:
        from harmonium_lab.trad import load_abc as _load

        tunes = [_load(FIXTURES / "reel_dmajor.abc"), _load(FIXTURES / "jig_gmajor.abc")]
        profile = build_profile(tunes, tune_type="test")
        assert profile["tune_count"] == 2
        assert profile["version"] == 1
        s = profile["scalars"]["register__b_minus_a_mean_pitch"]
        assert s["count"] == 2 and s["mean"] > 0
        assert profile["cell_frequencies"]["1 3 5 3 1 3 5 3"] > 0
        assert any("I->" in b for b in profile["chord_bigram_frequencies"])
        assert profile["histograms"]["interval_hist"]["count"] == 2

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        from harmonium_lab.trad import load_abc as _load

        tunes = [_load(FIXTURES / "reel_dmajor.abc")]
        profile = build_profile(tunes, tune_type="reel")
        out = tmp_path / "profile.json"
        save_profile(profile, out)
        assert load_profile(out) == profile

    def test_cli_trad_profile(self, tmp_path: Path) -> None:
        import shutil

        from harmonium_lab.cli import main

        corpus = tmp_path / "corpus" / "trad" / "tunes" / "reel"
        corpus.mkdir(parents=True)
        shutil.copy(FIXTURES / "reel_dmajor.abc", corpus / "reel_dmajor.abc")
        out = tmp_path / "profile.json"
        rc = main(["trad-profile", "--type", "reel",
                   "--corpus", str(tmp_path / "corpus" / "trad"),
                   "-o", str(out)])
        assert rc == 0
        profile = load_profile(out)
        assert profile["tune_type"] == "reel"
        assert profile["tune_count"] == 1
