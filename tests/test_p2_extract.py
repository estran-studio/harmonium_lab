"""Tests P2 : extraction d'alternatives depuis des transcriptions (fixture synthétique générée ici)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from harmonium_lab.p2 import enrich as p2_enrich
from harmonium_lab.p2 import extract as ex
from harmonium_lab.p2.engine_profile import load_profile

PROFILE_TOML = """
[files]
percussion = "percussion.toml"
[meta]
id = "fixture"
[meter]
steps_per_bar = 16
steps_per_pulse = 4
[fixed_tonality]
key = 0
mode = "aeolian"
[form]
sequence = [0, 1]
[[form.parts]]
name = "A"
roles = ["Open", "Open", "Open", "Open"]
[[form.parts]]
name = "B"
roles = ["Open", "Open", "Open", "Open"]
[harmony]
model = "loop"
steps_per_chord = 16
[harmony.parts.A]
kind = "pedal"
degree = 1
[harmony.parts.B]
kind = "chord_loop"
loops = [{ weight = 1, chords = [
  { semitones = 0, quality = "m", steps = 16 },
  { semitones = 5, quality = "m", steps = 16 },
  { semitones = 0, quality = "m", steps = 16 },
  { semitones = 7, quality = "", steps = 16 },
] }]
[accompaniment.bass]
low = 26
high = 37
[[accompaniment.bass.motifs]]
part = "B"
bars = 2
weight = 1
reference = "tonic"
notes = [
  { step = 0, duration = 32, semitones = 0, octave = 1, velocity = 90 },
]
"""

PERCUSSION_TOML = """
low_note = 36
high_note = 38
[[patterns]]
density = 0
hits = [{ step = 0, track = "PercussionLow" }]
[[patterns]]
density = 1
hits = [
  { step = 0, track = "PercussionLow" },
  { step = 8, track = "PercussionHigh" },
  { step = 10, track = "PercussionLow" },
]
[[patterns]]
density = 2
hits = [
  { step = 0, track = "PercussionLow" },
  { step = 2, track = "PercussionHigh", note = 42 },
  { step = 4, track = "PercussionHigh", note = 42 },
  { step = 8, track = "PercussionHigh" },
  { step = 10, track = "PercussionLow" },
  { step = 12, track = "PercussionHigh", note = 42 },
]
"""

C, G, F, GSHARP = "C", "G", "F", "G#"


def _chords(first: int, roots_q: list[tuple[str, str]], score: float = 0.8) -> dict:
    return {"bars": [{"bar": first + i, "root": r, "quality": q, "score": score, "start_s": 0.0}
                     for i, (r, q) in enumerate(roots_q)]}


def _bass(first: int, midis: list[int]) -> dict:
    """Une note tenue d'une mesure par hauteur."""
    return {"voiced_ratio": 0.9,
            "notes": [{"midi": m, "start_16th": (first + i) * 16, "len_16th": 16} for i, m in enumerate(midis)]}


def _write(path: Path, bars: tuple[int, int], **voices) -> None:
    a, b = bars
    path.write_text(json.dumps({"track_id": "t1", "bars": [a, b], "source_start_s": float(a * 2),
                                "source_end_s": float(b * 2), **voices}), encoding="utf-8")


@pytest.fixture()
def fixture(tmp_path: Path):
    """Profil minimal (A pédale, B boucle i–iv–i–V) et trois boucles transcrites d'une piste `t1`."""
    prof = tmp_path / "fixture"
    prof.mkdir()
    (prof / "profile.toml").write_text(PROFILE_TOML, encoding="utf-8")
    (prof / "percussion.toml").write_text(PERCUSSION_TOML, encoding="utf-8")
    tr = tmp_path / "transcriptions"
    tr.mkdir()
    # Mesures 0–3 : do mineur tenu (= pédale de A) ; 4–7 : la boucle écrite de B.
    _write(tr / "t1_a_head.json", (0, 8),
           chords=_chords(0, [(C, "min")] * 4 + [(C, "min"), (F, "min"), (C, "min"), (G, "maj")]),
           drums={"hits": [{"class": c, "pos_16th": b * 16 + p, "time_s": 0.0, "confidence": 0.5}
                           for b in range(4) for c, p in (("kick", 0), ("hat", 4), ("snare", 8), ("hat", 12))]
                  + [{"class": "snare", "pos_16th": 2 * 16 + 2, "time_s": 0.0, "confidence": 0.1}]})
    # Mesures 8–15 : deux fois « do mineur, la bémol, do mineur, sol » (3 mesures sur 4 comme B) ; basse C-F / C-G.
    both = [(C, "min"), (GSHARP, "maj"), (C, "min"), (G, "maj")]
    _write(tr / "t1_b_tail.json", (8, 16), chords=_chords(8, both * 2),
           bass=_bass(8, [36, 41, 36, 43] * 2))
    # Doublon de mesures 4–7 avec d'autres accords : la première boucle (ordre alphabétique) l'emporte.
    _write(tr / "t1_z_dup.json", (4, 8), chords=_chords(4, [(G, "maj")] * 4))
    return load_profile(prof), tr, prof


def test_load_track_dedupes_bars_and_smooths_pedal_quality(tmp_path: Path):
    tr = tmp_path
    flicker = [(C, "min"), (C, "maj"), (C, "min"), (C, "min")]
    _write(tr / "t1_a.json", (0, 4), chords={"bars": [
        {"bar": i, "root": r, "quality": q, "score": s, "start_s": 0.0}
        for i, ((r, q), s) in enumerate(zip(flicker, [0.9, 0.5, 0.8, 0.7]))]})
    _write(tr / "t1_b.json", (2, 6), chords=_chords(2, [(G, "maj")] * 4))
    track = ex.load_track(tr, "t1", 16)
    assert {track.chords[i][1] for i in range(4)} == {"m"}     # une pédale n'oscille pas maj/min
    assert track.chords[2][0] == 0 and track.chords[3][0] == 0  # mesures 2–3 : première boucle gardée
    assert track.chords[4][0] == 7                              # mesure 4 : seule la seconde la couvre
    assert track.time_of(3) == pytest.approx(6.0)               # minutage interpolé de la première boucle (2 s par mesure)


def test_windows_start_at_each_contiguous_run():
    assert ex.windows({0, 1, 2, 3, 4, 5, 6, 7, 8}, 4) == [0, 4]
    assert ex.windows({0, 1, 2, 3, 10, 11, 12, 13, 14, 15}, 4) == [0, 10]
    assert ex.windows({0, 1, 2}, 4) == []


def test_cluster_and_medoid():
    items = [frozenset({1, 2, 3}), frozenset({1, 2, 3}), frozenset({1, 2, 4}), frozenset({9, 10})]
    groups = ex.cluster(items, ex.jaccard, 0.5)
    assert groups == [[0, 1, 2], [3]]
    assert ex.medoid([0, 1, 2], items, ex.jaccard) == 0           # égalité : plus petit indice
    assert ex.cluster(items, ex.jaccard, 1.0) == [[0, 1], [2], [3]]


def test_dejitter_absorbs_short_notes_and_resolves_overlaps():
    notes = [(40, 0, 4), (41, 4, 1), (40, 5, 3), (43, 8, 4), (45, 10, 4)]
    # 41 (1 pas) est absorbée par 40 ; 40 contigu se fond ; 45 coupe 43 au pas 10.
    assert ex.dejitter(notes) == [(40, 0, 8), (43, 8, 2), (45, 10, 4)]


def test_extraction_groups_by_frequency_and_keeps_present_alternatives_out(fixture):
    profile, tr, _ = fixture
    track = ex.load_track(tr, "t1", 16)
    result = ex.extract_profile(profile, [track], date="2026-01-01")

    chords = {(p.get("part"), p["status"]) for p in result["provenance"] if p["layer"] == "chords"}
    assert ("A", "présent") in chords                              # do mineur tenu = la pédale écrite (qualité libre)
    assert ("B", "présent") in chords                              # mesures 4–7 = la boucle écrite
    # « do m, la bémol, do m, sol » vue deux fois → un ajout de poids 2. La basse (fa sous la bémol)
    # donne un accord slash : la seconde mesure de la boucle porte `bass = 5`.
    assert [lp["weight"] for lp in result["loops"]["B"]] == [2]
    assert result["loops"]["B"][0]["chords"] == [
        {"semitones": 0, "quality": "m", "steps": 16}, {"semitones": 8, "quality": "", "bass": 5, "steps": 16},
        {"semitones": 0, "quality": "m", "steps": 16}, {"semitones": 7, "quality": "", "steps": 16}]
    assert any(p["status"] == "présent" and p["layer"] == "chords" and p["bars"] == [4, 8] for p in result["provenance"])
    # Chaque alternative porte sa provenance minutée.
    prov = next(p for p in result["provenance"] if p.get("ref") == "harmony.parts.B.loops[0]")
    assert prov["track"] == "t1" and prov["support"] == 2 and prov["start"].count(":") == 1
    assert 0 < prov["confidence"] <= 1


def test_bass_motifs_are_relative_to_the_reference_and_weighted(fixture):
    profile, tr, _ = fixture
    result = ex.extract_profile(profile, [ex.load_track(tr, "t1", 16)], date="2026-01-01")
    motifs = sorted(result["motifs"], key=lambda m: m["notes"][1]["semitones"])
    assert [m["weight"] for m in motifs] == [2, 2]                  # deux motifs vus deux fois
    assert all(m["part"] == "B" and m["bars"] == 2 and m["reference"] == "tonic" for m in motifs)
    # do tenu une mesure puis fa (5) ou sol (7) ; registre recalé sur celui du motif écrit (octave 1).
    assert [(n["step"], n["duration"], n["semitones"], n.get("octave", 0)) for n in motifs[0]["notes"]] == [
        (0, 16, 0, 1), (16, 16, 5, 1)]
    assert motifs[1]["notes"][1]["semitones"] == 7
    assert motifs[0]["notes"][1].get("legato") is True              # notes contiguës


def test_drum_consensus_and_density_by_hit_count(fixture):
    profile, tr, _ = fixture
    result = ex.extract_profile(profile, [ex.load_track(tr, "t1", 16)], date="2026-01-01")
    (pattern,) = result["patterns"]
    # Le coup parasite de la mesure 2 (< moitié des mesures) n'entre pas dans le consensus.
    assert pattern["hits"] == [
        {"step": 0, "track": "PercussionLow", "delta_velocity": 0},
        {"step": 4, "track": "PercussionHigh", "note": 42, "delta_velocity": -40},
        {"step": 8, "track": "PercussionHigh", "delta_velocity": 0},
        {"step": 12, "track": "PercussionHigh", "note": 42, "delta_velocity": -40}]
    assert pattern["weight"] == 4 and pattern["density"] == 1      # 4 coups : plus proche de la densité 1 (3) que de 2 (6)
    prov = next(p for p in result["provenance"] if p["layer"] == "drums")
    assert prov["bars_used"] == [0, 1, 2, 3] and len(prov["times"]) == 4
    assert any(g["layer"] == "drums" for g in result["gaps"])      # limite du schéma consignée


def test_pedal_part_cannot_take_alternatives_and_is_reported(fixture):
    profile, tr, _ = fixture
    # Mesures 0–3 en do mineur sauf une : proche de la pédale de A, mais différente.
    _write(tr / "t1_a_head.json", (0, 8),
           chords=_chords(0, [(C, "min")] * 3 + [(G, "maj")] + [(C, "min"), (F, "min"), (C, "min"), (G, "maj")]))
    result = ex.extract_profile(profile, [ex.load_track(tr, "t1", 16)], date="2026-01-01")
    assert "A" not in result["loops"]
    assert any(g["layer"] == "chords" and g["part"] == "A" for g in result["gaps"])


def test_proposal_is_valid_toml_in_the_engine_schema(fixture):
    profile, tr, _ = fixture
    result = ex.extract_profile(profile, [ex.load_track(tr, "t1", 16)], date="2026-01-01")
    text = ex.render_proposal(result, "v1")
    data = tomllib.loads(text)
    assert data["harmony"]["parts"]["B"]["loops"][0]["chords"][1] == {
        "semitones": 8, "quality": "", "bass": 5, "steps": 16}
    assert data["accompaniment"]["bass"]["motifs"][0]["reference"] == "tonic"
    assert data["percussion"]["patterns"][0]["density"] == 1
    assert {p["layer"] for p in data["provenance"]} == {"chords", "bass", "drums"}
    assert data["stats"]["drums"] == {"bars": 4, "groups": 1, "discarded": 0}
    assert "Aucun audio" in text


def test_balance_scales_additions_to_written_weight():
    assert p2_enrich.balance([4, 2], 3) == [2, 1]
    assert p2_enrich.balance([1, 1, 1], 1) == [1, 1, 1]            # minimum 1
    assert p2_enrich.balance([5], 0) == [5]                        # rien d'écrit : effectifs conservés


def test_enrich_copies_profile_without_touching_source(fixture, tmp_path: Path):
    profile, tr, prof_dir = fixture
    result = ex.extract_profile(profile, [ex.load_track(tr, "t1", 16)], date="2026-01-01")
    proposal = tmp_path / "p.toml"
    proposal.write_text(ex.render_proposal(result, None), encoding="utf-8")
    before = (prof_dir / "profile.toml").read_text(encoding="utf-8")

    counts = p2_enrich.enrich(prof_dir, proposal, tmp_path / "out")
    assert counts == {"loops": 1, "motifs": 2, "patterns": 1}
    assert (prof_dir / "profile.toml").read_text(encoding="utf-8") == before

    out = tomllib.loads((tmp_path / "out" / "profile.toml").read_text(encoding="utf-8"))
    loops = out["harmony"]["parts"]["B"]["loops"]
    assert [lp["weight"] for lp in loops] == [1, 1]                # poids 2 ramené au poids écrit (1)
    assert out["harmony"]["parts"]["B"]["kind"] == "chord_loop"
    assert len(out["accompaniment"]["bass"]["motifs"]) == 3
    assert [m["weight"] for m in out["accompaniment"]["bass"]["motifs"]] == [1, 1, 1]
    perc = tomllib.loads((tmp_path / "out" / "percussion.toml").read_text(encoding="utf-8"))
    assert len(perc["patterns"]) == 4 and perc["patterns"][-1]["density"] == 1

    p2_enrich.enrich(prof_dir, proposal, tmp_path / "raw", raw_weights=True)
    raw = tomllib.loads((tmp_path / "raw" / "profile.toml").read_text(encoding="utf-8"))
    assert [lp["weight"] for lp in raw["harmony"]["parts"]["B"]["loops"]] == [1, 2]
