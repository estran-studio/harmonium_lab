"""DS-T9 : invariants observables sur de courtes transcriptions ABC et MIDI."""
from pathlib import Path

import mido
import pytest

from harmonium_lab.trad.structure import (
    abc_material, analyze_materials, engine_material, letter_structure,
    motif, rhythm_cell, transformations,
)


@pytest.fixture
def abc():
    def build(body: str, meter: str = "4/4") -> str:
        return f"X:1\nT:Fixture structure\nM:{meter}\nL:1/8\nK:C\n{body}\n"
    return build


def first_motif(text):
    m = abc_material(text)
    return motif([m.rhythm_bars[0]], m.tonic, m.mode, m.length)


@pytest.mark.parametrize("source,target,expected", [
    ("CDEF GABc", "CDEF GABc", {"exact"}),
    ("CDEF GABc", "DEFG ABcd", {"sequence"}),
    ("CDEF GABc", "CDEF G2C2", {"varied_ending"}),
    ("CDEF GABc", "cBAG FEDC", {"inversion"}),
    ("C2D2 E2F2", "CD E2F4", {"rhythmic_variation"}),
    ("CDEF GABc", "G2G2 E2C2", set()),
])
def test_transformations_from_abc(abc, source, target, expected):
    assert set(transformations(first_motif(abc(source + "|")), first_motif(abc(target + "|")))) == expected


def test_chromatic_notes_are_not_collapsed(abc):
    assert transformations(first_motif(abc("CDEF GABc|")), first_motif(abc("^CDEF GABc|"))) == []


def test_octave_boundary_sequence(abc):
    assert transformations(first_motif(abc("G,2A,2 B,2C2|")), first_motif(abc("A,2B,2 C2D2|"))) == ["sequence"]


def test_a_aprime_b_c_and_repeat_denominator(abc):
    text = abc("|: CDEF GABc|cBAG FEDC|CDEF GABc|cBAG F2C2|E2E2 G2G2|c4z4|G3E G2C2|C8 :|")
    m = abc_material(text)
    pairs = [motif(m.parts[0][1][i:i+2], m.tonic, m.mode, m.length) for i in range(0, 8, 2)]
    assert letter_structure(pairs) == "a a' b c"
    stats = analyze_materials([m])
    assert stats["parts"] == {"A": 1, "all": 1}
    assert stats["structures"] == [{"pattern": "a a' b c", "count": 1, "share": 1.0, "tune_count": 1, "tune_share": 1.0}]
    assert stats["transformations"]["A:m3-4/m1-2"]["rates"]["varied_ending"] == 1.0
    assert stats["rhythm"]["counts"]["bars"] == 8


def test_phrase_and_b_link(abc):
    a = "CDEF GABc|cBAG FEDC|E2F2 G2A2|G8|CDEF GABc|cBAG FEDC|G2E2 D2B,2|C8"
    b = "G2E2 D2B,2|C8|E8|F8|G8|A8|B8|C8"
    stats = analyze_materials([abc_material(abc(f"|:{a}:|:{b}:|"))])
    assert stats["phrases"]["antecedent_consequent_rate"] == .5
    assert stats["phrases"]["opening_reprise_rate"] == .5
    assert stats["phrases"]["b_reuses_a_ending_rate"] == 1
    assert stats["transformations"]["B:m1-2/A:m7-8"]["rates"]["exact"] == 1
    assert stats["phrases"]["rest_by_position"]["A:m4"]["tonic_cadence_rate"] == 0
    assert stats["phrases"]["rest_by_position"]["A:m8"]["tonic_cadence_rate"] == 1


def test_triplets_accents_repeated_notes_and_syncopation(abc):
    m = abc_material(abc("!accent!(3eee e2 e2 e2|C D3 E4|CDEF GABc|", "4/4"))
    stats = analyze_materials([m])["rhythm"]
    assert stats["counts"]["repeated_triplets"] == 1
    assert stats["counts"]["syncopated_bars"] == 1
    assert stats["continuous_eighth_rate"] == pytest.approx(1/3, abs=1e-6)
    assert stats["accents"]["onsets"] == [{"pattern": "0", "count": 1, "share": 1.0}]
    assert stats["top20"][0]["count"] == 1
    assert stats["entropy_bits"] == pytest.approx(1.584963)
    assert rhythm_cell(m.rhythm_bars[0], 8) == "2/3 2/3 2/3 2 2 2"


def test_rests_are_distinct_from_held_notes(abc):
    held = abc_material(abc("C4D4|"))
    silent = abc_material(abc("C2z2D4|"))
    assert rhythm_cell(held.rhythm_bars[0], 8) == "4 4"
    assert rhythm_cell(silent.rhythm_bars[0], 8) == "2 z2 4"


def test_voltas_pickups_and_non8_parts(abc):
    first = "CDEF GABc|cBAG FEDC|E2F2 G2A2|G8|CDEF GABc|cBAG FEDC|"
    material = abc_material(abc(f"|:{first}[1 G2E2 D2B,2|C8 :|[2 C8|C8|"))
    assert len(material.parts) == 1
    assert material.parts[0][1][6][0].pitch == 67  # première fin, pas seconde
    pickup = abc_material(abc("G2|:C8|D8|E8|F8|G8|A8|B8|C6:|"))
    assert len(pickup.parts[0][1]) == 8
    assert pickup.parts[0][1][-1][-1].onset == 6
    crooked = abc_material(abc("|:C8|D8|E8|F8|G8|A8|B8:|"))
    assert crooked.parts == []
    assert analyze_materials([crooked])["phrases"]["opening_reprise_rate"] is None


def test_matrices_compare_pitch_and_rhythm_separately(abc):
    m = abc_material(abc("|:C2D2 E2F2|CD E2F4|G8|A8|B8|c8|d8|e8:|"))
    matrix = analyze_materials([m])["similarity"]["A"]
    assert matrix["pitch"][0][1] == 1
    assert matrix["rhythm"][0][1] == 0
    assert matrix["joint"][0][0] == 1
    assert matrix["pitch"][0][2] == matrix["pitch"][2][0] == 0


@pytest.mark.parametrize("drift_ticks_per_bar", [0, 2])
def test_engine_gate_swing_and_clock_drift_do_not_destroy_copy(tmp_path: Path, drift_ticks_per_bar):
    import json
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
    track.append(mido.MetaMessage("key_signature", key="C"))
    events = []
    # Même cellule de 8 croches à chaque mesure ; gate variable et swing 56%.
    for bar in range(36):
        for i in range(8):
            tick = bar * 1920 + i * 240 + (29 if i % 2 else 0) - bar * drift_ticks_per_bar
            events += [(tick, True, 60 + i), (tick + 80 + (bar % 3) * 10, False, 60 + i)]
    last = 0
    for tick, on, pitch in sorted(events):
        track.append(mido.Message("note_on" if on else "note_off", channel=0, note=pitch, velocity=90 if on else 0, time=tick-last))
        last = tick
    path = tmp_path / "seed1.mid"
    mid.save(path)
    path.with_suffix(".json").write_text(json.dumps([{"session_key":"C", "session_scale":"Ionian"}]))
    material = engine_material(path, "reel")
    stats = analyze_materials([material])
    assert material.key_source == "record-truth"
    assert stats["excluded_engine_tail_bars"] == 4
    assert stats["phrases"]["opening_reprise_rate"] == 1
    assert stats["rhythm"]["continuous_eighth_rate"] == 1
    assert stats["rhythm"]["entropy_bits"] == 0


def test_cli_rejects_missing_corpus(tmp_path: Path):
    from harmonium_lab.cli import main
    assert main(["trad-structure", "--corpus", str(tmp_path), "--type", "reel"]) == 1


@pytest.mark.parametrize("intro_bars", [1, 2])
def test_engine_excludes_sounding_intro_without_assuming_internal_copy(tmp_path: Path, intro_bars):
    import json
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
    track.append(mido.MetaMessage("key_signature", key="C"))
    a, b = list(range(60, 68)), list(range(72, 80))
    pitches = [48+i for i in range(intro_bars)] + a + a + b + b + [90, 91]
    for pitch in pitches:
        track.append(mido.Message("note_on", channel=0, note=pitch, velocity=90, time=0))
        track.append(mido.Message("note_off", channel=0, note=pitch, velocity=0, time=1920))
    path = tmp_path / "seed.mid"
    mid.save(path)
    path.with_suffix(".json").write_text(json.dumps([{"session_key":"", "session_scale":""}]))
    path.with_suffix(".log").write_text("  Tune 1 (bars 1..=96): D Ionian\n")
    material = engine_material(path, "reel")
    stats = analyze_materials([material])
    assert material.intro_bars == intro_bars
    assert material.alignment_score == 16
    assert material.alignment_candidates == 1
    assert material.tonic == 2
    assert material.key_source == "export-log"
    assert stats["phrases"]["opening_reprise_rate"] == 0
    assert stats["excluded_engine_tail_bars"] == 2
    assert [bar[0].pitch for bar in material.parts[0][1]] == a


def test_engine_alignment_follows_published_intro_when_candidates_tie(tmp_path: Path):
    """Bars all identical : tous les décalages égalent 16/16 ; sans vérité on retient le premier, avec elle l'intro publiée."""
    import json
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
    track.append(mido.MetaMessage("key_signature", key="C"))
    for _ in range(36):
        track.append(mido.Message("note_on", channel=0, note=60, velocity=90, time=0))
        track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=1920))
    plain, published = tmp_path / "plain.mid", tmp_path / "published.mid"
    mid.save(plain)
    mid.save(published)
    plain.with_suffix(".json").write_text(json.dumps([{"session_key": "C", "session_scale": "Ionian"}]))
    sections = ["Intro", "Intro"] + ["Tour"] * 34
    truth = {"reports": [{"session_key": "C", "session_scale": "Ionian"}],
             "measures": [{"measure": {"index": i + 1, "position": {"section": section}}} for i, section in enumerate(sections)]}
    published.with_suffix(".json").write_text(json.dumps(truth))
    unaligned = engine_material(plain, "reel")
    assert (unaligned.intro_bars, unaligned.alignment_candidates) == (0, 5)
    material = engine_material(published, "reel")
    assert (material.intro_bars, material.alignment_candidates, material.alignment_score) == (2, 1, 16)
