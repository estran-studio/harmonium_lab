"""Analyse de symboles d'accord : notation jazz de la Weimar Jazz Database et qualités du moteur.

Une seule structure, `Chord`, sert aux deux sources (corpus et généré) pour que les mesures
de basse (`bass_measures`) n'aient qu'un chemin de calcul. Sortie :

- `root` : classe de hauteur de la fondamentale (0 = do) ;
- `bass` : classe de hauteur de la basse (la basse d'un accord slash, sinon la fondamentale) ;
- `quality` : qualité normalisée parmi `maj`, `min`, `dom`, `dim`, `hdim`, `aug`, `sus` ;
- `tones` : classes de hauteur des notes d'accord (1, 3, 5, 7 écrites, plus 6 et les tensions
  écrites 9, 11, 13 et leurs altérations) ; une triade n'a que ses trois notes ;
- `scale` : classes de hauteur de la gamme de référence de l'accord.

Notation WJazzD (lue sur les 419 symboles distincts de la table `beats.chord`, dont 371
dans le sous-ensemble `rhythmfeel = 'SWING'`, plus `NC`) : fondamentale `[A-G][b#]?`, puis un
marqueur (`-` mineur, `+` augmenté, `o` diminué, `sus`, `m7b5` ou `h7` demi-diminué), une
extension (`j7` septième majeure, `7`, `6`, `69`), `alt` éventuel, puis des tensions dont
l'altération SUIT le nombre (`79b` = 7 ♭9, `7911#` = 7 9 ♯11, `79b13b` = 7 ♭9 ♭13), enfin une
basse `/X` ; l'écriture usuelle `C7b9`, `C7#11` (altération avant le nombre) est acceptée en
repli. `NC` = pas d'accord (renvoie `None`). Un symbole qui n'entre pas dans cette
grammaire lève `ChordParseError` : l'appelant compte les symboles non analysés.

Gammes de référence (choix déclarés ; « note diatonique » du moteur = note de cette gamme à 1,
2 ou 3 demi-tons de la cible) :

| qualité | gamme |
|---|---|
| `maj` | ionien ; lydien si ♯11 écrit |
| `min` | dorien ; mineur mélodique si septième majeure écrite (`-j7`) |
| `dom` | mixolydien ; lydien b7 si ♯11 ; octotonique demi-ton/ton si ♭9 seul ; altérée si `alt`, ♯9 ou ♭9 avec ♭13 ; mixolydien ♭6 si ♭13 seul |
| `dim` | octotonique ton/demi-ton |
| `hdim` | locrien ♮2 (0 2 3 5 6 8 10) |
| `aug` | gamme par tons ; lydien augmenté avec septième majeure |
| `sus` | mixolydien |

Les qualités du moteur (`""`, `m`, `7`, `maj7`, `m7b5`, `dim7`, `7alt`, `6/9`, `13sus4`…,
suffixes lus par `Chord::from_name`) passent par `from_engine`, qui produit la même
structure. Les synonymes acceptés par le moteur (`maj`, `aug`, `add2`, `m(b5)`, `sus`) le sont
aussi ici.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NOTE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITIES = ("maj", "min", "dom", "dim", "hdim", "aug", "sus")

# Gammes (demi-tons au-dessus de la fondamentale).
IONIAN = (0, 2, 4, 5, 7, 9, 11)
LYDIAN = (0, 2, 4, 6, 7, 9, 11)
MIXOLYDIAN = (0, 2, 4, 5, 7, 9, 10)
LYDIAN_DOMINANT = (0, 2, 4, 6, 7, 9, 10)
MIXOLYDIAN_B6 = (0, 2, 4, 5, 7, 8, 10)
HALF_WHOLE = (0, 1, 3, 4, 6, 7, 9, 10)
WHOLE_HALF = (0, 2, 3, 5, 6, 8, 9, 11)
ALTERED = (0, 1, 3, 4, 6, 8, 10)
DORIAN = (0, 2, 3, 5, 7, 9, 10)
MELODIC_MINOR = (0, 2, 3, 5, 7, 9, 11)
LOCRIAN_NAT2 = (0, 2, 3, 5, 6, 8, 10)
WHOLE_TONE = (0, 2, 4, 6, 8, 10)
LYDIAN_AUGMENTED = (0, 2, 4, 6, 8, 9, 11)


class ChordParseError(ValueError):
    """Symbole d'accord hors grammaire (à compter, jamais à deviner)."""


@dataclass(frozen=True)
class Chord:
    """Un accord analysé. `tones` et `scale` sont des ensembles de classes de hauteur absolues."""

    symbol: str
    root: int
    bass: int
    quality: str
    tones: frozenset[int]
    scale: frozenset[int]

    def relative(self, pc: int) -> int:
        """Intervalle (0..11) de la classe de hauteur `pc` au-dessus de la fondamentale."""
        return (pc - self.root) % 12


def _scale_for(quality: str, rel: frozenset[int], *, alt: bool) -> tuple[int, ...]:
    """Gamme de référence (relative à la fondamentale) selon la qualité et les notes écrites."""
    if quality == "maj":
        return LYDIAN if 6 in rel else IONIAN
    if quality == "min":
        return MELODIC_MINOR if 11 in rel else DORIAN
    if quality == "hdim":
        return LOCRIAN_NAT2
    if quality == "dim":
        return WHOLE_HALF
    if quality == "aug":
        return LYDIAN_AUGMENTED if 11 in rel else WHOLE_TONE
    if quality == "dom":
        flat9, sharp9, sharp11, flat13 = 1 in rel, 3 in rel and 4 in rel, 6 in rel, 8 in rel
        if alt or sharp9 or (flat9 and flat13):
            return ALTERED
        if flat9:
            return HALF_WHOLE
        if sharp11:
            return LYDIAN_DOMINANT
        if flat13:
            return MIXOLYDIAN_B6
        return MIXOLYDIAN
    return MIXOLYDIAN  # sus


def _build(symbol: str, root: int, bass: int, quality: str, rel: set[int], *, alt: bool = False) -> Chord:
    """Assemble un `Chord` depuis la qualité et les intervalles relatifs des notes d'accord."""
    frozen = frozenset(rel)
    scale = _scale_for(quality, frozen, alt=alt)
    return Chord(
        symbol=symbol,
        root=root,
        bass=bass,
        quality=quality,
        tones=frozenset((root + i) % 12 for i in frozen),
        scale=frozenset((root + i) % 12 for i in scale),
    )


def note_pc(token: str) -> int:
    """Nom de note (`Bb`, `F#`) → classe de hauteur."""
    pc = NOTE_PC[token[0]]
    for accidental in token[1:]:
        pc += 1 if accidental == "#" else -1
    return pc % 12


# Tension écrite (nombre, altération) → intervalle au-dessus de la fondamentale.
_TENSION = {("9", ""): 2, ("9", "b"): 1, ("9", "#"): 3, ("11", ""): 5, ("11", "#"): 6,
            ("11", "b"): 4, ("13", ""): 9, ("13", "b"): 8, ("13", "#"): 10}

_WJAZZD = re.compile(
    r"^(?P<root>[A-G][b#]?)"
    r"(?P<mark>m7b5|h7|o|\+|sus|-)?"
    r"(?P<ext>j7|69|7|6)?"
    r"(?P<alt>alt)?"
    r"(?P<tens>(?:(?:9|11|13)[b#]?)*)"
    r"(?:/(?P<bass>[A-G][b#]?))?$"
)
_TENSION_TOKEN = re.compile(r"(9|11|13)([b#]?)")
# Écriture usuelle hors WJazzD (`C7b9`, `C7#11`) : l'altération PRÉCÈDE le nombre.
_PREFIX_FORM = re.compile(_WJAZZD.pattern.replace("(?:(?:9|11|13)[b#]?)*", "(?:[b#](?:9|11|13))*"))
_PREFIX_TOKEN = re.compile(r"([b#])(9|11|13)")


def parse_wjazzd(symbol: str) -> Chord | None:
    """Symbole de `beats.chord` → `Chord` ; `None` pour `NC` ; `ChordParseError` sinon."""
    text = symbol.strip()
    if text == "NC":
        return None
    match = _WJAZZD.match(text)
    tens_token = _TENSION_TOKEN
    if match is None:
        match = _PREFIX_FORM.match(text)
        tens_token = _PREFIX_TOKEN
    if match is None:
        raise ChordParseError(f"symbole d'accord non analysé : {symbol!r}")
    root = note_pc(match["root"])
    bass = note_pc(match["bass"]) if match["bass"] else root
    mark, ext, alt = match["mark"] or "", match["ext"] or "", bool(match["alt"])
    found = tens_token.findall(match["tens"])
    tens = [(n, a) for n, a in found] if tens_token is _TENSION_TOKEN else [(n, a) for a, n in found]
    if mark == "h7":
        mark = "m7b5"

    rel: set[int] = {0}
    if mark == "m7b5":
        quality, rel = "hdim", {0, 3, 6, 10}
        if ext not in ("", "7"):
            raise ChordParseError(f"symbole d'accord non analysé : {symbol!r}")
    elif mark == "o":
        quality, rel = "dim", {0, 3, 6}
        if ext == "7":
            rel.add(9)
        elif ext:
            raise ChordParseError(f"symbole d'accord non analysé : {symbol!r}")
    elif mark == "sus":
        quality, rel = "sus", {0, 5, 7}
        if ext == "7":
            rel.add(10)
        elif ext == "j7":
            rel.add(11)
        elif ext in ("6", "69"):
            rel.add(9)
    elif mark == "+":
        quality, rel = "aug", {0, 4, 8}
        if ext == "7":
            rel.add(10)
        elif ext == "j7":
            rel.add(11)
    elif mark == "-":
        quality, rel = "min", {0, 3, 7}
        if ext == "7":
            rel.add(10)
        elif ext == "j7":
            rel.add(11)
        elif ext in ("6", "69"):
            rel.add(9)
    else:
        # Pas de marqueur : triade majeure, sixte, majeure 7, ou dominante (`7` seul, `alt`, tensions).
        if ext == "7" or alt or (not ext and tens):
            quality, rel = "dom", {0, 4, 7, 10}
        else:
            quality, rel = "maj", {0, 4, 7}
            if ext == "j7":
                rel.add(11)
            elif ext in ("6", "69"):
                rel.add(9)
    if ext == "69":
        rel.add(2)
    if alt:
        rel |= {0, 4, 10, 1, 3, 6, 8}
        rel -= {7}
    for number, accidental in tens:
        rel.add(_TENSION[(number, accidental)])
    return _build(text, root, bass, quality, rel, alt=alt)


# Suffixe d'une qualité du moteur : tête, pile (7/9/11/13/6/6/9), suspension, altérations.
_ENGINE = re.compile(
    r"^(?P<head>mMaj|maj|m|dim|aug|\+)?"
    r"(?P<stack>13|11|9|7|6/9|6)?"
    r"(?P<sus>sus[24])?"
    r"(?P<alts>(?:[b#](?:5|9|11|13))*)$"
)
_ALT_TOKEN = re.compile(r"([b#])(5|9|11|13)")


def from_engine(root_pc: int, bass_pc: int, quality: str | None, is_minor: bool = False) -> Chord:
    """Accord publié par le moteur : `root_pc`, `bass_pc`, `quality` (suffixe lu par
    `Chord::from_name`, `None` ou `""` = triade) et `is_minor` (triade sans qualité typée)."""
    suffix = (quality or "").strip()
    root, bass = root_pc % 12, bass_pc % 12
    symbol = f"{root}{suffix}" + (f"/{bass}" if bass != root else "")
    if suffix in ("", "maj"):
        # Triade sans qualité typée : majeure ou mineure selon `is_minor`.
        return _build(symbol, root, bass, "min" if is_minor else "maj",
                      {0, 3, 7} if is_minor else {0, 4, 7})
    if suffix == "7alt":
        return _build(symbol, root, bass, "dom", {0, 4, 10, 1, 3, 6, 8}, alt=True)
    special = {"sus": {0, 5, 7}, "sus4": {0, 5, 7}, "sus2": {0, 2, 7}}
    if suffix in special:
        return _build(symbol, root, bass, "sus", special[suffix])
    if suffix in ("add2", "add9"):
        return _build(symbol, root, bass, "maj", {0, 2, 4, 7})
    if suffix == "m(add9)":
        return _build(symbol, root, bass, "min", {0, 2, 3, 7})
    if suffix == "m(b5)":
        return _build(symbol, root, bass, "dim", {0, 3, 6})
    match = _ENGINE.match(suffix)
    if match is None:
        raise ChordParseError(f"qualité du moteur non analysée : {quality!r}")
    head, stack, sus = match["head"] or "", match["stack"] or "", match["sus"] or ""
    alts = _ALT_TOKEN.findall(match["alts"])
    natural = {"7": {10}, "9": {10, 2}, "11": {10, 2, 5}, "13": {10, 2, 9}}
    major_seventh = {"7": {11}, "9": {11, 2}, "11": {11, 2, 5}, "13": {11, 2, 9}}

    if head == "dim":
        name, rel = "dim", ({0, 3, 6, 9} if stack == "7" else {0, 3, 6})
    elif head in ("aug", "+"):
        name, rel = "aug", {0, 4, 8} | natural.get(stack, set())
    elif head == "mMaj":
        name, rel = "min", {0, 3, 7} | major_seventh.get(stack or "7", {11})
    elif head == "m":
        name, rel = "min", {0, 3, 7}
        if stack == "6":
            rel.add(9)
        elif stack == "6/9":
            rel |= {9, 2}
        else:
            rel |= natural.get(stack, set())
    elif head == "maj":
        name, rel = "maj", {0, 4, 7} | major_seventh.get(stack or "7", {11})
    elif stack in natural:
        name, rel = "dom", {0, 4, 7} | natural[stack]
    elif stack == "6":
        name, rel = "maj", {0, 4, 7, 9}
    elif stack == "6/9":
        name, rel = "maj", {0, 4, 7, 9, 2}
    else:
        name, rel = "maj", {0, 4, 7}
    if sus:
        rel -= {3, 4}
        rel.add(2 if sus == "sus2" else 5)
        name = "sus"
    for accidental, number in alts:
        if number == "5":
            rel.discard(7)
            rel.add(6 if accidental == "b" else 8)
        else:
            rel.add(_TENSION[(number, accidental)])
    if name == "min" and 6 in rel and 7 not in rel:
        name = "hdim" if 10 in rel else "dim"
    elif name == "dom" and 8 in rel and 7 not in rel:
        name = "aug"
    return _build(symbol, root, bass, name, rel)
