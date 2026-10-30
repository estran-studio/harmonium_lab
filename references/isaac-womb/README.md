# Références Womb — *The Binding of Isaac* (Ridiculon)

Analyse de **09 *Viscera* (The Womb, Rebirth, 183 s)** ; contexte :
**55 *Caesarian* (Utero, Repentance, 183 s)** et **35 *Cicatrix*
(Scarred Womb, Afterbirth, 192 s)**. Méthode des références
[Basement](../isaac-basement/README.md) et [Désert](../nt-desert/README.md),
avec transcription de la principale **sur toute sa durée**, pas seulement
une boucle d'ouverture. Mesures réalisées le 30 octobre 2026.

**Provenance et droits.** Ridiculon (Matthias Bossi, Jon Evans), compilation
fan MegaSamantha « The Binding of Isaac: Repentance - Full OST (HQ) », 2021,
[vidéo source](https://www.youtube.com/watch?v=pSO4td4rdRI).
Découpes du manifeste : Viscera 1671–1854 s, Caesarian 11228–11411 s,
Cicatrix 6791–6983 s. Droits réservés Ridiculon / Nicalis / Edmund McMillen.
Aucun enregistrement, stem, MIDI ou WAV de transcription dans ce dossier.

Le corpus réel, **extérieur à ce worktree**, est :

```text
/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac/
  manifest.jsonl
  tracks/{09_viscera,55_caesarian,35_cicatrix}.flac
  stems/htdemucs/09_viscera/{bass,drums,other,vocals}.wav
  transcriptions/09_viscera_<nom>.{mid,wav,json}
```

Seuls `README.md`, `measures.json` et `grids.json` sont versionnés.
**Pas d'audition revendiquée** : les constats sont issus du signal et des
transcriptions automatiques ; les qualifications de timbre et de mode
restent des hypothèses explicitement signalées.

## 1. Mesures et contexte des 25 zones

`measures.json` conserve les **25 pistes** dans `tracks`, leurs métadonnées,
les statistiques `context` et ajoute les trois grilles. Les mesures du mix
proviennent d'un unique appel frais commun aux trois analyses de niveaux ;
elles ne sont pas reprises des anciennes mesures Basement. `analysis`
ajoute les preuves de structure, métriques des stems et inventaire des
transcriptions de Womb.

| Mesure | Viscera | Caesarian | Cicatrix | 25 zones : moyenne ± écart-type [min..max] |
|---|---:|---:|---:|---:|
| Tempo brut `beat_track` (BPM) | 89,1 | 89,1 | 89,1 | 114,712 ± 29,926 [49,7..215,3] |
| Tempo de grille, noire (BPM) | **90,008** | **90,000** | **90,002** | — |
| Attaques / s | **2,75** | 1,82 | 2,56 | 1,8624 ± 0,6363 [0,75..2,99] |
| Stabilité du tempo brut | **0,9385** | 0,9708 | 0,9787 | 0,9709 ± 0,0096 [0,9385..0,9823] |
| Force tonale | 1,8393 | 1,4537 | 1,6434 | 1,6503 ± 0,3543 [1,2609..2,7686] |
| Entropie chroma (bits) | 3,5041 | 3,5103 | 3,5139 | valeurs complètes dans `context.stats` |
| Centroïde (Hz) | **1492,57** | 1731,32 | 1783,93 | 1988,83 ± 481,99 [998,33..2660,04] |
| Rolloff 85 % (Hz) | 3424,76 | 4105,00 | 4026,26 | 4336,82 ± 1030,77 [2154,91..5844,17] |
| Platitude spectrale | 0,006505 | 0,007333 | 0,007238 | 0,0146 ± 0,0079 [0,0030..0,0337] |
| RMS moyen du mix | 0,078001 | 0,097834 | 0,081084 | 0,0898 ± 0,0243 [0,0443..0,1360] |
| `dynamic_range_db` | 80,00 | 80,00 | 60,63 | 75,734 ± 8,531 [52,98..80,00] |
| Énergie HPSS harmonique / percussive | **94,18 / 5,82 %** | **93,68 / 6,32 %** | 86,32 / 13,68 % | 85,15 / 14,85 % (σ = 5,10 points) |

**Constats sûrs.** Viscera combine une densité d'attaques élevée (+1,39 σ)
et la **plus faible part percussive HPSS des 25 zones**. Cela n'implique
nullement une absence de kit : le stem batterie entre franchement dans la
seconde moitié (§3). Une attaque de basse distordue compte aussi comme
attaque ; HPSS mesure une décomposition énergétique, pas le pourcentage de
batterie. La famille Womb est spectralement sombre : ses centroïdes
1493–1784 Hz sont sous ceux de Caves (2024–2604 Hz), mais au-dessus de
Depths (1099–1450 Hz), dans cette même mesure fraîche.

`dynamic_range_db = max(rms_db) - min(rms_db)` : les silences, queues et
fondus des découpes de compilation dominent cette valeur, plafonnée ici à
80 dB pour deux pistes. **Ce n'est pas une plage EBU/LUFS ni une preuve de
contrastes de jeu de 80 dB.**

## 2. Tempo, mètre, calage et centres locaux

### Grilles retenues

Convention de lecture : **4/4 lent à 90 BPM**, 16 doubles-croches par
mesure ; une lecture deux fois plus rapide à 180 BPM subdivise les mêmes
événements. Le choix du premier temps n'a pas été arbitré à l'oreille :
confiance moyenne, plus faible sur la phase métrique de Viscera que sur sa
période. Il ne faut pas confondre une grille reproductible avec une édition
musicologique définitive.

| Paramètre | Viscera | Caesarian | Cicatrix |
|---|---:|---:|---:|
| `beat_s` | 0,66661 | 0,66667 | 0,66665 |
| `origin_s` | **0,28220** | **2,25293** | **0,82600** |
| `bar_s` | 2,66644 | 2,66668 | 2,66660 |
| Mesures entières | **68** | **67** | **71** |
| Fin des mesures entières (s) | 181,60012 | 180,92049 | 190,15460 |
| Résidu régression des attaques retenues (ms) | 11,35 | 12,89 | 11,10 |
| Attaques retenues / détectées | 312 / 620 | 420 / 723 | 689 / 754 |
| `R_beat/2`, hypothèse exacte 90 BPM | 0,3341 | 0,3501 | 0,3684 |
| `R_beat/3`, même hypothèse | 0,1762 | 0,2240 | 0,1346 |
| `R_beat/4`, même hypothèse | 0,3207 | 0,4114 | **0,8582** |

**Procédure de contrôle.** Détection à 22050 Hz, hop 128 ; stem `drums`
pour Viscera, mix pour les deux contextes. Essais `fit_beat` depuis
60/90/120/150/180/240 BPM, puis hypothèses explicites **45/90/180 BPM**.
Les fits bruts de Viscera à 89,927 BPM ont 94,95 ms de résidu ; le fit à
180,033 BPM a 20,11 ms. On ne conserve donc pas aveuglément le résultat
brut à 90. La régression finale porte sur les attaques à ±25 ms de la
grille de doubles-croches voisine de 90 BPM : estimation 90,0073,
89,9998 et 90,0027 BPM avant arrondi du JSON. Le résidu de 11–13 ms est
**conditionnel à cette sélection**, pas celui de toutes les attaques.

Le score ternaire est inférieur au meilleur score binaire pour les trois
pistes. À 180 BPM, scores binaire/ternaire : 0,3207/0,2299,
0,4114/0,3224, 0,8582/0,2931. À 45 BPM, le meilleur score binaire reste
0,3341, 0,3501 et 0,3684. Rien ici n'oblige à un 12/8 ; Cicatrix montre
très clairement la subdivision régulière de doubles-croches à 90.

Comparaison des 45 premières et dernières secondes, phase de la grille
fine raffinée : Viscera **124,0 → 103,5 ms** (écart 20,5 ms), Caesarian
84,8 → 75,8 ms (9,0 ms), Cicatrix 166,35 → 166,04 ms (0,31 ms, modulo une
double-croche). La cohérence début/fin de Viscera est seulement
0,247/0,488 : début peu percussif et nombreux événements hors de la grille
principale. L'origine utilise nouveauté chromatique et attaques graves ;
une autre numérotation de mesure à phase de temps équivalente reste possible.

### Tonique locale contre gabarit global

- **Viscera : centre grave Bb/A#**, pas F par simple lecture du chroma.
  PYIN sur le stem basse donne **834 / 1082 doubles-croches voisées sur
  Bb0 (77,1 %)** et 192 sur B0 (17,7 %). Le spectre grave confirme une
  large crête 28,94–30,95 Hz, et une harmonique forte 87,5–88,8 Hz.
  **B naturel est le voisin supérieur `b2` relatif à Bb**, mais le spectre
  et la basse saturée font envisager un glissement/modulation plutôt que
  192 notes B parfaitement tempérées. F, très fort dans le chroma moyen,
  peut être la quinte/harmonique de cette basse ; ce n'est pas une preuve
  de pédale F. La racine du détecteur d'accords est Bb dans 63/68 mesures.
- Le mix Viscera donne `estimated_key = F`, tandis que le gabarit de gamme
  donne **C# majeur / D# dorien ex aequo, marge 0**. Le stem `other` préfère
  D mineur harmonique, marge 0,0088. Ces résultats discordants interdisent
  de proclamer un mode unique. **Bb phrygien / pédale chromatique** est une
  hypothèse de couleur locale exploitable, pas une identification certaine
  de toutes les voix. Confiance haute sur la région Bb–B grave, moyenne
  sur Bb comme tonique fonctionnelle, faible à moyenne sur le mode.
- **Caesarian :** classe dominante globale E (`key_strength` 1,4537),
  gabarit **D mineur harmonique**, marge 0,0195 contre C éolien. Les crêtes
  graves du mix vers 36,3 et 41,7 Hz sont larges ; sans séparation dédiée,
  ne pas les transformer en une basse D certaine. Tonique locale non
  tranchée, contrairement à la lecture de Bb dans Viscera.
- **Cicatrix :** classe dominante globale G, gabarit **F mineur harmonique**,
  marge seulement 0,0026 contre C phrygien. Crêtes du mix 46–48 et
  96–97 Hz : énergie autour de F#/G, pas preuve de pédale F. Centre local
  à départager ; ne pas confondre détection de classe dominante et tonalité.

## 3. Structure complète de Viscera

Mesures 0-based, intervalles **début inclus, fin exclue**. Les frontières
ci-dessous combinent énergie des stems et chroma par mesure ; elles ne
proviennent pas d'une écoute. Le détecteur de nouveauté seul ne coupe
Viscera **nulle part** : le matériau harmonique reste très homogène.

| Section analytique | Mesures | Source (s) | Évidence et contenu probable |
|---|---:|---:|---|
| Avant-grille | — | **0–0,28220** | Résidu très faible ; RMS stems 0,000031–0,000091. Complément `pickup`, pas une levée mélodique certaine. |
| A0 — basse exposée | 0–4 | **0,282–10,948** | Basse RMS 0,05285 ; `other` seulement 0,00334 ; batterie 0,00868. |
| A1 — développement du bourdon | 4–16 | **10,948–42,945** | Basse 0,07316, nappe 0,01879 ; batterie très faible (0,00373). Boucles candidates de 8 mesures. |
| V1 — événement vocal/nappe | 16–20 | **42,945–53,611** | `vocals` monte à **0,01432**, contre environ 0,0001 hors événements. Pas preuve d'une voix humaine identifiable. |
| A2 — matière instrumentale | 20–32 | **53,611–85,608** | Nappe RMS 0,02380, basse 0,07387 ; kit encore discret (0,00461). |
| B — seconde exposition avec kit | 32–48 | **85,608–128,271** | Batterie **0,03773** ; environ huit fois le niveau de 20–32. Retour du matériau harmonique de la première moitié. |
| V2 — rappel vocal/nappe | 48–52 | **128,271–138,937** | `vocals` **0,01555** ; correspond à l'événement 16–20, 32 mesures plus tard. |
| B2 — prolongement avec kit | 52–64 | **138,937–170,934** | Batterie 0,03267, basse 0,07360 ; boucle de matériau, pas nouvelle modulation établie. |
| Coda / retrait du kit | 64–68 | **170,934–181,600** | Batterie retombe à 0,00879, basse à 0,04568 ; nappe monte à 0,03348. |
| Queue hors mesures | — | **181,60012–183,000** | Matière résiduelle non nulle : RMS `other` **0,001060**, basse 0,000320. Complément `tail`, pas un silence numérique. |

**Répétition de 32 mesures = 85,32608 s.** Similarité cosinus moyenne des
chroma de blocs correspondants : mes. 8–16 / 40–48 = **0,98982**,
16–24 / 48–56 = **0,98815**, 24–32 / 56–64 = **0,98965**.
Cependant, le score corrigé du fond de similarité de la longueur 32 n'est
que **0,0146** : presque tout se ressemble déjà. Il indique une reprise de
matériau, non une copie audio littérale et non une démonstration autonome
de forme. Le changement de batterie à 32 et les deux événements `vocals`
fournissent les indices indépendants. Boucles de travail **8 mesures** ;
macrocycle **32 mesures** ; aucune boucle de basse plus courte n'est
prouvée par la seule auto-similarité chromatique.

### Contexte : reprises et frontières des deux autres pistes

- **Caesarian**, grille 67 mesures : frontières de nouveauté à
  **31,59 ; 52,92 ; 116,92 ; 138,25 ; 172,92 s** (mes. 11, 19, 43, 51,
  64), puis fin entière 180,92049 et queue jusqu'à 183. Les frontières
  11/43 et 19/51 se répètent à +32 mesures. Blocs 16–24 / 48–56 :
  cosinus **0,99393** ; 24–32 / 56–64 : **0,99173**. Score de boucle
  32 corrigé **0,1240**, beaucoup plus discriminant que pour Viscera.
- **Cicatrix**, grille 71 mesures : changement à **11,49 s** (mes. 4),
  long corps jusqu'à **182,15 s** (mes. 68), puis coda jusqu'à
  190,15460 et queue jusqu'à 192. Correspondances 0–8 / 32–40 :
  **0,98995** ; 8–16 / 40–48 : **0,98524** ; 16–24 / 48–56 :
  **0,98655**. Score 32 corrigé **0,0595**. Le découpage de nouveauté
  grossier ne prétend pas supprimer les phrases internes.

## 4. Instrumentation probable et programmes GM

Stems de Viscera séparés par **htdemucs**, déjà fournis dans le corpus
partagé ; aucune seconde séparation n'a été lancée. Les RMS de stems ne
sont pas des pourcentages additifs : décomposition non orthogonale,
fuites et annulations possibles.

| Stem / rôle | Évidence sur toute la piste | Interprétation, confiance | GM **0-based** proposé pour la transcription |
|---|---|---|---|
| `bass` | RMS **0,070734** ; centroïde **214,86 Hz** ; platitude **0,000294** ; PYIN voisée **0,9694** | Basse grave très harmonique, saturée/modulée ; fondamentale Bb0–B0, harmoniques fortes. Haute sur région grave, moyenne sur instrument réel et octave. | **38 Synth Bass 1** ; alternative **34 Electric Bass (pick)** plus articulée |
| `drums` | RMS **0,025652** ; centroïde **3409,62 Hz** ; platitude **0,062507** ; forte montée vers 85,6 s | Kit rock/industriel, attaques bruiteuses, surtout seconde moitié. Haute sur présence/entrée ; moyenne sur type exact des coups. | Canal MIDI 10 : **36 Bass Drum 1**, **38 Acoustic Snare**, **42 Closed Hi-Hat** |
| `other` | RMS **0,023307** ; centroïde **1912,58 Hz** ; platitude **0,010633** | Nappe/texture harmonique médium, possibles cordes/synthé/guitare traitée ; pas assez pour nommer un instrument d'origine. Moyenne-faible. | **89 Pad 2 (warm)** ; **91 Pad 4 (choir)** pour une couleur plus chorale |
| `vocals` | RMS **0,006261** ; centroïde **2917,15 Hz** ; platitude **0,034416** ; événements 16–20 et 48–52 | Matière formantique/vocale ponctuelle, avec fuite instrumentale. Le nom de stem n'est pas une preuve de chant. Faible sur timbre, moyenne sur présence de deux événements. | **52 Choir Aahs** ; alternative **53 Voice Oohs** |

Le lead est transcrit depuis `vocals` avec un taux voisé global **0,4801**.
Ce taux **n'atteste pas 48 % de mélodie utile** : dans un stem presque vide,
PYIN peut suivre une harmonique de fuite. Ne pas convertir ses 287 événements
full en un solo omniprésent. Ni sifflement, ni GM30 ne sont proposés.

Presets Odin candidats, noms exacts des fichiers plats dans
`/Users/william.quintal/Project/bascanada/odin-presets/` :
**`Bass Crusher [RM].odin`**, **`Bass Low [RM].odin`**,
**`Growly FM Bass [XR].odin`**, **`Haunt [RM].odin`**,
**`Moonshade.odin`**, **`Eerie Pad.odin`**, **`Voices.odin`**.
Percussion éventuelle : `Kick-1 [Photonic].odin`, `Snare-1 [Photonic].odin`,
`HiHat-closed [Photonic].odin`. Ces candidats n'ont pas été écoutés ici.
Exclusions : **Phazzy Organ**, **Sausage Bassener sur notes rapides**,
lead sifflé et guitare distorsion GM30.

## 5. Transcriptions exécutées et couverture entière

Répertoire absolu :
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac/transcriptions/`.
Chaque nom ci-dessous existe sous les trois extensions **`.mid`, `.wav`,
`.json`**. Le rendu est réellement passé par fluidsynth / GeneralUser GS,
normalisé au pic **0,125**. C'est un rendu de réduction symbolique, pas un
stem reconstruit ni une imitation fidèle du mix original.

| Préfixe `09_viscera_` | Mesures | Source (s) | Événements basse / batterie / lead / accords | Usage et confiance |
|---|---:|---:|---:|---|
| `pickup` | fragment | **0–0,28220** | 1 / 2 / 1 / — | Résidu quasi silencieux, confiance musicale **très faible** |
| `full` | **0–68** | **0,282–181,600** | **340 / 355 / 287 / 68** | Réduction de tout le corps : basse haute, batterie moyenne, lead/qualité des accords faible |
| `bass_opening` | 0–8 | 0,282–21,614 | 31 / 29 / 31 / 8 | Bourdon exposé et premières textures |
| `development` | 8–16 | 21,614–42,945 | 32 / 37 / 28 / 8 | Voisin B récurrent ; basse assez sûre |
| `voices` | 16–24 | 42,945–64,277 | 38 / 39 / 31 / 8 | Événement formantique puis retour de nappe |
| `kit_entry` | 32–40 | 85,608–106,940 | 49 / 48 / 52 / 8 | Entrée de kit ; meilleur extrait pour la grille de batterie |
| `return` | 48–56 | 128,271–149,603 | 47 / 50 / 33 / 8 | Rappel d'événement vocal, seconde exposition |
| `coda` | 60–68 | 160,269–181,600 | 55 / 39 / 27 / 8 | Retrait du kit et queue harmonique |
| `tail` | fragment | **181,60012–183,000** | 2 / 3 / 1 / — | Queue réellement non nulle ; détection musicale **très faible** |

Couverture source : **[0 ; 0,28220] ∪ [0,28220 ; 181,60012] ∪
[181,60012 ; 183]**, sans partie musicale écartée par `floor(n_bars)`.
Les arrondis à la milliseconde des sidecars CLI expliquent `0,282` et
`181,600` ; les frontières exactes sont celles de la grille ci-dessus.
`pickup` et `tail` sont des fragments exportés avec un repère local et
`fragment = true`, **pas deux mesures ajoutées à la forme**. Leurs accords
sont omis, car ils ne contiennent pas une mesure entière. Les quelques
événements PYIN et coups très faibles sont conservés comme résultat brut,
non comme notes musicales assurées. La normalisation rend ces résidus
artificiellement audibles : ne pas comparer leur volume rendu au mix.
Le WAV contient aussi une traîne de synthèse au-delà de la durée source.

Limites : monophonie PYIN, lissage des octaves et quantification à la
double-croche ; aucune séparation de plusieurs notes de basse simultanées.
Le détecteur d'accords ne connaît que majeur/mineur et force une triade
même sur une nappe sans tierce. Aucun de ces exports n'est une partition
validée à l'oreille. Les contextes Caesarian/Cicatrix sont mesurés et
calés en entier, mais **ne sont pas présentés comme transcrits en stems**.

## 6. Grilles détaillées de Viscera

Grille **16 pas/mesure** à 90,008 BPM ; pas ≈166,65 ms. Degrés chromatiques
relatifs à **Bb = 0** : B = 1, C = 2, Db = 3, Eb = 5, F = 7,
Ab = 10, A = 11. Cette convention n'est pas le degré modal 1-based du moteur.

### 6.1 Basse : occupation des pas et non fausses réattaques

Vote des hauteurs sur mes. **8–16** :

```text
Position      0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
Degré / Bb    0  0  0  0  0  0  0  0  0  0  0  0  1  0  0  0
Votes / 8     7  5  5  8  8  7  8  8  5  7  8  8  8  8  8  8
```

Une case « 0 » signifie hauteur occupée, **pas attaque obligatoire**.
Exemple exact de la mesure 2 : Bb déjà tenu depuis la précédente,
**B pas 12, durée 2 → Bb pas 14, durée 14** (tenue dans la suivante).
Mesure 8 : B pas 0 durée 3 ; Bb pas 3 durée 2 ; Bb pas 6 durée 2 ;
Bb pas 9 durée 3 ; B pas 12 durée 1 ; Bb pas 13 durée 15.
Mes. 32–40 : B au pas 12 dans **7/8** mesures ; à 7 dans seulement 4/8.
Le voisin supérieur reste récurrent, mais sa durée et ses petites
oscillations changent. Une banque de motifs de 1–2 mesures est pertinente ;
la copie d'un pattern de 16 notes réattaquées serait trompeuse.

### 6.2 Batterie : vote sur l'entrée mes. 32–40

Résultat du classifieur spectral ; `X` ≥6/8, `x` =4–5/8, `.` <4/8.

```text
Position      0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
Kick  GM36    .  .  .  .  .  .  X  .  .  .  .  .  X  .  .  .
Snare GM38    .  .  X  .  .  .  .  .  .  .  .  .  .  .  X  .
Hat   GM42    .  .  .  .  .  .  .  .  .  .  x  .  .  .  .  .
```

Comptages exacts des appuis : kick6 **8/8**, kick12 **6/8** ; snare2
**7/8**, snare14 **8/8**, hat10 **5/8**. Mes. 48–56 : kick6 **7/8**,
kick12 **6/8**, snare14 **8/8** ; la classe au pas2 se partage entre
snare et hat. Positions mesurées sur **cette origine**, pas un backbeat
standard replaqué après coup. La classification peut confondre snare,
tom et cymbale, et les décalages de phase restent à écouter.
Marge moyenne globale **0,429**, coups de marge <0,15 : **8,5 %**.
Une caisse claire « forte » classée spectralement n'est pas une certitude
instrumentale ; les coups simultanés sont mal séparés.

### 6.3 Accords par mesure : résultat brut et interprétation

Premiers 16 résultats (une case = une mesure) :

```text
0–7 :  | Bbm | Bbm | Bb | Bb | Bb | Bbm | Bb | Bb |
8–15 : | Bb  | Bb  | Bbm| Bb | Fm | Bbm | Bb | Bb |
```

Racine Bb **63/68**, part 0,926, score moyen **0,859**. Exceptions :
**Fm mes.12**, **Db majeur mes.30,44,45,62**. Mes.16–20 : Bb majeur
quatre mesures ; mes.44–48 : Db, Db, Bbm, Bbm.

Ce n'est **pas** une preuve d'une modulation majeure/mineure à presque
chaque mesure : la tierce est contaminée par les textures. Lecture
musicale prudente : **pédale Bb avec frottement B**, couleur changeante,
et brèves régions F/Db à vérifier. Le profil proposé ci-dessous utilise
principalement une vraie pédale et des accords de contraste composés,
plutôt que de recopier les 68 triades du classifieur.

## 7. Proposition de données actuelles `isaac_womb`

**Proposition inspirée, distincte de la transcription. Aucun fichier moteur
modifié.** Le schéma a été lu dans `harmonium/profiles/README.md` et dans
les vrais `isaac_burning/profile.toml`, `cells.toml`, `feet.toml`.
Les blocs suivants sont des données concrètes à intégrer avec les réglages
généraux d'arrangement/dynamique/mix d'un profil existant ; ils ne prétendent
pas être à eux seuls un profil complet installable.

Choix : 4/4 lent, Bb phrygien comme **couleur générative volontaire**,
non comme vérité modale prouvée ; forme originale de 32 mesures **A A B A**,
parties de 8 mesures. A = pédale grave, B = respiration harmonique et
événement choral clairsemé. Pas de copie de la séquence exacte de Viscera.

```toml
[meta]
id = "isaac_womb"
name = "Womb de The Binding of Isaac (proposition)"
tradition = "Ridiculon, Womb — inspiration analytique, 2014-2021"
tags = ["isaac", "womb", "bourdon", "sombre"]
corpus = "harmonium_lab corpus/isaac/manifest.jsonl : 09 Viscera, 55 Caesarian, 35 Cicatrix ; droits réservés, analyse et inspiration seulement"

[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16
steps_per_unit = 2
steps_per_pulse = 4
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 90.0
min_bpm = 82.0
max_bpm = 100.0

[form]
sequence = [0, 0, 1, 0]
resolve = "per_tune"
repeat_variation = 0.12
tour_variation = 0.15
variation_operations = ["varied_end", "repeated_notes"]
varied_end_keep = 0.75
avoid_adjacent = false
[[form.parts]]
name = "A"
melody_center_offset = 0
phrase_ends = [8]
tracks_off = ["Melody"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]
[[form.parts]]
name = "B"
melody_center_offset = 0
phrase_ends = [8]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]

[melody]
cell_units = 8
strong_units = [0, 2, 4, 6]
weak_units = [1, 3, 5, 7]
key_modes = [{ key = 10, mode = "phrygian", weight = 1 }]
[melody.params]
weight_role_run = 2
weight_role_arp = 0
weight_role_turn = 0
max_continuity_step_distance = 2
continuity_max_retries = 8
melody_center_midi = 62
tonic_midi_min = 58
tonic_midi_max = 70
tessitura_min = 55
tessitura_max = 72
base_velocity = 52
strong_eighth_velocity_offset = 4
even_eighth_velocity_offset = -4
[melody.cells]
cells = [
  { role = "open", notes = "5 - - - 3 - - -", weight = 2 },
  { role = "open", notes = "8 - - - - - 5 -", weight = 1 },
  { role = "run", notes = "2 - - - 1 - - -", weight = 3 },
  { role = "run", notes = "3 - - - 2 - 1 -", weight = 1 },
]

[harmony]
model = "loop"
steps_per_chord = 16
default_bars_per_chord = 1
[harmony.parts.A]
kind = "pedal"
degree = 1
[harmony.parts.B]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { degree = 1, quality = "Minor", bars = 4 },
    { semitones = 3, quality = "Major", bars = 2 },
    { degree = 1, quality = "Minor", bars = 2 },
  ] },
  { weight = 1, chords = [
    { degree = 1, quality = "Minor", bars = 2 },
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 10, quality = "Major", bars = 2 },
    { degree = 1, quality = "Minor", bars = 2 },
  ] },
]

[accompaniment]
strong_steps = [0, 8]
strong_weight = 2
weak_weight = 1
tie_priority = ["I", "V", "IV"]
[accompaniment.bass]
low = 22
high = 34
[[accompaniment.bass.motifs]]
part = "A"
bars = 1
weight = 3
reference = "tonic"
notes = [
  { step = 0, duration = 12, semitones = 0, octave = 0, velocity = 92 },
  { step = 12, duration = 1, semitones = 1, octave = 0, velocity = 78, legato = true },
  { step = 13, duration = 3, semitones = 0, octave = 0, velocity = 88, legato = true },
]
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 1
reference = "tonic"
notes = [
  { step = 0, duration = 16, semitones = 0, octave = 0, velocity = 90 },
  { step = 16, duration = 10, semitones = 0, octave = 0, velocity = 86 },
  { step = 26, duration = 2, semitones = 1, octave = 0, velocity = 76, legato = true },
  { step = 28, duration = 4, semitones = 0, octave = 0, velocity = 88, legato = true },
]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 2
reference = "chord_root"
notes = [{ step = 0, duration = 16, semitones = 0, octave = 0, velocity = 86 }]
[[accompaniment.bass.motifs]]
part = "B"
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 8, semitones = 0, octave = 0, velocity = 88 },
  { step = 8, duration = 8, semitones = 0, octave = 0, velocity = 78 },
]
[accompaniment.chords]
center = 58
max_drift = 6
strings = 4
default_pattern = 0
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 54, tie = true }] }]

[instruments]
melody_program = 52
chords_program = 89
bass_program = 38
percussion_bank = 128
percussion_program = 0

[[odin.Bass.zones]]
when = { tension = [0.7, 1.0], arousal = [0.55, 1.0] }
preset = "Growly FM Bass [XR]"
level_db = -7.0
glide_ms = 18.0
morph = [{ param = "fil1_freq", arousal = 2000.0, tension = 1000.0 }]
[[odin.Bass.zones]]
when = { tension = [0.45, 1.0] }
preset = "Bass Low [RM]"
level_db = -5.0
glide_ms = 25.0
[[odin.Bass.zones]]
preset = "Bass Crusher [RM]"
level_db = -4.0
morph = [{ param = "fil1_freq", arousal = 1800.0 }]

[[odin.Chords.zones]]
when = { valence = [-1.0, -0.45], arousal = [0.0, 0.4] }
preset = "Eerie Pad"
level_db = -8.0
[[odin.Chords.zones]]
when = { tension = [0.6, 1.0] }
preset = "Moonshade"
level_db = -7.0
morph = [{ param = "fil1_freq", arousal = 1400.0 }]
[[odin.Chords.zones]]
preset = "Haunt [RM]"
level_db = -6.0

[[odin.Melody.zones]]
preset = "Voices"
level_db = -10.0
```

Les deux alternatives harmoniques B font **exactement 8 mesures**
(4+2+2 et 2+2+2+2). `degree = 1` est modal/1-based ; `semitones = 0`
serait le même centre chromatique. A n'ajoute pas B en nappe continue :
le voisin chromatique est une articulation de basse, pas nécessairement
une dyade persistante. Motifs de 1 ou 2 mesures divisant exactement les
parties de 8, choix pondérés conservés aux reprises selon la graine.
La banque de cellules est composée ici, non extraite de la piste.

Batterie proposée, **bloc `[percussion]` inline** dans le même profil
(équivalent à une banque `feet.toml`, où l'en-tête serait omis) :

```toml
[percussion]
heel_note = 36
toe_note = 38
heel_velocity = 88
toe_velocity = 78
feet_gain = 0.8
velocity_humanize = 4
[[percussion.patterns]]
density = 0
weight = 2
hits = [{ step = 6, track = "Heel" }, { step = 14, track = "Toe", delta_velocity = -12 }]
[[percussion.patterns]]
density = 0
weight = 1
hits = [{ step = 6, track = "Heel", delta_velocity = -12 }]
[[percussion.patterns]]
density = 1
weight = 3
hits = [
  { step = 2, track = "Toe", delta_velocity = -8 },
  { step = 6, track = "Heel" },
  { step = 12, track = "Heel", delta_velocity = -12 },
  { step = 14, track = "Toe" },
]
[[percussion.patterns]]
density = 1
weight = 1
hits = [
  { step = 6, track = "Heel" },
  { step = 10, track = "Toe", note = 42, delta_velocity = -24 },
  { step = 12, track = "Heel", delta_velocity = -12 },
  { step = 14, track = "Toe" },
]
[[percussion.patterns]]
density = 2
weight = 2
hits = [
  { step = 2, track = "Toe", delta_velocity = -8 },
  { step = 6, track = "Heel" },
  { step = 10, track = "Toe", note = 42, delta_velocity = -24 },
  { step = 12, track = "Heel", delta_velocity = -10 },
  { step = 14, track = "Toe" },
]
[[percussion.patterns]]
density = 2
weight = 1
hits = [
  { step = 2, track = "Toe", delta_velocity = -8 },
  { step = 6, track = "Heel" },
  { step = 10, track = "Toe", note = 42, delta_velocity = -28 },
  { step = 12, track = "Heel", delta_velocity = -10 },
  { step = 14, track = "Toe" },
  { step = 15, track = "Toe", note = 43, delta_velocity = -20 },
]
```

Ce ne sont pas des superpositions : une alternative est tirée par partie
et densité. Le dernier tom est **composé**, pas un coup certain de
l'original. Les zones Odin sont ordonnées ; la dernière de chaque piste
est bien le défaut sans `when`. Les seuils conjoints de Bass rendent la
zone FM dépendante de tension **et** d'activation ; bascule et morphing
suivent le mécanisme actuel, sans prétendre à une automation copiée.
Aucune zone Odin de batterie non prise en charge n'est inventée.

**Limites moteur à ne pas masquer.** Les accords sont entiers par mesure,
majeurs/mineurs ou pédales/dyades ; ni glissando microtonal Bb–B, ni texture
polytonale réelle, ni identification de timbres par htdemucs n'est exprimée
par ces données. Le legato MIDI/Odin est une approximation de la modulation
grave, pas sa transcription acoustique. La forme A A B A est volontairement
nouvelle ; les entrées d'arrangement ne doivent pas être vendues comme une
copie exacte du kit entrant à 85,6 s ni de ses retraits ultérieurs. Une
émulation des volumes de stems par mesure demanderait des automatismes non
décrits ici. L'enveloppe forte/faible doit être composée avec les mécanismes
d'arrangement et de dynamique existants lors de l'intégration du profil.

## 8. Reproduction et preuves d'exécution

Depuis ce worktree, utiliser **l'environnement du checkout principal**, pas
une `.venv` locale :

```bash
export PYTHONPATH=src
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
PY=/Users/william.quintal/Project/bascanada/harmonium_lab/.venv/bin/python
ROOT=/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac
SF=/Users/william.quintal/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2
```

La séparation utilise un environnement Demucs distinct de celui du labo ;
les quatre stems existants sont réutilisés sans recalcul :

```bash
PYTHONPATH=src /tmp/demucs-env/bin/python - <<'PY'
from pathlib import Path
from harmonium_lab.audioref.stems import separate
root = Path('/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac')
separate([('09_viscera', root / 'tracks/09_viscera.flac')],
         root / 'stems', model='htdemucs', device='mps', shifts=1)
PY
```

### Mesures avec les grilles retenues

```bash
"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$ROOT/manifest.jsonl" --corpus-root "$ROOT" \
  --filter 'id=09_viscera|55_caesarian|35_cicatrix' --context type=zone \
  --grids references/isaac-womb/grids.json --grid '{"estimate":false}' \
  --output /tmp/isaac-womb-measures.json
```

**Exécution réellement utilisée :** appel commun `--filter type=zone
--context type=zone --grid '{"estimate":false}'`, sortie
`/tmp/harmonium-017/isaac-niveaux-measures.json`, succès **25 pistes**, durée
254,73 s ; ajout des trois grilles sans relancer 25 analyses. La commande
ci-dessus reproduit les mêmes mesures mixtes et grilles ; elle ne crée pas
les diagnostics supplémentaires `analysis` (chroma/énergie des stems).

Pour refaire les contrôles de grille avec les fonctions du labo :
`onset_times`, `fit_beat(start_bpm=60,90,120,150,180,240)`,
`choose_tatum(onsets, 60/bpm)` à 45/90/180, puis régression
`np.polyfit(round((onsets-phase)/(beat_s/4)), onsets, 1)` sur les résidus
absolus <25 ms ; `estimate_grid(..., beat_s=4*slope,
tatums_per_beat=2, beats_per_bar=4)`. La phase initiale est celle de
`coherence(onsets, (2/3)/4)`. Les valeurs arrondies réellement exportées
sont celles de `grids.json`. La structure utilise `bar_chroma`,
`self_similarity`, `analyze_structure(max_loop_bars=40)` et le RMS des
échantillons de chaque intervalle de mesure. Les scores de toutes les
hypothèses, nombres d'inliers, phases début/fin, énergie par mesure et
correspondances de blocs sont conservés dans les deux JSON.

### Une seule transcription de toute la piste pour sept exports

```bash
"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/09_viscera.flac" \
  --stems "$ROOT/stems/htdemucs/09_viscera" --track-id 09_viscera \
  --grid '{"beat_s":0.66661,"tatums_per_beat":2,"beats_per_bar":4,"origin_s":0.2822}' \
  --tonic 'A#' --parts bass drums lead chords \
  --loop full:0:68 --loop bass_opening:0:8 --loop development:8:16 \
  --loop voices:16:24 --loop kit_entry:32:40 --loop return:48:56 --loop coda:60:68 \
  --bass-prog 38 --pad-prog 89 --lead-prog 52 \
  --soundfont "$SF" --out "$ROOT/transcriptions"
```

**Preuve :** CLI terminée avec succès en **16,56 s**, sept MIDI+JSON et
sept rendus WAV. Pics avant → après normalisation : full **0,170→0,125**,
ouverture 0,121→0,125, development 0,135→0,125, voices 0,160→0,125,
kit_entry 0,125→0,125, return 0,151→0,125, coda 0,167→0,125.
Lors de l'exécution initiale, la tonique de degrés était encore F ; les
**seuls degrés des sidecars** ont ensuite été recalculés par
`notes_to_degrees(notes, 10)` après constat de la basse Bb. Hauteurs MIDI,
rendus, grille et analyses de pitch n'ont pas été refaits. La commande
ci-dessus emploie directement la tonique locale finale.

### Compléments hors mesures, réellement transcrits et rendus

Le code suivant reproduit les deux fragments sans retraiter toute la
piste avec PYIN ; seuls 0,2822 et 1,39988 s sont analysés. Aucun audio
intermédiaire n'est écrit. Les sidecars donnent les **vrais temps source**,
non les fins de mesure fictives d'une grille d'export.

```bash
"$PY" - <<'PY'
import json
from pathlib import Path
import numpy as np
import librosa
from harmonium_lab.audioref.grid import Grid
from harmonium_lab.audioref.transcribe import (
    pitch_notes, drum_hits, notes_to_degrees, write_loop_midi,
)
from harmonium_lab.audioref.render import render_loop_wav
root = Path('/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac')
out = root / 'transcriptions'
sf = Path('/Users/william.quintal/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2')
sr, beat = 22050, 0.66661
stems = {s: librosa.load(root / 'stems/htdemucs/09_viscera' / f'{s}.wav', sr=sr)[0]
         for s in ('bass', 'drums', 'vocals')}
for name, start, end in [('pickup', 0.0, 0.2822),
                         ('tail', 0.2822 + 68 * 4 * beat, 183.0)]:
    seg = {s: y[round(start * sr):round(end * sr)] for s, y in stems.items()}
    g = Grid(beat, beat / 2, 2, 4, 0.0, end - start, {})
    parts = {}
    side = dict(track_id='09_viscera', loop=name, bars=[0, 1], fragment=True,
                source_start_s=start, source_end_s=end, grid=g.to_dict(),
                tonic='A#', tonic_pc=10)
    for stem, role, prog in [('bass', 'bass', 38), ('vocals', 'lead', 52)]:
        notes, info = pitch_notes(seg[stem], sr, g, role)
        parts[role] = (notes, prog)
        side[role] = dict(notes=notes_to_degrees(notes, 10), **info,
                          rms_source=float(np.sqrt(np.mean(seg[stem] ** 2))))
    hits, info = drum_hits(seg['drums'], sr, g)
    parts['drums'] = (hits, 0)
    side['drums'] = dict(hits=hits, **info)
    midi = out / f'09_viscera_{name}.mid'
    write_loop_midi(parts, g, midi, (0, 1))
    (out / f'09_viscera_{name}.json').write_text(
        json.dumps(side, ensure_ascii=False, indent=2) + '\n')
    print(name, start, end, render_loop_wav(midi, out / f'09_viscera_{name}.wav', sf))
PY
```

**Preuve :** compléments terminés avec succès en **11,36 s** ; `pickup`
0–0,2822 et `tail` 181,60012–183,0 ; pics rendus
**0,09155→0,125** et **0,09247→0,125**. Analyse temporelle et transcription
complètes sont donc exécutées, malgré la faible confiance musicale des
résidus. Contrôles techniques d'intégration réussis : JSON/TOML, presets,
lecture et couverture des 25 triplets privés ; tests du labo :
**286 réussis, 31 ignorés, 8 avertissements**. Périmètre détaillé dans le
[récapitulatif commun](../isaac-niveaux.md) ; aucun profil moteur installé.
