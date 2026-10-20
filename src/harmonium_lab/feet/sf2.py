"""Écrivain SoundFont 2.01 minimal, sans dépendance binaire (stdlib uniquement).

Produit `harmonium_trad.sf2` : RIFF `sfbk` avec `INFO`, `sdta/smpl`
(16 bits mono 44,1 kHz) et `pdta` (`phdr/pbag/pmod/pgen/inst/ibag/
imod/igen/shdr`, enregistrements terminaux EOP/EOI/EOS inclus).

Un preset banque 0 programme 0 « Podorythmie » : une zone d'instrument
par variante, `keyRange` sur une touche (36 = talon, 37 = pointe),
`velRange` en couches (les variantes d'un rôle se partagent 0–127),
`sampleModes` sans boucle, enveloppe courte.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from harmonium_lab.feet import SAMPLE_RATE

# ── Générateurs SF2 ──────────────────────────────────────────────
GEN_INSTRUMENT = 41
GEN_KEY_RANGE = 43
GEN_VEL_RANGE = 44
GEN_ATTENUATION = 48
GEN_SAMPLE_ID = 53
GEN_SAMPLE_MODES = 54
GEN_OVERRIDING_ROOT_KEY = 58
GEN_ATTACK_VOL_ENV = 34
GEN_RELEASE_VOL_ENV = 38

SAMPLE_MODE_NO_LOOP = 0
SAMPLE_TYPE_MONO = 1

#: Échantillons de garde exigés après chaque fin d'échantillon.
GUARD_SAMPLES = 46


@dataclass
class VoiceSample:
    """Un échantillon prêt à embarquer : PCM 16 bits mono 44,1 kHz."""

    name: str  # ≤ 20 caractères (tronqué au besoin)
    pcm: bytes  # int16 little-endian mono 44100 Hz
    key: int  # touche jouée (36 talon, 37 pointe)
    vel_lo: int  # borne basse de la couche de vélocité
    vel_hi: int  # borne haute


@dataclass
class FeetBank:
    """Les variantes par rôle, dans l'ordre de lecture (vélocité croissante)."""

    heel: list[VoiceSample] = field(default_factory=list)
    toe: list[VoiceSample] = field(default_factory=list)

    def zones(self) -> list[VoiceSample]:
        return list(self.heel) + list(self.toe)


# ── Bas niveau RIFF ──────────────────────────────────────────────

def _chunk(chunk_id: bytes, payload: bytes) -> bytes:
    """Chunk RIFF : id (4) + taille (LE32, sans le pad) + données + pad pair."""
    assert len(chunk_id) == 4
    out = bytearray(chunk_id + struct.pack("<I", len(payload)) + payload)
    if len(payload) % 2:
        out += b"\x00"
    return bytes(out)


def _string_chunk(chunk_id: bytes, text: str) -> bytes:
    """Chaîne INFO : terminée par nul, taille paire (exigé par fluidsynth)."""
    payload = text.encode("ascii", "replace") + b"\x00"
    if len(payload) % 2:
        payload += b"\x00"
    return _chunk(chunk_id, payload)


def _cstr(raw: bytes) -> bytes:
    """Nom SF2 : 20 octets, tronqué si besoin, complété de zéros."""
    return raw[:20].ljust(20, b"\x00")


def _range(lo: int, hi: int) -> int:
    """Plage keyRange/velRange : octet bas = min, octet haut = max."""
    assert 0 <= lo <= hi <= 127
    return lo | (hi << 8)


# ── Assemblage ───────────────────────────────────────────────────

def _info_chunk() -> bytes:
    body = b"".join([
        _chunk(b"ifil", struct.pack("<HH", 2, 1)),  # SoundFont 2.01
        _string_chunk(b"isng", "EMU8000"),
        _string_chunk(b"INAM", "harmonium_trad pieds"),
        _string_chunk(b"ICRD", "2026-10-20"),
        _string_chunk(b"IENG", "harmonium_lab"),
        _string_chunk(b"IPRD", "Podorythmie"),
        _string_chunk(b"ICOP", "Echantillons : voir samples/feet/manifest.jsonl (CC0)"),
        _string_chunk(b"ISFT", "harmonium_lab feet sf2"),
    ])
    return _chunk(b"LIST", b"INFO" + body)


def _sdta_chunk(samples: list[VoiceSample]) -> tuple[bytes, list[tuple[int, int]]]:
    """Données `smpl` concaténées (+ 46 zéros de garde par échantillon).

    Retourne le chunk et les (début, fin) en points 16 bits de chaque échantillon.
    """
    data = bytearray()
    spans: list[tuple[int, int]] = []
    for s in samples:
        assert len(s.pcm) % 2 == 0, f"{s.name} : PCM non aligné 16 bits"
        start = len(data) // 2
        data += s.pcm
        end = len(data) // 2
        spans.append((start, end))
        data += b"\x00" * (GUARD_SAMPLES * 2)
    return _chunk(b"LIST", b"sdta" + _chunk(b"smpl", bytes(data))), spans


def _pdta_chunk(bank: FeetBank, spans: list[tuple[int, int]]) -> bytes:
    zones = bank.zones()
    n_zones = len(zones)
    if n_zones == 0:
        raise ValueError("banque vide : aucun échantillon talon/pointe")

    # ── phdr : 1 preset + EOP (EOP.wPresetBagNdx = nb de zones : ──
    # les zones d'un preset vont jusqu'à l'index du preset suivant, ──
    # sans terminal intermédiaire — cf. GeneralUser-GS) ──
    phdr = struct.pack("<20sHHHIII", _cstr(b"Podorythmie"), 0, 0, 0, 0, 0, 0)
    phdr += struct.pack("<20sHHHIII", b"\x00" * 20, 0, 0, 1, 0, 0, 0)  # EOP

    # ── pbag : zone + terminal global (nb = EOP.wPresetBagNdx + 1) ──
    pbag = struct.pack("<HH", 0, 0) + struct.pack("<HH", 1, 0)

    # ── pmod : terminal seul ──
    pmod = struct.pack("<HHhHH", 0, 0, 0, 0, 0)

    # ── pgen : instrument 0 + terminal ──
    pgen = struct.pack("<Hh", GEN_INSTRUMENT, 0)
    pgen += struct.pack("<Hh", 0, 0)

    # ── inst : 1 instrument + EOI (EOI.wInstBagNdx = nb de zones, ──
    # le terminal global suit : nb enregistrements = EOI + 1) ──
    inst = struct.pack("<20sH", _cstr(b"Pieds"), 0)
    inst += struct.pack("<20sH", b"\x00" * 20, n_zones)  # EOI

    # ── ibag/igen : une zone par variante + terminal ──
    ibag = bytearray()
    igen = bytearray()
    gen_index = 0
    for idx, zone in enumerate(zones):
        ibag += struct.pack("<HH", gen_index, 0)
        gens = [
            # keyRange/velRange d'abord, sampleID en dernier (§8.1.2)
            (GEN_KEY_RANGE, _range(zone.key, zone.key)),
            (GEN_VEL_RANGE, _range(zone.vel_lo, zone.vel_hi)),
            (GEN_SAMPLE_MODES, SAMPLE_MODE_NO_LOOP),
            (GEN_OVERRIDING_ROOT_KEY, zone.key),
            (GEN_ATTACK_VOL_ENV, -12000),  # ~1 ms
            (GEN_RELEASE_VOL_ENV, -800),  # ~0,6 s de queue
            (GEN_SAMPLE_ID, idx),
        ]
        for oper, amount in gens:
            igen += struct.pack("<Hh", oper, amount)
        gen_index += len(gens)
    ibag += struct.pack("<HH", gen_index, 0)  # terminal global (igen/imod terminaux)
    igen += struct.pack("<Hh", 0, 0)  # igen terminal
    imod = struct.pack("<HHhHH", 0, 0, 0, 0, 0)  # imod terminal seul

    # ── shdr : un enregistrement par échantillon + EOS ──
    shdr = bytearray()
    for zone, (start, end) in zip(zones, spans):
        shdr += struct.pack(
            "<20sIIIIIBbHH",
            _cstr(zone.name.encode("ascii", "replace")),
            start, end, start, end,
            SAMPLE_RATE, zone.key, 0, 0, SAMPLE_TYPE_MONO,
        )
    shdr += struct.pack("<20sIIIIIBbHH", b"\x00" * 20, 0, 0, 0, 0, 0, 0, 0, 0, 0)  # EOS

    body = b"".join([
        _chunk(b"phdr", phdr),
        _chunk(b"pbag", bytes(pbag)),
        _chunk(b"pmod", pmod),
        _chunk(b"pgen", pgen),
        _chunk(b"inst", inst),
        _chunk(b"ibag", bytes(ibag)),
        _chunk(b"imod", imod),
        _chunk(b"igen", bytes(igen)),
        _chunk(b"shdr", bytes(shdr)),
    ])
    return _chunk(b"LIST", b"pdta" + body)


def build_sf2(bank: FeetBank) -> bytes:
    """Assemble la SoundFont complète (prête à écrire sur disque)."""
    zones = bank.zones()
    if len({(z.key, z.vel_lo, z.vel_hi) for z in zones}) != len(zones):
        raise ValueError("recouvrement keyRange/velRange : deux zones identiques")
    sdta, spans = _sdta_chunk(zones)
    body = _info_chunk() + sdta + _pdta_chunk(bank, spans)
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"sfbk" + body


def velocity_layers(n: int) -> list[tuple[int, int]]:
    """Partage 0–127 en `n` couches contiguës (variantes douces → fortes)."""
    if n < 1:
        raise ValueError("il faut au moins une variante")
    step, layers, lo = 128 // n, [], 0
    for i in range(n):
        hi = 127 if i == n - 1 else lo + step - 1
        layers.append((lo, hi))
        lo = hi + 1
    return layers
