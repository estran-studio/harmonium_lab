"""Comparatif SK3 : violons seuls 8 mesures, puis guitare/basse jusqu'à 16."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import mido
import numpy as np
import soundfile as sf
from scipy import signal

from .fiddle_samples import acquire
from .render import load_manifest, parse_meter_value, render_midi, require_tool

RATE = 44100
TEMPO = 230
VELOCITY = 96
RMS_TARGET = 0.06


def folded(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if not unicodedata.combining(c)).replace("'", "").replace("-", " ")


def select_tunes(rows: list[dict], corpus: Path) -> list[dict]:
    available = sorted((r for r in rows if r["type"] == "reel"
                        and (corpus / "tunes/reel" / (r["id"] + ".abc")).is_file()),
                       key=lambda r: (r["source"] != "chambers", r["id"]))
    chosen = []
    for names in (("sainte anne", "st ann", "saint anne"), ("beatrice",), ("joys of quebec",)):
        candidates = [r for r in available if any(n in folded(" ".join([r["title"], *r.get("aliases", [])])) for n in names)]
        if candidates:
            chosen.append(candidates[0])
    for row in available:
        if len(chosen) >= 3:
            break
        if row not in chosen and all(folded(row["title"]) != folded(r["title"]) for r in chosen):
            chosen.append(row)
    if len(chosen) != 3:
        raise ValueError("trois reels ABC requis : lancer make trad-corpus")
    return chosen


def comparison_stem(source: mido.MidiFile, *, melody: bool, bank: int = 0,
                    program: int = 40, quarters_per_bar: float = 4) -> mido.MidiFile:
    """Coupe à 16 mesures ; aucun pied, note pendante ou changement de vélocité."""
    result = mido.MidiFile(ticks_per_beat=source.ticks_per_beat)
    track = mido.MidiTrack()
    result.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(TEMPO)))
    if melody:
        track.extend([mido.Message("control_change", channel=0, control=0, value=bank // 128),
                      mido.Message("control_change", channel=0, control=32, value=bank % 128),
                      mido.Message("program_change", channel=0, program=program)])
    start = 0 if melody else round(8 * quarters_per_bar * source.ticks_per_beat)
    end = round(16 * quarters_per_bar * source.ticks_per_beat)
    tick = last = 0
    active = set()
    for msg in mido.merge_tracks(source.tracks):
        tick += msg.time
        if tick >= end:
            break
        if msg.is_meta or not hasattr(msg, "channel"):
            continue
        if (melody and msg.channel != 0) or (not melody and msg.channel not in (1, 2)):
            continue
        if msg.type == "program_change":
            if melody:
                continue
        elif msg.type in ("note_on", "note_off"):
            key = (msg.channel, msg.note)
            on = msg.type == "note_on" and msg.velocity > 0
            if tick < start:
                continue
            if on:
                active.add(key)
            elif key not in active:
                continue
            else:
                active.remove(key)
            if melody and on:
                msg = msg.copy(velocity=VELOCITY)
        elif msg.type != "control_change":
            continue
        track.append(msg.copy(time=tick - last))
        last = tick
    for channel, note in sorted(active):
        track.append(mido.Message("note_off", channel=channel, note=note, time=end-last))
        last = end
    track.append(mido.MetaMessage("end_of_track", time=end-last))
    return result


def synthesize(midi: Path, font: Path, destination: Path) -> np.ndarray:
    tool = require_tool("fluidsynth", "brew install fluidsynth")
    proc = subprocess.run([tool, "-ni", "-R", "0", "-C", "0", "-g", "0.2",
                           "-r", str(RATE), "-T", "wav", "-O", "float", "-F",
                           str(destination), str(font), str(midi)],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode or not destination.is_file():
        raise RuntimeError(f"fluidsynth : {proc.stdout} {proc.stderr}")
    audio, rate = sf.read(destination, always_2d=True)
    if rate != RATE or not np.isfinite(audio).all():
        raise ValueError("rendu audio invalide")
    return audio


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio * audio)))


def discontinuities(audio: np.ndarray, rate: int = RATE) -> dict:
    """Sauts isolés > 8× la pente RMS locale ET > 2 % FS, hors attaques/relâches.

    Détecteur de suspicion, pas une preuve psychoacoustique d'absence de clic.
    Chaque canal est inspecté (pas d'annulation lors d'une sommation mono).
    """
    data = np.asarray(audio)
    if data.ndim == 1:
        data = data[:, None]
    derivative = np.diff(data, axis=0)
    local = np.sqrt(signal.convolve(derivative ** 2, np.ones((441, 1)) / 441,
                                   mode="same", method="auto"))
    mask = (np.abs(derivative) > 0.02) & (np.abs(derivative) > 8 * np.maximum(local, 1e-9))
    where = np.flatnonzero(np.any(mask, axis=1))
    groups = where[np.r_[True, np.diff(where) > rate // 100]] if len(where) else where
    return {"suspect_count": int(len(groups)), "times_s": [round(float(i / rate), 5) for i in groups],
            "max_step": float(np.max(np.abs(derivative))) if len(derivative) else 0.0}


def probe(font: Path, preset: dict, work: Path) -> dict:
    """Quatre tenues couvrant le registre ; métriques et WAV conservés pour écoute."""
    midi = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    track.extend([mido.MetaMessage("set_tempo", tempo=500000),
                  mido.Message("control_change", control=0, value=preset["bank"] // 128),
                  mido.Message("control_change", control=32, value=preset["bank"] % 128),
                  mido.Message("program_change", program=preset["program"])])
    notes = [55, 62, 69, 76]
    for note in notes:
        track.append(mido.Message("note_on", note=note, velocity=VELOCITY, time=480))
        track.append(mido.Message("note_off", note=note, time=2880))
    mid = work.with_suffix(".mid")
    midi.save(mid)
    audio = synthesize(mid, font, work.with_suffix(".wav"))
    results = []
    for index, note in enumerate(notes):
        onset = 0.5 + index * 3.5
        segment = audio[round((onset + 0.25) * RATE):round((onset + 2.8) * RATE)]
        mono = segment.mean(axis=1)
        frequency = 440 * 2 ** ((note - 69) / 12)
        sos = signal.butter(3, [frequency * .8, frequency * 1.2], btype="bandpass", fs=RATE, output="sos")
        analytic = signal.hilbert(signal.sosfiltfilt(sos, mono))
        pitch = np.diff(np.unwrap(np.angle(analytic))) * RATE / (2 * np.pi)
        cents = 1200 * np.log2(np.maximum(pitch, 1) / frequency)
        modulation = signal.sosfiltfilt(signal.butter(2, [4, 9], btype="bandpass", fs=RATE, output="sos"), cents)[RATE//4:-RATE//4]
        spectrum = np.abs(np.fft.rfft(mono)) ** 2
        high = np.fft.rfftfreq(len(mono), 1/RATE) > 8000
        onset_audio = audio[round(onset * RATE):round((onset + .4) * RATE)]
        envelope = np.sqrt(np.mean(onset_audio.reshape(-1, 2) ** 2, axis=1))
        envelope = np.convolve(envelope, np.ones(441)/441, mode="same")
        threshold = np.max(envelope) * .9
        attack = np.flatnonzero(envelope >= threshold)
        results.append({"note": note, "attack90_ms": round(float(attack[0] / RATE * 1000), 1) if len(attack) else None,
                        "vibrato_4_9hz_cents_rms": round(rms(modulation), 2),
                        "energy_above_8khz_pct": round(float(spectrum[high].sum() / max(spectrum.sum(), 1e-20) * 100), 4),
                        "discontinuities": discontinuities(segment)})
    return {"notes": results}


def run(manifest: Path, corpus: Path, raw: Path, output: Path, offline: bool) -> None:
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    acquire(rows, raw, offline=offline)
    fonts = [r for r in rows if r["status"] == "accepted"]
    if len(fonts) < 4:
        raise ValueError("au moins quatre banques autorisées requises")
    generaluser = raw / "generaluser.sf2"
    tunes = select_tunes(load_manifest(corpus), corpus)
    output.mkdir(parents=True, exist_ok=True)
    probes = output / "probes"
    probes.mkdir(exist_ok=True)
    analysis = {"tempo_quarter": TEMPO, "velocity": VELOCITY, "rms_target": RMS_TARGET,
                "fonts": {}, "tunes": []}
    for row in fonts:
        print(f"Tenues : {row['name']}", flush=True)
        analysis["fonts"][row["id"]] = probe(raw / (row["id"] + ".sf2"), row["selected"], probes / row["id"])
    for tune in tunes:
        print(f"Reel : {tune['title']}", flush=True)
        folder = output / tune["id"]
        folder.mkdir(exist_ok=True)
        meter = parse_meter_value(tune.get("meter"), "reel")
        quarters = meter[0] * 4 / meter[1]
        source_path = folder / "source.mid"
        rendered = render_midi(corpus / "tunes/reel" / (tune["id"] + ".abc"), source_path, "reel", meter)
        if not rendered.has_chords:
            raise ValueError(f"accords requis pour {tune['id']}")
        source = mido.MidiFile(source_path)
        solo_frames = round(8 * quarters * 60 / TEMPO * RATE)
        frames = round((16 * quarters * 60 / TEMPO + 1) * RATE)
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            backing_midi = work / "backing.mid"
            comparison_stem(source, melody=False, quarters_per_bar=quarters).save(backing_midi)
            backing = synthesize(backing_midi, generaluser, work / "backing.wav")
            backing = np.pad(backing[:frames], ((0, max(0, frames-len(backing))), (0, 0)))
            backing[:solo_frames] = 0
            tune_analysis = {"id": tune["id"], "title": tune["title"], "source": tune["url"],
                             "license": tune["license"], "solo_seconds": solo_frames/RATE, "renders": []}
            for number, row in enumerate(fonts, 1):
                mid = folder / f"{number:02}_{row['id']}.mid"
                comparison_stem(source, melody=True, **row["selected"], quarters_per_bar=quarters).save(mid)
                melody = synthesize(mid, raw / (row["id"] + ".sf2"), work / "solo.wav")
                melody = np.pad(melody[:frames], ((0, max(0, frames-len(melody))), (0, 0)))
                measured = rms(melody[:solo_frames])
                if measured < 1e-8:
                    raise ValueError(f"violon silencieux : {row['id']}")
                gain = RMS_TARGET / measured
                mixed = melody * gain + backing
                if np.max(np.abs(mixed)) >= 1:
                    raise ValueError(f"écrêtage : {row['id']} ; réduire RMS_TARGET pour tous")
                name = f"{number:02}_{row['id']}.wav"
                sf.write(folder / name, mixed, RATE, subtype="PCM_24")
                tune_analysis["renders"].append({"file": name, "melody_gain": gain,
                                                 "solo_rms": rms(mixed[:solo_frames]),
                                                 "peak": float(np.max(np.abs(mixed)))})
            analysis["tunes"].append(tune_analysis)
    (output / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    write_readme(output, rows, analysis)
    print(f"Comparatif : {output / 'README.md'}", flush=True)


def write_readme(output: Path, rows: list[dict], analysis: dict) -> None:
    lines = ["# Comparatif de violons libres — SK3", "",
             "230 à la noire ; vélocité mélodie 96 ; droit, effets reverb/chorus désactivés.",
             "8 premières mesures : violon seul ; mesures 9–16 : même guitare 24/basse 32 GeneralUser GS, sans pieds.",
             "Gain de chaque violon mesuré sur ses 8 mesures solo : RMS stéréo 0,060 (−24,44 dBFS).",
             "Accompagnement rendu une seule fois par air, jamais renormalisé. WAV PCM 24 bits, 44,1 kHz.", "",
             "| N° | Violon | Licence | Taille SF2 (octets) | Banque/programme (0-based) |", "|---|---|---|---:|---|"]
    for number, row in enumerate((r for r in rows if r["status"] == "accepted"), 1):
        p = row["selected"]
        lines.append(f"| {number:02} | {row['name']} | {row['license']} | {row['size_bytes']} | {p['bank']}/{p['program']} |")
    lines.extend(["", "## Airs réels (usage interne uniquement)", ""])
    for tune in analysis["tunes"]:
        lines.append(f"- [{tune['title']}]({tune['source']}) : `{tune['id']}/` ; solo {tune['solo_seconds']:.3f} s ; {tune['license']}.")
    lines.extend(["", "## Observations instrumentales — pas une écoute humaine", "",
                  "Aucune écoute humaine n'est revendiquée : ces notes viennent des WAV de contrôle `probes/`.",
                  "Tenues G3/D4/A4/E5 de 3 s ; attaques et relâches exclues du détecteur de clic (fenêtre 0,25–2,8 s).",
                  "Attaque = délai pour atteindre 90 % du maximum des 400 premières ms ; vibrato = modulation 4–9 Hz du fondamental (cents RMS).",
                  "L'énergie > 8 kHz est un indice de brillance/bruit, pas une séparation certaine bruit/harmoniques.",
                  "Clic suspect : saut > 0,02 FS et > 8× pente RMS locale sur 10 ms, tous canaux ; seuils heuristiques, pas garantie d'inaudibilité.", "",
                  "| Violon | Attaque90 G3 (ms) | Vibrato G3 (cents RMS) | Énergie >8 kHz G3 (%) | Discontinuités sur 4 tenues |",
                  "|---|---:|---:|---:|---:|"])
    for row in rows:
        if row["status"] != "accepted":
            continue
        notes = analysis["fonts"][row["id"]]["notes"]
        first = notes[0]
        clicks = sum(n["discontinuities"]["suspect_count"] for n in notes)
        lines.append(f"| {row['name']} | {first['attack90_ms']} | {first['vibrato_4_9hz_cents_rms']} | {first['energy_above_8khz_pct']} | {clicks} |")
    lines.extend(["", "## Droits et exclusions", "",
                  "Rien n'est redistribué : SF2, ABC, MIDI et WAV restent locaux/gitignorés. Le manifeste versionné cite les sources et empreintes.",
                  "MIT : conserver les notices ; CC-BY-3.0 : créditer Fernando A. Martin, LDK1609, Jeff Glatt (voir manifeste).",
                  "GeneralUser : autorisation commerciale explicite, mais provenance de certains samples non garantie par son auteur.", ""])
    for row in rows:
        if row["status"] == "rejected":
            lines.append(f"- **{row['name']}** — {row['license']} : {row['reason']} [Source]({row['license_source']}).")
    (output / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("samples/fiddles/manifest.jsonl"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus/trad"))
    parser.add_argument("--raw", type=Path, default=Path("samples/fiddles/raw"))
    parser.add_argument("--output", type=Path, default=Path("target/fiddle_compare"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    run(args.manifest, args.corpus, args.raw, args.output, args.offline)


if __name__ == "__main__":
    main()
