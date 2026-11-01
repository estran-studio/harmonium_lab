"""Tests de la basse mesurée (WJazzD) : analyseur d'accords, classification, lecteur, comparaison.

Tout est synthétique : la mini base SQLite est écrite par le test avec le schéma de WJazzD,
la vérité terrain est un mini JSON au format `--record-truth`. Aucune note de solo réel n'entre
dans `tests/`. Les contrôles sur la vraie base (facultatifs) sont marqués `skipif`.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from harmonium_lab.backing import bass_compare as bc
from harmonium_lab.backing import bass_measures as bm
from harmonium_lab.backing import wjazzd
from harmonium_lab.backing._util import dump_json, percentile, sha256_file
from harmonium_lab.backing.chords import ChordParseError, from_engine, parse_wjazzd

C, F, BB = 0, 5, 10


# ── Analyseur d'accords ──────────────────────────────────────────────────

@pytest.mark.parametrize("symbol, root, bass, quality, tones", [
    ("Bb7", 10, 10, "dom", {10, 2, 5, 8}),
    ("C-7", 0, 0, "min", {0, 3, 7, 10}),
    ("Ebj7", 3, 3, "maj", {3, 7, 10, 2}),
    ("Bb6", 10, 10, "maj", {10, 2, 5, 7}),
    ("F#o7", 6, 6, "dim", {6, 9, 0, 3}),
    ("Go", 7, 7, "dim", {7, 10, 1}),
    ("Gh7", 7, 7, "hdim", {7, 10, 1, 5}),
    ("Am7b5", 9, 9, "hdim", {9, 0, 3, 7}),
    ("C+7", 0, 0, "aug", {0, 4, 8, 10}),
    ("Dsus7", 2, 2, "sus", {2, 7, 9, 0}),
    ("F-6", 5, 5, "min", {5, 8, 0, 2}),
    ("C-j7", 0, 0, "min", {0, 3, 7, 11}),
    ("F", 5, 5, "maj", {5, 9, 0}),
    ("Bb-", 10, 10, "min", {10, 1, 5}),
])
def test_parse_wjazzd_symbols(symbol, root, bass, quality, tones):
    chord = parse_wjazzd(symbol)
    assert (chord.root, chord.bass, chord.quality) == (root, bass, quality)
    assert chord.tones == frozenset(tones)


def test_tensions_follow_wjazzd_notation_and_usual_notation():
    # WJazzD : l'altération suit le nombre ; l'écriture usuelle (précédant) est un repli.
    for symbol in ("C79b", "C7b9"):
        chord = parse_wjazzd(symbol)
        assert chord.quality == "dom" and 1 in {(p - chord.root) % 12 for p in chord.tones}
    sharp11 = parse_wjazzd("C7#11")
    assert 6 in sharp11.tones
    stack = parse_wjazzd("Ebj7911#")
    assert {(p - stack.root) % 12 for p in stack.tones} >= {0, 2, 4, 6, 7, 11}
    both = parse_wjazzd("D79b13b")
    assert {(p - both.root) % 12 for p in both.tones} >= {1, 8}


def test_slash_chord_uses_slash_bass_and_nc_is_no_chord():
    slash = parse_wjazzd("C-7/Bb")
    assert (slash.root, slash.bass, slash.quality) == (0, 10, "min")
    assert parse_wjazzd("Bb/D").bass == 2
    assert parse_wjazzd("NC") is None
    with pytest.raises(ChordParseError):
        parse_wjazzd("H7")
    with pytest.raises(ChordParseError):
        parse_wjazzd("C7zz")


def test_reference_scales_follow_the_declared_choices():
    def rel(symbol):
        chord = parse_wjazzd(symbol)
        return {(p - chord.root) % 12 for p in chord.scale}

    assert rel("C7") == {0, 2, 4, 5, 7, 9, 10}            # mixolydien
    assert rel("C-7") == {0, 2, 3, 5, 7, 9, 10}           # dorien
    assert rel("Cj7") == {0, 2, 4, 5, 7, 9, 11}           # ionien
    assert rel("C79b") == {0, 1, 3, 4, 6, 7, 9, 10}       # octotonique demi-ton/ton
    assert rel("C7alt") == {0, 1, 3, 4, 6, 8, 10}         # altérée
    assert rel("C7#11") == {0, 2, 4, 6, 7, 9, 10}         # lydien b7
    assert rel("Co7") == {0, 2, 3, 5, 6, 8, 9, 11}        # octotonique ton/demi-ton
    assert rel("Cm7b5") == {0, 2, 3, 5, 6, 8, 10}         # locrien ♮2
    assert rel("C+7") == {0, 2, 4, 6, 8, 10}              # gamme par tons


@pytest.mark.parametrize("quality, is_minor, expected, tones", [
    ("", False, "maj", {0, 4, 7}),
    ("", True, "min", {0, 3, 7}),
    ("m7", False, "min", {0, 3, 7, 10}),
    ("maj7", False, "maj", {0, 4, 7, 11}),
    ("maj9", False, "maj", {0, 4, 7, 11, 2}),
    ("7", False, "dom", {0, 4, 7, 10}),
    ("13", False, "dom", {0, 4, 7, 10, 2, 9}),
    ("7b9", False, "dom", {0, 4, 7, 10, 1}),
    ("7alt", False, "dom", {0, 4, 10, 1, 3, 6, 8}),
    ("m7b5", False, "hdim", {0, 3, 6, 10}),
    ("dim7", False, "dim", {0, 3, 6, 9}),
    ("6", False, "maj", {0, 4, 7, 9}),
    ("6/9", False, "maj", {0, 4, 7, 9, 2}),
    ("m9", False, "min", {0, 3, 7, 10, 2}),
    ("13sus4", False, "sus", {0, 5, 7, 10, 2, 9}),
    ("mMaj7", False, "min", {0, 3, 7, 11}),
    ("+", False, "aug", {0, 4, 8}),
])
def test_engine_qualities(quality, is_minor, expected, tones):
    chord = from_engine(0, 0, quality, is_minor)
    assert chord.quality == expected
    assert chord.tones == frozenset(tones)


def test_engine_slash_and_unknown_quality():
    assert from_engine(7, 11, "7b9").bass == 11
    with pytest.raises(ChordParseError):
        from_engine(0, 0, "Major")


# ── Classification d'une note ────────────────────────────────────────────

def test_arrival_classes():
    g7 = parse_wjazzd("G7")
    assert [bm.arrival_class(p, g7) for p in (43, 47, 50, 53, 45)] == ["bass", "third", "fifth", "seventh", "other"]
    slash = parse_wjazzd("C/E")
    assert bm.arrival_class(40, slash) == "bass"
    assert bm.arrival_class(36, slash) == "root"


def test_approach_classes():
    entering, outgoing = parse_wjazzd("F7"), parse_wjazzd("C7")  # cible : fa (41) ; do7 = do mi sol si♭
    target = 41
    cases = {
        41: "same",
        40: "chromatic_below",
        42: "chromatic_above",
        43: "diatonic",     # sol à +2, dans le fa mixolydien
        39: "diatonic",     # mi♭ à −2
        38: "diatonic",     # ré à −3
        44: "other",        # la♭ à +3 : hors gamme de fa, hors do7
        48: "fifth",        # do à +7
        34: "fifth",        # si♭ à −7
        36: "chord_tone",   # do à −5 : note de l'accord sortant
        45: "other",        # la à +4 : ni gamme à 2-3 demi-tons, ni note de do7
    }
    for pitch, expected in cases.items():
        assert bm.approach_class(pitch, target, entering, outgoing) == expected, pitch


def test_approach_diatonic_requires_the_entering_scale_and_nearest_note():
    entering = outgoing = parse_wjazzd("Cj7")   # do ionien : pas de si♭
    assert bm.approach_class(46, 48, entering, outgoing) == "other"         # si♭ à −2, hors gamme
    assert bm.approach_class(50, 48, entering, outgoing) == "diatonic"      # ré à +2
    assert bm.approach_class(45, 48, entering, outgoing) == "diatonic"      # la à −3
    assert bm.is_nearest_scale_note(50, 48, entering) is True
    assert bm.is_nearest_scale_note(45, 48, entering) is False              # le si (47) est dans la gamme, plus proche


def test_passing_classes_nearest_pitch_and_window():
    c7 = parse_wjazzd("C7")
    assert [bm.passing_class(p, c7) for p in (40, 41, 37)] == ["chord_tone", "scale_step", "chromatic"]
    assert bm.nearest_with_pc(46, 10) == 46
    assert bm.nearest_with_pc(47, 10) == 46
    assert bm.nearest_with_pc(41, 11) == 35            # si le plus proche de fa (41) : 35 (−6)
    assert bm.best_window([40, 41, 41, 42, 60], 12) == {"low": 40, "high": 51, "n_inside": 4, "share_inside": 0.8}
    assert bm.best_window([], 12) is None


# ── Mesures sur une suite synthétique ────────────────────────────────────

def _bar(chords, pitches, prev=None):
    return bm.BassBar([bm.Beat(parse_wjazzd(c), p) for c, p in zip(chords, pitches)], prev_chord=prev)


def _run():
    """3 mesures : C7, F7, Bb7 ; approche chromatique (E → F) puis diatonique (C → Bb, +2)."""
    return bm.BassRun([
        _bar(["C7"] * 4, [36, 40, 43, 40]),
        _bar(["F7"] * 4, [41, 44, 45, 48]),
        _bar(["Bb7"] * 4, [46, 44, 43, 42]),
    ], key=None)


def test_measures_arrival_and_approach_counts():
    m = bm.measure_runs([_run()])
    assert m["bars"] == 3 and m["runs"] == 1
    assert m["arrival"]["change"]["counts"]["bass"] == 2 and m["arrival"]["change"]["n"] == 2
    assert m["arrival"]["bar_start_no_change"]["counts"]["bass"] == 1
    ap = m["approach"]["all"]
    assert ap["n"] == 2
    assert ap["counts"]["chromatic_below"] == 1 and ap["counts"]["diatonic"] == 1
    assert ap["weights"]["counts"] == {"none": 0, "chromatic": 1, "diatonic": 1}
    assert m["approach"]["bar_change"]["n"] == 2 and m["approach"]["mid_change"]["n"] == 0
    assert ap["moving"]["above_below"]["counts"] == {"above": 1, "below": 1}
    assert ap["moving"]["rising_falling"]["counts"]["falling"] == 1
    assert ap["moving"]["rising_falling"]["counts"]["rising"] == 1
    assert ap["moving"]["side"]["counts"] == {"same_side_as_arrival": 1, "other_side": 1}
    assert ap["distance"]["counts"]["1"] == 1 and ap["distance"]["counts"]["2"] == 1
    assert ap["semitone_share"] == 0.5 and ap["whole_tone_share"] == 0.5


def test_measures_passage_intervals_and_rhythm():
    m = bm.measure_runs([_run()])
    assert m["passage"]["counts"] == {"chord_tone": 4, "scale_step": 1, "chromatic": 1}
    assert m["passage"]["by_beat"]["2"]["counts"] == {"chord_tone": 2, "scale_step": 0, "chromatic": 1}
    assert m["passage"]["by_beat"]["3"]["counts"] == {"chord_tone": 2, "scale_step": 1, "chromatic": 0}
    assert m["passage"]["by_beat"]["4"]["n"] == 0  # le 4ᵉ temps précède toujours l'arrivée de la barre
    iv = m["intervals"]
    assert iv["n"] == 11 and iv["counts"]["0"] == 0 and iv["repeat_share"] == 0.0
    assert (iv["counts"]["1"], iv["counts"]["2"], iv["counts"]["3"], iv["counts"]["4"]) == (4, 2, 4, 1)
    assert iv["percentiles"]["p50"] == 2.0
    assert iv["keep_direction"]["counts"] == {"keep": 7, "reverse": 3}
    assert iv["toward_target"]["counts"] == {"toward": 3, "not_toward": 1}
    assert iv["toward_target"]["share"] == 0.75
    hr = m["harmonic_rhythm"]
    assert hr["chords_per_bar"]["counts"] == {"1": 3, "2": 0, "3": 0, "4": 0}
    assert hr["change_beat"]["counts"]["1"] == 2 and hr["change_beat"]["share_beat1"] == 1.0
    assert hr["chord_duration_beats"]["counts"]["4"] == 1 and hr["chord_duration_beats"]["mean"] == 4.0
    assert m["register"]["pitch_range"] == [36, 48] and m["register"]["relative_to_tonic"]["n"] == 0


def test_repeated_note_on_approach_beat_is_none_and_engine_passage():
    run = bm.BassRun([_bar(["C7"] * 4, [36, 43, 40, 36]), _bar(["C7"] * 4, [36, 43, 40, 36])])
    m = bm.measure_runs([run])
    assert m["approach"]["bar_same"]["n"] == 1 and m["approach"]["bar_same"]["counts"]["same"] == 1
    assert m["approach"]["bar_same"]["weights"]["counts"]["none"] == 1
    assert m["passage"]["n"] == 4 and m["passage_engine"]["n"] == 5  # + le temps 4 de la 1ʳᵉ mesure, non approche
    assert m["passage_engine"]["by_beat"]["4"]["n"] == 1


def test_mid_bar_change_and_slash_bass():
    run = bm.BassRun([
        _bar(["C7", "C7", "F7", "F7"], [36, 40, 41, 43]),
        _bar(["Bb7/D"] * 4, [38, 38, 38, 38], prev=parse_wjazzd("F7")),
    ])
    m = bm.measure_runs([run])
    assert m["arrival"]["change_mid_bar"]["n"] == 1 and m["arrival"]["change_bar_start"]["n"] == 1
    # fa au 3ᵉ temps ; ré (basse du slash si♭7/ré) à la barre : deux arrivées sur la basse de l'accord
    assert m["arrival"]["change"]["counts"]["bass"] == 2
    assert m["approach"]["mid_change"]["n"] == 1 and m["approach"]["mid_change"]["counts"]["chromatic_below"] == 1
    assert m["harmonic_rhythm"]["chords_per_bar"]["counts"] == {"1": 1, "2": 1, "3": 0, "4": 0}
    assert m["harmonic_rhythm"]["change_beat"]["counts"]["3"] == 1
    assert m["harmonic_rhythm"]["change_beat"]["share_beat3"] == 0.5


def test_register_percentiles_and_transposition():
    run = bm.BassRun([_bar(["C7"] * 4, [30, 40, 50, 60])], key=7)
    m = bm.measure_runs([run])
    assert m["register"]["pitch"]["p50"] == 45.0 and m["register"]["pitch"]["p1"] == 30.3
    assert m["register"]["relative_to_tonic"]["n"] == 4 and m["register"]["relative_to_tonic"]["p50"] == 38.0
    assert percentile([1, 2, 3, 4], 50) == 2.5


def test_tempo_bins_are_contiguous_and_cover_the_range():
    assert [bm.tempo_bin(t) for t in (50, 129.9, 130, 174.9, 175, 234.9, 235, 400)] == [
        "tempo_lt130", "tempo_lt130", "tempo_130_175", "tempo_130_175",
        "tempo_175_235", "tempo_175_235", "tempo_ge235", "tempo_ge235"]
    assert bm.tempo_bin(None) is None


# ── Base SQLite synthétique, lecteur, manifeste ──────────────────────────

SCHEMA = """
create table composition_info(compid integer primary key autoincrement, title text, composer text,
  form text, template text, tonalitytype text, genre text);
create table solo_info(melid integer, trackid integer, compid integer, recordid integer, performer text,
  title text, titleaddon text, solopart integer, instrument text, style text, avgtempo float,
  tempoclass text, rhythmfeel text, key text, signature text, chord_changes text, chorus_count integer);
create table beats(beatid integer primary key autoincrement, melid integer, onset real, bar integer,
  beat integer, signature text, chord text, form text, bass_pitch integer, chorus_id integer);
"""


def _beats(melid, bars, first_signature="4/4", chorus=1, start_beatid=None):
    """Lignes `beats` d'une suite de mesures `[(bar, chord, [pitches])]` : chord/form écrits au changement."""
    rows, last = [], None
    for bar, chord, pitches in bars:
        for k, p in enumerate(pitches, start=1):
            rows.append((melid, 0.0, bar, k, first_signature if (bar == bars[0][0] and k == 1) else "",
                         chord if (k == 1 and chord != last) else "", "A1" if (bar == 1 and k == 1) else "",
                         p, chorus if bar >= 1 else 0))
        last = chord
    return rows


def _make_db(path: Path) -> Path:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("insert into composition_info(title, template, form) values ('Blues synthétique', 'Blues', 'A12')")
    con.execute("insert into composition_info(title, template, form) values ('Standard synthétique', '', 'A8A8B8A8')")
    solo = "insert into solo_info(melid, compid, performer, title, instrument, style, avgtempo, tempoclass, " \
           "rhythmfeel, key, signature, chorus_count) values (?,?,?,?,?,?,?,?,?,?,?,?)"
    con.execute(solo, (1, 1, "Joueur A", "Blues synthétique", "ts", "BEBOP", 120.0, "MEDIUM", "SWING", "F-blues", "4/4", 2))
    con.execute(solo, (2, 2, "Joueur B", "Standard synthétique", "tp", "COOL", 240.0, "UP", "SWING", "", "4/4", 1))
    con.execute(solo, (3, 2, "Joueur C", "Valse synthétique", "p", "COOL", 150.0, "MEDIUM", "SWING", "C-maj", "3/4", 1))
    con.execute(solo, (4, 2, "Joueur D", "Latin synthétique", "p", "COOL", 150.0, "MEDIUM", "LATIN", "C-maj", "4/4", 1))
    rows = []
    # Solo 1 : levée (bar -1, bar 0), puis mesures 1..4 : F7 | F7 | Bb7 | NC ; mesure 3 sans basse au temps 2 ;
    # la mesure 2 reste sans changement d'accord (propagé) ; un 5ᵉ temps hors 4/4 n'existe pas.
    rows += _beats(1, [(-1, "F7", [41, 41, 41, 41]), (0, "F7", [41, 43, 45, 46]),
                       (1, "F7", [41, 43, 45, 40]), (2, "F7", [41, 42, 43, 44]),
                       (3, "Bb7", [46, 45, 44, 43]), (4, "NC", [41, 41, 41, 41]),
                       (5, "F7", [41, 43, 45, 47])], first_signature="4/4")
    rows += _beats(2, [(1, "Bbj7", [46, 48, 50, 45]), (2, "Bbj7", [46, 46, 46, 46])])
    rows += _beats(3, [(1, "C7", [36, 38, 40]), ], first_signature="3/4")
    rows += _beats(4, [(1, "C7", [36, 38, 40, 41])])
    con.executemany("insert into beats(melid, onset, bar, beat, signature, chord, form, bass_pitch, chorus_id) "
                    "values (?,?,?,?,?,?,?,?,?)", rows)
    # mesure 3 de F7/Bb7 : retire la basse du temps 2 (trou de `bass_pitch`)
    con.execute("update beats set bass_pitch = null where melid = 1 and bar = 3 and beat = 2")
    con.commit()
    con.close()
    return path


@pytest.fixture()
def synth_db(tmp_path):
    path = _make_db(tmp_path / "wjazzd.db")
    return path, sha256_file(path)


def test_reader_skips_pickups_propagates_chords_keeps_4_4(synth_db):
    path, sha = synth_db
    con = wjazzd.open_db(path, sha)
    rows = wjazzd.read_solo(con, 1, "4/4")
    assert min(r.bar for r in rows) == 1                       # levées (bar < 1) ignorées
    assert [r.chord for r in rows if r.bar == 1] == ["F7"] * 4  # accord propagé aux temps sans symbole
    assert [r.chord for r in rows if r.bar == 2] == ["F7"] * 4  # rien d'écrit à la mesure 2 : propagé
    assert [r.chord for r in rows if r.bar == 4] == ["NC"] * 4
    assert [r.form for r in rows if r.bar == 1] == ["A1"] * 4
    assert [r.bass_pitch for r in rows if r.bar == 3] == [46, None, 44, 43]  # trou conservé
    assert wjazzd.read_solo(con, 3, "3/4") == []                # solo en 3/4 : aucune mesure 4/4
    assert [len(b) for b in wjazzd.bars_of(rows)] == [4] * 5
    con.close()


def test_measure_pipeline_on_synthetic_db(synth_db):
    path, sha = synth_db
    doc = bm.build(path, sha)
    assert doc["provenance"]["n_solos"] == 3                      # le solo LATIN est hors sous-ensemble
    allg = doc["groups"]["all"]
    # solo 1 : mesures 1, 2, 5 valides (3 : trou de basse ; 4 : NC) ; solo 2 : mesures 1 et 2
    assert allg["counts"]["bars"] == 7 and allg["counts"]["bars_valid"] == 5
    assert allg["counts"]["bars_no_bass"] == 1 and allg["counts"]["bars_no_chord"] == 1
    assert doc["groups"]["blues"]["counts"]["solos"] == 1 and doc["groups"]["other_forms"]["counts"]["solos"] == 2
    assert doc["groups"]["tempo_lt130"]["counts"]["solos"] == 1 and doc["groups"]["tempo_ge235"]["counts"]["solos"] == 1
    assert doc["groups"]["tempo_130_175"]["counts"]["solos"] == 1  # la valse (3/4) : un solo, aucune mesure
    assert doc["groups"]["tempo_130_175"]["counts"]["bars_valid"] == 0
    assert doc["chord_parsing"]["beats_nc"] == 4 and doc["chord_parsing"]["beats_unparsed"] == 0
    # suites : (1, 2) du solo 1 contiguës ; la mesure 5 isole une suite ; (1, 2) du solo 2
    assert allg["runs"] == 3
    # tonique de solo 1 = fa (F-blues) : registre transposé présent seulement pour lui
    assert allg["register"]["relative_to_tonic"]["n"] == 12
    assert allg["structure"]["templates"] == {"(aucun)": 2, "Blues": 1}


def test_unparsed_chord_symbols_are_counted_and_bars_dropped(tmp_path):
    path = tmp_path / "w.db"
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("insert into solo_info(melid, rhythmfeel, signature, avgtempo, key) values (1, 'SWING', '4/4', 200.0, 'C-maj')")
    rows = _beats(1, [(1, "C7", [36, 38, 40, 41]), (2, "Zq9", [36, 38, 40, 41])])
    con.executemany("insert into beats(melid, onset, bar, beat, signature, chord, form, bass_pitch, chorus_id) "
                    "values (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    doc = bm.build(path, sha256_file(path))
    assert doc["chord_parsing"]["beats_unparsed"] == 4
    assert doc["chord_parsing"]["share_unparsed"] == 0.5
    assert doc["chord_parsing"]["unparsed_symbols"] == {"Zq9": 4}
    assert doc["groups"]["all"]["counts"]["bars_valid"] == 1


def test_sha256_mismatch_is_a_clear_error(synth_db):
    path, sha = synth_db
    assert wjazzd.verify(path, sha) == sha
    with path.open("ab") as f:
        f.write(b"\x00")
    with pytest.raises(wjazzd.IntegrityError, match="SHA256 non conforme"):
        wjazzd.verify(path, sha)
    with pytest.raises(wjazzd.IntegrityError):
        wjazzd.open_db(path, sha)
    with pytest.raises(wjazzd.IntegrityError):
        bm.build(path, sha)
    with pytest.raises(wjazzd.IntegrityError, match="absent"):
        wjazzd.verify(path.with_name("absent.db"), sha)


def test_fetch_rejects_a_corrupt_download_and_keeps_nothing(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"pas la base")
    dest = tmp_path / "raw" / "wjazzd.db"
    with pytest.raises(wjazzd.IntegrityError):
        wjazzd.fetch(dest, url=source.as_uri(), expected="0" * 64)
    assert not dest.exists()


def test_manifest_has_licence_no_notes_and_is_reproducible(synth_db, tmp_path):
    path, sha = synth_db
    manifest, version = tmp_path / "m" / "manifest.jsonl", tmp_path / "m" / "VERSION"
    rows = wjazzd.write_manifest(path, manifest, version, sha, today="2026-01-02")
    first = (manifest.read_text(), version.read_text())
    assert len(rows) == 4 and sum(1 for r in rows if r["swing_subset"]) == 3
    for line in manifest.read_text().splitlines():
        entry = json.loads(line)
        assert entry["licence"] == wjazzd.LICENCE
        assert "rhythmfeel" in entry and not {"notes", "pitches", "bass_pitch", "chord_changes"} & set(entry)
    assert rows[0]["n_beats"] == 28 and rows[0]["n_beats_bass"] == 27  # un trou de `bass_pitch`
    wjazzd.write_manifest(path, manifest, version, sha, today="2030-12-31")  # la date de relevé est conservée
    assert (manifest.read_text(), version.read_text()) == first
    assert "retrieved: 2026-01-02" in first[1] and sha in first[1] and "ODbL" in first[1]


def test_measures_json_is_deterministic(synth_db):
    path, sha = synth_db
    assert dump_json(bm.build(path, sha)) == dump_json(bm.build(path, sha))


def test_summary_text_mentions_groups(synth_db):
    path, sha = synth_db
    text = bm.summary_text(bm.build(path, sha), ["all"])
    assert "== all" in text and "Arrivée" in text and "Approche" in text


# ── Comparaison sur vérité terrain synthétique ───────────────────────────

def _truth_entry(bar, chords, bass, key=F, tune=0):
    """Entrée `measures[i]` de `--record-truth` : `chords` = [(pas, racine abs., basse abs., qualité)] ;
    `bass` = hauteurs MIDI absolues aux pas 0, 4, 8, 12."""
    return {"bar": bar, "measure": {
        "position": {"key": key, "part": 0, "tune_index": tune, "tour": 1, "sequence_index": 0},
        "chord_changes": [{"start_step": s, "context": {"root_pc": r, "bass_pc": b, "quality": q, "is_minor": False}}
                          for s, r, b, q in chords],
        "notes": [{"track": 2, "start_step": 4 * k, "pitch": p, "duration_steps": 4, "velocity": 80}
                  for k, p in enumerate(bass) if p is not None]
                 + [{"track": 0, "start_step": 0, "pitch": 70, "duration_steps": 2, "velocity": 80}],
    }}


def _truth(path, entries):
    path.write_text(json.dumps({"measures": entries}), encoding="utf-8")
    return path


def _entries():
    return [
        _truth_entry(1, [(0, F, F, "7")], [41, 44, 45, 48]),
        _truth_entry(2, [(0, F, F, "7"), (8, BB, BB, "7")], [41, 44, 46, 45]),
        _truth_entry(3, [(0, BB, BB, "7")], [46, 48, 50, 41]),
        _truth_entry(4, [(0, F, F, "maj7")], [41, 43, 45, 47]),
        _truth_entry(5, [(0, F, F, "7")], [41, 43, None, 47]),       # une note de basse manque : mesure écartée
        _truth_entry(6, [(0, F, F, "7")], [41, 43, 45, 47]),
        _truth_entry(7, [(0, C, C, "m7")], [36, 38, 40, 41], tune=1),  # autre air : ignoré
    ]


def test_runs_from_truth_reads_bass_and_chords(tmp_path):
    runs, stats = bc.runs_from_truth([_truth(tmp_path / "t.json", _entries())])
    assert (stats.bars, stats.bars_valid, stats.bars_no_bass, stats.runs) == (6, 5, 1, 2)
    first = runs[0]
    assert [len(r.bars) for r in runs] == [4, 1] and first.key == F
    assert [b.pitch for b in first.bars[0].beats] == [41, 44, 45, 48]
    assert [b.chord.root for b in first.bars[1].beats] == [F, F, BB, BB]    # changement au pas 8
    assert first.bars[1].prev_chord.root == F and first.bars[3].beats[0].chord.quality == "maj"
    assert first.bars[0].prev_chord is None


def test_distance_of_a_source_with_itself_is_zero(tmp_path):
    truth = _truth(tmp_path / "t.json", _entries())
    runs, _ = bc.runs_from_truth([truth])
    reference = {"provenance": {"source": "s", "version": "v", "licence": "l", "attribution": "a",
                                "n_solos": 1, "n_bars_valid": 5},
                 "groups": {"all": {**bm.measure_runs(runs), "counts": {"solos": 1, "bars_valid": 5}}}}
    result = bc.build(reference, {"self": [truth]}, ["all"], "cmd", "ref.json")["comparisons"]["all"]["self"]
    assert result["distance"] == 0.0
    assert all(v["distance"] in (0.0, None) for v in result["criteria"].values())
    assert set(result["by_family"]) >= {"arrival", "approach", "intervals", "register", "harmonic_rhythm"}
    assert result["by_family"]["intervals"] == 0.0


def test_distance_grows_with_difference_and_is_bounded(tmp_path):
    a = _truth(tmp_path / "a.json", _entries())
    shifted = [_truth_entry(e["bar"], [(0, F, F, "7")], [41 + 24, 43 + 24, 45 + 24, 41 + 24]) for e in _entries()[:4]]
    b = _truth(tmp_path / "b.json", shifted)
    ref_runs, _ = bc.runs_from_truth([a])
    ref = bm.measure_runs(ref_runs)
    gen_runs, _ = bc.runs_from_truth([b])
    result = bc.compare(ref, bm.measure_runs(gen_runs))
    assert 0.0 < result["distance"] <= 1.0
    assert result["criteria"]["register_percentiles"]["distance"] == 1.0   # deux octaves d'écart : plafonné à 1
    assert all(0.0 <= v["distance"] <= 1.0 for v in result["criteria"].values() if v["distance"] is not None)


def test_tv_distance_and_share_bounds():
    assert bc.tv_distance({"a": 2, "b": 2}, {"a": 1, "b": 1}) == 0.0
    assert bc.tv_distance({"a": 1}, {"b": 1}) == 1.0
    assert bc.tv_distance({"a": 1, "b": 3}, {"a": 3, "b": 1}) == 0.5
    assert bc.tv_distance({}, {"a": 1}) is None


def test_labels_group_the_preceding_truths():
    events = [("truth", "a1.json"), ("truth", "a2.json"), ("label", "A"), ("truth", "b.json"), ("label", "B"),
              ("truth", "c.json")]
    labels = bc.labels_from_events(events)
    assert {k: [p.name for p in v] for k, v in labels.items()} == {
        "A": ["a1.json", "a2.json"], "B": ["b.json"], "genere": ["c.json"]}
    with pytest.raises(ValueError):
        bc.labels_from_events([("label", "X")])


def test_compare_cli_writes_json_and_markdown(tmp_path):
    t1 = _truth(tmp_path / "t1.json", _entries())
    t2 = _truth(tmp_path / "t2.json", _entries()[:4])
    runs, _ = bc.runs_from_truth([t1])
    ref = tmp_path / "ref.json"
    ref.write_text(dump_json({"provenance": {"source": "s", "version": "v", "licence": "l", "attribution": "a",
                                             "n_solos": 1, "n_bars_valid": 5},
                              "groups": {"all": {**bm.measure_runs(runs), "counts": {"solos": 1, "bars_valid": 5}}}}))
    out = tmp_path / "out" / "cmp.json"
    code = bc.main(["--truth", str(t1), "--label", "base", "--truth", str(t2), "--label", "autre",
                    "--reference", str(ref), "-o", str(out), "--markdown"])
    assert code == 0
    doc = json.loads(out.read_text())
    assert set(doc["labels"]) == {"base", "autre"} and doc["comparisons"]["all"]["base"]["distance"] == 0.0
    assert "d(base)" in out.with_suffix(".md").read_text() and "agrégée" in out.with_suffix(".md").read_text()
    again = tmp_path / "out2" / "cmp.json"
    bc.main(["--truth", str(t1), "--label", "base", "--truth", str(t2), "--label", "autre",
             "--reference", str(ref), "-o", str(again)])
    assert json.loads(again.read_text())["labels"] == doc["labels"]


# ── Contrôles facultatifs sur la vraie base (sautés sans le brut) ────────

REAL = pytest.mark.skipif(not wjazzd.RAW_DB.is_file(), reason="brut WJazzD absent (cache gitignoré)")


@REAL
def test_real_swing_chords_are_analysed_below_two_percent():
    doc = bm.build()
    parsing = doc["chord_parsing"]
    assert parsing["share_unparsed"] < 0.02
    assert doc["provenance"]["n_solos"] == 361
    assert doc["groups"]["blues"]["counts"]["solos"] == 87


@REAL
def test_real_measures_are_deterministic():
    assert dump_json(bm.build()) == dump_json(bm.build())
