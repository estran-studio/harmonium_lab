"""Tests des sous-ensembles WJazzD non swing (BALLAD, TWOBEAT, LATIN, FUNK) : rythme de la basse, IC, rejets.

Tout est synthétique : la mini base SQLite est écrite par le test avec le schéma de WJazzD (y compris
`track_info`), aucune note de solo réel n'entre dans `tests/`. Les contrôles sur la vraie base sont
marqués `skipif`.
"""

from __future__ import annotations

import json
import random
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

from harmonium_lab.backing import bass_measures as bm
from harmonium_lab.backing import wjazzd
from harmonium_lab.backing import wjazzd_subsets as ws
from harmonium_lab.backing._util import dump_json, percentile, sha256_file
from harmonium_lab.backing.chords import parse_wjazzd

C7 = parse_wjazzd("C7")


def _run(*bars: list[int]) -> bm.BassRun:
    """Suite de mesures sur C7 : une mesure = quatre hauteurs."""
    return bm.BassRun([bm.BassBar([bm.Beat(C7, p) for p in pitches]) for pitches in bars])


# ── Rythme de la basse ───────────────────────────────────────────────────

@pytest.mark.parametrize("pitches, expected", [
    ([40, 42, 44, 45], "quarters"),
    ([40, 42, 40, 42], "quarters"),            # hauteurs revenues mais jamais deux temps de suite
    ([40, 42, 44, 44], "quarters_half"),
    ([40, 42, 42, 45], "quarter_half_quarter"),
    ([40, 42, 42, 42], "quarter_dotted_half"),
    ([40, 40, 42, 45], "half_quarters"),
    ([40, 40, 42, 42], "halves"),
    ([40, 40, 40, 42], "dotted_half_quarter"),
    ([40, 40, 40, 40], "whole"),
])
def test_bar_pattern_follows_pitch_equalities_between_consecutive_beats(pitches, expected):
    summary = ws.measure_rhythm([_run(pitches)]).summary()
    assert summary["bar_pattern"]["counts"][expected] == 1
    assert summary["bar_pattern"]["n"] == 1  # une mesure, une seule classe


def test_eight_patterns_cover_all_equality_combinations():
    assert set(ws._PATTERN_OF.values()) == set(ws.PATTERN_KEYS) and len(ws._PATTERN_OF) == 8


def test_hold_lengths_cross_bar_lines_but_never_join_two_runs():
    # 40 40 40 40 | 40 41 41 41 : 40 tenu cinq temps à travers la barre, puis 41 trois temps
    summary = ws.measure_rhythm([_run([40, 40, 40, 40], [40, 41, 41, 41])]).summary()
    assert summary["hold_beats"]["counts"] == {"1": 0, "2": 0, "3": 1, "4+": 1}
    assert summary["hold_beats"]["beats"] == 8 and summary["hold_beats"]["mean"] == 4.0
    assert summary["bar_tie"] == {"n": 1, "tied": 1, "share": 1.0}
    # deux suites distinctes (mesure écartée entre les deux) : la hauteur identique ne s'attache pas
    split = ws.measure_rhythm([_run([40, 41, 42, 43]), _run([43, 44, 45, 46])]).summary()
    assert split["bar_tie"]["n"] == 0 and split["hold_beats"]["counts"]["1"] == 8


def test_share_of_beats_in_holds_and_repeat_positions():
    summary = ws.measure_rhythm([_run([40, 40, 42, 43], [43, 44, 44, 44])]).summary()
    # suites : 40×2, 42, 43×2, 44×3 → temps dans une suite ≥ 2 : 2 + 2 + 3 = 7 sur 8
    assert summary["hold_beats"]["share_beats_in_holds"] == round(7 / 8, 4)
    assert summary["repeat_by_transition"]["counts"] == {"1-2": 1, "2-3": 1, "3-4": 1}
    assert summary["distinct_pitches_per_bar"]["counts"] == {"1": 0, "2": 1, "3": 1, "4": 0}


# ── Statistiques ─────────────────────────────────────────────────────────

def test_percentile_of_counts_matches_the_plain_percentile():
    rng = random.Random(3)
    values = [rng.randrange(0, 15) for _ in range(137)]
    for q in (0, 1, 25, 50, 63.7, 90, 99, 100):
        assert ws.percentile_of_counts(Counter(values), q) == pytest.approx(percentile(values, q))
    assert ws.percentile_of_counts(Counter(), 50) is None


def test_bootstrap_is_deterministic_and_resamples_solos_not_bars():
    items = [(0, 100), (100, 100)]  # deux solos de 100 mesures : 0 % et 100 %
    a = ws.bootstrap_ci(items, ws._ratio, "graine", resamples=500)
    assert a == ws.bootstrap_ci(items, ws._ratio, "graine", resamples=500)
    # un rééchantillonnage des mesures donnerait ≈ [0,45 ; 0,55] ; par solo : toute l'étendue 0..1
    assert a == (0.0, 1.0)
    same = ws.bootstrap_ci([(30, 100), (30, 100), (30, 100)], ws._ratio, "x", resamples=200)
    assert same == (0.3, 0.3)  # solos identiques : aucune incertitude


def test_bootstrap_ci_brackets_the_estimate_and_narrows_with_more_solos():
    rng = random.Random(11)
    few = [(rng.randrange(10, 60), 100) for _ in range(6)]
    many = few * 5
    lo_f, hi_f = ws.bootstrap_ci(few, ws._ratio, "s")
    lo_m, hi_m = ws.bootstrap_ci(many, ws._ratio, "s")
    estimate = ws._ratio(few)
    assert lo_f <= estimate <= hi_f and lo_m <= estimate <= hi_m
    assert hi_m - lo_m < hi_f - lo_f


def test_verdict_thresholds_are_inclusive_and_need_both_solos_and_bars():
    assert ws.verdict(20, 1500) == "assez"
    assert ws.verdict(20, 1499) == "juste"
    assert ws.verdict(19, 99999) == "juste"
    assert ws.verdict(8, 500) == "juste"
    assert ws.verdict(8, 499) == "trop peu"
    assert ws.verdict(7, 99999) == "trop peu"
    assert ws.verdict(0, 0) == "trop peu"


def test_tempo_classes_are_contiguous_with_lower_bound_inclusive():
    cases = [(50, "tempo_lt120"), (119.9, "tempo_lt120"), (120, "tempo_120_180"), (179.9, "tempo_120_180"),
             (180, "tempo_180_240"), (239.9, "tempo_180_240"), (240, "tempo_ge240"), (400, "tempo_ge240")]
    for tempo, expected in cases:
        assert ws.tempo_class(tempo) == expected
    assert ws.tempo_class(None) is None


# ── Base SQLite synthétique ──────────────────────────────────────────────

SCHEMA = """
create table composition_info(compid integer primary key autoincrement, title text, composer text,
  form text, template text, tonalitytype text, genre text);
create table track_info(trackid integer primary key autoincrement, filename_track text, recordid integer,
  lineup text, mbzid text, trackno integer, recordingdate text, compid integer);
create table solo_info(melid integer, trackid integer, compid integer, recordid integer, performer text,
  title text, titleaddon text, solopart integer, instrument text, style text, avgtempo float,
  tempoclass text, rhythmfeel text, key text, signature text, chord_changes text, chorus_count integer);
create table beats(beatid integer primary key autoincrement, melid integer, onset real, bar integer,
  beat integer, signature text, chord text, form text, bass_pitch integer, chorus_id integer);
"""

# (barre, accord, hauteurs, signature écrite au 1ᵉʳ temps) ; hauteur None : temps sans basse
Bar = tuple


def _insert_bars(con: sqlite3.Connection, melid: int, bars: list[Bar], seconds_per_beat: float = 0.5) -> None:
    rows, t, last = [], 0.0, None
    for bar, chord, pitches, sig in bars:
        for k, p in enumerate(pitches, start=1):
            rows.append((melid, t, bar, k, sig if k == 1 else "", chord if (k == 1 and chord != last) else "",
                         "A1" if (bar == 1 and k == 1) else "", p, 1 if bar >= 1 else 0))
            t += seconds_per_beat
        last = chord
    con.executemany("insert into beats(melid, onset, bar, beat, signature, chord, form, bass_pitch, chorus_id) "
                    "values (?,?,?,?,?,?,?,?,?)", rows)


def _make_db(path: Path) -> Path:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("insert into composition_info(title, template, form) values ('Ballade synthétique', '', 'A8')")
    con.execute("insert into composition_info(title, template, form) values ('Vamp synthétique', '', 'open')")
    for trackid, date in ((1, "1957-03-04"), (2, "04.20.1927"), (3, "1-05-1962"), (4, ""), (5, "2001-01-01")):
        con.execute("insert into track_info(trackid, recordingdate) values (?,?)", (trackid, date))
    solo = ("insert into solo_info(melid, trackid, compid, performer, title, instrument, style, avgtempo, "
            "tempoclass, rhythmfeel, key, signature, chorus_count) values (?,?,?,?,?,?,?,?,?,?,?,?,?)")
    con.execute(solo, (1, 1, 1, "A", "t1", "ts", "COOL", 60.0, "SLOW", "BALLAD", "C-maj", "4/4", 1))
    con.execute(solo, (2, 2, 2, "B", "t2", "tp", "COOL", 80.0, "SLOW", "BALLAD", "", "6/8", 1))
    con.execute(solo, (3, 3, 1, "C", "t3", "p", "COOL", 120.0, "MEDIUM", "BALLAD", "C-maj", "4/4", 1))
    con.execute(solo, (4, 4, 1, "D", "t4", "p", "COOL", 120.0, "MEDIUM", "LATIN/FUNK", "C-maj", "4/4", 1))
    con.execute(solo, (5, 5, 1, "E", "t5", "p", "COOL", 150.0, "MEDIUM", "SWING", "C-maj", "4/4", 1))
    # Solo 1 (60 BPM) : levée (bar 0), puis 8 mesures ; bar 6 : un temps sans basse ; bar 8 : NC.
    _insert_bars(con, 1, [
        (0, "C7", [36, 36, 36, 36], "4/4"),
        (1, "C7", [36, 36, 36, 36], ""),          # whole
        (2, "C7", [36, 38, 40, 41], ""),          # quarters
        (3, "C7", [41, 41, 43, 43], ""),          # halves
        (4, "C7", [43, 40, 40, 40], ""),          # quarter_dotted_half
        (5, "F7", [41, 41, 41, 40], ""),          # dotted_half_quarter
        (6, "F7", [41, None, 43, 45], ""),        # basse manquante : écartée
        (7, "F7", [41, 43, 43, 45], ""),          # quarter_half_quarter
        (8, "NC", [41, 41, 41, 41], ""),          # accord inconnu : écartée
    ])
    # Solo 2 (80 BPM, signature de solo 6/8 mais « 4/4 » écrit au 1ᵉʳ temps) : deux mesures valides.
    _insert_bars(con, 2, [(1, "D-7", [38, 39, 40, 41], "4/4"), (2, "D-7", [38, 39, 40, 41], "")])
    # Solo 3 (120 BPM) : 4/4 (1, 2), 3/4 (3, 4), 4/4 (5), puis une mesure 4/4 à trois temps (6).
    _insert_bars(con, 3, [
        (1, "C7", [36, 38, 40, 41], "4/4"), (2, "C7", [36, 38, 40, 41], ""),
        (3, "C7", [36, 38, 40], "3/4"), (4, "C7", [36, 38, 40], ""),
        (5, "C7", [36, 38, 40, 41], "4/4"), (6, "C7", [36, 38, 40], ""),
    ])
    _insert_bars(con, 4, [(1, "C7", [36, 38, 40, 41], "4/4")])
    _insert_bars(con, 5, [(1, "C7", [36, 38, 40, 41], "4/4")])
    con.commit()
    con.close()
    return path


@pytest.fixture()
def synth_db(tmp_path):
    path = _make_db(tmp_path / "wjazzd.db")
    return path, sha256_file(path)


def test_subset_uses_the_exact_rhythmfeel_and_counts_composites(synth_db):
    path, sha = synth_db
    doc = ws.build_subset("BALLAD", path, sha)
    prov = doc["provenance"]
    assert prov["n_solos"] == 3  # `LATIN/FUNK` et `SWING` ne sont pas du sous-ensemble
    assert prov["composite_rhythmfeel_excluded"] == {"values": {"LATIN/FUNK": 1}, "n_solos": 1}
    assert prov["rhythmfeel_values_in_db"] == {"BALLAD": 3, "LATIN/FUNK": 1, "SWING": 1}
    assert ws.build_subset("LATIN", path, sha)["provenance"]["n_solos"] == 0  # pas de `LATIN` seul
    assert prov["attribution"] == wjazzd.ATTRIBUTION and prov["sha256"] == sha and "ODbL" in prov["licence"]


def test_discarded_bars_are_partitioned_and_signatures_counted(synth_db):
    path, sha = synth_db
    doc = ws.build_subset("BALLAD", path, sha)
    d = doc["groups"]["all"]["discarded"]
    # solo 1 : 8 mesures (6 valides, 1 sans basse, 1 NC) ; solo 2 : 2 valides ; solo 3 : 3 valides,
    # 2 en 3/4, 1 incomplète
    assert d["counts"] == {"bars_all": 16, "non_4_4": 2, "incomplete": 1, "no_bass": 1, "no_chord": 1, "valid": 11}
    assert sum(v for k, v in d["counts"].items() if k != "bars_all") == d["counts"]["bars_all"]
    assert d["shares"]["valid"] == round(11 / 16, 4)
    sig = doc["signatures"]
    assert sig["solo_signature"] == {"4/4": 2, "6/8": 1}
    assert sig["non_4_4"]["bars_by_signature"] == {"3/4": 2} and sig["non_4_4"]["melids_touched"] == [3]
    assert sig["non_4_4"]["solos_without_any_4_4_bar"] == 0
    # le solo 2 s'annonce en 6/8 mais ses temps écrivent 4/4 : ses mesures sont lues, la bascule est signalée
    assert sig["solo_label_overridden_by_beats"] == [2]
    assert doc["chord_parsing"]["beats_nc"] == 4


def test_non_4_4_only_solo_is_counted_without_valid_bars(tmp_path):
    path = tmp_path / "w.db"
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("insert into solo_info(melid, rhythmfeel, signature, avgtempo, key) "
                "values (1, 'FUNK', '9/4', 100.0, '')")
    _insert_bars(con, 1, [(1, "C7", [36] * 9, ""), (2, "C7", [36] * 9, "")])
    con.commit()
    con.close()
    doc = ws.build_subset("FUNK", path, sha256_file(path))
    g = doc["groups"]["all"]
    assert g["counts"]["solos"] == 1 and g["counts"]["solos_with_bars"] == 0
    assert g["discarded"]["counts"]["non_4_4"] == 2 and g["discarded"]["counts"]["valid"] == 0
    assert doc["signatures"]["non_4_4"]["solos_without_any_4_4_bar"] == 1
    assert g["indicators"]["repeat_share"]["estimate"] is None
    assert g["indicators"]["repeat_share"]["ci_reason"] == "aucun solo avec événement"
    assert doc["reliability"]["verdict"] == "trop peu"
    assert "aucun solo" in ws.summary_text(doc, ["tempo_ge240"])


def test_bass_rhythm_counts_on_synthetic_solos(synth_db):
    path, sha = synth_db
    r = ws.build_subset("BALLAD", path, sha)["groups"]["all"]["bass_rhythm"]
    assert r["bars"] == 11
    assert r["bar_pattern"]["counts"] == {
        "quarters": 6, "quarters_half": 0, "quarter_half_quarter": 1, "quarter_dotted_half": 1,
        "half_quarters": 0, "halves": 1, "dotted_half_quarter": 1, "whole": 1}
    # suites : solo 1 mesures 1-5 (4 frontières, 3 attachées) ; mesure 7 seule ; solo 2 (1) ; solo 3 mesures 1-2 (1) et 5
    assert r["bar_tie"] == {"n": 6, "tied": 3, "share": 0.5}
    assert r["hold_beats"]["counts"] == {"1": 25, "2": 1, "3": 4, "4+": 1}
    assert r["hold_beats"]["beats"] == 44  # tous les temps valides sont dans une suite


def test_duration_uses_bars_times_four_over_avgtempo_and_onsets_check(synth_db):
    path, sha = synth_db
    dur = ws.build_subset("BALLAD", path, sha)["groups"]["all"]["duration"]
    # 6 × 4 / 60 + 2 × 4 / 80 + 3 × 4 / 120 = 0,4 + 0,1 + 0,1
    assert dur["minutes_valid_bars"] == 0.6
    # mesures 4/4 vues : 8, 2 et 4 (la mesure incomplète en fait partie)
    assert dur["minutes_4_4_bars"] == round(8 * 4 / 60 + 2 * 4 / 80 + 4 * 4 / 120, 2)
    # temps de mesure ≥ 1 : 32, 8 et 21 ; onsets de 0,5 s : étendues 15,5 s + 3,5 s + 10 s
    assert dur["minutes_all_beats_at_avgtempo"] == round(32 / 60 + 8 / 80 + 21 / 120, 2)
    assert dur["minutes_onset_span"] == round(29 / 60, 2)


def test_tempo_classes_group_solos_and_small_groups_have_no_ci(synth_db):
    path, sha = synth_db
    doc = ws.build_subset("BALLAD", path, sha)
    groups = doc["groups"]
    assert [groups[n]["counts"]["solos"] for n in ("tempo_lt120", "tempo_120_180", "tempo_180_240")] == [2, 1, 0]
    one = groups["tempo_120_180"]["indicators"]["repeat_share"]
    assert one["ci95"] is None and "un seul solo" in one["ci_reason"] and one["n_solos"] == 1
    assert one["n_events"] == groups["tempo_120_180"]["intervals"]["n"]
    many = groups["all"]["indicators"]["repeat_share"]
    assert many["n_solos"] == 3 and many["ci95"] is not None and many["ci95"][0] <= many["ci95"][1]
    assert many["n_events"] == groups["all"]["intervals"]["n"]
    assert doc["reliability"]["by_group"]["all"] == "trop peu"  # 3 solos, 11 mesures


def test_recording_years_parse_mixed_date_formats(synth_db):
    path, sha = synth_db
    years = ws.build_subset("BALLAD", path, sha)["recording_years"]
    assert years["known"] == 3 and years["min"] == 1927 and years["max"] == 1962
    assert years["by_decade"] == {"1920s": 1, "1950s": 1, "1960s": 1}


def test_documents_and_readme_are_deterministic_and_carry_the_licence(synth_db):
    path, sha = synth_db
    a, b = ws.build_subset("BALLAD", path, sha), ws.build_subset("BALLAD", path, sha)
    assert dump_json(a) == dump_json(b) and ws.readme_text(a) == ws.readme_text(b)
    readme = ws.readme_text(a)
    assert wjazzd.ATTRIBUTION in readme and "croches ne sont pas observables" in readme
    assert "python -m harmonium_lab.backing.wjazzd_subsets --subset BALLAD" in readme
    assert any("croches" in lim and "PAS observables" in lim for lim in a["limits"])
    assert set(a) >= {"command", "provenance", "limits", "reliability"}


def test_sha256_mismatch_is_refused(synth_db):
    path, sha = synth_db
    with path.open("ab") as f:
        f.write(b"\x00")
    with pytest.raises(wjazzd.IntegrityError):
        ws.build_subset("BALLAD", path, sha)
    with pytest.raises(wjazzd.IntegrityError):
        ws.write_manifest(path, path.parent / "corpus", sha)
    assert not (path.parent / "corpus" / "manifest.jsonl").exists()


def test_manifest_gains_l2_subset_and_keeps_swing_subset(synth_db, tmp_path):
    path, sha = synth_db
    corpus = tmp_path / "corpus"
    rows = ws.write_manifest(path, corpus, sha)
    by_melid = {r["melid"]: r for r in rows}
    assert [by_melid[m]["l2_subset"] for m in (1, 2, 3, 4, 5)] == ["BALLAD", "BALLAD", "BALLAD", None, None]
    assert [by_melid[m]["swing_subset"] for m in (1, 4, 5)] == [False, False, True]
    assert all(json.loads(line)["licence"] == wjazzd.LICENCE
               for line in (corpus / "manifest.jsonl").read_text().splitlines())
    version = (corpus / "VERSION").read_text()
    assert "l2_subsets: BALLAD 3, TWOBEAT 0, LATIN 0, FUNK 0" in version and sha in version
    first = ((corpus / "manifest.jsonl").read_text(), version)
    ws.write_manifest(path, corpus, sha)
    assert ((corpus / "manifest.jsonl").read_text(), (corpus / "VERSION").read_text()) == first


# ── CLI ──────────────────────────────────────────────────────────────────

def test_cli_writes_json_and_readme_for_the_requested_subset_only(synth_db, tmp_path):
    path, sha = synth_db
    out = tmp_path / "refs"
    # la CLI attend le SHA256 de la vraie base : la base synthétique est refusée, rien n'est écrit
    assert ws.main(["--subset", "BALLAD", "--db", str(path), "--out-dir", str(out)]) == 1
    assert not out.exists()
    doc = ws.write_subset("BALLAD", path, out, sha)
    folder = out / "wjazzd-ballad"
    written = json.loads((folder / "measures-bass.json").read_text(encoding="utf-8"))
    assert written["provenance"]["n_solos"] == doc["provenance"]["n_solos"] == 3
    assert (folder / "README.md").is_file() and not (out / "wjazzd-funk").exists()
    assert ws.main(["--subset", "BALLAD", "--summary", "--out-dir", str(out)]) == 0


def test_cli_rejects_a_corrupt_database(tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_bytes(b"pas la base")
    assert ws.main(["--manifest", "--db", str(bad), "--corpus-dir", str(tmp_path / "c")]) == 1
    assert not (tmp_path / "c" / "manifest.jsonl").exists()


# ── Vraie base (facultatif) ──────────────────────────────────────────────

real = pytest.mark.skipif(not wjazzd.RAW_DB.is_file(), reason="base WJazzD absente du cache")


@real
def test_real_subsets_have_the_documented_sizes():
    con = wjazzd.open_db()
    try:
        sizes = {s: len(wjazzd.list_solos(con, s)) for s in ws.SUBSETS}
        assert sizes == {"BALLAD": 10, "TWOBEAT": 32, "LATIN": 27, "FUNK": 20}
        assert ws.composite_count(con) == {"A:LATIN/B:SWING": 1, "FUNK/SWING": 1, "LATIN/FUNK": 3, "LATIN/SWING": 1}
    finally:
        con.close()


@real
def test_real_funk_has_open_form_vamps_and_non_4_4_solos():
    doc = ws.build_subset("FUNK")
    g = doc["groups"]["all"]
    assert g["open_form"]["solos"] == 8 and g["open_form"]["bars_valid"] > 0
    assert "9/4" in doc["signatures"]["non_4_4"]["bars_by_signature"]
    assert g["discarded"]["counts"]["valid"] == g["counts"]["bars_valid"]
