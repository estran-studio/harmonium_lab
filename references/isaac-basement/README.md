# Références Basement — *The Binding of Isaac* (Ridiculon)

Analyse de la zone Basement et de ses variantes (tâche G9-G0 de la phase
014) : mesures audio (`measures.json`), structure, instrumentation,
boucles transcrites (hors dépôt) et propositions de données pour un futur
profil `isaac_basement` (G1 à G7b).

**Provenance et droits (principe VII).** Quatre pistes de la compilation de
fan « The Binding of Isaac: Repentance - Full OST (HQ) » (MegaSamantha,
2021), composées par Ridiculon (Matthias Bossi, Jon Evans) : 02 *Diptera
Sonata* (Basement, Rebirth), 21 *Periculum* (Cellar), 36 *Fundamentum*
(Burning Basement, Afterbirth), 47 *River of Despair* (Downpour,
Repentance). Enregistrements, stems et transcriptions MIDI restent hors
dépôt, dans le checkout principal gitignoré :

- audio : `corpus/isaac/tracks/02_diptera_sonata.flac` … `47_river_of_despair.flac` ;
- stems (demucs `htdemucs`) : `corpus/isaac/stems/htdemucs/<id>/` ;
- boucles MIDI + WAV + JSON : `corpus/isaac/transcriptions/`.

Seuls ce compte rendu, `measures.json` et `grids.json` sont versionnés.

---

## 1. Mesures audio et mise en contexte (25 pistes `zone`)

Sortie complète : `references/isaac-basement/measures.json` (reproduite par
`harmonium-lab audioref-measures`). Les quatre Basement occupent le pôle
**lent, sombre et harmonique** du corpus de zone :

| Mesure | *Diptera Sonata* | *Periculum* | *Fundamentum* | *River of Despair* | Contexte 25 pistes `zone` (moy. ± é.-t., [min..max]) |
|---|---:|---:|---:|---:|---:|
| Tempo `beat_track` brut (BPM) | 143,6 | 143,6 | 136,0 | 143,6 | 114,7 ± 29,9 [49,7..215,3] |
| Tempo grille vérifiée (BPM) | **140,0** | **140,0** | **140,0** | **144,0** | — (résidu de calage < 10 ms) |
| Taux d'attaques (/s) | 1,86 | 1,31 | 1,22 | 1,12 | 1,86 ± 0,64 [0,75..2,99] |
| Force tonale (`key_strength`) | **2,30** (max des 4) | 1,75 | 1,78 | 1,41 | 1,65 ± 0,35 [1,26..2,77] |
| Entropie de chroma (bits) | 3,46 | 3,51 | 3,52 | 3,52 | 3,51 ± 0,04 |
| Centroïde spectral (Hz) | **2 638** | 2 175 | **2 614** | **2 040** | 1 989 ± 482 [998..2 660] |
| Rolloff spectral 85 % (Hz) | 5 462 | 4 857 | 5 618 | 4 447 | 4 337 ± 1 031 |
| Platitude spectrale | 0,020 | 0,018 | 0,030 | 0,010 | 0,015 ± 0,008 |
| RMS moyen | 0,095 | 0,098 | 0,076 | **0,134** | 0,090 ± 0,024 |
| Part harmonique / percussive | 79,9 / 20,1 % | 79,1 / 21,0 % | 80,1 / 19,9 % | **89,3 / 10,7 %** | 85,2 / 14,8 % (± 5,1 %) |

Constat : les quatre pistes jouent un **4/4 métronomique autour de 140 BPM**
(tempo_stability ≥ 0,97), plus sombres et plus harmoniques que la moyenne
des zones d'action. *Diptera Sonata* est la plus percussive et la plus
tonalement affirmée (pédale D) ; *River of Despair* est un tapis lent quasi
sans percussion (89,3 % harmonique, RMS le plus fort).

**Mode global (gabarits de chroma).** Le corpus de zone Isaac est massivement
**mineur harmonique : 17 des 25 pistes**, dont 9 sur D. Nos quatre :
D mineur harmonique pour *Diptera Sonata* (marge 0,005), *Periculum*
(0,003) et *River of Despair* (0,006) ; *Fundamentum* est ambigu (D majeur vs
E dorien, marge 0,000) car son centre local est **F#** (voir § 2). Les marges
nulles signifient : **à départager à l'oreille**, le chromatisme ambiant
(C et C# ensemble) déroutant les gabarits.

---

## 2. Tempo, mètre, tonalité et mode

| Paramètre | *Diptera Sonata* (Basement) | *Periculum* (Cellar) | *Fundamentum* (Burning Basement) | *River of Despair* (Downpour) |
|---|---|---|---|---|
| Grille | 4/4, `beat_s = 0,4286 s`, origin 0,671 s, 144 mes. | 4/4, `beat_s = 0,4286 s`, origin 0,481 s, 133 mes. | 4/4, `beat_s = 0,4286 s`, origin 1,442 s, 146 mes. | 4/4, `beat_s = 0,4167 s`, origin 0,359 s, 147 mes. |
| Tatum | Binaire : 2 croches/pulsation (`R_beat/2 = 0,89..0,97`), pas de shuffle | idem | idem | idem (`R_beat/2 = 0,92`) |
| Tonique locale | **D** (pédale D1 continue) | **D** (pédale D1, voisins D#/E) | **F#** (riff F#1, `b2` = G) | **D** (descente chromatique vers D, élan depuis F#) |
| Mode | **D mineur harmonique** : C# sensible sur pédale D, Bb/A/G/F dans la descente | **D mineur harmonique + inflexion phrygienne** (D# = `b2` rampant), pont sur **G#** | **F# phrygien / éolien** : G = `b2`, E = `b7`, accords Bm–Dm ; le gabarit global (D maj/E dorien, marge 0) confirme l'ambiguïté | **D mineur harmonique** : descente chromatique F#→Bb puis C#/D# (sensible et `b2`) |
| Confiance | Haute (pédale et descente mesurées) ; qualité des accords à l'oreille | Haute sur D, **moyenne** sur D# (pyin voit un glissando plus qu'une note) | Haute sur F# et `b2` G ; à l'oreille : phrygien vs éolien | Moyenne : la basse est douce, pyin hésite sur des tenues de 2 mesures |

**Conclusion pour G1 (modes).** Le « son Basement » est le **mineur
harmonique sur pédale** : sensible C# et sous-médiante Bb entendues contre
la tonique tenue, avec des **voisines chromatiques locales** (D# au-dessus
de D dans *Periculum*, G au-dessus de F# dans *Fundamentum*) — le moteur a
déjà `HarmonicMinor` et `Phrygian` (G1), aucun ajout nécessaire.

---

## 3. Structure et longueur des boucles

Auto-similarité par mesure (chroma), énergie du stem batterie et séquence
de la basse. L'auto-similarité reste faible partout (nappe continue,
$r < 0{,}12$) : les boucles sont affirmées à la basse et à la batterie,
pas dans le chromatisme global.

### *Diptera Sonata* — 144 mesures de 4/4 (249 s)

| Section | Mesures | Contenu | Boucle |
|---|---|---|---|
| A1 — Pédale D | 0–8 | Pédale D1 tenue, relance chromatique C#→D, stomp batterie | 4 mes. |
| A2 — Montée | 8–12 | Basse **F–G–A–Bb** (1 note/mesure), nappe Dm→Gm | 4 mes. |
| A1' — Pédale D | 12–21 | Retour pédale D | — |
| D — Descente | 21–32 | Basse **Bb–A–G–F–E** (1 note/mesure), accords Bbm Am Gm Fm | ~8–11 mes. (longueur originale irrégulière : à l'oreille) |
| Pédales | 32–76 | Pédale D, batterie continue, chœur épars | 8 mes. |
| Reprise A2 + D | 76–101 | Mêmes montée et descente (r ≈ 1,00 avec 8–12 et 21–32) | idem |
| Coda | 101–144 | Pédale D, batterie coupe à la mes. 141 (silence final) | — |

### *Periculum* — 133 mesures

Boucle principale de **8 mesures** (D/D#/F chromatique rampant) ×6 jusqu'à
la mes. 48 → **pont 16 mes.** sur G#/G/F/C# (mes. 48–64) → boucle (64–112)
→ pont' (112–128) → coda D, batterie coupe à la mes. 128.

### *Fundamentum* — 146 mesures

**Riff de 2 mesures** F# (F#–F#–E–F#–G, `b2` en fin de cycle) pendant ~60 %
de la piste, entrecoupé de sections d'accords : D–B–A–F# (mes. 32–40),
A–B (56–64), reprises (96–104, 128–136). Fin : accords E, batterie coupe à
la mes. 143.

### *River of Despair* — 147 mesures

Forme en blocs de **16 mesures**, chaque note de basse tient 2 mesures :
levée (0–2) → **A** descente chromatique G→Bb (2–32) → **B** élan
C–C#–D–Bb–F#–F–E–D# (32–48) → **C** montée D–G–Bb–C–C#–D–D#–F (48–64) →
A B C répétés (64–128) → A final (128–147, batterie en fondu dès la
mes. 138).

---

## 4. Instrumentation probable et programmes General MIDI

Timbres déduits des stems (centroïde, platitude, part percussive —
confiance moyenne, **à valider à l'oreille**) :

| Rôle | Timbre dans l'original (évidence stem) | Programme General MIDI (0-indexé, GeneralUser GS) |
|---|---|---|
| Basse | Basse électrique saturée / fuzz : centroïde 253–400 Hz, platitude ≈ 0, fondamentale D1/F#1 (37/46 Hz) riche en harmoniques | **33** *Fingered Bass* (pédale) ou **34** *Pick Bass* (riff piqué de *Fundamentum*) ; **38** *Synth Bass 1* si plus synthé à l'oreille |
| Batterie | Kit rock sec et compressé : centroïde 2,8–3,5 kHz, kick sous 80 Hz, caisse claire claquante | Canal 10 GM Standard Kit : **36** *Bass Drum 1*, **38** *Acoustic Snare*, **42** *Closed Hi-Hat* (charleston épars, jamais continu) |
| Nappe / accords | Nappe sombre tenue (orgue ?) : centroïde ≈ 2 kHz, 80–89 % harmonique, sans attaque franche | **91** *Pad 4 (choir)* pour le lit sombre ; **89** *Pad 2 (warm)* ; **19** *Rock Organ* si l'ostinato est organique |
| Chœur / nappe vocale | Stem `vocals` significatif sur 47 (rms 0,019) et par blocs sur 02 (mes. 56–64) et 21 (mes. 8–16) : « aah » graves | **52** *Choir Aahs* / **53** *Voice Oohs* |
| Motif / lead | Motif médium-aigu ponctuel, plus clairsemé que la nappe (voiced 0,24–0,66) ; timbre indéterminé par les stems | **53** *Voice Oohs* (chœur mélodique) ; à l'oreille si un timbre clavier/célesta apparaît : **8** *Celesta* / **10** *Music Box* |

### Presets d'usine Odin 2 candidats (noms seulement)

| Rôle | Candidats Odin 2 (`Factory Presets/`) |
|---|---|
| Basse | `Bass/Sausage Bassener`, `Bass/Bass Low [RM]`, `Bass/Analog Bass [tx]`, `Bass/Growly FM Bass [XR]`, `Bass/Bass Crusher [RM]` |
| Batterie (kit sec) | `Drums/Kick-1 [Photonic]`, `Drums/kick 909`, `Drums/Snare-1 [Photonic]`, `Drums/Snappy Snare [Projektor]`, `Drums/Hi-Hat [RS]`, `Drums/HiHat-closed [Photonic]`, `Drums/Crash-1 [Photonic]`, `Drums/SnarNoize`, `Drums/Toms-1 [Photonic]` |
| Nappe sombre / orgue | `Organ/666-001-Organ`, `Organ/Church Organ`, `Organ/Pad Pleasure`, `Pads/Haunt [RM]`, `Pads/Darken Nature [RM]`, `Pads/Moonshade`, `Pads/PAD Open`, `Atmospheres/Eerie Pad` |
| Chœur | `Pads/Choir Aahs 1 [RS]`, `Pads/Choir Aahs 2 [RS]`, `Pads/Choir [Photonic]`, `Pads/Voices`, `Pads/Female aah`, `Pads/Choir Yeah [RS]` |
| Motif (si clavier/célesta à l'oreille) | `Instruments/MusicBox [Photonic]`, `Keys/Toy Piano`, `Chimes/Vibraphone`, `Chimes/Ethereal Bells`, `Leads/Vibrato Lead` |

---

## 5. Transcriptions, minutages sources et confiance

Les 13 boucles MIDI et leurs rendus WAV (`fluidsynth` + GeneralUser GS,
pic 0,125) sont dans
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac/transcriptions/` :

| Fichier (`.mid`/`.wav`/`.json`) | Piste | Mesures | Minutage source | Contenu | Confiance | À valider à l'oreille |
|---|---|---:|---:|---|---|---|
| `02_diptera_sonata_pedal_intro` | *Diptera Sonata* | 0–8 | **0,67–14,39 s** | Pédale D + stomp batterie + Dm tenu | **Haute** (voiced 0,89 ; Dm ×8, score 0,74) | Octave réelle de la basse (D1 vs D2, distorsion) |
| `02_diptera_sonata_climb_riff` | idem | 8–12 | **14,39–21,24 s** | Montée F–G–A–Bb + accords Dm Gm Dm Dm | Haute | Dernier degré (A# vs A) et qualité Gm |
| `02_diptera_sonata_walkdown` | idem | 21–32 | **36,67–55,53 s** | Descente Bb–A–G–F–E + accords mineurs | Haute sur la basse, moyenne sur les accords (Bbm/Gm) | Nombre réel de mesures de la descente (11 à l'original ?) |
| `02_diptera_sonata_choir_verse` | idem | 56–64 | **96,67–110,39 s** | Chœur depuis le stem `vocals` | **Faible** (voiced 0,24) | Le stem capte autant la nappe qu'un vrai chœur |
| `21_periculum_main_loop` | *Periculum* | 0–8 | **0,48–14,20 s** | Ostinato chromatique D/D#/E/F + Dm + stomp | **Haute** (voiced 0,96) | D# = note réelle ou glissando de basse |
| `21_periculum_bridge_Gsharp` | idem | 48–56 | **82,77–96,48 s** | Pont Dm ×4 → G#m Gm Fm C#m | **Haute** (scores 0,84–0,93) | G#m vs G#maj |
| `21_periculum_choir_intro` | idem | 8–16 | **14,20–27,91 s** | Motif du stem `vocals` | Moyenne (voiced 0,66) | Timbre (chœur vs nappe filtrée) |
| `36_fundamentum_fsharp_riff` | *Fundamentum* | 0–4 | **1,44–8,30 s** | Riff 2-mes F# + batterie backbeat | **Très haute** (voiced 0,94 ; marge batterie 0,38) | Octave (F#1) et relance E exacte |
| `36_fundamentum_chords_D` | idem | 32–40 | **56,30–70,01 s** | Cycle Dm Bm F#m ×2 + basse | Haute (0,80–0,89) | Am à la mes. 37 (Dm à l'oreille ?) |
| `36_fundamentum_chords_A_G` | idem | 56–64 | **97,44–111,16 s** | F#m Bm ×2 + relance A | Haute (0,78–0,86) | — |
| `47_river_of_despair_descent_A` | *River of Despair* | 16–32 | **27,03–53,69 s** | Descente chromatique (notes de 2 mes.) + nappe | Haute sur la basse (voiced 0,96) ; **moyenne** sur la batterie (marge 0,28, 33 % de coups ambigus) | Limites exactes de la descente (décalées d'une mesure par la correction d'origine) |
| `47_river_of_despair_rise_B` | idem | 32–48 | **53,69–80,36 s** | Élan C–C#–D–Bb–F#–F–E–D# | Haute | — |
| `47_river_of_despair_chromatic_C` | idem | 48–64 | **80,36–107,03 s** | Montée D–G–Bb–C–C#–D–D#–F | Haute (0,76–0,98) | Qualité mineure plaquée par le détecteur |

---

## 6. Grilles détaillées (basse, batterie, accords)

Grille de 16 doubles-croches par mesure (4/4), positions `0..15`, vote sur
les mesures indiquées.

### 6.1 Basse (degrés en demi-tons depuis la tonique locale)

- ***Diptera Sonata* — A1 (pédale)** : tenue sur **0 (D1)**, relance
  chromatique `11 (C#) → 0` en fin de cycle.
- ***Diptera Sonata* — montée A2 (mes. 8–11)** : une note par mesure,
  croches tenues :

```
Mes. 8 : F(3)  | Mes. 9 : G(5)  | Mes. 10 : A(7)  | Mes. 11 : Bb(8)
```

- ***Diptera Sonata* — descente D (mes. 21–31)** : `Bb(8) A(7) G(5) F(3) E(2)`,
  une note par mesure.
- ***Periculum* — ostinato (mes. 0–48)** : pédale **0 (D1)** hachée en
  croches avec voisins chromatiques **1 (D#)** et **2 (E)** et appuis brefs
  sur **3 (F)**, ré-attaque de la pédale sur le temps 3 (pos. 8–11).
- ***Fundamentum* — riff (2 mesures)** :

```
Pos (0..31) :  0 1 2 3 4 5 | 6  7  8 ...   | 16..23 (tenue) | 26 27 | 34 35
Degré / F#  :  0 0 0 0 0 0 | 0  b7(E) 0    | 0             | 0  0  | b2(G) 0
```
(tenue de F# presque continue, E en note de passage au milieu de chaque
mesure, G = `b2` en appui vers la fin du cycle de 2 mesures).

- ***River of Despair* — blocs de 16 mesures** : chaque note tient
  2 mesures. A : `G G F# F# F F E E D# D# D D C Bb` ; B : `C C C# C# D D
  Bb Bb F# F# F F E E D# D#` ; C : `D D G G Bb Bb C C C# C# D D D# D# F F`.

### 6.2 Batterie

- ***Diptera Sonata* et *Periculum* — « stomp » industriel** (vote 8 mes.) :

```
Pos (0..15) :  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
Kick  (36) :  X  .  x  .  .  .  x  .  .  .  .  .  .  .  .  .
Snare (38) :  .  .  .  .  X  .  .  .  X  .  .  .  X  .  .  .
```

(`X` = ≥ 0,75 des mesures ; `x` = 0,4–0,75). La caisse claire marque
**chaque temps 2–3–4** et la grosse caisse le temps 1 et ses contretemps
proches : marche lourde sans charleston continu.
- ***Fundamentum* — backbeat rock** : Kick `{0, 2}`, Snare `{8}`,
  Charleston `{4, 12}` (sur les temps 2 et 4).
- ***River of Despair* — ossature clairsemée** : snare sur le temps 3
  (pos. 8) chaque mesure, kick faible sur 0 et 4, charleston épars
  (marge 0,28 : coups noyés dans la nappe).

### 6.3 Accords par mesure (détecteur triades, qualités toutes mineures)

- ***Diptera Sonata*** : pédale `Dm` (mes. 0–21, 32–76, 101–144) ;
  montée `| Dm | Gm | Dm | Dm |` ; descente `| Bbm | Bbm | Am | Am | Gm |
  Bbm | Am | Am | Cm | Fm | Am |`.
- ***Periculum*** : boucle `Dm` ×8 ; pont `| Dm ×4 | G#m | Gm | Fm | C#m |`.
- ***Fundamentum*** : `| F#m | Bm |` sur le riff ; sections
  `| Dm | Bm | F#m | F#m | Dm | Am | Dm | F#m |` et `| F#m | Bm | F#m | F#m |`
  (×2 avec relance A).
- ***River of Despair* — A** : `| F#m Dm | Gm Gm | F#m F#m | Fm Dm | Cm Am |
  D#m D#m | Dm Dm | Cm Bbm |` (une entrée par paire de mesures) ; **B** :
  `| D#m Dm | Cm Cm | C#m C#m | Bbm Dm | Bbm Gm | Dm Dm | Fm Dm | Em D#m |` ;
  **C** : `| Dm Dm | Gm Gm | Bbm Bbm | Cm Cm | Bbm Am | Dm Gm | D#m D#m | Fm Fm |`.

**Attention** : le détecteur ne connaît que majeur/mineur ; les nappes
originales sont souvent des dyades quinte+octave (sans tierce). Vérifier à
l'oreille la qualité avant d'en faire des données de profil.

---

## 7. Propositions de données pour le profil `isaac_basement`

Esquisse dans le schéma réel du moteur (`profiles/nt_desert/profile.toml`) ;
réutilise uniquement des mécanismes existants.

```toml
[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16          # 16 doubles-croches
steps_per_pulse = 4
pulses_per_bar = 4
default_bpm = 140.0

# G1 : mineur harmonique sur D (le gabarit global des 25 pistes zone)
[melody]
key_modes = [{ key = 2, mode = "harmonic_minor", weight = 1 }]

# G4 : forme en boucle, sans cadence (rôles Open/Free)
[form]
sequence = [0, 1, 2, 3, 0]
# A1 pédale D (8 mes.) / A2 montée (4) / D descente (8) / Pont chœur (8) / A1'

# G2 : pédale + boucle d'accords (modèle "loop" de G2)
[harmony]
model = "loop"
steps_per_chord = 16
[harmony.parts.A1]                 # pédale de tonique, voisine C# dans la basse
kind = "pedal"
degree = 0
[harmony.parts.A2]                 # la montée reste harmoniquement sur D
kind = "pedal"
degree = 0
[harmony.parts.D]                  # descente : deux mesures par accord
kind = "chord_loop"
chords = [
  { semitones = 10, quality = "Minor", bars = 2 },   # Bbm
  { semitones = 9,  quality = "Minor", bars = 2 },    # Am
  { semitones = 7,  quality = "Minor", bars = 2 },    # Gm
  { semitones = 5,  quality = "Minor", bars = 2 },    # Fm
]
[harmony.parts.Pont]               # pont à la Periculum : bV, iv, sensibilité
kind = "chord_loop"
chords = [
  { semitones = 6,  quality = "Minor", bars = 4 },   # G#m
  { semitones = 7,  quality = "Minor", bars = 4 },    # Gm
  { semitones = 5,  quality = "Minor", bars = 4 },    # Fm
  { semitones = 1,  quality = "Minor", bars = 4 },    # C#m
]

# G3 : basse motivique (demi-tons relatifs, 16 pas/mesure)
[[accompaniment.bass.motifs]]
part = "A1"
bars = 2
reference = "tonic"
notes = [
  { step = 0, duration = 28, semitones = 0, velocity = 92, tie = true },
  { step = 28, duration = 2, semitones = 11, velocity = 85 },  # relance C#
  { step = 30, duration = 2, semitones = 0, velocity = 100 },
]
[[accompaniment.bass.motifs]]
part = "A2"
bars = 4
reference = "tonic"          # montée F G A Bb, une note par mesure
notes = [
  { step = 0,  duration = 16, semitones = 3, velocity = 95 },
  { step = 16, duration = 16, semitones = 5, velocity = 95 },
  { step = 32, duration = 16, semitones = 7, velocity = 95 },
  { step = 48, duration = 16, semitones = 8, velocity = 95 },
]
[[accompaniment.bass.motifs]]
part = "D"
bars = 4
reference = "tonic"          # descente Bb A G F, deux mesures par note
notes = [
  { step = 0, duration = 32, semitones = 8, velocity = 90, tie = true },
  { step = 32, duration = 32, semitones = 7, velocity = 90, tie = true },
]
# Variante Fundamentum (autre étage / basse valence) : riff 2-mes
# 0 0 0 0 0 0 | tenue | 0 0 2(b2) 0 ...

# G5 : nappe liée — un plaqué tenu par changement d'accord, pas de ré-attaque
[accompaniment.chords]
center = 60
max_drift = 6
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 53, tie = true }] }]

[instruments]
chords_program = 91            # Pad 4 (choir)
melody_program = 52            # Choir Aahs (pont uniquement, arrangement)
bass_program = 33              # Fingered Bass
percussion_bank = 128
percussion_program = 0

# G7b : le pont tait la batterie, la coda tait tout sauf la nappe
# [form.parts.Pont] tracks_off = ["Heel", "Toe"]

# G6b : Odin par piste (présents d'usine, candidats du §4)
[odin.Bass]
preset = "Sausage Bassener"
[odin.Chords]
preset = "Haunt"
```

**Batterie (`feet.toml`, G7c)** : `heel_note = 36`, `toe_note = 38` ;
le stomp Basement : Kick `{0, 2, 6}` / Snare `{4, 8, 12}` ; le backbeat
Fundamentum : Kick `{0, 2}` / Snare `{8}` / Charleston (note 42 sur Toe)
`{4, 12}` ; *River of Despair* : densité 0 seulement (Kick `{0}`, Snare
`{8}`), charleston absent — la densité moteur module déjà ce choix.

**Manques moteur : aucun bloquant identifié.** Le mineur harmonique (G1),
le modèle `loop`/`pedal` (G2), les motifs de basse libres (G3), la forme en
boucle sans cadence (G4), les nappes liées (G5), `tracks_off` par partie
(G7b) et l'Odin par piste (G6b) couvrent tout le vocabulaire mesuré. Points
à suivre :

1. **Descente originale de 11 mesures** (*Diptera Sonata*, mes. 21–32) :
   irrégulière ; le profil l'arrondit à 8 ou 12 mesures — écouter si
   l'asymétrie est essentielle.
2. **Voisine chromatique de pédale** (D + D# dans *Periculum*) : le modèle
   `pedal` n'a pas de champ « note voisine » ; contournement déjà employé
   par `nt_desert` (une triade mineure sur le degré voisin), ou la basse
   motivique porte la voisine seule.
3. **Chœur entrant par partie** : l'arrangement (entrées par tour/partie)
   suffit à faire entrer `Melody` au pont seulement ; vérifier que le
   programme 52/53 sonne sur GeneralUser avant d'en faire une donnée.

---

## Reproduction

```bash
harmonium-lab audioref-measures \
  --manifest corpus/isaac/manifest.jsonl --corpus-root corpus/isaac \
  --filter "id=02_diptera_sonata|21_periculum|36_fundamentum|47_river_of_despair" \
  --context type=zone \
  --grids references/isaac-basement/grids.json \
  -o references/isaac-basement/measures.json
# boucles : harmonium-lab audioref-loops (grilles de grids.json,
# minutages sources dans chaque .json de transcriptions)
```

---

## 8. Distance de l'essai `isaac_basement` (M1)

Profil d'essai de fin de phase 014 (`profiles/isaac_basement`, moteur
`aadc812` + profil non commité au moment de la mesure), graines 1–10,
48 mesures, banque GeneralUser GS. Chiffres complets :
`distance-isaac_basement.json` (`make style-distance PROFILE=isaac_basement
REF=isaac-basement TRACKS=02_diptera_sonata,21_periculum
STYLE_CORPUS=corpus/isaac CONTEXT=type=zone`).

| Score (0–100) | *Diptera Sonata* | *Periculum* |
|---|---:|---:|
| **Audio global** | **40,9** | **38,7** |
| tempo | 100,0 | 100,0 |
| tonalité | 30,3 | 5,7 |
| brillance | 0,0 | 11,9 |
| percussif | 13,2 | 7,5 |
| attaques | 26,3 | 0,0 |
| dynamique | 88,6 | 91,2 |
| bandes | 27,5 | 54,3 |
| **Symbolique global** | **65,9** | **69,0** |
| basse | 76,6 | 65,9 |
| batterie | 56,8 | 85,6 |
| accords | 77,8 | 64,8 |
| boucles | 52,5 | 59,6 |

Lecture : l'écriture (basse, stomp, pédale et boucles) est proche des
transcriptions ; le son ne l'est pas. Le rendu GeneralUser est trop sombre
(brillance 0) et trop peu percussif face au mix saturé et compressé de
Ridiculon ; la tonalité contre *Periculum* souffre de son D# rampant, absent
de l'essai. Pistes : basse saturée (Odin), batterie plus présente au mix,
voisine chromatique D# sur la pédale.
