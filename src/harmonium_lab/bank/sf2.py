"""Écrivain et lecteur SoundFont 2.01 multi-presets et multi-banques (stdlib + numpy).

Prend en charge :
- plusieurs presets répartis sur plusieurs banques (ex. banque 0 GM mélodique
  et banque 128 kit de batterie GM) ;
- plusieurs zones de tessiture (`keyRange`) et de vélocité (`velRange`) par preset ;
- échantillons bouclés (`sampleModes = 1` ou `3`) avec recopie des 8 points
  post-boucle (§7.10 SF2.01) et 46 zéros de garde ;
- échantillons percussifs one-shot (`sampleModes = 0`) avec `exclusiveClass`
  optionnel (ex. charleston fermé coupant le charleston ouvert).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

import numpy as np

from harmonium_lab.bank import SAMPLE_RATE

# ── Générateurs SF2 2.01 (§8.1.2) ────────────────────────────────
GEN_ATTACK_VOL_ENV = 34
GEN_DECAY_VOL_ENV = 36
GEN_SUSTAIN_VOL_ENV = 37
GEN_RELEASE_VOL_ENV = 38
GEN_INSTRUMENT = 41
GEN_KEY_RANGE = 43
GEN_VEL_RANGE = 44
GEN_ATTENUATION = 48
GEN_SAMPLE_ID = 53
GEN_SAMPLE_MODES = 54
GEN_EXCLUSIVE_CLASS = 57
GEN_OVERRIDING_ROOT_KEY = 58

SAMPLE_MODE_NO_LOOP = 0
SAMPLE_MODE_CONTINUOUS_LOOP = 1
SAMPLE_MODE_LOOP_UNTIL_RELEASE = 3
SAMPLE_TYPE_MONO = 1

#: Échantillons de garde exigés après chaque fin d'échantillon (§7.2).
GUARD_SAMPLES = 46
#: Points de sécurité copiés après `loop_end` pour l'interpolation (§7.10).
POST_LOOP_PAD = 8


def seconds_to_timecents(seconds: float) -> int:
    """Convertit une durée (s) en timecents SF2 (borné à [-12000, 8000])."""
    clamped = max(float(seconds), 0.001)
    tc = round(1200.0 * math.log2(clamped))
    return max(-12000, min(8000, tc))


@dataclass
class BankZone:
    """Une zone d'instrument associée à un échantillon mono 16 bits."""

    sample_name: str
    audio: np.ndarray  # float [-1, 1] ou int16 1D
    root_key: int
    key_lo: int
    key_hi: int
    vel_lo: int = 0
    vel_hi: int = 127
    loop: bool = False
    loop_start: int = 0
    loop_end: int = 0
    sample_mode: int | None = None
    attack_s: float = 0.002
    decay_s: float | None = None
    sustain_cb: int | None = None
    release_s: float = 0.25
    attenuation_cb: int = 0
    exclusive_class: int = 0
    sample_rate: int = SAMPLE_RATE


@dataclass
class BankPreset:
    """Un preset SF2 identifié par `(bank, program)` et ses zones."""

    name: str
    bank: int
    program: int
    zones: list[BankZone] = field(default_factory=list)


@dataclass
class SoundFontSpec:
    """Spécification complète d'une banque SoundFont 2.01."""

    name: str
    presets: list[BankPreset]
    copyright: str = "CC0-1.0 / harmonium_lab"
    comment: str = "Built by harmonium_lab.bank"


def _chunk(chunk_id: bytes, payload: bytes) -> bytes:
    out = bytearray(chunk_id)
    out += struct.pack("<I", len(payload))
    out += payload
    if len(payload) % 2 == 1:
        out.append(0)
    return bytes(out)


def _string_chunk(chunk_id: bytes, text: str) -> bytes:
    raw = text.encode("ascii", "replace") + b"\x00"
    if len(raw) % 2 == 1:
        raw += b"\x00"
    return _chunk(chunk_id, raw)


def _cstr(text: str | bytes) -> bytes:
    raw = text.encode("ascii", "replace") if isinstance(text, str) else text
    return raw[:20].ljust(20, b"\x00")


def _range(lo: int, hi: int) -> int:
    if not (0 <= lo <= hi <= 127):
        raise ValueError(f"plage MIDI invalide : [{lo}, {hi}]")
    return lo | (hi << 8)


def _to_int16_pcm(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError("échantillon vide ou non mono")
    if not np.all(np.isfinite(arr)):
        raise ValueError("échantillon contenant NaN ou Inf")
    if np.issubdtype(arr.dtype, np.integer):
        pcm = np.clip(arr, -32768, 32767).astype("<i2")
    else:
        pcm = np.rint(np.clip(arr, -1.0, 1.0) * 32767.0).astype("<i2")
    if not np.any(pcm):
        raise ValueError("échantillon silencieux")
    return pcm


def _validate_preset_zones(preset: BankPreset) -> None:
    if not (0 <= preset.program <= 127):
        raise ValueError(f"preset {preset.name} : programme {preset.program} hors 0..127")
    if not (0 <= preset.bank <= 128):
        raise ValueError(f"preset {preset.name} : banque {preset.bank} hors 0..128")
    if not preset.zones:
        raise ValueError(f"preset {preset.name} ({preset.bank}/{preset.program}) : aucune zone")
    for idx, z in enumerate(preset.zones):
        if not (0 <= z.key_lo <= z.key_hi <= 127):
            raise ValueError(f"{preset.name} zone {idx} : keyRange [{z.key_lo}, {z.key_hi}] invalide")
        if not (0 <= z.vel_lo <= z.vel_hi <= 127):
            raise ValueError(f"{preset.name} zone {idx} : velRange [{z.vel_lo}, {z.vel_hi}] invalide")
        if not (0 <= z.root_key <= 127):
            raise ValueError(f"{preset.name} zone {idx} : root_key {z.root_key} invalide")
        n = len(z.audio)
        if z.loop:
            if not (POST_LOOP_PAD <= z.loop_start < z.loop_end <= n - POST_LOOP_PAD):
                raise ValueError(
                    f"{preset.name} zone {idx} ({z.sample_name}) : "
                    f"boucle [{z.loop_start}, {z.loop_end}] invalide pour {n} points"
                )
        for prev in preset.zones[:idx]:
            overlap_key = max(z.key_lo, prev.key_lo) <= min(z.key_hi, prev.key_hi)
            overlap_vel = max(z.vel_lo, prev.vel_lo) <= min(z.vel_hi, prev.vel_hi)
            if overlap_key and overlap_vel:
                raise ValueError(
                    f"{preset.name} ({preset.bank}/{preset.program}) : "
                    f"zones qui se recouvrent ({prev.sample_name} et {z.sample_name})"
                )


def build_multi_sf2(spec: SoundFontSpec) -> bytes:
    """Assemble une SoundFont 2.01 complète à partir de `spec`."""
    if not spec.presets:
        raise ValueError("banque vide : aucun preset")

    sorted_presets = sorted(spec.presets, key=lambda p: (p.bank, p.program))
    seen_pairs: set[tuple[int, int]] = set()
    for p in sorted_presets:
        pair = (p.bank, p.program)
        if pair in seen_pairs:
            raise ValueError(f"preset en double pour (bank={p.bank}, program={p.program})")
        seen_pairs.add(pair)
        _validate_preset_zones(p)

    # ── Déduplication des échantillons dans smpl / shdr ──────────
    sample_data = bytearray()
    shdr = bytearray()
    sample_index_by_key: dict[tuple, int] = {}

    def register_sample(zone: BankZone) -> int:
        pcm = _to_int16_pcm(zone.audio)
        if zone.loop:
            pcm = pcm.copy()
            # Recopie les 8 premiers points de la boucle juste après loop_end (§7.10)
            pcm[zone.loop_end : zone.loop_end + POST_LOOP_PAD] = pcm[
                zone.loop_start : zone.loop_start + POST_LOOP_PAD
            ]
        raw_bytes = pcm.tobytes()
        cache_key = (
            zone.sample_name,
            zone.root_key,
            zone.sample_rate,
            zone.loop,
            zone.loop_start,
            zone.loop_end,
            raw_bytes,
        )
        if cache_key in sample_index_by_key:
            return sample_index_by_key[cache_key]

        idx = len(sample_index_by_key)
        start = len(sample_data) // 2
        sample_data.extend(raw_bytes)
        end = len(sample_data) // 2
        sample_data.extend(b"\x00" * (GUARD_SAMPLES * 2))

        if zone.loop:
            loop_start = start + zone.loop_start
            loop_end = start + zone.loop_end
        else:
            loop_start = start
            loop_end = end

        shdr.extend(
            struct.pack(
                "<20sIIIIIBbHH",
                _cstr(zone.sample_name),
                start,
                end,
                loop_start,
                loop_end,
                zone.sample_rate,
                zone.root_key,
                0,
                0,
                SAMPLE_TYPE_MONO,
            )
        )
        sample_index_by_key[cache_key] = idx
        return idx

    # ── Construction phdr / pbag / pgen / inst / ibag / igen ─────
    phdr = bytearray()
    pbag = bytearray()
    pgen = bytearray()
    inst = bytearray()
    ibag = bytearray()
    igen = bytearray()

    ibag_count = 0
    igen_count = 0

    for preset_idx, preset in enumerate(sorted_presets):
        phdr.extend(
            struct.pack(
                "<20sHHHIII",
                _cstr(preset.name),
                preset.program,
                preset.bank,
                preset_idx,
                0,
                0,
                0,
            )
        )
        pbag.extend(struct.pack("<HH", preset_idx, 0))
        pgen.extend(struct.pack("<Hh", GEN_INSTRUMENT, preset_idx))
        inst.extend(struct.pack("<20sH", _cstr(preset.name), ibag_count))

        for zone in preset.zones:
            sample_idx = register_sample(zone)
            mode = (
                zone.sample_mode
                if zone.sample_mode is not None
                else (SAMPLE_MODE_CONTINUOUS_LOOP if zone.loop else SAMPLE_MODE_NO_LOOP)
            )
            gens: list[tuple[int, int]] = [
                (GEN_KEY_RANGE, _range(zone.key_lo, zone.key_hi)),
                (GEN_VEL_RANGE, _range(zone.vel_lo, zone.vel_hi)),
                (GEN_ATTACK_VOL_ENV, seconds_to_timecents(zone.attack_s)),
            ]
            if zone.decay_s is not None:
                gens.append((GEN_DECAY_VOL_ENV, seconds_to_timecents(zone.decay_s)))
            if zone.sustain_cb is not None:
                gens.append((GEN_SUSTAIN_VOL_ENV, max(0, min(1440, int(zone.sustain_cb)))))
            gens.extend(
                [
                    (GEN_RELEASE_VOL_ENV, seconds_to_timecents(zone.release_s)),
                    (GEN_ATTENUATION, max(0, min(1440, int(zone.attenuation_cb)))),
                    (GEN_SAMPLE_MODES, mode),
                ]
            )
            if zone.exclusive_class > 0:
                gens.append((GEN_EXCLUSIVE_CLASS, int(zone.exclusive_class)))
            gens.extend(
                [
                    (GEN_OVERRIDING_ROOT_KEY, zone.root_key),
                    (GEN_SAMPLE_ID, sample_idx),
                ]
            )

            ibag.extend(struct.pack("<HH", igen_count, 0))
            for oper, amount in gens:
                igen.extend(struct.pack("<Hh", oper, amount))
            igen_count += len(gens)
            ibag_count += 1

    # Enregistrements terminaux obligatoires SF2 2.01
    n_presets = len(sorted_presets)
    phdr.extend(struct.pack("<20sHHHIII", _cstr(b"EOP"), 0, 0, n_presets, 0, 0, 0))
    pbag.extend(struct.pack("<HH", n_presets, 0))
    pmod = struct.pack("<HHhHH", 0, 0, 0, 0, 0)
    pgen.extend(struct.pack("<Hh", 0, 0))
    inst.extend(struct.pack("<20sH", _cstr(b"EOI"), ibag_count))
    ibag.extend(struct.pack("<HH", igen_count, 0))
    imod = struct.pack("<HHhHH", 0, 0, 0, 0, 0)
    igen.extend(struct.pack("<Hh", 0, 0))
    shdr.extend(struct.pack("<20sIIIIIBbHH", _cstr(b"EOS"), 0, 0, 0, 0, 0, 0, 0, 0, 0))

    info_body = b"".join(
        [
            _chunk(b"ifil", struct.pack("<HH", 2, 1)),
            _string_chunk(b"isng", "EMU8000"),
            _string_chunk(b"INAM", spec.name),
            _string_chunk(b"ICOP", spec.copyright),
            _string_chunk(b"ICMT", spec.comment),
        ]
    )
    info_chunk = _chunk(b"LIST", b"INFO" + info_body)
    sdta_chunk = _chunk(b"LIST", b"sdta" + _chunk(b"smpl", bytes(sample_data)))
    pdta_body = b"".join(
        [
            _chunk(b"phdr", bytes(phdr)),
            _chunk(b"pbag", bytes(pbag)),
            _chunk(b"pmod", pmod),
            _chunk(b"pgen", bytes(pgen)),
            _chunk(b"inst", bytes(inst)),
            _chunk(b"ibag", bytes(ibag)),
            _chunk(b"imod", imod),
            _chunk(b"igen", bytes(igen)),
            _chunk(b"shdr", bytes(shdr)),
        ]
    )
    pdta_chunk = _chunk(b"LIST", b"pdta" + pdta_body)
    riff_body = info_chunk + sdta_chunk + pdta_chunk
    return b"RIFF" + struct.pack("<I", 4 + len(riff_body)) + b"sfbk" + riff_body


def inspect_sf2(data: bytes) -> dict:
    """Inspecte les tables `phdr` et `shdr` d'un binaire SF2 2.01."""
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"sfbk":
        raise ValueError("en-tête RIFF/sfbk invalide")
    pos = 12
    presets: list[dict] = []
    samples: list[dict] = []
    while pos + 8 <= len(data):
        cid = data[pos : pos + 4]
        size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        payload = data[pos + 8 : pos + 8 + size]
        if cid == b"LIST" and payload[:4] == b"pdta":
            sub = 4
            while sub + 8 <= len(payload):
                scid = payload[sub : sub + 4]
                ssize = struct.unpack("<I", payload[sub + 4 : sub + 8])[0]
                spayload = payload[sub + 8 : sub + 8 + ssize]
                if scid == b"phdr":
                    for off in range(0, len(spayload) - 38, 38):
                        raw_name, prog, bank, bag, _, _, _ = struct.unpack(
                            "<20sHHHIII", spayload[off : off + 38]
                        )
                        name = raw_name.split(b"\x00", 1)[0].decode("ascii", "replace")
                        presets.append({"name": name, "bank": bank, "program": prog, "bag": bag})
                elif scid == b"shdr":
                    for off in range(0, len(spayload) - 46, 46):
                        raw_name, s, e, ls, le, sr, pitch, corr, link, stype = struct.unpack(
                            "<20sIIIIIBbHH", spayload[off : off + 46]
                        )
                        name = raw_name.split(b"\x00", 1)[0].decode("ascii", "replace")
                        samples.append(
                            {
                                "name": name,
                                "start": s,
                                "end": e,
                                "loop_start": ls,
                                "loop_end": le,
                                "sample_rate": sr,
                                "root_key": pitch,
                                "type": stype,
                            }
                        )
                sub += 8 + ssize + (ssize % 2)
        pos += 8 + size + (size % 2)
    return {"presets": presets, "samples": samples}
