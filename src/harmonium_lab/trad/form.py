"""Analyse de forme depuis le texte ABC (reprises, voltas, levées).

``music21.expandRepeats`` perd les airs à levée (anacrouse comptée comme
mesure), à 1re/2e fins (33/36 mesures au lieu de 32) ou aux barres ``::`` /
``|:`` en début de ligne. Ce module découpe les parties à partir des barres
de reprise elles-mêmes :

- une mesure incomplète en tête n'est pas une mesure : c'est la levée
  (``pickup``, en croches), rattachée pour compléter la mesure partielle
  de fin de reprise ;
- 1re/2e fins (``[1 … :| [2 …``) : passe 1 = corps + fin 1, passe 2 = corps
  + fin 2 ;
- ``::`` ferme la reprise en cours et en ouvre une nouvelle ;
- une partie de 16 mesures à moitiés identiques vaut 8+8 (reprise écrite).

Conventions documentées : hauteurs = note la plus aiguë des doubles-cordes,
chromatismes ramenés au degré le plus proche (cf. ``cells``), changements
de métrique en cours d'air non gérés (repli ``music21`` marqué).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from .abcnorm import (
    _first_voice_lines,
    _length,
    _PC,
    _TUPLET_Q,
    parse_key,
    parse_meter,
    parse_tune,
    parse_unit,
)

# Tokenisation du corps (proche de abcnorm._TOKEN, plus annotations
# d'accords "G" et liaisons "-" ; les champs en ligne [M:..] sont sautés).
_TOKEN = re.compile(
    r"""
    (?P<inline>\[[A-Za-z]:[^\]]*\])
  | (?P<bar>::|:+\|?|\|:+|\[?\||\|+|\|)(?P<bvolta>\s*\d[\d,\-]*)?
  | (?P<voltabr>\[?\|\d[\d,\-]*|\[\d[\d,\-]*)
  | (?P<chordanno>"(?P<symbol>[^"]*)")
  | (?P<tuplet>\((?P<tp>\d)(?::(?P<tq>\d*))?(?::(?P<tr>\d*))?)
  | (?P<chord>\[(?P<chordbody>[^\]\[|]*)\](?P<clen>\d*(?:/\d*)*))
  | (?P<note>(?P<acc>[\^_=]*)(?P<pitch>[A-Ga-g])(?P<oct>[,']*)(?P<len>\d*(?:/\d*)*)(?P<tie>-?))
  | (?P<rest>(?P<rk>[zxZX])(?P<rlen>\d*(?:/\d*)*))
  | (?P<broken>[<>]+)
    """,
    re.VERBOSE,
)
_CHORD_NOTE = re.compile(r"([\^_=]*)([A-Ga-g])([,']*)(\d*(?:/\d*)*)")
_DECOR = [re.compile(r"![^!]*!"), re.compile(r"\+[^+]+\+"), re.compile(r"\{[^}]*\}")]

_FRENCH_MODES = {
    "majeur": "ionian",
    "mineur": "aeolian",
    "dorien": "dorian",
    "mixolydien": "mixolydian",
    "lydien": "lydian",
    "phrygien": "phrygian",
    "locrien": "locrian",
}


@dataclass
class Segment:
    """Morceau de musique entre deux barres (durée totale + notes + accords)."""

    notes: list[tuple[Fraction, Fraction, int | None]] = field(default_factory=list)
    dur: Fraction = Fraction(0)
    chords: list[tuple[Fraction, str]] = field(default_factory=list)
    bar_before: str = ""  # symbole de barre d'ouverture ("", "|", "|:", ...)
    volta_before: int | None = None  # n° de fin ([1, [2, |2, :|2...)


@dataclass
class FormPlan:
    """Forme développée : suites de mesures pleines + fragments, par passe."""

    meter: str
    eighths_per_bar: int
    key_tonic_pc: int
    key_name: str
    mode: str
    # Mesures développées : (notes [(onset, dur, midi|None)] en croches Fraction,
    # accords [(offset, symbole)], n° de passe, pleine ou fragment).
    bars: list[tuple[list[tuple[Fraction, Fraction, int | None]], list[tuple[Fraction, str]], int, bool]] = field(
        default_factory=list
    )
    passes: list[list[int]] = field(default_factory=list)  # indices de mesures par passe
    parts: list[int] = field(default_factory=list)  # mesures pleines par passe
    scheme: str = ""
    is_aabb: bool = False
    pickup: Fraction = Fraction(0)
    cause: str | None = None
    source: str = "abc"


_CHORDLIKE = re.compile(r"^[A-G][#b]?(m(?!aj)|maj|min|dim|aug|sus|[0-9/]|$)")


def _looks_like_chord(symbol: str) -> bool:
    """Annotations `"Fin"`, `"1."` ne sont pas des accords (Acrobat's Reel)."""
    return bool(_CHORDLIKE.match(symbol.strip()))


def _volta_group(spec: str | None) -> int | None:
    """Spécification de fin (`1`, `2`, `1,3`, `2,4`, `1-2`) -> groupe 1, 2 ou 0 (les deux).

    Les fins impaires (1re, 3e...) jouent à la 1re passe, les paires à la 2e.
    """
    if not spec:
        return None
    nums: set[int] = set()
    for part in spec.strip().split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = (int(x) for x in part.split("-", 1))
            except ValueError:
                continue
            nums.update(range(a, b + 1))
        elif part.isdigit():
            nums.add(int(part))
    if not nums:
        return None
    odd = any(n % 2 == 1 for n in nums)
    even = any(n % 2 == 0 for n in nums)
    if odd and even:
        return 0
    return 1 if odd else 2


def _pc(letter: str, acc: str) -> int:
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[letter]
    if acc:
        base += acc.count("#") - acc.count("b")
    return base % 12


def _tokenize(body: list[str], signature: dict[str, int], unit: Fraction) -> list[Segment]:
    """Corps ABC -> segments (notes en fractions de ronde, hauteurs MIDI)."""
    text = " ".join(_first_voice_lines(body))
    for rx in _DECOR:
        text = rx.sub(" ", text)

    segments: list[Segment] = [Segment()]
    accidentals: dict[tuple[str, str], int] = {}
    tuplet_left, tuplet_ratio = 0, Fraction(1)
    next_factor = Fraction(1)
    pending_tie: tuple[int, Fraction] | None = None  # (midi, durée cumulée)
    offset = Fraction(0)

    def pitch_of(acc: str, letter: str, octv: str) -> int:
        base = _PC[letter.upper()] + (60 if letter.isupper() else 72)
        base += 12 * octv.count("'") - 12 * octv.count(",")
        slot = (letter, octv)
        if acc:
            shift = 0 if "=" in acc else acc.count("^") - acc.count("_")
            accidentals[slot] = shift
        else:
            shift = accidentals.get(slot, signature.get(letter.upper(), 0))
        return base + shift

    def cur() -> Segment:
        return segments[-1]

    def flush_tie() -> None:
        nonlocal pending_tie, offset
        if pending_tie is not None:
            midi, dur = pending_tie
            cur().notes.append((offset, dur, midi))
            offset += dur
            pending_tie = None

    def push(dur: Fraction, midi: int | None, tie: bool = False) -> None:
        nonlocal tuplet_left, next_factor, pending_tie, offset
        d = dur * next_factor
        next_factor = Fraction(1)
        if tuplet_left > 0:
            d *= tuplet_ratio
            tuplet_left -= 1
        if midi is None:
            flush_tie()
            cur().notes.append((offset, d, None))
            offset += d
            return
        if pending_tie is not None:
            if midi == pending_tie[0]:
                pending_tie = (midi, pending_tie[1] + d)
                if not tie:
                    flush_tie()
                return
            flush_tie()
        if tie:
            pending_tie = (midi, d)
        else:
            cur().notes.append((offset, d, midi))
            offset += d

    def new_bar(symbol: str, volta: int | None) -> None:
        nonlocal accidentals, next_factor, offset
        flush_tie()
        seg = cur()
        seg.dur = offset
        accidentals = {}
        next_factor = Fraction(1)
        offset = Fraction(0)
        segments.append(Segment(bar_before=symbol, volta_before=volta))

    for m in _TOKEN.finditer(text):
        if m.group("inline") is not None:
            continue
        elif m.group("bar") is not None:
            new_bar(m.group("bar"), _volta_group(m.group("bvolta")))
        elif m.group("voltabr") is not None:
            digits = re.search(r"\d[\d,\-]*", m.group("voltabr") or "")
            new_bar(m.group("voltabr"), _volta_group(digits.group(0) if digits else None))
        elif m.group("chordanno") is not None:
            symbol = m.group("symbol")
            if _looks_like_chord(symbol):
                cur().chords.append((offset, symbol))
        elif m.group("tuplet") is not None:
            p = int(m.group("tp"))
            q = int(m.group("tq")) if m.group("tq") else _TUPLET_Q.get(p, 2)
            r = int(m.group("tr")) if m.group("tr") else p
            tuplet_left, tuplet_ratio = r, Fraction(q, p)
        elif m.group("chord") is not None:
            inner = _CHORD_NOTE.findall(m.group("chordbody"))
            if inner:
                top = max(pitch_of(a, ltr, o) for a, ltr, o, _ in inner)
                push(_length(inner[0][3]) * _length(m.group("clen")) * unit, top)
        elif m.group("note") is not None:
            push(
                _length(m.group("len")) * unit,
                pitch_of(m.group("acc"), m.group("pitch"), m.group("oct")),
                tie=bool(m.group("tie")),
            )
        elif m.group("rest") is not None:
            n = _length(m.group("rlen"))
            push(n * unit, None)
        elif m.group("broken") is not None:
            sym = m.group("broken")
            # Même convention qu'abcnorm : > allonge la précédente.
            # L'offset courant suit la durée modifiée (sinon la somme diverge).
            if cur().notes:
                o, d, p = cur().notes[-1]
                small = Fraction(1, 2 ** len(sym))
                if sym[0] == ">":
                    new_d, next_factor = d * (2 - small), small
                else:
                    new_d, next_factor = d * small, 2 - small
                cur().notes[-1] = (o, new_d, p)
                offset += new_d - d
    flush_tie()
    cur().dur = offset
    # Segment final vide (après la dernière barre) : poubelle.
    if segments and not segments[-1].notes and not segments[-1].chords and segments[-1].dur == 0:
        segments.pop()
    return segments


def _combine_markers(old: tuple[str, int | None], new: tuple[str, int | None]) -> tuple[str, int | None]:
    """Fusionne deux frontières vides consécutives (`:|` + `|:` -> `::`)."""
    _, old_end = _classify_bar(old[0])
    new_start, new_end = _classify_bar(new[0])
    volta = new[1] if new[1] is not None else old[1]
    if old_end and new_start:
        return ("::", volta)
    if old_end:
        return (old[0], volta)
    if new_start or new_end or new[1] is not None:
        return (new[0], volta)
    if old[0]:
        return (old[0], volta)
    return ("", volta)


def _drop_empty(segments: list[Segment]) -> tuple[list[Segment], tuple[str, int | None]]:
    """Retire les segments vides (barres consécutives, fins de ligne).

    Les marqueurs portés sont fusionnés et reportés sur le segment non vide
    suivant (ou renvoyés comme frontière finale) : aucun `:|` ne se perd.
    """
    kept: list[Segment] = []
    pending = ("", None)
    for seg in segments:
        if seg.notes or seg.chords or seg.dur != 0:
            if pending != ("", None):
                # La frontière porte la fermeture en attente + son marqueur
                # (`:|` perdu + `|:` -> `::` : aucune reprise ne se perd).
                seg.bar_before, seg.volta_before = _combine_markers(
                    pending, (seg.bar_before, seg.volta_before)
                )
            pending = ("", None)
            kept.append(seg)
        else:
            pending = _combine_markers(pending, (seg.bar_before, seg.volta_before))
    return kept, pending


def _classify_bar(symbol: str) -> tuple[bool, bool]:
    """Symbole -> (début de reprise, fin de reprise)."""
    if symbol == "::":
        return True, True
    return symbol.startswith("|:"), ":|" in symbol


def analyze_form(text: str) -> FormPlan:
    """Texte ABC complet (en-têtes + corps) -> plan de forme développé."""
    tune = parse_tune(text)
    key = parse_key(tune.first("K") or "")
    parsed_meter = parse_meter(tune.first("M"))
    if parsed_meter is None:
        raise ValueError("signature rythmique absente")
    meter, measure_len = parsed_meter
    num, den = (int(x) for x in meter.split("/"))
    unit = parse_unit(tune.first("L"), measure_len)
    k = num * 8 // den

    segments, final = _drop_empty(_tokenize(tune.body, key.signature, unit))
    # Frontières : (symbole, volta) avant chaque segment + après le dernier.
    bounds: list[tuple[str, int | None]] = [(s.bar_before, s.volta_before) for s in segments]
    start_f, end_f = _classify_bar(final[0])
    bounds.append(final if (start_f or end_f or final[1] is not None) else ("", None))

    # Machine à reprises (les ":|" volta-médians — fin 1re suivie d'une 2e —
    # ne ferment rien : ni ":|2" sur la même frontière, ni 2e fin après).
    volta_mid = set()
    for i in range(len(bounds) - 1):
        sym, vol = bounds[i]
        _, end = _classify_bar(sym)
        nxt, nxt_v = bounds[i + 1]
        nxt_starts_second = nxt_v is not None and nxt_v >= 2 or re.match(r"\[?\|\s*2", nxt)
        if end and ((vol is not None and vol >= 2) or nxt_starts_second):
            volta_mid.add(i)
    intervals: list[tuple[int, int]] = []
    stack: list[int] = []
    last_end = 0
    for i, (sym, _) in enumerate(bounds):
        start, end = _classify_bar(sym)
        if start and end:
            # "::" : clôt la section en cours (implicite depuis last_end si
            # besoin) et ouvre la suivante.
            intervals.append((stack.pop() if stack else last_end, i))
            last_end = i
            stack.append(i)
        else:
            if start and stack:
                # Reprise imbriquée : on clôt la précédente (mal formé, déterministe).
                intervals.append((stack.pop(), i))
                last_end = i
            elif start and i > last_end and any(m > last_end and m < i for m in volta_mid):
                # Début d'air sans "|:" explicite mais avec fins : la section
                # volta se clôt ici (reprise implicite depuis last_end).
                intervals.append((last_end, i))
                last_end = i
            if start:
                stack.append(i)
            if end and i not in volta_mid:
                intervals.append((stack.pop() if stack else last_end, i))
                last_end = i
    while stack:
        intervals.append((stack.pop(), len(segments)))

    # Sections non répétées entre les intervalles.
    covered = sorted(intervals)
    sections: list[tuple[int, int, bool]] = []  # (début, fin, répété)
    pos = 0
    for s, e in covered:
        if pos < s:
            sections.append((pos, s, False))
        sections.append((s, e, True))
        pos = e
    if pos < len(segments):
        sections.append((pos, len(segments), False))
    if not sections and segments:
        sections.append((0, len(segments), False))

    # Levée initiale : premier segment incomplet (convention : pas une mesure).
    # Retenue pour compléter les fins partielles (globale, repli par passe).
    first = 0
    if segments and 0 < segments[0].dur < measure_len:
        first = 1
    pickup_8 = segments[0].dur * 8 if first else Fraction(0)

    # Levées médianes : tête partielle d'une section non répétée (ni la 1re)
    # suivant une fin pleine (`...dBB:| d|f2...`) : hors mesures, non marquées.
    # Au-delà de 2, l'air est déclaré croche (trop irrégulier).
    drop: set[int] = set()
    for idx, (s, e, repeated) in enumerate(sections):
        if idx == 0 or repeated:
            continue
        h = max(s, first)
        if h >= e or not (0 < segments[h].dur < measure_len):
            continue
        pd = segments[h - 1].dur if h > 0 else Fraction(0)
        prev_full = pd == measure_len or (
            0 < pd < measure_len
            and (measure_len - pd == (segments[0].dur if first else None))
        )
        if prev_full:
            drop.add(h)
    mid_pickups = len(drop)

    # Passes : chaque intervalle répété joue deux fois (voltas), sinon une.
    # sec_info mémorise l'association section -> passes pour le scheme.
    # pass_pickup : segment de levée complétant la fin de chaque passe
    # (levée de section prioritaire, sinon levée initiale).
    passes: list[list[int]] = []
    pass_pickups: list[int | None] = []
    sec_info: list[dict] = []
    for s, e, repeated in sections:
        lo = max(s, first)
        sec_pickup: int | None = None
        if repeated and lo < e and 0 < segments[lo].dur < measure_len:
            # Levée en tête de reprise (`|: fg | ...`) : hors mesures,
            # complète la fin de chaque passe de la section.
            sec_pickup = lo
            lo += 1
        ids = [i for i in range(lo, e) if i not in drop]
        if not ids:
            continue
        pickup_here = sec_pickup if sec_pickup is not None else (0 if first else None)
        if not repeated:
            passes.append(ids)
            pass_pickups.append(pickup_here)
            sec_info.append({"repeated": False, "body": [], "npasses": 1})
            continue
        tags: dict[int, int] = {}
        tag: int | None = None
        for i in range(lo, e):
            _, v = bounds[i]
            if v is not None:
                tag = v
            tags[i] = tag if tag is not None else 0
        p1 = [i for i in ids if tags.get(i, 0) in (0, 1)]
        p2 = [i for i in ids if tags.get(i, 0) in (0, 2)]
        passes.append(p1 if p1 else ids)
        pass_pickups.append(pickup_here)
        passes.append(p2 if p2 else ids)
        pass_pickups.append(pickup_here)
        sec_info.append({
            "repeated": True,
            "body": [i for i in ids if tags.get(i, 0) == 0],
            "npasses": 2,
        })

    # Développement en mesures : complétion levée/fin, puis jonctions partielle+partielle.
    eighth = Fraction(1, 8)
    bars: list[tuple[list[tuple[Fraction, Fraction, int | None]], list[tuple[Fraction, str]], int, bool]] = []
    pass_bars: list[list[int]] = []
    for pi, ids in enumerate(passes):
        cur: list[int] = []
        seq = list(ids)
        pk = pass_pickups[pi]
        for si in seq:
            seg = segments[si]
            notes = [(o / eighth, d / eighth, p) for o, d, p in seg.notes]
            chords = [(o / eighth, s) for o, s in seg.chords]
            full = seg.dur == measure_len
            # Complétion du dernier segment partiel par la levée.
            if pk is not None and si == seq[-1] and 0 < seg.dur < measure_len:
                need = measure_len - seg.dur
                if need == segments[pk].dur:
                    tail, tseg = seg, segments[pk]
                    shift = tail.dur / eighth
                    notes = notes + [(o / eighth + shift, d / eighth, p) for o, d, p in tseg.notes]
                    chords = chords + [(o / eighth + shift, s) for o, s in tseg.chords]
                    full = True
            bars.append((notes, chords, pi, full))
            cur.append(len(bars) - 1)
        pass_bars.append(cur)

    # Jonctions : fin partielle + début partiel de la passe suivante = mesure pleine.
    merged: list[bool] = [False] * len(bars)
    for a, b in zip(pass_bars, pass_bars[1:]):
        if not a or not b or merged[a[-1]] or merged[b[0]]:
            continue
        na, ca, pa, fa = bars[a[-1]]
        nb, cb, pb, fb = bars[b[0]]
        if not fa and not fb and pa != pb:
            span_a = max([o + d for o, d, _ in na] + [Fraction(0)])
            span_b = max([o + d for o, d, _ in nb] + [Fraction(0)])
            if span_a + span_b == k:
                nb_shifted = [(o + span_a, d, p) for o, d, p in nb]
                cb_shifted = [(o + span_a, s) for o, s in cb]
                bars[a[-1]] = (na + nb_shifted, ca + cb_shifted, pa, True)
                merged[b[0]] = True
    bars = [b for i, b in enumerate(bars) if not merged[i]]
    pass_bars = [[i for i in pb if not merged[i]] for pb in pass_bars]
    # Réindexe après filtrage.
    kept = [i for i, m in enumerate(merged) if not m]
    remap = {old: new for new, old in enumerate(kept)}
    pass_bars = [[remap[i] for i in pb] for pb in pass_bars]

    # Signatures de contenu (hauteurs, attaques, durées).
    def sig(bi: int) -> tuple:
        notes, _, _, _ = bars[bi]
        return tuple((p, float(o), float(d)) for o, d, p in notes if p is not None)

    def seg_sig(si: int) -> tuple:
        seg = segments[si]
        return tuple((p, float(d)) for _, d, p in seg.notes)

    def letter_of(key: tuple) -> str:
        if key not in letters:
            letters[key] = chr(ord("A") + len(letters))
        return letters[key]

    letters: dict[tuple, str] = {}
    scheme_chars: list[str] = []
    part_lens: list[int] = []
    cursor = 0
    for sec in sec_info:
        if sec["repeated"]:
            # Une lettre par section (corps sans les fins) : les 1re/2e fins
            # diffèrent par construction, les deux passes rejouent la même partie.
            letter = letter_of(("sec", tuple(seg_sig(i) for i in sec["body"])))
            for _ in range(sec["npasses"]):
                pb = pass_bars[cursor]
                cursor += 1
                full = [bi for bi in pb if bars[bi][3]]
                # Partie de 16 : reprise écrite ? Moitiés identiques (8+8),
                # ou corps répété avec fins propres (6+ communes au moins).
                if len(full) == 16 and not [bi for bi in pb if not bars[bi][3]]:
                    first_half = tuple(sig(bi) for bi in full[:8])
                    second_half = tuple(sig(bi) for bi in full[8:])
                    if first_half == second_half or first_half[:6] == second_half[:6]:
                        scheme_chars += [letter] * 2
                        part_lens += [8, 8]
                        continue
                scheme_chars.append(letter)
                part_lens.append(len(full))
        else:
            # Section non répétée : découpée en mesures de 8 (reprise écrite).
            pb = pass_bars[cursor]
            cursor += 1
            full = [bi for bi in pb if bars[bi][3]]
            chunks = [full[c : c + 8] for c in range(0, len(full), 8)]
            ci = 0
            while ci < len(chunks):
                cur_sig = tuple(sig(bi) for bi in chunks[ci])
                nxt = tuple(sig(bi) for bi in chunks[ci + 1]) if ci + 1 < len(chunks) else None
                # Paire au même corps (6+ communes) : deux passes d'une partie.
                if nxt is not None and (cur_sig == nxt or cur_sig[:6] == nxt[:6]):
                    letter = letter_of(("pair", cur_sig, nxt))
                    scheme_chars += [letter, letter]
                    part_lens += [len(chunks[ci]), len(chunks[ci + 1])]
                    ci += 2
                else:
                    scheme_chars.append(letter_of(("chunk", cur_sig)))
                    part_lens.append(len(chunks[ci]))
                    ci += 1
    scheme = "".join(scheme_chars)
    has_frags = any(not full for _, _, _, full in bars)
    if has_frags or mid_pickups > 2:
        scheme = "croche"
    frag_ids = [bi for pb in pass_bars for bi in pb if not bars[bi][3]]
    is_aabb, cause = describe_form(
        scheme, part_lens, frag_ids,
        too_many_pickups=mid_pickups > 2, n_pickups=mid_pickups,
    )

    mode_en = _FRENCH_MODES.get(key.mode, "ionian")
    return FormPlan(
        meter=meter,
        eighths_per_bar=k,
        key_tonic_pc=_pc(key.tonic[0], key.tonic[1:] if len(key.tonic) > 1 else ""),
        key_name=key.tonic,
        mode=mode_en,
        bars=bars,
        passes=pass_bars,
        parts=part_lens,
        scheme=scheme,
        is_aabb=is_aabb,
        pickup=pickup_8,
        cause=cause,
        source="abc",
    )


def describe_form(
    scheme: str,
    part_lens: list[int],
    frag_ids: list[int],
    too_many_pickups: bool = False,
    n_pickups: int = 0,
) -> tuple[bool, str | None]:
    """(is_aabb, cause) depuis un scheme : règle partagée ABC / MIDI."""
    is_aabb = scheme == "AABB" and part_lens == [8, 8, 8, 8]
    if is_aabb:
        return True, None
    if too_many_pickups:
        return False, f"croche:trop-de-levées-médianes ({n_pickups})"
    if frag_ids:
        return False, f"croche:mesures-partielles {frag_ids}"
    if scheme in ("AA", "A"):
        return False, "partie-unique"
    if scheme == "AB":
        return False, "AB-sans-reprises"
    if scheme in ("ABC", "ABCD", "AABBCC", "AABBCCDD"):
        return False, "trois-parties-et-plus"
    if scheme == "ABAB":
        return False, "ABAB"
    if any(p == 16 for p in part_lens):
        return False, "parties-16-mesures"
    if any(p != 8 for p in part_lens):
        return False, f"parties-irregulieres:{part_lens}"
    return False, f"forme-libre:{scheme}"


def plan_to_dict(plan: FormPlan) -> dict[str, Any]:
    """Plan -> dict JSON-sérialisable pour ``TradTune.form``."""
    return {
        "scheme": plan.scheme,
        "parts": list(plan.parts),
        "is_aabb": plan.is_aabb,
        "pickup": float(plan.pickup),
        "cause": plan.cause,
        "source": plan.source,
    }
