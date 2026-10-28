# Références Désert — *Nuclear Throne* (Jukio Kallio)

Analyse de la zone désert de *Nuclear Throne* (tâche G0 de la phase 014) :
mesures audio (`measures.json`), structure, instrumentation, boucles
transcrites (hors dépôt) et propositions de données pour G2 (harmonie en
boucle / pédale), G3 (basse motivique) et G7 (profil `nt_desert`) ; distance
du profil `nt_desert` au corpus (M1) en §8.

**Provenance et droits (principe VII).** Pistes 02 *Fläshyn* (Desert A,
87 s) et 19 *A Way* (Desert B, 145 s) de *Nuclear Throne OST*, composées
par Jukio Kallio (Vlambeer, 2015). Enregistrements, stems et transcriptions
MIDI restent hors dépôt, dans le checkout principal gitignoré :

- audio : `corpus/nuclear_throne/tracks/02_flashyn.flac`, `19_a_way.flac` ;
- stems (demucs `htdemucs`) : `corpus/nuclear_throne/stems/htdemucs/<id>/` ;
- boucles MIDI + WAV + JSON : `corpus/nuclear_throne/transcriptions/`.

Seuls ce compte rendu et les dérivés (`measures.json`, `grids.json`,
`banque-mesures.json`, `banque.md`, `distance-nt_desert.json`) sont versionnés.

---

## 1. Mesures audio et mise en contexte (20 pistes `zone`)

Sortie complète : `references/nt-desert/measures.json` (reproduite par
`harmonium-lab audioref-measures`). Les deux pistes du désert occupent deux
pôles opposés du corpus de zone :

| Mesure | *Fläshyn* (Desert A) | *A Way* (Desert B) | Contexte 20 pistes `zone` (moy. ± é.-t., [min..max]) |
|---|---:|---:|---:|
| Tempo `beat_track` brut (BPM) | 69,8 *(sous-harmonique ÷2 de 140)* | 47,0 *(pas de pulsation : nappe)* | 115,4 ± 43,8 [47,0..215,3] |
| Taux d'attaques (/s) | 0,62 | 1,44 *(bruit de nappe)* | 2,42 ± 1,03 [0,62..4,50] |
| Force tonale (`key_strength`) | 1,41 (G# dominant) | **2,99** (pédale A écrasante) | 1,92 ± 0,43 [1,37..2,99] |
| Entropie de chroma (bits) | 3,56 (riche, chromatique) | 3,34 (concentrée sur A) | 3,47 ± 0,08 [3,27..3,57] |
| Centroïde spectral (Hz) | **3 093** (brillant, saturé) | **1 518** (sombre, filtré) | 2 045 ± 739 [827..3 736] |
| Rolloff spectral 85 % (Hz) | 6 309 | 3 011 | 4 157 ± 1 644 [1 399..7 556] |
| Platitude spectrale | 0,0567 | 0,0122 | 0,0279 ± 0,0236 |
| RMS moyen | 0,231 | 0,159 | 0,183 ± 0,052 |
| Part harmonique / percussive | 80,7 % / **19,3 %** | **95,2 %** / 4,8 % | 87,5 % / 12,5 % (± 11,0 %) |

Constat : *Fläshyn* est une boucle d'action percussive et brillante
(+1,4 σ de centroïde, +0,6 σ de part percussive) ; *A Way* est une nappe
ambiante quasi sans percussion (95,2 % harmonique, maximum de `key_strength`
du corpus à 2,99 grâce au bourdon de la).

---

## 2. Tempo, mètre, tonalité et mode

| Paramètre | *Fläshyn* (Desert A) | *A Way* (Desert B) | Confiance |
|---|---|---|---|
| Pulsation | **140,0 BPM** (`beat_s = 0,4286 s`, résidu 62 ms) | Aucune pulsation périodique (autocorr. enveloppe < 0,05 entre 0,25 s et 4 s) ; fenêtre d'analyse de 2,0 s (`quarter_bpm = 120`) | Haute (A) / Haute sur l'absence de battue (B) |
| Division (tatum) | **Ternaire** : 3 croches par pulsation (`tatum_s = 0,1429 s`, cohérence $R_3 = 0,889 \gg R_2 = 0,254$) | Sans objet (tenues) | Très haute ($R_3 = 0,89$) |
| Mètre | **12/8** (4 pulsations ternaires par mesure, `bar_s = 1,7143 s`, autocorr. pic à 4 temps = 0,738 ; équivalent : 4/4 shuffle à 140 BPM) | Non mesuré (blocs lents de ~8 s) | Haute |
| Premier temps | `origin_s = 0,553 s` (après levée de batterie de 0,55 s) | `0,0 s` | Moyenne (levée : valider à l'oreille si bar 1 = t=0,55 s ou t=2,27 s) |
| Centre(s) et mode | **Bimodal / pédales phrygiennes** : section A1 sur pédale **G#** (avec A♮ = $\flat 2$, couleur **G# phrygien**), section A2 sur **D** avec **D#** ($\flat 2$, **D phrygien** / locrien), pont sur **C / E / A / B**, section B alterne **G** et **G#** toutes les 2 mesures. Le gabarit global donne C# mineur harmonique (G# = dominante, marge 0,008 : ambigu). | **A phrygien / éolien sur bourdon A** : 0–64 s et 128–145 s = pédale **A** (+ quinte D/E et voisin **G#** = $7$ majeur ou $\flat 2$ inversé) ; 64–128 s = mouvement lent **A – C – B – G#**. | Haute sur les pédales (G#, D, A) et le demi-ton $\flat 2$ ; **à valider à l'oreille** : G# phrygien vs C# mineur avec pédale de dominante |

**Conclusion pour G1 (modes).** Les deux pistes reposent sur le **demi-ton
au-dessus de la pédale** (G#–A et D–D# dans *Fläshyn*, G#–A dans *A Way*) :
c'est la signature **phrygienne** ($\flat 2$), déjà prévue en G1.

---

## 3. Structure et longueur des boucles

### *Fläshyn* — 50 mesures de 12/8 (1,714 s/mesure, 87 s)

L'auto-similarité par mesure et l'énergie du stem batterie découpent
exactement **5 sections** en arche, avec reprise littérale de l'ouverture à
la mesure 40 ($r = 0,99$ entre mes. 0–9 et mes. 40–49) :

| Section | Mesures | Minutage | Batterie (RMS rel.) | Basse | Harmonie / matériau | Longueur de boucle |
|---|---|---|---:|---|---|---|
| **A1 — Pédale G#** | 0–7 (8 mes.) | 0,55–14,27 s | 0,47 → 1,00 | Pédale G#1 tenue + relance chromatique D–F–F#–G–G# (mes. 0 et 4) | Bourdon G# (+ D#, A♮) ; chute F–F#–C#–D aux mes. 6–7 | **4 mesures** (×2, avec fill aux mes. 6–7) |
| **A2 — Riff D/D#** | 8–15 (8 mes.) | 14,27–27,98 s | 0,72 → 0,56 | Riff motivique grave D1–D#1 ($\flat 2$) en croches/doubles | Pédale D + D# + A | **2 ou 4 mesures** (×4 ou ×2) |
| **Pont — Nappes (breakdown)** | 16–31 (16 mes.) | 27,98–55,41 s | **0,00** (silence total mes. 17–30) | Absente (quelques notes E1 aux mes. 18–19, 25) | Boucle d'accords tenus : **C – C/E – E – E – F/A – B – C – C** (mes. 16–23, 8 mes.) répétée **F – C/E – E – E – F – B – C# – C#** (mes. 24–31) | **8 mesures** (×2, sans batterie ni basse) |
| **B — Alternance G / G#** | 32–39 (8 mes.) | 55,41–69,12 s | 0,07 → 0,48 (crescendo) | Absente du stem `bass` (médiums seuls) | Alternance de 2 mesures : **G (2 mes.) – G# (2 mes.) – G (2 mes.) – G# (2 mes.)** | **4 mesures** (2 mes. G + 2 mes. G#, ×2) |
| **A1' — Reprise** | 40–49 (10 mes.) | 69,12–86,27 s | 0,58 → 0,74 puis coupure mes. 48–49 | Identique à A1 (pédale G#1 mes. 40–46, riff D1–D#1 mes. 48–49) | Identique à mes. 0–9 | **4 mesures** + coda 2 mes. |

### *A Way* — 145 s, forme ternaire A – B – A' sans battue

Matrice d'auto-similarité par fenêtres de 8 s ($r \ge 0,98$ sur tout A et
entre A et A') :

| Section | Minutage | Contenu | Longueur d'unité |
|---|---|---|---|
| **A — Bourdon A** | 0–64 s (64 s) | Nappe tenue sur **A** (chroma A = 0,97–1,00, secondaire D = 0,40 et G# = 0,30) ; motifs épars d'harmoniques aiguës (F5–G5) à 16–24 s et 32–64 s | Pédale continue (respiration de **8 s ≈ 4 mesures** à 120 BPM) |
| **B — Mouvement harmonique** | 64–128 s (64 s) | Décrochage de la pédale : **A → C → B → G# → C → A** par paliers de 8 à 16 s ; motif mélodique grave/médium (registre E3–G3) | Boucle lente de **8 ou 16 mesures** |
| **A' — Retour au bourdon** | 128–145 s (17 s) | Retour exact au bourdon **A** ($r = 1,00$ avec 8–24 s) | Pédale continue |

---

## 4. Instrumentation probable et programmes General MIDI

| Rôle | Timbre dans l'original | Piste où il domine | Programme General MIDI (0-indexé, GeneralUser GS) |
|---|---|---|---|
| **Basse** | Basse synthé saturée / guitare basse fuzz, fondamentale ~36–73 Hz (D1–G#1) très riche en harmoniques 2 et 3 | *Fläshyn* A1, A2, A1' | **38** *Synth Bass 1* (ou **39** *Synth Bass 2* ; **30** *Distortion Guitar* à l'octave basse pour le grain fuzz) |
| **Batterie** | Kit rock sec et compressé (kick lourd sous 80 Hz, snare claquante 200–3 000 Hz, charleston/cymbale très brillante > 5 kHz) | *Fläshyn* A1, A2, B, A1' | Canal 10 GM Standard Kit : **36** *Bass Drum 1*, **38** *Acoustic Snare*, **42** *Closed Hi-Hat* (ou **46** *Open Hi-Hat*) |
| **Nappe / accords** | Pad synthé chaud + guitare/synthé saturé tenu sans attaque | *Fläshyn* pont (mes. 16–31) et B ; *A Way* tout du long | **88** *Pad 1 (new age)* ou **89** *Pad 2 (warm)* (**95** *Pad 8 (sweep)* pour *A Way*) |
| **Motif / lead** | Sifflement / synthé monophonique aigu réverbéré (style western d'Ennio Morricone) | *A Way* (entrées à 16 s, 36 s, 64–120 s) ; bribes dans *Fläshyn* pont | **81** *Lead 2 (sawtooth)* ou **75** *Pan Flute* / **78** *Whistle* |

---

## 5. Transcriptions, minutages sources et confiance

Les 10 boucles MIDI et leurs rendus WAV (`fluidsynth` + `GeneralUser-GS.sf2`,
normalisés au pic 0,125 comme `trad-render`) sont dans
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/nuclear_throne/transcriptions/` :

| Fichier (`.mid` / `.wav` / `.json`) | Piste | Mesures | Minutage source | Contenu | Confiance | À valider à l'oreille |
|---|---|---:|---:|---|---|---|
| `02_flashyn_bass_pedal` | *Fläshyn* | 1–5 (4 mes.) | **2,27–9,12 s** | Pédale G#1 tenue + relance chromatique D–E–F#–G–G# (mes. 4) | **Moyenne** (`voiced = 0,45`) | Octave réelle (G#1 vs G#2 : la distorsion renforce l'harmonique 2) ; rythme exact de la relance mes. 4 |
| `02_flashyn_bass_riff_D` | *Fläshyn* | 9–13 (4 mes.) | **15,98–22,84 s** | Riff motivique D1–D#1 ($\flat 2$) + saut G1–G#1 | **Moyenne** | Frontières exactes des doubles-croches D1/D#1 (pyin lisse les attaques rapides) |
| `02_flashyn_drums_groove` | *Fläshyn* | 1–5 (4 mes.) | **2,27–9,12 s** | Groove 12/8 principal (kick/snare) | **Haute** sur les positions, **moyenne** sur kick vs snare au temps 1 (`margin = 0,38`) | Coup du temps 1 : kick + cymbale simultanés parfois classés snare ; charleston continu masqué par le mix |
| `02_flashyn_drums_B` | *Fläshyn* | 32–36 (4 mes.) | **55,41–62,27 s** | Groove de reprise en crescendo (section B) | **Moyenne** | Niveau plus faible, fills de tom |
| `02_flashyn_chords_intro` | *Fläshyn* | 1–9 (8 mes.) | **2,27–15,98 s** | Pédale G# (mes. 1–5), chute F–C# (mes. 6–7), entrée D (mes. 8) | **Haute** (`score = 0,68`) | Qualité majeure/mineure sur le bourdon (quinte seule sans tierce claire) |
| `02_flashyn_chords_B` | *Fläshyn* | 32–40 (8 mes.) | **55,41–69,12 s** | Alternance 2 mes. G / 2 mes. G# (×2) | **Très haute** (`score = 0,72`) | Renversement exact (triade C/G vs G majeur) |
| `02_flashyn_full_loop_A` | *Fläshyn* | 1–5 (4 mes.) | **2,27–9,12 s** | Basse + batterie + nappe superposées (boucle A1 complète) | **Moyenne–haute** | Cohérence d'ensemble face à l'original 2,27–9,12 s |
| `19_a_way_pedal_A` | *A Way* | 0–4 (4 mes.) | **0,00–8,00 s** | Bourdon A mineur tenu | **Très haute** (`score = 0,80`, `pedal_share = 0,68`) | Ras : bourdon statique |
| `19_a_way_chords_B` | *A Way* | 32–48 (16 mes.) | **64,00–96,00 s** | Décrochage harmonique A → C → B | **Haute** (`score = 0,69`) | Instants exacts de fondu entre accords (pas d'attaque franche) |
| `19_a_way_lead_motif` | *A Way* | 36–40 (4 mes.) | **72,00–80,00 s** | Motif grave/médium extrait du stem `vocals` | **Faible** (`voiced_ratio` utile ~7 %) | Le stem `vocals` capte des harmoniques de nappe autant qu'un vrai lead : vérifier à l'oreille à 72–80 s (et à 16–24 s, 36–44 s) s'il s'agit d'un motif mélodique distinct ou d'une résonance de filtre |

---

## 6. Grilles détaillées (basse, batterie, accords)

### 6.1 Riff de basse (*Fläshyn*, grille de 24 sous-divisions par mesure de 12/8)

En 12/8, chaque pulsation ternaire vaut 3 croches = **6 doubles-croches**
(`step = 71,4 ms`), soit **24 doubles-croches par mesure** (4 temps × 6).
Degrés mesurés en demi-tons au-dessus de la tonique locale :

- **Motif A1 — Pédale G# et relance chromatique** (mes. 0–5, tonique locale **G# = 0**) :
  - Mes. 0 (levée + attaque) : montée chromatique `D(6) – D#(7) – F(9) – F#(10) – G(11)` sur les positions 12–23, puis tenue sur **G#(0)** dès le temps 1 de la mesure 1.
  - Mes. 1–3 : **pédale tenue sur G#(0)** (3 mesures pleines, ré-attaquée sur le temps 1).
  - Mes. 4 : même **relance chromatique** vers la fondamentale :

```
Temps (12/8) : | 1 . . . . . | 2 . . . . . | 3 . . . . . | 4 . . . . . |
Pos (0..23)  :   0 1 2 3 4 5   6 7 8 9 1011 121314151617 181920212223
Degré / G#   :   6 6 6 6 6 8  10111111 0  0  0 0 0 0 0 0  0 0 0 0 0 0
Note         :   D - - - - E  F# G - - G# -  (tenue sur G# → mes. 5)
```

- **Motif A2 — Ostinato phrygien D / D#** (mes. 8–15, tonique locale **D = 0**, **D# = $\flat 2$ = 1**, **G# = $\sharp 4$ = 6**) :
  - Alternance serrée entre la fondamentale **0 (D1)** et le demi-ton supérieur **1 (D#1)**, ponctuée sur la 12e mesure par un saut à la quarte augmentée / quinte **5–6 (G1–G#1)** :

```
Temps (12/8) : | 1 . . . . . | 2 . . . . . | 3 . . . . . | 4 . . . . . |
Pos (0..23)  :   0 1 2 3 4 5   6 7 8 9 1011 121314151617 181920212223
Mes. 9 (ost.):   0 0 0 0 1 0   0 0 1 1  1 0  0 0 0 0 0 1  0 0 0 0 0 0   (D / D# = 0 / b2)
Mes. 12 (rel):   0 0 0 0 0 1   1 3 5 5  5 6  6 0 0 1 1 0  0 2 0 0 0 0   (montée D–D#–F–G–G# puis retour D)
```

### 6.2 Pattern de batterie (*Fläshyn*, mes. 1–7, vote sur 7 mesures)

Dans chaque pulsation ternaire (6 positions `0..5`), seules les positions
**0** (temps) et **2** (2e croche du triolet) portent des attaques
($R_3 = 0,89$) ; les positions **4** (dernière croche du triolet) portent la
levée de grosse caisse vers le temps suivant :

```
Temps (12/8) : | 1  .  .  .  .  . | 2  .  .  .  .  . | 3  .  .  .  .  . | 4  .  .  .  .  . |
Croche triol.: | 1     2     3    | 1     2     3    | 1     2     3    | 1     2     3    |
Pos (0..23)  :   0  1  2  3  4  5   6  7  8  9 10 11  12 13 14 15 16 17  18 19 20 21 22 23
Kick  (GM 36):   X  .  .  .  .  .   .  .  X  .  .  .   .  .  .  .  x  .   .  .  X  .  .  .
Snare (GM 38):   .  .  X  .  .  .   .  .  .  .  X  .   .  .  X  .  .  .   .  .  .  .  x  .
Hat   (GM 42):   x  .  x  .  x  .   x  .  x  .  x  .   x  .  x  .  x  .   x  .  x  .  X  .
```

(`X` = coup présent dans $\ge 6/7$ mesures ; `x` = variante / fill ou
charleston de pulsation à confirmer à l'oreille). C'est un groove **shuffle
lourd** où la caisse claire répond sur la 2e croche du triolet (pos. 2, 10,
14) et la grosse caisse pousse sur les pos. 0, 8 et 20.

### 6.3 Boucles d'accords et pédales par mesure

- ***Fläshyn* — A1 (mes. 1–8)** : pédale `G#` (mes. 1–5) → cadence chromatique `F` (mes. 6) → `C#/D` (mes. 7) → `D` (mes. 8).
- ***Fläshyn* — A2 (mes. 8–15)** : pédale `D` (+ seconde mineure `D#` et quinte `A` superposées, 8 mesures).
- ***Fläshyn* — Pont (mes. 16–31, sans batterie ni basse)** : deux boucles de 8 mesures :
  - mes. 16–23 : `| C | C | E | E | A (ou F) | B | C | C |` ;
  - mes. 24–31 : `| F | C | E | E | F | B | C# | C# |` (prépare le retour à G#/G).
- ***Fläshyn* — Section B (mes. 32–39)** : boucle de **4 mesures** répétée 2 fois : `| G | G | G# | G# |` (mouvement de demi-ton phrygien I – $\flat$II sur G).
- ***A Way* — Section A (0–64 s) et A' (128–145 s)** : pédale statique `| Am | Am | Am | Am |` (avec voisin `G#` dans la nappe).
- ***A Way* — Section B (64–128 s, par paliers de 4 mesures à 120 BPM)** : `| Am (4 mes.) | C (8 mes.) | Am (4 mes.) | G#m/E (4 mes.) | C (8 mes.) | Am (4 mes.) |`.

---

## 7. Propositions concrètes de données pour G2, G3 et G7

Ces propositions décrivent uniquement des **structures de données de profil**
(aucun code moteur ici) et sont conçues pour servir aussi à d'autres styles
(principe VIII : bourdon trad, ostinato d'Isaac, etc.).

### 7.1 Pour G2 — Modèle d'harmonie `loop` / `pedal`

Dans `HarmonyConfig` (aujourd'hui limité à `trad_functional`, `jazz_functional`,
`none`), ajouter un modèle piloté par données où chaque partie de forme
choisit soit une **pédale**, soit une **boucle fixe d'accords** avec durée
en mesures :

```toml
[harmony]
model = "loop"              # nouveau modèle générique (sert aussi aux bourdons trad et à Isaac)
default_bars_per_chord = 2  # rythme harmonique par défaut

# Pédale : un seul degré tenu sur toute la partie, avec note voisine optionnelle (b2 phrygien)
[harmony.parts.A1]
kind = "pedal"
degree = 0                  # I (tonique de la partie)
neighbor_semitones = 1      # b2 phrygien (G# + A, ou D + D#)
turnaround = [              # optionnel : 2 dernières mesures de la boucle de 8
  { degree = 9, quality = "maj", bars = 1 },
  { degree = 5, quality = "maj", bars = 1 },
]

# Boucle d'accords fixe : liste (degré en demi-tons ou degré modal, qualité, durée en mesures)
[harmony.parts.B]
kind = "chord_loop"
chords = [
  { semitones = 0, quality = "maj", bars = 2 },   # ex. G pendant 2 mesures
  { semitones = 1, quality = "maj", bars = 2 },   # ex. G# (bII phrygien) pendant 2 mesures
]

[harmony.parts.Bridge]
kind = "chord_loop"
chords = [
  { semitones = 4, quality = "maj", bars = 2 },   # C (2 mes.)
  { semitones = 8, quality = "maj", bars = 2 },   # E (2 mes.)
  { semitones = 9, quality = "maj", bars = 1 },   # F (1 mes.)
  { semitones = 3, quality = "maj", bars = 1 },   # B (1 mes.)
  { semitones = 4, quality = "maj", bars = 2 },   # C (2 mes.)
]
```

**Réemploi hors NT (principe VIII)** : un reel ou une complainte acadienne à
bourdon de quinte utilise `kind = "pedal", degree = 0` ; une chaconne ou les
boucles de 4 accords d'*Isaac* (`i – VI – III – VII`) utilisent
`kind = "chord_loop"`.

### 7.2 Pour G3 — Basse motivique (`bass_cells`)

Au lieu de coups de basse asservis à `Root`/`Fifth`, permettre à une partie
de puiser un **motif de basse d'une ou deux mesures** sur la grille de
tatums/doubles-croches, exprimé en **demi-tons relatifs à la fondamentale
courante** (0 = fondamentale, 1 = $\flat 2$, 7 = quinte, etc.) et `octave` :

```toml
[[bass_cells]]
id = "pedal_hold_pickup"
part = "A1"
bars = 4
subdivisions_per_bar = 24   # 12/8 en doubles-croches (ou 12 en croches de triolet)
# (start_sub, len_sub, semitones_from_root, octave, velocity)
notes = [
  { start = 0,  len = 72, semitones = 0,  octave = 1, vel = 95 },  # 3 mesures tenues sur la fondamentale
  { start = 72, len = 6,  semitones = 6,  octave = 1, vel = 85 },  # relance : b5 (D sur G#)
  { start = 78, len = 3,  semitones = 8,  octave = 1, vel = 85 },  # b6
  { start = 81, len = 3,  semitones = 10, octave = 1, vel = 90 },  # b7
  { start = 84, len = 6,  semitones = 11, octave = 1, vel = 95 },  # 7 -> résout sur 0 au tour suivant
  { start = 90, len = 6,  semitones = 0,  octave = 1, vel = 100 },
]

[[bass_cells]]
id = "phrygian_ostinato_b2"
part = "A2"
bars = 1
subdivisions_per_bar = 12   # 12 croches de 12/8
notes = [
  { start = 0, len = 2, semitones = 0, octave = 1, vel = 95 },     # I (D1)
  { start = 2, len = 1, semitones = 1, octave = 1, vel = 85 },     # b2 (D#1)
  { start = 3, len = 3, semitones = 0, octave = 1, vel = 90 },     # I
  { start = 6, len = 2, semitones = 1, octave = 1, vel = 85 },     # b2
  { start = 8, len = 4, semitones = 0, octave = 1, vel = 95 },     # I
]
```

### 7.3 Pour G4, G5 et G7 — Esquisse du profil `nt_desert`

- **Mode (G1)** : `Phrygian`, tonique `G#` (ou `D`), bascule par la valence :
  valence basse → phrygien sur pédale ; valence plus haute ou calme (faible
  excitation) → nappe éolienne/phrygienne sur `A` façon *A Way* (sans
  batterie ni basse, `Chords` tenus seuls).
- **Mètre et tempo** : `12/8` à `bpm = 140` (pulsation noire pointée),
  ramené au calme vers un tapis lent (`bpm = 80`, percussion coupée sous un
  seuil de densité).
- **Forme (G4)** : boucle `A1 (8 mes.) → A2 (8 mes.) → Bridge (8 ou 16 mes.,
  drums_enabled = false, bass_enabled = false, pads_only = true) → B (8 mes.)`,
  sans exiger de cellules `Run`/`Arp`/`Turn` quand `melody_enabled = false`
  ou quand la mélodie n'entre qu'à forte densité.
- **Nappes (G5)** : piste `Chords` avec tenue sur 2 à 4 mesures sans
  ré-attaque à la barre de mesure (indispensable pour le pont de *Fläshyn*
  et pour tout *A Way*).
- **Percussion (`FeetTable`)** : `Heel` = Kick (GM 36) sur les pas
  `[0, 8, 20]` / 24, `Toe` = Snare (GM 38) sur `[2, 10, 14]` / 24 (ou
  sur une grille de 12 croches : Kick `[0, 4, 10]`, Snare `[1, 5, 7]`).

---

## 8. Distance du profil `nt_desert` au corpus (M1)

Critère 3 de la phase : le labo publie, pour chaque profil, la distance à son
corpus de référence, en audio et en symbolique. Outil générique (aucun nom de
jeu en dur) : `src/harmonium_lab/styledist/`, appelé par
`make style-distance PROFILE=<id> REF=<dossier> TRACKS=<id,id>
STYLE_CORPUS=<dir> [BANKS=label=sf2 …] [CONTEXT=champ=valeur]`. Le même outil
servira à Isaac. Chiffres complets et reproductibles :
`distance-nt_desert.json`, re-mesuré au moteur `aadc812` (après G7e et G7h,
état de clôture du profil), graines 1–10, 48 mesures, banques `nt_desert.sf2`
et `GeneralUser-GS.sf2`, batterie sur la banque du profil via
`--feet-soundfont`. Les tableaux §8.2 et la lecture §8.3 datent du moteur
`4b0fe7b` ; la re-mesure les déplace peu :

| Score global (0–100) | `4b0fe7b` | `aadc812` |
|---|---:|---:|
| Audio `nt_desert` vs *Fläshyn* | 63,3 | 60,9 |
| Audio `nt_desert` vs *A Way* | 50,5 | 54,2 |
| Audio GeneralUser vs *Fläshyn* | 60,7 | 59,6 |
| Audio GeneralUser vs *A Way* | 53,4 | 56,3 |
| Symbolique vs *Fläshyn* | 70,7 | 72,6 |
| Symbolique vs *A Way* | 24,2 | 24,2 |

Le gain symbolique vient de la boucle de basse (`loop_bass` 40,0 → 64,0) :
la relance et le riff liés de G7e/G7h se répètent à l'identique.

### 8.1 Méthode et normalisation

**Audio.** Chaque piste (référence, contexte et rendu) est mesurée au pic
normalisé : tempo (pulsation — MIDI côté rendu, grille G0 côté référence,
repliée à l'octave, tolérance 1/12 d'octave), chroma moyen (cosinus),
`key_strength`, entropie de chroma, centroïde et rolloff spectraux, platitude
(log10), part percussive (HPSS), taux d'attaques, niveau moyen et étalement
RMS (dB), énergie par bande (20–80, 80–250, 250–1000, 1–4 k, > 4 kHz, en dB).
Chaque mesure devient un écart z : `|g − r| / σ`, σ calculé sur les 20 pistes
`type=zone` du corpus (médiane des distances inter-pistes pour le chroma).
Score : `100 · max(0, 1 − z/3)` ; le score d'un groupe est la moyenne de ses
mesures, le score global la moyenne des groupes (tempo, tonalité, brillance,
percussif, attaques, dynamique, bandes).

**Symbolique.** Le MIDI moteur (grille de 24 pas/mesure, celle des
transcriptions) est comparé aux boucles transcrites §5–6 : histogramme de
classes de hauteur de la basse (pondéré par les durées), grilles d'attaques
kick/snare/charleston par position, fondamentale d'accord par mesure
(pédale, taux de changement), et longueur des boucles (part des paires de
mesures `(b, b+L)` qui se ressemblent, à la longueur L de chaque boucle de
référence). Toutes les distances sont dans [0, 1] (Bray-Curtis ou écarts de
parts) ; score = 100 · (1 − d).

### 8.2 Résultats (moyenne sur 10 graines)

**Audio — banque `nt_desert`** (score 0–100)

| Groupe | vs *Fläshyn* | vs *A Way* |
|---|---:|---:|
| **Score global** | **63,3** | **50,5** |
| tempo | 100,0 | 11,0 |
| tonalité | 81,0 | 13,1 |
| brillance | 18,2 | 82,4 |
| percussif | 71,5 | 84,3 |
| attaques | 52,3 | 68,9 |
| dynamique | 58,7 | 23,8 |
| bandes | 61,3 | 70,0 |

**Audio — banque `GeneralUser`** (score 0–100)

| Groupe | vs *Fläshyn* | vs *A Way* |
|---|---:|---:|
| **Score global** | **60,7** | **53,4** |
| tempo | 100,0 | 11,0 |
| tonalité | 60,2 | 24,4 |
| brillance | 10,5 | 62,7 |
| percussif | 65,2 | 90,7 |
| attaques | 65,9 | 82,5 |
| dynamique | 77,9 | 56,0 |
| bandes | 45,2 | 46,5 |

**Symbolique** (score 0–100, 100 = identique)

| Groupe / mesure | vs *Fläshyn* | vs *A Way* |
|---|---:|---:|
| **Score global** | **70,7** | **24,2** |
| basse `bass_pc` | 87,7 (d = 0,12) | 0,0 (référence sans basse transcrite) |
| batterie `drums_any` | 73,6 (d = 0,26) | 0,0 (référence sans batterie) |
| · kick | 76,5 (d = 0,23) | — |
| · snare | 86,4 (d = 0,14) | — |
| · charleston | 0,0 (d = 1,0) | — |
| accords `chord_roots` | 72,9 (d = 0,27) | 36,3 (d = 0,64) |
| · part de pédale | 89,6 (d = 0,10) | 96,7 (d = 0,03) |
| · taux de changement | 76,9 (d = 0,23) | 89,6 (d = 0,10) |
| boucles basse / batterie / accords | 40,0 / 98,4 / 30,1 | — / — / 22,7 |

### 8.3 Lecture

1. **Le profil est du côté *Fläshyn*** (63,3 audio, 70,7 symbolique), pas du
   côté *A Way* (50,5 / 24,2) : c'est ce que la forme en arche de G4 veut.
   Contre *A Way*, la distance est structurelle : tempo 140 contre 120
   (z = 2,7), batterie et basse présentes là où le bourdon n'en a pas
   (distance 1,0, voix réellement absentes — `reference_empty_voices`), tonalité
   G# phrygien contre pédale A (chroma z = 2,5). Le point commun le plus fort
   est l'absence de percussif.
2. **La basse et la poursuite de la pédale sont justes** : histogramme de
   classes de hauteur à 0,12 de *Fläshyn* (registre médian identique, G#1),
   part de pédale à 0,10, taux de changement d'accords à 0,23. Les grilles
   kick (d = 0,23) et snare (d = 0,14) suivent §6.2.
3. **Deux écarts réels, un artefact.**
   - *Brillance* (18,2 contre *Fläshyn*) : le rendu manque de centroïde
     (z = 2,3) et de platitude (z = 3,6) — la saturation de la scie G6 est
     loin de la boucle originale saturée et filtrée passe-haut. Écart réel,
     déjà pointé par l'écoute G7 (« buzz »).
   - *Boucles d'accords* (30,1) : l'harmonie générée ne se répète pas au
     décalage de 8 mesures des boucles du pont ; l'original non plus ne
     répète pas ses sections dos à dos — mesure exigeante, à lire comme
     « ostinato » (batterie 98,4, proche de l'original) contre
     « harmonie évolutive » (30,1).
   - *Charleston* (0,0) : artefact du référentiel, pas du moteur — la
     transcription G0 note que « le charleston continu est masqué par le
     mix » (§5, confiance moyenne) ; les rares coups transcrits ne se
     superposent pas aux pulsations jouées. À ne pas utiliser pour régler le
     moteur.
4. **Banques** : `nt_desert.sf2` bat GeneralUser sur la tonalité (81,0 contre
   60,2 — nappe 89 fidèle au bourdon), GeneralUser sur l'étalement dynamique
   (77,9 contre 58,7 — les presets G6 tenus « < 0,1 dB de chute » rendent le
   rendu plat). Cohérent avec les mesures G6 et l'écoute.

### 8.4 Limites

- Les distances symboliques se calculent contre les transcriptions §5 telles
  que publiées : la pédale de *A Way* y est vue F/D (la détection sur bourdon
  sans pulsation est fragile), et le charleston y est sous-transcrit. Voir les
  confiances par boucle avant de régler le moteur sur un chiffre.
- La longueur de boucle (part des paires `(b, b+L)`) exige la répétition au
  décalage L : bonne pour un ostinato, sévère pour une harmonie qui évolue
  par section.
- Le charleston et la platitude spectrale sont les deux mesures où le
  référentiel (masqué au mix) ou la chaîne (rendu sec contre master
  compressé) tirent le score vers le bas sans faute d'écriture du moteur.
