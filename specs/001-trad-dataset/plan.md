# Dataset trad québécois — écouter, comparer, s'inspirer

**Statut** : en cours | **Date** : 2026-10-19 | **Repo** : `harmonium_lab` (Python) | **Consommateur** : moteur `harmonium` (`harmonium_core::trad`)

## Pourquoi

Le moteur génère des reels (phase 1 du moteur). Le propriétaire n'est pas
expert : il ne peut pas dire *pourquoi* un air sonne « pas trad ». Le dataset
remplace l'expertise par trois outils :

1. **Écouter à armes égales** — chaque air réel est rendu avec la même
   SoundFont (GeneralUser GS), le même violon, la même basse/guitare et des
   pieds comparables au moteur ; un kit en aveugle mélange réels et générés.
   La question devient « est-ce que j'entends la différence ? ».
2. **Comparer** — les mêmes statistiques trad sont calculées sur le corpus
   et sur la sortie du moteur ; le rapport dit en clair où ça diverge.
3. **S'inspirer** — le vocabulaire du moteur (cellules d'une mesure,
   enchaînements d'accords, tempos) est extrait du corpus au lieu d'être
   inventé.

La direction musicale du jeu (`1867_lore`, `design/jeu.md` §10 bis,
`design/biomes/*.md`) fixe les styles : reel (salles, boss du Diable),
gigue (pas de gigue du gameplay), valse (veillées), quadrille / cotillon /
marche (bal de Québec).

## Décisions

### D1 — Droits : usage interne

Les sources sont téléchargées par script et **jamais redistribuées** : seuls
les manifestes (titre, source, URL, licence, empreinte) et les statistiques
dérivées sont versionnés. Le jeu n'embarque jamais un air du corpus tel quel ;
le moteur ne reçoit que des tables agrégées (cellules en degrés, fréquences).

### D2 — Sources v1

| Source | Contenu | Licence |
|---|---|---|
| John Chambers, `trillian.mit.edu/~jc/music/abc/Quebec/{reel,jig,waltz,march,...}` | ~387 reels, ~71 gigues, ~31 valses, ~6 marches en ABC, avec accords (`"G"`), `R:`, `O:`, `Z:` | non précisée — usage interne, attribution |
| The Session, `github.com/adactio/TheSession-data` | ABC typés (reel, jig, waltz, march, …) ; filtrage québécois par enregistrements d'artistes québécois et titres français | ODbL |

Quadrille / cotillon : peu de transcriptions dédiées ; v1 = airs marqués
comme tels dans les sources (titre, `R:`, notes) + marches. Lacune documentée,
pas inventée.

### D3 — Disposition

```text
corpus/trad/                      gitignoré, recréé par `make trad-corpus`
  raw/<source>/...                fichiers tels que téléchargés
  tunes/<type>/<id>.abc           un air par fichier, normalisé
corpus/trad/manifest.jsonl        VERSIONNÉ : une ligne par air
corpus/trad/VERSION               VERSIONNÉ : version du corpus (constitution II)
target/trad_render/<type>/<id>.{mid,musicxml,wav}   gitignoré
references/trad-<type>/profile.json                  versionné (statistiques)
```

Ligne de manifeste :
`{id, title, aliases, type, meter, key, mode, bars, source, url, license, sha256, included_because, incipit}`
où `type ∈ {reel, jig, waltz, march, quadrille, cotillon}`, `id` stable
(slug titre + empreinte courte), `incipit` = 2 premières mesures en hauteurs
(sert au dédoublonnage entre sources).

### D4 — Rendu à armes égales

ABC → MIDI par `abc2midi` (`brew install abcmidi`) avec reprises jouées
(AABB), programmes GM identiques au moteur (violon 40, guitare acier 24 pour
les accords de l'ABC, basse acoustique 32), un motif de pieds `%%MIDI drum`
équivalent à la table D9 du moteur (talon 36 / pointe 37), tempo par type
(reel 230 à la noire, gigue 115 à la noire pointée, valse 150, marche 110),
swing nul (le violon de l'ABC est noté droit). MIDI → WAV par `fluidsynth`
avec `GeneralUser-GS.sf2` (la même banque que le moteur, `make soundfont`
côté moteur). MusicXML par `music21` pour le crate Rust si besoin.

### D5 — Statistiques trad (mêmes fonctions pour corpus et moteur)

Sur la mélodie (canal 0 du moteur ; voix principale de l'ABC) :
- forme : segmentation en parties de 8 mesures, détection AABB, taux de
  mesures identiques (1-2 vs 5-6, reprises) ;
- cadences : degré de la dernière note forte des mesures 4 et 8 ;
- registre : ambitus et hauteur moyenne par partie (A vs B) ;
- intervalles : histogramme (unisson, seconde, tierce, quarte, quinte, >
  quinte), taux de mouvement conjoint ;
- rythme : histogramme des durées et des positions d'attaque dans la mesure ;
- tonalité et mode ; vocabulaire de cellules (une mesure en degrés, notation
  du moteur : `1 3 5 3 1 3 5 3`, `5,`, `-`).
Sur l'harmonie (accords de l'ABC ; pistes Chords/Bass du moteur) :
vocabulaire en degrés, enchaînements, rythme harmonique.

Profil par type = distribution (moyenne, écart-type, quantiles,
histogrammes) sur tout le corpus de ce type.

### D6 — Comparaison et écoute

- `harmonium-lab trad-compare --generated <dir de .mid> --type reel` :
  rapport JSON + Markdown en français, écarts triés par z-score, avec une
  phrase par écart (« les reels réels font 31 % de sauts ≥ quarte, le moteur
  12 % »), et les 3 airs réels les plus proches de chaque généré.
- `harmonium-lab blindtest --type reel --real 10 --generated 10` : WAV
  renommés au hasard dans `target/blindtest/<horodatage>/`, feuille de
  réponse vide, corrigé séparé, script de score.

### D7 — Inspiration vers le moteur

`harmonium-lab mine-cells --type reel -o reel_cells.toml` : cellules d'une
mesure extraites du corpus, en degrés relatifs à la tonique, au format exact
de `harmonium_core/src/trad/reel_cells.toml`, rôle déduit de la position
(mesure 1 `open`, 4 `cad_half`, 8 `cad_full`, autres `run`/`arp`/`turn` par
les intervalles), poids = fréquence. Plus : table d'enchaînements d'accords
et plages de tempo par type. Le moteur les adopte par PR, après écoute.

## Découpage

| Tâche | Contenu | Dépend de |
|---|---|---|
| DS-T1 | Téléchargement + normalisation + manifeste + dédoublonnage (D1-D3), `make trad-corpus` | — |
| DS-T2 | Rendu MIDI/WAV/MusicXML à armes égales (D4), `make trad-render` | T1 |
| DS-T3 | Extracteur de statistiques trad + profils par type (D5) ; mise à jour de `types.py` aux 5 pistes du moteur | T1 (format) — démarre sur fixtures |
| DS-T4 | `trad-compare` + `blindtest` (D6) | T2, T3 |
| DS-T5 | `mine-cells` + tables d'harmonie/tempo (D7) | T3 |

## Acceptation

1. `make trad-corpus` sur machine vierge : manifeste reproduit à
   l'identique (mêmes `sha256`), comptes par type affichés.
2. Un reel, une gigue, une valse rendus : WAV audibles avec violon, accords,
   basse et pieds ; AABB joué.
3. Profils `trad-reel`, `trad-jig`, `trad-waltz` construits ; sur le corpus
   reel, ≥ 80 % des airs détectés AABB à 8 mesures (sinon on documente
   pourquoi : airs « croches », parties de 16).
4. `trad-compare` sur les démos du moteur (`harmonium/demos/*.mid`) produit
   un rapport lisible par un non-musicien.
5. `blindtest` produit un kit jouable de 20 fichiers.
6. `mine-cells` produit un TOML que le parseur du moteur accepte
   (`CellBank` : vérifié en le chargeant via un test Rust ou une commande).

## DS-T9 — Phrases, motifs, répétitions et rythmes

Mesure descriptive, sans modification du moteur :

```bash
make setup
make engine-tunes STYLE=gigue_quebecoise N=20 ENGINE_DIR=/chemin/vers/harmonium
.venv/bin/harmonium-lab trad-structure \
  --corpus corpus/trad --type jig \
  --generated target/engine_tunes/gigue_quebecoise
```

La commande écrit `target/structure/quebecoise-jig/{report.md,stats.json}`,
la référence statistique `references/structure/quebecoise-jig.json`, puis
actualise `target/structure/synthese.md` à partir des comparaisons disponibles.
Sans `--generated`, elle ne mesure que le réel. `--output` et `--references`
permettent de changer les deux racines de sortie. Types acceptés : `reel`,
`jig`, `waltz`, `march`, `hornpipe`. Aucun ABC, MIDI ou incipit n'est copié
dans les références.

Pour reproduire les cinq comparaisons, exporter 20 seeds (1..20) de chacun de
`reel_quebecois`, `gigue_quebecoise`, `valse_quebecoise`, `reel_acadien` et
`marche_britannique_coloniale`. Relancer ensuite la commande pour chaque couple :

| Profil | Corpus | Type |
|---|---|---|
| reel_quebecois | corpus/trad | reel |
| gigue_quebecoise | corpus/trad | jig |
| valse_quebecoise | corpus/trad | waltz |
| reel_acadien | corpus/acadienne | reel |
| marche_britannique_coloniale | corpus/britannique_coloniale | march |

Mesurer également sans `--generated` chaque autre groupe ayant au moins
15 ABC. Lot mesuré : 12 groupes, 2 003 airs analysables sur 2 019 fichiers
(16 sans mesure pleine). Québec : reel, jig, waltz, march ; Acadie : reel,
jig, hornpipe ; britannique colonial : les cinq types. Les 5 valses et
11 marches acadiennes, et les hornpipes québécois absents, restent hors lot.

### Définitions, dénominateurs et prudence

- Lecture par `trad.form.analyze_form`, comme les analyses de forme et
  l'extraction de cellules existantes ; pas de second parseur ABC.
- Première passe de chaque partie ABC (première fin) ; parties de 8 mesures
  uniquement pour les positions. Les formes croches restent dans les rythmes
  avec leurs mesures pleines jouées : ce dénominateur diffère du positionnel.
- Matrices 8×8 de hauteurs en degrés (altérations et octaves conservées),
  de rythme et conjointes ; structures de quatre paires de mesures, dont
  `a a' b c`. Fréquences par partie et présence par air (non exclusive).
- Répétition exacte, séquence diatonique constante, fin variée après un
  début identique, inversion stricte et variation rythmique. Catégories non
  exclusives ; toutes les positions de mesures et de paires sont comparées,
  ainsi que B/A et le début de B avec la fin de A. Les déplacements de
  séquence sont distribués dans `sequence_shifts`.
- « Question-réponse » est un indice strict 4+4 : début repris, finale de m.4
  non tonique, finale de m.8 tonique longue. Ce n'est pas une classification
  musicologique certaine. Une levée rattachée à la fin peut changer la dernière
  note littérale ; ne pas transformer ce taux seul en objectif de qualité.
- Rythmes en fractions de croche, silences distingués des tenues ; top 20,
  vocabulaire complet, entropie, syncopes métriques, répétitions de notes
  (triolets compris), attaques des notes longues et marques d'accent ABC.
  L'absence de marque d'accent ne signifie pas absence d'accent joué.
- Les exports contiennent une intro (1 ou 2 mesures), pas seulement AABB.
  Le début du corps est repéré par identité des reprises A/A et B/B parmi
  les décalages 0..4, sans supposer les copies internes que l'on mesure.
  Le meilleur candidat doit obtenir au moins 14 identités sur 16 ; les
  égalités sont signalées et le premier candidat est retenu. Les 100 exports
  mesurés obtiennent 16/16, avec 7 alignements ambigus à interpréter prudemment.
- Les attaques MIDI sont quantifiées **en temps absolu avant** le découpage
  des mesures. Cela évite qu'une petite dérive d'horloge place une attaque
  de début de mesure à la fin de la précédente. Les banques distribuées
  sont en croches : swing et gate ne sont pas des variations écrites.
  Les durées sont reconstruites jusqu'à l'attaque suivante ou à la barre ;
  les silences internes éventuels du moteur sont donc assimilés à des tenues.
- `make engine-tunes` garde désormais un journal `.log` pour chaque seed,
  en plus des WAV/MIDI/vérités. La vérité est prioritaire pour tonalité/mode ;
  ses champs vides sont suppléés par la tonalité annoncée dans **ce même**
  journal, sinon par une estimation explicitement comptée.

La synthèse retient cinq écarts absolus de taux avec au moins un par domaine
(répétition, phrases, rythme), puis les plus grands restants ; les vues
redondantes de la copie m.1-2 → m.5-6 ne sont pas proposées trois fois.
Chaque proposition est une règle en données avec une probabilité cible.
Pas de significativité revendiquée : mesures corrélées et 20 seeds moteur
seulement ; l'entropie dépend de la taille du lot. Mesurer, puis écouter,
puis décider.

**Observation de contrôle** : le résultat antérieur « 52 % contre 0 % » des
gigues portait sur les mesures d'export non réalignées. Après exclusion des
intros, m.5-6 = m.1-2 vaut 52,8 % des parties réelles contre 100 % du moteur ;
ce changement de fenêtre explique l'écart, sans modification du générateur.

Tests : fixtures ABC courtes pour chaque transformation, `a a' b c`,
4+4, lien A/B, triolets, silences, levées et voltas ; MIDI synthétiques pour
gate/swing/dérive d'horloge et intros sonores. Vérification globale : `make test`.

## DS-T10 — ornements

Mesure descriptive en données, sans modification du moteur (phase 012,
point 3 ; constitution V et VII). Reproduction :

```bash
make trad-ornaments
# Cache situé ailleurs, sans réseau ni modification des ABC :
make trad-ornaments CORPUS_ROOT=/chemin/vers/harmonium_lab/corpus
```

`trad.ornaments.extract_ornaments` utilise `trad.form.analyze_form` :
le tokenizer commun conserve désormais les marques et la provenance des
segments écrits dans les mesures développées. Pas de second parseur ABC.
La sélection de première voix traite également les changements `[V:…]`.
Sorties : **18 combinaisons présentes**, 2 059 airs, 233 593 attaques,
dans `references/ornaments/<tradition>-<type>.json` ; rapport complet
`target/ornaments/report.md`, événements dérivés `target/ornaments/events.jsonl`.
Les petits groupes cotillon/quadrille et les valses/marches acadiennes sont
inclus, contrairement au seuil de 15 airs du lot DS-T9.

### Comptage et positions

- Une occurrence **écrite**, pas deux lors des reprises ; les deux voltas
  restent présentes. Une double corde compte comme une attaque porteuse,
  hauteur supérieure pour le contexte ; trois notes de triolet comptent
  comme trois attaques, une seule occurrence de groupe. Les agréments
  eux-mêmes ne gonflent pas le nombre de notes.
- Mesures équivalentes = durée écrite / durée nominale, levées et fragments
  inclus. Pour m.1..8, seulement les parties reconnues de huit mesures ;
  les autres événements gardent `bar=null`, pas de modulo huit inventé.
  Une levée complète sa fin complémentaire quand le plan le permet,
  sinon reste une levée sans position. Les secondes fins ont la même
  position que les premières, avec leurs propres opportunités.
- Temps métrique 1-based et phase exacte : blanche en 2/2, noire en 4/4
  et 3/4, noire pointée en 6/8 ; demi-temps et fractions des triolets
  conservés. Durées en croches rationnelles ; intervalles signés en
  demi-tons, degré 1..7 et altération ; fin de phrase = m.4/m.8.
- Chaque cellule JSON donne occurrences, notes et mesures du dénominateur.
  Par mesure **conditionnelle** pour position/partie/fin de phrase ; par
  mesure totale du groupe pour temps/durée/degré/intervalles.
  Dans `by_position`, type absent = zéro ; position absente = non mesurée.
  `by_source` reprend ces distributions ; `by_source_transcriber` ne garde
  que les totaux par type (effectifs trop petits pour des tables par position),
  sans confondre attribution de collection et identité d'un interprète.

Contrôle des fichiers contenant une marque, brut / première voix extraite :

| Tradition | Airs | Agréments | Rouleaux | Triolets | Accords ABC complets |
|---|---:|---:|---:|---:|---:|
| québécoise | 764 | 69/69 | 116/113 | 204/204 | 62/61 |
| acadienne | 270 | 29/29 | 52/52 | 61/61 | 12/12 |
| britannique coloniale | 1 025 | 11/11 | 3/3 | 136/136 | 25/24 |

Les trois faux rouleaux québécois sont `(~1981)` dans deux champs `C:` et
`/~jh/` dans une URL `F:`. Le brut initial des accords (29/2/17) ne se
reproduit pas en acceptant durées, octaves et altérations internes :
`[G,2D2]`, `[d2f2]`, `[^db]` sont de vraies doubles cordes.
La regex lexicale complète du contrôle est publiée dans `ornaments.RAW`.
Deux autres exclusions exactes : `{[Aa]}` est un agrément, pas un accord
de la ligne porteuse (`miss-laura-andrew-d184d803`) ; `[D,A]` est dans le
titre de `hundred-pipers-bagpipe-version-d-a-bffcb0f6`. Les accords
d'accompagnement entre guillemets et les voix secondaires ne sont jamais
des doubles cordes mélodiques.

### Sept profils distribués : effectifs et taux

Taux pour **100 notes**, occurrences entre parenthèses ; zéro observé ne
prouve pas une interdiction musicale. GS/GM = agrément simple/multiple ;
TR = triolet répété ; DC = double corde ; AC = accord ≥ trois notes.
Les triolets mélodiques et les articulations `.`/`H` sont mesurés
séparément dans le rapport, mais pas proposés comme ornements à générer.

| Profil | Airs / notes | GS | GM | Rouleau | Turn | TR | DC | AC | Trille |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reel_quebecois | 574 / 72627 | 0.185 (134) | 0.047 (34) | 0.690 (501) | 0.004 (3) | 0.182 (132) | 0.344 (250) | 0.000 (0) | 0.010 (7) |
| gigue_quebecoise | 88 / 9194 | 0.207 (19) | 0.033 (3) | 0.207 (19) | 0.000 (0) | 0.000 (0) | 0.076 (7) | 0.000 (0) | 0.000 (0) |
| valse_quebecoise | 67 / 8183 | 0.073 (6) | 0.012 (1) | 0.061 (5) | 0.000 (0) | 0.061 (5) | 1.283 (105) | 0.086 (7) | 0.000 (0) |
| reel_acadien | 169 / 21640 | 0.273 (59) | 0.102 (22) | 0.878 (190) | 0.000 (0) | 0.573 (124) | 0.125 (27) | 0.000 (0) | 0.028 (6) |
| marche_britannique_coloniale | 25 / 2026 | 0.000 (0) | 0.000 (0) | 0.247 (5) | 0.000 (0) | 0.000 (0) | 0.099 (2) | 0.000 (0) | 0.000 (0) |
| gigue_britannique_coloniale | 365 / 37036 | 0.049 (18) | 0.011 (4) | 0.019 (7) | 0.000 (0) | 0.003 (1) | 0.059 (22) | 0.062 (23) | 0.005 (2) |
| hornpipe_britannique_coloniale | 78 / 9162 | 0.000 (0) | 0.000 (0) | 0.000 (0) | 0.000 (0) | 0.327 (30) | 0.022 (2) | 0.000 (0) | 0.000 (0) |

Taux des huit types proposés réunis par position, toujours /100 notes
et avec occurrences. Le détail **type × position** est dans le rapport
et les JSON. Ces sous-populations ne se substituent pas au taux global :
43 960 notes positionnées sur 72 627 pour le reel québécois, seulement
3 530 sur 8 183 pour la valse québécoise.

| Profil | m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| reel_quebecois | 1.583 (82) | 1.016 (54) | 1.538 (83) | 0.859 (46) | 1.686 (89) | 1.243 (67) | 1.068 (62) | 1.090 (68) |
| gigue_quebecoise | 0.587 (5) | 0.350 (3) | 0.659 (6) | 0.116 (1) | 0.458 (4) | 0.229 (2) | 0.294 (3) | 0.545 (5) |
| valse_quebecoise | 0.000 (0) | 0.000 (0) | 0.622 (3) | 0.000 (0) | 0.000 (0) | 0.000 (0) | 0.426 (2) | 0.259 (1) |
| reel_acadien | 1.826 (28) | 1.677 (27) | 2.434 (39) | 1.303 (21) | 2.070 (33) | 1.525 (25) | 1.397 (24) | 0.996 (17) |
| marche_britannique_coloniale | 1.299 (2) | 0.000 (0) | 0.568 (1) | 1.408 (2) | 1.176 (2) | 0.000 (0) | 0.000 (0) | 0.000 (0) |
| gigue_britannique_coloniale | 0.239 (9) | 0.385 (14) | 0.128 (5) | 0.444 (15) | 0.131 (5) | 0.189 (7) | 0.219 (9) | 0.316 (9) |
| hornpipe_britannique_coloniale | 0.983 (9) | 0.548 (5) | 0.423 (4) | 0.000 (0) | 0.746 (7) | 0.535 (5) | 0.000 (0) | 0.000 (0) |

### Proposition `[ornaments]`, pas encore décision d'écoute

Une section générique, sans nom de style dans le code, contenant la
référence, l'unité de taux, les multiplicateurs d'arousal et une sous-table
par type. Exemple **mesuré**, reel québécois / agrément simple :

```toml
[ornaments]
reference = "references/ornaments/quebecoise-reel.json"
rate_unit = "per_100_carrier_notes"
arousal_low_multiplier = 1.0
arousal_high_multiplier = 1.0

[ornaments.types.grace_single]
enabled = true
written_per_100_notes = 0.184504
occurrences = 134 # preuve statistique, pas réglage
per_100_notes_by_bar = { "1" = 0.096525, "2" = 0.131703, "3" = 0.018532, "4" = 0.168036, "5" = 0.113636, "6" = 0.148451, "7" = 0.155092, "8" = 0.192277 }
min_carrier_eighths = 0.5
```

Les huit sous-tables et leurs valeurs pour les sept profils sont dans
`engine_proposal.types` de chaque JSON. Durées porteuses **minimales
observées**, en croches ; `—` = aucun événement, désactiver faute de données :

| Profil | GS | GM | Rouleau | Turn | TR | DC | AC | Trille |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| reel_quebecois | 1/2 | 1 | 1/2 | 1 | 1/3 | 1 | — | 1 |
| gigue_quebecoise | 1 | 1 | 3 | — | — | 1 | — | — |
| valse_quebecoise | 1 | 1 | 3 | — | 2/3 | 1 | 2 | — |
| reel_acadien | 1 | 1 | 1/3 | — | 1/3 | 1 | — | 2 |
| marche_britannique_coloniale | — | — | 2 | — | — | 2 | — | — |
| gigue_britannique_coloniale | 1 | 2 | 3 | — | 1/3 | 1 | 1 | 2 |
| hornpipe_britannique_coloniale | — | — | — | — | 2/3 | 2 | — | — |

Ces minima ne sont **pas des seuils musicaux validés**. Pour les triolets,
ils concernent la première note après subdivision, pas la durée totale
à remplacer. Les marques peuvent coexister sur une porteuse : ne pas
normaliser aveuglément les taux comme catégories exclusives. Aucun
arousal n'est annoté dans les ABC : lien possible par multiplicateur,
mais pente neutre 1→1 proposée avant écoute, pas de corrélation inventée.

### Limites et vérification

Les transcriptions **sous-notent** les ornements : taux écrit = plancher.
Effectifs faibles, notes d'un air corrélées : fournir les occurrences,
pas un IC binomial prétendument indépendant. « Aucun ornement » signifie
aucune des marques mesurées, pas absence d'ornement dans le jeu réel.
Parts sans marque : 50,2 % reel québécois, 84,1 % gigue québécoise,
67,2 % valse québécoise, 51,5 % reel acadien, 80,0 % marche britannique,
91,0 % gigue britannique, 35,9 % hornpipe britannique.

Effet de source manifeste : dans le reel québécois, Chambers note
166 rouleaux / 42 632 notes, The Session 335 / 29 995 ; les 22 agréments
de la gigue britannique proviennent uniquement des 12 airs Cahusac.
Ne pas interpréter ces écarts comme effet causal de tradition. `Z:`
identifie un transcripteur quand fourni, sinon « non renseigné ».
Les changements de métrique, unité ou tonalité en cours d'air restent
une limite du parseur commun ; les changements `[M:…]`/`[K:…]` sont
comptés dans `inline_changes` pour rendre cette incertitude visible.

**Effet de bord sur le parseur commun (relevé par le coordinateur).** L'ancien
nettoyage `\+[^+]+\+` de `form.py` prenait pour une décoration `+…+` le texte
compris entre deux accords chiffrés finissant par `+` (ex. `"D/f+"` … `"A7/c+"`)
et **supprimait la musique entre les deux**. La lecture par jetons de DS-T10
corrige ce défaut : `analyze_form` donne d'autres mesures pour **47 airs sur
2 059**, tous britanniques coloniaux (reel 16, jig 20, waltz 9, hornpipe 2),
le plus souvent plus de mesures et de notes (ex. *Beaux of Oakhill* : 15 → 24
mesures). Les références déjà publiées qui reposent sur ce parseur
(`references/structure/britannique_coloniale-*.json` de DS-T9, profils
`references/trad-britannique_coloniale-*`) datent d'avant la correction et
sont à régénérer ; ce n'est pas fait ici.

Vérification : commande réelle sur les trois caches locaux, sans réseau ;
2 059/2 059 SHA256 ABC égaux aux manifestes versionnés, manifestes du
cache identiques à ceux du worktree. Conservation des dénominateurs et
occurrences entre groupes, positions et sources contrôlée.
`PYTHONPATH=src make test` : **241 réussis, 31 ignorés** (assets/outils
optionnels absents), dont 21 cas dédiés aux types, contexte, levées,
reprises, voltas, changements de voix, triolets avec silence et agrégation.
Le `PYTHONPATH` sélectionne ce worktree quand le venv est partagé.

