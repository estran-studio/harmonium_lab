"""Tests for the preliminary trad style-profile bundle."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from harmonium_lab.trad import mine as M
from harmonium_lab.trad.profile_draft import build_profile_draft, write_profile_draft

JIG = """X:1
T:Mini jig
R:jig
M:6/8
L:1/8
Q:3/8=120
K:G
|: "G"GABcBA | "D"AGFEDG | "G"GABcBA | "D"AGFEDG | "G"GABcBA | "C"cBAGFE | "D"AGFEDG | "G"GABcBA :|
"""

WALTZ = """X:2
T:Mini waltz
R:waltz
M:3/4
L:1/8
K:D
|: "D"D2F A2F | "G"G2B d2B | "D"A2F D2F | "A"E2G A2c | "D"d2f a2f | "G"g2b g2a | "Em"e2g f2e | "D"F2A D3 :|
"""


def trad_corpus(root: Path, tune_type: str, abc: str) -> Path:
    tunes = root / "tunes" / tune_type
    tunes.mkdir(parents=True)
    (tunes / "mini.abc").write_text(abc, encoding="utf-8")
    (root / "VERSION").write_text("test+1\n", encoding="utf-8")
    return root


def test_six_eighth_cell_validation_and_mining(tmp_path: Path) -> None:
    corpus = trad_corpus(tmp_path, "jig", JIG)
    assert M.validate_cell("1 2 3 4 3 2", expected=6) is None
    assert M.validate_cell("1 2 3 4 3 2") == "mauvais-nombre"

    cells, stats = M.mine_cells(corpus, "jig")
    assert stats["croches_par_mesure"] == 6
    assert stats["airs_lus"] == 1
    assert stats["cellules_valides_par_role"]["open"] >= 1
    assert stats["occurrences_valides_par_role"]["open"] >= stats["cellules_valides_par_role"]["open"]
    assert all(len(cell["notes"].split()) == 6 for cell in cells)
    assert all(M.validate_cell(cell["notes"], expected=6) is None for cell in cells)
    assert any(cell["role"] == "open" for cell in cells)
    assert any(cell["role"] == "cad_half" for cell in cells)
    assert any(cell["role"] == "cad_full" for cell in cells)


def test_profile_draft_has_named_sections_weights_and_sources(tmp_path: Path) -> None:
    corpus = trad_corpus(tmp_path / "corpus", "jig", JIG)
    profile = build_profile_draft(corpus, "jig")
    out = write_profile_draft(profile, tmp_path / "draft")
    draft = tomllib.loads((out / "profile.toml").read_text(encoding="utf-8"))

    assert draft["meta"]["name"] == "jig"
    assert draft["meter"]["signature"] == "6/8"
    assert draft["meter"]["default_tempo"] == 120
    assert profile["harmony"]["rythme_harmonique_dominant"] == "1"
    assert draft["accompaniment"]["jig_bass_eighths"] == [1, 4]
    assert draft["percussion"]["source"] == "convention métrique; pas mesuré dans les ABC"
    assert draft["melody"]["cells"]
    assert all(cell["weight"] > 0 and len(cell["notes"].split()) == 6 for cell in draft["melody"]["cells"])
    assert json.loads((out / "harmony.json").read_text())["rythme_harmonique_dominant"] == "1"
    assert "pas mesurés dans l’ABC" in (out / "README.md").read_text(encoding="utf-8")


def test_waltz_meter_is_six_eighths_and_form_report_runs(tmp_path: Path, capsys) -> None:
    corpus = trad_corpus(tmp_path, "waltz", WALTZ)
    profile = build_profile_draft(corpus, "waltz")
    cells, stats = M.mine_cells(corpus, "waltz")
    from harmonium_lab.cli import main

    assert profile["meter"] == {"3/4": 1}
    assert stats["croches_par_mesure"] == 6
    assert cells
    assert all(len(cell["notes"].split()) == 6 for cell in cells)
    assert all(M.validate_cell(cell["notes"], expected=6) is None for cell in cells)
    assert main(["trad-form-report", "--type", "waltz", "--corpus", str(corpus)]) == 0
    report = capsys.readouterr().out
    assert "3/4" in report and "longueurs de parties" in report and "levées (croches)" in report


MARCH_4_4 = """X:10
T:British March 4/4
R:march
M:4/4
L:1/8
K:D
|: "D"D2F2 A2d2 | "G"B2d2 "A"A4 | "D"d2fd "A"e2c2 | "D"d4 d4 :|
|: "D"f2d2 a2f2 | "G"g2e2 "A"e4 | "D"f2d2 "A"e2c2 | "D"d4 d4 :|
"""

MARCH_2_4 = """X:11
T:British March 2/4
R:march
M:2/4
L:1/8
K:D
|: "D"DF Ad | "G"Bd "A"A2 | "D"df "A"ec | "D"d2 d2 :|
|: "D"fd af | "G"ge "A"e2 | "D"fd "A"ec | "D"d2 d2 :|
"""


def test_profile_draft_tradition_from_manifest_and_cell_length(tmp_path: Path) -> None:
    root = tmp_path / "british_corpus"
    tunes = root / "tunes" / "march"
    tunes.mkdir(parents=True)
    (tunes / "march_4_4.abc").write_text(MARCH_4_4, encoding="utf-8")
    (root / "VERSION").write_text("v1\n", encoding="utf-8")
    (root / "manifest.jsonl").write_text(
        json.dumps({
            "id": "march-1",
            "tradition": "britannique_coloniale",
            "type": "march",
        }) + "\n",
        encoding="utf-8",
    )

    profile = build_profile_draft(root, "march")
    assert profile["tradition"] == "britannique_coloniale"
    assert profile["tunes"] == 1

    out = write_profile_draft(profile, tmp_path / "draft")
    draft = tomllib.loads((out / "profile.toml").read_text(encoding="utf-8"))
    assert draft["meta"]["tradition"] == "britannique_coloniale"
    assert draft["meter"]["steps_per_bar"] == 8
    assert draft["melody"]["cell_length"] == 8
    assert draft["melody"]["cell_length"] != 0


def test_profile_draft_mixed_meters_filtering(tmp_path: Path) -> None:
    root = tmp_path / "mixed_corpus"
    tunes = root / "tunes" / "march"
    tunes.mkdir(parents=True)
    (tunes / "m1.abc").write_text(MARCH_4_4, encoding="utf-8")
    (tunes / "m2.abc").write_text(MARCH_4_4.replace("British March 4/4", "Second 4/4"), encoding="utf-8")
    (tunes / "m3.abc").write_text(MARCH_2_4, encoding="utf-8")
    (root / "VERSION").write_text("v1\n", encoding="utf-8")
    (root / "manifest.jsonl").write_text(
        json.dumps({"id": "m1", "tradition": "britannique_coloniale", "type": "march"}) + "\n",
        encoding="utf-8",
    )

    # Sans option : sélectionne la famille majoritaire (8 croches : 2 airs sur 3)
    p_auto = build_profile_draft(root, "march")
    assert p_auto["tunes"] == 2
    assert p_auto["target_eighths"] == 8
    assert p_auto["majority_selected"] is True
    out_auto = write_profile_draft(p_auto, tmp_path / "draft_auto")
    readme = (out_auto / "README.md").read_text(encoding="utf-8")
    assert "Famille métrique majoritaire sélectionnée automatiquement : 8 croches" in readme
    draft_auto = tomllib.loads((out_auto / "profile.toml").read_text(encoding="utf-8"))
    assert draft_auto["melody"]["cell_length"] == 8

    # Option --eighths-per-bar 4 : sélectionne le 2/4 (1 air)
    p_4 = build_profile_draft(root, "march", eighths_per_bar=4)
    assert p_4["tunes"] == 1
    assert p_4["target_eighths"] == 4
    out_4 = write_profile_draft(p_4, tmp_path / "draft_4")
    draft_4 = tomllib.loads((out_4 / "profile.toml").read_text(encoding="utf-8"))
    assert draft_4["melody"]["cell_length"] == 4

    # Option --meter 4/4 : sélectionne les 2 airs en 4/4
    p_m = build_profile_draft(root, "march", meter="4/4")
    assert p_m["tunes"] == 2


def test_cli_profile_draft_default_output(tmp_path: Path, monkeypatch) -> None:
    from harmonium_lab.cli import main

    monkeypatch.chdir(tmp_path)
    root = tmp_path / "corpus_b"
    tunes = root / "tunes" / "march"
    tunes.mkdir(parents=True)
    (tunes / "m1.abc").write_text(MARCH_4_4, encoding="utf-8")
    (root / "VERSION").write_text("v1\n", encoding="utf-8")
    (root / "manifest.jsonl").write_text(
        json.dumps({"id": "m1", "tradition": "britannique_coloniale", "type": "march"}) + "\n",
        encoding="utf-8",
    )

    rc = main(["profile-draft", "--type", "march", "--corpus", str(root)])
    assert rc == 0
    expected_dir = tmp_path / "target" / "profiles" / "britannique_coloniale-march"
    assert expected_dir.exists()
    assert (expected_dir / "profile.toml").exists()
    assert (expected_dir / "README.md").exists()
    draft = tomllib.loads((expected_dir / "profile.toml").read_text(encoding="utf-8"))
    assert draft["meta"]["tradition"] == "britannique_coloniale"
    assert draft["melody"]["cell_length"] == 8
