# Références Crystal Caves — *Nuclear Throne* (Jukio Kallio)

Analyse **intégrale de 08 Crystallized Fear** (A, 141 s), transcriptions comprises.
**33 Is This Happening** (Cursed Crystal Caves, 148 s) : contexte en mesures audio
seulement, sans stems ni transcription. Méthode G9-G0 des références Isaac
Basement et NT Desert, avec limites de confiance explicites.

**Provenance et droits — principe VII.** Jukio Kallio / Vlambeer, OST 2015,
source officielle du manifeste :
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=694s> et
<https://www.youtube.com/watch?v=Jk5jogaEsz8&t=3747s>.
Tout fichier audio, stem, MIDI ou JSON de transcription reste dans le checkout
principal gitignoré : `~/Project/bascanada/harmonium_lab/corpus/nuclear_throne/`.
Ce dossier versionne seulement `README.md`, `measures.json`, `grids.json`.

## 1. Mesures audio et contexte `type=zone`

Les 20 zones sont remesurées dans `measures.json`, avec leurs métadonnées et
statistiques agrégées ; les versions de bibliothèques diffèrent de l'ancien
rapport Desert, d'où des écarts possibles sur certaines métriques.

| Mesure du mix complet | Crystallized Fear | Cursed, contexte | 20 zones, moyenne ± écart-type |
|---|---:|---:|---:|
| Tempo brut `beat_track`, BPM | 143,6 | 198,8 **non validé** | 115,4 ± 43,8 |
| Attaques / s | 1,86 | 1,84 | 2,58 ± 1,65 |
| Force tonale | 1,354 | 1,492 | 1,699 ± 0,445 |
| Entropie chroma, bits | 3,564 | 3,553 | 3,511 ± 0,068 |
| Centroïde, Hz | **2 243** | **1 931** | 2 045 ± 739 |
| Rolloff 85 %, Hz | 4 287 | 3 831 | 4 051 ± 1 620 |
| Platitude | 0,02672 | 0,02078 | 0,0285 ± 0,0231 |
| Part harmonique / percussive HPSS | 82,63 / **17,37 %** | 90,86 / **9,14 %** | 87,45 / 12,55 % |
| RMS moyen ± dispersion temporelle | 0,19511 ± 0,08774 | **0,11978 ± 0,08449** | 0,1934 ± 0,0482 entre pistes |

La variante Cursed est plus sombre, moins percussive et a le plus faible RMS
moyen des 20 zones. Une simple accélération de Crystallized Fear ne suffit donc
pas à la décrire. La dynamique brute `dynamic_range_db = 80` plafonne sur toutes
les zones ; elle ne discrimine rien. Pour A, RMS P90/P10 **10,02 dB** sur les
fenêtres au-dessus de 1 % du maximum : contraste réel entre blocs légers et denses.
La séparation HPSS ne mesure pas directement la présence d'un instrument.

## 2. Tempo, mètre, tonique et mode

| Paramètre | Crystallized Fear A | Is This Happening, contexte |
|---|---|---|
| Tempo retenu | **139,9961 BPM à la noire pointée**, soit **209,9942 BPM à la noire** du moteur/MIDI | **Aucun tempo constant validé** ; 198,8 est seulement la sortie brute |
| Mètre / subdivision | **12/8**, 4 pulsations ternaires, **24 pas** par mesure ; confiance haute sur le ternaire, moyenne sur la barre | Mètre indéterminé sur le mix ; ne pas lui attribuer un 4/4 à 198,8 |
| Preuve de grille | Croche ternaire : **R = 0,7399**, résidu médian **9,28 ms**, P90 **29,46 ms** | Balayage 60–220 BPM, divisions 2/3/4 : meilleur R global ~**0,116** ; les maxima locaux de 20 s dérivent de 96,7 à 204,1 BPM, R ≤ 0,253 |
| Premier temps positif | **0,83925 s**, convention de phase, confiance moyenne | Pas de premier temps global fiable |
| Tonique / centre | **A**, moyenne–haute sur A/Bb et le retour A ; le maximum global de chroma est A | Maximum chroma D, mais gabarit modal sur F# : tonique fonctionnelle **non établie**, faible confiance |
| Mode local | **A phrygien** dans le thème A/Bb, puis **A mineur harmonique** au pont | Gabarit **F# mineur harmonique**, score 0,877, marge 0,017 sur D mineur harmonique ; hypothèse faible, pas une tonalité certifiée |

A : sur les mes. 1–9, le gabarit **fixé sur A** donne phrygien 0,849 (marge
0,055) ; mes. 41–49 : 0,831 (marge **0,118**), et la basse alterne A/Bb.
Au pont 49–65 : mineur harmonique 0,917–0,935 (marges 0,039–0,045), avec E majeur
et G# sensible. Le gabarit libre global C mixolydien = D éolien (marge 0) masque
cette alternance locale ; il ne justifie pas de déplacer la tonique de A vers C.

À 210 BPM binaires, la même croche de 0,14286 s est obtenue, mais la répétition
d'enveloppe à quatre pulsations serait faible (**0,083**, contre **0,500** à
quatre pulsations de 140 pointées) : lecture **12/8 retenue**, pas 4/4 à 210.
`grids.json` ne contient volontairement **aucune grille inventée pour 33**.
L'échec de calage global n'exclut pas des pulsations locales ou un traitement
variable de vitesse ; leur existence exacte n'est pas déterminée ici.

Mesures 0-based et bornes `[début, fin)`. Origine théorique de A :
**−0,875083 s**, première barre partielle ; mesure 1 à 0,83925 s.
L'intégrale conserve aussi la fin partielle. Les temps négatifs et ceux après
141 s du sidecar sont du remplissage de grille, pas des passages source existants.

## 3. Structure complète et longueurs de boucles

Croisement chroma par mesure, basse et RMS de batterie. Les intitulés sont
analytiques. Les bornes sont une convention de transcription à confiance moyenne,
non une découpe officielle au sample près.

| Mesures | Source, s | Matériau | Longueur / répétition |
|---|---:|---|---|
| 0, partielle | 0–0,839 | Amorce | — |
| 1–9 | 0,839–14,554 | Thème A/Bb, texture harmonique, quelques percussions | Cellules **4 mes.**, groupées par 8 |
| 9–17 | 14,554–28,269 | Réponse plus chromatique G#/G, retour A/Bb | Réponse de 8 mes. |
| 17–25 | 28,269–41,983 | Thème varié, entrée progressive du bloc dense vers la fin | 8 mes. |
| 25–41 | 41,983–69,413 | Batterie forte (RMS ~0,17–0,20), pôles F/C/E puis G#/G | **Deux cycles de 8 mes.** avec fins différentes |
| 41–49 | 69,413–83,127 | Retour A/Bb, batterie presque absente | Thème de 8 mes. |
| 49–57 | 83,127–96,842 | Pont F/C/E, sensible G#, batterie faible | 8 mes. |
| 57–65 | 96,842–110,557 | Variante F/G/Am/E puis F/Dm/E, relance finale | 8 mes. |
| 65–81 | 110,557–137,986 | Reprise de l'ouverture et de sa réponse | Retour après **64 mes.** |
| 81–82 + fin partielle | 137,986–141 | Extinction | Coda |

Le score `loop_scores` au retard **64** est **0,1893** sur 18 paires (cosinus
au retard moins fond hors diagonale), contre des petits scores locaux dans
l'analyse limitée à 32 mesures. La reprise longue est donc réelle dans les
descripteurs ; il serait incorrect de conclure « pas de boucle » en ne testant
que 1–16 mesures. Unité harmonique locale utile : **8 mesures = 13,715 s** ;
le motif A/Bb comporte des blocs de deux mesures et un retour en quatre mesures.
La coupe globale de 141 s ne correspond pas à un nombre entier de mesures.

## 4. Instrumentation probable, GM et candidats Odin

`htdemucs` 4.1.0, CPU, shifts=1 ; statistiques sur les stems complets.
**Inférences de timbre**, aucune écoute humaine ni identification de synthétiseur
original revendiquée. `vocals` peut être une résonance/ligne synthétique.

| Rôle / évidence | Timbre probable et confiance | GM 0-based GeneralUser GS | Noms exacts des fichiers Odin candidats |
|---|---|---|---|
| Basse RMS **0,12508**, centroïde **1 749 Hz**, platitude **0,05353** | Basse/synthé bruité, riche en harmoniques et transitoires ; moyenne sur le rôle, faible sur les attaques au début | **38 Synth Bass 1**, 39 Synth Bass 2 | `Bass Low [RM].odin`, `Growly FM Bass [XR].odin`, `Bass Crusher [RM].odin` |
| `other` RMS **0,12962**, centroïde **2 151 Hz**, platitude **0,00581** | Nappe/clavier harmonique clair, notes tenues et résonances ; moyenne | **89 Pad 2 (warm)**, 91 Pad 4 (choir) | `Eerie Pad.odin`, `Moonshade.odin`, `Haunt [RM].odin` |
| Ligne/résonances, `vocals` RMS **0,02788**, centroïde **2 576 Hz** | Motif médium/aigu réverbéré ; nature « cloche/verre » possible mais non prouvée, confiance faible | **8 Celesta**, 10 Music Box pour un essai non sifflant ; 89 si simple doublure de nappe | `Ethereal Bells.odin`, `MusicBox [Photonic].odin`, `Glass Harp A slow.odin` |
| Batterie RMS **0,08767**, centroïde **3 838 Hz**, platitude **0,09093** | Kit percussif/bruité, surtout dans le bloc dense ; moyenne | Canal 10 Standard : **36/38/42**, banque 128 | `Kick-1 [Photonic].odin`, `Snare-1 [Photonic].odin`, `HiHat-closed [Photonic].odin` : comparaison uniquement, pas Odin sur Heel/Toe |

Tous ces noms existent dans `~/Project/bascanada/odin-presets/` (dossier plat).
Base proposée : Bass Low + Eerie Pad ; Crusher/Growly et Moonshade si tension et
arousal montent. Les niveaux sont des points de départ, pas des appariements
mesurés. Écarter Phazzy Organ, Sausage Bassener sur les notes rapides, le
sifflement et GM 30 guitare saturée. Les rendus de transcription sont GM seul.

## 5. Transcriptions hors dépôt et confiance

**Neuf triplets `.mid` + `.wav` + `.json`** réellement produits dans
`$ROOT/transcriptions/`, préfixe `08_crystallized_fear_`.

| Suffixe | Mesures | Source théorique, s | Contenu / confiance |
|---|---|---:|---|
| `integrale` | 0–83 | −0,875–141,415, source utile **0–141** | Basse + batterie + lead + accords ; structure moyenne–haute, détails variables |
| `ostinato` | 1–9 | 0,839–14,554 | A/Bb ; haute sur les pôles, **faible sur la basse monophonique non voisée** |
| `reponse` | 9–17 | 14,554–28,269 | Réponse chromatique ; moyenne sur le chroma, basse lacunaire |
| `montee` | 25–33 | 41,983–55,698 | Première moitié dense, groove ; moyenne |
| `dense` | 33–41 | 55,698–69,413 | Variante du cycle dense ; moyenne |
| `retour` | 41–49 | 69,413–83,127 | A/Bb nettement récupérés dans la basse ; moyenne–haute |
| `pont` | 49–57 | 83,127–96,842 | F/C/E et sensible G# ; moyenne–haute sur les pôles |
| `pont_resolution` | 57–65 | 96,842–110,557 | F/G/Am/E puis Dm/E ; moyenne |
| `reprise` | 65–73 | 110,557–124,271 | Retour du thème ; moyenne, basse de nouveau lacunaire |

Indicateurs globaux : basse `voiced_ratio` **0,4334**, lead **0,5411**, accords
score moyen **0,836** ; 179 attaques batterie, marge **0,403**, **12,8 %** de
marges < 0,15. Le détecteur majeur/mineur impose des tierces même sur des dyades ;
Bb mineur vs majeur et A majeur vs mineur sont donc incertains.
**Les silences MIDI de basse au début sont des échecs d'extraction**, pas la
preuve d'une absence de grave audible. L'intégrale transcrit tous les segments
analysables, sans remplir les lacunes par une basse inventée. pYIN est borné à son
registre d'analyse ; octave et glissandos ne sont pas certifiés par cette borne.
Les valeurs de confiance du sidecar sont globales, pas des scores locaux d'extrait.
Les WAV incluent relâchement/réverbération de FluidSynth après la fenêtre source.

## 6. Grilles basse / batterie / accords

### 6.1 Basse — degrés chromatiques depuis A

Grille **24 pas** par mesure de 12/8 (6 pas par pulsation pointée).
`0 A`, `1 Bb`, `3 C`, `5 D`, `7 E`, `8 F`, `10 G`, `11 G#`.

- Thème : pôles **Bb (deux mesures) → A (deux mesures)**, avec variantes.
  Preuve monophonique la plus claire mes. **41–49** : occupations **A 78 pas,
  Bb 76**, contre G 10, C 7, E 6. Pas de rythme d'attaque exact fiable au début.
- Bloc dense mes. 25–41 : E 82 pas, G 67, F 43, G# 37 ; contour F/C/E puis
  G#/G confirmé plus nettement par le chroma que par un riff pYIN unique.
- Pont mes. 49–65 : E 96, A 62, F 60, G# 58 pas ; la sensible **11** distingue
  le pont du **1** phrygien du thème.

Ces nombres sont des occupations, pas des événements à copier dans le moteur.

### 6.2 Batterie — vote sur les 16 mesures denses 25–41

| Classe / position 0..23 | Présence mesurée |
|---|---:|
| Kick 0 | 7/16 |
| Kick **4** | **9/16** |
| Kick **16** | **8/16** |
| Kick 20 | 7/16 |
| Snare **6** | **16/16** |
| Snare **10** | **14/16** |
| Snare 18 | 6/16 |
| Snare 22 | 4/16 |

Le contretemps ternaire et les deux appuis 6/10 sont plus sûrs que l'identification
kick de chaque attaque. Pas de hat fiable dans ce bloc : les cymbales superposées
ne sont pas séparées par ce classifieur à trois bandes. Au thème initial, hats
sur **6 (3/8)** et **18 (4/8)** ; mes. 41–49, aucun événement dépassant le seuil.
Cela interdit un kit plein joué du début à la fin. Les quelques détections du
pont ne démontrent pas une batterie régulière : ses RMS sont très faibles.

### 6.3 Grille harmonique réduite

- Thème : **Bb (2 mes.) – A (2 mes.)**, répété/varié ; le détecteur passe
  brièvement par Eb. Préférer des sonorités ouvertes aux tierces incertaines.
- Cycle dense 25–33 : **F – C – E – E – G# – Eb – G – D**.
- Variante 33–41 : **F – C – E – E – G#m – G#m – G – G**.
- Pont 49–57 : **F – C – E – E – F – Em – E – E**.
- Pont 57–65 : **F – G – Am – E – F – Dm – E – E**.

Qualités et renversements des passages denses : confiance faible à moyenne ;
la répétition **F/C/E/E** et le retour A/Bb sont plus sûrs. Ces réductions sont
des dérivés analytiques ; la liste détaillée d'événements reste hors dépôt.

## 7. Propositions de données — `nt_crystal_caves`

Écriture inspirée, **pas un profil installable complet ni une copie du relevé**.
Trois parties de **8 mesures** : A thème phrygien, L bloc dense, B pont ;
8 rôles `Open/Free` chacune, par exemple
`sequence = [0,0,0,1,1,0,2,2,0]`. B tait `Heel/Toe` par `tracks_off`.
Les poids 3:1 sont des choix de composition. Le mineur harmonique du pont
s'exprime par **E majeur explicite et notes chromatiques**, sans prétendre que
le mode global phrygien change automatiquement avec le nom de partie.

```toml
[meter]
time_signature = { numerator = 12, denominator = 8 }
steps_per_bar = 24
steps_per_unit = 2
steps_per_pulse = 6
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 210.0
min_bpm = 195.0
max_bpm = 225.0
[melody]
key_modes = [{ key = 9, mode = "phrygian", weight = 1 }]
[harmony]
model = "loop"
steps_per_chord = 24
[harmony.parts.A]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 6, quality = "Major", bars = 1 },
    { semitones = 1, quality = "Major", bars = 1 },
    { semitones = 0, quality = "Minor", bars = 2 },
  ] },
]
[harmony.parts.L]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 3, quality = "Major", bars = 1 },
    { semitones = 7, quality = "Major", bars = 2 },
    { semitones = 11, quality = "Minor", bars = 2 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 3, quality = "Major", bars = 1 },
    { semitones = 7, quality = "Major", bars = 2 },
    { semitones = 11, quality = "Major", bars = 1 },
    { semitones = 1, quality = "Major", bars = 1 },
    { semitones = 10, quality = "Major", bars = 2 },
  ] },
]
[harmony.parts.B]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 3, quality = "Major", bars = 1 },
    { semitones = 7, quality = "Major", bars = 2 },
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 5, quality = "Minor", bars = 1 },
    { semitones = 7, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 10, quality = "Major", bars = 1 },
    { semitones = 0, quality = "Minor", bars = 1 },
    { semitones = 7, quality = "Major", bars = 1 },
    { semitones = 8, quality = "Major", bars = 1 },
    { semitones = 5, quality = "Minor", bars = 1 },
    { semitones = 7, quality = "Major", bars = 2 },
  ] },
]
[accompaniment.bass]
low = 21
high = 32
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 3
reference = "chord_root"
notes = [{ step = 0, duration = 48, semitones = 0, velocity = 78, tie = true }]
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 42, semitones = 0, velocity = 78, tie = true },
  { step = 42, duration = 6, semitones = -1, velocity = 72, legato = true },
]
[[accompaniment.bass.motifs]]
part = "L"
bars = 1
weight = 3
reference = "chord_root"
notes = [
  { step = 0, duration = 4, semitones = 0, velocity = 96 },
  { step = 4, duration = 2, semitones = 0, velocity = 84 },
  { step = 6, duration = 6, semitones = 7, velocity = 86 },
  { step = 12, duration = 4, semitones = 0, velocity = 92 },
  { step = 16, duration = 4, semitones = 0, velocity = 84 },
  { step = 20, duration = 4, semitones = -1, velocity = 80 },
]
[[accompaniment.bass.motifs]]
part = "L"
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 6, semitones = 0, velocity = 94 },
  { step = 6, duration = 6, semitones = 7, velocity = 84 },
  { step = 12, duration = 8, semitones = 0, velocity = 90 },
  { step = 20, duration = 4, semitones = 1, velocity = 78 },
]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 3
reference = "chord_root"
notes = [{ step = 0, duration = 24, semitones = 0, velocity = 74, tie = true }]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 18, semitones = 0, velocity = 74 },
  { step = 18, duration = 6, semitones = 7, velocity = 68, legato = true },
]
[accompaniment.chords]
center = 60
max_drift = 6
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 24, velocity = 54, tie = true }] }]
[instruments]
melody_program = 8
chords_program = 89
bass_program = 38
percussion_bank = 128
percussion_program = 0
[[odin.Bass.zones]]
when = { tension = [0.6, 1.0], arousal = [0.55, 1.0] }
preset = "Growly FM Bass [XR]"
level_db = -6.0
glide_ms = 0.0
[[odin.Bass.zones]]
preset = "Bass Low [RM]"
level_db = -5.0
glide_ms = 80.0
[[odin.Chords.zones]]
when = { tension = [0.6, 1.0] }
preset = "Moonshade"
level_db = -7.0
[[odin.Chords.zones]]
preset = "Eerie Pad"
level_db = -6.0
[[odin.Melody.zones]]
when = { arousal = [0.65, 1.0] }
preset = "Ethereal Bells"
level_db = -8.0
[[odin.Melody.zones]]
preset = "Haunt [RM]"
level_db = -8.0
```

`feet.toml` proposé, **24 pas et non 16** :

```toml
heel_note = 36
toe_note = 38
[[patterns]]
density = 0
weight = 1
hits = [{ step = 6, track = "Toe", note = 42, delta_velocity = -32 }, { step = 18, track = "Toe", note = 42, delta_velocity = -32 }]
[[patterns]]
density = 1
weight = 3
hits = [{ step = 4, track = "Heel" }, { step = 6, track = "Toe" }, { step = 10, track = "Toe", delta_velocity = -12 }, { step = 16, track = "Heel" }]
[[patterns]]
density = 1
weight = 1
hits = [{ step = 0, track = "Heel" }, { step = 6, track = "Toe" }, { step = 10, track = "Toe", delta_velocity = -12 }, { step = 20, track = "Heel" }]
[[patterns]]
density = 2
weight = 3
hits = [{ step = 0, track = "Heel", delta_velocity = -12 }, { step = 4, track = "Heel" }, { step = 6, track = "Toe" }, { step = 10, track = "Toe" }, { step = 16, track = "Heel" }, { step = 18, track = "Toe", delta_velocity = -20 }, { step = 20, track = "Heel" }]
[[patterns]]
density = 2
weight = 1
hits = [{ step = 4, track = "Heel" }, { step = 6, track = "Toe" }, { step = 10, track = "Toe" }, { step = 16, track = "Heel" }, { step = 22, track = "Toe", delta_velocity = -18 }]
```

Toutes les alternatives harmoniques durent 8 mesures ; motifs bornés à 1–2
mesures, notes ordonnées sans chevauchement. `degree` modal serait 1-based ;
les `semitones` ci-dessus sont chromatiques depuis A. Les zones sont ordonnées
et finissent par le défaut sans `when`. Le moteur choisit les zones par émotion,
pas par le nom de partie : l'hôte reste responsable de ses trajectoires émotionnelles.

**Manques moteur : aucun bloquant pour cette proposition.** Le 12/8, les boucles
pondérées, le phrygien et le mineur harmonique, les accords chromatiques, motifs
libres, tenues, silences par partie et zones Odin existent. Une reproduction
littérale des dyades originales sans tierce, changeant de racine toutes les deux
mesures, dépasse les triades Major/Minor du `chord_loop` documenté ; la pédale
avec voisin existe mais ne décrit pas cette alternance exacte. C'est une limite
de fidélité possible, pas un ajout nécessaire au profil inspiré proposé.
Aucune proposition de profil Cursed à grille fixe : le calage n'est pas établi.

## Reproduction

Labo et `fluidsynth` installés. Séparation : environnement Python 3.11 distinct,
`uv venv --python 3.11 /tmp/nt-demucs` puis
`uv --native-tls pip install --python /tmp/nt-demucs/bin/python demucs==4.1.0 soundfile`.

```bash
ROOT="$HOME/Project/bascanada/harmonium_lab/corpus/nuclear_throne"
PY="$HOME/Project/bascanada/harmonium_lab/.venv/bin/python"
export PYTHONPATH="$PWD/src"
"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$ROOT/manifest.jsonl" --corpus-root "$ROOT" \
  --filter 'id=08_crystallized_fear|33_is_this_happening' --context type=zone \
  --grid '{"estimate":false}' --grids references/nt-crystal-caves/grids.json \
  -o references/nt-crystal-caves/measures.json
# Aucun stem / transcription de 33.
/tmp/nt-demucs/bin/python - <<'PY'
from pathlib import Path
from harmonium_lab.audioref.stems import separate
r = Path.home() / "Project/bascanada/harmonium_lab/corpus/nuclear_throne"
separate([("08_crystallized_fear", r / "tracks/08_crystallized_fear.flac")],
         r / "stems", model="htdemucs", device="cpu", shifts=1)
PY
GRID=$("$PY" -c 'import json; print(json.dumps(json.load(open("references/nt-crystal-caves/grids.json"))["08_crystallized_fear"]))')
"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/08_crystallized_fear.flac" \
  --stems "$ROOT/stems/htdemucs/08_crystallized_fear" \
  --track-id 08_crystallized_fear --grid "$GRID" --tonic A \
  --bass-prog 38 --lead-prog 8 --pad-prog 89 --parts bass drums lead chords \
  --loop integrale:0:83 --loop ostinato:1:9 --loop reponse:9:17 \
  --loop montee:25:33 --loop dense:33:41 --loop retour:41:49 \
  --loop pont:49:57 --loop pont_resolution:57:65 --loop reprise:65:73 \
  --soundfont "$HOME/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2" \
  --out "$ROOT/transcriptions"
```

Calage : concentration circulaire des attaques du mix, division 3 autour de
140 pointées ; résidus sur la croche ternaire. Phase de nouveauté chroma et
attaques graves, puis vérification avec les stems. Versions et validation
commune : [nt-niveaux.md](../nt-niveaux.md).
