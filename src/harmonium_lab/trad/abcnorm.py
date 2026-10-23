"""Lecture ABC légère : en-têtes, normalisation et analyse minimale d'un air.

Parse volontairement léger (pas de music21) : il ne vise que `meter`, `key`,
`mode`, `bars` et `incipit`, reste déterministe et traite ~1 500 airs en
quelques secondes. Voix : seule la première voix (`V:`) est analysée.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction

# ── Erreurs ──────────────────────────────────────────────────────────


class AbcError(ValueError):
    """Air inexploitable ; `reason` est un code de rejet stable."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


REJECT_NO_KEY = "sans K:"
REJECT_NO_MELODY = "sans mélodie"
REJECT_PARSE = "parse impossible"

# ── Texte : échappements ABC, repli ASCII ────────────────────────────

_COMBINING = {
    "'": "\u0301",
    "`": "\u0300",
    "^": "\u0302",
    '"': "\u0308",
    "~": "\u0303",
    ",": "\u0327",
    "v": "\u030c",
}
_LIGATURES = {
    "ss": "ß", "oe": "œ", "OE": "Œ", "ae": "æ", "AE": "Æ",
    "aa": "å", "AA": "Å", "o": "ø", "O": "Ø",
}
_ESC_ACCENT = re.compile(r"\\([`'^\"~,v])([A-Za-z])")
_ESC_LIGATURE = re.compile(r"\\(ss|oe|OE|ae|AE|aa|AA|o|O)(?![A-Za-z])")
_ESC_UNICODE = re.compile(r"\\u([0-9a-fA-F]{4})")


def decode_abc_text(text: str) -> str:
    """`Qu\\'ebec` → `Québec` (échappements ABC 2.1), normalisé NFC."""
    text = _ESC_UNICODE.sub(lambda m: chr(int(m.group(1), 16)), text)
    text = _ESC_ACCENT.sub(lambda m: m.group(2) + _COMBINING[m.group(1)], text)
    text = _ESC_LIGATURE.sub(lambda m: _LIGATURES[m.group(1)], text)
    return unicodedata.normalize("NFC", text).strip()


def fold(text: str) -> str:
    """Minuscules sans accents."""
    nfd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfd if not unicodedata.combining(c)).lower()


_ARTICLES = {"le", "la", "les", "l", "un", "une", "the", "a", "an", "du", "de", "des"}


def title_key(title: str) -> str:
    """Titre normalisé pour le dédoublonnage (sans accents, sans article initial)."""
    words = re.findall(r"[a-z0-9]+", fold(title))
    while len(words) > 1 and words[0] in _ARTICLES:
        words.pop(0)
    return " ".join(words)


def slugify(title: str, limit: int = 40) -> str:
    slug = "-".join(re.findall(r"[a-z0-9]+", fold(title)))[:limit].strip("-")
    return slug or "untitled"


# ── Découpe en airs et en-têtes ──────────────────────────────────────

_FIELD = re.compile(r"^([A-Za-z]):\s*(.*)$")


def split_tunes(text: str) -> list[str]:
    """Sépare un fichier ABC en airs (un bloc par ligne `X:`). Le texte avant le premier `X:` est ignoré."""
    tunes: list[list[str]] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if re.match(r"^X:", line):
            tunes.append([])
        if tunes:
            tunes[-1].append(line)
    return ["\n".join(t).strip("\n") for t in tunes]


@dataclass
class Tune:
    """Air ABC séparé en en-têtes (avant `K:`) et corps."""

    headers: list[tuple[str, str]]  # (lettre, valeur), dans l'ordre, K: inclus en dernier
    body: list[str]
    has_key: bool = True

    def first(self, letter: str) -> str | None:
        for k, v in self.headers:
            if k == letter:
                return v
        return None

    def all(self, letter: str) -> list[str]:
        return [v for k, v in self.headers if k == letter]


def parse_tune(block: str) -> Tune:
    """Sépare en-têtes et corps. Sans `K:`, `has_key` est faux (l'appelant rejette) mais les en-têtes restent lisibles."""
    headers: list[tuple[str, str]] = []
    body: list[str] = []
    in_body = False
    for line in block.split("\n"):
        if in_body:
            body.append(line)
            continue
        if line.startswith("%") or not line.strip():
            continue
        m = _FIELD.match(line)
        if not m:
            break  # musique avant tout K: → pas de tonalité
        headers.append((m.group(1), m.group(2).strip()))
        if m.group(1) == "K":
            in_body = True
    return Tune(headers, body, has_key=any(k == "K" for k, _ in headers))


# ── Tonalité, mode, métrique ─────────────────────────────────────────

_MODES = {  # préfixe de 3 lettres → (nom ABC, nom français, décalage de quintes)
    "maj": ("major", "majeur", 0),
    "ion": ("major", "majeur", 0),
    "min": ("minor", "mineur", -3),
    "aeo": ("minor", "mineur", -3),
    "dor": ("dorian", "dorien", -2),
    "mix": ("mixolydian", "mixolydien", -1),
    "lyd": ("lydian", "lydien", 1),
    "phr": ("phrygian", "phrygien", -4),
    "loc": ("locrian", "locrien", -5),
}
_KEY = re.compile(r"^\s*([A-Ga-g])([#b]?)\s*([A-Za-z]*)")
_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F": -1}
_SHARP_ORDER = "FCGDAEB"
_FLAT_ORDER = "BEADGCF"


@dataclass(frozen=True)
class KeyInfo:
    tonic: str  # "D", "F#", "Bb"
    mode: str  # "majeur", "mineur", "dorien", "mixolydien", ...
    signature: dict[str, int]  # lettre → altération (+1 / -1)


def parse_key(value: str) -> KeyInfo:
    raw = value.strip()
    head = raw.split()[0] if raw.split() else ""
    if head.lower() in {"hp", "hp.", "hp:"} or raw.lower().startswith("hp"):
        # Cornemuse écossaise : sol mixolydien ouvert sur la, deux dièses.
        return KeyInfo("A", "mixolydien", {"F": 1, "C": 1})
    m = _KEY.match(raw)
    if not m:
        raise AbcError(REJECT_PARSE, f"K: invalide {value!r}")
    letter, acc, mode_text = m.group(1).upper(), m.group(2), m.group(3).lower()
    if mode_text in {"m"}:
        mode_text = "min"
    mode_key = mode_text[:3] if mode_text else "maj"
    if mode_key not in _MODES:
        raise AbcError(REJECT_PARSE, f"mode inconnu {value!r}")
    _, mode_fr, offset = _MODES[mode_key]
    fifths = _FIFTHS[letter] + (7 if acc == "#" else -7 if acc == "b" else 0) + offset
    sig: dict[str, int] = {}
    if fifths > 0:
        sig = {n: 1 for n in _SHARP_ORDER[: min(fifths, 7)]}
    elif fifths < 0:
        sig = {n: -1 for n in _FLAT_ORDER[: min(-fifths, 7)]}
    return KeyInfo(letter + acc, mode_fr, sig)


_METER_SYMBOLS = {"C": "4/4", "C|": "2/2"}


def parse_meter(value: str | None) -> tuple[str, Fraction] | None:
    """`M:` → (forme normalisée « 6/8 », durée d'une mesure en ronde). None si libre/absent."""
    if value is None:
        return None
    v = value.strip()
    if v in _METER_SYMBOLS:
        v = _METER_SYMBOLS[v]
    m = re.match(r"^\(?([\d+ ]+)\)?/(\d+)$", v)
    if not m:
        return None
    num = sum(int(n) for n in re.findall(r"\d+", m.group(1)))
    den = int(m.group(2))
    if num == 0 or den == 0:
        return None
    return f"{num}/{den}", Fraction(num, den)


def parse_unit(value: str | None, measure: Fraction) -> Fraction:
    if value:
        m = re.match(r"^(\d+)/(\d+)$", value.strip())
        if m and int(m.group(2)) > 0 and int(m.group(1)) > 0:
            return Fraction(int(m.group(1)), int(m.group(2)))
    return Fraction(1, 8) if measure >= Fraction(3, 4) else Fraction(1, 16)


# ── Types ────────────────────────────────────────────────────────────

TYPES = ("reel", "jig", "waltz", "march", "quadrille", "cotillon", "hornpipe")
_TYPE_WORDS = {
    "reel": "reel", "reels": "reel",
    "jig": "jig", "jigs": "jig", "gigue": "jig", "gigues": "jig",
    "waltz": "waltz", "waltzes": "waltz", "valse": "waltz", "valses": "waltz",
    "march": "march", "marche": "march", "marches": "march",
    "quadrille": "quadrille", "quadrilles": "quadrille",
    "cotillon": "cotillon", "cotillion": "cotillon", "cotillons": "cotillon",
    "hornpipe": "hornpipe", "hornpipes": "hornpipe",
}


def type_from_text(text: str | None) -> str | None:
    """Type trouvé dans un `R:` ou un titre ; quadrille/cotillon priment. `slip jig` → None."""
    if not text:
        return None
    words = re.findall(r"[a-z]+", fold(text))
    if "slip" in words or "slide" in words:
        return None
    found = [_TYPE_WORDS[w] for w in words if w in _TYPE_WORDS]
    for special in ("quadrille", "cotillon"):
        if special in found:
            return special
    return found[0] if found else None


# ── Analyse mélodique ────────────────────────────────────────────────

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_TOKEN = re.compile(
    r"""
    (?P<bar>[:\[]*\|[|:\]]*|::+|:\|)(?P<volta>\s*\d[\d,\-]*)?
  | (?P<voltabr>\[\d[\d,\-]*)
  | (?P<tuplet>\((?P<tp>\d)(?::(?P<tq>\d*))?(?::(?P<tr>\d*))?)
  | (?P<chord>\[(?P<chordbody>[^\]\[|]*)\](?P<clen>\d*(?:/\d*)*))
  | (?P<note>(?P<acc>[\^_=]*)(?P<pitch>[A-Ga-g])(?P<oct>[,']*)(?P<len>\d*(?:/\d*)*))
  | (?P<rest>(?P<rk>[zxZX])(?P<rlen>\d*(?:/\d*)*))
  | (?P<broken>[<>]+)
    """,
    re.VERBOSE,
)
_CHORD_NOTE = re.compile(r"([\^_=]*)([A-Ga-g])([,']*)(\d*(?:/\d*)*)")
_STRIP = [
    re.compile(r"\[[A-Za-z]:[^\]]*\]"),  # champs en ligne
    re.compile(r'"[^"]*"'),  # accords / annotations
    re.compile(r"![^!]*!"),  # décorations
    re.compile(r"\+[^+]*\+"),
    re.compile(r"\{[^}]*\}"),  # notes d'ornement
]
_TUPLET_Q = {2: 3, 3: 2, 4: 3, 6: 2, 8: 3}


def _length(spec: str) -> Fraction:
    """`3/2` → 3/2, `/` → 1/2, `//` → 1/4, `` → 1."""
    if not spec:
        return Fraction(1)
    if "/" not in spec:
        return Fraction(int(spec))
    num_s, *dens = spec.split("/")
    num = int(num_s) if num_s else 1
    value = Fraction(num)
    for d in dens:
        value /= int(d) if d else 2
    return value


def _first_voice_lines(body: list[str]) -> list[str]:
    out: list[str] = []
    first_voice: str | None = None
    current: str | None = None
    for raw in body:
        line = raw.split("%", 1)[0]
        if not line.strip():
            continue
        v = re.match(r"^\s*V:\s*(\S+)", line)
        if v:
            current = v.group(1)
            first_voice = first_voice or current
            continue
        if re.match(r"^[A-Za-z]:", line):  # w:, W:, P:, Q:, M: … : pas de musique
            continue
        # Une ligne peut alterner [V:1] et [V:2] ; même sélection que V:.
        for chunk in re.split(r"(\[V:[^\]]*\])", line):
            inline = re.fullmatch(r"\[V:\s*(\S+).*?\]", chunk)
            if inline:
                current = inline.group(1)
                first_voice = first_voice or current
            elif current is None or current == first_voice:
                out.append(chunk.rstrip().removesuffix("\\"))
    return out


@dataclass
class Analysis:
    meter: str
    unit: Fraction
    key: str
    mode: str
    bars: int
    incipit: list[int]
    notes: int
    inferred: list[str] = field(default_factory=list)


def analyse(tune: Tune, default_meter: str | None = None) -> Analysis:
    key = parse_key(tune.first("K") or "")
    meter_raw = tune.first("M")
    parsed = parse_meter(meter_raw)
    inferred: list[str] = []
    if parsed is None:
        if default_meter is None:
            raise AbcError(REJECT_PARSE, f"M: absent ou libre {meter_raw!r}")
        parsed = parse_meter(default_meter)
        assert parsed is not None
        inferred.append("M")
    meter, measure_len = parsed
    unit = parse_unit(tune.first("L"), measure_len)

    text = " ".join(_first_voice_lines(tune.body))
    for rx in _STRIP:
        text = rx.sub(" ", text)

    # Mesure courante : événements [durée, hauteur MIDI | None pour un silence].
    events: list[list] = []
    segments: list[tuple[Fraction, list[int]]] = []
    accidentals: dict[tuple[str, str], int] = {}
    tuplet_left, tuplet_ratio = 0, Fraction(1)
    next_factor = Fraction(1)
    note_count = 0

    def pitch_of(acc: str, letter: str, octv: str) -> int:
        base = _PC[letter.upper()] + (60 if letter.isupper() else 72)
        base += 12 * octv.count("'") - 12 * octv.count(",")
        slot = (letter, octv)
        if acc:
            shift = 0 if "=" in acc else acc.count("^") - acc.count("_")
            accidentals[slot] = shift
        else:
            shift = accidentals.get(slot, key.signature.get(letter.upper(), 0))
        return base + shift

    def flush() -> None:
        nonlocal events, accidentals, next_factor
        dur = sum((e[0] for e in events), Fraction(0))
        if dur > 0:
            segments.append((dur, [e[1] for e in events if e[1] is not None]))
        events, accidentals, next_factor = [], {}, Fraction(1)

    def push(base: Fraction, pitch: int | None) -> None:
        nonlocal tuplet_left, next_factor
        d = base * next_factor
        next_factor = Fraction(1)
        if tuplet_left > 0:
            d *= tuplet_ratio
            tuplet_left -= 1
        events.append([d, pitch])

    for m in _TOKEN.finditer(text):
        if m.group("bar") is not None or m.group("voltabr") is not None:
            flush()
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
                note_count += 1
        elif m.group("note") is not None:
            push(_length(m.group("len")) * unit,
                 pitch_of(m.group("acc"), m.group("pitch"), m.group("oct")))
            note_count += 1
        elif m.group("rest") is not None:
            n = _length(m.group("rlen"))
            push(n * measure_len if m.group("rk") in "ZX" else n * unit, None)
        elif m.group("broken") is not None:
            sym = m.group("broken")
            small = Fraction(1, 2 ** len(sym))
            long_, short = 2 - small, small
            if events:
                events[-1][0] *= long_ if sym[0] == ">" else short
                next_factor = short if sym[0] == ">" else long_
    flush()

    if note_count == 0:
        raise AbcError(REJECT_NO_MELODY)

    # Anacrouse : première mesure incomplète, ni comptée ni dans l'incipit.
    if segments and segments[0][0] < measure_len:
        segments = segments[1:]
    incipit: list[int] = []
    for _, pitches in segments[:2]:
        incipit.extend(pitches)
    return Analysis(meter, unit, key.tonic, key.mode, len(segments), incipit, note_count, inferred)


def intervals(incipit: list[int]) -> tuple[int, ...]:
    """Incipit transposé : suite d'intervalles en demi-tons."""
    return tuple(b - a for a, b in zip(incipit, incipit[1:]))
