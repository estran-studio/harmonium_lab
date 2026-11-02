"""Variance par chorus et par couche (phase 019, V0) : extension de `seed-variety`.

Le moteur écrit la vérité terrain (`--record-truth`) et le MIDI (`--record-midi`) d'un air
joué `--tours N` fois. Un **chorus** est une passe de la forme (`form.sequence`, un « tour » du
moteur ; pour un profil `loop` sous grille utilisateur : la partie répétée). Le numéro de chorus
est lu dans `position.chorus` s'il existe (A3), sinon `position.tour`, sinon déduit de la
longueur de forme (`bar_in_cycle` revient à 0). Les mesures d'intro (section ≠ `Tour`) et les
airs suivants du set sont écartés. Le moteur remplace la dernière mesure de l'air par sa clôture
(accord de tonique, grosse caisse) : cette mesure est écartée (le dernier chorus n'a donc pas sa
dernière place ; les comparaisons se font sur les places communes). Une mesure est repérée par sa **place dans le chorus**
(`bar_in_cycle`) : le chorus k et le chorus j se comparent mesure à mesure, à place égale.

Deux lectures, pour chaque couche :

- **intra-graine** : pour une graine, chorus k contre chorus j ; part des mesures (actives dans
  l'un des deux chorus) dont la signature diffère (`exact`) et distance graduée moyenne (`graded`).
  Chorus voisins (k, k+1), toutes paires (k < j), « stable » = paires dont les deux chorus sont
  au rang `steady_from` ou plus (les entrées de couches par tour y sont passées). Matrice
  graine-moyennée, distribution des parts sur toutes les paires, part de paires **identiques**
  (le chorus rejoue le précédent à l'identique : la boucle) et nombre moyen de chorus distincts ;
- **inter-graines** à chorus égal : pour chaque (chorus, place), les N graines donnent N
  signatures ; part des places où elles diffèrent, diversité `(distinct − 1) / (N − 1)`, distance
  graduée moyenne par paire de graines (extension de P2) ; `distinct_runs` : nombre de séquences
  complètes (tous chorus, toutes places) distinctes parmi les N graines (N : chaque graine a la
  sienne ; 1 : la graine ne change rien à la couche).

Signatures d'une mesure, par couche (hauteurs relatives à la tonique `position.key`, vélocités et
décalages d'interprétation ignorés : l'humanisation dérive de la graine même quand le motif est
identique) :

| Couche | Notes | Éléments de la signature |
|---|---|---|
| `chords` | `chord_changes` | (pas, fondamentale, qualité, mineur, basse) |
| `comping_rhythm` | piste 1 | pas d'attaque |
| `comping_voicing` | piste 1 | hauteurs relatives triées de chaque attaque (suite dans le temps) |
| `bass` | piste 2 | (pas, hauteur, durée) |
| `drums` | pistes 3 et 4 | (piste, pas, note) |
| `drums_kick` … `drums_other` | pistes 3 et 4 | idem, filtré par rôle GM de la note |
| `melody` | pistes 0 et 5 | (piste, pas, hauteur, durée) |
| `orchestration` | MIDI + `[instruments]` | (canal, banque, programme) par piste |
| `all` | `chords`, `comping_*`, `bass`, `drums` | tuple des signatures ; la mélodie et l'orchestration restent à part |

Égalité exacte : signatures égales. Distance graduée : 1 − Jaccard des ensembles d'éléments (deux
mesures vides : 0) ; `orchestration` : part des pistes dont le programme diffère ; `all` : moyenne
des distances des couches actives dans l'une des deux mesures. Une mesure est **active** pour une
couche si au moins l'une des deux mesures comparées joue dans cette couche.

Couches numériques (par chorus, moyenne sur les mesures) : densité (notes par mesure) et
intensité (vélocité moyenne) pour toutes les notes, le comping, la basse, la batterie et la
mélodie ; `intensity` de la vérité terrain (courbe d'intensité du moteur). Intra-graine :
`adjacent_change` (|x(k+1) − x(k)| / moyenne de la série, moyenné) et `cv` (écart-type / moyenne
sur les chorus) ; inter-graines : `cv` sur les graines à chorus égal ; `trajectory` : moyenne sur
les graines à chaque chorus, `trajectory_range` : (max − min) / moyenne de cette trajectoire (un arc
sur plusieurs chorus l'élargit).
"""

from __future__ import annotations

import itertools
import json
import re
import statistics
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, NamedTuple

from . import seedvariety as sv

TICKS_PER_STEP = 120          # `midi_export.rs` : TICKS_PER_STEP
PERCUSSION_CHANNEL = 9
STEADY_FROM = 3
CORE = ("chords", "comping_rhythm", "comping_voicing", "bass", "drums")
ROLES = ("kick", "snare", "hihat", "ride", "other")
LAYERS = (*CORE, *(f"drums_{r}" for r in ROLES), "melody", "orchestration")
ALL = "all"
LAYER_LABELS = {
    "chords": "accords (symboles)", "comping_rhythm": "comping : rythme", "comping_voicing": "comping : voicings",
    "bass": "basse", "drums": "batterie", "drums_kick": "batterie : grosse caisse",
    "drums_snare": "batterie : caisse claire", "drums_hihat": "batterie : charleston",
    "drums_ride": "batterie : ride", "drums_other": "batterie : autres", "melody": "mélodie",
    "orchestration": "orchestration", ALL: "accompagnement (toutes couches)",
}
GROUPS = {"all": None, "comping": (1,), "bass": (2,), "drums": (3, 4), "melody": (0, 5)}

GM_ROLE = {35: "kick", 36: "kick", 37: "snare", 38: "snare", 39: "snare", 40: "snare",
           42: "hihat", 44: "hihat", 46: "hihat", 51: "ride", 53: "ride", 59: "ride"}


def drum_role(pitch: int) -> str:
    """Rôle GM d'une note de batterie (autres notes, cymbales crash et toms : `other`)."""
    return GM_ROLE.get(pitch, "other")


# ── Mesure ────────────────────────────────────────────────────────────────

class CBar(NamedTuple):
    """Une mesure d'un chorus : place, signatures par couche, ensembles d'éléments, mesures numériques."""
    index: int
    chorus: int
    pos: int
    part: int
    sigs: dict[str, tuple]
    sets: dict[str, frozenset]
    metrics: dict[str, float]


def make_bar(index: int, chorus: int, pos: int, sigs: dict[str, tuple], part: int = 0,
             metrics: dict[str, float] | None = None) -> CBar:
    """Mesure à partir de ses signatures (les couches absentes sont vides)."""
    full = {ly: tuple(sigs.get(ly, ())) for ly in LAYERS}
    return CBar(index, chorus, pos, part, full, {ly: frozenset(s) for ly, s in full.items()}, metrics or {})


def _group_metrics(notes: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, tracks in GROUPS.items():
        sel = [n for n in notes if tracks is None or n["track"] in tracks]
        out[f"n_{name}"] = float(len(sel))
        out[f"vel_{name}"] = float(sum(n["velocity"] for n in sel))
    return out


def chorus_of(pos: dict[str, Any]) -> int | None:
    """Numéro de chorus d'une mesure : `chorus`, sinon `tour` ; `None` hors chorus (intro, outro)."""
    if "section" in pos and pos["section"] != "Tour":
        return None
    c = pos.get("chorus", pos.get("tour"))
    return int(c) if c is not None and int(c) >= 1 else None


def bar_from_entry(entry: dict[str, Any]) -> CBar | None:
    """Entrée `measures[i]` de `--record-truth` → mesure d'un chorus (`None` hors chorus)."""
    measure = entry["measure"]
    pos = measure["position"]
    chorus = chorus_of(pos)
    if chorus is None:
        return None
    base = sv.bar_from_entry(entry)
    key = int(pos["key"])
    notes = measure["notes"]
    comp: dict[int, list[int]] = {}
    for n in notes:
        if n["track"] == 1:
            comp.setdefault(int(n["start_step"]), []).append(int(n["pitch"]) - key)
    drums = base.sigs["drums"]
    sigs = {
        "chords": base.sigs["chords"],
        "comping_rhythm": tuple(sorted(comp)),
        "comping_voicing": tuple(tuple(sorted(comp[s])) for s in sorted(comp)),
        "bass": base.sigs["bass"],
        "drums": drums,
        "melody": tuple(sorted((int(n["track"]), int(n["start_step"]), int(n["pitch"]) - key,
                                int(n["duration_steps"])) for n in notes if n["track"] in GROUPS["melody"])),
    }
    for role in ROLES:
        sigs[f"drums_{role}"] = tuple(h for h in drums if drum_role(h[2]) == role)
    metrics = _group_metrics(notes)
    metrics["intensity"] = float(entry.get("intensity", 0.0))
    return make_bar(int(entry["bar"]), chorus, int(pos.get("bar_in_cycle", -1)), sigs, int(pos["part"]), metrics)


def _with_chorus(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sans `chorus` ni `tour` dans la position : chorus déduit de la longueur de forme (le
    `bar_in_cycle` repart de 0 à chaque passe) ; les mesures hors section `Tour` restent écartées."""
    if all("chorus" in e["measure"]["position"] or "tour" in e["measure"]["position"] for e in entries):
        return entries
    out, current, last = [], 1, -1
    for e in entries:
        pos = dict(e["measure"]["position"])
        cyc = int(pos.get("bar_in_cycle", 0))
        if cyc <= last:
            current += 1
        last = cyc
        pos["tour"] = current
        out.append({**e, "measure": {**e["measure"], "position": pos}})
    return out


def load_truth(path: Path, max_bars: int | None = None) -> list[CBar]:
    """Mesures de chorus du premier air d'un fichier `--record-truth`, mesure de clôture exclue (elle
    remplace la dernière mesure de l'air ; reconnue quand un air suit dans le fichier). Sans
    `bar_in_cycle`, la place est déduite du rang dans le chorus."""
    data = json.loads(path.read_text(encoding="utf-8"))
    first_tune = [e for e in data["measures"]
                  if (max_bars is None or e["bar"] <= max_bars) and e["measure"]["position"]["tune_index"] == 0]
    if first_tune and any(e["measure"]["position"]["tune_index"] > 0 for e in data["measures"]):
        first_tune.pop(max(range(len(first_tune)), key=lambda i: first_tune[i]["bar"]))   # clôture de l'air
    bars = [b for b in map(bar_from_entry, _with_chorus(first_tune)) if b is not None]
    if any(b.pos < 0 for b in bars):
        count: dict[int, int] = {}
        ranked = []
        for b in bars:
            ranked.append(b._replace(pos=count.get(b.chorus, 0)))
            count[b.chorus] = count.get(b.chorus, 0) + 1
        bars = ranked
    return bars


# ── Orchestration : programmes par piste et par mesure ────────────────────

def instruments_of(profile_dir: Path) -> dict[int, tuple[int, int]]:
    """`[instruments]` du profil → `{canal: (banque, programme)}` (percussion : canal 9)."""
    data = tomllib.loads((profile_dir / "profile.toml").read_text(encoding="utf-8")).get("instruments", {})
    out: dict[int, tuple[int, int]] = {}
    for channel, name in ((0, "melody_program"), (1, "chords_program"), (2, "bass_program"),
                          (5, "countermelody_program")):
        if name in data:
            out[channel] = (0, int(data[name]))
    if "percussion_program" in data:
        out[PERCUSSION_CHANNEL] = (int(data.get("percussion_bank", 128)), int(data["percussion_program"]))
    return out


def midi_programs(path: Path) -> list[tuple[int, int, int]]:
    """Changements de programme du MIDI : `(tick, canal, programme)` triés."""
    import mido
    events = []
    for track in mido.MidiFile(str(path)).tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "program_change":
                events.append((tick, msg.channel, msg.program))
    return sorted(events)


def orchestration_sigs(base: dict[int, tuple[int, int]], events: list[tuple[int, int, int]],
                       bar_starts: dict[int, int]) -> dict[int, tuple]:
    """Signature d'orchestration de chaque mesure : `((canal, banque, programme), …)`. Départ :
    `[instruments]` ; un `program_change` du MIDI au tick ≤ début de mesure remplace le programme
    de son canal à partir de cette mesure."""
    current = dict(base)
    out: dict[int, tuple] = {}
    pending = iter(events)
    nxt = next(pending, None)
    for index in sorted(bar_starts):
        while nxt is not None and nxt[0] <= bar_starts[index]:
            current[nxt[1]] = (current.get(nxt[1], (0, 0))[0], nxt[2])
            nxt = next(pending, None)
        out[index] = tuple((ch, b, p) for ch, (b, p) in sorted(current.items()))
    return out


def attach_orchestration(bars: list[CBar], sigs: dict[int, tuple]) -> list[CBar]:
    return [make_bar(b.index, b.chorus, b.pos, {**b.sigs, "orchestration": sigs.get(b.index, ())}, b.part, b.metrics)
            for b in bars]


def bar_start_ticks(path: Path) -> dict[int, int]:
    """Début de chaque mesure en ticks MIDI (`measure_start` du moteur : `(index − 1) × pas × 120`)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(e["measure"]["index"]): (int(e["measure"]["index"]) - 1) * int(e["measure"]["steps"]) * TICKS_PER_STEP
            for e in data["measures"]}


# ── Distances ─────────────────────────────────────────────────────────────

def _jaccard_distance(a: frozenset, b: frozenset) -> float:
    union = len(a | b)
    return 0.0 if union == 0 else 1.0 - len(a & b) / union


def _orchestration_distance(a: tuple, b: tuple) -> float:
    da, db = {e[0]: e[1:] for e in a}, {e[0]: e[1:] for e in b}
    channels = set(da) | set(db)
    return sum(da.get(c) != db.get(c) for c in channels) / len(channels) if channels else 0.0


def layer_distance(layer: str, a: CBar, b: CBar) -> tuple[bool, float, bool]:
    """(diffère, distance graduée, active) pour une couche entre deux mesures."""
    if layer == ALL:
        parts = [(a.sigs[ly] != b.sigs[ly], _jaccard_distance(a.sets[ly], b.sets[ly]))
                 for ly in CORE if a.sigs[ly] or b.sigs[ly]]
        if not parts:
            return False, 0.0, False
        return any(p[0] for p in parts), sum(p[1] for p in parts) / len(parts), True
    sa, sb = a.sigs[layer], b.sigs[layer]
    active = bool(sa or sb)
    if layer == "orchestration":
        return sa != sb, _orchestration_distance(sa, sb), active
    return sa != sb, _jaccard_distance(a.sets[layer], b.sets[layer]), active


def _key(layer: str, bar: CBar) -> tuple:
    return tuple(bar.sigs[ly] for ly in CORE) if layer == ALL else bar.sigs[layer]


# ── Intra-graine ──────────────────────────────────────────────────────────

def chorus_table(bars: list[CBar]) -> dict[int, dict[int, CBar]]:
    """`{chorus: {place: mesure}}`."""
    table: dict[int, dict[int, CBar]] = {}
    for b in bars:
        table.setdefault(b.chorus, {})[b.pos] = b
    if not table:
        raise ValueError("variance par chorus : aucune mesure de chorus")
    return dict(sorted(table.items()))


class Pair(NamedTuple):
    active: int
    diff: int
    graded: float
    by_part: dict[int, tuple[int, int]]
    places: int


def compare_choruses(layer: str, ca: dict[int, CBar], cb: dict[int, CBar]) -> Pair:
    active = diff = 0
    graded = 0.0
    by_part: dict[int, list[int]] = {}
    shared = sorted(set(ca) & set(cb))
    for pos in shared:
        d, g, act = layer_distance(layer, ca[pos], cb[pos])
        if not act:
            continue
        active += 1
        diff += d
        graded += g
        slot = by_part.setdefault(cb[pos].part, [0, 0])
        slot[0] += 1
        slot[1] += d
    return Pair(active, diff, graded, {p: (v[0], v[1]) for p, v in by_part.items()}, len(shared))


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 4) if xs else None


def _quantile(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    i = q * (len(s) - 1)
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (i - lo), 4)


def intra_seed(runs: dict[int, list[CBar]], steady_from: int = STEADY_FROM,
               part_names: list[str] | None = None) -> dict[str, Any]:
    """Variance d'un chorus au suivant, par couche, agrégée sur les graines."""
    tables = {s: chorus_table(b) for s, b in runs.items()}
    n_chorus = min(len(t) for t in tables.values())
    result: dict[str, Any] = {}
    for layer in (ALL, *LAYERS):
        matrix = [[[] for _ in range(n_chorus)] for _ in range(n_chorus)]
        adjacent, adjacent_g, steady, steady_g, pair_shares = [], [], [], [], []
        identical = pairs_active = 0
        distinct_choruses: list[int] = []
        active_places: list[float] = []
        part_tally: dict[int, list[int]] = {}
        for table in tables.values():
            ids = sorted(table)[:n_chorus]
            common = sorted(set.intersection(*(set(table[c]) for c in ids)))
            distinct_choruses.append(len({tuple(_key(layer, table[c][p]) for p in common) for c in ids}))
            for i, j in itertools.combinations(range(n_chorus), 2):
                pr = compare_choruses(layer, table[ids[i]], table[ids[j]])
                if j == i + 1:
                    active_places.append(pr.active / pr.places)
                if pr.active == 0:
                    continue
                share = pr.diff / pr.active
                matrix[i][j].append(share)
                matrix[j][i].append(share)
                pair_shares.append(share)
                pairs_active += 1
                identical += pr.diff == 0
                if j == i + 1:
                    adjacent.append(share)
                    adjacent_g.append(pr.graded / pr.active)
                    for part, (n, d) in pr.by_part.items():
                        slot = part_tally.setdefault(part, [0, 0])
                        slot[0] += n
                        slot[1] += d
                if j == i + 1 and i + 1 >= steady_from:
                    steady.append(share)
                    steady_g.append(pr.graded / pr.active)
        names = (lambda p: part_names[p] if part_names and p < len(part_names) else f"part{p}")
        result[layer] = {
            "choruses": n_chorus,
            "active_share": _mean(active_places),
            "adjacent": {"exact": _mean(adjacent), "graded": _mean(adjacent_g), "pairs": len(adjacent)},
            "adjacent_steady": {"exact": _mean(steady), "graded": _mean(steady_g), "pairs": len(steady)},
            "any_pair": {"exact": _mean(pair_shares), "p10": _quantile(pair_shares, 0.1),
                         "p50": _quantile(pair_shares, 0.5), "p90": _quantile(pair_shares, 0.9),
                         "pairs": pairs_active},
            "identical_pairs": round(identical / pairs_active, 4) if pairs_active else None,
            "distinct_choruses_mean": round(sum(distinct_choruses) / len(distinct_choruses), 3),
            "adjacent_by_part": {names(p): round(v[1] / v[0], 4) for p, v in sorted(part_tally.items()) if v[0]},
            "matrix": [[_mean(c) for c in row] for row in matrix],
        }
    return result


# ── Inter-graines ─────────────────────────────────────────────────────────

def inter_seed(runs: dict[int, list[CBar]]) -> dict[str, Any]:
    """Variance entre graines à chorus égal et place égale, par couche."""
    seeds = sorted(runs)
    n = len(seeds)
    if n < 2:
        raise ValueError("variance par chorus : au moins deux graines requises")
    tables = {s: chorus_table(runs[s]) for s in seeds}
    n_chorus = min(len(t) for t in tables.values())
    ids = {s: sorted(tables[s])[:n_chorus] for s in seeds}
    everywhere = sorted(set.intersection(*(set(tables[s][c]) for s in seeds for c in ids[s])))
    result: dict[str, Any] = {}
    for layer in (ALL, *LAYERS):
        per_chorus: list[dict[str, float]] = []
        for k in range(n_chorus):
            positions = set.intersection(*(set(tables[s][ids[s][k]]) for s in seeds))
            varying = active = varying_active = 0
            diversity = distinct_sum = graded_sum = 0.0
            for pos in sorted(positions):
                groups: dict[tuple, list[CBar]] = {}
                for s in seeds:
                    b = tables[s][ids[s][k]][pos]
                    groups.setdefault(_key(layer, b), []).append(b)
                distinct = len(groups)
                is_active = any(bool(k_) if layer != ALL else any(bool(s_) for s_ in k_) for k_ in groups)
                counts = [len(g) for g in groups.values()]
                reps = [g[0] for g in groups.values()]
                dist = sum(layer_distance(layer, ra, rb)[1] * ca * cb
                           for (ra, ca), (rb, cb) in itertools.combinations(zip(reps, counts), 2))
                varying += distinct > 1
                diversity += (distinct - 1) / (n - 1)
                distinct_sum += distinct
                if is_active:
                    active += 1
                    varying_active += distinct > 1
                    graded_sum += dist / (n * (n - 1) / 2)
            total = len(positions)
            per_chorus.append({
                "share": varying / total if total else 0.0,
                "share_active": varying_active / active if active else 0.0,
                "diversity": diversity / total if total else 0.0,
                "distinct_mean": distinct_sum / total if total else 0.0,
                "graded": graded_sum / active if active else 0.0,
                "active_places": active, "places": total,
            })
        def avg(field: str) -> float:
            return round(sum(c[field] for c in per_chorus) / len(per_chorus), 4)
        result[layer] = {
            "choruses": n_chorus,
            "distinct_runs": len({tuple(_key(layer, tables[s][c][p]) for c in ids[s] for p in everywhere)
                                  for s in seeds}),
            "share": avg("share"), "share_active": avg("share_active"),
            "diversity": avg("diversity"), "distinct_mean": round(avg("distinct_mean"), 3), "graded": avg("graded"),
            "by_chorus_share_active": [round(c["share_active"], 4) for c in per_chorus],
            "by_chorus_graded": [round(c["graded"], 4) for c in per_chorus],
        }
    return result


# ── Couches numériques ────────────────────────────────────────────────────

def _series(bars: list[CBar], group: str, metric: str) -> dict[int, float | None]:
    """Valeur par chorus : notes par mesure (`density`), vélocité moyenne (`velocity`) ou
    intensité du moteur (`intensity`)."""
    per: dict[int, list[CBar]] = {}
    for b in bars:
        per.setdefault(b.chorus, []).append(b)
    out: dict[int, float | None] = {}
    for c, bs in sorted(per.items()):
        if metric == "density":
            out[c] = sum(b.metrics.get(f"n_{group}", 0.0) for b in bs) / len(bs)
        elif metric == "velocity":
            n = sum(b.metrics.get(f"n_{group}", 0.0) for b in bs)
            out[c] = sum(b.metrics.get(f"vel_{group}", 0.0) for b in bs) / n if n else None
        else:
            out[c] = sum(b.metrics.get("intensity", 0.0) for b in bs) / len(bs)
    return out


def _cv(xs: list[float]) -> float | None:
    m = sum(xs) / len(xs) if xs else 0.0
    return statistics.pstdev(xs) / m if len(xs) > 1 and m > 0 else None


def _trajectory_range(traj: list[float | None]) -> float | None:
    vals = [v for v in traj if v is not None]
    m = sum(vals) / len(vals) if vals else 0.0
    return round((max(vals) - min(vals)) / m, 4) if m > 0 else None


def numeric_variance(runs: dict[int, list[CBar]], n_chorus: int) -> dict[str, Any]:
    seeds = sorted(runs)
    out: dict[str, Any] = {}
    for group, metric in [(g, m) for g in GROUPS for m in ("density", "velocity")] + [("engine", "intensity")]:
        series = {s: _series(runs[s], group, metric) for s in seeds}
        mat = [[series[s].get(c) for c in sorted(series[s])[:n_chorus]] for s in seeds]
        if not any(v for row in mat for v in row if v):
            continue
        adj, cvs = [], []
        for row in mat:
            vals = [v for v in row if v is not None]
            m = sum(vals) / len(vals) if vals else 0.0
            if m > 0 and len(vals) > 1:
                adj.extend(abs(b - a) / m for a, b in zip(vals, vals[1:]))
                cvs.append(_cv(vals))
        inter = [_cv([row[c] for row in mat if row[c] is not None]) for c in range(n_chorus)]
        inter = [v for v in inter if v is not None]
        traj = [_mean([row[c] for row in mat if row[c] is not None]) for c in range(n_chorus)]
        out.setdefault(group, {})[metric] = {
            "trajectory": traj,
            "trajectory_range": _trajectory_range(traj),
            "intra": {"adjacent_change": _mean(adj), "cv": _mean([v for v in cvs if v is not None])},
            "inter": {"cv": _mean(inter)},
        }
    return out


# ── Rapport d'un profil ───────────────────────────────────────────────────

def chorus_variance(runs: dict[int, list[CBar]], part_names: list[str] | None = None,
                    steady_from: int = STEADY_FROM) -> dict[str, Any]:
    """Rapport complet : intra-graine, inter-graines, numérique, orchestration."""
    if len(runs) < 2:
        raise ValueError("variance par chorus : au moins deux graines requises")
    intra = intra_seed(runs, steady_from, part_names)
    inter = inter_seed(runs)
    n_chorus = intra[ALL]["choruses"]
    first = chorus_table(runs[min(runs)])
    orch: dict[str, set[int]] = {}
    for bars in runs.values():
        for b in bars:
            for ch, bank, prog in b.sigs["orchestration"]:
                orch.setdefault(str(ch), set()).add(bank * 1000 + prog)
    return {
        "seeds": sorted(runs), "choruses": n_chorus, "bars_per_chorus": len(first[min(first)]),
        "steady_from": steady_from,
        "intra": intra, "inter": inter,
        "numeric": numeric_variance(runs, n_chorus),
        "orchestration_programs": {ch: sorted(v) for ch, v in sorted(orch.items(), key=lambda kv: int(kv[0]))},
    }


# ── Rendu moteur ──────────────────────────────────────────────────────────

def _truth_bars(path: Path) -> tuple[int, int]:
    """(mesures d'intro, mesures du premier tour) du premier air d'une vérité terrain."""
    data = json.loads(path.read_text(encoding="utf-8"))
    intro = cycle = 0
    for e in data["measures"]:
        pos = e["measure"]["position"]
        if pos["tune_index"] != 0:
            continue
        if pos.get("section", "Tour") != "Tour" or int(pos.get("tour", 1)) < 1:
            intro += 1
        elif int(pos.get("chorus", pos.get("tour", 1))) == 1:
            cycle += 1
    return intro, cycle


def plan_bars(engine_dir: Path, engine_bin: Path | None, profile_dir: Path, chorus: int,
              work_dir: Path, tag: str, force: bool) -> int:
    """Mesures à demander pour `chorus` chorus : sonde d'un tour (graine 1) → intro + tour × N + marge
    (l'intro peut varier d'une graine à l'autre ; la marge fait entrer l'air suivant dans le fichier,
    ce qui désigne la mesure de clôture)."""
    probe = sv.export_truth(engine_dir, engine_bin, profile_dir, 1, 400, work_dir / f"{tag}_probe.truth.json",
                            force, tours=1)
    intro, cycle = _truth_bars(probe)
    if cycle == 0:
        raise RuntimeError(f"{profile_dir.name} : aucun tour lu dans la sonde ({probe})")
    return intro + cycle * chorus + 8


def measure_profile(engine_dir: Path, engine_bin: Path | None, profile: str, seeds: list[int], chorus: int,
                    work_dir: Path, force: bool = False, tag: str | None = None,
                    steady_from: int = STEADY_FROM) -> dict[str, Any]:
    profile_dir = sv.resolve_profile(engine_dir, profile)
    label = tag or profile_dir.name
    bars = plan_bars(engine_dir, engine_bin, profile_dir, chorus, work_dir, label, force)
    base = instruments_of(profile_dir)
    runs: dict[int, list[CBar]] = {}
    for seed in seeds:
        truth = work_dir / f"{label}_c{chorus}_s{seed}.truth.json"
        midi = truth.with_suffix("").with_suffix(".mid")
        sv.export_truth(engine_dir, engine_bin, profile_dir, seed, bars, truth, force, tours=chorus, midi=midi)
        loaded = load_truth(truth, bars)
        starts = bar_start_ticks(truth)
        events = midi_programs(midi) if midi.is_file() else []
        runs[seed] = attach_orchestration(loaded, orchestration_sigs(base, events, starts))
    result = chorus_variance(runs, sv.part_names_of(profile_dir), steady_from)
    got = result["choruses"]
    if got < chorus:
        result["warning"] = f"{got} chorus complets sur {chorus} demandés"
    result.update({"profile": profile_dir.name, "chorus_requested": chorus, "bars": bars})
    return result


# ── Sortie ────────────────────────────────────────────────────────────────

def _pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.0f} %"


def markdown(results: list[dict[str, Any]]) -> str:
    lines = ["| Profil | Couche | Mesures actives | Intra : mesures changées, chorus k → k+1 | Intra : distance graduée | "
             "Intra : paires de chorus identiques | Chorus distincts / graine | Inter : places qui varient | Inter : distance graduée | Inter : séquences distinctes |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        name = r.get("label", r["profile"])
        for layer in (ALL, *LAYERS):
            a, i = r["intra"][layer], r["inter"][layer]
            if a["adjacent"]["exact"] is None and not i["share_active"]:
                continue
            lines.append(
                f"| `{name}` | {LAYER_LABELS[layer]} | {_pct(a['active_share'])} | {_pct(a['adjacent']['exact'])} "
                f"(stable {_pct(a['adjacent_steady']['exact'])}) | {_pct(a['adjacent']['graded'])} | "
                f"{_pct(a['identical_pairs'])} | {a['distinct_choruses_mean']:.1f} / {a['choruses']} | "
                f"{_pct(i['share_active'])} | {_pct(i['graded'])} | {i['distinct_runs']} / {len(r['seeds'])} |")
    return "\n".join(lines)


def numeric_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["| Profil | Groupe | Mesure | Intra : écart k → k+1 | Intra : cv | Inter : cv | Étendue de la trajectoire | Trajectoire (chorus 1, 2, 3, dernier) |",
             "|---|---|---|---:|---:|---:|---:|---|"]
    for r in results:
        name = r.get("label", r["profile"])
        for group, metrics in r["numeric"].items():
            for metric, v in metrics.items():
                t = v["trajectory"]
                traj = " ; ".join("—" if x is None else f"{x:.2f}" for x in (*t[:3], t[-1]))
                lines.append(f"| `{name}` | {group} | {metric} | {_pct(v['intra']['adjacent_change'])} | "
                             f"{_pct(v['intra']['cv'])} | {_pct(v['inter']['cv'])} | {_pct(v['trajectory_range'])} | {traj} |")
    return "\n".join(lines)


_NUMBER_LIST = re.compile(r"\[\s*((?:(?:-?[\d.]+(?:[eE][-+]?\d+)?|null)\s*,?\s*)*)\]")


def dumps(payload: Any) -> str:
    """JSON indenté dont les listes de nombres (matrices, trajectoires) tiennent sur une ligne."""
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    return _NUMBER_LIST.sub(lambda m: "[" + re.sub(r"\s+", " ", m.group(1)).strip() + "]", text) + "\n"


def _engine_rev(engine_dir: Path) -> str | None:
    """Révision git du moteur mesuré (dépôt non modifié : lecture seule)."""
    proc = subprocess.run(["git", "-C", str(engine_dir), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def run(args: Any) -> int:
    engine_dir = Path(args.engine_dir).expanduser().resolve()
    engine_bin = Path(args.engine_bin).expanduser().resolve() if args.engine_bin else None
    seeds = list(range(1, args.seeds + 1))
    results = []
    for profile in args.profile:
        print(f"[seed-variety] {profile} : {len(seeds)} graines × {args.chorus} chorus", file=sys.stderr)
        tag = f"{args.label}_{Path(profile).name}" if args.label else None
        r = measure_profile(engine_dir, engine_bin, profile, seeds, args.chorus, Path(args.work_dir),
                            args.force, tag, args.steady_from)
        if args.label:
            r["measure"] = args.label
        results.append(r)
    payload = {"schema": 2, "kind": "chorus", "seeds": seeds, "chorus": args.chorus,
               "engine_rev": _engine_rev(engine_dir), "profiles": results}
    if args.output:
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(dumps(payload), encoding="utf-8")
        print(f"Variance par chorus publiée → {dest}", file=sys.stderr)
    if args.markdown or not args.output:
        print(markdown(results))
        print()
        print(numeric_markdown(results))
    return 0


# ── Tableau de synthèse (profil × couche) depuis les JSON publiés ─────────

SUMMARY_LAYERS = (("accords", "chords"), ("comping rythme", "comping_rhythm"), ("comping voicings", "comping_voicing"),
                  ("basse", "bass"), ("batterie", "drums"), ("mélodie", "melody"), ("orchestration", "orchestration"),
                  ("accompagnement", ALL))


def summary_markdown(results: list[dict[str, Any]]) -> str:
    """Tableaux profil × couche : intra-graine, inter-graines, séquences distinctes, distances
    graduées, puis couches numériques. `·` : couche muette dans le profil."""
    def pct(x: float | None) -> str:
        return "—" if x is None else f"{100 * x:.0f}"

    def table(title: str, cell) -> str:
        lines = [f"**{title}**", "", "| Profil | " + " | ".join(c[0] for c in SUMMARY_LAYERS) + " |",
                 "|---|" + "---:|" * len(SUMMARY_LAYERS)]
        for r in results:
            row = [("·" if r["intra"][ly]["adjacent"]["exact"] is None else cell(r, ly)) for _, ly in SUMMARY_LAYERS]
            lines.append(f"| `{r.get('label', r['profile'])}` | " + " | ".join(row) + " |")
        return "\n".join(lines)

    blocks = [
        table("Intra-graine : % de mesures changées d'un chorus au suivant (chorus ≥ 3)",
              lambda r, ly: pct(r["intra"][ly]["adjacent_steady"]["exact"])),
        table("Intra-graine : % de paires de chorus identiques", lambda r, ly: pct(r["intra"][ly]["identical_pairs"])),
        table("Intra-graine / inter-graines : distance graduée moyenne, en % (chorus voisins / graines à chorus égal)",
              lambda r, ly: f"{pct(r['intra'][ly]['adjacent']['graded'])} / {pct(r['inter'][ly]['graded'])}"),
        table("Inter-graines : % de places (chorus, mesure) où les graines diffèrent",
              lambda r, ly: pct(r["inter"][ly]["share_active"])),
        table("Inter-graines : séquences de 16 chorus distinctes parmi les graines",
              lambda r, ly: str(r["inter"][ly]["distinct_runs"])),
    ]
    num = ["**Couches numériques** (cv : écart-type / moyenne, en % ; étendue : (max − min) / moyenne de la trajectoire)", "",
           "| Profil | Groupe | Densité : cv intra | Densité : étendue | Densité : cv inter | Vélocité : cv intra | "
           "Vélocité : étendue | Vélocité : cv inter |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        for group, metrics in r["numeric"].items():
            if group == "engine":
                continue
            d, v = metrics.get("density"), metrics.get("velocity")
            cells = []
            for m in (d, v):
                cells += [pct(m["intra"]["cv"]), pct(m["trajectory_range"]), pct(m["inter"]["cv"])] if m else ["—"] * 3
            num.append(f"| `{r.get('label', r['profile'])}` | {group} | " + " | ".join(cells) + " |")
        eng = r["numeric"].get("engine", {}).get("intensity")
        if eng:
            num.append(f"| `{r.get('label', r['profile'])}` | intensité moteur | {pct(eng['intra']['cv'])} | "
                       f"{pct(eng['trajectory_range'])} | {pct(eng['inter']['cv'])} | | | |")
    return "\n\n".join([*blocks, "\n".join(num)])


def main(argv: list[str] | None = None) -> int:
    """`python -m harmonium_lab.chorusvariety references/v0-variance/*.json` : tableaux de synthèse."""
    paths = [Path(a) for a in (sys.argv[1:] if argv is None else argv)]
    if not paths:
        print(main.__doc__, file=sys.stderr)
        return 2
    results = [p for path in paths for p in json.loads(path.read_text(encoding="utf-8"))["profiles"]]
    print(summary_markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
