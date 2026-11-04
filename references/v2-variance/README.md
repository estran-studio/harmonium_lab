# V2 — Variance prouvée par style (phase 019, vague 5)

Mesure, sur **les 32 profils distribués**, de ce que « New seed » change et de ce qui change d'un chorus au suivant,
avec les seuils de V0 ajustés au vu des chiffres (section « Seuils »). Outil : `src/harmonium_lab/v2variance.py`
(étend `seed-variety --chorus`, V0), `src/harmonium_lab/usergrid.py` (grille utilisateur), `src/harmonium_lab/v2distance.py`
(distance au corpus). Compte rendu côté moteur : `specs/019-bibliotheque-accompagnements/v2-variance.md`. Rien n'est
modifié dans le moteur ni dans les profils.

## Conditions

- Moteur : binaire `harmonium-cli --release` compilé depuis le worktree `v2t1-preuve-livraison` (HEAD `3fb01da`, profils
  identiques à ceux de `main` `22c3afb`, `engine_rev` des JSON ; `TUNING_VERSION` 32), lancé depuis le checkout principal
  du moteur (pour `assets/`, GeneralUser GS). Aucune lecture audio : vérités terrain (`--record-truth`) et MIDI
  (`--record-midi`) seulement.
- **16 graines (1..16) × 4 chorus** par profil (`--tours 4`), `seed-variety --chorus 4` (V0 : 16 chorus ; le brief de V2 en
  demande 4, ce qui couvre l'arc des profils de style, de 3 étapes sur 4 chorus, et laisse le chorus 4 à la retombée).
  Mesures d'intro, air suivant et mesure de clôture écartés (V0). **Un chorus = un tour de la forme du profil** (12 à 48
  mesures selon le profil ; 8, 16 ou 24 mesures sous grille utilisateur).
- Mesure « **sous grille utilisateur** » : les 17 profils `loop` d'accompagnement (`gmd_*`, `wjazzd_*`) sont copiés par
  `usergrid.py` sous une grille standard de 8 mesures (I6 · VI7 · ii7 · V7 · iii7 · VI7 · ii7 V7 · I6) avec
  `[fixed_tonality]` (fa ionien, ou celle du profil), comme le fait l'hôte. Généralise `scripts/v0_user_grid_profile.py`
  (V0 : 16 pas par mesure seulement) : pas par mesure (12, 16), `steps_per_chord` du profil. **Longueur** : 8 mesures,
  portée à 16 ou 24 seulement si le moteur refuse le profil à cause d'un `breaks.start` de l'arc (`gmd_latin_*`, `gmd_funk`,
  `gmd_afrocuban` : 16 ; `gmd_jazz_waltz`, `wjazzd_ballad` : 24). Les profils de jeu (`isaac_*`, `nt_desert`) sont `loop`
  mais portent des motifs de basse par partie nommée : **refusés** par le chargeur (`accompaniment.bass.motifs[0].part: partie
  inconnue dans form.parts`) ; les profils trad (`melody_functional`, `none`) n'ont pas de grille utilisateur : « sans objet ».
- Durée à froid : environ 33 minutes pour les 64 mesures (3 exports en parallèle, machine partagée) ; les vérités
  terrain sont en cache hors dépôt (`--work-dir`), un rejeu des JSON dure ~1 minute.

## Reproduire

```bash
cd <moteur> && cargo build --release -p harmonium-cli
cd <labo>
make v2-variance ENGINE_DIR=<moteur avec assets/> ENGINE_BIN=<moteur>/target/release/harmonium-cli     # collect + report
make v2-report                                   # seulement les tableaux, depuis les JSON versionnés → summary.json
make v2-distance-trad ENGINE_DIR=… ENGINE_BIN=… CORPUS_ROOT=<corpus/ du labo>        # écart au corpus des profils trad
make v2-distance-batterie ENGINE_WORKTREE=<moteur compilé en --release>             # batterie contre le GMD (scripts B)
```

Fichiers : `<profil>.json` (profil tel que distribué), `<profil>.grille.json` (sous grille ; « sans objet » avec la raison pour
les profils sans grille), `summary.json` (valeurs et verdicts par critère), `distance-trad.json`,
`distance-batterie-gmd.json`. Un JSON porte `variance` (sortie de `chorusvariety`, V0 : matrices, par partie, numérique),
`habillage` (une ligne par graine : tempo, tonalité, programmes, voicing, arc, swing, `session`), `bass_walking`, `meter`.

## Définitions

- **Habillage distinct** (R2) : tuple (grappe de tempo à ± 8 BPM du premier tempo de la grappe, tonalité et mode, programmes de
  mélodie, d'accords, de basse, kit (banque, programme), famille de voicings, swing) lu dans le **premier**
  `MeasureSnapshot` de chaque graine (`session`, `instruments`, `tempo`, `swing_ratio`, `position`). Sous grille, **hôte :
  tempo et tonalité imposés** : on compte (mélodie, accords, basse, kit, voicings) seuls.
- **Mesures changées d'un chorus au suivant** (`intra.adjacent.exact`) : sur **toutes** les paires de chorus voisins (3 pour
  4 chorus). V0 utilisait les chorus ≥ 3 (« stable ») : avec 4 chorus, cela réduit à la paire 3→4, qui est la **retombée**
  (`[[fall]]`) de l'arc, et gonfle les chiffres (ex. `gmd_rock` : comping 99 % contre 77 %). Les entrées de pistes
  du premier chorus des profils trad en sont écartées par les critères d'arc (étendue lue dès le 2ᵉ chorus).
- Les autres définitions (signatures par couche, paires de chorus identiques, séquences distinctes sur 16 graines,
  distance graduée) sont celles de V0 (`references/v0-variance/README.md`).

## Seuils

Départ : les 12 seuils proposés par V0 (16 chorus, `wjazzd_swing` seul) ; ajustés au vu des 64 mesures de ce dossier. Les
valeurs sont les constantes `T` de `v2variance.py`.

| # | Critère | V0 | V2 | Ce qui a changé, et pourquoi |
|---|---|---|---|---|
| H1 | **Habillages distincts sur 16 graines** (D6 : « New seed s'entend ») | — (nouveau) | **≥ 12** ; sous grille, tempo et tonalité imposés : **≥ 8** | Plan V2. 20 des 32 profils donnent 16 / 16 et 9 autres 14 ou 15 ; le seuil (12) laisse 4 habillages communs : seuls `isaac_downpour` (11) et `nt_desert` (8) y échouent. Sous grille, 8 = la moitié des graines |
| H2 | **Grappes de tempo** (± 8 BPM) | — (nouveau) | **≥ 2** (sans objet sous grille : l'hôte impose le tempo) | Plan V2 : « tempo à ± 8 BPM près ». Une plage de 10 BPM (`valse_quebecoise`) ne donne qu'une grappe |
| H3 | **Places (chorus, mesure) où les graines diffèrent** : comping rythme / batterie | — (nouveau) | **≥ 75 % / ≥ 50 %** des places où la couche joue | Plan V2 (« part des mesures dont comping et batterie diffèrent d'une graine à l'autre »). 75 % : V0 `wjazzd_swing` 81 % / grille 75 % ; 50 % : la batterie des profils trad (pieds) |
| 1 | Paires de chorus identiques, accompagnement entier | 0 % | **0 %** | Inchangé. 16 / 16 chorus distincts de V0 devient « aucune paire identique » (4 chorus) |
| 2 | Paires de chorus identiques par couche | ≤ 5 % pour comping rythme, voicings, **basse**, batterie | **≤ 5 %** pour comping rythme, voicings, batterie | La **basse** sort de ce critère : les riffs de basse des profils de style sont des ostinatos (9 des 14 profils GMD rejouent 94 à 98 % de leurs mesures de basse à l'identique d'un chorus au suivant) ; elle est jugée au critère 6, par sa classe |
| 3 | Accords changés d'un chorus au suivant | ≤ 2 % | **≤ 2 %** | Inchangé (D4 : pas de réharmonisation par défaut) ; 0 % partout |
| 4 | Comping rythme changé | ≥ 75 % | **≥ 75 %** | Inchangé (jazz 82-83 %, GMD 77-93 %) |
| 5 | Comping voicings changés | ≥ 65 % | **≥ 65 %** | Inchangé (GMD 82-99 %) |
| 6 | Basse changée | ≥ 80 % | **≥ 80 % pour une basse en marche** (`accompaniment.bass.walking`), **≥ 10 % pour un riff ou un ostinato** | Les 80 % de V0 sont ceux d'une marche de jazz (90-100 % mesuré aujourd'hui). 9 profils GMD à riff changent 2 à 6 % de leurs mesures de basse : le seuil de 10 % (une mesure sur dix, une relance de phrase) **les compte comme sous le seuil** au lieu de l'abaisser jusqu'à les faire passer. La classe est lue dans le profil, jamais dans son nom (D3) |
| 7 | Batterie changée ; distance graduée | ≥ 30 % ; ≥ 10 % | **≥ 30 % ; ≥ 10 %** | Inchangé (GMD 71-100 %, jazz 79-87 %) |
| 8 | Suites de chorus distinctes sur 16 graines : comping rythme, basse, batterie | ≥ 12 / 16 (suites de 16 chorus) | **≥ 12 / 16** (suites de 4 chorus) | Inchangé en valeur ; 4 chorus au lieu de 16 : une suite de 4 est plus facile à partager entre deux graines, mais le seuil n'est manqué que là où la couche **est** identique (trad : 2-3 suites) |
| 9 | Orchestration : programmes de comping / basse / kit sur 16 graines, suites distinctes | ≥ 3 / 2 / 2 ; ≥ 4 | **≥ 3 / 2 / 2 ; ≥ 4** | Inchangé. Lu dans le MIDI (`program_change`) : voir la correction de `midi_programs` plus bas |
| 10 | Arc, densité | cv intra ≥ 10 % **et** étendue ≥ 25 % | **étendue de la trajectoire dès le 2ᵉ chorus ≥ 25 %** | Le cv intra mélange l'arc et l'entrée des pistes du premier chorus : `gigue_acadienne` donnait un cv de 16 % avec une courbe [22, 34, 34, 33] notes par mesure (aucun arc, une piste qui entre). La trajectoire dès le 2ᵉ chorus mesure l'arc sans cette entrée |
| 11 | Arc, vélocité moyenne | cv ≥ 3 % **et** étendue ≥ 8 % | **étendue dès le 2ᵉ chorus ≥ 8 %** | Même raison |
| 12 | Arc, `intensity` du moteur (étendue ≥ 20 %) | proposé | **abandonné** | `MeasureSnapshot` publie l'`intensity` de l'hôte (0,50 constante sur les 64 mesures) : l'arc la multiplie dans `dynamics`, il ne la republie pas. Aucune mesure ne peut la passer ; 10 et 11 lisent l'arc dans ses effets |

Rien n'a été abaissé pour qu'un profil passe : les seuils 2 à 5, 7, 8, 9 sont ceux de V0, le 6 est scindé en deux classes
(chaque profil est jugé à la classe de sa basse), les 10 et 11 sont réécrits pour ne plus compter l'entrée des pistes. Les
profils sous le seuil sont **rapportés**, pas masqués.

### Correction de V0 : `chorusvariety.midi_programs`

La lecture des programmes d'un MIDI triait les `program_change` par (tick, canal, programme) : quand le profil et la
session règlent le même canal au même tick (profil d'abord, session ensuite), **le plus grand numéro gagnait au lieu du
dernier écrit**. `gmd_rock` seed 7 : basse 33 (session) comptée 34 (profil). Le tri est désormais stable sur le tick seul
(`tests/test_v2_variance.py::test_same_tick_program_changes_keep_file_order`). Les chiffres d'orchestration de V0 n'en
dépendent pas (aucun profil de V0 n'avait de session) ; **ceux de R2 et B (« Orchestration : suites distinctes »)
étaient sous-estimés** quand la graine tirait un programme plus petit que celui du profil.

## Résultats

Tenu (✓), non tenu (✗), sans objet (·, couche muette ou critère propre à l'hôte) ; colonne **Tenus** = tenus / applicables.
Valeurs mesurées dans `summary.json` et, plus bas, « Valeurs mesurées ».

### Profils distribués

| Profil | H1 | H2 | H3 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | Tenus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|
| `gigue_acadienne` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | 5 / 14 |
| `gigue_britannique_coloniale` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | · | ✗ | ✓ | ✗ | ✗ | 6 / 13 |
| `gigue_quebecoise` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | 5 / 14 |
| `gmd_afrobeat` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_afrocuban` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 13 / 14 |
| `gmd_blues_shuffle` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_dance_disco` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 14 |
| `gmd_funk` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_hiphop` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_jazz_waltz` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 12 / 14 |
| `gmd_latin_brazilian_baiao` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_latin_brazilian_bossa` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | 13 / 14 |
| `gmd_latin_brazilian_samba` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_neworleans_funk_secondline` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 14 / 14 |
| `gmd_pop` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_reggae` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_rock` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `gmd_soul` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `hornpipe_britannique_coloniale` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | · | ✗ | ✓ | ✗ | ✗ | 6 / 13 |
| `isaac_basement` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 7 / 14 |
| `isaac_burning` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 8 / 14 |
| `isaac_cellar` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 8 / 14 |
| `isaac_downpour` | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 6 / 14 |
| `marche_britannique_coloniale` | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | · | · | · | ✗ | ✗ | ✗ | ✗ | ✗ | 4 / 11 |
| `nt_desert` | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 5 / 14 |
| `reel_acadien` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | 5 / 14 |
| `reel_britannique_coloniale` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | · | ✗ | ✓ | ✗ | ✗ | 6 / 13 |
| `reel_quebecois` | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | 5 / 14 |
| `valse_britannique_coloniale` | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | · | ✗ | ✓ | ✗ | ✗ | 4 / 13 |
| `valse_quebecoise` | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 2 / 14 |
| `wjazzd_ballad` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 14 |
| `wjazzd_swing` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 13 / 14 |

### Sous grille utilisateur (17 profils `loop` d'accompagnement ; trad et jeux : sans objet, raisons plus haut)

| Profil | H1 | H2 | H3 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | Tenus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|
| `gmd_afrobeat.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | 11 / 13 |
| `gmd_afrocuban.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 12 / 13 |
| `gmd_blues_shuffle.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_dance_disco.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 11 / 13 |
| `gmd_funk.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_hiphop.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_jazz_waltz.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 11 / 13 |
| `gmd_latin_brazilian_baiao.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_latin_brazilian_bossa.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 13 / 13 |
| `gmd_latin_brazilian_samba.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_neworleans_funk_secondline.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_pop.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_reggae.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_rock.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `gmd_soul.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `isaac_basement.grille` | sans objet |  |  |  |  |  |  |  |  |  |  |  |  |  | |
| `isaac_burning.grille` | sans objet |  |  |  |  |  |  |  |  |  |  |  |  |  | |
| `isaac_cellar.grille` | sans objet |  |  |  |  |  |  |  |  |  |  |  |  |  | |
| `isaac_downpour.grille` | sans objet |  |  |  |  |  |  |  |  |  |  |  |  |  | |
| `nt_desert.grille` | sans objet |  |  |  |  |  |  |  |  |  |  |  |  |  | |
| `wjazzd_ballad.grille` | ✓ | · | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 12 / 13 |
| `wjazzd_swing.grille` | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 12 / 13 |

## Profils sous le seuil, et pourquoi

Les 17 profils d'accompagnement (`gmd_*`, `wjazzd_*`) tiennent **12 à 14 critères sur 14** (un seul, `gmd_neworleans_funk_secondline`,
les tient tous ; sous grille, `gmd_latin_brazilian_bossa` 13 / 13) : aucune boucle (critère 1 : 0 % de paires de chorus
identiques), accords stables, comping, voicings et batterie qui changent d'un chorus au suivant, 16 suites distinctes sur 16
graines, arc visible dans la densité. Trois familles de causes expliquent les écarts ; les deux autres familles de profils
(trad, jeux) échouent par construction.

**1. Basse en riff identique d'un chorus au suivant (critère 6) : 9 profils GMD, aussi sous grille.**
`gmd_afrobeat`, `gmd_blues_shuffle`, `gmd_dance_disco`, `gmd_funk`, `gmd_hiphop`, `gmd_pop`, `gmd_reggae`, `gmd_rock`,
`gmd_soul` : 2 à 6 % des mesures de basse changent d'un chorus au suivant (seuil 10 %), 21 à 53 % des paires de chorus ont une basse
exactement identique (`gmd_hiphop` 53 %, `gmd_rock` 50 %, cinq profils 46 %, `gmd_blues_shuffle` 37 %, `gmd_funk` 21 %). Les riffs sont des motifs écrits, choisis à la partie ;
l'arc ne restreint pas les motifs de basse (il ne règle que `bass_feel`), et les options d'A4 ne s'appliquent pas aux riffs :
c'est le manque cité par R2-styles et repris par A7 (« 3 % de mesures de basse changent d'un chorus au suivant »).
La graine, elle, change la basse (16 suites distinctes sur 16 graines, programmes de basse ≥ 2) : **entre graines oui,
d'un chorus à l'autre non**. Les profils à basse en marche (`wjazzd_*`, `gmd_jazz_waltz`) changent 90 à 100 % de leurs
mesures ; les latins et New Orleans (basse en riff avec plusieurs motifs) 20 à 76 %.

**2. Batterie qui rejoue un chorus à l'identique (critère 2) : `wjazzd_ballad` 29 %, `gmd_jazz_waltz` 21 %,
`gmd_latin_brazilian_samba` 17 %, `gmd_dance_disco` 15 %, `gmd_latin_brazilian_baiao` 5,2 % (0,2 point au-dessus du seuil),
`gmd_neworleans_funk_secondline` 8 % sous grille de 8 mesures.** Cause probable **[INFERENCE : non isolée par un export de contrôle]** : les chorus 2 à 4 partagent la dernière
étape de l'arc (`repeat_from = 1`) et la batterie y est tirée par étiquette. Le critère est plus dur que la musique (deux
chorus de solo qui partagent une même batterie sont normaux) ; il est tenu par les 12 autres profils.

**3. Arc de vélocité ou de densité sous le seuil (critères 10 et 11) :**
`wjazzd_swing` 3,3 %, `gmd_jazz_waltz` 1,1 %, `gmd_afrocuban` 7,3 % (seuil 8 %) : les arcs de jazz et d'afro-cubain
agissent sur la densité (étendue 49 à 82 %) et le feel, pas sur la vélocité. `gmd_latin_brazilian_bossa` : densité 24,85 %
(seuil 25 %), au point près ; sous grille de 16 mesures le même profil tient tout (13 / 13). `gmd_afrobeat` sous grille : vélocité
6,7 % (le profil seul la tient à 11 %).

**Profils trad (10 : `reel_*`, `gigue_*`, `hornpipe_*`, `marche_*`, `valse_*`) : 2 à 6 critères tenus sur 11 à 14.** L'habillage
est là (H1 : 16 / 16 pour 8 d'entre eux, 15 / 16 pour `reel_acadien` et `reel_quebecois`, tempo sur 1 à 4 grappes ; kit unique
pour les profils québécois et acadiens : une seule banque de percussion), la variance par chorus **non** : R2-trad a posé `[session]` (tempo, tonalité, instrument de mélodie, comping,
basse, voicings, énergie, arcs sur les tours qui règlent l'intensité et la vélocité de la mélodie) sans comping de phrases,
sans phrases ni relances de batterie (A1) et sans `[arc]`. Mesuré : comping rythme et voicings changent 4 à 11 % des mesures
d'un chorus au suivant (51 à 78 % de paires de chorus identiques pour le comping), batterie de pieds 15 à 25 % (absente de
`gigue_britannique_coloniale`, `hornpipe`, `reel_britannique_coloniale`, `valse_britannique_coloniale`), densité plate dès le 2ᵉ chorus (étendue 0 à 8 %), vélocité
2 à 7 %. **`marche_britannique_coloniale`** (`harmony.model = "none"`, caisse seule, pas de comping ni de basse) et les deux
valses boucle **l'accompagnement entier** (critère 1) : 83 % de paires identiques pour la marche, 54 % pour
`valse_britannique_coloniale`, 31 % pour `valse_quebecoise` (basse 7 à 8 % de mesures changées). `valse_quebecoise` est le
profil le plus bas (2 / 14) : plage de tempo de 10 BPM (140-150 : une seule grappe, critère H2), kit unique, comping à 57 % et batterie à 65 % de paires
identiques. Les trad sont des **airs de danse** : répéter l'accompagnement d'un tour au suivant
est la tradition même, et les profils n'ont aucune grille utilisateur ; la décision est celle du propriétaire (D2 : « tous les styles
d'iReal », donc pas ces profils pour training ; leur variance entre graines, elle, est prouvée).

**Profils de jeu (5 : `isaac_*`, `nt_desert`) : 5 à 8 critères tenus sur 14.** Habillage correct (H1 : 14 / 16 pour `isaac_burning` et
`isaac_cellar`, 12 pour `isaac_basement`, 11 pour `isaac_downpour` sous le seuil de 12, **8 pour `nt_desert`**), mais **comping, basse et
accords-nappes identiques d'un chorus à l'autre** (basse 0 % de mesures changées ; comping : 100 % de paires de chorus identiques pour
`isaac_burning`, `isaac_cellar` et `isaac_downpour`, 40 % pour `isaac_basement`, 31 % pour `nt_desert`), densité plate (`isaac_cellar` : 16,8 / 16,7 / 16,7 / 16,6 notes par mesure, étendue 1 %) : seules la batterie (40 à
69 % de mesures changées, par phrases et relances) et la mélodie bougent. C'est le constat de R2-jeux (« arc sans choix de motifs ou
gabarits de basse ni de boucles ») : l'arc des jeux règle l'intensité et les tags de batterie, rien qui change les
notes du comping ou de la basse. `isaac_downpour` n'a qu'un tour par air (`tours_per_tune = 1`, 11 habillages) et `nt_desert` n'a ni groupe de kit ni
groupe de comping (2 programmes de comping, 2 de basse, 1 de kit sur 16 graines). Ces profils ne sont pas candidats à training (D1, D2) : la mesure
dit où le moteur ne varie pas, elle ne demande pas de les corriger ici.

## Distance au corpus

Aucun profil ne perd de distance par rapport à `main` : **aucun profil n'est modifié par V2**, et les distances rejouées
ici avec le binaire de ce worktree **retrouvent à l'identique** les chiffres des comptes rendus (R2-trad, R2-styles B8,
B3, B5, B6) ; c'est la preuve que la variance mesurée plus haut et la distance au corpus décrivent le même état du moteur.

**Profils trad** (`make v2-distance-trad`, `harmonium-lab trad-compare`, 16 graines × 32 mesures, écart moyen |z| des écarts signalés, **plus petit = plus proche**, bruit de tirage ± 0,07 ; `hornpipe_britannique_coloniale` : aucun air de hornpipe dans le corpus, non mesuré) :

| Profil | Référence du labo | |z| (corpus de la tradition) | |z| (corpus québécois par défaut, comme R2-trad) | R2-trad « après » |
|---|---|---:|---:|---:|
| `reel_quebecois` | `trad-reel` | 0.430 | 0.430 | 0.430 |
| `reel_acadien` | `trad-acadienne-reel` | 0.764 | 0.672 | 0.672 |
| `reel_britannique_coloniale` | `trad-britannique_coloniale-reel` | 0.446 | 0.845 | 0.845 |
| `gigue_quebecoise` | `trad-jig` | 0.587 | 0.587 | 0.587 |
| `gigue_acadienne` | `trad-acadienne-jig` | 0.782 | 0.700 | 0.700 |
| `gigue_britannique_coloniale` | `trad-britannique_coloniale-jig` | 0.596 | 0.650 | 0.650 |
| `marche_britannique_coloniale` | `trad-britannique_coloniale-march` | 0.908 | 1.012 | 1.012 |
| `valse_quebecoise` | `trad-waltz` | 0.632 | 0.632 | 0.632 |
| `valse_britannique_coloniale` | `trad-britannique_coloniale-waltz` | 1.002 | 0.721 | 0.721 |

La colonne « corpus québécois » retrouve **les neuf valeurs de R2-trad** : R2-trad comparait les profils acadiens et britanniques aux airs réels du corpus québécois (`trad-compare` charge `corpus/trad` par défaut). La colonne « corpus de la tradition » est la comparaison cohérente : acadien +0,09 (reel), +0,08 (gigue), britannique −0,40 (reel), −0,05 (gigue), −0,10 (marche), **+0,28 (valse britannique, 1,002)** ; la valse britannique est le profil trad le plus loin de son corpus (60 airs réels, un accord par mesure là où 32 % des mesures chiffrées en portent deux : R1 § Mesures).

**Batterie des profils d'accompagnement contre le GMD** (`make v2-distance-batterie` : scripts `b8/distance_gmd.py`, `b6/distance_gmd.py`, `b25_distance.py`, `b3/*_distance.py` du moteur, 16 graines × 48 mesures ; Bray-Curtis des fréquences d'attaque par pas, moyenne de tout / grosse caisse / caisse claire / charleston, **0 = identique, plus petit = plus proche**) :

| Profil | Script | Profil distribué | Copie sans arc ni session (ou témoin B2/B5) | Copie non calibrée |
|---|---|---:|---:|---:|
| `gmd_rock` | `b8/distance_gmd.py` | 0.184 | 0.236 | 0.500 |
| `gmd_pop` | `b8/distance_gmd.py` | 0.171 | 0.170 | 0.479 |
| `gmd_hiphop` | `b8/distance_gmd.py` | 0.147 | 0.156 | 0.543 |
| `gmd_soul` | `b8/distance_gmd.py` | 0.252 | 0.247 | 0.525 |
| `gmd_reggae` | `b8/distance_gmd.py` | 0.179 | 0.186 | 0.595 |
| `gmd_dance_disco` | `b8/distance_gmd.py` | 0.163 | 0.111 | 0.643 |
| `gmd_afrobeat` | `b8/distance_gmd.py` | 0.152 | 0.114 | 0.548 |
| `gmd_blues_shuffle` | `b6/distance_gmd.py` | 0.090 | 0.097 | 0.666 |
| `wjazzd_ballad` | `b25_distance.py` | 0.510 | 0.346 (témoin) | — |
| `gmd_jazz_waltz` | `b25_distance.py` | 0.380 | 0.542 (témoin) | — |
| `gmd_latin_brazilian_bossa` | `b3/gmd_latin_brazilian_bossa_distance.py` | 0.203 | 0.194 | 0.490 |
| `gmd_latin_brazilian_samba` | `b3/gmd_latin_brazilian_samba_distance.py` | 0.354 | 0.367 | 0.735 |
| `gmd_latin_brazilian_baiao` | `b3/gmd_latin_brazilian_baiao_distance.py` | 0.157 | 0.074 | 0.661 |
| `gmd_afrocuban` | `b3/gmd_afrocuban_distance.py` | 0.301 | 0.300 | 0.559 |

Les quatorze valeurs « profil distribué » sont **identiques à celles des comptes rendus** (B8 : 0,184 / 0,171 / 0,147 / 0,252 / 0,179 / 0,163 / 0,152 ; B6 0,090 ; B2 + B5 0,510 et 0,380 ; B3 0,203, 0,354, 0,157, 0,301). Seul le **témoin** de `wjazzd_ballad` diffère du compte rendu B2 (0,346 contre 0,651) : c'est le `percussion.toml` de `wjazzd_swing`, que B1 a réécrit (patterns et relances du GMD jazz) après B2, le jour même ; la valeur du témoin n'est pas stable, celle du profil l'est. Le témoin de la valse est celui de la fixture d'exercice (0,542, identique).

**Reprises des comptes rendus, non rejouées** (profil inchangé depuis, `git log` ; les outils demandent l'audio ou une
copie dédiée du profil) : jeux (`make style-distance`, R2-jeux § 4, 10 graines × 48 mesures, score 0-100 plus grand = plus
proche : `isaac_cellar` audio 50,9 / basse 78,4 / batterie 84,7 / accords 67,3 ; `isaac_basement` 40,4 et 37,6 / 74,9 /
58,6 / 78,4 (*Diptera Sonata*) ; `isaac_burning` 37,4 / 67,8 / 82,8 / 61,1 ; `isaac_downpour` 56,7 / 78,9 / 62,6 / 86,4 ;
`nt_desert` *Fläshyn* 58,5 / 86,1 / 63,0 / 82,2), `gmd_funk` et `gmd_neworleans_funk_secondline` (`make style-distance` sur le corpus
GMD, R2-styles : groupe batterie 76,6 et 72,7), `wjazzd_swing` (basse contre WJazzD 0,158 ; mélodie contre le corpus 0,323 :
B1, E12). Sans corpus de référence : `wjazzd_ballad` et `gmd_jazz_waltz` pour la basse (aucune mesure 3/4 dans WJazzD, aucune
basse de ballade lisible), `gmd_hiphop` et `gmd_afrobeat` pour la basse et le comping, tous les profils pour le comping (pas de
corpus de comping).

## Limites

- **4 chorus** : l'arc des profils de style (3 étapes sur 4 chorus + retombée) est vu en entier, mais un arc plus long
  (`tours_per_tune` 5 de `gmd_funk`, `gmd_blues_shuffle`) n'est mesuré que sur ses quatre premiers chorus ; les critères d'arc
  lisent la courbe moyenne des 16 graines (4 points), pas une distribution.
- **Les chorus de 8 mesures sous grille** ne portent pas les breaks de l'arc dont le `start` dépasse 8 ; les profils concernés
  sont mesurés sur 16 ou 24 mesures (colonne « grille » de `summary.json`) : leur variance par chorus n'est pas comparable au
  point près à celle d'une grille de 8.
- **Habillage lu dans le premier snapshot** : l'orchestration qui change **par chorus** (arc `orchestre`) n'entre que dans le
  critère 9 (MIDI), pas dans H1.
- La variance ne dit rien de la musique (V0) : **l'écoute reste le juge** (D5, facultative).
- Rendu audio, SoundFont de training (GeneralUser GS) et profils Odin : non exercés (D1 : Odin hors training).
