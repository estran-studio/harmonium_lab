# Références Scrapyard — *Nuclear Throne* (Jukio Kallio)

Analyse **intégrale, transcriptions comprises**, de **05 Mt. Rubble** (A, 95 s)
et **21 Secret Entrance** (B, 111 s). Les deux variantes sont contrastées :
A percussif et chromatique, B presque entièrement harmonique, mais pulsé.
Méthode G9-G0 des dossiers Isaac Basement et NT Desert.

**Provenance et droits — principe VII.** Jukio Kallio / Vlambeer, OST 2015,
source officielle du manifeste :
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=441s> et
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=2384s>.
Audio, stems et transcriptions sous droits restent exclusivement dans
`~/Project/bascanada/harmonium_lab/corpus/nuclear_throne/` du checkout principal,
jamais dans le worktree. Seuls les trois dérivés de ce dossier sont versionnés.

## 1. Mesures audio, contexte des 20 pistes `type=zone`

`measures.json` est une nouvelle mesure du corpus complet de zones, avec grilles
vérifiées pour les deux pistes Scrapyard. Ne pas mélanger ces valeurs avec les
anciens chiffres Desert obtenus sous d'autres versions de bibliothèques.

| Mesure, mix complet | Mt. Rubble A | Secret Entrance B | Contexte, moyenne ± écart-type |
|---|---:|---:|---:|
| Tempo brut `beat_track`, BPM | 60,1 | 103,4 | 115,4 ± 43,8 |
| Attaques / s | 0,87 | 2,15 | 2,58 ± 1,65 |
| Force tonale | 1,348 | **2,431** | 1,699 ± 0,445 |
| Entropie chroma, bits | 3,575 | **3,387** | 3,511 ± 0,068 |
| Centroïde, Hz | **2 351** | **1 456** | 2 045 ± 739 |
| Rolloff 85 %, Hz | 4 432 | 2 784 | 4 051 ± 1 620 |
| Platitude | 0,04125 | 0,01205 | 0,0285 ± 0,0231 |
| Part harmonique / percussive HPSS | 76,59 / **23,41 %** | **98,39 / 1,61 %** | 87,45 / 12,55 % |
| RMS moyen ± dispersion temporelle | 0,24777 ± 0,07331 | 0,18357 ± 0,10393 | 0,1934 ± 0,0482 entre pistes |

A est plus dense et bruité ; B a la **plus faible part percussive des 20 zones**.
Les 2,15 attaques/s de B proviennent donc surtout des articulations de la nappe,
pas d'une batterie. Le champ `dynamic_range_db` plafonne à 80 pour toutes les
zones : impropre à leur comparaison. A : RMS P90/P10 **5,81 dB** après exclusion
des fenêtres sous 1 % du RMS maximal ; sa faible dispersion et son RMS élevé
sont compatibles avec un mix fortement tenu/compressé, sans prouver un compresseur.

## 2. Tempo, mètre, centres et modes

| Paramètre | Mt. Rubble A | Secret Entrance B |
|---|---|---|
| Grille retenue | **4/4, 119,9881 BPM**, mesure 2,000199 s, 16 pas | **4/4, 105,0553 BPM**, mesure 2,284512 s, 16 pas |
| Calage | Division noire/4 : **R = 0,9555**, résidu médian **4,10 ms**, P90 **9,48 ms** | Division noire/2 : **R = 0,9387**, médiane **7,72 ms**, P90 **20,74 ms** |
| Confiance rythmique | Haute sur 120 et le binaire ; moyenne sur le premier temps | Haute sur la pulsation et le binaire ; moyenne sur le mètre/phase de nappe |
| Premier temps positif | **0,12574 s**, choisi côté kick ; l'auto-calage harmonique à 1,12584 s donne le demi-cycle opposé | **1,12422 s**, phase de nouveauté harmonique |
| Centre | **B**, confiance moyenne : maximum chroma global et racine de 43,8 % des accords ; riff de basse très chromatique | **A / D** : A est la classe globale dominante ; **Dm** revient dans 51,0 % des mesures, dont l'ouverture et la reprise ; centre fonctionnel ambigu |
| Mode local probable | **B phrygien / mineur chromatique**, faible à moyenne : gabarit fixé sur B, 0,857 (marge 0,008) à l'ouverture, 0,868 (0,007) au centre ; passages doriens | Couleur **A mineur harmonique** à l'ouverture (0,879, marge 0,016), **A phrygien** au centre (0,899, marge 0,102) ; compatible avec D mineur et pédale de dominante A |

Le gabarit global libre de A donne **C# phrygien = D lydien**, marge 0 ; celui
de B **C mixolydien = D éolien**, marge 0. Ces égalités entre relatifs ne prouvent
ni C# ni C comme tonique. Sur A, B majeur et mineur alternent dans le détecteur
triades : la qualité est moins sûre que le pôle B. Sur B, éviter de confondre
classe A dominante et tonique A définitivement établie.

Le pic de cohérence à 160 BPM ternaires sur A est une **équivalence de subdivision**
(0,125 s), pas une preuve de 12/8 : la régression des temps donne ~120 BPM, et le
retour d'attaques à 2 s est plus fort qu'à 1,5 s. Le tempo brut 60,1 est le demi-temps.

Mesures 0-based, bornes `[début, fin)`. Les grilles ont une origine théorique
négative : **−1,874459 s** pour A, **−1,160292 s** pour B. La mesure 0 est
partielle, la mesure 1 est le premier temps positif. Les intégrales incluent
l'amorce et la fin partielle ; leurs bornes théoriques hors source sont du silence.

## 3. Structure complète et longueur des unités

### A — Mt. Rubble

La nouveauté chroma ne produit **aucune frontière forte**. Le meilleur score de
répétition longue n'est que **0,0341** à 36 mesures : pas de boucle intégrale
formellement démontrée. Le tableau est un découpage de travail par énergie des
stems et retour du matériau, non une forme certaine déduite de ce seul score.

| Mesures | Source, s | Lecture des stems et du chroma |
|---|---:|---|
| 0, partielle | 0–0,126 | Amorce |
| 1–9 | 0,126–16,127 | Riff chromatique, kit fort ; pôle B installé après F#/F/E |
| 9–17 | 16,127–32,129 | Bm/B majeur et E, variations de timbre/attaques |
| 17–25 | 32,129–48,131 | Même pôle B/E ; batterie descend fortement vers les mes. 22–24 |
| 25–33 | 48,131–64,132 | Passage plus léger, basse souvent non voisée ; déplacement harmonique B–G#–C#–F#–E |
| 33–41 | 64,132–80,134 | Retour progressif du riff, vraiment dense vers la mes. 37 (~72 s), pas reprise littérale à 64 s |
| 41–48 + fin partielle | 80,134–95 | B/E puis coda ; baisse finale de batterie |

Unité utile de transcription : **4 mesures / 8 s**, puis blocs de 8 mesures.
La boucle du profil sera une réduction composée ; le relevé ne justifie pas un
riff original invariant sur toute la piste.

### B — Secret Entrance

| Mesures | Source, s | Matériau / unité |
|---|---:|---|
| 0, partielle | 0–1,124 | Mise en place |
| 1–9 | 1,124–19,400 | Nappe Dm, sortie E/G ; cellule lente de **8 mes.** |
| 9–17 | 19,400–37,676 | Reprise variée Dm, arrivée E ; 8 mes. |
| 17–21 | 37,676–46,814 | Maintien Dm, transition de 4 mes. |
| 21–29 | 46,814–65,091 | Élargissement Bb/C/F/A et passages chromatiques ; 8 mes. |
| 29–37 | 65,091–83,367 | Variante Bb/C/A, retour vers A ; 8 mes. |
| 37–45 | 83,367–101,643 | Retour du début Dm/E/G |
| 45–49 + fin partielle | 101,643–111 | Dm puis extinction |

Reprise à **36 mesures = 82,242 s**, score de répétition **0,2605** sur 13 paires.
Le score à 8 mesures, **0,1032**, confirme une parenté locale plus faible ; il
ne faut pas confondre la cellule de 8 mesures et la reprise longue de 36.

## 4. Instrumentation probable et programmes General MIDI

Inférences numériques depuis `htdemucs` 4.1.0 (CPU, shifts=1), sans validation
auditive humaine. Les quatre noms de stems sont des classes du séparateur,
pas l'identification d'instruments ni de chanteurs.

| Rôle | Évidence stem complet / interprétation probable | GM 0-based, GeneralUser GS | Fichiers Odin d'usine candidats exacts |
|---|---|---|---|
| Basse A | RMS **0,08966**, centroïde **1 450 Hz** : basse saturée riche, très chromatique ; moyenne sur le rôle, faible sur l'octave | **34 Electric Bass (pick)** ou 38 Synth Bass 1 | `Bass Crusher [RM].odin`, `Growly FM Bass [XR].odin`, `Bass Low [RM].odin` |
| Batterie A | RMS **0,10249**, centroïde **3 440 Hz**, platitude 0,07727 : kit sec/bruité, grave et frappe médiane ; moyenne | Canal 10 Standard : **36**, **38**, **42** | `Kick-1 [Photonic].odin`, `Snappy Snare [Projektor].odin`, `HiHat-closed [Photonic].odin` ; candidats comparatifs, pas zones Heel/Toe |
| Accords A | `other` RMS **0,16217**, centroïde **2 206 Hz**, platitude 0,01008 : synthé/nappe médium riche, rôle dominant ; moyenne | **89 Pad 2 (warm)**, 81 Lead 2 (sawtooth) en accords si plus mordant | `Haunt [RM].odin`, `Moonshade.odin` |
| Dessus A | `vocals` RMS 0,02086, pYIN voisé 25,17 % : fragments, pas un solo autonome établi ; faible | **81 Lead 2 (sawtooth)**, bas dans le mix | `Haunt [RM].odin`, `Eerie Pad.odin` |
| Nappe B | `other` RMS **0,19379**, centroïde **1 504 Hz**, platitude **0,00239** ; basse RMS 0,00402, batterie **0,00046** | **89 Pad 2 (warm)**, 91 Pad 4 (choir) | `Eerie Pad.odin`, `Haunt [RM].odin`, `Moonshade.odin` |
| Dessus B | `vocals` RMS 0,01852, voisé 67,06 %, probablement composante harmonique/ligne lente ; moyenne sur les hauteurs, faible sur le timbre | **52 Choir Aahs**, 89 si pas de voix distincte | `Haunt [RM].odin`, `Eerie Pad.odin` |

**B : aucune batterie ni basse indépendante suffisamment établie.** Les faibles
fuites ne doivent pas être transformées en kit MIDI ; son grave harmonique reste
dans la nappe. Pas de Phazzy Organ, de Sausage Bassener rapide, de sifflement,
ni de guitare saturée GM 30. Les presets nommés existent dans le dossier plat
`~/Project/bascanada/odin-presets/` ; ils restent des candidats non écoutés ici.

## 5. Transcriptions, minutages sources et confiance

**14 triplets MIDI + WAV + JSON** dans `$ROOT/transcriptions/` : sept par piste.
Les intégrales couvrent respectivement **0–95** et **0–111 s**, avec remplissage
théorique avant/après. Les autres noms décrivent des fenêtres, pas une certification
de boucles originales parfaitement identiques.

| Préfixe | Suffixe | Mesures | Source théorique, s | Confiance / contenu |
|---|---|---|---:|---|
| `05_mt_rubble_` | `integrale` | 0–49 | −1,874–96,135 | Toute la source, quatre rôles ; moyenne sur les pôles, faible sur les traits |
| idem | `riff_A` | 1–5 | 0,126–8,127 | Riff chromatique et kit, moyenne |
| idem | `variante_A` | 9–13 | 16,127–24,128 | B/E, moyenne |
| idem | `centre` | 17–25 | 32,129–48,131 | Affaiblissement du kit, moyenne |
| idem | `pont` | 25–33 | 48,131–64,132 | Harmonie mobile, basse lacunaire ; faible sur le détail |
| idem | `reprise` | 33–41 | 64,132–80,134 | Retour progressif du matériau, moyenne |
| idem | `coda` | 41–49 | 80,134–96,135 | Dernier passage et extinction, moyenne |
| `21_secret_entrance_` | `integrale` | 0–50 | −1,160–113,065 | Toute la source, **lead + accords seulement**, moyenne |
| idem | `nappe_A` | 1–9 | 1,124–19,400 | Dm et sortie E/G, moyenne–haute sur les racines |
| idem | `nappe_A_var` | 9–17 | 19,400–37,676 | Dm, variante, moyenne |
| idem | `transition` | 17–21 | 37,676–46,814 | Dm, moyenne |
| idem | `nappe_B` | 21–29 | 46,814–65,091 | Bb/C/F/A, moyenne sur les pôles, faible sur les accords intermédiaires |
| idem | `nappe_B_var` | 29–37 | 65,091–83,367 | Variante du centre, moyenne |
| idem | `reprise` | 37–45 | 83,367–101,643 | Dm/E/G, moyenne–haute |

Indicateurs globaux : A basse voisée **0,5985**, lead **0,2517**, accords score
**0,807**, 167 attaques batterie, marge **0,555**, **25,7 %** de marges < 0,15.
B lead voisé **0,6706**, accords score **0,877**. Ces scores de modèle ne sont pas
des probabilités de justesse ni des scores locaux par extrait.

**Correction labo nécessaire au relevé.** Le lissage d'octave accumulait les
transpositions sur le riff A jusqu'à **MIDI 352**, faisant échouer l'export.
`audioref.transcribe` borne désormais les déplacements d'octave au registre pYIN
(dérivé de `fmin/fmax`), tout en gardant la classe de hauteur ; aucune note n'est
clampée à 127. Les quatre intégrales et tous leurs extraits ont été régénérés
après correction. L'octave réelle et les glissandos restent à valider à l'oreille.

## 6. Grilles détaillées : basse, batterie, accords

### 6.1 Basse

A, grille **16 pas/mesure**, degrés chromatiques relatifs à B :
**0 B**, **1 C**, **3 D**, **5 E**, **6 F**, **7 F#**, **8 G**, **9 G#**, **10 A**.
Le riff est chromatique, pas une basse I–V : sur les mes. 1–9, les occupations
détectées dominantes sont A 17 pas, E 15, G et G# 14 chacun, F 12, B 10.
La chaîne de notes originale détaillée reste dans le sidecar hors dépôt.
Les positions et petits glissandos ne sont pas assez fiables pour figer une
unique mesure « exacte ». Pour le profil : notes courtes, retours B/E et voisins
C/A ; les variantes pondérées ci-dessous sont composées, non recopiées.

B : **pas de ligne de basse indépendante établie** ; grille vide sur Bass.
Les racines de la nappe sont réalisées sur Chords, sans doubler tout au grave.

### 6.2 Batterie A, vote sur mes. 1–9

| Position, 16 pas | Kick identifié | Snare identifiée |
|---|---:|---:|
| 0 | **7/8** | — |
| 8 | **5/8** | **3/8** |
| 4 / 6 | Kick 1/8 sur 4 | Snare 1/8 sur 6 |

L'attaque de milieu de mesure est stable mais sa classe est ambiguë : le mélange
kick/snare se partage entre les deux règles spectrales. Pas de charleston continu
fiablement identifié. Au pont, la majorité des événements deviennent `snare`
bruitée et le kick disparaît du détecteur : ne pas conserver le groove plein.
B : **grille batterie vide** ; `tracks_off = ["Heel", "Toe", "Bass"]` dans sa
partie de forme, pas une batterie extraite des fuites demucs.

### 6.3 Accords / pôles par mesure

Qualités automatiques majeur/mineur seulement, confiance inférieure aux racines :

- A, mes. 5–9 : **B – B – B – E** ; mes. 17–21 : **B – B – E – B**.
- A, pont 25–33 : **B – B – G# – C# – F# – E – E – F** ; le dernier F
  et les tierces sont particulièrement incertains dans la texture bruitée.
- B, ouverture 1–9 : **Dm ×5 – E – G – Em** ; variante suivante Dm ×5,
  D/C/E à l'approche du centre.
- B, centre 21–29 : **Bb – C – C#m – F – Bb – Bb – Dm – A**.
  C#m est une étiquette de meilleure triade, pas une modulation établie.
- B, retour 37–45 : **Dm ×5 – E – G – A**.

## 7. Propositions de données — profil `nt_scrapyard`

Réduction originale, **pas un profil complet ni une transcription sous droits**.
Deux parties **A/B de 8 mesures**, par exemple `sequence = [0,0,1,0]`,
8 rôles `Open/Free` par partie. B porte
`tracks_off = ["Bass", "Heel", "Toe"]` et une nappe plus douce ; aucune banque
Bass ne doit cibler B. Les poids 3:1 sont proposés, non appris du corpus.

```toml
[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16
steps_per_unit = 2
steps_per_pulse = 4
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 120.0
min_bpm = 100.0
max_bpm = 132.0
[melody]
key_modes = [{ key = 11, mode = "phrygian", weight = 1 }]
[harmony]
model = "loop"
steps_per_chord = 16
[harmony.parts.A]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 5, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 8, quality = "Major", bars = 2 },
    { semitones = 5, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
  ] },
]
# D/E/G/Bb/A exprimés relativement à la tonique globale B : 3/5/8/11/10.
[harmony.parts.B]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 3, quality = "Minor", bars = 4 },
    { semitones = 5, quality = "Major", bars = 1 },
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 11, quality = "Major", bars = 2 },
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 3, quality = "Minor", bars = 2 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
]
[accompaniment.bass]
low = 23
high = 34
[[accompaniment.bass.motifs]]
part = "A"
bars = 1
weight = 3
reference = "chord_root"
notes = [
  { step = 0, duration = 3, semitones = 0, velocity = 96 },
  { step = 4, duration = 2, semitones = 1, velocity = 82 },
  { step = 6, duration = 2, semitones = 0, velocity = 88 },
  { step = 8, duration = 4, semitones = -2, velocity = 92 },
  { step = 12, duration = 2, semitones = 0, velocity = 86 },
  { step = 14, duration = 2, semitones = 7, velocity = 80 },
]
[[accompaniment.bass.motifs]]
part = "A"
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 6, semitones = 0, velocity = 96 },
  { step = 6, duration = 2, semitones = -1, velocity = 80 },
  { step = 8, duration = 4, semitones = 0, velocity = 90 },
  { step = 12, duration = 2, semitones = 5, velocity = 82 },
  { step = 14, duration = 2, semitones = 6, velocity = 78 },
]
[accompaniment.chords]
center = 58
max_drift = 6
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 54, tie = true }] }]
[instruments]
melody_program = 52
chords_program = 89
bass_program = 34
percussion_bank = 128
percussion_program = 0
[[odin.Bass.zones]]
when = { tension = [0.65, 1.0] }
preset = "Growly FM Bass [XR]"
level_db = -6.0
glide_ms = 0.0
[[odin.Bass.zones]]
preset = "Bass Crusher [RM]"
level_db = -5.0
glide_ms = 0.0
[[odin.Chords.zones]]
when = { arousal = [0.0, 0.35] }
preset = "Eerie Pad"
level_db = -6.0
[[odin.Chords.zones]]
when = { tension = [0.6, 1.0] }
preset = "Moonshade"
level_db = -7.0
[[odin.Chords.zones]]
preset = "Haunt [RM]"
```

`feet.toml`, banque pondérée ; le kick/snare de milieu de mesure est une
interprétation jouable du coup ambigu, pas une certitude de transcription.

```toml
heel_note = 36
toe_note = 38
[[patterns]]
density = 0
weight = 1
hits = [{ step = 0, track = "Heel", delta_velocity = -12 }]
[[patterns]]
density = 1
weight = 3
hits = [{ step = 0, track = "Heel" }, { step = 8, track = "Toe" }]
[[patterns]]
density = 1
weight = 1
hits = [{ step = 0, track = "Heel" }, { step = 6, track = "Heel", delta_velocity = -18 }, { step = 8, track = "Toe" }]
[[patterns]]
density = 2
weight = 3
hits = [{ step = 0, track = "Heel" }, { step = 4, track = "Toe", note = 42, delta_velocity = -28 }, { step = 8, track = "Toe" }, { step = 12, track = "Toe", note = 42, delta_velocity = -28 }]
[[patterns]]
density = 2
weight = 1
hits = [{ step = 0, track = "Heel" }, { step = 6, track = "Heel", delta_velocity = -18 }, { step = 8, track = "Toe" }, { step = 14, track = "Heel", delta_velocity = -16 }]
```

Chaque alternative harmonique totalise exactement 8 mesures. La graine fixe
les choix par partie/air ; les reprises gardent leurs choix, sans utiliser
l'ancien champ `chords` direct. Zones Odin ordonnées, dernier défaut sans `when` ;
Heel/Toe demeurent SoundFont. Les sections obligatoires non illustrées suivent
`profiles/isaac_burning/`, pas le vieux schéma des premiers READMEs labo.

**Manques moteur : aucun bloquant pour un profil inspiré à tempo paramétrable.**
Les changements chromatiques, nappes liées, motifs et pieds pondérés, silences
par partie et timbres par émotion existent. **Limite de fidélité explicite** :
A est à 120 et B à 105,055 BPM ; un profil joué à tempo constant n'est pas leur
montage exact. Le schéma documenté n'a pas de tempo automatique par partie :
pour cette succession précise, il faut un pilotage de tempo par l'hôte ou une
extension de données de forme. Aucun tel pilotage n'est simulé ici. Les zones
émotionnelles ne se sélectionnent pas automatiquement d'après le nom A/B.

## Reproduction

Labo et `fluidsynth` installés. Pour la séparation utilisée : Python 3.11,
`uv venv --python 3.11 /tmp/nt-demucs` puis
`uv --native-tls pip install --python /tmp/nt-demucs/bin/python demucs==4.1.0 soundfile`.

```bash
ROOT="$HOME/Project/bascanada/harmonium_lab/corpus/nuclear_throne"
PY="$HOME/Project/bascanada/harmonium_lab/.venv/bin/python"
export PYTHONPATH="$PWD/src"
"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$ROOT/manifest.jsonl" --corpus-root "$ROOT" \
  --filter 'id=05_mt_rubble|21_secret_entrance' --context type=zone \
  --grid '{"estimate":false}' --grids references/nt-scrapyard/grids.json \
  -o references/nt-scrapyard/measures.json
/tmp/nt-demucs/bin/python - <<'PY'
from pathlib import Path
from harmonium_lab.audioref.stems import separate
r = Path.home() / "Project/bascanada/harmonium_lab/corpus/nuclear_throne"
ids = ["05_mt_rubble", "21_secret_entrance"]
separate([(i, r / "tracks" / (i + ".flac")) for i in ids],
         r / "stems", model="htdemucs", device="cpu", shifts=1)
PY
GRID=$("$PY" -c 'import json; print(json.dumps(json.load(open("references/nt-scrapyard/grids.json"))["05_mt_rubble"]))')
"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/05_mt_rubble.flac" --stems "$ROOT/stems/htdemucs/05_mt_rubble" \
  --track-id 05_mt_rubble --grid "$GRID" --tonic B \
  --bass-prog 34 --lead-prog 81 --pad-prog 89 --parts bass drums lead chords \
  --loop integrale:0:49 --loop riff_A:1:5 --loop variante_A:9:13 \
  --loop centre:17:25 --loop pont:25:33 --loop reprise:33:41 --loop coda:41:49 \
  --soundfont "$HOME/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2" \
  --out "$ROOT/transcriptions"
GRID=$("$PY" -c 'import json; print(json.dumps(json.load(open("references/nt-scrapyard/grids.json"))["21_secret_entrance"]))')
"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/21_secret_entrance.flac" --stems "$ROOT/stems/htdemucs/21_secret_entrance" \
  --track-id 21_secret_entrance --grid "$GRID" --tonic A \
  --lead-prog 52 --pad-prog 89 --parts lead chords \
  --loop integrale:0:50 --loop nappe_A:1:9 --loop nappe_A_var:9:17 \
  --loop transition:17:21 --loop nappe_B:21:29 --loop nappe_B_var:29:37 --loop reprise:37:45 \
  --soundfont "$HOME/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2" \
  --out "$ROOT/transcriptions"
```

Calage : maximisation locale de la concentration circulaire des attaques sur
noire/4 près de 120, noire/2 près de 105,05 ; résidus sur ces subdivisions,
pas sur les seuls temps forts. Convention de phase, versions et validation
commune : [nt-niveaux.md](../nt-niveaux.md).
