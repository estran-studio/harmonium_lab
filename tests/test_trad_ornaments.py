"""Ornements ABC écrits : fixtures fabriquées, sans corpus ni accès réseau."""
import json
from fractions import Fraction

import pytest

from harmonium_lab.cli import main
from harmonium_lab.trad.ornaments import aggregate, extract_ornaments


def abc(body, meter="4/4", key="C"):
    return f"X:1\nT:Fixture\nM:{meter}\nL:1/8\nZ:Testeur\nK:{key}\n{body}\n"


@pytest.mark.parametrize(("body", "kind", "duration"), [
    ("{g}C8|", "grace_single", "8"),
    ("{gag}C8|", "grace_multiple", "8"),
    ("~C8|", "roll", "8"),
    ("!turn!C8|", "turn", "8"),
    ("(3CCC D6|", "triplet_repeated", "2/3"),
    ("(3CDE F6|", "triplet_melodic", "2/3"),
    ("[C2E2] G6|", "double_stop", "2"),
    ("[C,E,G]8|", "chord", "8"),
    ("TC8|", "trill", "8"),
    ("!trill!C8|", "trill", "8"),
    ("+trill+C8|", "trill", "8"),
    (".C8|", "staccato", "8"),
    ("HC8|", "fermata", "8"),
])
def test_each_written_type(body, kind, duration):
    measured = extract_ornaments(abc(body))
    assert [e["type"] for e in measured["events"]] == [kind]
    assert measured["events"][0]["duration_eighths"] == duration
    assert measured["bar_equivalents"] == 1


def test_carrier_context_and_broken_rhythm():
    measured = extract_ornaments(abc("C {g}E>G A4|"))
    event, = measured["events"]
    assert (event["beat"], event["beat_phase"], event["half_beat"]) == (1, "1/2", 1)
    assert event["duration_eighths"] == "3/2"
    assert (event["previous_interval"], event["next_interval"], event["degree"]) == (4, 3, 3)
    assert event["accidental_semitones"] == 0
    # Grace pitches are never included among carrier notes.
    assert len(measured["notes"]) == 4


def test_repeats_voltas_part_and_phrase_positions():
    a = "|:" + "C8|" * 3 + "{g}D8|" + "C8|" * 3 + "[1~E8:|[2!trill!F8||"
    b = "|:" + "G8|" * 7 + "{ag}c8:|"
    measured = extract_ornaments(abc(a + b))
    assert [(e["type"], e["part"], e["bar"], e["phrase_end"]) for e in measured["events"]] == [
        ("grace_single", "A", 4, True), ("roll", "A", 8, True),
        ("trill", "A", 8, True), ("grace_multiple", "B", 8, True),
    ]
    assert len(measured["notes"]) == 17  # both written endings, no playback duplicates
    assert measured["events"][2]["previous_interval"] == 5  # C -> F on second pass
    stats = aggregate([{**measured, "id": "fixture"}])
    eighth = stats["by_position"]["bar_position"]["8"]
    assert eighth["notes"] == 3
    assert eighth["bar_equivalents"] == 3
    assert eighth["by_type"]["roll"]["per_bar"] == pytest.approx(1 / 3, abs=1e-6)


def test_pickup_completes_final_bar_without_duplication():
    body = "{g}B|:" + "C8|" * 7 + "D7:|"
    measured = extract_ornaments(abc(body))
    event, = measured["events"]
    assert (event["part"], event["bar"], event["onset_eighths"]) == ("A", 8, "7")
    assert (event["beat"], event["beat_phase"]) == (4, "1/2")
    assert event["previous_interval"] == 9
    assert measured["bar_equivalents"] == 8
    assert len(measured["notes"]) == 9


def test_unjoined_pickup_and_irregular_parts_have_no_invented_position():
    measured = extract_ornaments(abc("{g}B|:" + "C8|" * 5 + "~D8:|"))
    pickup, roll = measured["events"]
    assert pickup["pickup"] and pickup["bar"] is None
    assert roll["bar"] is None and roll["phrase_end"] is None


def test_quoted_annotations_comments_and_inline_secondary_voices_are_not_notes():
    text = abc('V:lead\n"G"C8| % ~ {g} (3eee [CE]\n[V:bass]{g}~[C,E,]8|[V:lead]!trill!D8|')
    measured = extract_ornaments(text)
    assert [e["type"] for e in measured["events"]] == ["trill"]
    assert len(measured["notes"]) == 2
    assert set(measured["exclusions"]) == {"grace", "roll", "triplet", "chord"}


def test_compound_beat_and_triplet_rest_are_distinguished():
    measured = extract_ornaments(abc("C3 {g}D3| (3EzG A4|", meter="6/8"))
    event, = measured["events"]
    assert (event["beat"], event["beat_phase"]) == (2, "0")
    assert measured["incomplete_triplets"] == 1
    assert Fraction(event["duration_eighths"]) == 3


def test_ties_and_chord_top_note_preserve_carrier_intervals():
    measured = extract_ornaments(abc("C-C {g}E2 [G,B]4|"))
    grace, chord = measured["events"]
    assert (grace["previous_interval"], grace["next_interval"]) == (4, 7)
    assert chord["degree"] == 7
    assert len(measured["notes"]) == 3


def test_command_aggregates_source_denominators_and_empty_tunes(tmp_path):
    root = tmp_path / "corpus" / "trad"
    tunes = root / "tunes" / "reel"
    tunes.mkdir(parents=True)
    (tunes / "marked.abc").write_text(abc("|:~C8:|"))
    (tunes / "plain.abc").write_text(abc("C4 D4|"))
    (root / "manifest.jsonl").write_text('\n'.join(json.dumps({"id": name, "type": "reel", "source": source}) for name, source in [("marked", "chambers"), ("plain", "thesession")]))
    output, refs = tmp_path / "output", tmp_path / "refs"
    assert main(["trad-ornaments", "--corpus-root", str(root.parent), "--tradition", "quebecoise", "--output", str(output), "--references", str(refs)]) == 0
    stats = json.loads((refs / "quebecoise-reel.json").read_text())
    assert stats["tunes_without_marks"] == 1
    assert stats["share_without_marks"] == .5
    assert stats["by_type"]["roll"] == {"count": 1, "per_100_notes": 33.333333, "per_bar": .5}
    assert stats["by_source"]["chambers"]["by_type"]["roll"]["per_100_notes"] == 100
    assert stats["by_source"]["thesession"]["by_type"]["roll"]["count"] == 0
    assert stats["engine_proposal"]["types"]["grace_single"]["min_carrier_eighths_observed"] is None
    assert stats["by_source_transcriber"]["chambers / Testeur"]["tunes"] == 1
    assert len((output / "events.jsonl").read_text().splitlines()) == 1
