# `wjazzd-melodie` — mélodie swing synthétisée depuis WJazzD (phase 019, E12)

Banque de cellules de `wjazzd_swing` (une mesure de huit croches, schéma du moteur) **synthétisée** à
partir de statistiques agrégées des solos du sous-ensemble `rhythmfeel = SWING` de la Weimar Jazz
Database v2.1. Demande de `harmonium_training` (étapes « lire le solo » et « mesures à trous »).

## Licence (ODbL 1.0, usage A)

*Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made
available here under the Open Database License (ODbL) 1.0 ; individual contents under the Database
Contents License (DbCL) 1.0.* Les solos restent la propriété de leurs ayants droit. **Aucune phrase de solo
n'est copiée** : `measures-melody.json` ne porte que des comptes et des parts ; `cells.toml` est tiré d'un
modèle statistique, puis chaque cellule est **refusée** si l'une de ses suites de notes figure dans un solo
(voir « Refus de copie »). Le profil est un *Produced Work* (ODbL §1.0, §4.3) ; la mention est dans
`[meta] corpus` du profil moteur. Aucun fichier sous droits, aucune base brute : `corpus/wjazzd/raw/` reste
gitignoré, l'index de suites de notes ne vit qu'en mémoire.

## Commandes

| Commande | Effet |
|---|---|
| `make melody-measures` | `measures-melody.json` (348 solos, 26 086 mesures, 124 348 attaques ; ~30 s) |
| `make melody-cells` | `cells.toml` (213 cellules, graine `MELODY_SEED` = 12 ; ~1 à 4 min) puis cellules par rôle et niveau |
| `make melody-check [FILE=…]` | aucune suite de N notes du fichier n'est dans un solo (code de sortie 1 sinon) |
| `make melody-compare MELODY_RUNS="--truth a.json … --label nom …" [MELODY_LEVELS="nom=2"]` | distance à WJazzD, conformité E10 : `compare-melody.{json,md}` |

Le moteur valide la banque : `harmonium-cli --check-cells references/wjazzd-melodie/cells.toml`.
Modules : `backing/melody_measures.py` (corpus et généré, un seul chemin de calcul), `backing/melody_cells.py`
(modèle, synthèse, refus de copie, niveaux), `backing/melody_compare.py` (distance, conformité). Tests :
`tests/test_backing_melody.py` (30 ; le contrôle sur la vraie base est `skipif` sans `corpus/wjazzd/raw/`).

## Ce qui est mesuré

Mesures 4/4 à quatre temps, huit créneaux de croche par mesure ; les attaques sont rangées par la fraction
de noire (seuils 0,31 et 0,81, lus sur l'histogramme : la croche swinguée est jouée vers 0,6 à 0,7). 31 805
attaques sur 156 153 (20 %) tombent sur un créneau déjà pris (seizièmes) et sont écartées. Définitions
complètes en tête de `melody_measures.py`.

| Mesure | Valeur |
|---|---|
| Attaques par mesure | moyenne 4,77 ; 5 % de mesures vides, 14 % à 8 attaques |
| Créneau d'attaque (part des mesures) | temps 1 : 0,64 ; croches de 0,53 à 0,60 ; temps 3 : 0,66 |
| Anticipation (attaque au créneau 7) | 0,58 des mesures ; 3 232 sans rejouer le temps 1 de la suivante (liaison ou silence) |
| Mesures sans attaque sur le temps 1 | 0,33 (**irreprésentables** dans une cellule, qui commence par une attaque) |
| Cibles sur les temps 1 et 3 | fondamentale 0,146, tierce 0,131, quinte 0,144, septième 0,090, autre note d'accord 0,020, gamme 0,262, chromatique 0,207 |
| Part d'accord sur les temps 1 et 3 / les quatre temps / les croches | 0,530 / 0,527 / 0,492 |
| Phrases | longueur médiane 5,5 temps (10 590 phrases, centiles 25–75 : 2,5–10) ; 20 % des temps sans note |
| Rôles de mesure | ouverture 0,178, conjoint 0,208, arpège 0,059, broderie 0,157, demi-cadence 0,103, cadence 0,117, creuses (< 3 attaques) 0,178 |
| Registre (centiles 5 / 50 / 95) | 53 / 65 / 77 (concert) |

## Synthèse

Un modèle par rôle de cellule du moteur (`open`, `run`, `arp`, `turn`, `cad_half`, `cad_full`) : chaîne
rythmique sur huit croches (probabilité d'attaque sachant les deux créneaux précédents), chaîne d'ordre 2
sur les pas diatoniques, première note selon sa relation à l'accord, cibles sur les temps dans l'accord de
tonique dans la proportion mesurée du rôle, tenue finale des cadences selon la loi mesurée. Détail en tête de
`melody_cells.py`.

**Boucle fermée.** Sous une grille, le moteur (modèle `loop`) ramène **chaque** note à la note d'accord la
plus proche ; une ligne conjointe s'y effondre en notes répétées (le bouche-trou en jouait 39 %, les solos
7 %). `melody_cells.realize` simule ce rapprochement sur les accords des grilles du profil
(`CHORD_BATTERY`) et refuse toute cellule dont la part de notes répétées rendues dépasse deux fois celle du
corpus (0,139). Contrôle : part de notes répétées simulée 0,27 pour la banque sans ce filtre, 0,29 mesurée
sur la vérité terrain du moteur ; avec le filtre : 0,080 mesurée, contre 0,070 au corpus.

**Niveaux E10.** Chaque cellule est rangée au plus bas niveau de difficulté qu'elle respecte (bornes de
référence de `e10-e11-melodie-qr.md`) ; la banque garde au moins 15 % de chaque niveau 1 à 3 par rôle
(`TIER_FLOOR`), et le poids d'une cellule est la part de son niveau dans les mesures du rôle du corpus.

| Rôle | niveau 1 | niveau 2 | niveau 3 | niveau 4 |
|---|---|---|---|---|
| open | 4 | 4 | 23 | 5 |
| run | 6 | 6 | 31 | 6 |
| arp | 4 | 4 | 13 | 10 |
| turn | 4 | 4 | 18 | 10 |
| cad_half | 4 | 4 | 18 | 5 |
| cad_full | 4 | 4 | 18 | 4 |

## Refus de copie : N

Une cellule est refusée si l'une de ses suites de **6 notes** a les mêmes pas diatoniques **et** les mêmes
durées qu'une suite d'un solo, ou si l'une de ses suites de **7 notes** a les mêmes pas (durées libres :
critère plus sévère). Les pas sont diatoniques (`steps_of`) : une tierce mineure et une tierce majeure sont
la même suite, ce qui refuse plus de cellules qu'un critère en demi-tons. Les suites ne franchissent pas un
silence d'une noire. Justification, lue dans `ngram_sharing` de `measures-melody.json` (parts des suites
distinctes présentes dans au moins deux solos) :

| n notes | contour + rythme | contour seul | demi-tons + rythme |
|---|---|---|---|
| 4 | 0,431 | 0,637 | 0,377 |
| 5 | 0,271 | 0,513 | 0,183 |
| 6 | **0,151** | 0,332 | 0,078 |
| 7 | 0,085 | **0,200** | 0,037 |
| 8 | 0,050 | 0,116 | 0,020 |

Une suite partagée par plusieurs solistes est un idiome commun (gamme, arpège, chiffrage) ; à 6 notes avec
rythme, 85 % des suites distinctes n'appartiennent qu'à un solo, à 7 notes sans rythme 80 %. En dessous ce
sont des fragments de langage courant ; au-dessus, refuser davantage est impossible : une cellule n'a que
huit croches, donc au plus 8 attaques. Les deux tailles sont des **décisions** du labo (`N_RHYTHM`,
`N_CONTOUR`), pas des seuils de droit. Sur la banque livrée, 51 tirages acceptés par ailleurs ont été refusés
pour copie (sur 53 175 tirages) ; `make melody-check` et le test
`test_aucune_cellule_de_la_banque_n_est_une_suite_de_n_notes_d_un_solo` confirment 0 cellule présente.

## Validation (`compare-melody.md`)

8 graines (1 à 8), 176 mesures chacune (le premier air du profil), `--record-truth` du moteur sur
`profiles/wjazzd_swing` ; `bouche_trou` = l'ancienne banque, mêmes accompagnement et arrangement avec la
mélodie ajoutée, ses rôles `open` et `run` seuls. Distance de 0 (identique au corpus) à 1 ; mesures de
`melody_measures.measure`, distances de `bass_compare`.

| Famille | bouche-trou | banque swing | niveau 1 | niveau 2 | niveau 3 |
|---|---|---|---|---|---|
| intervalles | 0,359 | **0,169** | 0,268 | 0,242 | 0,244 |
| rythme | 0,383 | **0,181** | 0,592 | 0,581 | 0,199 |
| accord (notes sur les temps) | 0,493 | 0,487 | 0,197 | 0,127 | 0,099 |
| registre | 0,424 | **0,292** | 0,419 | 0,383 | 0,301 |
| phrasé | 0,599 | 0,599 | 0,599 | 0,599 | 0,599 |
| **agrégée** | 0,435 | **0,321** | 0,374 | 0,341 | 0,239 |

- **Part des notes sur les temps forts dans l'accord courant** : corpus 0,530 ; banque swing **1,000**
  (chaque note est ramenée à l'accord) ; niveaux 1 à 3 (`chord_fit = false`) 0,52 à 0,57.
- **Notes répétées** : corpus 0,070 ; bouche-trou 0,390 ; banque 0,080.
- **Attaques par mesure** : corpus 4,77 ; bouche-trou 7,96 ; banque 4,96.
- **Difficulté E10** : aux niveaux 1, 2 et 3 (filtre de référence, `chord_fit = false`), 0 mesure hors bornes
  sur 1 400 par niveau ; pires valeurs saut / attaques / durée / ambitus : 4 / 4 / 2 / 7, 5 / 4 / 2 / 9,
  7 / 7 / 1 / 12. Niveau 4 = le profil. La mesure de clôture de l'air n'est pas filtrée par le moteur : écartée.
  Les niveaux 1 et 2 s'écartent du corpus pour le rythme **par construction** (≤ 4 attaques, durée ≥ 2).
- **Hors de portée d'une banque** (manques de schéma, listés dans le compte rendu du moteur) : le **phrasé**
  (une cellule n'a pas de silence : phrases de 701 temps contre 5,5, silences 0,4 % contre 20 %) ; le
  **rapprochement tout-accord** du modèle `loop` (aucune note de passage ni d'approche : la part d'accord
  de 1,000 ci-dessus, intervalles de ±1 demi-ton : 2 % contre 22 %) ; les mesures qui ne commencent pas par une attaque
  (33 % au corpus).

## Limites

- Le corpus ne donne ni les cellules ni les phrases au moteur : la banque est un modèle de surface
  (rythme, contour, cibles, cadences), pas des licks ; elle ne contient ni chiffrage ni formule d'une
  œuvre. Elle n'a **pas été écoutée** (D5/D7 : l'écoute est celle du propriétaire).
- Les tailles `N` sont des décisions de labo ; une banque à `N` plus petit refuserait des idiomes communs.
- `CHORD_BATTERY` est écrit à la main d'après les grilles du profil (durées arrondies) ; une grille d'hôte
  très différente (modale, sans septième) rapproche autrement les notes.
- Mesures irreprésentables dans une cellule (comptées dans le corpus, pas dans la banque) : ligne qui
  commence par une liaison ou un silence, mesures vides, anticipation liée au temps 1 suivant.
