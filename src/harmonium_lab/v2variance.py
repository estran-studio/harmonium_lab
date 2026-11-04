"""V2 (phase 019, vague 5) : variance prouvée par style, sur tous les profils distribués.

Deux étapes, deux sous-commandes :

    python -m harmonium_lab.v2variance collect --engine-dir ~/workspace/harmonium --engine-bin <harmonium-cli> \\
        --work-dir /tmp/h019-v2t1/truth --out references/v2-variance [--jobs 3] [--profiles id ...]
    python -m harmonium_lab.v2variance report --out references/v2-variance          # tableaux + summary.json

`collect` mesure, pour chaque profil, 16 graines × 4 chorus (`--tours 4`) : variance par chorus et par couche
(`chorusvariety`, V0) et **habillages distincts** lus dans la vérité terrain (`MeasureSnapshot.session`,
`instruments`, tempo, tonalité ; définition de R2 : grappe de tempo à ± 8 BPM, tonalité et mode, programmes de
mélodie, d'accords, de basse et de kit, famille de voicings, swing). Les profils `loop` sont mesurés une seconde
fois **sous une grille utilisateur** (`usergrid` : 8 mesures, plus longue seulement si les breaks de l'arc du
profil l'exigent) avec `[fixed_tonality]` imposé comme le fait l'hôte. Un JSON par mesure :
`<profil>.json`, `<profil>.grille.json`. `report` lit ces JSON et applique les seuils (`CRITERIA`).
Aucune lecture audio ; vérités terrain et MIDI en cache hors dépôt (`--work-dir`).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

from . import chorusvariety as cv
from . import usergrid

CHORUS = 4
SEEDS = 16
GRID_LADDER = (8, 16, 24, 32)     # longueurs de grille essayées : la première que le profil accepte
TEMPO_WIDTH = 8.0                 # grappe de tempo (R2) : ± 8 BPM


# ── Habillage (R2) ────────────────────────────────────────────────────────

def tempo_clusters(values: list[float], width: float = TEMPO_WIDTH) -> list[int]:
    """Grappes de tempo : un tempo à moins de `width` BPM du premier de la grappe y entre."""
    firsts: list[float] = []
    out = []
    for v in values:
        for i, f in enumerate(firsts):
            if abs(v - f) <= width:
                out.append(i)
                break
        else:
            firsts.append(v)
            out.append(len(firsts) - 1)
    return out


def seed_habillage(truth: Path) -> dict[str, Any]:
    """Habillage d'une graine : premier `MeasureSnapshot` de la vérité terrain."""
    measures: dict[int, dict] = {}
    for rec in json.loads(truth.read_text(encoding="utf-8"))["measures"]:
        measures.setdefault(rec["measure"]["index"], rec["measure"])
    first = measures[min(measures)]
    session = {s["group"]: s["name"] for s in (first.get("session") or [])}
    ins = first.get("instruments") or {}
    pos = first["position"]
    return {"tempo": first["tempo"], "key": pos["key"], "mode": pos["mode"], "swing": round(first["swing_ratio"], 3),
            "melody": ins.get("melody_program"), "chords": ins.get("chords_program"), "bass": ins.get("bass_program"),
            "kit": (ins["percussion_bank"], ins["percussion_program"]) if ins.get("percussion_program") is not None else None,
            "voicing": session.get("voicing"), "arc": session.get("arc"), "session": session}


def habillage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = tempo_clusters([r["tempo"] for r in rows])
    full = {(g, r["key"], r["mode"], r["melody"], r["chords"], r["bass"], r["kit"], r["voicing"], r["swing"])
            for g, r in zip(groups, rows)}
    # ce qui reste quand l'hôte impose le tempo (`SetBpm`) et la tonalité (`[fixed_tonality]`)
    host = {(r["melody"], r["chords"], r["bass"], r["kit"], r["voicing"]) for r in rows}
    return {
        "distinct": len(full), "distinct_hote_tempo_tonalite": len(host), "tempo_clusters": len(set(groups)),
        "tempo_min_max": [min(r["tempo"] for r in rows), max(r["tempo"] for r in rows)],
        "tonalites": len({(r["key"], r["mode"]) for r in rows}),
        "programmes": {k: sorted({r[k] for r in rows if r[k] is not None}, key=str)
                       for k in ("melody", "chords", "bass", "kit")},
        "voicings": sorted({r["voicing"] for r in rows if r["voicing"]}),
        "arcs": dict(Counter(r["arc"] for r in rows if r["arc"])),
        "swings": sorted({r["swing"] for r in rows}),
        "par_graine": rows,
    }


# ── Mesure d'un profil ────────────────────────────────────────────────────

def probe_grid(engine_dir: Path, engine_bin: Path, profile_dir: Path, scratch: Path) -> str | None:
    """None si le moteur charge le profil et exporte 2 mesures ; sinon son message d'erreur."""
    proc = subprocess.run([str(engine_bin), "--export", "--bars", "2", "--profile", str(profile_dir), "--seed", "1",
                           "--record-truth", str(scratch)], capture_output=True, text=True, cwd=engine_dir, timeout=300)
    return None if proc.returncode == 0 else (proc.stderr.strip() or proc.stdout.strip())[-400:]


def grid_profile(engine_dir: Path, engine_bin: Path, src: Path, work_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    """Profil sous grille utilisateur : (dossier, rapport) ; dossier None si le profil n'en accepte aucune."""
    info: dict[str, Any] = {"applicable": False}
    if not usergrid.is_loop(src):
        model = tomllib.loads((src / "profile.toml").read_text(encoding="utf-8")).get("harmony", {}).get("model")
        info["reason"] = f"harmonie `{model}` : pas de grille utilisateur (seule `loop` en reçoit une)"
        return None, info
    tried = []
    for bars in GRID_LADDER:
        dst = work_dir / "grid" / f"{src.name}_{bars}"
        report = usergrid.make_profile(src, dst, bars)
        err = probe_grid(engine_dir, engine_bin, dst, work_dir / "grid" / f"{src.name}_probe.json")
        if err is None:
            info.update(applicable=True, bars=bars, steps_per_bar=report.steps_per_bar, steps_per_chord=report.steps_per_chord,
                        fixed_tonality=report.fixed_tonality, tonality_from_profile=report.tonality_from_profile,
                        merged_bars=report.merged_bars, refused_lengths=tried)
            return dst, info
        tried.append({"bars": bars, "error": err})
        if "breaks" not in err:        # seule la longueur de chorus se corrige en allongeant la grille
            break
    info["reason"] = tried[-1]["error"]
    info["refused_lengths"] = tried
    return None, info


def measure(job: dict[str, Any]) -> dict[str, Any]:
    engine_dir, engine_bin = Path(job["engine_dir"]), Path(job["engine_bin"])
    work_dir, out = Path(job["work_dir"]), Path(job["out"])
    src = engine_dir / "profiles" / job["profile"]
    seeds = list(range(1, job["seeds"] + 1))
    result: dict[str, Any] = {"profile": job["profile"], "variant": job["variant"], "chorus": job["chorus"], "seeds": job["seeds"]}
    if job["variant"] == "grille":
        profile_dir, info = grid_profile(engine_dir, engine_bin, src, work_dir)
        result["grid"] = info
        if profile_dir is None:
            out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            return result
        tag = f"V2grille_{job['profile']}"
    else:
        profile_dir, tag = src, f"V2_{job['profile']}"
    var = cv.measure_profile(engine_dir, engine_bin, str(profile_dir), seeds, job["chorus"], work_dir, False, tag)
    rows = [seed_habillage(work_dir / f"{tag}_c{job['chorus']}_s{s}.truth.json") for s in seeds]
    walking = "walking" in tomllib.loads((src / "profile.toml").read_text(encoding="utf-8")).get("accompaniment", {}).get("bass", {})
    result.update(variance=var, habillage=habillage_summary(rows), meter=_meter(profile_dir), bass_walking=walking,
                  engine_rev=cv._engine_rev(engine_dir))
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def _meter(profile_dir: Path) -> dict[str, Any]:
    data = tomllib.loads((profile_dir / "profile.toml").read_text(encoding="utf-8"))
    m = data["meter"]
    ts = m.get("time_signature", {})
    return {"time_signature": f"{ts.get('numerator')}/{ts.get('denominator')}", "steps_per_bar": m.get("steps_per_bar"),
            "min_bpm": m.get("min_bpm"), "max_bpm": m.get("max_bpm"), "model": data.get("harmony", {}).get("model")}


def distributed_profiles(engine_dir: Path) -> list[str]:
    return sorted(d.name for d in (engine_dir / "profiles").iterdir() if (d / "profile.toml").is_file())


def collect(args: argparse.Namespace) -> int:
    engine_dir = Path(args.engine_dir).expanduser().resolve()
    engine_bin = Path(args.engine_bin).expanduser().resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    jobs = []
    for pid in args.profiles or distributed_profiles(engine_dir):
        for variant in ("defaut", "grille"):
            dest = out / (f"{pid}.json" if variant == "defaut" else f"{pid}.grille.json")
            if variant == "grille" and args.no_grid:
                continue
            if dest.is_file() and not args.force:
                continue
            jobs.append({"engine_dir": str(engine_dir), "engine_bin": str(engine_bin), "work_dir": str(work), "out": str(dest),
                         "profile": pid, "variant": variant, "chorus": args.chorus, "seeds": args.seeds})
    print(f"[v2] {len(jobs)} mesures à faire ({args.jobs} en parallèle)", file=sys.stderr)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for job, res in zip(jobs, pool.map(measure, jobs)):
            state = "sans objet" if "variance" not in res else f"{res['habillage']['distinct']}/{args.seeds} habillages"
            print(f"[v2] {job['profile']} ({job['variant']}) : {state}", file=sys.stderr)
    return 0


# ── Critères ──────────────────────────────────────────────────────────────

def pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.0f} %"


class Criterion:
    """Un critère V2 : `check(mesure) -> (valeur lisible, tenu | None)` ; None = sans objet (couche muette)."""

    def __init__(self, ident: str, label: str, check: Callable[[dict[str, Any]], tuple[str, bool | None]]):
        self.ident, self.label, self.check = ident, label, check


def _ok(values: list[float | None], pred: Callable[[float], bool]) -> bool | None:
    vals = [v for v in values if v is not None]
    return all(pred(v) for v in vals) if vals else None


def _layer(m: dict, key: str, kind: str = "intra") -> dict:
    return m["variance"][kind][key]


def steady_range(trajectory: list[float | None]) -> float | None:
    """(max - min) / moyenne de la courbe moyenne, **à partir du 2e chorus** : les entrées de pistes du premier
    chorus (`[arrangement.entries]`) gonflent la densité sans être un arc (V0 le notait pour `reel_quebecois` et
    `nt_desert`)."""
    pts = [x for x in (trajectory[1:] if len(trajectory) >= 3 else trajectory) if x is not None]
    if len(pts) < 2 or not sum(pts):
        return None
    return (max(pts) - min(pts)) / (sum(pts) / len(pts))


# Seuils : voir `references/v2-variance/README.md` (V0 puis ajustements, avec les chiffres). Constantes nommées pour
# que le rapport et le code disent la même chose.
T = {
    "habillages": 12,            # habillages distincts sur 16 graines
    "habillages_hote": 8,        # idem sous grille, tempo et tonalité imposés par l'hôte
    "tempo_grappes": 2,
    "inter_comping": 0.75, "inter_drums": 0.50,        # places où les graines diffèrent
    "identiques": 0.05,          # paires de chorus identiques, par couche (comping rythme, voicings, batterie)
    "accords": 0.02,
    "comping": 0.75, "voicing": 0.65, "drums": 0.30, "drums_graded": 0.10,   # mesures changées d'un chorus au suivant
    "bass_walking": 0.80, "bass_riff": 0.10,
    "suites": 12,
    "prog_comping": 3, "prog_basse": 2, "prog_kit": 2, "orch_suites": 4,
    "dens_range": 0.25, "vel_range": 0.08,
}


def build_criteria() -> list[Criterion]:
    def grid(m):
        return bool(m.get("grid", {}).get("applicable"))

    def hab(m):
        h = m["habillage"]
        n = h["distinct_hote_tempo_tonalite"] if grid(m) else h["distinct"]
        need = T["habillages_hote"] if grid(m) else T["habillages"]
        return f"{n} / {m['seeds']}", n >= need

    def tempo(m):
        h = m["habillage"]
        lo, hi = h["tempo_min_max"]
        shown = f"{h['tempo_clusters']} ({lo:g}–{hi:g})"
        return shown, None if grid(m) else h["tempo_clusters"] >= T["tempo_grappes"]      # sous grille l'hôte impose le tempo

    def inter_share(m):
        vals = {k: _layer(m, k, "inter") for k in ("comping_rhythm", "drums")}
        shown = " / ".join(pct(v["share_active"]) if v["share_active"] > 0 else "·" for v in vals.values())
        checks = [v["share_active"] >= T[t] for v, t in zip(vals.values(), ("inter_comping", "inter_drums")) if v["share_active"] > 0]
        return shown, all(checks) if checks else None

    def loop(m):
        v = _layer(m, "all")["identical_pairs"]
        return pct(v), None if v is None else v <= 0.0

    def layers(m):
        vals = [_layer(m, k)["identical_pairs"] for k in ("comping_rhythm", "comping_voicing", "drums")]
        return " / ".join(pct(v) for v in vals), _ok(vals, lambda v: v <= T["identiques"])

    def accords(m):
        v = _layer(m, "chords")["adjacent"]["exact"]
        return pct(v), None if v is None else v <= T["accords"]

    def changed(key, thr):
        def f(m):
            blk = _layer(m, key)
            if blk["active_share"] == 0:
                return "·", None
            e = blk["adjacent"]["exact"]
            return pct(e), None if e is None else e >= thr
        return f

    def bass(m):
        walking = bool(m.get("bass_walking"))
        thr = T["bass_walking"] if walking else T["bass_riff"]
        shown, ok = changed("bass", thr)(m)
        return f"{shown} ({'marche' if walking else 'riff'})", ok

    def drums(m):
        blk = _layer(m, "drums")
        if blk["active_share"] == 0:
            return "·", None
        e, g = blk["adjacent"]["exact"], blk["adjacent"]["graded"]
        return f"{pct(e)} ; {pct(g)}", None if e is None else (e >= T["drums"] and g >= T["drums_graded"])

    def suites(m):
        keys = ("comping_rhythm", "bass", "drums")
        runs = [_layer(m, k, "inter")["distinct_runs"] for k in keys]
        act = [_layer(m, k, "inter")["share_active"] > 0 for k in keys]
        ok = [r >= T["suites"] for r, a in zip(runs, act) if a]
        return " / ".join(str(r) if a else "·" for r, a in zip(runs, act)), all(ok) if ok else None

    def orch(m):
        p = m["variance"]["orchestration_programs"]
        c, b, k = len(p.get("1", [])), len(p.get("2", [])), len(p.get("9", []))
        runs = _layer(m, "orchestration", "inter")["distinct_runs"]
        ok = c >= T["prog_comping"] and b >= T["prog_basse"] and k >= T["prog_kit"] and runs >= T["orch_suites"]
        return f"{c} / {b} / {k} ; {runs}", ok

    def arc(metric, thr):
        def f(m):
            r = steady_range(m["variance"]["numeric"]["all"][metric]["trajectory"])
            return pct(r), None if r is None else r >= thr
        return f

    return [
        Criterion("H1", f"habillages distincts sur 16 graines ≥ {T['habillages']} (sous grille, tempo et tonalité imposés : ≥ {T['habillages_hote']})", hab),
        Criterion("H2", f"grappes de tempo (± 8 BPM) ≥ {T['tempo_grappes']} (sans objet sous grille)", tempo),
        Criterion("H3", f"places où les graines diffèrent : comping rythme ≥ {pct(T['inter_comping'])} / batterie ≥ {pct(T['inter_drums'])}", inter_share),
        Criterion("1", "paires de chorus identiques, accompagnement entier : 0 %", loop),
        Criterion("2", f"paires de chorus identiques par couche (comping rythme / voicings / batterie) ≤ {pct(T['identiques'])}", layers),
        Criterion("3", f"accords changés d'un chorus au suivant ≤ {pct(T['accords'])}", accords),
        Criterion("4", f"comping rythme changé d'un chorus au suivant ≥ {pct(T['comping'])}", changed("comping_rhythm", T["comping"])),
        Criterion("5", f"comping voicings changés ≥ {pct(T['voicing'])}", changed("comping_voicing", T["voicing"])),
        Criterion("6", f"basse changée ≥ {pct(T['bass_walking'])} (marche) ou ≥ {pct(T['bass_riff'])} (riff, ostinato)", bass),
        Criterion("7", f"batterie changée ≥ {pct(T['drums'])} ; distance graduée ≥ {pct(T['drums_graded'])}", drums),
        Criterion("8", f"suites de {CHORUS} chorus distinctes sur 16 graines (comping rythme / basse / batterie) ≥ {T['suites']}", suites),
        Criterion("9", f"orchestration : programmes de comping / basse / kit ≥ {T['prog_comping']} / {T['prog_basse']} / {T['prog_kit']} ; suites distinctes ≥ {T['orch_suites']}", orch),
        Criterion("10", f"arc, densité (notes par mesure) : étendue de la trajectoire dès le 2e chorus ≥ {pct(T['dens_range'])}", arc("density", T["dens_range"])),
        Criterion("11", f"arc, vélocité moyenne : étendue dès le 2e chorus ≥ {pct(T['vel_range'])}", arc("velocity", T["vel_range"])),
    ]


def load_all(out: Path) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for f in sorted(out.glob("*.json")):
        if f.name == "summary.json" or f.name.startswith("distance-"):
            continue
        m = json.loads(f.read_text(encoding="utf-8"))
        data[f"{m['profile']}.grille" if m["variant"] == "grille" else m["profile"]] = m
    return data


def evaluate(data: dict[str, dict[str, Any]], criteria: list[Criterion]) -> dict[str, Any]:
    summary: dict[str, Any] = {"thresholds": T, "criteria": {c.ident: c.label for c in criteria}, "profiles": {}}
    for key, m in data.items():
        if "variance" not in m:
            summary["profiles"][key] = {"applicable": False, "reason": m["grid"]["reason"],
                                        "loop": not m["grid"]["reason"].startswith("harmonie")}
            continue
        row = {"applicable": True, "grid_bars": m.get("grid", {}).get("bars"), "criteria": {}}
        for c in criteria:
            value, ok = c.check(m)
            row["criteria"][c.ident] = {"value": value, "ok": ok}
        row["held"] = sum(1 for v in row["criteria"].values() if v["ok"] is True)
        row["failed"] = [k for k, v in row["criteria"].items() if v["ok"] is False]
        summary["profiles"][key] = row
    return summary


def table(summary: dict[str, Any], keys: list[str]) -> str:
    ids = list(summary["criteria"])
    lines = ["| Profil | " + " | ".join(ids) + " | Tenus |", "|---|" + "---|" * len(ids) + "---:|"]
    for k in keys:
        row = summary["profiles"][k]
        if not row["applicable"]:
            lines.append(f"| `{k}` | " + " | ".join(["sans objet"] + [""] * (len(ids) - 1)) + " | |")
            continue
        marks = {None: "·", True: "✓", False: "✗"}
        lines.append(f"| `{k}` | " + " | ".join(marks[row["criteria"][i]["ok"]] for i in ids) +
                     f" | {row['held']} / {sum(1 for i in ids if row['criteria'][i]['ok'] is not None)} |")
    return "\n".join(lines)


def values_table(summary: dict[str, Any], keys: list[str]) -> str:
    """Valeurs mesurées (pas seulement tenu / non tenu), une ligne par profil applicable."""
    ids = list(summary["criteria"])
    lines = ["| Profil | " + " | ".join(ids) + " |", "|---|" + "---|" * len(ids)]
    for k in keys:
        row = summary["profiles"][k]
        if row["applicable"]:
            lines.append(f"| `{k}` | " + " | ".join(row["criteria"][i]["value"] for i in ids) + " |")
    return "\n".join(lines)


def report(args: argparse.Namespace) -> int:
    out = Path(args.out)
    data = load_all(out)
    summary = evaluate(data, build_criteria())
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    plain = [k for k in summary["profiles"] if not k.endswith(".grille")]
    grids = [k for k in summary["profiles"] if k.endswith(".grille") and summary["profiles"][k].get("loop", True)]
    print("## Profils distribués (grille propre du profil)\n")
    print(table(summary, plain))
    print("\n## Sous grille utilisateur (profils `loop`)\n")
    print(table(summary, grids))
    print("\n## Valeurs mesurées (grille propre du profil)\n")
    print(values_table(summary, plain))
    print("\n## Valeurs mesurées (sous grille utilisateur)\n")
    print(values_table(summary, grids))
    print("\n## Critères\n")
    for k, v in summary["criteria"].items():
        print(f"- **{k}** : {v}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect", help="mesure les profils (graines × chorus) et écrit un JSON par mesure")
    c.add_argument("--engine-dir", required=True, help="dépôt du moteur (`profiles/`, `assets/`)")
    c.add_argument("--engine-bin", required=True, help="binaire harmonium-cli déjà compilé")
    c.add_argument("--work-dir", required=True, help="vérités terrain et MIDI (cache, hors dépôt)")
    c.add_argument("--out", default="references/v2-variance")
    c.add_argument("--chorus", type=int, default=CHORUS)
    c.add_argument("--seeds", type=int, default=SEEDS)
    c.add_argument("--jobs", type=int, default=3)
    c.add_argument("--profiles", nargs="*", help="ids (défaut : tous les profils distribués)")
    c.add_argument("--no-grid", action="store_true", help="sans la mesure sous grille utilisateur")
    c.add_argument("--force", action="store_true", help="refait les JSON existants (le cache des exports reste)")
    c.set_defaults(func=collect)
    r = sub.add_parser("report", help="applique les critères aux JSON de --out")
    r.add_argument("--out", default="references/v2-variance")
    r.set_defaults(func=report)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
