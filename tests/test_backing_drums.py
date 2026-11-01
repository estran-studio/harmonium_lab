"""Tests de `harmonium_lab.backing.drums` : fixtures SYNTHÉTIQUES seulement (aucun brut GMD)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import mido
import pretty_midi
import pytest

from harmonium_lab.backing import corpus_cache, drums
from harmonium_lab.backing.drums import FileRow, Hit, Measure, Performance

RIDE, KICK, SNARE, PEDAL = 51, 36, 38, 44


def midi_bytes(notes: list[tuple[float, int, int]], bpm: float = 120.0) -> bytes:
    """MIDI de batterie en mémoire : `(position en pulsations, hauteur, vélocité)`, tempo constant."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, is_drum=True)
    spb = 60.0 / bpm
    for beat, pitch, vel in notes:
        inst.notes.append(pretty_midi.Note(velocity=vel, pitch=pitch, start=beat * spb, end=beat * spb + 0.05))
    pm.instruments.append(inst)
    buffer = io.BytesIO()
    pm.write(buffer)
    return buffer.getvalue()


def swung_ride(n_beats: int, ratio: float, start: float = 0.0) -> list[tuple[float, int, int]]:
    """Ride : noire sur chaque pulsation et croche retardée au rapport `ratio` aux pulsations 2 et 4."""
    notes = []
    for b in range(n_beats):
        notes.append((start + b, RIDE, 80))
        if b % 2 == 1:
            notes.append((start + b + ratio, RIDE, 60))
    return notes


def row(path: str = "d1/a.mid", style: str = "jazz", beat_type: str = "beat", bpm: int = 120,
        duration: float = 10.0) -> FileRow:
    return FileRow(path, "d1", "d1/s1", path[:-4], style, bpm, beat_type, "4-4", duration, "train")


# ---------------------------------------------------------------- table Roland → GM → rôles


def test_table_roland_vers_roles_et_gm():
    expected = {
        36: ("kick", 36), 38: ("snare", 38), 40: ("snare", 38), 37: ("snare", 37),
        42: ("hat_closed", 42), 22: ("hat_closed", 42), 46: ("hat_open", 46), 26: ("hat_open", 46),
        44: ("hat_pedal", 44), 51: ("ride", 51), 59: ("ride", 51), 53: ("ride", 53),
        49: ("crash", 49), 55: ("crash", 49), 57: ("crash", 49), 52: ("crash", 49),
        43: ("tom", 43), 45: ("tom", 47), 48: ("tom", 50), 58: ("tom", 43),
    }
    for pitch, (role, gm) in expected.items():
        assert drums.role_of(pitch) == role, pitch
        assert drums.gm_note(pitch) == gm, pitch
    assert drums.role_of(99) is None
    assert drums.gm_note(99) is None


def test_groupes_de_styles_et_filtre_4_4():
    assert drums.group_of("jazz") == "core"
    assert drums.group_of("jazz/swing") == "core"
    assert drums.group_of("jazz/funk") == "jazz_other"
    assert drums.group_of("jazz/march") == "jazz_other"
    assert drums.group_of("neworleans/funk") == "neworleans"
    assert drums.group_of("blues/shuffle") == "blues_shuffle"
    assert drums.group_of("rock") is None
    assert drums.group_of("blues/other") is None
    base = {"drummer": "d1", "session": "d1/s", "id": "d1/s/1", "bpm": "120", "beat_type": "beat",
            "duration": "10.5", "split": "train"}
    rows = [
        {**base, "style": "jazz", "time_signature": "4-4", "midi_filename": "b.mid"},
        {**base, "style": "jazz", "time_signature": "3-4", "midi_filename": "a.mid"},
        {**base, "style": "rock", "time_signature": "4-4", "midi_filename": "c.mid"},
        {**base, "style": "blues/shuffle", "time_signature": "4-4", "midi_filename": "a2.mid"},
    ]
    kept = drums.select_rows(rows)
    assert [r.path for r in kept] == ["a2.mid", "b.mid"]
    manifest = drums.manifest_rows(kept)
    assert all(m["licence"] == "CC-BY-4.0" for m in manifest)
    assert all(set(m) >= {"path", "style", "bpm", "beat_type", "time_signature", "duration", "split", "drummer"}
               for m in manifest)


# ---------------------------------------------------------------- rapport de swing et quantification


@pytest.mark.parametrize("ratio", [0.5, 0.6, 2 / 3, 0.72])
def test_rapport_de_swing_du_midi_synthetique(ratio):
    perf = drums.read_performance(midi_bytes(swung_ride(40, ratio) , bpm=130))
    assert perf is not None
    measured, n = drums.swing_ratio(perf.hits)
    assert n == 20
    assert measured == pytest.approx(ratio, abs=0.005)


def test_rapport_de_swing_charleston_en_repli_et_sans_contretemps():
    # Pas de ride : le charleston fermé donne le rapport.
    hat = [(b + (0.6 if b % 2 else 0.0), 42, 70) for b in range(30)]
    hat += [(b + 0.6, 42, 70) for b in range(1, 30, 2)]
    measured, _ = drums.swing_ratio(drums.read_performance(midi_bytes(hat)).hits)
    assert measured == pytest.approx(0.6, abs=0.01)
    # Seulement des noires : aucun contretemps, pas de rapport ; repli triolet.
    quarters = [(float(b), RIDE, 80) for b in range(40)]
    measured, n = drums.swing_ratio(drums.read_performance(midi_bytes(quarters)).hits)
    assert measured is None and n == 0
    assert drums.effective_ratio(None) == pytest.approx(2 / 3)
    assert drums.effective_ratio(0.4) == 0.5 and drums.effective_ratio(0.95) == 0.8


def test_ride_prioritaire_sur_charleston_pour_le_rapport():
    # Ride swingué (0,667) + charleston droit (0,5) : le ride l'emporte.
    notes = swung_ride(40, 2 / 3) + [(b + 0.5, 42, 50) for b in range(40)]
    measured, _ = drums.swing_ratio(drums.read_performance(midi_bytes(notes)).hits)
    assert measured == pytest.approx(2 / 3, abs=0.005)


def test_quantification_triolet_vers_pas_2():
    r = 2 / 3
    assert drums.quantize(0.0, r) == (0, 0)
    assert drums.quantize(2 / 3, r) == (0, 2)
    assert drums.quantize(1 + 2 / 3, r) == (1, 2)
    assert drums.quantize(0.34, r) == (0, 1)
    assert drums.quantize(0.84, r) == (0, 3)
    assert drums.quantize(0.97, r) == (1, 0)  # juste avant le temps suivant
    assert drums.quantize(3.99, r) == (4, 0)  # → premier pas de la mesure suivante
    # Swing droit : les pas sont des doubles croches régulières.
    assert [drums.quantize(x, 0.5)[1] for x in (0.0, 0.25, 0.5, 0.75)] == [0, 1, 2, 3]
    # Même attaque, rapport différent : 0,6 de la pulsation est le pas 2 à r = 0,6 mais le pas 1 à r = 0,8.
    assert drums.quantize(0.6, 0.6) == (0, 2)
    assert drums.quantize(0.45, 0.8)[1] == 1


def test_attaques_swinguees_tombent_sur_les_pas_attendus():
    notes = swung_ride(16, 0.62) + [(0.0, KICK, 90), (2.0, KICK, 90), (1.0, SNARE, 40)]
    perf = drums.read_performance(midi_bytes(notes))
    measured, _ = drums.swing_ratio(perf.hits)
    measures = drums.measures_of(perf, row(duration=8.0), drums.effective_ratio(measured))
    assert len(measures) == 4
    ride_steps = {m.role_steps("ride") for m in measures}
    assert ride_steps == {(0, 4, 6, 8, 12, 14)}
    assert measures[0].role_steps("kick") == (0, 8)
    assert measures[0].role_steps("snare") == (4,)
    assert drums.ride_class(measures[1]) == "spang_a_lang"


# ---------------------------------------------------------------- mesures entières


def test_mesure_incomplete_finale_ignoree():
    # 2,5 mesures de ride aux noires : la troisième est incomplète.
    notes = [(float(b), RIDE, 80) for b in range(10)]
    perf = drums.read_performance(midi_bytes(notes))
    assert perf.end_beat < 10.5
    measures = drums.measures_of(perf, row(), 2 / 3)
    assert len(measures) == 2


def test_premiere_mesure_entree_en_cours_ignoree_et_mesure_vide_ignoree():
    # Silence 0..5, ride dès la pulsation 5 (en cours de mesure 1), 3 mesures entières ensuite.
    notes = [(float(b), RIDE, 80) for b in range(5, 17)]
    perf = drums.read_performance(midi_bytes(notes))
    measures = drums.measures_of(perf, row(), 2 / 3)
    # Mesure 0 vide (ignorée), mesure 1 entrée au 2ᵉ temps (ignorée), mesures 2 et 3 entières.
    assert len(measures) == 2
    assert all(m.role_steps("ride") == (0, 4, 8, 12) for m in measures)


def test_fichier_de_relance_court_garde_sa_mesure_mais_pas_un_beat():
    notes = [(0.0, SNARE, 90), (1.0, 48, 90), (2.0, 45, 90), (2.5, 43, 90), (3.0, 36, 90)]
    perf = drums.read_performance(midi_bytes(notes))
    # Le fichier s'arrête à la dernière attaque : 3,1 pulsations (0,78 mesure).
    assert 3.0 < perf.end_beat < 3.3
    assert len(drums.measures_of(perf, row(beat_type="fill"), 2 / 3)) == 1
    assert len(drums.measures_of(perf, row(beat_type="beat"), 2 / 3)) == 0
    # Une relance qui ne couvre que la moitié d'une mesure n'est pas gardée.
    short = drums.read_performance(midi_bytes(notes[:3]))
    assert len(drums.measures_of(short, row(beat_type="fill"), 2 / 3)) == 0


def test_tempo_variable_sans_effet_sur_les_positions_en_pulsations():
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(100), time=0))
    for b in range(8):
        if b == 4:
            track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(140), time=0))
        track.append(mido.Message("note_on", note=RIDE, velocity=80, time=0 if b == 0 else 480))
    buffer = io.BytesIO()
    mid.save(file=buffer)
    perf = drums.read_performance(buffer.getvalue())
    assert [h.beat for h in perf.hits] == [float(b) for b in range(8)]


def test_metrique_non_4_4_refusee():
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0))
    track.append(mido.Message("note_on", note=KICK, velocity=80, time=0))
    buffer = io.BytesIO()
    mid.save(file=buffer)
    assert drums.read_performance(buffer.getvalue()) is None


# ---------------------------------------------------------------- agrégats


def make_measure(file: str, ride=(), kick=(), snare=(), pedal=(), ride_vel=80, kick_vel=70) -> Measure:
    m = Measure(file, "jazz", "beat", 2 / 3)
    for role, steps, vel, note in (("ride", ride, ride_vel, 51), ("kick", kick, kick_vel, 36),
                                   ("snare", snare, 50, 38), ("hat_pedal", pedal, 60, 44)):
        if steps:
            m.steps[role] = {s: (vel, note) for s in steps}
    return m


def test_probabilites_par_pas_sur_mini_corpus():
    spang = (0, 4, 6, 8, 12, 14)
    measures = (
        [make_measure("a", ride=spang, kick=(0,), pedal=(4, 12)) for _ in range(4)]
        + [make_measure("b", ride=spang, snare=(6,)) for _ in range(4)]
        + [make_measure("c", ride=(), kick=(0, 8)) for _ in range(2)]
    )
    stats = drums.group_stats(measures)
    assert stats["n_measures"] == 10 and stats["n_files"] == 3
    assert stats["max_file_share"] == pytest.approx(0.4)
    ride = stats["per_step"]["ride"]
    assert ride[0]["prob"] == pytest.approx(0.8) and ride[0]["n"] == 8
    assert ride[1]["prob"] == 0 and "velocity" not in ride[1]
    assert ride[6]["prob"] == pytest.approx(0.8)
    assert stats["per_step"]["kick"][0]["prob"] == pytest.approx(0.6)
    assert stats["per_step"]["kick"][8]["prob"] == pytest.approx(0.2)
    assert stats["per_step"]["snare"][6]["prob"] == pytest.approx(0.4)
    pedal = stats["densities"]["hat_pedal_beats_2_4"]
    assert pedal["n_both_steps_4_and_12"] == 4 and pedal["share_both"] == pytest.approx(0.4)
    assert stats["densities"]["kick_on_beat_1"]["share"] == pytest.approx(0.6)
    assert stats["densities"]["snare_offbeat_steps_2_6_10_14"]["share"] == pytest.approx(0.4)
    assert stats["densities"]["hits_per_measure"]["ride"]["p50"] == 6.0
    figures = stats["ride_figures"]["classes"]
    assert figures["spang_a_lang"]["n"] == 8 and figures["none"]["n"] == 2
    assert sum(c["share"] for c in figures.values()) == pytest.approx(1.0)
    # Vélocité relative : part de la médiane du rôle (ride constant à 80 → 1,0).
    assert ride[0]["rel_velocity"]["mean"] == pytest.approx(1.0)
    assert ride[0]["velocity"]["p50"] == 80


def test_top_patterns_exigent_deux_fichiers():
    spang = (0, 4, 6, 8, 12, 14)
    measures = [make_measure("a", ride=spang) for _ in range(5)] + [make_measure("b", ride=spang)] \
        + [make_measure("a", ride=(0, 1, 2)) for _ in range(9)]  # motif d'un seul fichier : jamais listé
    top = drums.top_patterns(measures)
    ride = top["ride"]
    assert ride[0]["steps"] == list(spang) and ride[0]["n"] == 6 and ride[0]["n_files"] == 2
    assert all(p["steps"] != [0, 1, 2] for p in ride)
    assert ride[0]["share"] == pytest.approx(6 / 15)


def test_accent_du_contretemps_du_ride():
    measures = []
    for f in "ab":
        for _ in range(12):
            m = Measure(f, "jazz", "beat", 2 / 3)
            m.steps["ride"] = {0: (100, 51), 2: (50, 51), 4: (100, 51), 6: (50, 51)}
            measures.append(m)
    accent = drums.ride_accent(measures)
    assert accent["offbeat_over_on_beat_mean"] == pytest.approx(0.5)
    assert accent["per_file_median_ratio"]["p50"] == pytest.approx(0.5)


def test_patterns_proposes_construits_sur_les_probabilites_par_pas():
    spang = (0, 4, 6, 8, 12, 14)
    measures = []
    for i in range(36):  # 3 fichiers de 12 mesures, jamais deux mesures identiques entre fichiers voulues
        file = "abc"[i % 3]
        kick = (0,) if i % 5 < 3 else ()            # P(kick@0) = 0,6
        kick += (8,) if i % 5 == 4 else ()          # P(kick@8) ≈ 0,2 : sous 0,25
        snare = (6,) if i % 3 == 0 else ()          # P(snare@6) ≈ 0,33
        pedal = (4, 12) if i % 4 != 0 else ()       # P(pédale) = 0,75
        measures.append(make_measure(file, ride=spang, kick=kick, snare=snare, pedal=pedal))
    proposals = drums.proposed_patterns(measures, [])
    patterns = {p["density"]: p for p in proposals["patterns"]}
    assert set(patterns) == {0, 1, 2}
    assert all(p["weight"] == 36 for p in proposals["patterns"])
    d0 = {(h["step"], h["role"]) for h in patterns[0]["hits"]}
    assert d0 == {(s, "ride") for s in spang}
    d1 = {(h["step"], h["role"]) for h in patterns[1]["hits"]}
    assert (4, "hat_pedal") in d1 and (12, "hat_pedal") in d1 and (0, "kick") in d1
    assert (6, "snare") not in d1 and (8, "kick") not in d1  # sous 0,5
    d2 = {(h["step"], h["role"]) for h in patterns[2]["hits"]}
    assert (6, "snare") in d2 and (8, "kick") not in d2  # 0,33 ≥ 0,25 ; 0,2 < 0,25
    for p in proposals["patterns"]:
        for h in p["hits"]:
            assert set(h) == {"step", "role", "note", "rel_velocity", "velocity"}
            assert 0 <= h["step"] < 16 and h["note"] == drums.gm_note({"ride": 51, "kick": 36, "snare": 38, "hat_pedal": 44}[h["role"]])


def test_aucun_pattern_propose_depuis_un_fichier_dominant_ou_unique():
    spang = (0, 4, 6, 8, 12, 14)
    solo = [make_measure("a", ride=spang, kick=(0,)) for _ in range(40)]
    proposals = drums.proposed_patterns(solo, [])
    assert proposals["patterns"] == []
    assert proposals["skipped"] and proposals["skipped"][0]["class"] == "spang_a_lang"
    # Deux fichiers dont un à 70 % : refusé aussi.
    dominated = solo[:28] + [make_measure("b", ride=spang) for _ in range(12)]
    assert drums.proposed_patterns(dominated, [])["patterns"] == []


# ---------------------------------------------------------------- empreinte, archive, déterminisme


def make_archive(path: Path) -> None:
    """Archive GMD synthétique : `info.csv` et trois fichiers MIDI de ride swingué (r = 0,62)."""
    info = ["drummer,session,id,style,bpm,beat_type,time_signature,midi_filename,audio_filename,duration,split"]
    with zipfile.ZipFile(path, "w") as z:
        for i, file in enumerate(("a", "b", "c")):
            notes = swung_ride(48, 0.62) + [(float(b), KICK, 80 + i) for b in range(0, 48, 4)] \
                + [(b + 1.0, SNARE, 50) for b in range(0, 48, 4)]
            name = f"drummer{i}/session1/{i}_jazz_120_beat_4-4.mid"
            z.writestr(f"groove/{name}", midi_bytes(notes))
            info.append(f"drummer{i},drummer{i}/session1,drummer{i}/session1/{i},jazz,120,beat,4-4,{name},,24.0,train")
        z.writestr("groove/drummer9/s/9_rock_90_beat_4-4.mid", b"pas lu")
        info.append("drummer9,drummer9/s,drummer9/s/9,rock/pop,90,beat,4-4,drummer9/s/9_rock_90_beat_4-4.mid,,5.0,train")
        z.writestr("groove/info.csv", "\n".join(info) + "\n")


def test_sha256_errone_est_refuse(tmp_path):
    bad = tmp_path / "groove.zip"
    bad.write_bytes(b"pas la bonne archive")
    with pytest.raises(corpus_cache.DigestError, match="SHA256 différent"):
        drums.open_archive(bad)
    with pytest.raises(FileNotFoundError):
        drums.open_archive(tmp_path / "absent.zip")


def test_pipeline_synthetique_et_determinisme(tmp_path):
    archive_path = tmp_path / "g.zip"
    make_archive(archive_path)
    outputs = []
    for _ in range(2):
        with zipfile.ZipFile(archive_path) as archive:
            rows = drums.read_info(archive)
            assert [r.drummer for r in rows] == ["drummer0", "drummer1", "drummer2"]  # le rock est écarté
            data = drums.build_measures(archive, rows)
        outputs.append(corpus_cache.dumps_json(data))
    assert outputs[0] == outputs[1]
    data = json.loads(outputs[0])
    assert data["core"]["beat"]["n_measures"] == 36 and data["core"]["beat"]["n_files"] == 3
    ratios = data["swing_ratio"]["by_style"]["jazz"]
    assert ratios["n_files_measured"] == 3 and ratios["p50"] == pytest.approx(0.62, abs=0.005)
    assert data["provenance"]["licence"] == "CC-BY-4.0" and data["provenance"]["sha256"] == drums.SOURCE_SHA256
    kick0 = data["core"]["beat"]["per_step"]["kick"][0]
    assert kick0["prob"] == pytest.approx(1.0)
    # Aucune suite de notes brute n'est stockée : seules des clés agrégées.
    assert "notes" not in data["core"]["beat"]
    assert data["core"]["beat"]["ride_figures"]["classes"]["spang_a_lang"]["share"] > 0.9
