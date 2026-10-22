"""Rendu à armes égales du corpus trad québécois (specs/001-trad-dataset D4).

Chaîne : ABC du corpus → MIDI (`abc2midi`) → WAV (`fluidsynth`,
`GeneralUser-GS.sf2`, la même banque que le moteur) ; MusicXML via
`music21` en option. Le fichier ABC source n'est jamais modifié : les
directives `%%MIDI` et le tempo sont injectés dans une copie temporaire.

Réglages « armes égales », identiques au moteur :
- mélodie : programme GM 40 (violon) ; swing nul (l'ABC est noté droit) ;
- accords de l'ABC (`"G"`) : `gchord`, programme 24 (guitare), basse 32 ;
- pieds : talon 36 sur chaque temps, pointe 37 sur les contretemps
  (motifs `%%MIDI drum` par métrique, voir `feet_pattern`) ;
- tempo par type : reel 230 à la noire, gigue 115 à la noire pointée,
  valse 145 à la noire, marche 110 à la noire (quadrille/cotillon : 115
  à la noire pointée, comme la gigue : même 6/8) ;
- reprises jouées (comportement par défaut d'`abc2midi`, sections AABB).

Normalisation WAV : `fluidsynth` + GeneralUser-GS sort ces MIDIs autour
de 0.10 de pic ; les démos du moteur (`harmonium/demos/*.wav`) pichent
à 0.125–0.177. Chaque WAV est donc ramené à `PEAK_TARGET = 0.125`
(≈ −18 dBFS) par simple gain linéaire (stdlib uniquement), ce qui garde
les rendus comparables en écoute aveugle sans écrêtage.

Reproductibilité : même ABC ⇒ même MIDI (octet près, vérifié en test) ;
le WAV suit (rendu `fluidsynth` déterministe + gain pur). `render_log.jsonl`
ne contient aucune date, seulement le résultat par air.
"""
from __future__ import annotations

import array
import argparse
import json
import random
import re
import shutil
import struct
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

# ── Réglages ───────────────────────────────────────────────────────────

PROG_MELODY = 40  # violon
PROG_CHORD = 24  # guitare
PROG_BASS = 32  # basse acoustique
DRUM_HEEL = 36  # talon (`%%MIDI drum`, avant réassignation)
DRUM_TOE = 37  # pointe (`%%MIDI drum`, avant réassignation)
VEL_HEEL = 100
VEL_TOE = 70

#: Pieds (chantier SK1) : les notes 36/37 du canal percussion sont
#: réassignées sur ce canal mélodique, preset banque 0 programme 0 de
#: `harmonium_trad.sf2` (sélection : CC0=0, CC32=0 + program change 0).
#: `fluidsynth` charge GeneralUser-GS puis harmonium_trad.sf2 : la
#: seconde banque prime pour banque 0 / programme 0 (le piano GM, non
#: utilisé ici, est masqué sur ce seul couple).
FEET_CHANNEL = 10  # canal 11
FEET_BANK = 0
FEET_PROG = 0
#: Niveau des pieds : gain appliqué aux vélocités (mesuré : RMS pieds
#: ≤ RMS violon − 8 dB sur `reel_complet`, voir samples/feet/review.md).
FEET_VEL_SCALE = 0.55
#: Humanisation déterministe des vélocités (alterne les couches SF2).
FEET_HUMANIZE = 12
FEET_SEED = 20261019
FEET_NOTES = (DRUM_HEEL, DRUM_TOE)
DRUM_CHANNEL = 9  # canal percussion (0-based) où `abc2midi` met les pieds
TEMPO_Q = {
    "reel": "1/4=230",
    "jig": "3/8=115",
    "waltz": "1/4=145",
    "march": "1/4=110",
    "quadrille": "3/8=115",
    "cotillon": "3/8=115",
    "hornpipe": "1/4=150",
}

DEFAULT_METER = {
    "reel": (4, 4), "jig": (6, 8), "waltz": (3, 4), "march": (2, 4),
    "quadrille": (6, 8), "cotillon": (6, 8),
    "hornpipe": (4, 4),
}

def default_soundfont() -> Path:
    """Banque du moteur : `../harmonium/assets/GeneralUser-GS.sf2`."""
    return repo_root().parent / "harmonium" / "assets" / "GeneralUser-GS.sf2"

#: Pic cible des WAV : calé sur les démos du moteur
#: (`reel_seed1.wav` 0.126, `reel_seed2.wav` 0.125, `legacy_seed1.wav` 0.177).
PEAK_TARGET = 0.125
SAMPLE_SEED = 20261019

ABC2MIDI_HINT = "abc2midi introuvable : installe avec `brew install abcmidi`"
FLUIDSYNTH_HINT = "fluidsynth introuvable : installe avec `brew install fluidsynth`"
SOUNDFONT_HINT = "lance `make soundfont` dans le repo harmonium"


class RenderError(RuntimeError):
    """Échec de rendu avec un message actionnable en français."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def require_tool(name: str, hint: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RenderError(f"{name} introuvable : {hint}")
    return path


def resolve_soundfont(explicit: str | None) -> Path:
    if explicit:
        sf = Path(explicit)
    else:
        sf = default_soundfont()
    if not sf.is_file():
        raise RenderError(f"SoundFont introuvable ({sf}) : {SOUNDFONT_HINT}")
    return sf


def resolve_feet_soundfont(explicit: str | None) -> Path | None:
    """Banque des pieds : `--feet-soundfont`, sinon résolution auto."""
    if explicit:
        sf = Path(explicit)
        if not sf.is_file():
            raise RenderError(f"banque des pieds introuvable ({sf})")
        return sf
    from harmonium_lab.feet.build import resolve_output
    auto = resolve_output(None)
    return auto if auto.is_file() else None


def remap_feet_channel(midi_path: Path, vel_scale: float = FEET_VEL_SCALE,
                       humanize: int = FEET_HUMANIZE, seed: int = FEET_SEED) -> int:
    """Canal percussion → canal mélodique des pieds (SK1).

    Déplace les notes 36/37 du canal 9 vers le canal 11 et insère la
    sélection de banque (CC0=0, CC32=`FEET_BANK`, programme `FEET_PROG`
    sur le canal 11). Les vélocités sont réduites (`vel_scale`, niveau
    pieds sous le violon) et humanisées (`±humanize`, graine `seed` :
    déterministe, alterne les couches de la SF2). Retourne le nombre de
    notes déplacées (0 : le fichier est laissé intact).
    """
    import mido
    mid = mido.MidiFile(str(midi_path))
    rng = random.Random(seed)
    moved = 0
    for track in mid.tracks:
        for msg in track:
            if msg.type in ("note_on", "note_off") and msg.channel == DRUM_CHANNEL \
                    and msg.note in FEET_NOTES:
                msg.channel = FEET_CHANNEL
                if msg.type == "note_on" and msg.velocity > 0:
                    msg.velocity = feet_velocity(msg.velocity, rng, vel_scale, humanize)
                    moved += 1
    if not moved:
        return 0
    head = [
        mido.Message("control_change", channel=FEET_CHANNEL, control=0, value=0, time=0),
        mido.Message("control_change", channel=FEET_CHANNEL, control=32, value=FEET_BANK, time=0),
        mido.Message("program_change", channel=FEET_CHANNEL, program=FEET_PROG, time=0),
    ]
    mid.tracks[0][0:0] = head
    mid.save(str(midi_path))
    return moved


def feet_velocity(base: int, rng: "random.Random", vel_scale: float,
                  humanize: int) -> int:
    """Vélocité pied : gain puis tirage uniforme `±humanize` (1–127)."""
    return max(1, min(127, round(base * vel_scale + rng.randint(-humanize, humanize))))


# ── Métrique et pieds ──────────────────────────────────────────────────


def parse_meter_value(value: str | None, tune_type: str) -> tuple[int, int]:
    """`M:` (ou métrique du manifeste) → (numérateur, dénominateur).

    `C` → 4/4, `C|` → 2/2 ; toute valeur invalide retombe sur le mètre
    par défaut du type (jamais d'exception : le rendu doit aboutir).
    """
    v = (value or "").strip()
    if v == "C":
        return (4, 4)
    if v == "C|":
        return (2, 2)
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", v)
    if m and int(m.group(2)) in (1, 2, 4, 8, 16) and int(m.group(1)) > 0:
        return (int(m.group(1)), int(m.group(2)))
    return DEFAULT_METER[tune_type]


def feet_pattern(num: int, den: int) -> tuple[str, list[int], list[int]]:
    """Motif `%%MIDI drum` : (chaîne, programmes, vélocités).

    La chaîne compte un créneau par croche de la mesure ; chaque `d`
    consomme le programme suivant (talon 36, pointe 37).
    - 6/8 (et composées) : talon sur les temps pointés, pointe sur la
      3ᵉ et 6ᵉ croche (`dzddzd`) ;
    - 3/4 : talon sur le 1, pointes sur 2 et 3 (`dzdzdz`) ;
    - 2/2 (noté `C|`, fréquent dans les reels) : talon sur les deux
      temps (blanches), pointe sur les contretemps à la noire ;
    - autres simples (4/4, 2/4) : talon sur chaque temps (noire),
      pointe sur chaque contretemps de croche.
    """
    if (den == 8 or den == 4) and num % 3 == 0 and num > 3:
        beats = num // 3
        group = num * 8 // den // beats  # croches par temps pointé
        unit = "d" + "z" * (group - 2) + "d"
        string = unit * beats
        progs = [DRUM_HEEL, DRUM_TOE] * beats
        vels = [VEL_HEEL, VEL_TOE] * beats
        return string, progs, vels
    if (num, den) == (3, 4):
        return "dzdzdz", [DRUM_HEEL, DRUM_TOE, DRUM_TOE], [VEL_HEEL, VEL_TOE, VEL_TOE]
    if (num, den) == (2, 2):
        return "dzdzdzdz", [DRUM_HEEL, DRUM_TOE] * 2, [VEL_HEEL, VEL_TOE] * 2
    slots = max(2, round(num * 8 / den))
    string = "d" * slots
    progs = [DRUM_HEEL if i % 2 == 0 else DRUM_TOE for i in range(slots)]
    vels = [VEL_HEEL if i % 2 == 0 else VEL_TOE for i in range(slots)]
    return string, progs, vels


def gchord_pattern(num: int, den: int) -> str:
    """Motif `gchord` : les défauts d'`abc2midi` quand ils existent."""
    if (num, den) in ((4, 4), (2, 4), (2, 2)):
        return "fzczfzcz"  # défaut abc2midi pour 2/4 et 4/4
    if (num, den) == (3, 4):
        return "fzczcz"  # défaut abc2midi pour 3/4
    return "fzcfzc"  # défaut abc2midi pour 6/8 (étiré aux autres composées)


# ── Accords : détection et nettoyage ───────────────────────────────────

#: Un symbole entre guillemets compte comme accord s'il commence par une
#: fondamentale A–G suivie d'une qualité connue (m, 7, maj, dim, sus…).
#: Les annotations (`"Fin"`, `"Vamp"`, `"N.C."`) sont exclues.
_CHORD = re.compile(r'^[A-G][#b]?(?:$|[mMjJdsaugD0123456789+°/\-(#])')
_QUOTED = re.compile(r'"([^"]*)"')


def _is_chord(text: str) -> bool:
    return _CHORD.match(text.strip().strip("()").strip()) is not None


def split_quotes(body: str) -> tuple[bool, str]:
    """(a des accords, corps nettoyé des annotations non-accords).

    `abc2midi` joue tout `"texte"` comme un accord : une annotation comme
    `["Fin"` le fait échouer (« Unrecognized chord »). On retire donc les
    guillemets qui ne ressemblent pas à des accords ; les vrais accords
    (y compris `(A7)`, `D(Bm)`) sont gardés tels quels.
    """
    found = False

    def _sub(m: re.Match) -> str:
        nonlocal found
        if _is_chord(m.group(1)):
            found = True
            return m.group(0)
        return ""

    cleaned = _QUOTED.sub(_sub, body)
    return found, cleaned


# ── ABC temporaire ─────────────────────────────────────────────────────


def build_render_abc(src: str, tune_type: str, meter: tuple[int, int],
                     include_feet: bool = True) -> tuple[str, bool]:
    """Copie de travail : tempo + directives `%%MIDI`, sans toucher la source.

    - les `Q:` et `%%MIDI` éventuels de la source sont neutralisés (armes
      égales : tempo et programmes uniformes) ;
    - les annotations `"..."` non-accords sont retirées (voir `split_quotes`) ;
    - `Q:` passe *avant* le premier `K:` (sinon `abc2midi` émet deux
      événements de tempo), `%%MIDI drumon` *après* (exigé, sinon fatal).
    """
    num, den = meter
    lines = src.splitlines()
    lines = [ln for ln in lines if not re.match(r"^Q:", ln) and not ln.startswith("%%MIDI")]
    try:
        k = next(i for i, ln in enumerate(lines) if re.match(r"^K:", ln))
    except StopIteration:
        raise RenderError("ABC sans ligne K: (tonalité), rendu impossible")
    head, tail = lines[:k], lines[k + 1:]
    has_chords = False
    cleaned_tail = []
    for ln in tail:
        if ln.startswith("V:"):
            cleaned_tail.append(ln)
            cleaned_tail.append(f"%%MIDI program {PROG_MELODY}")
            continue
        found, ln = split_quotes(ln)
        has_chords = has_chords or found
        cleaned_tail.append(ln)
    drum, progs, vels = feet_pattern(num, den)
    out = [
        *head,
        f"Q:{TEMPO_Q[tune_type]}",
        lines[k],
        f"%%MIDI program {PROG_MELODY}",
        f"%%MIDI chordprog {PROG_CHORD}",
        f"%%MIDI bassprog {PROG_BASS}",
        f"%%MIDI gchord {gchord_pattern(num, den)}",
        *([f"%%MIDI drum {drum} {' '.join(map(str, progs))} {' '.join(map(str, vels))}",
           "%%MIDI drumon"] if include_feet else []),
        *cleaned_tail,
    ]
    return "\n".join(out) + "\n", has_chords


# ── Étapes de rendu ────────────────────────────────────────────────────


@dataclass
class MidiResult:
    path: Path
    has_chords: bool
    returncode: int
    log: str  # sortie d'abc2midi (avertissements éventuels, ex. voltas)


def render_midi(abc_path: Path, midi_path: Path, tune_type: str, meter: tuple[int, int],
                remap_feet: bool = True, vel_scale: float = FEET_VEL_SCALE,
                humanize: int = FEET_HUMANIZE, seed: int = FEET_SEED,
                include_feet: bool = True) -> MidiResult:
    """ABC → MIDI ; si `remap_feet`, pieds GM → canal 11 (banque dédiée).

    `remap_feet` doit être faux quand `render_wav` ne chargera pas la
    banque des pieds (sinon programme 0 = piano GeneralUser).
    """
    abc2midi = require_tool("abc2midi", ABC2MIDI_HINT)
    text, has_chords = build_render_abc(
        abc_path.read_text(encoding="utf-8"), tune_type, meter, include_feet
    )
    tmp = midi_path.with_suffix(".render.abc")
    tmp.write_text(text, encoding="utf-8")
    try:
        proc = subprocess.run(
            [abc2midi, str(tmp), "-o", str(midi_path)],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        tmp.unlink(missing_ok=True)
    log = (proc.stdout + proc.stderr).strip()
    # abc2midi sort 1 sur erreur non fatale mais écrit quand même un MIDI
    # exploitable (ex. voltas `|1,3`) ; seul un MIDI absent est un échec.
    if not midi_path.is_file() or midi_path.stat().st_size == 0:
        raise RenderError(f"abc2midi n'a produit aucun MIDI pour {abc_path.name} : {log}")
    if remap_feet:
        n_feet = remap_feet_channel(midi_path, vel_scale, humanize, seed)  # SK1
        if n_feet:
            suffix = f"{n_feet} notes de pieds réassignées au canal 11"
            log = f"{log}\n({suffix})" if log else suffix
    return MidiResult(midi_path, has_chords, proc.returncode, log)


def wav_peak(path: Path) -> float:
    """Pic d'un WAV PCM 16 bits (0–1)."""
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2:
            raise RenderError(f"{path.name} : WAV non PCM 16 bits, normalisation impossible")
        raw = w.readframes(w.getnframes())
    if not raw:
        return 0.0
    peak = max(abs(s) for s in struct.unpack("<" + "h" * (len(raw) // 2), raw))
    return peak / 32768.0


def normalize_wav(path: Path, target: float = PEAK_TARGET) -> tuple[float, float]:
    """Ramène le pic à `target` par gain linéaire. Retourne (avant, après)."""
    if sys.byteorder != "little":
        raise RenderError("normalisation WAV : machine big-endian non gérée")
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2:
            raise RenderError(f"{path.name} : WAV non PCM 16 bits, normalisation impossible")
        params = w.getparams()
        raw = w.readframes(w.getnframes())
    if not raw:
        return 0.0, 0.0
    samples = array.array("h")
    samples.frombytes(raw)
    peak = max(abs(s) for s in samples)
    if peak == 0:
        return 0.0, 0.0
    gain = target * 32768.0 / peak
    scaled = array.array("h", (max(-32768, min(32767, round(s * gain))) for s in samples))
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(scaled.tobytes())
    return peak / 32768.0, min(1.0, peak * gain / 32768.0)


def render_wav(midi_path: Path, wav_path: Path, soundfont: Path,
               feet_soundfont: Path | None = None, normalize: bool = True) -> tuple[float, float]:
    fluidsynth = require_tool("fluidsynth", FLUIDSYNTH_HINT)
    fonts = [str(soundfont)] + ([str(feet_soundfont)] if feet_soundfont else [])
    proc = subprocess.run(
        [fluidsynth, "-ni", "-r", "44100", "-F", str(wav_path), *fonts, str(midi_path)],
        capture_output=True, text=True, timeout=300,
    )
    if not wav_path.is_file() or wav_path.stat().st_size == 0:
        raise RenderError(f"fluidsynth n'a produit aucun WAV pour {midi_path.name} : {(proc.stdout + proc.stderr).strip()}")
    if not normalize:
        peak = wav_peak(wav_path)
        return peak, peak
    return normalize_wav(wav_path)


def render_musicxml(midi_path: Path, xml_path: Path) -> None:
    try:
        from music21 import converter
    except ImportError:
        raise RenderError("music21 introuvable : installe les dépendances (`pip install -e .`)")
    score = converter.parse(str(midi_path))
    score.write("musicxml", str(xml_path))


# ── Sélection et orchestration ─────────────────────────────────────────


def load_manifest(root: Path) -> list[dict]:
    manifest = root / "manifest.jsonl"
    if not manifest.is_file():
        raise RenderError(f"manifeste introuvable ({manifest}) : lance `make trad-corpus`")
    return [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]


def select_rows(rows: list[dict], tune_type: str | None, limit: int | None,
                seed: int, ids: list[str] | None) -> list[dict]:
    """Lignes à rendre : `--ids`, ou tirage `seed` + `limit` (reproductible)."""
    if tune_type is not None:
        rows = [r for r in rows if r["type"] == tune_type]
    if ids:
        wanted = set(ids)
        picked = [r for r in rows if r["id"] in wanted]
        missing = wanted - {r["id"] for r in picked}
        if missing:
            raise RenderError(f"airs inconnus dans le manifeste : {sorted(missing)}")
        return picked
    if limit is not None:
        return random.Random(seed).sample(rows, min(limit, len(rows)))
    return rows


def render_one(abc_path: Path, row: dict, out_dir: Path, soundfont: Path,
               musicxml: bool, feet_soundfont: Path | None = None,
               vel_scale: float = FEET_VEL_SCALE, humanize: int = FEET_HUMANIZE,
               feet_seed: int = FEET_SEED, include_feet: bool = True) -> dict:
    """Rend un air (MIDI + WAV [+ MusicXML]). Retourne la ligne de log."""
    tune_type = row["type"]
    meter = parse_meter_value(row.get("meter"), tune_type)
    out_dir.mkdir(parents=True, exist_ok=True)
    midi_path = out_dir / f"{row['id']}.mid"
    wav_path = out_dir / f"{row['id']}.wav"
    res = render_midi(abc_path, midi_path, tune_type, meter,
                      remap_feet=include_feet and feet_soundfont is not None,
                      vel_scale=vel_scale, humanize=humanize, seed=feet_seed,
                      include_feet=include_feet)
    peak_before, peak_after = render_wav(midi_path, wav_path, soundfont, feet_soundfont)
    entry = {
        "id": row["id"], "type": tune_type,
        "meter": f"{meter[0]}/{meter[1]}",
        "midi": midi_path.name, "wav": wav_path.name,
        "has_chords": res.has_chords,
        "abc2midi_returncode": res.returncode,
        "peak_before": round(peak_before, 4), "peak_after": round(peak_after, 4),
    }
    if not res.has_chords:
        entry["note"] = "sans accords : mélodie + pieds seulement"
    if res.log:
        entry["abc2midi_log"] = res.log[-500:]
    if musicxml:
        xml_path = out_dir / f"{row['id']}.musicxml"
        render_musicxml(midi_path, xml_path)
        entry["musicxml"] = xml_path.name
    return entry


def render_all(root: Path, out: Path, tune_type: str | None, limit: int | None,
               seed: int, ids: list[str] | None, soundfont: Path,
               musicxml: bool, feet_soundfont: Path | None = None,
               vel_scale: float = FEET_VEL_SCALE, humanize: int = FEET_HUMANIZE,
               feet_seed: int = FEET_SEED, include_feet: bool = True) -> list[dict]:
    rows = load_manifest(root)
    picked = select_rows(rows, tune_type, limit, seed, ids)
    if not picked:
        raise RenderError("rien à rendre (type inconnu ou limite nulle ?)")
    entries = []
    for row in picked:
        abc_path = root / "tunes" / row["type"] / f"{row['id']}.abc"
        if not abc_path.is_file():
            raise RenderError(f"ABC introuvable ({abc_path}) : relance `make trad-corpus`")
        entries.append(render_one(abc_path, row, out / row["type"], soundfont, musicxml,
                                  feet_soundfont, vel_scale, humanize, feet_seed, include_feet))
    log_path = out / "render_log.jsonl"
    merged = {}
    if log_path.is_file():  # cumulatif entre invocations (un type par appel)
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                old = json.loads(line)
                merged[old["id"]] = old
    for e in entries:
        merged[e["id"]] = e
    log_path.write_text(
        "".join(json.dumps(merged[k], ensure_ascii=False, separators=(",", ":")) + "\n"
                for k in sorted(merged)),
        encoding="utf-8",
    )
    return entries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trad-render", description="Rend le corpus trad à armes égales (MIDI + WAV)")
    ap.add_argument("--root", type=Path, default=Path("corpus/trad"), help="racine du corpus")
    ap.add_argument("--out", type=Path, default=Path("target/trad_render"), help="dossier de sortie")
    ap.add_argument("--type", default=None, help="reel, jig, waltz, march, quadrille, cotillon (défaut : tous)")
    ap.add_argument("--limit", type=int, default=None, help="échantillon reproductible de N airs")
    ap.add_argument("--seed", type=int, default=SAMPLE_SEED, help="graine du tirage")
    ap.add_argument("--ids", nargs="*", default=None, help="identifiants d'airs (ignore --limit/--seed)")
    ap.add_argument("--soundfont", default=None, help="banque .sf2 (défaut : ../harmonium/assets/GeneralUser-GS.sf2)")
    ap.add_argument("--feet-soundfont", default=None, help="banque des pieds .sf2 (défaut : résolution auto, absente = percussions GM)")
    ap.add_argument("--feet-gain", type=float, default=FEET_VEL_SCALE, help="gain des vélocités pieds (défaut : %(default)s)")
    ap.add_argument("--feet-humanize", type=int, default=FEET_HUMANIZE, help="humanisation ± vélocité (défaut : %(default)s)")
    ap.add_argument("--feet-seed", type=int, default=FEET_SEED, help="graine humanisation pieds (défaut : %(default)s)")
    ap.add_argument("--no-feet", action="store_true", help="n’ajoute pas la podorythmie dans le MIDI")
    ap.add_argument("--musicxml", action="store_true", help="émet aussi .musicxml via music21")
    args = ap.parse_args(argv)

    try:
        soundfont = resolve_soundfont(args.soundfont)
        feet_soundfont = resolve_feet_soundfont(args.feet_soundfont)
        print(f"banque : {soundfont.name}"
              + (f" + {feet_soundfont} (pieds canal 11, gain {args.feet_gain})" if feet_soundfont
                 else " (pieds : percussions GM, banque dédiée absente)"))
        entries = render_all(args.root, args.out, args.type, args.limit,
                             args.seed, args.ids, soundfont, args.musicxml, feet_soundfont,
                             args.feet_gain, args.feet_humanize, args.feet_seed, not args.no_feet)
    except RenderError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    by_type: dict[str, list[dict]] = {}
    for e in entries:
        by_type.setdefault(e["type"], []).append(e)
    for t in sorted(by_type):
        print(f"{t} : {len(by_type[t])} airs → {args.out / t}/")
        for e in by_type[t][:5]:
            print(f"  {e['midi']} pic {e['peak_after']}")
    no_chords = sum(1 for e in entries if not e["has_chords"])
    print(f"\n{len(entries)} airs rendus, {no_chords} sans accords (voir render_log.jsonl).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
