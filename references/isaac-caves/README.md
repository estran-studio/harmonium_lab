# Références Caves — *The Binding of Isaac* (Ridiculon)

Analyse de **Sodden Hollow** (Caves, Rebirth), avec **Capiticus Calvaria**
(Catacombs, Rebirth) et **Kave Diluvii** (Flooded Caves, Afterbirth) comme
contexte proche. Méthode : mesures du mix entier, régression de pulsation,
comparaison binaire/ternaire et demi/double tempo, nouveauté harmonique,
auto-similarité et énergie des stems ; transcription automatique complète
et extraits représentatifs ; proposition de données **distincte de la
transcription**, pour un futur `isaac_caves`.

**Provenance et droits.** Ridiculon (Matthias Bossi, Jon Evans), compilation
de fan MegaSamantha « The Binding of Isaac: Repentance - Full OST (HQ) »,
2021 : [Sodden Hollow, 621–875 s](https://www.youtube.com/watch?v=pSO4td4rdRI&t=621s),
[Capiticus Calvaria, 4355–4615 s](https://www.youtube.com/watch?v=pSO4td4rdRI&t=4355s),
[Kave Diluvii, 7236–7477 s](https://www.youtube.com/watch?v=pSO4td4rdRI&t=7236s).
Les temps ci-dessous sont **locaux aux FLAC**, pas ceux de la compilation.
Droits réservés : analyse et inspiration, aucune redistribution sonore.

Racine absolue du corpus, hors de ce worktree :
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac`.
Les FLAC sont dans `tracks/`, les quatre stems `htdemucs` de la principale
dans `stems/htdemucs/04_sodden_hollow/`, les MIDI/WAV/JSON de transcription
dans `transcriptions/`. **Seuls README.md, measures.json et grids.json sont
versionnés ici.** Aucune modification du moteur ni installation de profil.
L'analyse n'inclut pas d'audition humaine : les mots instrumentaux sont des
hypothèses, les hauteurs et coups ci-dessous des résultats d'extraction.

## 1. Mesures audio : trois pistes et contexte de 25 zones

`measures.json` conserve les **25 pistes** et les statistiques `context`
de la mesure fraîche commune, plus nos trois grilles vérifiées. Les
statistiques de contexte portent donc aussi sur les trois pistes étudiées,
comme dans la référence Basement ; ce n'est pas un groupe témoin disjoint.

| Mesure | Sodden Hollow | Capiticus Calvaria | Kave Diluvii | 25 zones : moyenne ± écart-type [min..max] |
|---|---:|---:|---:|---:|
| Durée du FLAC (s) | 254 | 260 | 241 | — |
| Tempo brut `beat_track` (BPM) | 123,0 | 117,5 | 117,5 | 114,7 ± 29,9 [49,7..215,3] |
| Tempo de grille retenu | **120** | **120** | **120** | — |
| Attaques / s | 1,50 | 1,52 | **2,60** | 1,86 ± 0,64 [0,75..2,99] |
| Stabilité de tempo | 0,9733 | 0,9741 | 0,9758 | 0,9709 ± 0,0096 |
| Force tonale | 1,5302 | 1,3221 | 1,3296 | 1,6503 ± 0,3543 |
| Entropie chroma (bits) | 3,5344 | 3,5473 | **3,5658** | 3,5098 ± 0,0391 [3,3727..3,5658] |
| Centroïde spectral (Hz) | 2 024,13 | **2 603,65** | 2 052,97 | 1 988,83 ± 481,99 [998,33..2 660,04] |
| Rolloff 85 % (Hz) | 4 442,38 | **5 844,17** | 4 610,55 | 4 336,82 ± 1 030,77 |
| Platitude spectrale | 0,016237 | **0,033733** | 0,013484 | 0,0146 ± 0,0079 |
| RMS moyen du mix | 0,066656 | 0,058993 | 0,078273 | 0,0898 ± 0,0243 |
| Plage RMS min–max (dB) | 71,86 | 80,00 | 52,98 | 75,73 ± 8,53 |
| Énergie HPSS harmonique / percussive | **75,27 / 24,73 %** | 88,30 / 11,70 % | 89,93 / 10,07 % | 85,15 / 14,85 % (écart-type 5,10 points) |

**Positionnement sûr.** *Sodden Hollow* a la part percussive HPSS la plus
forte des 25 zones (24,73 %, environ +1,94 σ), sans avoir le plus grand
nombre d'attaques. *Kave Diluvii* est plus dense en attaques, mais davantage
harmonique, et atteint l'entropie chromatique maximale du contexte.
*Capiticus* est nettement plus brillant (+1,28 σ de centroïde), avec le
rolloff maximal des 25 et une platitude élevée. Tous trois ont un RMS
moyen inférieur à la moyenne des zones.

**Précautions :** HPSS mesure une séparation d'énergie harmonique/percussive,
**pas** le pourcentage d'instruments de batterie. `dynamic_range_db` est
`max(rms_db) - min(rms_db)` : les silences et fondus de compilation peuvent
expliquer les 53–80 dB. Ce n'est ni une plage EBU R128, ni une mesure LUFS,
ni la dynamique musicale utile d'une section. La platitude ne suffit pas à
identifier une distorsion ou un instrument précis.

## 2. Tempo, mètre, phase, centres et modes

### 2.1 Calage sur les pistes entières

| Paramètre | Sodden Hollow | Capiticus Calvaria | Kave Diluvii |
|---|---:|---:|---:|
| Tempo régressé (BPM) | 120,00004 | 119,99890 | 120,00072 |
| Résidu temporel de la régression | 8,921 ms | 9,495 ms | 6,611 ms |
| Grille retenue | 4/4 binaire, 120 BPM | 4/4 binaire, 120 BPM | 4/4 binaire, 120 BPM |
| `beat_s` / `tatum_s` / `bar_s` | 0,5 / 0,25 / 2 s | idem | idem |
| `origin_s` | **0,82832** | **0,66402** | **0,52454** |
| Mesures pleines (`n_bars`) | 126 | 129 | 120 |
| Fin de dernière mesure pleine (s) | 252,82832 | 258,66402 | 240,52454 |
| Cohérence R à la croche P/2 | **0,0464** | 0,5647 | 0,4498 |
| R ternaire P/3 | 0,2689 | 0,0655 | 0,0837 |
| R double-croche P/4 | **0,8200** | **0,7550** | **0,8150** |
| Tempo premier / dernier tiers | 120,0037 / 119,9852 | 120,0016 / 119,9890 | 120,0091 / 119,9259 |

Régression de *Sodden* sur **le stem batterie**, des contextes sur **le mix**
(stems contextuels non nécessaires ici). La différence de tempo entre
premier et dernier tiers est très faible. Les phases absolues modulo 0,5 s
passent respectivement de 0,33996 à 0,33509 s, de 0,18030 à 0,17438 s et de
0,03660 à 0,01919 s. Le dernier tiers de *Kave* a un résidu plus fort
(39,72 ms contre 11,45 au début) : fin/fondu ou attaques plus ambiguës,
**pas une preuve d'accélération**. Les trois grilles à période exactement
0,5 s restent cohérentes du début à la fin.

Les candidats **60, 120 et 240 BPM** ont été comparés : à 60, les R à la
division par quatre ne valent que 0,0464 / 0,5647 / 0,4498 ; à 240, le R
croche reproduit mathématiquement le R double-croche à 120. Le double
n'apporte donc pas une nouvelle périodicité musicale. L'autocorrélation de
*Sodden* favorise 4 ou 8 temps (0,6273 / 0,6727), contre 0,4337 pour 2 temps :
**4/4 avec cycle de deux mesures**, plutôt qu'une preuve de 8/4. Le choix
120 reste une convention métrique appuyée par les accents, non une
certitude perceptive entre demi-temps et double-temps.

**Cas important : R croche faible n'implique pas ternaire.** Dans *Sodden*,
les attaques sur deux phases de croche se compensent ; leur concentration
sur les doubles-croches est forte. R(P/3)=0,269 reste très inférieur à
R(P/4)=0,820. Un estimateur qui compare seulement P/2 et P/3 choisirait à
tort une division ternaire. On conserve huit croches / seize pas par mesure.

L'origine de *Sodden* est contrainte à la phase de noire de la régression
(~0,3385 s modulo 0,5), puis départagée par nouveauté harmonique et attaques
graves. La phase P/4 est 0,07832 s modulo 0,125 ; le candidat **0,82832**
aligne la caisse claire dominante sur le temps 3, plutôt que de choisir le
contretemps harmonique 0,07832. Le score harmonique seul ne suffit donc pas
à fixer un premier temps. **Confiance haute sur tempo/division ; moyenne
sur premier temps et mètre perceptif**, y compris les deux contextes dont
la basse n'a pas été séparée. Les candidats et régressions figurent dans
`grids.json`, y compris les candidats d'origine rejetés.

### 2.2 Centre local contre gabarit global

| Piste | Gabarit global sur mix | Lecture locale et prudence |
|---|---|---|
| Sodden Hollow | C# mineur harmonique, score 0,8739, marge 0,0139 ; second A# mineur harmonique | **Pédale D#1** et **A0** dans l'ouverture, séparées d'un triton. D# ne doit pas être remplacé par C# parce que le gabarit global le préfère. Le détecteur de triades donne D# majeur puis A majeur, quatre mesures chacun, deux fois. Couleur locale chromatique / bipolaire, pas un mineur harmonique uniforme démontré. |
| Capiticus Calvaria | D mineur harmonique, 0,8641, marge 0,0200 ; second D majeur | Centre D et mode restent des hypothèses de mix. Sans basse isolée/transcription contextuelle, ne pas affirmer une pédale D locale ni une qualité d'accord certaine. |
| Kave Diluvii | D mineur harmonique, 0,8730, marge 0,0144 ; second C dorien | Ambiguïté forte et chroma très diffus ; D est une proposition globale, pas une tonique locale vérifiée. |

Sur la basse isolée de *Sodden*, imposer D# au gabarit donne lydien
0,8449 contre mixolydien 0,8442 (marge 0,0007). Sur `other`, D# phrygien
0,8515 et mixolydien 0,8512 sont presque égaux. Ces résultats **ne permettent
pas de nommer un mode unique**. Les centres D#/A et la descente chromatique
sont plus informatifs que l'étiquette modale. Le D# phrygien proposé en §7
est un choix de composition sombre, non une identification de l'original.

## 3. Structure complète de Sodden Hollow

Mesures **0-based**, plages `[début, fin)` ; une mesure vaut 2 s.
Découpage manuel de l'analyse, par changement d'énergie de basse,
répétition de chroma, résultats de transcription et fin de batterie.
L'algorithme de nouveauté seul ne voit que 0–60, 60–104, 104–112 et 112–126 :
il manque des contrastes d'orchestration sans changement harmonique net.

| Section | Mesures | Source (s) | Évidence et contenu | Unité / récurrence |
|---|---:|---:|---|---|
| Levée / attaque de compilation | hors grille | **0–0,82832** | Énergie réelle (RMS 0,01388, pic 0,24265), une hauteur F1 extraite ; timbre/hauteur de cette attaque peu sûrs | Complément transcrit, pas écarté comme silence |
| A — alternance de pôles | 0–16 | **0,82832–32,82832** | Pédale D# puis A, quatre mesures chacun ; basse RMS 0,00950, batterie 0,04631 | **8 mesures ×2**, cosinus chroma 0,9905 entre 0–8 et 8–16 |
| B — basse descendante au premier plan | 16–32 | **32,82832–64,82832** | Basse RMS **0,05814**, nappe 0,01909 ; attaque D# puis descente chromatique, détections d'octave fragiles | Cellule de **4 mesures ×4**, reprise à 72–88 |
| C1 — retrait de basse | 32–44 | **64,82832–88,82832** | Basse RMS **0,00114**, batterie maintenue 0,04585, `other` 0,04664 ; retour D#/A après transition | Transition 2 mes. puis matériau A réagencé ; pas un silence de kit |
| C2 — pédales plus mobiles | 44–56 | **88,82832–112,82832** | D#/A en blocs de 2 mes., passage G# en fin ; basse intermittente RMS 0,01408 | 4 à 8 mes., non strictement identiques |
| A' — retour enrichi | 56–72 | **112,82832–144,82832** | D#/A de nouveau, nappe plus forte (RMS 0,05724), gabarits F#m en fin | 16 mes. ; cosinus 0,9634 avec 0–16 |
| B' — reprise de la descente | 72–88 | **144,82832–176,82832** | Basse RMS **0,05706**, nappe 0,03575 ; départ du motif identique, contexte harmonique plus riche | 16 mes., cosinus **0,9844** avec 16–32 |
| C' — retour des pôles / nappe | 88–104 | **176,82832–208,82832** | Retrait de basse (0,00742), nappe **0,06053**, batterie 0,04456 | Reprise variée de C ; 32–56 / 88–112 : cosinus 0,9475 |
| Prolongation / préparation finale | 104–112 | **208,82832–224,82832** | A–D#–A selon triades, `other` 0,06360 ; batterie encore stable | 8 mes., pas une copie littérale du début |
| Coda active | 112–116 | **224,82832–232,82832** | Retour D#, basse 0,02284, voix/stem `vocals` plus présent (0,01327), batterie 0,03567 | 4 mes. |
| Extinction | 116–126 | **232,82832–252,82832** | Basse moyenne 0,00014, batterie 0,00199, `other` 0,00252 ; résidus/fondu, pas 10 mes. de véritable F#m | Pas une boucle jouable à reprendre telle quelle |
| Queue résiduelle | hors grille | **252,82832–254** | RMS **0,0000767**, pic 0,000343 ; très faible, mais pas silence numérique | Complément exact hors grille |

Le cosinus moyen au décalage **56 mesures = 112 s** vaut 0,9529.
Cependant son excès sur la similarité de fond n'est que **0,0586**
(4 mes. : 0,0196 ; 8 : 0,0268 ; 16 : 0,0089). Le chroma est similaire
presque partout : on ne transforme pas ces valeurs en « probabilité de
boucle ». La reprise 16–32 / 72–88, l'énergie de basse et les notes de
départ soutiennent mieux une grande récurrence de 56 mesures. Le tout
n'est **pas** une seule boucle de 126 mesures répétée exactement.

Contexte, sans prétendre une étude de structure aussi approfondie :
*Capiticus* a sa meilleure récurrence chromatique mesurée à 64 mesures
(cosinus moyen 0,9751), *Kave* à 56 (0,9785), sur leurs grilles de 120 BPM.
Ces similarités de mix seules n'établissent ni la longueur de leur riff,
ni les accords de chaque section.

## 4. Instrumentation probable, GM 0-based et Odin

Métriques sur les **stems entiers de Sodden Hollow**, pas identification de
la source réelle. La séparation redistribue parfois une même nappe entre
`bass`, `other` et `vocals` ; les RMS ne sont pas des pourcentages additifs.

| Stem / rôle | RMS | Centroïde (Hz) | Platitude | Hypothèse et programme GM **0-based** |
|---|---:|---:|---:|---|
| `bass` | 0,032896 | **874,19** | 0,042564 | Basse électronique / électrique très traitée, avec grave et glissements ; **38 Synth Bass 1**, alternative **34 Electric Bass (pick)**. Fondamentale stable D#1 ~38,9 Hz, puis A0 ~27,5 Hz ; octave très incertaine dans les descentes. |
| `drums` | **0,047214** | **3 926,08** | 0,100915 | Kit percussif bruité/brillant, kick grave et snare ; canal 10, Standard Kit programme 0, notes **36 Bass Drum 1**, **38 Acoustic Snare**, **42 Closed Hi-Hat**. Les bandes ne séparent pas tous les toms/cymbales. |
| `other` | 0,045006 | **1 546,15** | 0,004821 | Lit harmonique assez tonal, nappe/orgue ou cordes traitées probables ; **89 Pad 2 (warm)**, alternative **91 Pad 4 (choir)**. Un orgue rock serait **18**, non 19. Pas de preuve d'instrument acoustique exact. |
| `vocals` | **0,005716** | 2 204,59 | 0,063760 | Petite composante de nappe/chœur ou fuite des autres instruments ; **52 Choir Aahs**, alternative **53 Voice Oohs**. `voiced_ratio=0,514` ne prouve pas une voix humaine ni un vrai solo. |

Odin : fichiers présents dans le dossier **plat**
`/Users/william.quintal/Project/bascanada/odin-presets` :

- Basse : `Bass Low [RM].odin`, `Bass Crusher [RM].odin`,
  `Growly FM Bass [XR].odin` ; premier pour le grave contenu, deuxième
  pour les accents, troisième sous forte tension. L'équilibre de niveau
  reste une proposition non auditionnée.
- Nappe : `Haunt [RM].odin`, `Moonshade.odin`, `Eerie Pad.odin`.
  `Haunt` pour le fond sombre, `Moonshade` pour l'expansion tendue,
  `Eerie Pad` pour une valence très négative et une texture plus vide.
- Couleur vocale facultative : `Choir Aahs 1 [RS].odin`,
  `Voices.odin` ; ne pas inventer de ligne chantée à partir du seul stem.
- Batterie synthétique candidate : `Kick-1 [Photonic].odin`,
  `Snare-1 [Photonic].odin`, `HiHat-closed [Photonic].odin` ; le profil
  proposé conserve toutefois le kit SoundFont, pas des zones Odin sur
  `Heel`/`Toe` non documentées.

**Exclusions de cette proposition :** pas de Phazzy Organ, pas de Sausage
Bassener sur notes rapides, pas de sifflement, pas de GM 30. Aucun de ces
choix de timbre n'est présenté comme une audition comparative effectuée.

## 5. Transcription intégrale, boucles et confiance

Huit triplets `.mid` + `.wav` + `.json` existent **hors dépôt**, sous le
préfixe `04_sodden_hollow_` dans le dossier `transcriptions/` du corpus.
La principale a été analysée une fois par appel CLI, avec toutes les
boucles dans **un seul appel** sur la grille finale. Les compléments
non métriques traitent les bords sans les perdre par `floor(n_bars)`.

| Suffixe des fichiers | Mesures | Intervalle source exact (s) | Événements basse / batterie / lead / accords | Usage et confiance |
|---|---:|---:|---:|---|
| `full` | 0–126 | **0,82832–252,82832** | 292 / 909 / 379 / 126 | Toute la partie métrique, **pas seulement l'intro**. Haute couverture temporelle ; fidélité des notes variable selon section. |
| `pedal_intro` | 0–8 | **0,82832–16,82832** | 5 / 62 / 23 / 8 | D# puis A, demi-temps ; moyenne–haute pour les pôles, moyenne pour la tierce. |
| `bass_section` | 16–32 | **32,82832–64,82832** | 94 / 110 / 55 / 16 | Descente grave ; confiance **faible sur les octaves**, moyenne sur D#–D–C# du départ. |
| `bass_break` | 32–40 | **64,82832–80,82832** | 5 / 54 / 25 / 8 | Vérifie que retrait de basse ne signifie pas arrêt de batterie ; notes résiduelles peu sûres. |
| `reprise` | 72–88 | **144,82832–176,82832** | 86 / 127 / 42 / 16 | Reprise B', changement de nappe et même départ de basse ; moyenne sur les classes de hauteur, faible sur la fin des glissements. |
| `coda` | 112–126 | **224,82832–252,82832** | 3 / 83 / 17 / 14 | Coda **et extinction** ; les triades de fin incluent des détections de résidus, pas des accords certains. |
| `pickup` | fenêtre non métrique | **0–0,82832** | 1 / 1 / 0 / non inféré | F1 extrait ; une mesure technique couvrant la fenêtre, **pas** une indication métrique ni un nouveau tempo musical. |
| `tail` | fenêtre non métrique | **252,82832–254** | 0 / 6 / 0 / non inféré | Résidu quasi silencieux ; les six « coups » détectés ne sont pas validés comme batterie musicale. |

Les sidecars CLI arrondissent les bornes à la milliseconde (0,828 et
252,828) ; les valeurs exactes sont celles de la grille ci-dessus. Les
compléments consignent les bornes non arrondies. La couverture réunie est
bien **0–254 s**, sans tronquer levée ni queue.

Sur l'analyse entière : basse `voiced_ratio=0,6126`, lead 0,514 ; batterie
909 attaques, marge moyenne **0,395**, taux de marge <0,15 **8,5 %** ;
triades score moyen **0,873**, fondamentale la plus fréquente **A**, part
0,278. Un score de triade élevé signifie ressemblance spectrale, **pas**
validation harmonique ni preuve d'une pédale continue sur A.

**Limites importantes de la transcription automatique :**

1. `pyin` puis lissage d'octave peuvent ramener la longue descente à **G-1**
   ou à d'autres notes sous la plage acoustique analysée (25–300 Hz).
   Ces octaves sont des artefacts possibles du lissage et de la distorsion,
   pas une basse réelle de registre négatif. Les fichiers restent une
   transcription automatique de contrôle, non une partition corrigée.
2. Le stem `vocals` est faible et peut contenir une nappe polyphonique :
   les 379 événements lead ne doivent pas devenir une mélodie de 379 notes
   à recopier. Les degrés sont relatifs à D#, sans résoudre le mode global.
3. L'accord par mesure force une triade majeure ou mineure, même sur une
   pédale, un glissando ou le fondu. Les classes Cm/C#m/F#/D dans B et F#m
   à la fin sont particulièrement peu fiables comme accords écrits.
4. Les rendus `fluidsynth` ont terminé avec succès ; pic normalisé à
   **0,125**, après pics 0,176 (`full`), 0,117 (intro), 0,145 (B), 0,129
   (retrait), 0,160 (reprise), 0,152 (coda), 0,040 (levée), 0,121 (queue).
   **Cette normalisation amplifie aussi les faux coups de la queue** : son
   WAV n'est pas une restitution de son niveau d'origine. Aucun rendu n'a
   été écouté ici. Les durées WAV peuvent inclure la réverbération du synthé.

## 6. Grilles détaillées : basse, batterie, accords

### 6.1 Basse — seize doubles-croches par mesure

`step = 0,125 s`, positions 0..15. Degrés chromatiques par rapport à
**D# = 0**, et non degrés modaux du futur profil. `—` est une continuation,
`.` une absence de hauteur fiable, non une preuve de silence acoustique.

- Ouverture, mesures 0–3 : **D#1** tenu 64 pas, puis changement vers A.
- Mesure 4 : E1 très bref au pas 0, A0 aux pas **5–7**, **9–11**, **13–15**.
  E1 (voisin +1) peut être transition/glissando, pas un accord de mi.
- Retour stable 56–59 : D#1 tenu, malgré enrichissement des autres stems.

Départ de B, mesure 16 (identique au départ de B', mesure 72) :

```text
Pas            00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
Note extraite  D# —  —  —  —  —  —  —  D  —  —  C# —  —  C  B
Degré / D#      0  0  0  0  0  0  0  0 11 11 11 10 10 10  9  8
```

La descente se poursuit (mes. 17) vers Bb, A, G, F, E, mais les positions
fines et surtout les octaves deviennent peu fiables. Ne pas transformer
la sortie G-1 du détecteur en note musicale certaine. Dans B', les mesures
74–75 fournissent une relance mieux lisible : **G0**, puis **C1** au pas 7
et **C#1** au pas 9 (6 pas), retour C1 au pas 15 ; mesure suivante
C–B–Bb–A–Ab–A, puis C#→D# aux pas 14–15. Confiance moyenne sur les
classes, faible sur la tessiture exacte. Une cellule de quatre mesures est
plus crédible qu'un motif monophonique « exact » de toute la descente.

### 6.2 Batterie — vote sur les mesures 16–31

Nombre de mesures avec chaque classe au pas indiqué (16 observations,
chaque pas compté une fois par classe/mesure) :

```text
Pas             00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
Kick  GM 36      8  0  1  4  0  0  0  0  0  0  0  0  9  0  0  0
Snare GM 38      5  0  1  1  1 10  0  7 16  0  1  0  2  3  1  1
Hat   GM 42      1  0  3  3 14  3  1  7  0  0  0  4  0  0  2  1
```

Ossature : **caisse claire au temps 3 (pas 8, 16/16)**,
charleston/attaque brillante au temps 2 (pas 4, 14/16), grosse caisse au
temps 1 ou 4 selon la mesure (pas 0 : 8/16 ; pas 12 : 9/16). Des réponses
sur 5 et 7 densifient le groove. Il ne s'agit pas de trois instruments
parfaitement isolés : certains kick+snare/cymbale simultanés sont classés
dans une seule bande. Le profil §7 retient le demi-temps et les réponses,
**pas** la reproduction aveugle de toutes les détections.

### 6.3 Accords / pôles par mesure

- **A, 0–15 :** `[D#maj ×4, Amaj ×4] ×2`, scores de triades 0,821–0,985.
  Basse D#/A confirmée localement ; majeure/mineure reste à auditionner.
- **B, 16–31 :** détecteur `[Cm, C#m, C#m, D]`, puis principalement
  Cm/C#m avec G# ; le grave descend pendant que la nappe se raréfie.
  **Ce n'est pas une grille fonctionnelle validée.** La transcription MIDI
  plaque ces triades techniques pour rendre la comparaison possible.
- **C, 32–55 :** transition C#–Fm, retour de pôles D#/A, puis alternances
  de deux mesures ; G# vers 54–55.
- **A', 56–71 :** D# (4 mes.) → A (3) → F#m (1), puis D# (4) et
  A/F#m/A/D# (1 chacune) selon le gabarit. Les basses ne suivent pas
  nécessairement ces fondamentales de triades.
- **B', 72–87 :** nouveau départ de descente identique à B, triades
  Cm/C#m/F#/D, plus sensibles à l'enrichissement de la nappe.
- **Final, 112–115 :** D# puis D#m ; à partir de 116, ne pas tenir pour
  une vraie modulation les F#m répétés sur le fondu.

## 7. Proposition de données : futur `isaac_caves`

**Inspiration, pas reconstitution.** Conserver le contraste pédales / basse
descendante / nappe sans basse, le demi-temps, la tension du triton et une
forme de 56 mesures ; composer des cellules nouvelles. Les fragments
ci-dessous sont des données proposées, **pas un profil installé ou validé
par le chargeur moteur**. Ils spécifient mètre, forme, harmonie, basse,
cellules nouvelles, percussion et timbres ; ce n'est pas une livraison de
profil moteur autonome. Aucun fichier de profil n'est modifié ici. Le schéma est
celui du `profiles/README.md` actuel et des vrais `isaac_burning/profile.toml`
et `feet.toml`, pas celui des anciens exemples Basement.

### 7.1 Mètre, forme et alternatives harmoniques

Chaque partie a **8 mesures** et **chaque** alternative `loops` totalise
exactement 8. Les reprises conservent le choix par partie et par graine.
A = pôles contrastés, B = pédale et voisin chromatique, C = respiration
harmonique. La gamme D# phrygienne est une option de composition ; les
racines explicites chromatiques gardent leur intervalle si le mode change.

```toml
[meta]
id = "isaac_caves"
name = "Caves — pédales et descentes (proposition)"
tradition = "The Binding of Isaac, Caves — inspiration Ridiculon"
tags = ["isaac", "caves", "sombre", "demi-temps"]
corpus = "harmonium_lab references/isaac-caves ; analyse seulement, droits réservés"

[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16
steps_per_unit = 2
steps_per_pulse = 4
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 120.0
min_bpm = 108.0
max_bpm = 132.0

[form]
sequence = [0, 0, 1, 2, 0, 1, 2]
resolve = "per_tune"
[[form.parts]]
name = "A"
melody_center_offset = 0
phrase_ends = [8]
tracks_off = ["Melody"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]
[[form.parts]]
name = "B"
melody_center_offset = -3
phrase_ends = [8]
tracks_off = ["Melody"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]
[[form.parts]]
name = "C"
melody_center_offset = 0
phrase_ends = [8]
tracks_off = ["Bass"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]

[melody]
cell_units = 8
strong_units = [0, 2, 4, 6]
weak_units = [1, 3, 5, 7]
key_modes = [{ key = 3, mode = "phrygian", weight = 1 }]
[melody.params]
weight_role_run = 2
weight_role_arp = 0
weight_role_turn = 0
max_continuity_step_distance = 2
continuity_max_retries = 8
melody_center_midi = 63
tonic_midi_min = 60
tonic_midi_max = 72
tessitura_min = 55
tessitura_max = 75
base_velocity = 54
strong_eighth_velocity_offset = 3
even_eighth_velocity_offset = -4

[harmony]
model = "loop"
steps_per_chord = 16
default_bars_per_chord = 1
[harmony.parts.A]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { semitones = 0, quality = "Minor", bars = 2 },
    { semitones = 6, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 4 },
  ] },
  { weight = 1, chords = [
    { semitones = 0, quality = "Minor", bars = 4 },
    { semitones = 1, quality = "Major", bars = 2 },
    { semitones = 6, quality = "Major", bars = 2 },
  ] },
]
[harmony.parts.B]
kind = "pedal"
degree = 1
neighbor_semitones = 1
[harmony.parts.C]
kind = "chord_loop"
loops = [
  { weight = 2, chords = [
    { semitones = 10, quality = "Minor", bars = 2 },
    { semitones = 8, quality = "Major", bars = 2 },
    { semitones = 6, quality = "Major", bars = 2 },
    { semitones = 0, quality = "Minor", bars = 2 },
  ] },
  { weight = 1, chords = [
    { degree = 1, quality = "Minor", bars = 2 },
    { degree = 2, quality = "Major", bars = 2 },
    { degree = 6, quality = "Major", bars = 2 },
    { degree = 1, quality = "Minor", bars = 2 },
  ] },
]
```

Les degrés du TOML sont **1-based** (`degree=1` = tonique), contrairement
aux demi-tons 0..11 des racines et aux positions 0-based des motifs.
A n'est pas `[D#maj ×4, Amaj ×4]` recopié : durée, qualité et réponse sont
changées. C n'est pas la liste de triades incertaines du détecteur.

### 7.2 Motifs de basse pondérés, tenue de nappe et programmes

Banque alternative pour A et B ; C coupe Bass par la forme. Motifs
composés et quantifiés, pas les sorties d'octave aberrantes de `pyin`.

```toml
[accompaniment]
strong_steps = [0, 8]
strong_weight = 2
weak_weight = 1
tie_priority = ["I", "V", "IV"]
[accompaniment.bass]
low = 24
high = 47
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 3
reference = "chord_root"
notes = [
  { step = 0, duration = 16, semitones = 0, octave = 1, velocity = 92 },
  { step = 16, duration = 12, semitones = 0, octave = 1, velocity = 84 },
  { step = 28, duration = 4, semitones = 7, octave = 1, velocity = 70 },
]
[[accompaniment.bass.motifs]]
part = "A"
bars = 2
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 12, semitones = 0, octave = 1, velocity = 88 },
  { step = 12, duration = 4, semitones = 7, octave = 1, velocity = 70 },
  { step = 16, duration = 16, semitones = 0, octave = 1, velocity = 82 },
]
[[accompaniment.bass.motifs]]
part = "B"
bars = 2
weight = 2
reference = "tonic"
notes = [
  { step = 0, duration = 8, semitones = 0, octave = 1, velocity = 96 },
  { step = 8, duration = 4, semitones = -1, octave = 1, velocity = 84, legato = true },
  { step = 12, duration = 4, semitones = -2, octave = 1, velocity = 78, legato = true },
  { step = 16, duration = 8, semitones = 6, octave = 1, velocity = 86 },
  { step = 24, duration = 8, semitones = 0, octave = 1, velocity = 90, legato = true },
]
[[accompaniment.bass.motifs]]
part = "B"
bars = 2
weight = 1
reference = "tonic"
notes = [
  { step = 0, duration = 12, semitones = 0, octave = 1, velocity = 92 },
  { step = 12, duration = 4, semitones = 1, octave = 1, velocity = 78, legato = true },
  { step = 16, duration = 8, semitones = 0, octave = 1, velocity = 88, legato = true },
  { step = 24, duration = 4, semitones = -2, octave = 1, velocity = 74, legato = true },
  { step = 28, duration = 4, semitones = 0, octave = 1, velocity = 90, legato = true },
]
[accompaniment.chords]
center = 55
max_drift = 6
strings = 3
default_pattern = 0
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 56, tie = true }] }]

[instruments]
melody_program = 52
chords_program = 89
bass_program = 38
percussion_bank = 128
percussion_program = 0
```

Cellules de C **rares et longues**, en réponse de chœur de 2 à 4 mesures,
sans solo continu. Banque proposée de `cells.toml` (huit unités par cellule,
degrés modaux phrygiens ; `-` prolonge, ce n'est pas un silence) :

```toml
cells = [
  { role = "open", notes = "1 - - - - - 2 -", weight = 2 },
  { role = "open", notes = "5 - - - 3 - - -", weight = 1 },
  { role = "run", notes = "2 - - - 1 - - -", weight = 3 },
  { role = "run", notes = "3 - - - - - 1 -", weight = 2 },
  { role = "run", notes = "6 - - - 5 - - -", weight = 1 },
]
```

Le choix d'alternative n'est pas un changement à chaque mesure : la banque
est tirée selon les règles existantes par partie/air, puis conservée aux
reprises. Une graine différente ne doit pas seulement transposer la même
copie de la référence.

### 7.3 Batterie par graine — contenu proposé de feet.toml

Toutes les densités 0/1/2 sont couvertes ; alternatives d'une même densité
**exclusives**, non superposées. Les notes explicites 42 gardent le hat
sur le kit, sans changer le programme des autres pistes.

```toml
heel_note = 36
toe_note = 38
heel_velocity = 94
toe_velocity = 88
feet_gain = 1.0
velocity_humanize = 4

[[patterns]]
density = 0
weight = 1
hits = [{ step = 0, track = "Heel" }, { step = 8, track = "Toe" }]

[[patterns]]
density = 1
weight = 3
hits = [
  { step = 0, track = "Heel" },
  { step = 4, track = "Toe", note = 42, delta_velocity = -26 },
  { step = 8, track = "Toe" },
  { step = 12, track = "Heel", delta_velocity = -10 },
]
[[patterns]]
density = 1
weight = 1
hits = [
  { step = 0, track = "Heel" },
  { step = 4, track = "Toe", note = 42, delta_velocity = -30 },
  { step = 7, track = "Toe", delta_velocity = -24 },
  { step = 8, track = "Toe" },
  { step = 14, track = "Heel", delta_velocity = -16 },
]

[[patterns]]
density = 2
weight = 2
hits = [
  { step = 0, track = "Heel" },
  { step = 2, track = "Toe", note = 42, delta_velocity = -38 },
  { step = 4, track = "Toe", note = 42, delta_velocity = -26 },
  { step = 5, track = "Toe", delta_velocity = -25 },
  { step = 8, track = "Toe" },
  { step = 10, track = "Toe", note = 42, delta_velocity = -36 },
  { step = 12, track = "Heel", delta_velocity = -10 },
  { step = 14, track = "Toe", note = 42, delta_velocity = -32 },
]
[[patterns]]
density = 2
weight = 1
hits = [
  { step = 0, track = "Heel" },
  { step = 3, track = "Heel", delta_velocity = -18 },
  { step = 4, track = "Toe", note = 42, delta_velocity = -26 },
  { step = 7, track = "Toe", delta_velocity = -24 },
  { step = 8, track = "Toe" },
  { step = 11, track = "Toe", note = 42, delta_velocity = -32 },
  { step = 12, track = "Heel", delta_velocity = -12 },
  { step = 15, track = "Toe", note = 42, delta_velocity = -40 },
]
```

### 7.4 Zones Odin émotionnelles (noms exacts, défaut final)

Les champs `preset` sont les noms sans extension `.odin` des fichiers plats
énumérés au §4. Programmes SoundFont maintenus pour les rendus sans Odin.
Les niveaux sont des points de départ de composition, pas un mix écouté.

```toml
[[odin.Bass.zones]]
when = { tension = [0.7, 1.0] }
preset = "Growly FM Bass [XR]"
level_db = -7.0
glide_ms = 55.0
morph = [{ param = "fil1_freq", arousal = 2200.0, tension = 900.0 }]
[[odin.Bass.zones]]
when = { arousal = [0.65, 1.0] }
preset = "Bass Crusher [RM]"
level_db = -3.0
glide_ms = 25.0
morph = [{ param = "fil1_freq", arousal = 1800.0, tension = 600.0 }]
[[odin.Bass.zones]]
preset = "Bass Low [RM]"
level_db = -5.0
glide_ms = 35.0
morph = [{ param = "fil1_freq", arousal = 1200.0 }]

[[odin.Chords.zones]]
when = { tension = [0.65, 1.0] }
preset = "Moonshade"
level_db = -7.0
morph = [{ param = "fil1_freq", arousal = 1600.0, valence = 600.0 }]
[[odin.Chords.zones]]
when = { valence = [-1.0, -0.4] }
preset = "Eerie Pad"
level_db = -8.0
morph = [{ param = "env1_release", density = 0.5 }]
[[odin.Chords.zones]]
preset = "Haunt [RM]"
level_db = -4.0
morph = [{ param = "fil1_freq", arousal = 1200.0, valence = 600.0 }]
```

La priorité va à la première zone admissible ; la dernière n'a pas de
`when`. L'hystérésis 0,03 et la frontière de partie suivent le comportement
moteur actuel. Le glissando concerne les notes `legato`, pas les répétitions
réattaquées ; le SoundFont ne devient pas portamento par cette donnée.

**Limites moteur / données.** Le schéma actuel de boucle harmonique change
d'accord aux mesures entières : il ne représente pas une harmonie qui
glisse continûment, une tierce ambiguë, un accord slash ou une transition
intra-mesure. Une pédale avec voisin exprime une dyade, pas une nappe
spectrale complexe. Les motifs peuvent exprimer une descente discrète,
mais pas garantir les courbes de pitch réelles ni la distorsion de la basse
originale. `tracks_off` peut créer un contraste de section, pas copier un
fondu de compilation. Aucun ajout moteur n'est nécessaire pour les
fragments proposés ; la restitution littérale de l'enregistrement ne doit
pas être promise par ces données.

## 8. Reproduction et preuves d'exécution

Depuis la racine de ce worktree :

```bash
export CORPUS=/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac
export PY=/Users/william.quintal/Project/bascanada/harmonium_lab/.venv/bin/python
export SF=/Users/william.quintal/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2
export PYTHONPATH=src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2

"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$CORPUS/manifest.jsonl" --corpus-root "$CORPUS" \
  --filter 'id=04_sodden_hollow|22_capiticus_calvaria|37_kave_diluvii' \
  --context type=zone --grids references/isaac-caves/grids.json \
  --grid '{"estimate":false}' --output /tmp/isaac-caves-measures.json

"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$CORPUS/tracks/04_sodden_hollow.flac" \
  --stems "$CORPUS/stems/htdemucs/04_sodden_hollow" \
  --track-id 04_sodden_hollow \
  --grid '{"beat_s":0.5,"tatums_per_beat":2,"beats_per_bar":4,"origin_s":0.82832}' \
  --tonic 'D#' --loop full:0:126 --loop pedal_intro:0:8 \
  --loop bass_section:16:32 --loop bass_break:32:40 \
  --loop reprise:72:88 --loop coda:112:126 \
  --parts bass drums lead chords --bass-prog 38 --pad-prog 89 --lead-prog 52 \
  --soundfont "$SF" --out "$CORPUS/transcriptions"
```

**Exécuté :** mesure fraîche commune des 25 zones, sans estimation de grille,
en 254,73 s ; réemploi sans recalcul des statistiques, ajout de nos trois
grilles dans `tracks.<id>.grid`. Commande commune : même environnement et
même `--manifest`/`--corpus-root`, `--filter type=zone --context type=zone
--grid '{"estimate":false}' --output /tmp/harmonium-017/isaac-niveaux-measures.json`.
La commande filtrée ci-dessus est la reproduction spécifique du livrable,
non un second calcul de 25 zones effectué par cet agent.

**Exécuté :** analyses de grille (piste entière et tiers), comparaison des
subdivisions/tempos, stems, structure et transcription CLI finale en
**30,55 s**, code retour 0, six triplets rendus. Deux compléments de bord
rendus en **7,58 s**, code retour 0. Une première transcription sur origine
harmonique de contretemps a été remplacée par celle sur origine 0,82832 ;
les noms du tableau §5 désignent exclusivement la sortie finale.

Pour reproduire la séparation principale si elle n'existe pas (le calcul
présent a **réutilisé** les quatre stems `htdemucs` produits sur MPS, sans
les séparer une deuxième fois) :

```bash
PYTHONPATH=src /tmp/demucs-env/bin/python - <<'PY'
import os
from pathlib import Path
from harmonium_lab.audioref.stems import separate
r = Path(os.environ["CORPUS"])
separate([("04_sodden_hollow", r / "tracks/04_sodden_hollow.flac")],
         r / "stems", model="htdemucs", device="mps", shifts=1)
PY
```

Reproduction des régressions, mesures de timbre et structure :

```bash
"$PY" - <<'PY'
import json, os
from pathlib import Path
import librosa
import numpy as np
from harmonium_lab.audioref.grid import Grid, fit_beat, onset_times, coherence
from harmonium_lab.audioref.structure import analyze_structure
r = Path(os.environ["CORPUS"])
grids = json.loads(Path("references/isaac-caves/grids.json").read_text())
for tid, d in grids.items():
    mix, sr = librosa.load(r / "tracks" / (tid + ".flac"), sr=22050)
    drum = r / "stems/htdemucs" / tid / "drums.wav"
    rhythm = librosa.load(drum, sr=sr)[0] if drum.exists() else mix
    p, phase, resid = fit_beat(rhythm, sr)
    times = onset_times(rhythm, sr)
    print(tid, "period/phase/residual", p, phase, resid)
    for factor in (0.5, 1.0, 2.0):
        print("BPM", 60 / (p * factor),
              {k: coherence(times, p * factor / k)[0] for k in (1, 2, 3, 4)})
    g = Grid(**{k: d[k] for k in ("beat_s", "tatum_s", "tatums_per_beat",
                                 "beats_per_bar", "origin_s", "duration_s")})
    print("structure", analyze_structure(mix, g, sr, max_loop_bars=64))
    if tid == "04_sodden_hollow":
        for name in ("bass", "drums", "other", "vocals"):
            y = librosa.load(r / "stems/htdemucs" / tid / (name + ".wav"), sr=sr)[0]
            s = np.abs(librosa.stft(y))
            print(name, "RMS/centroid/flatness", np.sqrt(np.mean(y*y)),
                  librosa.feature.spectral_centroid(S=s, sr=sr).mean(),
                  librosa.feature.spectral_flatness(S=s).mean())
PY
```

Les deux bords ne sont pas des mesures musicales. Cette commande utilise
les mêmes fonctions de transcription/rendu sur leurs fenêtres exactes ;
le découpage ne crée aucun nouveau fichier audio source :

```bash
"$PY" - <<'PY'
import json, os
from pathlib import Path
import librosa
import numpy as np
from harmonium_lab.audioref.grid import Grid
from harmonium_lab.audioref.transcribe import pitch_notes, drum_hits, notes_to_degrees, write_loop_midi
from harmonium_lab.audioref.render import render_loop_wav
r = Path(os.environ["CORPUS"])
tid = "04_sodden_hollow"
out = r / "transcriptions"
for name, start, end in (("pickup", 0, 0.82832), ("tail", 252.82832, 254)):
    g = Grid((end-start)/4, (end-start)/8, 2, 4, 0, end-start)
    parts = {}
    side = {"track_id": tid, "loop": name, "source_start_s": start,
            "source_end_s": end, "grid_role": "non-metric one-window edge; no tempo inference",
            "grid": g.to_dict(), "source_duration_s": end-start}
    for role, stem, program in (("bass", "bass", 38), ("lead", "vocals", 52)):
        y, sr = librosa.load(r / "stems/htdemucs" / tid / (stem+".wav"),
                             sr=22050, offset=start, duration=end-start)
        notes, info = pitch_notes(y, sr, g, role)
        parts[role] = (notes, program)
        side[role] = {"notes": notes_to_degrees(notes, 3), **info}
    y, sr = librosa.load(r / "stems/htdemucs" / tid / "drums.wav",
                         sr=22050, offset=start, duration=end-start)
    hits, info = drum_hits(y, sr, g)
    parts["drums"] = (hits, 0)
    side["drums"] = {"hits": hits, **info}
    mix, sr = librosa.load(r / "tracks" / (tid+".flac"),
                           sr=22050, offset=start, duration=end-start)
    side["source_audio"] = {"rms": float(np.sqrt(np.mean(mix*mix))),
                            "peak": float(abs(mix).max()),
                            "interpretation": "non-metric compilation edge; drum residual detections and pitch errors require audition"}
    midi = out / (tid+"_"+name+".mid")
    write_loop_midi(parts, g, midi, (0, 1))
    (out / (tid+"_"+name+".json")).write_text(json.dumps(side, indent=2))
    print(name, render_loop_wav(midi, out / (tid+"_"+name+".wav"), Path(os.environ["SF"])))
PY
```

**Contrôle restant humain, non prétendu exécuté :** audition de la levée
0–0,828 s, choix du premier temps, tierces D#/A de l'ouverture, registre et
courbe de la descente 32,828–64,828 s et sa reprise, vraie nature du stem
`vocals`, distinction coups réels / fuite dans l'extinction. Contrôles
techniques d'intégration réussis : JSON/TOML, presets et 25 triplets privés ;
tests du labo : **286 réussis, 31 ignorés, 8 avertissements**. Voir le
[récapitulatif commun](../isaac-niveaux.md) pour le périmètre de vérification.
