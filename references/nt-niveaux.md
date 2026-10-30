# Nouveaux niveaux — références labo *Nuclear Throne*

Brief L : trois dossiers d'analyse, **quatre pistes principales intégrales**, deux
pistes de contexte en mesures audio seulement. Jukio Kallio / Vlambeer, OST 2015.
Le [manifeste de provenance](https://www.youtube.com/watch?v=Jk5jogaEsz8) du corpus
local précise les coupes et les droits. Méthode G9-G0 des références
[Isaac Basement](isaac-basement/README.md) et [NT Desert](nt-desert/README.md).

## Ce qui distingue les niveaux

Tempos du tableau **calés numériquement**, non déduits du seul `beat_track`.
Les modes sont locaux et accompagnés de leur incertitude dans chaque dossier.

| Niveau / piste | Tempo et mètre | Centre / mode retenu | Caractère | Instruments probables / candidats privilégiés | Différence dans le jeu |
|---|---|---|---|---|---|
| [Sewers — Groundwork of the Past](nt-sewers/README.md) | **80 BPM, 4/4**, lecture double 160 ; demi-temps de confiance moyenne | **D** puis pôles **C/E/A** ; modal/chromatique, choix de profil D mixolydien, mode unique non démontré | Sombre, pédale puis roulements bruités, contraste de blocs | Basse synthé, nappe et ligne médium ; **Bass Low [RM] / Haunt [RM]**, Crusher/Moonshade sous tension | Plus retenu et sombre que Desert A ; pas son shuffle 12/8. Le contexte Pizza est au contraire très brillant et percussif |
| [Scrapyard — Mt. Rubble / Secret Entrance](nt-scrapyard/README.md) | A **120 BPM, 4/4** ; B **105,055 BPM, 4/4** pulsé sans kit établi | A pôle **B**, phrygien/mineur chromatique incertain ; B **A/D**, mineur harmonique ↔ couleur phrygienne | A : riff saturé, kit et mix soutenu ; B : nappe articulée presque sans percussion | A : basse piquée, synthé médium, kit ; **Bass Crusher [RM] / Growly FM Bass [XR]**. B : **Eerie Pad / Haunt [RM]** | Plus franc et percussif que Sewers ; contraste A/B extrême, mais B reste pulsé, contrairement à l'absence de battue décrite pour Desert B |
| [Crystal Caves — Crystallized Fear](nt-crystal-caves/README.md) | **140 BPM pointées, 12/8** = **210 BPM à la noire** | **A phrygien** (A/Bb), pont **A mineur harmonique** (E/G#) ; confiance moyenne–haute localement | Alternance de thème léger, bloc dense et pont harmonique ; reprise longue | Basse bruitée, nappe claire, ligne/résonances aiguës, kit ponctuel ; **Bass Low [RM] / Eerie Pad**, Moonshade et éventuelles Ethereal Bells | Même famille ternaire que Desert A, mais alternance Bb/A et sensible G# au pont, cycles harmoniques plus développés ; Cursed n'a pas de grille globale validée |

Les programmes GM 0-based et **noms exacts `.odin`** figurent dans chaque README.
Les presets sont des candidats de rendu non écoutés ici, pas les instruments
identifiés de l'original. Goûts respectés : pas de Phazzy Organ, de Sausage
Bassener rapide, de sifflement ni de guitare saturée GM 30.

## Périmètre et fichiers

Chaque dossier contient **README.md, measures.json, grids.json**. Les mesures
comprennent les **20 pistes `type=zone`**, nécessaires à la mise en contexte ;
seules les pistes propres au dossier ont une grille ajoutée. `33 Is This Happening`
n'a pas de grille fixe : le balayage testé ne la valide pas. Ne pas substituer
198,8 BPM brut à un tempo musical vérifié.

Les pistes intégralement séparées et transcrites sont :

- 04 `groundwork_of_the_past` : **7 triplets** ;
- 05 `mt_rubble` : **7 triplets** ;
- 21 `secret_entrance` : **7 triplets**, lead/accords, sans transformer les fuites
  de basse/batterie en instruments indépendants ;
- 08 `crystallized_fear` : **9 triplets**.

Soit **30 MIDI + 30 WAV + 30 sidecars JSON**, dont quatre intégrales couvrant
respectivement les sources de **137, 95, 111 et 141 secondes**. Les extraits
couvrent les matériaux de toutes les sections ; les lacunes de pYIN sont
signalées, pas complétées par des notes inventées. Les pistes 31 Pizza et
33 Cursed n'ont fait l'objet que de mesures du mix, conformément au périmètre.

**Principe VII :** manifeste source, enregistrements, quatre stems par piste et
tous les événements de transcription restent exclusivement sous :

```text
~/Project/bascanada/harmonium_lab/corpus/nuclear_throne/
  manifest.jsonl
  tracks/<id>.flac
  stems/htdemucs/<id>/{bass,drums,other,vocals}.wav
  transcriptions/<id>_<extrait>.{mid,wav,json}
```

Aucun de ces fichiers n'est ajouté au worktree. Les grilles et réductions des
READMEs sont des dérivés analytiques, pas les transcriptions événementielles.
Aucun autre dossier `references/` ni fichier du dépôt moteur n'est modifié.

## Conventions et confiance

- Mesures **0-based**, fin exclue. Les coupes OST peuvent commencer au milieu
  d'une mesure. L'origine théorique précède alors zéro ; mesure 0 partielle,
  mesure 1 au premier temps positif. La transcription intégrale garde amorce
  et fin partielle ; les temps théoriques hors fichier représentent du silence.
- Binaire : **16 pas** ; 12/8 : **24 pas**. Dans le moteur et le MIDI, le BPM
  est à la noire : **140 pointées → 210**, pas 140 dans `meter.default_bpm`.
- Calage : attaques du mix (`onset_times`, hop 128 à 22 050 Hz), concentration
  circulaire, optimisation locale du tempo, vérification des lectures moitié/
  double et binaire/ternaire ; phase par nouveauté chroma et attaques graves,
  recoupée avec les stems. Résidus sur la **subdivision indiquée**, pas sur
  tous les temps forts. Phase/mètre restent moins certains que la subdivision.
- Structure : `bar_chroma`, `self_similarity`, `loop_scores` ; le score est le
  cosinus au retard moins le fond hors diagonale, **pas une corrélation audio**.
  Recherche des reprises longues jusqu'aux retards laissant huit paires, au-delà
  du défaut de 16 mesures ; énergie des stems pour les frontières d'arrangement.
- Mode : gabarit global et mode avec tonique locale fixée sont séparés ; une
  marge nulle entre relatifs n'établit pas une tonalité. Force tonale, voisement
  et scores d'accord ne sont pas des probabilités de justesse.
- Batterie : classification spectrale kick/snare/hat et vote par mesure. Une
  attaque simultanée ne peut donner plusieurs classes ; manque de kick ou de
  cymbale détecté ne signifie pas absence audible. Les cas ambigus sont nommés.
- Stems demucs : fuites et séparation par rôle, pas preuve de voix humaine ou
  d'instrument exact. **Aucune validation auditive humaine revendiquée.**
- `dynamic_range_db = 80` sur toutes les zones est un plafond non discriminant.
  RMS et contrastes de blocs sont plus utiles ; ne pas le présenter comme une
  dynamique musicale mesurée de 80 dB.

## Propositions de profils et limites du schéma

Les trois §7 emploient le **schéma actuel** lu dans le README moteur et dans
`profiles/isaac_burning/` :

- `harmony.parts` avec `loops = [{weight, chords}]` ; alternatives entières de
  **8 mesures**, choix par graine conservé aux reprises ; pédale `degree = 1`
  lorsque nécessaire, jamais l'ancien degré 0 ;
- pieds `[[patterns]]` pondérés, densités 0/1/2, notes GM par coup ;
- `accompaniment.bass.motifs` pondérés, intervalles relatifs et durées en pas,
  références `tonic`/`chord_root`, silences et tenues explicites ;
- `[[odin.<Piste>.zones]]` ordonnées, conditions émotionnelles et défaut final
  sans `when` ; fichiers fournis par l'hôte, Heel/Toe demeurent SoundFont.

Ce sont des **propositions de données composées**, pas des profils complets
installés ou des profils chargés/testés dans le moteur. Les sections communes
obligatoires suivent le profil réel cité ; aucune modification moteur n'est faite.
Poids et niveaux proposés ne sont pas des fréquences ni des balances apprises.

Aucun ajout moteur bloquant pour ces réductions. Limites de fidélité à ne pas
masquer : tempo automatique par partie non décrit (Scrapyard A/B ont des BPM
différents), triades Major/Minor plutôt que boucles de dyades sans tierce
(Crystal Caves), mode lydien explicite absent de la liste documentée mais lecture
incertaine (Sewers). Les zones émotionnelles ne suivent pas automatiquement les
noms de parties. Le contexte Cursed n'autorise pas encore une proposition de
profil à grille fixe.

## Reproduction et validation

Les commandes complètes `audioref-measures --corpus-root`, séparation puis
`audioref-loops` figurent dans chacun des trois READMEs. Elles lisent le checkout
principal et y écrivent les sorties sous droits. Les grilles fournies permettent
de rejouer exactement le découpage ; les limites d'inférence sont conservées.

Versions employées : **librosa 1.0.0, NumPy 2.5.4, SciPy 1.18.1, mido 1.3.3,
soundfile 0.14.0**, Python 3.14.7 pour le labo ; **demucs 4.1.0**, Python 3.11.14,
CPU, `htdemucs`, `shifts=1` pour la séparation ; **FluidSynth 2.5.3**, banque
`~/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2` pour les WAV.
Les quatre stems sont calculés sur chaque piste principale entière ; cache
réutilisable, aucune séparation supplémentaire pour les deux contextes.

Les 30 extractions ont été exécutées par la CLI, puis les MIDI relus, les WAV
décodés et leurs pics contrôlés à **0,125**. Le rendu comprend les relâchements
FluidSynth : sa durée n'est pas une nouvelle longueur de boucle source.

Un défaut bloquait l'intégrale de Mt. Rubble : le lissage d'octave accumulait
les transpositions jusqu'à MIDI **352**. Correction limitée au labo : déplacements
d'octave bornés au registre pYIN, classes de hauteur conservées, **sans clamp à
127**. Les 30 extractions sont régénérées après correction ; une régression
synthétique couvre cette dérive et les alias d'octave ordinaires.

Commande des tests, depuis ce worktree, en réutilisant l'environnement installé
sans modifier ses dépendances :

```bash
PYTHONPATH=src make test \
  VENV="$HOME/Project/bascanada/harmonium_lab/.venv"
```

Résultat de cette commande : **287 tests réussis, 31 ignorés, 9 avertissements**,
aucun échec. La régression de dérive d'octave est incluse dans ces 287 tests.
Les avertissements librosa/Numba n'ont pas été masqués.

Les trois commandes `audioref-measures` documentées ont aussi été rejouées :
**égalité JSON complète** avec chaque `measures.json` versionné (20 zones par
dossier). Les propositions TOML ont été relues et contrôlées : durées de toutes
les alternatives à 8 mesures, poids positifs, motifs sans chevauchement dans
leur grille, densités 0/1/2 couvertes et fichiers Odin nommés effectivement présents.
Ce contrôle de données ne prétend pas charger des profils complets dans le moteur.
