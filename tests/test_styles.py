"""S1 : invariants et erreurs réellement observables des mesures par style."""

from __future__ import annotations

import io

import mido

from harmonium_lab.backing.chords import from_engine
from harmonium_lab.styles.core import ChordSpan, Note, Piece, read_midi
from harmonium_lab.styles.harmony import infer_chords, parse_harte
from harmonium_lab.styles.measure import BassAcc, CompAcc, SyncAcc
from harmonium_lab.styles.sources.lmd import assign_style


def test_midi_reader_handles_first_signature_and_changes() -> None:
    midi = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    track.extend(
        [
            mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0),
            mido.Message("note_on", note=45, velocity=87, channel=0, time=0),
            mido.Message("note_off", note=45, channel=0, time=480),
            mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0),
        ]
    )
    out = io.BytesIO()
    midi.save(file=out)
    parsed = read_midi(out.getvalue())
    assert (parsed.numerator, parsed.denominator, parsed.signature_changes) == (3, 4, 1)
    assert parsed.tracks[0].notes[0] == Note(0.0, 1.0, 45, 87)


def test_bass_approach_and_chord_degree_and_repetition() -> None:
    c = from_engine(0, 0, "7")
    d = from_engine(2, 2, "m7")
    notes = [
        Note(b * 4 + i, 0.85, (36, 40, 43, 37)[i], 70 + i * 5)
        for b in range(8)
        for i in range(4)
    ]
    # Une seule pièce ne fait jamais paraître une mesure du corpus dans les « top patterns ».
    piece = Piece(
        "fixture",
        "one",
        ["swing"],
        120.0,
        bass=notes,
        chords=[ChordSpan(0, 32, c), ChordSpan(32, 64, d)],
    )
    acc = BassAcc()
    assert acc.add(piece)
    stats = acc.summary()
    assert stats["degrees"]["downbeat"]["root"] == 1.0
    assert stats["notes_per_bar"]["mean"] == 4.0
    assert stats["repetition_rhythm"]["lag_1"]["same_share"] == 1.0
    assert stats["rhythm_patterns"] == []
    assert stats["approach_to_next_chord"]["n"] == 1
    assert stats["approach_to_next_chord"]["semitone_below"] == 1.0


def test_comping_voicings_and_anticipation_and_ghost_notes() -> None:
    chord = from_engine(0, 0, "maj7")
    comp = []
    for b in range(8):
        for off in (1.0, 3.5):
            comp.extend(
                [
                    Note(b * 4 + off, 0.15, pitch, vel)
                    for pitch, vel in ((60, 60), (64, 90), (71, 100))
                ]
            )
    piece = Piece(
        "fixture", "comp", ["pop"], 120.0, comp=comp, chords=[ChordSpan(0, 32, chord)]
    )
    acc = CompAcc()
    assert acc.add(piece)
    stats = acc.summary()
    assert stats["notes_per_attack"]["shares"]["3"] == 1.0
    assert stats["voicing_vs_chord"]["third_and_seventh"] == 1.0
    assert stats["anticipation_share"]["value"] == 0.5
    assert stats["voicing_stacks"]["top"][0]["gaps"] == "4,7"


def test_sync_offsets_positive_means_bass_late() -> None:
    bass = [Note(b * 4 + 0.05, 0.5, 36) for b in range(16)]
    drums = [Note(b * 4, 0.1, 36) for b in range(16)]
    piece = Piece(
        "fixture", "sync", ["rock"], 120.0, bass=bass, drums=drums, quantized=False
    )
    acc = SyncAcc()
    assert acc.add(piece)
    stat = acc.summary()
    assert stat["bass_minus_kick_ms"]["n"] == 16
    assert stat["bass_minus_kick_ms"]["p50"] == 25.0
    assert stat["informative"] is True


def test_inferred_chord_is_marked_and_bass_degree_not_empty() -> None:
    comp = [Note(b * 4, 1.0, p) for b in range(8) for p in (60, 64, 67)]
    bass = [Note(b * 4, 0.8, 36) for b in range(8)]
    piece = Piece("fixture", "infer", ["reggae"], 120.0, bass=bass, comp=comp)
    piece.chords = infer_chords(piece, comp, bass=bass)
    piece.chords_inferred = True
    acc = BassAcc()
    assert acc.add(piece)
    stat = acc.summary()
    assert stat["chords"]["inferred_pieces"] == 1
    assert stat["degrees"]["downbeat"]["root"] == 1.0


def test_style_classifier_never_calls_generic_latin_bossa() -> None:
    assert assign_style({"Latin"}, set(), {}, 4, False, 120.0, "straight") is None
    assert (
        assign_style({"Latin"}, set(), {"bossa nova": 90}, 4, False, 120.0, "straight")
        == "bossa"
    )
    assert assign_style({"Jazz"}, set(), {}, 3, False, 170.0, "ternary") == "jazz_waltz"
    assert assign_style({"Blues"}, set(), {}, 4, False, 120.0, "straight") is None
    assert (
        assign_style({"Blues"}, set(), {}, 4, False, 120.0, "ternary")
        == "blues_shuffle"
    )
    assert parse_harte("N") is None
    assert parse_harte("C:7(b9)").relative(1) == 1


def test_pop909_annotated_downbeats_override_misleading_one_four_midi(tmp_path) -> None:
    """Dans la vraie archive, 617 MIDI sont en 1/4 alors que les temps annotés font du 4/4."""
    import zipfile

    from harmonium_lab.styles.sources.pop909 import pieces

    midi = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    track.name = "PIANO"
    midi.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=1, denominator=4))
    for _ in range(40):
        track.append(mido.Message("note_on", note=60, velocity=72, time=0))
        track.append(mido.Message("note_off", note=60, time=480))
    raw = io.BytesIO()
    midi.save(file=raw)
    path = tmp_path / "mini.zip"
    beats = "".join(
        f"{i / 2:.4f} 0.0 {1.0 if i % 4 == 0 else 0.0:.1f}\n" for i in range(40)
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("POP909/001/001.mid", raw.getvalue())
        archive.writestr("POP909/001/beat_midi.txt", beats)
        archive.writestr("POP909/001/chord_midi.txt", "0.0\t20.0\tC:maj\n")
    piece = list(pieces(path))[0]
    assert piece.beats_per_bar == 4.0
    assert piece.comp[0].on == 0.0
    assert piece.chords[0].chord.root == 0
