"""Comparaison généré vs réel (specs/001-trad-dataset D6, ``trad-compare``).

Compare les features D5 de MIDI du moteur au profil d'un type : écarts
triés par |z|, une phrase française par écart (table ``EXPLANATIONS``),
et les 3 airs réels les plus proches de chaque généré (distance
euclidienne sur vecteur normalisé).

Pur et déterministe (hors horodatage de sortie, géré par la CLI) ;
aucun réseau, aucune écriture disque ici.
"""

from __future__ import annotations

import math
from typing import Any

from .features import DURATION_BUCKETS, INTERVAL_CLASSES

#: Pluriels français des types, pour les phrases du rapport.
TYPE_PLURALS: dict[str, str] = {
    "reel": "reels",
    "jig": "gigues",
    "waltz": "valses",
    "march": "marches",
    "quadrille": "quadrilles",
    "cotillon": "cotillons",
}

#: Clés scalaires comparées (noms ``__``-joints de ``FEATURE_SCALARS``).
SCALAR_KEYS = [
    "n_bars",
    "register__ambitus",
    "register__mean_pitch_part0",
    "register__mean_pitch_part1",
    "register__b_minus_a_mean_pitch",
    "intervals__stepwise_ratio",
    "harmony__chords_per_bar",
    "form__repeat_identity",
    "form__share_identical_bars_5_6_vs_1_2",
]

#: Clé dérivée vedette : part d'intervalles ≥ quarte (quarte + quinte + > quinte).
LEAP_KEY = "leap_ratio"
LEAP_BINS = ("fourth", "fifth", "larger")

#: Table des textes explicatifs : UNE entrée par feature comparée.
#: Chaque entrée : sujet (ce que fait la vraie musique), unité ("%"
#: = gabarit à pourcentages, sinon gabarit à valeurs), plancher
#: d'écart-type (évite les z explosifs), et ce que l'écart veut dire
#: à l'oreille selon que le moteur est au-dessus (``oreille_plus``)
#: ou en dessous (``oreille_moins``). L'entrée ``onset_hist`` est
#: paramétrée par ``{slot}`` (une phrase par position d'attaque).
EXPLANATIONS: dict[str, dict[str, Any]] = {
    "leap_ratio": {
        "sujet": "sautent (intervalle ≥ quarte)",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "la mélodie générée sonne plus décousue, moins chantable",
        "oreille_moins": "la mélodie générée sonne plus « en gamme », moins dansante",
    },
    "intervals__stepwise_ratio": {
        "sujet": "avancent par pas conjoints (note répétée ou voisine)",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "la mélodie générée sonne plus coulée, presque ronronnante",
        "oreille_moins": "la mélodie générée sonne plus heurtée, moins coulée",
    },
    "interval_hist__unison": {
        "sujet": "répètent la même note d'affilée",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "le moteur martèle : effet mitraillette, moins de relief",
        "oreille_moins": "le moteur évite les répétitions : moins d'accent tonique",
    },
    "interval_hist__second": {
        "sujet": "avancent par seconde (note voisine)",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "la mélodie générée sonne plus en gamme, plus prévisible",
        "oreille_moins": "la mélodie générée sonne moins coulée, plus anguleuse",
    },
    "interval_hist__third": {
        "sujet": "avancent par tierce",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "la mélodie générée arpège plus, sonne plus guillerette",
        "oreille_moins": "la mélodie générée arpège moins, sonne plus plate",
    },
    "interval_hist__fourth": {
        "sujet": "sautent d'une quarte",
        "unite": "%",
        "plancher": 0.01,
        "oreille_plus": "le moteur saute plus : allure plus cavalière",
        "oreille_moins": "le moteur saute moins : allure plus sage",
    },
    "interval_hist__fifth": {
        "sujet": "sautent d'une quinte",
        "unite": "%",
        "plancher": 0.01,
        "oreille_plus": "le moteur fait des bonds : sonne plus fanfare",
        "oreille_moins": "le moteur reste plus sage dans ses intervalles",
    },
    "interval_hist__larger": {
        "sujet": "font des bonds de plus d'une quinte",
        "unite": "%",
        "plancher": 0.01,
        "oreille_plus": "la mélodie générée fait des bonds : sonne acrobatique, peu dansante",
        "oreille_moins": "la mélodie générée reste groupée : sonne plus posée",
    },
    "duration_hist__1": {
        "sujet": "jouent des notes courtes (une croche)",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "le moteur mitraille plus de croches : sonne plus nerveux",
        "oreille_moins": "le moteur tient moins le débit de croches : sonne moins nerveux, moins dansant",
    },
    "duration_hist__2": {
        "sujet": "tiennent des notes de deux croches (noires)",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "le moteur s'attarde plus : sonne plus chanté, moins perlé",
        "oreille_moins": "le moteur s'attarde moins : sonne plus perlé, moins chanté",
    },
    "duration_hist__3": {
        "sujet": "tiennent des notes de trois croches (noires pointées)",
        "unite": "%",
        "plancher": 0.01,
        "oreille_plus": "le moteur étire plus ses notes : sonne plus traînant",
        "oreille_moins": "le moteur étire moins ses notes : sonne plus carré",
    },
    "duration_hist__4+": {
        "sujet": "tiennent des notes longues (quatre croches et plus)",
        "unite": "%",
        "plancher": 0.01,
        "oreille_plus": "le moteur pose des notes longues : sonne plus solennel, moins dansant",
        "oreille_moins": "le moteur pose moins de notes longues : sonne plus enlevé",
    },
    "onset_hist": {
        "sujet": "attaquent sur la croche {slot} de la mesure",
        "unite": "%",
        "plancher": 0.02,
        "oreille_plus": "le moteur insiste plus sur ce temps : l'accent sonne déplacé",
        "oreille_moins": "le moteur délaisse ce temps : le pied tape moins juste",
    },
    "n_bars": {
        "sujet": "durent en moyenne",
        "unite": "mesures",
        "plancher": 1.0,
        "oreille_plus": "l'air généré sonne étiré, la forme se perd",
        "oreille_moins": "l'air généré sonne tronqué, on reste sur sa faim",
    },
    "register__ambitus": {
        "sujet": "couvrent un ambitus moyen de",
        "unite": "demi-tons",
        "plancher": 1.0,
        "oreille_plus": "la mélodie générée s'éparpille : moins chantable",
        "oreille_moins": "la mélodie générée reste resserrée : moins d'allant",
    },
    "register__mean_pitch_part0": {
        "sujet": "jouent la partie A autour de",
        "unite": "note",
        "plancher": 1.0,
        "oreille_plus": "la partie A générée sonne plus haut perchée : couleur plus criarde",
        "oreille_moins": "la partie A générée sonne plus grave : couleur plus sourde",
    },
    "register__mean_pitch_part1": {
        "sujet": "jouent la partie B autour de",
        "unite": "note",
        "plancher": 1.0,
        "oreille_plus": "la partie B générée sonne plus haut perchée : couleur plus criarde",
        "oreille_moins": "la partie B générée sonne plus grave : couleur plus sourde",
    },
    "register__b_minus_a_mean_pitch": {
        "sujet": "montent en moyenne de la partie A vers la partie B de",
        "unite": "demi-tons",
        "plancher": 0.5,
        "oreille_plus": "le contraste A/B généré sonne exagéré : la B décolle trop",
        "oreille_moins": "les parties A et B générées se ressemblent : on ne sent pas la montée",
    },
    "harmony__chords_per_bar": {
        "sujet": "changent d'accord en moyenne",
        "unite": "fois par mesure",
        "plancher": 0.1,
        "oreille_plus": "l'harmonie générée bouge trop : sonne agitée",
        "oreille_moins": "l'harmonie générée stagne : sonne monotone",
    },
    "form__repeat_identity": {
        "sujet": "rejouent leurs reprises à l'identique à",
        "unite": "%",
        "plancher": 0.05,
        "oreille_plus": "le moteur répète au cordeau : sonne mécanique",
        "oreille_moins": "le moteur varie trop ses reprises : on ne reconnaît pas l'air",
    },
    "form__share_identical_bars_5_6_vs_1_2": {
        "sujet": "recyclent leurs mesures 1-2 en mesures 5-6 à",
        "unite": "%",
        "plancher": 0.05,
        "oreille_plus": "le moteur tourne en rond : sonne redondant",
        "oreille_moins": "le moteur ne reprend jamais son motif : sonne décousu",
    },
}

#: Ordre d'affichage à |z| égal (déterministe) : insertion ci-dessus.
COMPARE_ORDER = list(EXPLANATIONS)


def _leap_ratio(feat: dict[str, Any]) -> float:
    hist = feat.get("intervals", {}).get("hist", {})
    return round(sum(float(hist.get(b, 0.0)) for b in LEAP_BINS), 4)


def feature_vector(feat: dict[str, Any]) -> dict[str, float]:
    """Vecteur comparé d'un air : scalaires + leap + bins + attaques."""
    vec: dict[str, float] = {}
    for key in SCALAR_KEYS:
        node: Any = feat
        for part in key.split("__"):
            if not isinstance(node, dict) or part not in node:
                node = None
                break
            node = node[part]
        if isinstance(node, (int, float)):
            vec[key] = float(node)
    vec[LEAP_KEY] = _leap_ratio(feat)
    hist = feat.get("intervals", {}).get("hist", {})
    for b in INTERVAL_CLASSES:
        vec[f"interval_hist__{b}"] = float(hist.get(b, 0.0))
    dhist = feat.get("rhythm", {}).get("duration_hist", {})
    for b in DURATION_BUCKETS:
        vec[f"duration_hist__{b}"] = float(dhist.get(b, 0.0))
    for i, v in enumerate(feat.get("rhythm", {}).get("onset_hist", [])):
        vec[f"onset_hist__{i}"] = float(v)
    return vec


def _stats(values: list[float]) -> tuple[float, float]:
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return mean, math.sqrt(var)


_SOLFEGE = ["do", "do#", "ré", "ré#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]


def midi_to_name(pitch: float) -> str:
    """Hauteur MIDI (moyenne) -> nom français (``la4``), pour non-musiciens."""
    p = int(round(pitch))
    return f"{_SOLFEGE[p % 12]}{p // 12 - 1}"


def _fmt_value(key: str, value: float) -> str:
    entry = EXPLANATIONS.get(key, EXPLANATIONS.get(key.rsplit("__", 1)[0], {}))
    unite = entry.get("unite", "")
    if unite == "%":
        return f"{value * 100:.0f}"
    if unite == "note":
        return midi_to_name(value)
    if unite in ("mesures", "demi-tons"):
        return f"{value:.0f}"
    if unite == "fois par mesure":
        return f"{value:.1f}"
    return f"{value:.2f}"


def explain(key: str, tune_type: str, real: float, gen: float) -> str:
    """Une phrase française : les deux valeurs + ce que ça veut dire à l'oreille."""
    base = key.rsplit("__", 1)[0] if key not in EXPLANATIONS else key
    slot = key.rsplit("__", 1)[1] if key not in EXPLANATIONS else None
    entry = EXPLANATIONS[base]
    sujet = entry["sujet"].format(slot=int(slot) + 1) if slot is not None else entry["sujet"]
    plurals = TYPE_PLURALS.get(tune_type, tune_type)
    oreille = entry["oreille_plus"] if gen >= real else entry["oreille_moins"]
    r, g = _fmt_value(base, real), _fmt_value(base, gen)
    if entry["unite"] == "%":
        # Sujets en « à » (« à 30 % des cas ») vs autres (« dans 31 % des cas »).
        to_pct = sujet.endswith(" à")
        real_part = f"{sujet} {r} % des cas" if to_pct else f"{sujet} dans {r} % des cas"
        gen_part = f"le moteur {g} %" if to_pct else f"le moteur dans {g} %"
        return f"Les {plurals} réels {real_part}, {gen_part} : {oreille}."
    if entry["unite"] == "note":
        return f"Les {plurals} réels {sujet} {r}, le moteur : {g} : {oreille}."
    return (
        f"Les {plurals} réels {sujet} : {r} {entry['unite']}, "
        f"le moteur : {g} {entry['unite']} : {oreille}."
    )


def reference_stats(
    profile: dict[str, Any], real_vectors: list[dict[str, float]]
) -> dict[str, tuple[float, float]]:
    """Référence par clé : (moyenne, écart-type).

    Scalaires : moyenne et écart-type du **profil** du type (c'est lui
    la référence) ; histogrammes et ``leap_ratio`` (le profil n'en
    garde que la moyenne) : dispersion calculée sur les airs réels.
    Repli : statistique des réels si le profil ne connaît pas la clé.
    """
    ref: dict[str, tuple[float, float]] = {}
    prof_scalars = profile.get("scalars", {})
    keys = {k for v in real_vectors for k in v}
    for key in keys:
        vals = [v[key] for v in real_vectors if key in v]
        mean, std = _stats(vals) if vals else (0.0, 0.0)
        if key in prof_scalars:
            mean = float(prof_scalars[key]["mean"])
            std = float(prof_scalars[key]["std"])
        base = key if key in EXPLANATIONS else key.rsplit("__", 1)[0]
        floor = float(EXPLANATIONS.get(base, {}).get("plancher", 0.01))
        ref[key] = (mean, max(std, floor))
    return ref


def _deviation(
    key: str, value: float, ref: dict[str, tuple[float, float]], tune_type: str
) -> dict[str, Any] | None:
    """Écart d'une valeur vs la référence (None si clé inconnue)."""
    if key not in ref:
        return None
    real_mean, denom = ref[key]
    z = (value - real_mean) / denom if denom > 0 else 0.0
    return {
        "key": key,
        "real_value": round(real_mean, 4),
        "generated_value": round(value, 4),
        "z": round(z, 3),
        "sentence": explain(key, tune_type, real_mean, value),
    }


def _sort_deviations(deviations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {k: i for i, k in enumerate(COMPARE_ORDER)}

    def base_key(key: str) -> str:
        return key if key in EXPLANATIONS else key.rsplit("__", 1)[0]

    deviations.sort(key=lambda d: (-abs(d["z"]), order.get(base_key(d["key"]), 999), d["key"]))
    return deviations


def compare_to_profile(
    generated: dict[str, dict[str, Any]],
    ref: dict[str, tuple[float, float]],
    tune_type: str,
) -> list[dict[str, Any]]:
    """Écarts agrégés (moyenne des générés vs profil), triés par |z|.

    ``generated`` : nom de fichier -> ``features()`` ; ``ref`` :
    sortie de ``reference_stats``.
    """
    gen_vecs = {name: feature_vector(f) for name, f in generated.items()}
    keys = sorted({k for v in gen_vecs.values() for k in v} & set(ref))
    deviations = []
    for key in keys:
        gens = [v[key] for v in gen_vecs.values() if key in v]
        if not gens:
            continue
        dev = _deviation(key, sum(gens) / len(gens), ref, tune_type)
        if dev is not None:
            deviations.append(dev)
    return _sort_deviations(deviations)


def deviations_for_file(
    feat: dict[str, Any],
    ref: dict[str, tuple[float, float]],
    tune_type: str,
) -> list[dict[str, Any]]:
    """Écarts d'un seul généré vs le profil, triés par |z|."""
    vec = feature_vector(feat)
    deviations = [
        dev
        for key in sorted(set(vec) & set(ref))
        if (dev := _deviation(key, vec[key], ref, tune_type)) is not None
    ]
    return _sort_deviations(deviations)


def nearest_reals(
    feat: dict[str, Any],
    reals: list[tuple[str, dict[str, float]]],
    ref: dict[str, tuple[float, float]],
    k: int = 3,
) -> list[tuple[str, float]]:
    """Les ``k`` airs réels les plus proches (id, distance), vecteur normalisé.

    ``reals`` : (id, vecteur) ; ``ref`` : normalisation (moyenne /
    écart-type plancher).
    """
    vec = feature_vector(feat)
    keys = sorted({kk for _, v in reals for kk in v} & set(vec) & set(ref))
    ranked = []
    for rid, rvec in reals:
        dist = math.sqrt(
            sum(
                ((vec[key] - rvec.get(key, ref[key][0])) / ref[key][1]) ** 2
                for key in keys
            )
        )
        ranked.append((rid, round(dist, 4)))
    ranked.sort(key=lambda t: (t[1], t[0]))
    return ranked[:k]
