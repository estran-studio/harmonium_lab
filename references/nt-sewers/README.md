# Références Sewers — *Nuclear Throne* (Jukio Kallio)

Analyse intégrale de **04 Groundwork of the Past** (Sewers A, 137 s) ;
**31 What's That Smell** (Pizza Sewers, 97 s) sert uniquement de contexte audio.
Méthode G9-G0 des références Isaac Basement et NT Desert : mesures du mix,
calage numérique, structure, stems, transcriptions puis propositions de données.

**Provenance et droits — principe VII.** OST de Jukio Kallio / Vlambeer,
2015, source officielle indiquée dans le manifeste :
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=304s> (04) et
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=3481s> (31).
Le manifeste et tous les enregistrements, stems et transcriptions restent dans
`~/Project/bascanada/harmonium_lab/corpus/nuclear_throne/`, **hors de ce worktree**.
Seuls `README.md`, `measures.json` et `grids.json` sont versionnés ici.

## 1. Mesures audio et contexte `type=zone`

`measures.json` contient les 20 pistes `zone`, leurs métadonnées et statistiques
agrégées, calculées de nouveau avec `audioref-measures` ; ce n'est pas une copie
numérique des anciennes mesures Desert (versions des bibliothèques différentes).

| Mesure du mix complet | Groundwork | Pizza Sewers, contexte | 20 zones, moyenne ± écart-type |
|---|---:|---:|---:|
| Tempo brut `beat_track`, BPM | 107,7 | 95,7 | 115,4 ± 43,8 |
| Attaques / s | 1,31 | 3,00 | 2,58 ± 1,65 |
| Force tonale | 1,587 | 1,442 | 1,699 ± 0,445 |
| Entropie chroma, bits | 3,534 | 3,558 | 3,511 ± 0,068 |
| Centroïde, Hz | **1 536** | **3 736** | 2 045 ± 739 |
| Rolloff 85 %, Hz | 3 149 | 7 712 | 4 051 ± 1 620 |
| Platitude spectrale | 0,01178 | 0,08707 | 0,0285 ± 0,0231 |
| Part harmonique / percussive HPSS | **90,35 / 9,65 %** | 71,30 / 28,70 % | 87,45 / 12,55 % |
| RMS moyen ± dispersion temporelle | 0,17374 ± 0,09704 | 0,26174 ± 0,09347 | 0,1934 ± 0,0482 entre pistes |

Groundwork est sombre et peu percussif en moyenne ; Pizza est le maximum de
brillance des 20 zones. **Ne pas transférer son kit brillant au Sewers normal.**
`dynamic_range_db = 80` pour les 20 fichiers : plafond lié au silence/plancher
numérique, pas une preuve de 80 dB de dynamique musicale. Sur Groundwork,
l'écart RMS P90/P10 des fenêtres au-dessus de 1 % du maximum est **12,05 dB**.
La part HPSS n'est ni une proportion d'instruments ni l'énergie du stem batterie.

## 2. Tempo, mètre, tonique et mode — confiance

| Paramètre | Groundwork | Pizza, mix seulement |
|---|---|---|
| Tempo retenu | **80,0006 BPM**, noire 0,749994 s ; lecture double 160 équivalente | **95,0016 BPM**, lecture double 190 possible |
| Mètre / grille | **4/4 binaire**, 16 pas, mesure 2,999978 s ; confiance moyenne sur le demi-temps, haute sur la subdivision | 4/4 binaire, 16 pas ; confiance moyenne sur le mètre |
| Preuve de calage | Cohérence des attaques à noire/4 **R = 0,7623**, résidu absolu médian **10,29 ms**, P90 **36,07 ms** | R = 0,8047, médiane 12,14 ms, P90 23,01 ms |
| Premier temps positif | **1,01488 s** ; phase conventionnelle de confiance moyenne | 0,77360 s, confiance moyenne |
| Centre local | **D**, pédale d'ouverture et reprise ; **C/E/A** au centre : haute confiance sur les classes D et C | Classe la plus forte A ; tonique fonctionnelle non établie, confiance faible |
| Mode | **Modal/chromatique, pas un mode unique démontré**. Ouverture : gabarit fixé sur D → lydien (0,823, marge 0,014) ; centre → mixolydien (0,839–0,892) ; retour tardif plus mineur | Gabarit global C mixolydien = D éolien, marge 0 : mode/tonique ambigus |

Le gabarit global de Groundwork est **C lydien = D mixolydien**, score 0,891,
marge nulle. Le départage alphabétique ne démontre pas une tonique C. Le stem
basse confirme D puis C ; les voisins D#/C# brefs ne suffisent pas à déclarer
une gamme phrygienne. **D mixolydien est un choix de profil, pas une certitude
musicologique.** La pédale sans tierce préserve mieux cette ambiguïté.

Convention commune : mesures **0-based**, intervalles `[début, fin)`.
`grids.json` place l'origine théorique à **−1,985098 s** : la mesure 0 est
partielle dans la source, la mesure 1 commence à 1,01488 s. Cela permet de
transcrire aussi l'amorce, sans la jeter avant le premier temps positif.
Les temps hors `[0,137]` dans le sidecar intégral désignent du remplissage,
jamais un segment audio existant. La dernière mesure partielle est conservée.

## 3. Structure complète et longueurs de boucles

Découpage de travail par basse, chroma par mesure et énergie des stems ;
les noms de sections sont analytiques, non officiels.

| Mesures | Source, s | Matériau / énergie | Unité répétée |
|---|---:|---|---|
| 0, partielle | 0–1,015 | Amorce et établissement de D | — |
| 1–9 | 1,015–25,015 | Pédale D, batterie presque absente : RMS par mesure ~0,0002–0,0006 avant la relance | Tenue ; fenêtre 4 mes. utile, pas un riff de 4 notes |
| 9–17 | 25,015–49,015 | Batterie dense (~0,08–0,10 RMS), hauteur de basse souvent non voisée ; D/A dans le chroma | Texture de 8 mes., subdivisions rapides |
| 17–29 | 49,015–85,014 | Basse **C, E**, passages A/B ; batterie ramenée à ~0,02 RMS | Cellules de **4 mes.** variées, pas un copier-coller harmonique exact |
| 29–33 | 85,014–97,014 | Descente chromatique **E–D#–D–C#–C–B**, retour vers D | Raccord de **4 mes.** |
| 33–41 | 97,014–121,014 | Reprise de la pédale et de l'ouverture | Retour après **32 mes. = 96 s** |
| 41–46 + fin partielle | 121,014–137 | Reprise du passage dense, puis extinction | Coda coupée par la fin du fichier |

Score `loop_scores` au décalage 32 : **0,2247**, 14 paires (cosinus moyen au
retard moins moyenne hors diagonale). C'est une preuve de reprise longue ;
ce n'est pas une corrélation waveform ni une preuve que toute la piste boucle
sur quatre mesures. La nouveauté chroma seule place la transition vers 55 s,
plus tard que la rupture de basse/batterie à 49 s : d'où le recoupement des stems.

## 4. Instrumentation probable et candidats de rendu

Stems demucs **htdemucs 4.1.0**, CPU, un décalage. Les valeurs ci-dessous
portent sur tout le fichier. **Inférences de timbre, non identification certaine ;
pas d'écoute humaine revendiquée.** `vocals` est une étiquette de séparation,
pas une preuve de chant.

| Rôle / preuve | Timbre probable et confiance | GM 0-based GeneralUser GS | Fichiers Odin candidats exacts, dossier plat `~/Project/bascanada/odin-presets/` |
|---|---|---|---|
| Basse, RMS 0,12360, centroïde 1 050 Hz | Pédale électrique/synthétique riche en harmoniques ; moyenne | **38 Synth Bass 1**, 33 Electric Bass (finger) plus doux | `Bass Low [RM].odin`, `Bass Crusher [RM].odin`, `Growly FM Bass [XR].odin` |
| `other`, RMS 0,08430, centroïde 1 724 Hz, platitude 0,00724 | Nappe/clavier tenu filtré ; moyenne | **89 Pad 2 (warm)**, 91 Pad 4 (choir) | `Haunt [RM].odin`, `Moonshade.odin`, `Eerie Pad.odin` |
| `vocals`, RMS 0,08496, centroïde 2 402 Hz | Ligne médium / texture expressive, possiblement doublée ; faible sur la source acoustique | **81 Lead 2 (sawtooth)**, 52 Choir Aahs si texture non soliste | `Haunt [RM].odin`, `Eerie Pad.odin` ; éviter un sifflement |
| Batterie, RMS 0,04666, centroïde 2 610 Hz | Percussions bruitées/roulements plus qu'un kit à backbeat constant ; moyenne | Canal 10, **36/38/42**, kit Standard, banque 128 | `Kick-1 [Photonic].odin`, `Snare-1 [Photonic].odin`, `HiHat-closed [Photonic].odin` : comparaison sonore seulement, Heel/Toe restent SoundFont |

Préférence de rendu : Bass Low + Haunt en base, Crusher/Moonshade sous tension.
Pas de Phazzy Organ, pas de Sausage Bassener pour les traits rapides, pas de
sifflement ni de guitare saturée GM 30. Les candidats Odin n'ont pas été écoutés
ni réglés dans ce chantier ; les WAV de transcription utilisent GeneralUser seul.

## 5. Transcriptions intégrales et boucles hors dépôt

Sept triplets réellement produits dans `$ROOT/transcriptions/`, préfixe
`04_groundwork_of_the_past_`, extensions **`.mid`, `.wav`, `.json`**.
L'intégrale couvre toute la source ; les autres fichiers sont des extraits
quantifiés, pas sept boucles originales indépendantes.

| Suffixe | Mesures | Minutage théorique source, s | Contenu / confiance |
|---|---|---:|---|
| `integrale` | 0–47 | −1,985–139,014, source utile **0–137** | Basse + batterie + lead + accords ; moyenne sur la structure, faible sur les détails bruités |
| `pedale_D` | 1–5 | 1,015–13,015 | Pédale D, haute sur la classe, moyenne sur l'octave |
| `transition` | 9–17 | 25,015–49,015 | Texture percussive, basse lacunaire ; faible sur les hauteurs |
| `cycle_C` | 17–21 | 49,015–61,014 | C/E et retour C, moyenne |
| `cycle_C_var` | 21–25 | 61,014–73,014 | Variante du même matériau, moyenne |
| `descente` | 29–33 | 85,014–97,014 | Descente chromatique, moyenne |
| `reprise` | 33–37 | 97,014–109,014 | Retour D, haute sur la classe |

Indicateurs **globaux**, pas probabilités par boucle : basse `voiced_ratio`
**0,6387**, lead **0,6174**, accords score moyen **0,824**, racine D dans
**54,3 %** des mesures ; 158 attaques de batterie, marge moyenne **0,721**.
La grande marge spectrale ne garantit pas la bonne classe de percussion.
Le détecteur d'accords ne connaît que majeur/mineur et impose des tierces à des
sons parfois sans tierce. pYIN peut perdre la basse saturée (notamment 25–47 s)
et hésiter d'une octave ; le lissage est borné au registre analysé, sans garantir
l'octave originale. Comparer au mix et aux stems avant tout relevé définitif.

## 6. Grilles basse / batterie / accords

### 6.1 Basse — 16 doubles-croches, demi-tons relatifs à D

- Mes. 1–9 : **0 = D** tenu ; 104 pas détectés sur D contre 3 sur D# et 2
  sur C#. Les autres pas sont non voisés : ne pas les remplir de notes inventées.
- Mes. 17–29 : **10 = C**, **2 = E**, passages **7 = A**, **9 = B** ;
  occupation détectée respectivement 120, 42, 9 et 9 pas. Ce sont des durées,
  pas des nombres d'attaques ni une suite d'événements.
- Raccord : `2 → 1 → 0 → 11 → 10 → 9` (E D# D C# C B), puis D.

### 6.2 Batterie — vote d'attaques par mesure

| Fenêtre | Kick détecté | Snare/bruit détecté | Hat détecté |
|---|---|---|---|
| 1–9 | Aucun | Épars, aucune position > 1/8 | Aucun |
| 9–17 | Aucun **identifié** | 4 : 8/8 ; 7,8,9,13,14 : 7/8 ; 5,10 : 6/8 | Épars |
| 17–29 | Aucun identifié | 12 : 2/12 | **4 : 12/12**, 12 : 7/12 |

La machine classe presque tout le passage dense en `snare` ; **ne pas traduire
ces 13 positions en caisse claire acoustique certaine**. Sous-graves et corps
percussif partagés avec la basse rendent le kick indécidable. Le motif de profil
ci-dessous est une réduction jouable, explicitement composée.

### 6.3 Accords — réduction, qualités incertaines

- Ouverture : **pédale D**, détecteur majoritaire D majeur mais D mineur ponctuel.
- Passage dense : D avec appuis A, pas de cadence fonctionnelle démontrée.
- Centre : pôles **C – E – Am**, variante C final ; E/A majeur vs mineur
  instables selon la fenêtre. Éviter d'ériger les étiquettes automatiques en partition.
- Raccord : pôles A – C – G avant D. Les degrés chromatiques de basse sont plus
  sûrs que les qualités des nappes.

## 7. Propositions de données — `nt_sewers`, schéma actuel

**Proposition originale inspirée**, pas transcription à installer ni profil complet.
Deux parties de **8 mesures**, rôles `Open/Free` (8 entrées chacune), par exemple
`sequence = [0,0,1,1,0]`. A garde la pédale D ; B développe les pôles centraux.
Les poids 3:1 sont des choix de diversité, pas des fréquences mesurées.
Les autres banques obligatoires suivent `profiles/isaac_burning/`.

```toml
[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16
steps_per_unit = 2
steps_per_pulse = 4
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 80.0
min_bpm = 72.0
max_bpm = 96.0
[melody]
key_modes = [{ key = 2, mode = "mixolydian", weight = 1 }]
[harmony]
model = "loop"
steps_per_chord = 16
[harmony.parts.A]
kind = "pedal"
degree = 1
[harmony.parts.B]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 10, quality = "Major", bars = 2 },
    { semitones = 2, quality = "Major", bars = 2 },
    { semitones = 7, quality = "Minor", bars = 2 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 10, quality = "Major", bars = 2 },
    { semitones = 2, quality = "Minor", bars = 2 },
    { semitones = 7, quality = "Minor", bars = 2 },
    { semitones = 5, quality = "Major", bars = 2 },
  ] },
]
[accompaniment.bass]
low = 26
high = 37
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 3
reference = "tonic"
notes = [{ step = 0, duration = 32, semitones = 0, velocity = 86, tie = true }]
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 1
reference = "tonic"
notes = [
  { step = 0, duration = 28, semitones = 0, velocity = 86, tie = true },
  { step = 28, duration = 2, semitones = -1, velocity = 70 },
  { step = 30, duration = 2, semitones = 0, velocity = 82, legato = true },
]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 3
reference = "chord_root"
notes = [{ step = 0, duration = 16, semitones = 0, velocity = 84, tie = true }]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 12, semitones = 0, velocity = 84 },
  { step = 12, duration = 4, semitones = 7, velocity = 72 },
]
[accompaniment.chords]
center = 55
max_drift = 6
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 55, tie = true }] }]
[instruments]
melody_program = 52
chords_program = 89
bass_program = 38
percussion_bank = 128
percussion_program = 0
[[odin.Bass.zones]]
when = { tension = [0.65, 1.0], arousal = [0.5, 1.0] }
preset = "Bass Crusher [RM]"
level_db = -5.0
glide_ms = 0.0
[[odin.Bass.zones]]
preset = "Bass Low [RM]"
level_db = -5.0
[[odin.Chords.zones]]
when = { tension = [0.6, 1.0] }
preset = "Moonshade"
level_db = -7.0
[[odin.Chords.zones]]
preset = "Haunt [RM]"
```

Banque `feet.toml` proposée : réductions pondérées, trois densités couvertes.
Pour retrouver le contraste source, une partie calme dédiée peut taire
`Heel/Toe` avec `form.parts[].tracks_off`, plutôt qu'un kick permanent.

```toml
heel_note = 36
toe_note = 38
[[patterns]]
density = 0
weight = 1
hits = [{ step = 4, track = "Toe", note = 42, delta_velocity = -32 }]
[[patterns]]
density = 1
weight = 3
hits = [{ step = 4, track = "Toe", note = 42 }, { step = 12, track = "Toe", note = 42 }]
[[patterns]]
density = 1
weight = 1
hits = [{ step = 0, track = "Heel", delta_velocity = -18 }, { step = 4, track = "Toe", note = 42 }, { step = 12, track = "Toe", note = 42 }]
[[patterns]]
density = 2
weight = 3
hits = [{ step = 4, track = "Toe" }, { step = 7, track = "Toe", delta_velocity = -18 }, { step = 8, track = "Toe" }, { step = 10, track = "Toe", delta_velocity = -20 }, { step = 13, track = "Toe", delta_velocity = -12 }, { step = 14, track = "Toe" }]
[[patterns]]
density = 2
weight = 1
hits = [{ step = 4, track = "Toe" }, { step = 8, track = "Toe" }, { step = 12, track = "Toe" }, { step = 15, track = "Toe", delta_velocity = -18 }]
```

**Manques moteur : aucun bloquant pour cette proposition.** Pédale, boucles
chromatiques, motifs pondérés, notes de percussion par coup, tenue liée,
`tracks_off` et zones émotionnelles existent. Un mode lydien mélodique explicite
n'est pas parmi les modes décrits du moteur ; il ne devient un besoin que si une
validation indépendante confirme cette lecture, actuellement faible. Les offsets
chromatiques permettent déjà les couleurs locales mesurées. Aucun changement
moteur ni profil moteur créé ici.

## Reproduction

Depuis ce worktree ; les chemins source et destination sous droits sont absolus.
Installer les dépendances du labo et `fluidsynth` ; pour demucs, environnement
Python 3.11 séparé (`uv venv --python 3.11 /tmp/nt-demucs` puis
`uv --native-tls pip install --python /tmp/nt-demucs/bin/python demucs==4.1.0 soundfile`).

```bash
ROOT="$HOME/Project/bascanada/harmonium_lab/corpus/nuclear_throne"
PY="$HOME/Project/bascanada/harmonium_lab/.venv/bin/python"
export PYTHONPATH="$PWD/src"
"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$ROOT/manifest.jsonl" --corpus-root "$ROOT" \
  --filter 'id=04_groundwork_of_the_past|31_what_s_that_smell' --context type=zone \
  --grid '{"estimate":false}' --grids references/nt-sewers/grids.json \
  -o references/nt-sewers/measures.json
# Aucun stem / transcription pour 31.
/tmp/nt-demucs/bin/python - <<'PY'
from pathlib import Path
from harmonium_lab.audioref.stems import separate
r = Path.home() / "Project/bascanada/harmonium_lab/corpus/nuclear_throne"
separate([("04_groundwork_of_the_past", r / "tracks/04_groundwork_of_the_past.flac")],
         r / "stems", model="htdemucs", device="cpu", shifts=1)
PY
GRID=$("$PY" -c 'import json; print(json.dumps(json.load(open("references/nt-sewers/grids.json"))["04_groundwork_of_the_past"]))')
"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/04_groundwork_of_the_past.flac" \
  --stems "$ROOT/stems/htdemucs/04_groundwork_of_the_past" \
  --track-id 04_groundwork_of_the_past --grid "$GRID" --tonic D \
  --bass-prog 38 --lead-prog 81 --pad-prog 89 --parts bass drums lead chords \
  --loop integrale:0:47 --loop pedale_D:1:5 --loop transition:9:17 \
  --loop cycle_C:17:21 --loop cycle_C_var:21:25 --loop descente:29:33 --loop reprise:33:37 \
  --soundfont "$HOME/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2" \
  --out "$ROOT/transcriptions"
```

Calage : maximiser la concentration circulaire des attaques du mix autour de
80 BPM, division 4 ; résidu = distance à la subdivision la plus proche. La phase
retenue maximise nouveauté chroma + attaques graves repliées sur la mesure.
Les scores de vérification sont conservés dans `grids.json`. Conventions,
versions et validation commune : [nt-niveaux.md](../nt-niveaux.md).
