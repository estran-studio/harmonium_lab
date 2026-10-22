"""Extraction D7 : cellules, harmonie et tempos du corpus pour le moteur.

`mine_cells` lit les airs ABC d'un type, situe chaque mesure dans sa partie
de 8 via `harmonium_lab.trad.form` (rôles positionnels), classe le reste par
intervalles (`run` / `arp` / `turn`, règle documentée) et ne garde que les
cellules valides selon les règles de `harmonium_core::trad::cells`
(`validate_cell`, réplique Python ; vérification croisée par le parseur Rust
du moteur : `make check-cells`, soit `harmonium-cli --check-cells`).
Les airs `croche` sont ignorés pour les rôles positionnels mais gardés
pour les cellules neutres.
"""

from __future__ import annotations

import datetime
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from .cells import bar_to_cell, pitch_to_degree
from .features import chord_degree_label
from .form import analyze_form
from .model import Note, normalize_mode

IONIAN = [0, 2, 4, 5, 7, 9, 11]

ROLES = ("open", "run", "arp", "turn", "cad_half", "cad_full")


def degree_to_semitones(degree: int) -> int:
    """Degré -> demi-tons (octave ionienne, comme la validation moteur)."""
    step = degree - 1 if degree >= 1 else degree
    octave, idx = divmod(step, 7)
    return octave * 12 + IONIAN[idx]


def degree_to_step(degree: int) -> int:
    """Degré -> pas diatoniques (comme `degree_to_diatonic_step` moteur)."""
    return degree - 1 if degree >= 1 else degree


def parse_degree_token(token: str) -> int | None:
    """Jeton (`1`, `8`, `5,`, `-`) -> degré moteur ou None (tenue)."""
    token = token.strip()
    if token == "-":
        return None
    if token.endswith(","):
        return int(token[:-1]) - 8
    return int(token)


def validate_cell(notes: str, expected: int = 8) -> str | None:
    """Réplique Python des règles `Cell::validate` (+ compte de croches).

    Retourne None si valide, sinon un code de rejet stable : `mauvais-nombre`,
    `commence-par-tenue`, `degré-hors-plage`, `ambitus-dépassé`,
    `trop-de-grands-sauts`. L'ambitus et les sauts se mesurent en ionien,
    comme le moteur (`Mode::Ionian`), quelle que soit la modalité de l'air.
    """
    tokens = notes.split()
    if len(tokens) != expected:
        return "mauvais-nombre"
    try:
        degrees = [parse_degree_token(t) for t in tokens]
    except ValueError:
        return "degré-hors-plage"
    if degrees[0] is None:
        return "commence-par-tenue"
    attacked = [d for d in degrees if d is not None]
    for i, d in enumerate(attacked):
        if d is not None and (d == 0 or not -7 <= d <= 14):
            return "degré-hors-plage"
    steps = [degree_to_step(d) for d in attacked]
    semis = [degree_to_semitones(d) for d in attacked]
    if max(steps) - min(steps) > 7:
        return "ambitus-dépassé"
    if degree_to_semitones(max(attacked, key=degree_to_semitones)) - degree_to_semitones(
        min(attacked, key=degree_to_semitones)
    ) > 12:
        return "ambitus-dépassé"
    leaps = sum(
        1
        for a, b, c, e in zip(steps, steps[1:], semis, semis[1:])
        if abs(b - a) > 4 or abs(e - c) > 7
    )
    if leaps > 1:
        return "trop-de-grands-sauts"
    return None


def classify_cell(midies: list[int], tonic_pc: int, mode: str) -> str:
    """Rôle `run` / `arp` / `turn` par intervalles (règle documentée).

    Sur les degrés attaqués : `arp` si la moitié au moins des intervalles
    sont des tierces (3-4 demi-tons) ; `run` si le mouvement est conjoint
    (>= 70 % à <= 2 demi-tons) avec au plus 2 changements de direction ;
    `turn` si conjoint mais tourbillonnant (>= 3 changements) ou, sinon,
    si les changements dominent ; repli `run` (note tenue).
    """
    degrees = [pitch_to_degree(m, tonic_pc, mode) for m in midies]
    if len(degrees) < 2:
        return "run"
    semis = [abs(b - a) for a, b in zip(midies, midies[1:])]
    steps = [degree_to_step(b) - degree_to_step(a) for a, b in zip(degrees, degrees[1:])]
    thirds = sum(1 for s in semis if 3 <= s <= 4) / len(semis)
    stepwise = sum(1 for s in semis if s <= 2) / len(semis)
    signs = [1 if s > 0 else -1 if s < 0 else 0 for s in steps]
    changes = sum(
        1 for a, b in zip(signs, signs[1:]) if a != 0 and b != 0 and a != b
    )
    if thirds >= 0.5:
        return "arp"
    if stepwise >= 0.7:
        return "run" if changes <= 2 else "turn"
    if changes >= 3:
        return "turn"
    return "arp"


def _bar_sig(notes: list[tuple[Fraction, Fraction, int | None]]) -> tuple:
    return tuple((p, float(o), float(d)) for o, d, p in notes if p is not None)


def _to_notes(notes: list[tuple[Fraction, Fraction, int | None]]) -> list[Note]:
    return [
        Note(pitch=p, onset=round(float(o), 3), duration=round(float(d), 3))
        for o, d, p in notes
        if p is not None
    ]


def mine_cells(
    corpus_root: Path | str,
    tune_type: str,
    top_per_role: int = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Cellules d'un type : (cellules triées, statistiques).

    Longueur homogène : le compte de croches majoritaire du type (8 pour
    le reel) ; les airs d'une autre métrique sont ignorés + comptés, car
    la banque moteur exige des cellules de longueur uniforme.
    Tri par rôle : (-compte, notes). `stats` contient les rejets par raison,
    les unités 4+4 notées et les airs `croche` écartés du positionnel.
    """
    root = Path(corpus_root)
    files = sorted((root / "tunes" / tune_type).glob("*.abc"))
    counts: Counter[tuple[str, str]] = Counter()
    rejects: Counter[str] = Counter()
    stats: dict[str, Any] = {
        "tune_type": tune_type,
        "airs_lus": 0,
        "airs_erreur": 0,
        "airs_autre_metre_ignores": 0,
        "airs_croche_positionnel_ignore": 0,
        "mesures_vues": 0,
        "unites_8": 0,
        "unites_4plus4_notees": 0,
        "unites_16_scindees_notees": 0,
        "passes_autres_ignorees": 0,
        "cellules_neutres_croche": 0,
    }
    meters: Counter[int] = Counter()
    plans: list[tuple[Path, Any]] = []
    for path in files:
        try:
            plan = analyze_form(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            stats["airs_erreur"] += 1
            rejects[f"air-illisible:{type(e).__name__}"] += 1
            continue
        meters[plan.eighths_per_bar] += 1
        plans.append((path, plan))
    # Longueur cible : la plus fréquente (égalité -> la plus grande).
    target = max(meters, key=lambda k: (meters[k], k)) if meters else 8
    stats["croches_par_mesure"] = target
    for path, plan in plans:
        if plan.eighths_per_bar != target:
            stats["airs_autre_metre_ignores"] += 1
            continue
        stats["airs_lus"] += 1
        k = plan.eighths_per_bar
        mode = normalize_mode(plan.mode)
        bars = plan.bars
        full = [i for i, (_, _, _, ok) in enumerate(bars) if ok]

        def emit(bar_idx: int, role: str | None) -> None:
            notes, _, _, ok = bars[bar_idx]
            if not ok:
                return
            cell = bar_to_cell(_to_notes(notes), plan.key_tonic_pc, mode, k)
            reason = validate_cell(cell, expected=k)
            if reason is not None:
                rejects[reason] += 1
                return
            if role is None:
                role = classify_cell([p for _, _, p in notes if p is not None],
                                     plan.key_tonic_pc, mode)
            counts[(role, cell)] += 1

        if plan.scheme == "croche":
            stats["airs_croche_positionnel_ignore"] += 1
            for i in full:
                emit(i, None)
                stats["cellules_neutres_croche"] += 1
        units: list[list[int]] = []
        idx = 0
        pass_list = [list(p) for p in plan.passes]
        while idx < len(pass_list):
            cur = [i for i in pass_list[idx] if i in full]
            nxt = [i for i in pass_list[idx + 1] if i in full] if idx + 1 < len(pass_list) else []
            if len(cur) == 8:
                units.append(cur)
                stats["unites_8"] += 1
                idx += 1
            elif len(cur) == 4 and len(nxt) == 4 and _pass_sig(bars, cur) == _pass_sig(bars, nxt):
                units.append(cur + nxt)
                stats["unites_4plus4_notees"] += 1
                idx += 2
            elif len(cur) == 16 and _splittable_16(bars, cur):
                units.append(cur[:8])
                units.append(cur[8:])
                stats["unites_16_scindees_notees"] += 1
                idx += 1
            else:
                stats["passes_autres_ignorees"] += 1
                idx += 1

        for unit in units:
            stats["mesures_vues"] += len(unit)
            # Mesures 5-6 copies de 1-2 : ignorées (pas de double compte).
            copies = (
                len(unit) >= 6
                and _bar_sig(bars[unit[4]][0]) == _bar_sig(bars[unit[0]][0])
                and _bar_sig(bars[unit[5]][0]) == _bar_sig(bars[unit[1]][0])
            )
            for pos, bar_idx in enumerate(unit, start=1):
                if copies and pos in (5, 6):
                    continue
                if pos == 1:
                    emit(bar_idx, "open")
                elif pos == 4:
                    emit(bar_idx, "cad_half")
                elif pos == 8:
                    emit(bar_idx, "cad_full")
                else:
                    emit(bar_idx, None)

    cells = [
        {"role": role, "notes": notes, "count": count}
        for (role, notes), count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))
    ]
    top: list[dict[str, Any]] = []
    for role in ROLES:
        top.extend([c for c in cells if c["role"] == role][:top_per_role])
    return top, {**stats, "rejets": dict(sorted(rejects.items()))}


def _pass_sig(bars: list, idxs: list[int]) -> tuple:
    return tuple(_bar_sig(bars[i][0]) for i in idxs)


def _splittable_16(bars: list, idxs: list[int]) -> bool:
    """16 mesures : moitiés identiques, ou 6+ communes (fins propres)."""
    first = [_bar_sig(bars[i][0]) for i in idxs[:8]]
    second = [_bar_sig(bars[i][0]) for i in idxs[8:]]
    return first == second or first[:6] == second[:6]


def render_bank(
    cells: list[dict[str, Any]],
    tune_type: str,
    corpus_version: str,
    n_airs: int,
    date: str,
) -> str:
    """TOML au format exact du moteur (`cells = [{ role, notes }, ...]`).

    Pas de champ `weight` : le parseur serde du moteur l'ignorerait
    silencieusement (`RawCell` n'a que `role` + `notes`) ; les poids vont
    dans le compagnon JSON.
    """
    lines = [
        f"# Cellules minées du corpus trad ({tune_type}) — voir D7.",
        "#",
        f"# corpus: {corpus_version} ({n_airs} airs), miné le {date}.",
        "# Notation et invariants : cf. harmonium_core::trad::cells.",
        "# Poids (fréquences) : fichier compagnon .weights.json.",
        "cells = [",
    ]
    for role in ROLES:
        for cell in [c for c in cells if c["role"] == role]:
            lines.append(f'  {{ role = "{role}", notes = "{cell["notes"]}" }},')
    lines.append("]")
    return "\n".join(lines) + "\n"


_ENGINE_CELL = re.compile(r'\{\s*role\s*=\s*"([^"]+)"\s*,\s*notes\s*=\s*"([^"]+)"\s*\}')


def load_engine_bank(path: Path | str) -> list[tuple[str, str]]:
    """Banque actuelle du moteur : [(rôle, notes)] depuis son TOML."""
    return _ENGINE_CELL.findall(Path(path).read_text(encoding="utf-8"))


def mine_harmony(corpus_root: Path | str, tune_type: str) -> dict[str, Any]:
    """Accords par position et rythme harmonique, bigrammes, par mode."""
    root = Path(corpus_root)
    files = sorted((root / "tunes" / tune_type).glob("*.abc"))
    by_position: dict[str, Counter] = {}
    cadences: dict[str, Counter] = {"m4": Counter(), "m8": Counter()}
    bigrams: Counter[str] = Counter()
    by_mode: dict[str, Counter] = {}
    chord_counts: Counter[str] = Counter()
    rhythm: Counter[str] = Counter()
    half_rhythm: Counter[str] = Counter()
    n_airs = 0
    for path in files:
        try:
            plan = analyze_form(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        n_airs += 1
        mode = normalize_mode(plan.mode)
        k = plan.eighths_per_bar
        labels: list[str] = []
        for notes, bar_chords, pass_idx, ok in plan.bars:
            ordered = sorted(bar_chords, key=lambda c: float(c[0]))
            if ordered:
                rhythm[str(len(ordered))] += 1
                first_half = sum(1 for offset, _ in ordered if float(offset) < k / 2)
                half_rhythm[f"{first_half}+{len(ordered) - first_half}"] += 1
            for offset, symbol in ordered:
                label = chord_degree_label(symbol, plan.key_tonic_pc, mode)
                labels.append(label)
                chord_counts[label] += 1
                by_mode.setdefault(mode, Counter())[label] += 1
        for a, b in zip(labels, labels[1:]):
            bigrams[f"{a}->{b}"] += 1
        if plan.scheme == "croche":
            continue
        units: list[list[int]] = []
        for p in plan.passes:
            full = [i for i in p if plan.bars[i][3]]
            if len(full) == 8:
                units.append(full)
        for unit in units:
            for pos, bar_idx in enumerate(unit, start=1):
                _, bar_chords, _, _ = plan.bars[bar_idx]
                for offset, symbol in sorted(bar_chords, key=lambda c: float(c[0])):
                    label = chord_degree_label(symbol, plan.key_tonic_pc, mode)
                    half = 0 if float(offset) < k / 2 else 1
                    by_position.setdefault(f"mesure_{pos}/demi_{half}", Counter())[label] += 1
                    if pos == 4:
                        cadences["m4"][label] += 1
                    if pos == 8:
                        cadences["m8"][label] += 1
    return {
        "tune_type": tune_type,
        "airs": n_airs,
        "par_position": {k: dict(sorted(v.items())) for k, v in sorted(by_position.items())},
        "mesure_4": dict(sorted(cadences["m4"].items())),
        "mesure_8": dict(sorted(cadences["m8"].items())),
        "bigrammes": dict(sorted(bigrams.items())),
        "par_mode": {m: dict(sorted(v.items())) for m, v in sorted(by_mode.items())},
        "rythme_harmonique_par_mesure": dict(sorted(rhythm.items(), key=lambda item: int(item[0]))),
        "rythme_harmonique_dominant": max(rhythm, key=lambda item: (rhythm[item], -int(item))) if rhythm else None,
        "rythme_harmonique_par_demi_mesure": dict(sorted(half_rhythm.items())),
        "accompagnement": {
            "source": "convention métrique; motifs proposés, non mesurés dans l’ABC",
            "mesure_3_4": {"basse": [1], "accord": [2, 3]},
            "mesure_6_8": {"basse_croche": [1, 4], "accord_croche": [3, 6]},
        },
        "top_accords": [{"degre": d, "n": n} for d, n in chord_counts.most_common(12)],
    }


_Q_BPM = re.compile(r"Q:\s*(?:(\d+)\s*/\s*(\d+)\s*=\s*)?(\d+)")


def mine_tempo(corpus_root: Path | str, tune_type: str | None = None) -> dict[str, Any]:
    """Tempos `Q:` et signatures par type ; signale quand l'info manque."""
    root = Path(corpus_root)
    types = [tune_type] if tune_type else sorted(p.name for p in (root / "tunes").iterdir() if p.is_dir())
    out: dict[str, Any] = {"types": {}, "q_manquant": []}
    for t in types:
        bpms: list[int] = []
        meters: Counter[str] = Counter()
        n = 0
        for path in sorted((root / "tunes" / t).glob("*.abc")):
            n += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^M:\s*(\S+)", text, re.M)
            if m:
                meters[m.group(1)] += 1
            q = re.search(r"^Q:\s*(.+)$", text, re.M)
            if q:
                qb = _Q_BPM.match("Q:" + q.group(1).strip())
                if qb and qb.group(3).isdigit():
                    bpms.append(int(qb.group(3)))
        entry: dict[str, Any] = {"airs": n, "signatures": dict(meters)}
        if bpms:
            bpms.sort()
            entry["tempo_q"] = {
                "n": len(bpms),
                "min": bpms[0],
                "mediane": bpms[len(bpms) // 2],
                "max": bpms[-1],
            }
        else:
            entry["tempo_q"] = None
            out["q_manquant"].append(t)
        out["types"][t] = entry
    return out


def corpus_version(root: Path | str) -> str:
    """Version du corpus (fichier VERSION, 1re ligne)."""
    return (Path(root) / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()


def today() -> str:
    return datetime.date.today().isoformat()
