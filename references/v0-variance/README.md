# V0 — Ligne de base de la variance par chorus et par couche (phase 019, vague 1)

Mesure de ce que le moteur varie **d'un chorus au suivant** (le « sonne procédural, pas une boucle »
de training) et **d'une graine à l'autre**, couche par couche. Les seuils de V2 partent de ces
chiffres (section « Seuils V2 proposés »). Extension de `harmonium-lab seed-variety` (P2 :
`src/harmonium_lab/seedvariety.py`) : option `--chorus N`, code dans `src/harmonium_lab/chorusvariety.py`.

## Conditions

- Moteur : `~/Project/bascanada/harmonium`, code de `63e26da` (HEAD `fa9c630` = docs seulement ; **avant A3**),
  `harmonium-cli --release`, lancé depuis le dossier du moteur (`assets/`). Dépôt moteur non modifié.
- **16 graines (1..16) × 16 chorus** par profil : `--tours 16` (limite du moteur, `tours_per_tune` ≤ 16).
  Un chorus = un **tour** du moteur = une passe de `form.sequence` ; pour la grille de 8 mesures : la partie
  répétée. Numéro de chorus lu dans `position.chorus` s'il existe (A3), sinon `position.tour`, sinon déduit de
  `bar_in_cycle` (retour à 0). Mesures d'intro, air suivant du set et **mesure de clôture** de l'air
  (le moteur remplace la dernière mesure du dernier tour par la tonique et la grosse caisse) écartés.
- Profils (durée d'un chorus entre parenthèses) :

| Profil | Chorus | Remarque |
|---|---:|---|
| `wjazzd_swing` | 44 mesures | grille par défaut : blues de 12 + AABA de 32 (un tour = les deux formes) |
| `wjazzd_swing_grille8` | 8 mesures | **grille utilisateur** : copie de `wjazzd_swing` hors dépôt (`/tmp/harmonium-019/v0/`), `[form]` et `[harmony.parts]` remplacés par une partie de 8 mesures (I6 · VI7 · ii7 · V7 · iii7 · VI7 · ii7 V7 · I6), `scripts/v0_user_grid_profile.py` |
| `nt_desert` | 48 mesures | profil de jeu, `sequence = [0, 1, 2, 3, 0]` |
| `isaac_basement` | 40 mesures | profil de jeu |
| `isaac_cellar` | 48 mesures | profil de jeu |
| `isaac_burning` | 40 mesures | profil de jeu |
| `isaac_downpour` | 48 mesures | profil de jeu |
| `reel_quebecois` | 32 mesures | trad, AABB ; intro écartée |

- Durée : 744 s à froid pour les 8 profils (17 exports moteur par profil : une sonde d'un tour qui donne la
  longueur de forme, puis une par graine ; rendu audio hors ligne compris), 22 s avec le cache
  (`/tmp/harmonium-019/v0/truth/`, hors dépôt : vérités terrain et MIDI). Rien n'a été réduit.
- Aucun rendu audio dans le dépôt : seuls les JSON de ce dossier sont versionnés (≈ 40 Ko par profil).

## Reproduire

```bash
cd ~/Project/bascanada/harmonium && cargo build -q -p harmonium-cli --release
cd <harmonium_lab>
make v0-variance ENGINE_DIR=~/Project/bascanada/harmonium \
     ENGINE_BIN=~/Project/bascanada/harmonium/target/release/harmonium-cli    # 8 profils → references/v0-variance/*.json
python -m harmonium_lab.chorusvariety references/v0-variance/*.json            # tableaux de synthèse ci-dessous
# un profil, tableau complet (couches, rôles de batterie, densité, intensité) :
.venv/bin/harmonium-lab seed-variety --profile wjazzd_swing --seeds 16 --chorus 16 --engine-dir ~/Project/bascanada/harmonium \
     --engine-bin ~/Project/bascanada/harmonium/target/release/harmonium-cli --label V0 --work-dir /tmp/harmonium-019/v0/truth \
     -o /tmp/wjazzd_swing.json --markdown
# grille utilisateur seule :
make v0-grid ENGINE_DIR=~/Project/bascanada/harmonium      # → /tmp/harmonium-019/v0/wjazzd_swing_grille8
```

Variables : `V0_PROFILES="id|dossier …"`, `V0_SEEDS`, `V0_CHORUS`, `V0_OUT`, `V0_DIR`, `V0_GRID_DIR`.
`--steady-from N` (défaut 3) : rang du chorus à partir duquel on compte « stable ».

## Définition des signatures

Hauteurs relatives à la tonique de la mesure (`position.key`). **Vélocités et décalages d'interprétation
ignorés** : l'humanisation dérive de la graine même quand le motif est identique. Une mesure est repérée par sa
**place dans le chorus** (`bar_in_cycle`) : chorus k et chorus j se comparent mesure à mesure, à place égale.

| Couche | Notes lues | Éléments de la signature d'une mesure |
|---|---|---|
| `accords` (symboles) | `chord_changes` | (pas, fondamentale, qualité, mineur, basse) |
| `comping rythme` | piste 1 (Chords) | pas d'attaque |
| `comping voicings` | piste 1 | hauteurs relatives triées de chaque attaque, dans l'ordre du temps (voicings joués) |
| `basse` | piste 2 | (pas, hauteur, durée) |
| `batterie` | pistes 3 et 4 | (piste, pas, note) ; par rôle GM : `kick` 35-36, `snare` 37-40, `hihat` 42-44-46, `ride` 51-53-59, `other` (les rôles sont indicatifs hors banque GM, p. ex. `reel_quebecois`) |
| `mélodie` (hors accompagnement) | pistes 0 et 5 | (piste, pas, hauteur, durée) |
| `orchestration` | `[instruments]` du profil + `program_change` du MIDI (`--record-midi`) | (canal, banque, programme) par piste ; un changement de programme dans le MIDI à la mesure m vaut à partir de m |
| `accompagnement` | accords, comping (rythme + voicings), basse, batterie | tuple des signatures ; mélodie et orchestration à part |
| densité, intensité | toutes les notes, par groupe (comping, basse, batterie, mélodie) | notes par mesure ; vélocité moyenne ; `intensity` de la vérité terrain |

- **Égalité exacte** : signatures égales. **Distance graduée** : 1 − Jaccard des ensembles d'éléments (deux mesures
  vides : 0) ; orchestration : part des pistes dont le programme diffère ; accompagnement : moyenne des distances
  des couches actives. Une mesure est **active** si la couche joue dans l'une des deux mesures comparées : une
  couche muette (basse absente d'un pont) n'est ni stable ni variable.
- **Intra-graine** (une graine, chorus k contre chorus j) : part des mesures changées, chorus voisins (k, k+1),
  « stable » (chorus voisins de rang ≥ 3 : les entrées de couches par tour, `[entries]`, sont passées), toutes
  paires (p10, p50, p90 dans le JSON), matrice 16 × 16 moyennée sur les graines, part de **paires de chorus
  identiques** (la boucle), nombre moyen de chorus distincts par graine, détail par partie nommée.
- **Inter-graines** (chorus égal, place égale) : part des places où les 16 graines ne sont pas toutes égales,
  diversité `(distinct − 1) / (N − 1)`, distance graduée par paire de graines, et **séquences distinctes** :
  nombre de suites complètes de 16 chorus différentes parmi les 16 graines (16 : chaque graine a la sienne ;
  1 : la graine ne change rien à la couche).
- **Numérique** (densité, vélocité, intensité du moteur) : `cv` = écart-type / moyenne des valeurs par chorus
  (intra, moyenné sur les graines ; inter, sur les graines à chorus égal, moyenné sur les chorus) et
  **étendue de la trajectoire** = (max − min) / moyenne de la courbe moyenne sur les graines : un arc sur
  plusieurs chorus l'élargit.

## Résultats

Tous les chiffres en %, sauf mention. `·` : couche muette dans le profil ; `—` : non défini. Détail (matrices,
distributions, par partie, rôles de batterie) : un JSON par profil dans ce dossier.

**Intra-graine : % de mesures changées d'un chorus au suivant (chorus ≥ 3)**

| Profil | accords | comping rythme | comping voicings | basse | batterie | mélodie | orchestration | accompagnement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | 0 | 82 | 75 | 93 | 0 | · | 0 | 100 |
| `wjazzd_swing_grille8` | 0 | 83 | 73 | 92 | 0 | · | 0 | 97 |
| `nt_desert` | 0 | 0 | 0 | 0 | 0 | 17 | 0 | 0 |
| `isaac_basement` | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 0 |
| `isaac_cellar` | 0 | 0 | 0 | 0 | 0 | 33 | 0 | 0 |
| `isaac_burning` | 0 | 0 | 0 | 0 | 0 | 31 | 0 | 0 |
| `isaac_downpour` | 0 | 0 | 0 | 0 | 0 | 32 | 0 | 0 |
| `reel_quebecois` | 0 | 0 | 0 | 60 | 0 | 67 | 0 | 60 |

**Intra-graine : % de paires de chorus identiques**

| Profil | accords | comping rythme | comping voicings | basse | batterie | mélodie | orchestration | accompagnement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | 100 | 0 | 0 | 0 | 100 | · | 100 | 0 |
| `wjazzd_swing_grille8` | 100 | 0 | 0 | 0 | 100 | · | 100 | 0 |
| `nt_desert` | 100 | 100 | 100 | 100 | 88 | 0 | 100 | 88 |
| `isaac_basement` | 100 | 100 | 100 | 100 | 100 | 1 | 100 | 100 |
| `isaac_cellar` | 100 | 100 | 100 | 100 | 100 | 0 | 100 | 100 |
| `isaac_burning` | 100 | 100 | 100 | 100 | 100 | 1 | 100 | 100 |
| `isaac_downpour` | 100 | 100 | 100 | 100 | 100 | 0 | 100 | 100 |
| `reel_quebecois` | 100 | 89 | 89 | 0 | 92 | 0 | 100 | 0 |

**Intra-graine / inter-graines : distance graduée moyenne, en % (chorus voisins / graines à chorus égal)**

| Profil | accords | comping rythme | comping voicings | basse | batterie | mélodie | orchestration | accompagnement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | 0 / 0 | 70 / 36 | 46 / 24 | 60 / 31 | 0 / 19 | · | 0 / 0 | 35 / 22 |
| `wjazzd_swing_grille8` | 0 / 0 | 72 / 34 | 33 / 15 | 67 / 37 | 0 / 21 | · | 0 / 0 | 34 / 22 |
| `nt_desert` | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 9 | 2 / 0 | 14 / 10 | 0 / 0 | 0 / 1 |
| `isaac_basement` | 0 / 17 | 0 / 0 | 0 / 17 | 0 / 22 | 0 / 11 | 25 / 66 | 0 / 0 | 0 / 14 |
| `isaac_cellar` | 0 / 10 | 0 / 0 | 0 / 10 | 0 / 34 | 0 / 12 | 25 / 50 | 0 / 0 | 0 / 13 |
| `isaac_burning` | 0 / 12 | 0 / 0 | 0 / 12 | 0 / 37 | 0 / 21 | 23 / 59 | 0 / 0 | 0 / 16 |
| `isaac_downpour` | 0 / 25 | 0 / 0 | 0 / 25 | 0 / 42 | 0 / 19 | 31 / 60 | 0 / 0 | 0 / 22 |
| `reel_quebecois` | 0 / 52 | 1 / 0 | 1 / 81 | 28 / 83 | 4 / 3 | 20 / 95 | 0 / 0 | 7 / 44 |

**Inter-graines : % de places (chorus, mesure) où les graines diffèrent**

| Profil | accords | comping rythme | comping voicings | basse | batterie | mélodie | orchestration | accompagnement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | 0 | 81 | 73 | 92 | 100 | · | 0 | 100 |
| `wjazzd_swing_grille8` | 0 | 75 | 63 | 96 | 100 | · | 0 | 100 |
| `nt_desert` | 0 | 0 | 0 | 29 | 0 | 47 | 0 | 17 |
| `isaac_basement` | 35 | 0 | 35 | 45 | 81 | 100 | 0 | 95 |
| `isaac_cellar` | 21 | 0 | 21 | 100 | 88 | 99 | 0 | 100 |
| `isaac_burning` | 25 | 0 | 25 | 100 | 88 | 100 | 0 | 100 |
| `isaac_downpour` | 50 | 0 | 50 | 75 | 88 | 99 | 0 | 100 |
| `reel_quebecois` | 81 | 2 | 100 | 100 | 6 | 100 | 0 | 100 |

**Inter-graines : séquences de 16 chorus distinctes parmi les graines**

| Profil | accords | comping rythme | comping voicings | basse | batterie | mélodie | orchestration | accompagnement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | 1 | 2 | 2 | 2 | 11 | · | 1 | 14 |
| `wjazzd_swing_grille8` | 1 | 2 | 2 | 2 | 3 | · | 1 | 5 |
| `nt_desert` | 1 | 1 | 1 | 8 | 1 | 16 | 1 | 8 |
| `isaac_basement` | 8 | 1 | 8 | 16 | 7 | 16 | 1 | 16 |
| `isaac_cellar` | 4 | 1 | 4 | 16 | 7 | 16 | 1 | 16 |
| `isaac_burning` | 4 | 1 | 4 | 16 | 7 | 16 | 1 | 16 |
| `isaac_downpour` | 7 | 1 | 7 | 16 | 7 | 16 | 1 | 16 |
| `reel_quebecois` | 16 | 2 | 16 | 16 | 2 | 16 | 1 | 16 |

**Couches numériques** (cv : écart-type / moyenne, en % ; étendue : (max − min) / moyenne de la trajectoire)

| Profil | Groupe | Densité : cv intra | Densité : étendue | Densité : cv inter | Vélocité : cv intra | Vélocité : étendue | Vélocité : cv inter |
|---|---|---:|---:|---:|---:|---:|---:|
| `wjazzd_swing` | all | 3 | 7 | 4 | 0 | 1 | 0 |
| `wjazzd_swing` | comping | 6 | 16 | 4 | 0 | 1 | 0 |
| `wjazzd_swing` | bass | 0 | 0 | 0 | 0 | 0 | 0 |
| `wjazzd_swing` | drums | 0 | 0 | 9 | 0 | 0 | 0 |
| `wjazzd_swing` | intensité moteur | 0 | 0 | 0 | | | |
| `wjazzd_swing_grille8` | all | 6 | 15 | 6 | 1 | 2 | 1 |
| `wjazzd_swing_grille8` | comping | 13 | 34 | 7 | 1 | 2 | 1 |
| `wjazzd_swing_grille8` | bass | 0 | 0 | 0 | 0 | 0 | 0 |
| `wjazzd_swing_grille8` | drums | 0 | 0 | 14 | 0 | 0 | 1 |
| `wjazzd_swing_grille8` | intensité moteur | 0 | 0 | 0 | | | |
| `nt_desert` | all | 7 | 28 | 1 | 0 | 1 | 1 |
| `nt_desert` | comping | 0 | 1 | 0 | 0 | 0 | 0 |
| `nt_desert` | bass | 1 | 4 | 10 | 0 | 0 | 1 |
| `nt_desert` | drums | 6 | 25 | 0 | 0 | 0 | 0 |
| `nt_desert` | melody | 18 | 67 | 1 | 0 | 0 | 0 |
| `nt_desert` | intensité moteur | 0 | 0 | 0 | | | |
| `isaac_basement` | all | 0 | 1 | 0 | 0 | 0 | 0 |
| `isaac_basement` | comping | 0 | 2 | 0 | 0 | 0 | 0 |
| `isaac_basement` | bass | 1 | 3 | 3 | 0 | 0 | 0 |
| `isaac_basement` | drums | 0 | 2 | 0 | 0 | 0 | 0 |
| `isaac_basement` | melody | 2 | 3 | 2 | 0 | 0 | 0 |
| `isaac_basement` | intensité moteur | 0 | 0 | 0 | | | |
| `isaac_cellar` | all | 0 | 1 | 1 | 0 | 0 | 0 |
| `isaac_cellar` | comping | 0 | 1 | 0 | 0 | 0 | 0 |
| `isaac_cellar` | bass | 0 | 0 | 3 | 0 | 0 | 0 |
| `isaac_cellar` | drums | 0 | 1 | 0 | 0 | 0 | 0 |
| `isaac_cellar` | melody | 2 | 2 | 2 | 0 | 0 | 0 |
| `isaac_cellar` | intensité moteur | 0 | 0 | 0 | | | |
| `isaac_burning` | all | 0 | 0 | 1 | 0 | 0 | 0 |
| `isaac_burning` | comping | 0 | 1 | 0 | 0 | 0 | 0 |
| `isaac_burning` | bass | 0 | 0 | 1 | 0 | 0 | 0 |
| `isaac_burning` | drums | 0 | 1 | 0 | 0 | 0 | 0 |
| `isaac_burning` | melody | 3 | 5 | 4 | 0 | 0 | 0 |
| `isaac_burning` | intensité moteur | 0 | 0 | 0 | | | |
| `isaac_downpour` | all | 1 | 6 | 1 | 0 | 0 | 0 |
| `isaac_downpour` | comping | 0 | 0 | 0 | 0 | 0 | 0 |
| `isaac_downpour` | bass | 0 | 0 | 5 | 0 | 0 | 1 |
| `isaac_downpour` | drums | 0 | 1 | 0 | 0 | 0 | 1 |
| `isaac_downpour` | melody | 9 | 37 | 1 | 0 | 0 | 0 |
| `isaac_downpour` | intensité moteur | 0 | 0 | 0 | | | |
| `reel_quebecois` | all | 11 | 45 | 3 | 2 | 4 | 1 |
| `reel_quebecois` | comping | 5 | 22 | 1 | 0 | 0 | 0 |
| `reel_quebecois` | bass | 7 | 25 | 6 | 1 | 1 | 1 |
| `reel_quebecois` | drums | 16 | 65 | 8 | 0 | 1 | 1 |
| `reel_quebecois` | melody | 12 | 50 | 5 | 0 | 1 | 1 |
| `reel_quebecois` | intensité moteur | 0 | 0 | 0 | | | |


## Manques connus, en chiffres

| Manque (plan 019) | Chiffre V0 |
|---|---|
| **Orchestration fixe** | 1 seul programme par piste sur les 16 graines × 16 chorus, dans les 8 profils (`orchestration_programs` des JSON : p. ex. `wjazzd_swing` comping 0, basse 32, kit 128:32). Orchestration : 0 % de changement d'un chorus au suivant, 0 % entre graines, 1 séquence distincte sur 16. |
| **Forme identique d'un chorus à l'autre** | Profils de jeu (`nt_desert`, `isaac_*`) : **88 à 100 % des paires de chorus identiques** pour le comping, la basse et la batterie (`nt_desert` 88 % : seul le premier chorus diffère, par les entrées de couches) ; 0 % de mesures changées en régime stable. Seule la mélodie bouge (17 à 33 % des mesures changées d'un chorus au suivant). `wjazzd_swing` : 0 % de mesures de batterie changées, 100 % des paires de chorus identiques pour la batterie ; `reel_quebecois` : comping 0–1 %, batterie 0 %, comping et batterie à 89–92 % de paires identiques. |
| **La graine ne change presque rien au comping et à la basse de `wjazzd_swing`** | **2 séquences distinctes sur 16 graines** pour le comping (rythme et voicings) et la basse, dans la grille par défaut comme dans la grille de 8 mesures : les graines se partagent en deux classes (grille par défaut : 1, 4, 8, 9, 13, 14, 15 contre les neuf autres) qui rejouent exactement les mêmes 16 chorus. Cause probable **[INFERENCE, lue dans le code moteur, non vérifiée par exécution]** : `generator.rs` (l. 508, 1456) tire le motif de comping avec `mix(tune.material_seed, mesure jouée)` et `material_seed = tune_seed(matériel mélodique écrit)` (l. 1688-1744), sans la graine de session ; un profil dont la mélodie n'est pas jouée n'aurait que deux matériels. La batterie, tirée par `variant_seed`, est moins touchée (11 séquences / 16 sur la grille par défaut, 3 sur la grille de 8 mesures). À corriger côté moteur avant de compter sur « beaucoup de variance d'un tirage à l'autre » (A1/A3). |
| **Comping tiré mesure par mesure** | `wjazzd_swing` : 82–83 % des mesures de comping changent d'un chorus au suivant, soit le plafond de la banque de 6 rythmes (poids 4-3-3-2-1-1 : P(changer) = 1 − Σp² = 79,6 % ; mesuré, toutes paires de chorus : 79,8 %). Les profils de jeu n'ont qu'un motif de comping : 0 %. |
| **Batterie** | `wjazzd_swing` (grille de 8 mesures) : 85 % des notes au ride, 15 % au charleston pédale, aucune caisse claire ni grosse caisse (hors clôture) ; motif constant d'un chorus à l'autre (0 %), mais différent d'une graine à l'autre (distance graduée 19–21 %). Choix pondérés « stables pour chaque partie et densité d'un air » (`profiles/README.md`, « Batterie par graine »). |
| **Densité et intensité plates** | Intensité du moteur : 0,50 constant dans les 8 profils (étendue 0 %). Vélocité moyenne : cv intra ≤ 1 % sous grille, ≤ 2 % ailleurs. Densité des notes : cv intra 3 % (`wjazzd_swing`, 44 mesures) à 6 % (grille 8), tout dans le comping ; basse 0 % ; batterie 0 %. Les valeurs élevées de `reel_quebecois` (11 %) et `nt_desert` (7 %) viennent des entrées de couches par tour et de la variation de la mélodie, pas d'un arc. |
| **Accords** | 0 % de mesures changées d'un chorus au suivant (par construction : la grille est fournie, D4) ; entre graines 0 % pour `wjazzd_swing` et `nt_desert`, 21 à 50 % pour `isaac_*`, 81 % pour `reel_quebecois` (harmonie tirée). |
| **Basse** | `wjazzd_swing` : 92–93 % des mesures changées d'un chorus au suivant (distance graduée 60–67 %), mais 2 séquences seulement entre graines (ci-dessus). `reel_quebecois` : 60 %. Profils de jeu : 0 %. |

## Seuils V2 proposés

À mesurer avec la même commande (`--chorus 16`, 16 graines), sur la grille de 8 mesures et la grille par
défaut de chaque profil B\*, **sous grille utilisateur** (accords imposés). « Stable » : chorus ≥ 3. Les
seuils 1 à 7 sont des mesures de cette page ; les seuils 8 à 10 (arc) n'ont pas de référence humaine mesurée :
ils sont fixés au-dessus du bruit de V0 et restent à confirmer par l'écoute de V2.

| # | Mesure (couche) | V0, `wjazzd_swing` défaut / grille 8 | Seuil V2 | Argument |
|---|---|---|---|---|
| 1 | Paires de chorus identiques, `accompagnement` | 0 % / 0 % ; **88–100 %** pour les profils de jeu | **0 %** ; `distinct_choruses` = 16 / 16 | Le critère « pas une boucle » lui-même. `wjazzd_swing` le passe seulement par le comping et la basse. |
| 2 | Paires de chorus identiques, par couche : comping rythme, comping voicings, basse, batterie | 0, 0, 0, **100** % | **≤ 5 %** chacune | Une couche qui rejoue le chorus précédent à l'identique s'entend (batterie V0 : 100 %). La tolérance de 5 % laisse passer un break ou un retour voulu. |
| 3 | Accords (symboles) changés d'un chorus au suivant | 0 % / 0 % | **≤ 2 %** (plafond, pas plancher) | D4 : pas de réharmonisation par défaut. V0 : 0 %. |
| 4 | Comping rythme changé (stable) | 82 % / 83 % | **≥ 75 %** | Non-régression. Plafond théorique d'une banque : 1 − 1/N_eff (N_eff = 1/Σp²) ; 75 % exige N_eff ≥ 4 rythmes ou phrases équivalents par position (V0 : 4,9). Pour A1 (phrases de 2 à 8 mesures) le tirage par phrase doit garder N_eff ≥ 4. |
| 5 | Comping voicings changés (stable) | 75 % / 73 % | **≥ 65 %** | Non-régression avec marge pour la conduite de voix (`voice_leading` impose des voix communes) ; A5 doit l'élargir, pas le réduire. |
| 6 | Basse changée (stable) | 93 % / 92 % | **≥ 80 %** | Non-régression avec marge pour A4 (deux temps, notes répétées : plus de mesures semblables). `reel_quebecois` : 60 %. |
| 7 | Batterie changée (stable), toutes notes ; distance graduée | **0 %** / **0 %** ; 0 % | **≥ 30 %** ; ≥ 10 % | Le ride (85 % des notes) est la référence rythmique et reste constant ; ce sont les notes de comping de la batterie, charleston, caisse claire, grosse caisse, breaks, qui doivent bouger. 30 % des mesures = bien en dessous du comping (82 %), au-dessus d'un simple break par chorus (1 mesure sur 8 = 12 %). |
| 8 | Séquences de 16 chorus distinctes parmi 16 graines : comping rythme, basse, batterie | **2**, **2**, 11 / **2**, **2**, 3 | **≥ 12 / 16** chacune | La graine doit changer le chorus ; V0 : deux classes de graines. Le corriger exige que la graine de session entre dans le tirage (voir « Manques »). Un profil de jeu a déjà 16 / 16 pour la basse et la mélodie. |
| 9 | Orchestration entre graines : programmes distincts sur 16 graines par piste ; séquences distinctes | 1 par piste ; 1 / 16 | comping **≥ 3**, basse **≥ 2**, kit de batterie **≥ 2** ; séquences **≥ 4 / 16** | A2, sans Odin (D1) : limité par la banque SoundFont (L1). Entre chorus : changement optionnel ; s'il est activé, **≥ 10 %** des paires de chorus voisins changent au moins un programme (V0 : 0 %). |
| 10 | Arc, `accompagnement` : densité (notes / mesure) cv intra ; étendue de la trajectoire | 3 % ; 7 % / 6 % ; 15 % | cv **≥ 10 %** ; étendue **≥ 25 %** | Bruit de V0 : 3 à 6 % de cv (tirage de rythmes), étendue 7 à 15 % ; le seuil vaut ≥ 2 × le bruit, sinon on ne distingue pas un arc d'un tirage. |
| 11 | Arc, vélocité moyenne : cv intra ; étendue | 0 % ; 1 % / 1 % ; 2 % | cv **≥ 3 %** ; étendue **≥ 8 %** | Bruit de V0 : ≤ 1 % (≈ 0,7 point MIDI sur 70). 8 % de la moyenne ≈ 5,6 points : un écart que l'écoute peut juger. |
| 12 | Arc, `intensity` du moteur (étendue de la trajectoire) | **0 %** (0,50 partout) | **≥ 20 %** | A3 expose l'intensité par chorus : une courbe constante ne peut pas porter l'arc. |

Lecture : `wjazzd_swing` passe aujourd'hui 1, 3, 4, 5 et 6 (le critère 1 seulement grâce au comping et à la basse :
la batterie, l'orchestration et la forme sont bouclées) ; il échoue à 2 (batterie), 7, 8, 9, 10, 11 et 12.
`nt_desert` et `isaac_*` échouent à 1, 2 et 4 à 12 (accompagnement identique d'un chorus à l'autre) ; leurs accords
varient entre graines (0 à 81 % des places), sans grille utilisateur : le seuil 3 ne les concerne pas.
`reel_quebecois` passe 1, échoue à 2 (comping 89 %, batterie 92 % de paires identiques), 4 à 9, 11 et 12, et passe 10 par
les entrées de couches du premier chorus, pas par un arc.
Aucun plafond n'est proposé : une variance sans musique ne prouve rien, l'écoute de V2 reste le juge.

## Limites de la mesure

- **Orchestration** : lue dans `[instruments]` (kit de percussion, absent du MIDI) et dans les `program_change` du
  MIDI exporté (`--record-midi`, `timeline_to_midi` : un seul programme par canal, au tick 0, programme du profil).
  Un changement d'instrument au chorus par A2 n'apparaît que s'il est écrit dans le MIDI ou dans la vérité terrain ;
  sinon cette couche restera à 0 % même si elle bouge en lecture temps réel (`take_pending_program_changes`).
  À vérifier à la fusion d'A2 ; la lecture est isolée dans `orchestration_sigs`.
- **Numéro de chorus** : `position.chorus` (A3) prime sur `position.tour`. Si A3 garde `tour` et ajoute `chorus` avec
  un autre découpage (p. ex. un chorus par partie), tous les chiffres suivent `chorus` ; le seuil « chorus ≥ 3 »
  d'un profil à entrées par tour se règle par `--steady-from`.
- **Clôture de l'air** : la dernière mesure du dernier chorus est écartée ; avec la « retombée finale » d'A3, elle
  peut occuper plusieurs mesures, qu'il faudra écarter de la même façon (`load_truth`).
- **Humanisation** : vélocités et décalages ne comptent pas dans les signatures ; la densité et la vélocité moyenne
  les incluent (couche numérique).
- **Rôles de batterie** : indicatifs hors banque GM ; `reel_quebecois` (banque 1, podorythmie) n'a que deux notes.
- **Mélodie** : mesurée pour comparaison, hors seuils (training joue contre la grille, pas de mélodie).
- `--tours` du moteur est limité à 16 : pas de mesure au-delà de 16 chorus.
