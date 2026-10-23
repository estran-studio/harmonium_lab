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

