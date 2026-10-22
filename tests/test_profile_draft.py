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
    assert cells
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
