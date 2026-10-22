"""Tests du corpus trad : aucun accès réseau (fixtures ABC, caches pré-remplis, `offline`)."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import pytest

from harmonium_lab.trad import corpus as C
from harmonium_lab.trad.abcnorm import (
    AbcError,
    analyse,
    decode_abc_text,
    intervals,
    parse_key,
    parse_tune,
    split_tunes,
    title_key,
    type_from_text,
)
from harmonium_lab.trad.download import Fetcher, list_abc_files

FIX = Path(__file__).parent / "fixtures" / "trad"


def _raw(name: str, source: str = C.CHAMBERS, hint: str | None = None, url: str | None = None) -> list[C.RawTune]:
    blocks = split_tunes((FIX / name).read_text(encoding="utf-8"))
    return [
        C.RawTune(source=source, origin=f"{name}#X{i}", url=url or f"fixture://{name}#{i}", block=b,
                  type_hint=hint, because="fixture", fallback_title=name)
        for i, b in enumerate(blocks, 1)
    ]


def _build(tmp_path: Path, raws: list[C.RawTune], today: dt.date = dt.date(2026, 1, 2)):
    return C.build(tmp_path / "trad", Fetcher(offline=True), today=today, raw_tunes=raws)


# ── Analyse ABC ──────────────────────────────────────────────────────


def test_analyse_reel_meter_bars_incipit():
    tune = parse_tune(split_tunes((FIX / "reel_bastringue.abc").read_text())[0])
    a = analyse(tune)
    assert (a.meter, a.key, a.mode, a.bars) == ("2/2", "D", "majeur", 16)
    # f2ff f2gf | e2c2 d4  en ré majeur : do dièse issu de la armure
    assert a.incipit == [78, 78, 78, 78, 79, 78, 76, 73, 74]


def test_anacrusis_is_not_a_bar_nor_in_incipit():
    block = "X:1\nT:t\nM:4/4\nL:1/8\nK:C\nG2 | c2 c2 e2 g2 | e4 c4 | d2 d2 f2 a2 | g8 |"
    a = analyse(parse_tune(block))
    assert a.bars == 4
    assert a.incipit[0] == 72  # c, pas le sol d'anacrouse


def test_dotted_rhythm_and_accidentals_fill_the_measure():
    # c>d e<f g2 = 3/2 + 1/2 + 1/2... : mesure complète seulement si > et < sont comptés.
    block = "X:1\nT:t\nM:4/4\nL:1/8\nK:C\nc>d e<f g2 g2 | ^f=fg^f g8 | c8 |"
    a = analyse(parse_tune(block))
    assert a.bars == 3  # pas d'anacrouse : la première mesure est pleine
    # dièse persistant dans la mesure puis bécarre : f♯ (78) f♮ (77) g f♯ (78)
    assert a.incipit[6:10] == [78, 77, 79, 78]


@pytest.mark.parametrize(
    "k,tonic,mode",
    [("D", "D", "majeur"), ("Em", "E", "mineur"), ("A dor", "A", "dorien"),
     ("G mix", "G", "mixolydien"), ("F#m", "F#", "mineur"), ("Bb", "Bb", "majeur"), ("Dmajor", "D", "majeur")],
)
def test_parse_key(k, tonic, mode):
    info = parse_key(k)
    assert (info.tonic, info.mode) == (tonic, mode)


def test_key_signature_applies_to_pitches():
    a = analyse(parse_tune("X:1\nT:t\nM:4/4\nL:1/8\nK:G\nF8 | f8 |"))
    assert a.incipit == [66, 78]  # fa dièse implicite en sol majeur
    with pytest.raises(AbcError) as exc:
        parse_key("_")
    assert exc.value.reason == C.REJECT_PARSE


def test_abc_escapes_decoded_and_title_key_ignores_accents_articles():
    assert decode_abc_text("Qu\\'ebec \\`a la gaspesie") == "Québec à la gaspesie"
    assert decode_abc_text("Fran\\,cois") == "François"
    assert title_key("La Bastringue") == title_key("bastringue") == title_key("Bâstringue!")


def test_type_from_text():
    assert type_from_text("reel") == "reel"
    assert type_from_text("Gigue du Forgeron") == "jig"
    assert type_from_text("Valse des Poêles") == "waltz"
    assert type_from_text("slip jig") is None
    assert type_from_text("polka") is None
    assert type_from_text("Bridal Festival Quadrille Fig 3") == "quadrille"
    assert type_from_text("Cotillion des Dames") == "cotillon"


def test_split_tunes_ignores_preamble():
    blocks = split_tunes((FIX / "multi_airs.abc").read_text())
    assert len(blocks) == 3 and all(b.startswith("X:") for b in blocks)


def test_list_abc_files_keeps_only_plain_abc_names():
    html = '<a href="/~jc/x/">p</a><a href="a%20b.abc">1</a><a href="b.txt">2</a><a href="sub/">3</a><a href="C.ABC">4</a>'
    assert list_abc_files(html) == ["C.ABC", "a b.abc"]


# ── Pipeline : rejets, multi-airs, dédoublonnage ─────────────────────


def test_multi_tune_file_is_split_and_typed(tmp_path):
    kept, stats, _ = _build(tmp_path, _raw("multi_airs.abc"))
    assert sorted((c.type, c.mode) for c in kept) == [("jig", "majeur"), ("reel", "dorien"), ("waltz", "mineur")]
    waltz = next(c for c in kept if c.type == "waltz")
    assert waltz.bars == 8  # l'anacrouse « E | » n'est pas comptée
    assert (tmp_path / "trad" / "tunes" / "waltz" / f"{waltz.id}.abc").exists()


def test_rejections_are_counted_with_reasons(tmp_path):
    raws = _raw("sans_cle.abc") + _raw("sans_melodie.abc") + _raw("reel_bastringue.abc")
    raws.append(C.RawTune(C.CHAMBERS, "bad#X1", "u", "X:1\nT:x\nR:reel\nM:4/4\nK:_\nabc|", None, "f", "x"))
    kept, stats, _ = _build(tmp_path, raws)
    assert len(kept) == 1
    assert stats.reject_reasons[(C.CHAMBERS, C.REJECT_NO_KEY)] == 1
    assert stats.reject_reasons[(C.CHAMBERS, C.REJECT_NO_MELODY)] == 1
    assert stats.reject_reasons[(C.CHAMBERS, C.REJECT_PARSE)] == 1
    rejects = [json.loads(line) for line in (tmp_path / "trad" / "rejects.jsonl").read_text().splitlines()]
    assert {r["reason"] for r in rejects} == {C.REJECT_NO_KEY, C.REJECT_NO_MELODY, C.REJECT_PARSE}
    assert all(r["origin"] for r in rejects)


def test_untyped_tune_is_ignored_not_rejected(tmp_path):
    block = "X:1\nT:Polka du coin\nR:polka\nM:2/4\nK:G\nGABc|"
    raw = C.RawTune(C.CHAMBERS, "p#X1", "u", block, None, "f", "p")
    kept, stats, _ = _build(tmp_path, [raw])
    assert kept == [] and stats.ignored[C.CHAMBERS] == 1 and not stats.rejected


def test_transposed_duplicate_across_sources_is_merged_keeping_chambers(tmp_path):
    jc = _raw("reel_bastringue.abc", C.CHAMBERS, url="http://jc/b.abc")
    ts = _raw("bastringue_transpose.abc", C.SESSION, url="https://thesession.org/tunes/1")
    kept, stats, _ = _build(tmp_path, ts + jc)  # l'ordre d'entrée ne compte pas
    assert len(kept) == 1
    keeper = kept[0]
    assert keeper.source == C.CHAMBERS
    assert [a["source"] for a in keeper.also_in] == [C.SESSION]
    assert stats.merged[("reel", C.SESSION)] == 1


def test_same_title_different_incipit_is_not_merged(tmp_path):
    other = (FIX / "bastringue_transpose.abc").read_text().replace("b2bb b2c'b", "g2gg a2c'b", 1)
    raw = C.RawTune(C.SESSION, "o#X1", "u", other, None, "f", "o")
    kept, _, _ = _build(tmp_path, _raw("reel_bastringue.abc") + [raw])
    assert len(kept) == 2


def test_same_source_duplicate_keeps_the_version_with_most_chords(tmp_path):
    bare = (FIX / "reel_bastringue.abc").read_text()
    bare = "\n".join(line for line in bare.splitlines() if not line.startswith("T:")).replace("X: 1", "X: 1\nT: Bastringue")
    bare = re.sub(r'"[^"]*"', "", bare)
    raws = [
        C.RawTune(C.CHAMBERS, "a#X1", "http://jc/a", bare, "reel", "f", "a"),
        *_raw("reel_bastringue.abc", url="http://jc/b"),
    ]
    kept, stats, _ = _build(tmp_path, raws)
    assert len(kept) == 1 and kept[0].url == "http://jc/b"
    assert [a["url"] for a in kept[0].also_in] == ["http://jc/a"]
    assert stats.merged[("reel", C.CHAMBERS)] == 1


def test_manifest_is_sorted_complete_and_deterministic(tmp_path):
    raws = _raw("multi_airs.abc") + _raw("reel_bastringue.abc") + _raw("bastringue_transpose.abc", C.SESSION)
    _build(tmp_path, raws)
    root = tmp_path / "trad"
    first = (root / "manifest.jsonl").read_bytes()
    version = (root / "VERSION").read_text()
    # Rejeu un autre jour, entrée mélangée : manifeste et VERSION identiques.
    _build(tmp_path, list(reversed(raws)), today=dt.date(2030, 5, 5))
    assert (root / "manifest.jsonl").read_bytes() == first
    assert (root / "VERSION").read_text() == version
    rows = [json.loads(line) for line in first.decode().splitlines()]
    assert [r["id"] for r in rows] == sorted(r["id"] for r in rows)
    required = {"id", "title", "aliases", "tradition", "type", "meter", "key", "mode", "bars", "source", "url",
                "license", "sha256", "included_because", "incipit"}
    assert all(required <= set(r) for r in rows)
    bast = next(r for r in rows if r["key"] == "D" and r["type"] == "reel" and "Bastringue" in r["title"])
    assert bast["title"] == "la Bastringue"
    assert "Bastringue des Ménetriers" in bast["aliases"]  # échappement ABC décodé
    assert version.startswith("2026-01-02+") and version.splitlines()[0].endswith(f"+{len(rows)}")


def test_version_date_changes_when_corpus_changes(tmp_path):
    _build(tmp_path, _raw("reel_bastringue.abc"))
    _build(tmp_path, _raw("reel_bastringue.abc") + _raw("multi_airs.abc"), today=dt.date(2026, 3, 4))
    assert (tmp_path / "trad" / "VERSION").read_text().startswith("2026-03-04+4")


def test_normalised_abc_always_has_xtmlk_headers(tmp_path):
    block = "X:9\nR: Reel\nP: Titre en P\nK:D\nD2 F2 A2 d2 | f8 |"  # ni T:, ni M:, ni L:
    raw = C.RawTune(C.CHAMBERS, "n#X1", "u", block, "reel", "f", "n")
    kept, stats, _ = _build(tmp_path, [raw])
    heads = {line[0] for line in kept[0].abc.splitlines() if line[1:2] == ":"}
    assert {"X", "T", "M", "L", "K", "R"} <= heads
    assert kept[0].title == "Titre en P" and kept[0].meter == "4/4" and stats.inferred_meter == 1
    assert "R:reel" in kept[0].abc


# ── The Session : filtre québécois explicable ────────────────────────


def _session_cache(tmp_path: Path) -> Path:
    base = tmp_path / "raw" / "thesession"
    base.mkdir(parents=True)

    def tune(tid, sid, name, typ, mode="Dmajor", meter="4/4"):
        return {"tune_id": tid, "setting_id": sid, "name": name, "type": typ, "meter": meter, "mode": mode,
                "abc": "|:D2FA d2fd|A2dA F2D2:|", "date": "", "username": "", "composer": ""}

    def rec(rid, artist, album, track, tune, tid):
        # Schéma réel de recordings.json : `artist` est le nom en clair.
        return {"id": rid, "artist": artist, "recording": album, "track": track, "number": "1",
                "tune": tune, "tune_id": tid}

    tunes = [
        tune("1", "10", "Ril Du Forgeron", "reel", mode="Amixolydian"),  # enregistré Bottine + alias FR
        tune("1", "11", "Ril Du Forgeron", "reel", mode="Amixolydian"),  # autre réglage (ignoré)
        tune("2", "20", "Gigue du Pendu", "jig", meter="6/8"),           # titre français
        tune("3", "30", "Cooley's", "reel", mode="Edorian"),             # irlandais : exclu
        tune("4", "40", "Valse Triste", "waltz", meter="3/4"),           # titre français
        tune("5", "50", "Slip Quelconque", "slip jig", meter="9/8"),     # type hors périmètre
        tune("6", "60", "The Old Reel", "reel"),                         # « reel » seul : pas français
        tune("7", "70", "Sangshyttevalsen", "waltz", meter="3/4"),       # suédois (« vals » ≠ valse)
        tune("8", "80", "Vals Efter Lasse I Lyby", "waltz", meter="3/4"),# suédois (« vals » ≠ valse)
        tune("9", "90", "Richmond Cotillion", "reel"),                   # anglais (pas cotillon)
        tune("10", "100", "Ettrick Vale Quadrilles", "reel"),            # écossais (pas quadrille)
        tune("11", "110", "A Jig For Christmas", "jig", meter="6/8"),    # alias anglais seulement
        tune("12", "120", "The Blacksmith", "reel"),                     # alias français déclencheur
        tune("13", "130", "Reel de Montréal", "reel"),                   # motif « reel de »
    ]
    recordings = [
        # Lignes au schéma réel (cf. corpus/trad/raw/thesession/recordings.json, id 1809) :
        rec("1809", "La Bottine Souriante", "Dance With LBS", "1", "Ril Du Forgeron", "1"),
        rec("1809", "La Bottine Souriante", "Dance With LBS", "1", "Le Reel De Forgeron", ""),
        rec("3720", "1651", "Cast A Bell", "1", "Kettledrum", "3"),
        rec("9999", "Genticorum", "Nagez Rameurs", "2", "Reel de Montréal", "13"),
    ]
    aliases = [{"tune_id": "1", "alias": "Le Reel Du Forgeron", "name": "Ril Du Forgeron"},
               {"tune_id": "3", "alias": "Cooleys", "name": "Cooley's"},
               {"tune_id": "11", "alias": "Christmas Jig", "name": "A Jig For Christmas"},
               {"tune_id": "12", "alias": "Reel du Forgeron", "name": "The Blacksmith"}]
    (base / "tunes.json").write_text(json.dumps(tunes))
    (base / "recordings.json").write_text(json.dumps(recordings))
    (base / "aliases.json").write_text(json.dumps(aliases))
    return tmp_path / "raw"


def test_session_filter_explains_each_inclusion(tmp_path):
    raw_dir = _session_cache(tmp_path)
    got = {r.url.split("/tunes/")[1].split("#")[0]: r for r in C.session_tunes(raw_dir, Fetcher(offline=True))}
    assert sorted(got, key=int) == ["1", "2", "4", "12", "13"]
    assert "La Bottine Souriante" in got["1"].because and "Dance With LBS" in got["1"].because
    assert got["1"].because_kinds == ("artist", "alias")  # titre « Ril » non français, alias oui
    assert "alias français « Le Reel Du Forgeron »" == got["1"].because.split(" ; ")[1]
    assert got["2"].because == "titre français (« gigue »)" and got["2"].because_kinds == ("title",)
    assert "Genticorum" in got["13"].because
    assert got["12"].because_kinds == ("alias",)
    assert got["1"].url.endswith("#setting10")  # réglage le plus ancien
    assert "Le Reel Du Forgeron" in got["1"].extra_aliases
    for excluded in ("6", "7", "8", "9", "10", "11"):
        assert excluded not in got


def test_quebec_artist_list_is_documented_and_big_enough():
    names = C.quebec_artist_names()
    assert len(names) >= 25 and "La Bottine Souriante" in names and "Jean Carignan" in names
    by_name = C.load_quebec_artists()
    assert by_name["la bottine souriante"] == "La Bottine Souriante"
    assert by_name["les freres brunet"] == "André Brunet" and len(by_name) >= 10


def test_french_title_patterns():
    assert C.french_match("Gigue du Pendu") == "gigue"
    assert C.french_match("Reel de Montréal") == "reel de"
    assert C.french_match("Le Réel du Pendu") == "réel"
    assert C.french_match("Quadrille des Lanciers") == "quadrille"
    assert C.french_match("Cotillon des Dames") == "cotillon"
    assert C.french_match("Valse Canadienne") == "valse"
    assert C.french_match("The Old Reel") is None
    assert C.french_match("Reel Of Tulloch") is None
    assert C.french_match("Sangshyttevalsen") is None
    assert C.french_match("Vals Efter Lasse I Lyby") is None
    assert C.french_match("Richmond Cotillion") is None
    assert C.french_match("Ettrick Vale Quadrilles") is None
    assert C.french_match("A Jig For Christmas") is None
    assert C.french_match("The Gigue") is None  # mot français, titre anglais


def test_offline_fetcher_refuses_missing_cache(tmp_path):
    with pytest.raises(RuntimeError, match="hors ligne"):
        Fetcher(offline=True).get("http://example.invalid/x", tmp_path / "x")


def test_acadian_artist_list_is_documented_and_valid():
    names = C.acadian_artist_names()
    assert len(names) >= 10 and "Barachois" in names and "Joe Cormier" in names and "Vishtèn" in names
    by_name = C.load_acadian_artists()
    assert by_name["barachois"] == "Barachois"
    assert by_name["vishten"] == "Vishtèn"
    assert by_name["joseph cormier"] == "Joe Cormier"


def test_acadian_title_patterns():
    assert C.acadian_match("Acadian Breakdown") is not None
    assert C.acadian_match("La Reel Des Acadiens") is not None
    assert C.acadian_match("Turlutte Acadienne") is not None
    assert C.acadian_match("Valse d'Acadie") is not None
    assert C.acadian_match("Reel de Montréal") is None
    assert C.acadian_match("The Old Reel") is None


def test_migrate_manifest_preserves_tune_sha256_and_sets_tradition(tmp_path):
    import hashlib
    old_row = {
        "id": "reel-test-12345678",
        "title": "Reel Test",
        "aliases": ["Alias 1"],
        "type": "reel",
        "meter": "4/4",
        "key": "D",
        "mode": "majeur",
        "bars": 16,
        "source": "chambers",
        "url": "http://jc/reel.abc",
        "license": "non précisée",
        "sha256": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "included_because": "fixture test",
        "incipit": [74, 76, 78],
    }
    manifest_file = tmp_path / "manifest.jsonl"
    manifest_file.write_text(json.dumps(old_row) + "\n", encoding="utf-8")
    old_sha = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    version_file = tmp_path / "VERSION"
    version_file.write_text(f"2026-10-19+1\nmanifest_sha256: {old_sha}\n", encoding="utf-8")

    new_sha = C.migrate_manifest(manifest_file, tradition="quebecoise")
    assert new_sha != old_sha

    migrated_lines = [json.loads(line) for line in manifest_file.read_text().splitlines() if line.strip()]
    assert len(migrated_lines) == 1
    m = migrated_lines[0]
    assert m["tradition"] == "quebecoise"
    assert m["sha256"] == old_row["sha256"]
    assert m["id"] == old_row["id"]
    assert "manifest_sha256: " + new_sha in version_file.read_text()


def test_tradition_filter_and_dispatch(tmp_path):
    raw_qc = C.RawTune(C.CHAMBERS, "q#1", "u1", "X:1\nT:Air QC\nR:reel\nM:4/4\nK:D\nD4|", "reel", "b", "Air QC", tradition="quebecoise")
    raw_acad = C.RawTune(C.CHAMBERS, "a#1", "u2", "X:2\nT:Air Acadien\nR:jig\nM:6/8\nK:G\nG3|", "jig", "b", "Air Acadien", tradition="acadienne")
    raw_brit = C.RawTune(C.NOTTINGHAM, "b#1", "u3", "X:3\nT:British March\nR:march\nM:2/4\nK:C\nC4|", "march", "b", "British March", tradition="britannique_coloniale", epoque="1809")

    kept, stats, _ = C.build(tmp_path / "custom", Fetcher(offline=True), raw_tunes=[raw_qc, raw_acad, raw_brit])
    assert len(kept) == 3
    by_trad = {c.tradition: c for c in kept}
    assert by_trad["quebecoise"].type == "reel"
    assert by_trad["acadienne"].type == "jig"
    assert by_trad["britannique_coloniale"].type == "march"
    assert by_trad["britannique_coloniale"].epoque == "1809"


def test_offline_fixture_determinism_acadienne_and_british(tmp_path):
    raws = [
        C.RawTune(C.SESSION, "acad#1", "https://thesession.org/tunes/1", "X:1\nT:Acadian Reel\nR:reel\nM:4/4\nK:D\nD2FA d2fd|", "reel", "test", "Acadian Reel", tradition="acadienne"),
        C.RawTune(C.NOTTINGHAM, "brit#1", "http://nmd/jigs#1", "X:2\nT:Country Dance\nR:jig\nM:6/8\nK:G\nG2B d2g|", "jig", "test", "Country Dance", tradition="britannique_coloniale", epoque="c. 1764"),
    ]
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"
    kept1, stats1, sha1 = C.build(dir1, Fetcher(offline=True), raw_tunes=raws, today=dt.date(2026, 1, 1))
    kept2, stats2, sha2 = C.build(dir2, Fetcher(offline=True), raw_tunes=list(reversed(raws)), today=dt.date(2026, 1, 1))

    assert sha1 == sha2
    assert (dir1 / "manifest.jsonl").read_bytes() == (dir2 / "manifest.jsonl").read_bytes()
    assert (dir1 / "VERSION").read_text() == (dir2 / "VERSION").read_text()
    assert stats1.kept == stats2.kept
