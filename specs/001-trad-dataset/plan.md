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

## SK4 — attaques courtes

Mesures instrumentales uniquement, **aucune écoute humaine revendiquée**.
Objectif : une croche de reel à 230/noire dure 130,435 ms ; les quatre
banques SK3 atteignaient leur attaque90 G3 entre 247 et 356 ms. La
constitution du moteur impose **SoundFont uniquement** : aucun modèle
physique implémenté, ni nécessaire pour atteindre les attaques mesurées.
Pas de modification ni de banque installée dans le repo moteur.

### Sources et droits

- **VSCO 2 Community Edition**, dépôt officiel Versilian Studios / Sam
  Gossner, révision `440300901dfe9275fd84e0b7763af1f8443ae62e` :
  [CC0-1.0](https://raw.githubusercontent.com/sgossner/VSCO-2-CE/440300901dfe9275fd84e0b7763af1f8443ae62e/LICENSE),
  « for any purposes, including without limitation commercial purposes ».
  Le [README source](https://raw.githubusercontent.com/sgossner/VSCO-2-CE/440300901dfe9275fd84e0b7763af1f8443ae62e/Readme.txt)
  autorise explicitement les banques personnelles commerciales et demande
  un crédit. WAV directs, piano/forte arco et deux niveaux spiccato ;
  pas besoin d'un convertisseur SFZ externe. Sélection avec URL et SHA256
  de chaque WAV dans `samples/fiddles/vsco_sources.json`.
- **FluidR3**, déjà accepté SK3, [MIT et notices de
  provenance](https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General_License.md) :
  dérivation autorisée, conserver les notices Frank Wen et autres notices
  applicables de la source. Variante économique : copie locale, instruments
  du preset 0/40 à attaque 2 ms et début avancé de 120 ms au maximum,
  jamais au-delà du début de boucle ; échantillons/boucles conservés.
- **University of Iowa MIS** : [source officielle](https://theremin.music.uiowa.edu/MIS.html),
  « may be downloaded and used for any projects, without restrictions ».
  Commercial autorisé ; non retenu ici car la [page violon
  2012](https://theremin.music.uiowa.edu/MISviolin2012.html) identifie arco et
  pizzicato, mais pas de détaché/spiccato/staccato à archet. Les couches
  dynamiques sont disponibles ; VSCO fournit déjà celles-ci et le spiccato.
  Rejet de sélection, pas rejet juridique.
- **Philharmonia** : [licence à la
  source](https://philharmonia.co.uk/resources/sound-samples/) permettant la
  musique commerciale, mais interdisant la mise à disposition « as samples
  or as a sampler instrument ». URL ZIP directe disponible ; rejet pour une
  SF2 embarquée dans un jeu, pas pour un rendu musical interne.
- Pistes SF2 « fiddle » : le preset Fiddle existe dans FluidR3/MuseScore,
  mais son nom ne prouve pas une articulation courte. Les pistes LDK1609,
  All-Around Violin, SGM et Arachno restent rejetées pour les raisons SK3
  conservées dans le manifeste (accès direct bloqué, origine ou droits).

Le manifeste `samples/fiddles/manifest.jsonl` contient les sept candidats
acceptés (quatre SK3 + trois dérivés SK4) et tous les rejets motivés. Seuls
code, manifestes et mesures agrégées ci-dessous sont versionnés : **aucun
WAV, ABC, MIDI ou SF2 redistribué**.

### Construction reproductible

```bash
make setup
make fiddle-sf2
make fiddle-compare
# Même construction et mêmes rendus, cache complet requis :
make fiddle-sf2 OFFLINE=1
make fiddle-compare OFFLINE=1
```

`src/harmonium_lab/trad/fiddle_sf2.py` réutilise les primitives RIFF du
constructeur des pieds. Banques dans `samples/fiddles/raw/`, gitignorées ;
rapport des zones, rognages, boucles et empreintes dans `raw/build.json`.
Chaque source est vérifiée par SHA256 avant lecture. Un changement voulu
du constructeur exige un réinventaire explicite :
`.venv/bin/python -m harmonium_lab.trad.fiddle_sf2 --inventory --offline`.

Les deux banques VSCO couvrent G3–E6 par huit racines, zones au plus proche
sans trou, couches 0–80 piano / 81–127 forte. Silence et montée lente coupés
(premier seuil 90 % du maximum RMS des 400 ms initiales), fondu initial
2 ms, enveloppe SF2 2 ms, release 35 ms. Variante **arco raccourci** :
échantillons arco p/f traités, pas un détaché réellement enregistré.
Variante **hybride** : couche douce arco, couche forte avec transient
spiccato enregistré et raccord de 50 ms vers la tenue arco à 120 ms ;
racine C6 soutenue par E6 transposé de −4 demi-tons. Boucle 0,5–1,8 s,
fondu des 50 dernières ms vers les 50 ms précédant le début de boucle :
continuité de forme d'onde, sans répétition d'une queue percussive silencieuse.

### Mesures

Méthode SK3 strictement conservée : tenues G3/D4/A4/E5 de 3 s, attaque90
relative au maximum des 400 premières ms avec le même lissage, vibrato du
fondamental filtré 4–9 Hz en cents RMS, énergie >8 kHz ; discontinuités
sur 0,25–2,8 s, saut >0,02 FS et >8 fois la pente RMS locale sur 10 ms.
Les quatre résultats de référence complets sont identiques à SK3.

| Violon | Licence | Taille SF2 (octets) | Attaque90 G3/A4 (ms) | Vibrato G3/A4 (cents RMS) | >8 kHz G3 (%) | Clics suspects /4 tenues |
|---|---|---:|---:|---:|---:|---:|
| GeneralUser GS 2.0.3 | GeneralUser GS v2 | 32319396 | 318,7 / 264,6 | 31,85 / 28,24 | 0,0062 | 0 |
| FluidR3 GM2-2 | MIT | 148345256 | 247,9 / 330,5 | 38,80 / 15,60 | 0,0012 | 0 |
| MuseScore General 0.2 | MIT | 215614036 | 247,2 / 330,5 | 37,39 / 18,47 | 0,0016 | 0 |
| Sonatina Solo | CC Sampling Plus 1.0 | 494723490 | 355,8 / 351,5 | 20,09 / 25,43 | 0,0020 | 0 |
| FluidR3 raccourci | MIT | 148345484 | 126,9 / 216,9 | 13,82 / 29,49 | 0,0018 | 0 |
| VSCO arco raccourci | CC0-1.0 | 2966686 | **9,1 / 8,5** | 11,84 / 15,09 | 0,0087 | 0 |
| VSCO hybride spiccato/arco | CC0-1.0 | 2966682 | **22,0 / 48,8** | 18,50 / 30,04 | 0,0112 | 0 |

Complément : huit croches répétées par hauteur, vélocité 96, 230/noire,
gate 90 %. Niveau à 65 ms = RMS stéréo de 55–65 ms, rapporté au pic RMS
glissant 10 ms des 400 ms initiales de la tenue 96 ; moyenne sur huit
attaques, queues précédentes incluses. Réponse vélocité 110−60 : niveau RMS
et centroïde de puissance sur les premières 130 ms, sans renormalisation.

| Violon | Niveau65 G3/A4 (% tenue) | Δ110−60 niveau G3/A4 (dB) | Δ110−60 brillance G3/A4 (Hz) |
|---|---:|---:|---:|
| GeneralUser | 51,11 / 47,15 | 11,28 / 10,54 | −149,7 / −15,7 |
| FluidR3 | 33,54 / 40,22 | 10,46 / 10,42 | −0,6 / −4,2 |
| MuseScore | 35,63 / 42,03 | 8,79 / 8,74 | 7,9 / −4,0 |
| Sonatina | 22,74 / 26,22 | 10,44 / 10,46 | 9,2 / −2,1 |
| FluidR3 raccourci | 74,57 / 69,09 | 10,45 / 10,46 | −2,6 / 0,4 |
| VSCO arco raccourci | 96,92 / 53,95 | 24,69 / 30,46 | 184,1 / 313,2 |
| VSCO hybride | 85,75 / 98,28 | 20,78 / 28,15 | 855,8 / 551,1 |

**Conclusion mesurée** : les deux VSCO satisfont <80 ms sur G3 et A4,
sans discontinuité détectée sur les quatre tenues. La copie FluidR3 est
moins coûteuse à fabriquer, mais insuffisante : attaque A4 216,9 ms malgré
le rognage ; raccourcir l'enveloppe ne supprime pas la montée enregistrée.
Les deux couches VSCO donnent beaucoup plus de dynamique/brillance ;
le saut de couche à 80/81 et les écarts de 21–30 dB entre 60 et 110 sont
des **risques d'équilibre à écouter**, pas une qualité déclarée.
L'hybride E5 atteint attaque90 à 252,6 ms : la tenue raccordée peut dépasser
le pic du transient ; le succès G3/A4 ne s'étend pas à toute la tessiture.

Vérification complémentaire réelle : G3–E6 chromatique, vélocités 60/110,
68 tenues par nouveau candidat, fenêtres 0,25–2,8 s égalisées à RMS 0,06
pour le détecteur ; **0 cas suspect sur 204 tenues**. Rapport local
`target/fiddle_compare/register_check.json`. Le détecteur est heuristique :
aucune garantie psychoacoustique d'absence de clic, ni validation à l'oreille.
Les changements de spectre au raccord, la répétition sans round-robin et
les différences FluidSynth/oxisynth restent à évaluer avant intégration.

### Kit et vérification

Kit rendu : `target/fiddle_compare/README.md` ; résultats complets
`analysis.json` (quatre notes, chaque croche, niveaux/brillance à 60/110
sur 0–130 ms et 0,25–0,9 s), contrôles MIDI/WAV dans `probes/`.
Correspondance isolée dans `correspondance.md`, ordre mélangé déterministe,
même numéro par violon sur les trois airs :

- `target/fiddle_compare/saint-anne-s-reel-1-349a3efd/{01..07}.wav`
- `target/fiddle_compare/reel-beatrice-82ea9328/{01..07}.wav`
- `target/fiddle_compare/joys-of-quebec-a6433cbc/{01..07}.wav`

Les mêmes trois reels que SK3 : 8 mesures solo (8,347823 s), puis
8 mesures avec guitare/basse GeneralUser, sans pieds. Vérification des
**21 WAV** : noms purement numériques, stéréo 44,1 kHz PCM24, RMS solo
0,060 à 1e−6 près, aucun écrêtage. Accompagnement commun non renormalisé.
Tests de téléchargement sur manifeste factice `file://`, reconstruction
hors ligne, corruption SHA256, raccord de boucle, recouvrement des zones,
rognage du silence et séparation des mesures de niveau/brillance.
Vérification finale : `make test` exécuté avec connexions réseau Python
bloquées par un garde temporaire, **225 réussis, 31 ignorés, 0 échec**
(un avertissement librosa sur une FFT trop grande pour un extrait).
Les deux cibles `make fiddle-sf2 OFFLINE=1` et
`make fiddle-compare OFFLINE=1` réussissent dans l'environnement propre du
worktree ; les trois empreintes dérivées sont reproduites à l'identique.
Le test de silence a révélé une énergie FFT négative d'arrondi avant
racine carrée : énergie bornée à zéro, régression conservée, sans changement
des banques ni des mesures.

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


## DS-T9b — références britanniques régénérées après la correction du parseur

Suite de la note « Effet de bord sur le parseur commun » de DS-T10. Tout est
mesuré avec le code actuel de `trad/form.py` sur les trois caches locaux
(2 059 ABC, sans réseau). Aucun ABC, MIDI ni incipit n'est copié ; le dépôt
moteur n'est pas modifié.

### Artefacts régénérés et vérifiés

Dépendent de `analyze_form`/`abcnorm` : `references/structure/*.json` (12),
`references/trad-*/profile.json` (14) et `references/ornaments/*.json` (18).
Les 44 fichiers versionnés hors références jazz/ambiance ont été régénérés vers
un dossier de travail et comparés aux fichiers du dépôt :

| Famille | Commande | Résultat |
|---|---|---|
| structure britannique reel, jig, waltz, hornpipe | `trad-structure --corpus corpus/britannique_coloniale --type T` | **régénérés** (4) |
| profils `trad-britannique_coloniale-{reel,jig,waltz,hornpipe}` | `trad-profile --type T --corpus corpus/britannique_coloniale` | **régénérés** (4) |
| structure march britannique, 3 acadiennes, 4 québécoises | idem | bloc `real` **identique octet pour octet** (8 fichiers) : non réécrits |
| profils march britannique, 3 acadiens, 6 québécois | `trad-profile` | **identiques** (10) |
| ornements, 18 fichiers | `trad-ornaments` | **identiques** : DS-T10 utilisait déjà le parseur corrigé |

Les cinq fichiers de structure qui portent aussi une comparaison moteur
(`deviations`, `generated`) ne sont pas réécrits : leur `real` n'a pas changé, et
`trad-structure` sans `--generated` effacerait cette comparaison. Les rapports
`target/structure/*/report.md` et `synthese.md` ne sont pas versionnés (`target/`
est gitignoré) ; la synthèse porte sur des exports moteur et seule la marche
britannique, inchangée, y figure.

Empreintes SHA-256 avant/après de chacun des 44 fichiers : `specs/001-trad-dataset/ds-t9b-empreintes.txt`.
Seuls les 8 fichiers listés comme régénérés diffèrent ; les 36 autres, y compris
toutes les références acadiennes, québécoises et la marche britannique, sont identiques.
Corpus : 2 059/2 059 SHA-256 ABC égaux aux manifestes versionnés ; manifestes
du cache identiques à ceux du dépôt ; aucune écriture dans le corpus.

Reproduction (venv partagé, code du worktree) :

```bash
export PYTHONPATH=$PWD/src; C=/chemin/vers/harmonium_lab/corpus
for t in reel jig waltz hornpipe; do
  .venv/bin/python -m harmonium_lab.cli trad-structure --corpus $C/britannique_coloniale --type $t
  .venv/bin/python -m harmonium_lab.cli trad-profile --type $t --corpus $C/britannique_coloniale \
    --output references/trad-britannique_coloniale-$t/profile.json
done
.venv/bin/python /chemin/vers/harmonium/specs/011-phase3-phrase/measure_endings.py \
  --lab-root <racine avec src/ et corpus/> --output endings.json   # lecture seule côté moteur
```

Pour les « anciennes » valeurs : références `HEAD` avant DS-T9b, et
`measure_endings.py` avec `src/` extrait de `59fa4a1^` (avant la correction). Cette
exécution retrouve exactement les effectifs publiés dans P3-T2 (ex. reel 564
parties appariées, 414/48/102 puis 437/41/86).

### Ancien → nouveau, par type britannique

Taux du **réel** en %, tels que le moteur les consomme (poids de phrase P3-T1,
repos de cadence, copie entre parties). Seules les tailles de lot changent
vraiment : reel 16 airs touchés, jig 20, waltz 9, hornpipe 2, march 0.

| Indicateur (réel, %) | reel | jig | hornpipe | waltz | march |
|---|---:|---:|---:|---:|---:|
| m.5–6 = m.1–2 | 34.7 → 35.0 | 37.3 → 37.4 | 47.2 → 46.9 | 6.0 → 5.6 | 20.5 → 20.5 |
| paires « a b a c » | 20.3 → 20.4 | 22.8 → 23.1 | 32.8 → 32.8 | 3.6 → 3.4 | 5.1 → 5.1 |
| paires « a b c d » | 40.4 → 40.0 | 37.6 → 38.3 | 27.2 → 28.1 | 66.1 → 66.7 | 48.7 → 48.7 |
| copie A:m.5 = m.1 | 63.6 → 64.2 | 74.3 → 74.0 | 84.7 → 85.0 | 20.4 → 20.0 | 52.9 → 52.9 |
| copie A:m.6 = m.2 | 48.9 → 49.6 | 52.7 → 53.4 | 74.6 → 75.0 | 12.2 → 14.0 | 29.4 → 29.4 |
| copie B:m.5 = m.1 | 48.3 → 48.2 | 49.7 → 48.7 | 44.1 → 42.6 | 12.2 → 11.8 | 33.3 → 33.3 |
| copie B:m.6 = m.2 | 37.7 → 37.4 | 33.2 → 32.9 | 28.8 → 27.9 | 6.1 → 5.9 | 16.7 → 16.7 |
| copie entre parties B:m.7 = A:m.7 | 33.1 → 33.4 | 34.5 → 35.0 | 42.1 → 43.1 | 4.3 → 6.1 | 47.1 → 47.1 |
| repos tonique A:m.4 | 5.3 → 5.3 | 1.7 → 1.9 | 0.0 → 0.0 | 12.2 → 12.0 | 5.9 → 5.9 |
| repos tonique A:m.8 | 16.0 → 15.8 | 13.3 → 12.9 | 6.8 → 6.7 | 4.1 → 2.0 | 41.2 → 41.2 |
| repos tonique B:m.4 | 5.1 → 5.0 | 1.4 → 1.7 | 5.1 → 4.9 | 10.2 → 9.8 | 11.1 → 11.1 |
| repos tonique B:m.8 | 18.3 → 18.1 | 18.2 → 17.8 | 8.5 → 8.2 | 8.2 → 11.8 | 50.0 → 50.0 |
| finale longue A:m.4 | 44.5 → 44.4 | 10.3 → 10.6 | 18.6 → 18.3 | 79.6 → 76.0 | 35.3 → 35.3 |
| finale longue A:m.8 | 55.2 → 54.6 | 19.7 → 19.3 | 33.9 → 33.3 | 79.6 → 80.0 | 64.7 → 64.7 |
| finale longue B:m.4 | 48.3 → 47.7 | 22.4 → 22.1 | 23.7 → 23.0 | 81.6 → 82.4 | 55.6 → 55.6 |
| finale longue B:m.8 | 55.0 → 54.5 | 24.5 → 23.8 | 23.7 → 23.0 | 77.6 → 78.4 | 66.7 → 66.7 |
| croches continues (mesures) | 16.0 → 16.1 | 34.5 → 34.3 | 31.1 → 31.3 | 3.2 → 3.1 | 8.1 → 8.1 |
| entropie rythmique (bits) | 5.32 → 5.31 | 3.12 → 3.12 | 4.63 → 4.62 | 3.15 → 3.13 | 5.19 → 5.19 |
| airs analysés (positionnables) | 491 (413) → 491 (416) | 355 (306) → 355 (316) | 78 (61) → 78 (63) | 60 (51) → 60 (52) | 25 (18) → 25 (18) |
| parties A/B/… (total) | 961 → 982 | 707 → 737 | 125 → 128 | 168 → 177 | 39 → 39 |

Secondes fins, note **écrite** de la dernière mesure (tonique/quinte/autre,
effectifs, `measure_endings.py` de P3-T2 relancé sans modification) :

| Passe (tonique/quinte/autre) | reel | jig | hornpipe | waltz | march |
|---|---:|---:|---:|---:|---:|
| toutes parties, 1re fin | 414/48/102 → 420/52/104 | 333/31/74 → 342/31/77 | 61/3/9 → 64/3/9 | 8/11/9 → 8/14/9 | 23/2/2 → 23/2/2 |
| toutes parties, fin finale | 437/41/86 → 443/45/88 | 346/33/59 → 356/33/61 | 62/4/7 → 65/4/7 | 15/7/6 → 16/7/8 | 23/2/2 → 23/2/2 |
| A 8 mes., 1re fin | 238/20/46 → 245/22/46 | 202/12/36 → 210/12/38 | 44/3/4 → 45/3/4 | 4/6/5 → 4/8/5 | 11/2/1 → 11/2/1 |
| A 8 mes., fin finale → `second_ending` A | 243/19/42 → 250/21/42 | 205/15/30 → 213/15/32 | 45/3/3 → 46/3/3 | 7/4/4 → 7/4/6 | 11/2/1 → 11/2/1 |
| B 8 mes., 1re fin | 119/18/27 → 121/19/27 | 94/13/26 → 96/13/27 | 11/0/1 → 12/0/1 | 1/3/2 → 1/4/2 | 9/0/1 → 9/0/1 |
| B 8 mes., fin finale → `second_ending` B | 127/16/21 → 129/17/21 | 100/12/21 → 103/12/21 | 11/0/1 → 12/0/1 | 4/1/1 → 5/1/1 | 9/0/1 → 9/0/1 |
| parties appariées (8 mesures) | 564 (492) → 576 (506) | 438 (413) → 450 (426) | 73 (67) → 76 (69) | 28 (24) → 31 (27) | 27 (24) → 27 (24) |

Rythmes de cadence m.4/m.8 (distribution des motifs de mesure pleine à durées
contrastées de `real.rhythm.cells`, base des `rhythm` des profils) :

| Type | motifs | mesures conservées | écart total (points) | plus grand écart d’un motif (points) |
|---|---:|---:|---:|---:|
| reel | 62 → 62 | 5108 → 5157 | 0.60 | 0.17 |
| jig | 15 → 15 | 4132 → 4165 | 0.16 | 0.10 |
| hornpipe | 30 → 30 | 487 → 482 | 0.84 | 0.44 |
| waltz | 15 → 15 | 1003 → 1022 | 1.01 | 0.69 |
| march | 24 → 24 | 201 → 201 | 0.00 | 0.00 |

**Écarts > 5 points** : aucun sur les taux par position, structures, repos, copies, croches ni
rythmes de cadence (plus grand écart : 3,6 points, finale longue A:m.4 de la valse ;
motif de cadence : 0,69 point). Seules les secondes fins de la **valse**
(28 → 31 parties appariées ; aucun profil moteur n'en dépend) dépassent 5 points,
avec de très petits effectifs :

| Type | Indicateur | ancien | nouveau | Δ points |
|---|---|---:|---:|---:|
| waltz | toutes parties, 1re fin quinte | 39.3 | 45.2 | +5.9 |
| waltz | 8 mesures, 1re fin quinte | 45.8 | 51.9 | +6.0 |
| waltz | 8 mesures, fin finale autre | 20.8 | 25.9 | +5.1 |
| waltz | A (8 mes.), fin finale (poids `second_ending`) tonique | 46.7 | 41.2 | -5.5 |
| waltz | A (8 mes.), fin finale (poids `second_ending`) autre | 26.7 | 35.3 | +8.6 |
| waltz | A (8 mes.), 1re fin quinte | 40.0 | 47.1 | +7.1 |
| waltz | B (8 mes.), 1re fin quinte | 50.0 | 57.1 | +7.1 |

Pour les trois profils moteur, le plus grand déplacement d'un poids de rôle est
1,55 point, d'un poids de seconde fin 0,6 point, d'un motif de cadence 0,44 point.
Reel et waltz britanniques n'ont pas de profil moteur distribué. Les références publiées
avant la correction étaient inexactes pour 47 airs, mais les valeurs agrégées bougent peu.

Autres sorties de ce même parseur, **non modifiées ici** car hors profils de phrase :
les banques `mine-cells` des profils moteur diffèrent aussi (jig 7 cellules
remplacées sur 180, hornpipe 5/180, reel 6/180, waltz 0/84) et les `profile.json`
britanniques ont d'autres statistiques (cellules, accords). Le coordinateur décide
s'il faut re-miner `cells.toml`.

### Valeurs proposées pour le moteur

`specs/001-trad-dataset/ds-t9b-profils-proposes.md` donne, **par champ**
(`roles`, `second_ending`, `rhythm` de chaque `[[form.parts]]`), l'extrait TOML exact à
substituer dans `gigue_britannique_coloniale` et `hornpipe_britannique_coloniale`.
`marche_britannique_coloniale` : **aucun changement** (références et secondes fins
identiques). La formule est celle de P3-T1/T2/T3 : rejouée sur les anciennes
références, elle reproduit à l'identique tous les champs actuels des trois profils.
Les blocs ont été substitués dans des copies temporaires et chargés par
`harmonium-cli --export --profile` (exports MIDI produits, validation passée) ;
Appliquer ces poids change les tirages du moteur : goldens et `TUNING_VERSION` probablement à régénérer par le coordinateur (non vérifié ici).

Vérification : `PYTHONPATH=src make test VENV=<venv partagé>` : **246 réussis, 31 ignorés**.

## DS-T10b — liaisons, ties et accents

Le parseur commun `trad.form.analyze_form` reconnaît les parenthèses de liaison
(groupes imbriqués et traversant les barres/reprises), sans confondre `(3` ou
`(3:2:3` avec un groupe de notes. Les ties `-` et les articulations écrites
`!accent!`, `!>!`, `!emphasis!`, `+accent+`, `L`, `!tenuto!`, `!marcato!`,
`!^!` et `.` sont annotés sans modifier les notes/mesures de `plan.bars`.
`extract_ornaments` garde les agréments dans `events` et livre les événements
`slur`, `tie`, `staccato`, `accent`, `tenuto`, `marcato` dans `articulations`.
Le staccato n'est donc pas doublé dans les agrégats d'ornements. Chaque liaison
expose `note_count`, `contour` (intervalles signés), `repeated_notes`, et les
champs de contexte de sa première note.

Le calcul utilise les corpus locaux hors ligne et conserve les contrôles des
manifestes : **2 059/2 059 SHA256 ABC conformes**. Empreinte SHA256 de la
sérialisation canonique `(id, plan.bars)` : **`18188ed67e4afc3c387e72437378a81591223a25e1e7e0dd741da8bb0c26081f`** avant et après.
La table rapporte les taux écrits par 100 notes, occurrences et longueur
moyenne des liaisons (notes). Ces marques sont un **plancher écrit, à valider
à l’oreille** ; l'absence dans une transcription n'est pas une preuve de jeu
détaché. Les références exposent aussi les mesures 1..8, temps, demi-temps,
durées, intervalles/contexte, fins de phrase, contour/longueur des liaisons,
et totaux par source/transcripteur (sans tables positionnelles par source).

| Profil | Notes | Liaison /100 (n) | Longueur moyenne | Répétées (n) | Tie /100 (n) | Staccato /100 (n) | Accent /100 (n) | Tenuto (n) | Marcato (n) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reel_quebecois | 72 627 | 0,249 (181) | 2,81 | 71 | 0,308 (224) | 0,089 (65) | 0,000 (0) | 0 | 0 |
| gigue_quebecoise | 9 194 | 0,261 (24) | 2,12 | 8 | 0,457 (42) | 0,000 (0) | 0,000 (0) | 0 | 0 |
| valse_quebecoise | 8 183 | 0,648 (53) | 2,92 | 28 | 1,271 (104) | 0,367 (30) | 0,000 (0) | 0 | 0 |
| reel_acadien | 21 640 | 0,462 (100) | 2,52 | 36 | 0,051 (11) | 0,102 (22) | 0,000 (0) | 0 | 0 |
| marche_britannique_coloniale | 2 026 | 1,185 (24) | 2,00 | 5 | 1,234 (25) | 0,000 (0) | 0,000 (0) | 0 | 0 |
| gigue_britannique_coloniale | 37 036 | 0,092 (34) | 2,00 | 8 | 0,186 (69) | 0,030 (11) | 0,000 (0) | 0 | 0 |
| hornpipe_britannique_coloniale | 9 162 | 0,000 (0) | — | 0 | 0,000 (0) | 0,000 (0) | 0,000 (0) | 0 | 0 |

`references/ornaments/*.json` versionne les agrégats (schéma 2) ;
`target/ornaments/report.md` résume les sept profils. Le bloc
`engine_proposal.performance` propose des taux de liaison par mesure et
contour, longueurs mesurées, et accents par temps ; il reste un plancher écrit
à valider à l'oreille, sans changement moteur.

Vérification DS-T10b : `PYTHONPATH=src make test` avec le venv partagé :
**257 réussis, 31 ignorés**, sans réseau. La génération offline a écrit les
références et `target/ornaments/report.md`; 2 059/2 059 empreintes du manifeste
concordent avec les fichiers ABC.

## DS-T9c — alignement AABB sur l'intro publiée (R1, phase 013)

`trad-structure --generated` cherchait le début du corps AABB par l'identité des reprises (décalages 0..4) et
gardait le premier candidat à égalité. Une intro « tail » rejoue la fin de l'air et les secondes fins font
tomber le meilleur score à 14/16 : sur 20 exports de chacun des trois styles de R1 et de la gigue québécoise
(contrôle), **16 à 17 exports sur 20 étaient alignés sur la mauvaise mesure** (intro lue 0 ou 1 au lieu de 1 ou 2),
donc les taux positionnels du généré (copies m.5←1, repos m.4/m.8, paires) décrivaient d'autres mesures.

Correction : `engine_material` lit la longueur de l'intro dans la vérité du moteur (`measures[].measure.position.section`,
première mesure `Tour`) et l'adopte quand l'identité des reprises la confirme (≥ 14/16) ; sans position publiée
(ancien format) le comportement est inchangé. Les `engine_ambiguous_alignments` tombent à 0 ; contrôle gigue québécoise :
copie A:m.5 = m.1 généré 90 % (15 % avant), repos tonique A:m.8 20 % (réel 16,4 %). Test :
`test_engine_alignment_follows_published_intro_when_candidates_tie`. `PYTHONPATH=src make test VENV=<venv partagé>` :
**258 réussis, 31 ignorés**. Les comparaisons moteur déjà publiées (DS-T9, phases 011/012) reposent sur l'ancien alignement
et sont à reprendre avant d'être citées.
