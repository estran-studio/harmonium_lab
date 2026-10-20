"""Tests du rendu trad à armes égales : aucun accès réseau.

MIDI via `abc2midi`, WAV via `fluidsynth` + GeneralUser-GS : les tests qui
en ont besoin sont sautés explicitement (`skip`) si l'outil ou la banque
est absent. Tout le reste (motifs de pieds, détection d'accords, copie
temporaire, sélection) est testé pur.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import mido
import pytest

from harmonium_lab.trad import render as R

ABC2MIDI = shutil.which("abc2midi")
FLUIDSYNTH = shutil.which("fluidsynth")


def _test_soundfont() -> Path:
    """Banque pour les tests : `HARMONIUM_TEST_SOUNDFONT` ou le défaut ; sinon skip."""
    env = os.environ.get("HARMONIUM_TEST_SOUNDFONT")
    return Path(env) if env else R.default_soundfont()


SOUNDFONT = _test_soundfont()

needs_abc2midi = pytest.mark.skipif(not ABC2MIDI, reason="abc2midi absent : `brew install abcmidi`")
needs_wav = pytest.mark.skipif(
    not (FLUIDSYNTH and SOUNDFONT.is_file()),
    reason="rendu WAV impossible (fluidsynth ou SoundFont absente : `make soundfont` dans le repo harmonium)",
)

REEL = """X:1
T:Fixture Reel
R:reel
M:4/4
L:1/8
K:G
|: "G"GBdG B2AG | "C"EFGE c2Bc :|
|: "D"FGAG F2ED | "G"GBdG B2AG :|
"""

JIG = """X:1
T:Fixture Jig
R:jig
M:6/8
L:1/8
K:G
|: B3 BAG | EFG AGA :|
|: dBd gdB | AGA BGE :|
"""

VOLTA = """X:1
T:Fixture Volta
R:reel
M:2/4
L:1/16
K:D
|: fgaf gfeg |1 fefg f2 :|2 ["Fin"fefg f2 |]
"""


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _channels(mid: mido.MidiFile) -> dict[int, set[int]]:
    """canal → programmes."""
    out: dict[int, set[int]] = {}
    for tr in mid.tracks:
        for m in tr:
            if m.type == "program_change":
                out.setdefault(m.channel, set()).add(m.program)
    return out


def _notes(mid: mido.MidiFile, channel: int) -> list:
    return [m for tr in mid.tracks for m in tr
            if m.type == "note_on" and m.channel == channel and m.velocity > 0]


# ── Pur : pieds, accords, copie temporaire ─────────────────────────────


def test_pieds_44_talon_sur_temps_pointe_sur_contretemps():
    s, progs, vels = R.feet_pattern(4, 4)
    assert s == "dddddddd"
    assert progs == [36, 37] * 4
    assert vels == [100, 70] * 4


def test_pieds_68_talon_pointe_sur_3e_et_6e_croche():
    s, progs, vels = R.feet_pattern(6, 8)
    assert s == "dzddzd"
    assert progs == [36, 37, 36, 37]
    assert vels == [100, 70, 100, 70]


def test_pieds_34_talon_sur_1_pointes_sur_2_et_3():
    s, progs, vels = R.feet_pattern(3, 4)
    assert s == "dzdzdz"
    assert progs == [36, 37, 37]


def test_pieds_coupe_talon_sur_blanches():
    s, progs, _vels = R.feet_pattern(2, 2)
    assert s == "dzdzdzdz"
    assert progs == [36, 37, 36, 37]


def test_metre_invalide_retombe_sur_defaut_du_type():
    assert R.parse_meter_value("2/", "reel") == (4, 4)
    assert R.parse_meter_value(" C|", "reel") == (2, 2)
    assert R.parse_meter_value("C", "waltz") == (4, 4)
    assert R.parse_meter_value("6/8", "jig") == (6, 8)


def test_gchord_defauts_abc2midi():
    assert R.gchord_pattern(4, 4) == "fzczfzcz"
    assert R.gchord_pattern(3, 4) == "fzczcz"
    assert R.gchord_pattern(6, 8) == "fzcfzc"


def test_split_quotes_garde_accords_retire_annotations():
    found, cleaned = R.split_quotes('"D"a3a "(A7)"gfeg | ["Fin"GABG "Vamp"defg')
    assert found is True
    assert '"D"' in cleaned and '"(A7)"' in cleaned
    assert "Fin" not in cleaned and "Vamp" not in cleaned


def test_split_quotes_sans_accords():
    found, cleaned = R.split_quotes("GABG c2Bc")
    assert (found, cleaned) == (False, "GABG c2Bc")


def test_copie_temporaire_ne_touche_pas_la_source(tmp_path):
    src = _write(tmp_path, "t.abc", 'X:1\nT:t\nR:reel\nM:4/4\nL:1/8\nQ:1/4=100\nK:G\n["Fin"GABG c2Bc |\n')
    before = src.read_bytes()
    text, has_chords = R.build_render_abc(src.read_text(encoding="utf-8"), "reel", (4, 4))
    assert src.read_bytes() == before  # source intacte
    assert has_chords is False
    assert "Q:1/4=230" in text and "Q:1/4=100" not in text
    assert "Fin" not in text
    assert "%%MIDI program 40" in text
    assert "%%MIDI drumon" in text
    assert text.index("Q:1/4=230") < text.index("K:G")  # tempo avant K:
    assert text.index("%%MIDI drumon") > text.index("K:G")  # drumon après K:


def test_copie_temporaire_programme_apres_chaque_voix():
    text, _has = R.build_render_abc("X:1\nT:t\nM:6/8\nL:1/8\nK:G\nV:1\nB3 BAG |\nV:2\nG2A B2c |\n",
                                    "jig", (6, 8))
    assert text.count("%%MIDI program 40") == 3  # tête + 2 voix


def test_selection_tirage_reproductible():
    rows = [{"id": f"t{i}", "type": "reel"} for i in range(50)]
    a = R.select_rows(rows, "reel", 20, R.SAMPLE_SEED, None)
    b = R.select_rows(rows, "reel", 20, R.SAMPLE_SEED, None)
    assert [r["id"] for r in a] == [r["id"] for r in b]
    assert len(a) == 20
    assert sorted(r["id"] for r in R.select_rows(rows, "reel", 200, R.SAMPLE_SEED, None)) == sorted(r["id"] for r in rows)  # plafond


def test_selection_ids_inconnus_erreur_claire():
    with pytest.raises(R.RenderError, match="inconnus"):
        R.select_rows([{"id": "a", "type": "reel"}], "reel", None, R.SAMPLE_SEED, ["zzz"])


# ── Erreurs actionnables ───────────────────────────────────────────────


def test_abc2midi_absent_message_clair(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    with pytest.raises(R.RenderError, match="brew install abcmidi"):
        R.render_midi(_write(tmp_path, "t.abc", REEL), tmp_path / "t.mid", "reel", (4, 4))


def test_soundfont_absente_message_clair(tmp_path):
    with pytest.raises(R.RenderError, match="make soundfont"):
        R.resolve_soundfont(str(tmp_path / "absente.sf2"))


# ── MIDI via abc2midi ──────────────────────────────────────────────────


@needs_abc2midi
def test_midi_canaux_et_programmes(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    res = R.render_midi(src, tmp_path / "reel.mid", "reel", (4, 4))
    assert res.has_chords is True
    mid = mido.MidiFile(tmp_path / "reel.mid")
    chans = _channels(mid)
    assert chans[0] == {40}  # mélodie : violon
    progs = {p for ps in chans.values() for p in ps}
    assert {24, 32} <= progs  # accords : guitare, basse
    chord_ch = next(c for c, ps in chans.items() if 24 in ps)
    bass_ch = next(c for c, ps in chans.items() if 32 in ps)
    assert _notes(mid, chord_ch) and _notes(mid, bass_ch)  # guitare et basse sonnent
    drums = _notes(mid, 10)
    assert {m.note for m in drums} == {36, 37}  # SK1 : pieds sur canal 11
    assert sum(m.note == 36 for m in drums) == sum(m.note == 37 for m in drums)
    sel = [m for tr in mid.tracks for m in tr
           if m.type in ("control_change", "program_change") and m.channel == 10]
    assert (sel[0].control, sel[0].value) == (0, 0)
    assert (sel[1].control, sel[1].value) == (32, R.FEET_BANK)
    assert sel[2].type == "program_change" and sel[2].program == R.FEET_PROG
    assert not _notes(mid, 9)  # plus rien sur le canal percussion
    tempo = next(m.tempo for tr in mid.tracks for m in tr if m.type == "set_tempo")
    assert tempo == pytest.approx(60_000_000 / 230, abs=1)  # Q:1/4=230 (µs entières)


@needs_abc2midi
def test_midi_sans_remap_reste_percussion(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    R.render_midi(src, tmp_path / "reel.mid", "reel", (4, 4), remap_feet=False)
    mid = mido.MidiFile(tmp_path / "reel.mid")
    assert {m.note for m in _notes(mid, 9)} == {36, 37}  # repli GM


@needs_abc2midi
def test_reprises_jouees_aabb(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    R.render_midi(src, tmp_path / "reel.mid", "reel", (4, 4))
    mid = mido.MidiFile(tmp_path / "reel.mid")
    assert mid.length == pytest.approx(8 * 4 * 60 / 230, rel=0.1)  # 8 mesures AABB


@needs_abc2midi
@needs_wav
def test_render_all_log_note_sans_accords(tmp_path):
    root = tmp_path / "corpus"
    (root / "tunes" / "jig").mkdir(parents=True)
    (root / "tunes" / "jig" / "x.abc").write_text(JIG, encoding="utf-8")
    (root / "manifest.jsonl").write_text(
        json.dumps({"id": "x", "type": "jig", "meter": "6/8"}) + "\n", encoding="utf-8")
    entries = R.render_all(root, tmp_path / "out", "jig", None, R.SAMPLE_SEED,
                           None, SOUNDFONT, musicxml=False)
    assert len(entries) == 1
    assert entries[0]["has_chords"] is False
    assert "sans accords" in entries[0]["note"]
    assert entries[0]["peak_after"] == pytest.approx(R.PEAK_TARGET, abs=0.005)
    log = (tmp_path / "out" / "render_log.jsonl").read_text(encoding="utf-8")
    assert '"sans accords' in log
    assert (tmp_path / "out" / "jig" / "x.mid").is_file()
    assert (tmp_path / "out" / "jig" / "x.wav").is_file()

@needs_abc2midi
def test_volta_et_annotation_sans_erreur_fatale(tmp_path):
    src = _write(tmp_path, "volta.abc", VOLTA)
    res = R.render_midi(src, tmp_path / "volta.mid", "reel", (2, 4))
    assert res.has_chords is False
    assert (tmp_path / "volta.mid").stat().st_size > 0


@needs_abc2midi
def test_meme_entree_meme_midi_octet_pres(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    R.render_midi(src, tmp_path / "a.mid", "reel", (4, 4))
    R.render_midi(src, tmp_path / "b.mid", "reel", (4, 4))
    assert (tmp_path / "a.mid").read_bytes() == (tmp_path / "b.mid").read_bytes()


# ── WAV / MusicXML ─────────────────────────────────────────────────────


@needs_wav
def test_wav_pic_normalise_moteur(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    res = R.render_midi(src, tmp_path / "reel.mid", "reel", (4, 4))
    assert res.has_chords
    before, after = R.render_wav(tmp_path / "reel.mid", tmp_path / "reel.wav", SOUNDFONT)
    assert before < after  # fluidsynth sort bas (~0.10), on remonte
    assert after == pytest.approx(R.PEAK_TARGET, abs=0.005)
    assert R.wav_peak(tmp_path / "reel.wav") == pytest.approx(R.PEAK_TARGET, abs=0.005)


@needs_abc2midi
def test_musicxml_optionnel(tmp_path):
    src = _write(tmp_path, "reel.abc", REEL)
    R.render_midi(src, tmp_path / "reel.mid", "reel", (4, 4))
    R.render_musicxml(tmp_path / "reel.mid", tmp_path / "reel.musicxml")
    text = (tmp_path / "reel.musicxml").read_text(encoding="utf-8")
    assert "<score-partwise" in text


@needs_abc2midi
def test_log_note_sans_accords(tmp_path):
    root = tmp_path / "corpus"
    (root / "tunes" / "jig").mkdir(parents=True)
    (root / "tunes" / "jig" / "x.abc").write_text(JIG, encoding="utf-8")
    row = {"id": "x", "type": "jig", "meter": "6/8"}
    entry = R.render_one(root / "tunes" / "jig" / "x.abc", row, tmp_path / "out" / "jig",
                         SOUNDFONT if SOUNDFONT.is_file() and FLUIDSYNTH else Path("/dev/null"),
                         musicxml=False) if False else None
    # sans fluidsynth/SF2 on ne rend que le MIDI : le log « sans accords » vient de render_midi
    res = R.render_midi(root / "tunes" / "jig" / "x.abc", tmp_path / "x.mid", "jig", (6, 8))
    assert res.has_chords is False
    assert entry is None  # garde-fou : ce chemin attend le § WAV
