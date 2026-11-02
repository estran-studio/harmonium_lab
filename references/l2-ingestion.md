# L2 — Ingestion complète du GMD, sous-ensembles WJazzD, swing JTD par tempo (phase 019, vague 1)

Date : 2026-11-02. Branche `wquintal/l2-ingestion-styles` (partie de `main` du labo, `197d9fa`). Le dépôt moteur n'est pas
modifié. Aucun fichier sous droits ni base brute dans le diff : bruts en cache gitignoré (`corpus/{gmd,wjazzd,jtd}/raw/`),
versionnés seulement les manifestes (champ `licence`), les `VERSION` et les JSON agrégés. **Aucune phrase de solo** ni mesure
d'un enregistrement n'est copiée : comptes, parts, probabilités par pas, centiles, intervalles de confiance.

## 1. Sources et empreintes

SHA256 vérifié par le code avant toute lecture (`corpus_cache.open_verified`, `wjazzd.verify`) ; identiques à `corpus/sources-jazz.md`.

| Source | Version, SHA256 | Licence | Mention portée par chaque `references/*` |
|---|---|---|---|
| Groove MIDI Dataset | v1.0.0 midi-only, `651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e` | CC BY 4.0 | Gillick, Roberts, Engel, Eck, Bamman, ICML 2019 ; Google LLC |
| Weimar Jazz Database | v2.1 (base 2.2), `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` | ODbL 1.0 + DbCL 1.0 | ODbL §4.3 (« Contains information from the Weimar Jazz Database… ») |
| Jazz Trio Database | v0.2, `42c3df0700e0cd6e73231b9ed111283600750305e2e9cf451f80664d1ec90025` (MD5 `43f543fb…`) | MIT | Cheston, Schlichting, Cross, Harrison, TISMIR 2024 |

Aucune source NC ou SA n'est lue.

## 2. Ce qui est livré

| Module (`src/harmonium_lab/backing/`) | Sortie | Commande |
|---|---|---|
| `gmd_styles.py` (+ `drums.py` : manifeste complet) | `corpus/gmd/manifest.jsonl` (1 150 fichiers, champs `family`, `group` E7, `licence`), `references/gmd-<famille>/` (18) et `references/gmd-<famille>-<style>/` (18 styles secondaires), `references/gmd-inventory.json` | `make backing-gmd` |
| `wjazzd_subsets.py` (+ `wjazzd.py` : champ `l2_subset`) | `references/wjazzd-{ballad,twobeat,latin,funk}/` ; `corpus/wjazzd/manifest.jsonl` | `make backing-wjazzd` |
| `swing_tempo.py` | `references/jtd-swing-tempo/` (swing, micro-timing, courbe, `a6_table`) | `make backing-jtd-tempo` |

`make backing-l2` enchaîne les trois. Chaque dossier a son `README.md` (provenance, licence et mention, commande, effectifs, limites) et son
JSON ; deux exécutions donnent des fichiers identiques (clés triées, arrondis fixes, bootstrap à graine fixe). `make backing-measures` (E7)
régénère `references/wjazzd-swing/` à l'identique (vérifié : `measures-drums.json` et `measures-timing.json` identiques octet pour octet).
`drums.write_manifest` écrit désormais le manifeste COMPLET du GMD (E7 n'écrivait que les 156 fichiers jazz / New Orleans / blues-shuffle) ;
le champ `group` marque toujours le sous-ensemble E7 (`null` hors sous-ensemble).

## 3. Méthode

### GMD (batterie, tous les styles)

- **Périmètre** : 1 150 fichiers, 18 familles, 76 styles, 815 minutes. `beat` et `fill` séparés. Métriques : 4/4 (1 138), 3/4 (5), 6/8 (5) mesurées ;
  un 5/4 et un 5/8 sont listés et refusés (un seul fichier, `rejects` dans le JSON).
- **Rôles** : 8 rôles d'E7 → 12 : `kick`, `snare`, `sidestick` (cross-stick 37), `hat_closed`, `hat_pedal`, `hat_open`, `ride`, `ride_bell` (53), `crash`,
  `tom_high` (48, 50), `tom_mid` (45, 47), `tom_low` (43, 58). Table Roland TD-11 → rôle → note GM : `references/gmd-*/measures-drums.json`, clé
  `role_table` (page officielle du GMD, section « Drum Mapping », consultée le 2026-11-01). **Le GMD ne contient aucune percussion latine** : le TD-11 n'a
  que des pads de kit ; les styles latins sont joués au kit avec cross-stick, cloche de ride et toms. `role_table.latin_stand_in` note des équivalents
  GM possibles pour un rendu (claves 75, cowbell 56, congas 62–64) : hypothèses d'écoute, jamais mesurées.
- **Grille selon le feel** (par fichier, `gmd_styles.classify_feel`), au lieu de la grille unique swinguée d'E7 :
  `straight` 16 pas en 4/4 (doubles croches) ; `swing` même grille, pas 2 retardé au rapport mesuré (0,56 ≤ r < 0,62) ; `ternary` triolets, 12 pas en 4/4
  (shuffle, 12/8, swing appuyé r ≥ 0,62). 3/4 : 12 pas (droit) ou 9 (ternaire) ; 6/8 : 12 pas droits. Le feel vient des contretemps du ride et du charleston :
  fractions de pulsation près de 1/4 et 3/4 (doubles croches droites) contre rapport médian dans [0,45 ; 0,73] ; à défaut, des autres rôles sauf la grosse caisse ;
  sans preuve, `straight`. Un test attrape le piège du charleston en doubles croches (les attaques à 0,75 tireraient le rapport vers un swing). Un `fill` sans
  contretemps hérite du feel des `beat` de son style. Un style a un groupe par (métrique, feel) : `4-4:straight`, `4-4:ternary`… (le style `rock` : 154 fichiers 4/4 droits,
  19 ternaires, 7 swing, 5 en 6/8, 1 en 3/4).
- **Par groupe** : probabilités par pas et par rôle, vélocités (absolue, relative à la médiane du rôle), **micro-timing par rôle** (écart à la grille, en pas
  et en ms au tempo du fichier, sur la pulsation et hors pulsation), fidélité de la grille (`grid_fit`), densités, rôle du timekeeper et figure (`quarters`,
  `eighths`, `sixteenths`, `spang`…), patterns de mesure vus dans ≥ 2 fichiers par rôle et kick+snare, **patterns proposés** de densité 0, 1, 2 mappables
  sur `[[patterns]]` (probabilités par pas ≥ seuil, jamais une mesure copiée ; éligibilité d'E7 : ≥ 20 mesures, ≥ 3 fichiers, aucun fichier > 60 %),
  **fills** (relance de densité 2 et position : pas et temps de la première et de la dernière attaque, durée en temps, mesures touchées).
- **Dossiers** : un par famille (`gmd-rock`…) avec ses styles de base et petits styles ; un style secondaire a son propre dossier s'il est nommé par le brief
  (samba, bossa, shuffles, bembé, second line, jazz/swing) ou assez fourni (≥ 3 fichiers `beat` et ≥ 150 mesures, ou ≥ 2 fichiers et ≥ 300 mesures).

### WJazzD (basse de `BALLAD`, `TWOBEAT`, `LATIN`, `FUNK`)

Mêmes mesures qu'E7 (arrivées, approche du 4ᵉ temps, passage, intervalles, registre, rythme harmonique, tempos, formes), mêmes structures (`bass_measures`).
Ajouts : métriques (signature par solo), **rythme de la basse au temps** (motif d'égalités de hauteur entre temps consécutifs : `quarters`, `halves`,
`whole`… ; longueur des notes tenues), **intervalle de confiance à 95 % par bootstrap par solo** (2 000 rééchantillons, graine fixe), effectifs par classe de tempo.
`bass_pitch` n'existe qu'au temps : **les croches ne sont pas observables**, et une hauteur répétée est une noire rejouée ou une note tenue (indiscernable).
Les valeurs de `rhythmfeel` composées (`LATIN/FUNK` 3, `LATIN/SWING` 1, `FUNK/SWING` 1, `A:LATIN/B:SWING` 1) sont hors sous-ensembles.

### JTD (swing et micro-timing par tempo)

Quatre classes (< 120, 120–180, 180–240, ≥ 240 BPM), chacune ≥ 30 pistes mesurées ; **toute l'archive est entre 102 et 299 BPM** (« < 120 » = 100–120 BPM, « ≥ 240 » =
240–300 BPM ; aucune valeur hors de cette plage). Par classe et instrument : swing (médiane par piste, puis médiane et IC à 95 % **par musicien**, les pistes d'un
même musicien se ressemblant), dispersion, effectifs de musiciens distincts ; micro-timing relatif basse/piano − batterie en pas et en ms ; courbe continue
(régression robuste de Huber, validation croisée par blocs de musiciens) et table `a6_table` pour A6.

## 4. Tableaux style → source → effectif → métriques → fiabilité → tâche B

### 4.1 Seuils de fiabilité (écrits dans le code et les JSON)

| Source | `assez` | `juste` | `trop peu` |
|---|---|---|---|
| GMD `beat` (`gmd_styles.RELIABILITY`) | ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures | ≥ 3 fichiers, ≥ 60 mesures | en dessous |
| GMD `fill` | ≥ 30 fichiers, ≥ 3 batteurs, ≥ 30 mesures | ≥ 10 fichiers, ≥ 10 mesures | en dessous |
| WJazzD (`wjazzd_subsets`) | ≥ 20 solos avec mesures valides et ≥ 1 500 mesures valides | ≥ 8 solos et ≥ 500 mesures | en dessous |
| JTD (`swing_tempo`) | ≥ 60 pistes mesurées, ≥ 8 musiciens, aucun musicien > 25 % des pistes, demi-largeur de l'IC par musicien ≤ 0,02 | ≥ 30 pistes et ≥ 5 musiciens | en dessous |

Justification : un `beat` du GMD dure environ une minute (30 à 40 mesures) ; huit fichiers de trois batteurs donnent 200 mesures qui ne tiennent pas à un seul
idiome ; trois fichiers suffisent pour proposer un pattern (seuil d'E7) mais pas pour parler d'un style. Un `fill` est une mesure : trente en font un répertoire.
WJazzD : avec un écart-type d'environ 0,2 entre solos sur une part, la demi-largeur de l'IC vaut ≈ ±0,09 pour 20 solos, ±0,14 pour 8, ±0,20 pour 4.
Les dix batteurs du GMD sont la limite de tout style : un style à un batteur décrit un batteur.

### 4.2 GMD (CC BY 4.0), batterie, par style

Colonnes `beat` et `fill` : fichiers / mesures entières / minutes de fichiers. Mesures de chaque groupe : probabilités par pas et par rôle, vélocités,
micro-timing par rôle, figures du timekeeper, patterns par rôle, patterns proposés, position des fills. `Fiabilité` : verdict `beat` (puis `fills` si présents).
Tâche B : B1, B2, B5 jazz ; B3 latin et afro-cubain ; B4 funk ; B6 shuffles et 12/8 ; B7 New Orleans ; B8 le reste.

| Style | beat | fill | Métrique (fichiers) | Feel (fichiers) | Fiabilité | Tâche B |
|---|---|---|---|---|---|---|
| afrobeat | 13 / 982 / 40.0 | — | 4-4 13 | straight 13 | juste | B8 |
| afrocuban | 3 / 276 / 9.7 | 6 / 6 / 0.2 | 4-4 9 | straight 2, ternary 7 | juste ; fills trop peu | B3 |
| afrocuban/bembe | 1 / 104 / 3.4 | 29 / 29 / 0.9 | 4-4 30 | ternary 29, straight 1 | trop peu ; fills juste | B3 |
| afrocuban/calypso | 2 / 287 / 9.9 | — | 4-4 2 | straight 2 | trop peu | B3 |
| afrocuban/rhumba | 1 / 103 / 3.8 | 18 / 18 / 0.6 | 4-4 19 | straight 19 | trop peu ; fills juste | B3 |
| blues/shuffle | 4 / 90 / 4.8 | — | 4-4 4 | straight 1, swing 1, ternary 2 | juste | B6 |
| country | 2 / 120 / 5.0 | 27 / 30 / 1.1 | 4-4 29 | straight 29 | trop peu ; fills juste | B8 |
| dance/breakbeat | 2 / 115 / 2.7 | — | 4-4 2 | straight 2 | trop peu | B8 |
| dance/disco | 5 / 431 / 13.7 | — | 4-4 5 | straight 5 | juste | B8 |
| funk | 36 / 1904 / 80.2 | 41 / 52 / 1.9 | 4-4 77 | straight 74, ternary 2, swing 1 | assez ; fills juste | B4 |
| funk/fast | 1 / 70 / 2.3 | 18 / 18 / 0.5 | 4-4 19 | straight 19 | trop peu ; fills juste | B4 |
| funk/groove1 | 4 / 64 / 1.9 | — | 4-4 4 | straight 4 | juste | B4 |
| funk/groove2 | 4 / 63 / 2.4 | — | 4-4 4 | straight 4 | juste | B4 |
| funk/groove5 | 4 / 64 / 3.0 | — | 4-4 4 | straight 4 | juste | B4 |
| funk/latin | 2 / 132 / 5.3 | — | 4-4 2 | straight 2 | trop peu | B4 |
| funk/purdieshuffle | 1 / 104 / 3.2 | 29 / 35 / 1.0 | 4-4 30 | ternary 27, straight 3 | trop peu ; fills juste | B6 |
| funk/rock | 1 / 44 / 2.0 | 19 / 19 / 0.8 | 4-4 20 | straight 20 | trop peu ; fills juste | B4 |
| gospel | 1 / 68 / 2.3 | 18 / 18 / 0.6 | 4-4 19 | straight 19 | trop peu ; fills juste | B8 |
| highlife | 2 / 143 / 4.6 | — | 4-4 2 | straight 2 | trop peu | B8 |
| hiphop | 30 / 796 / 36.8 | 61 / 83 / 4.0 | 4-4 91 | straight 80, swing 10, ternary 1 | assez ; fills juste | B8 |
| hiphop/groove6 | 4 / 64 / 2.9 | — | 4-4 4 | straight 4 | juste | B8 |
| jazz | 24 / 748 / 23.1 | 22 / 22 / 0.6 | 3-4 2, 4-4 44 | straight 34, swing 3, ternary 9 | assez ; fills juste | B1, B2, B5 |
| jazz/fast | 1 / 126 / 1.8 | — | 4-4 1 | straight 1 | trop peu | B1, B2, B5 |
| jazz/funk | 2 / 107 / 3.8 | 22 / 28 / 0.9 | 4-4 24 | straight 22, ternary 2 | trop peu ; fills juste | B1, B2, B5 |
| jazz/fusion | 4 / 62 / 2.7 | 7 / 12 / 0.5 | 4-4 11 | straight 10, ternary 1 | juste ; fills trop peu | B1, B2, B5 |
| jazz/klezmer | 1 / 23 / 0.6 | — | 4-4 1 | straight 1 | trop peu | B1, B2, B5 |
| jazz/linear | 2 / 334 / 8.6 | — | 4-4 2 | swing 1, ternary 1 | trop peu | B1, B2, B5 |
| jazz/march | 3 / 236 / 7.8 | — | 4-4 3 | straight 3 | juste | B1, B2, B5 |
| jazz/mediumfast | 2 / 115 / 2.6 | — | 4-4 2 | swing 1, ternary 1 | trop peu | B1, B2, B5 |
| jazz/swing | 11 / 698 / 17.6 | — | 4-4 11 | straight 3, swing 6, ternary 2 | juste | B1, B2, B5 |
| latin | 8 / 572 / 22.0 | — | 4-4 8 | straight 6, ternary 2 | juste | B3 |
| latin/ando | 1 / 111 / 2.7 | — | 3-4 1 | straight 1 | trop peu | B3 |
| latin/bomba | 1 / 89 / 3.7 | — | 4-4 1 | straight 1 | trop peu | B3 |
| latin/bounce | 2 / 132 / 5.0 | — | 4-4 2 | straight 2 | trop peu | B3 |
| latin/brazilian | 4 / 106 / 3.8 | — | 4-4 4 | straight 3, ternary 1 | juste | B3 |
| latin/brazilian-baiao | 3 / 200 / 7.9 | 29 / 29 / 1.1 | 4-4 32 | straight 32 | juste ; fills juste | B3 |
| latin/brazilian-bossa | 2 / 631 / 19.9 | — | 4-4 2 | straight 2 | trop peu | B3 |
| latin/brazilian-frevo | 1 / 79 / 2.4 | — | 4-4 1 | straight 1 | trop peu | B3 |
| latin/brazilian-ijexa | 3 / 85 / 3.2 | — | 4-4 3 | straight 3 | juste | B3 |
| latin/brazilian-maracatu | 2 / 182 / 7.6 | — | 4-4 2 | straight 1, ternary 1 | trop peu | B3 |
| latin/brazilian-samba | 5 / 322 / 14.0 | — | 4-4 5 | straight 5 | juste | B3 |
| latin/brazilian-sambareggae | 3 / 180 / 7.6 | — | 4-4 3 | straight 3 | juste | B3 |
| latin/brazilian-songo | 5 / 446 / 15.4 | — | 4-4 5 | straight 5 | juste | B3 |
| latin/chacarera | 3 / 241 / 6.4 | — | 3-4 1, 4-4 2 | straight 1, ternary 2 | juste | B3 |
| latin/dominican-merengue | 1 / 166 / 5.1 | — | 4-4 1 | straight 1 | trop peu | B3 |
| latin/merengue | 1 / 12 / 0.3 | — | 4-4 1 | straight 1 | trop peu | B3 |
| latin/reggaeton | 1 / 32 / 1.5 | — | 4-4 1 | straight 1 | trop peu | B3 |
| latin/samba | 2 / 136 / 4.7 | 17 / 13 / 0.5 | 4-4 19 | straight 18, swing 1 | trop peu ; fills juste | B3 |
| latin/venezuelan-joropo | 1 / 41 / 2.1 | — | 4-4 1 | swing 1 | trop peu | B3 |
| latin/venezuelan-merengue | 1 / 0 / 2.8 | — | 5-8 1 | — | trop peu | B3 |
| latin/venezuelan-sangueo | 1 / 34 / 1.3 | — | 4-4 1 | straight 1 | trop peu | B3 |
| middleeastern | 1 / 118 / 3.8 | — | 4-4 1 | straight 1 | trop peu | B8 |
| neworleans/chacha | 1 / 59 / 1.9 | — | 4-4 1 | straight 1 | trop peu | B7 |
| neworleans/funk | 8 / 396 / 17.9 | 40 / 59 / 2.5 | 4-4 48 | straight 48 | assez ; fills juste | B7 |
| neworleans/secondline | 3 / 212 / 8.4 | — | 4-4 3 | straight 3 | juste | B7 |
| neworleans/shuffle | 1 / 56 / 2.2 | — | 4-4 1 | straight 1 | trop peu | B6 |
| pop | 8 / 174 / 5.2 | 2 / 9 / 0.3 | 4-4 10 | straight 8, ternary 1, swing 1 | juste ; fills trop peu | B8 |
| pop/groove7 | 4 / 64 / 1.8 | — | 4-4 4 | straight 4 | juste | B8 |
| pop/soft | 3 / 72 / 3.6 | 10 / 12 / 0.6 | 4-4 13 | straight 13 | juste ; fills juste | B8 |
| punk | 7 / 275 / 8.1 | 51 / 51 / 1.4 | 4-4 58 | straight 54, ternary 4 | juste ; fills juste | B8 |
| reggae | 3 / 253 / 8.5 | 16 / 16 / 0.7 | 4-4 19 | straight 18, ternary 1 | juste ; fills juste | B8 |
| reggae/slow | 1 / 29 / 1.9 | — | 4-4 1 | straight 1 | trop peu | B8 |
| rock | 193 / 5367 / 204.6 | 88 / 134 / 5.3 | 3-4 1, 4-4 275, 6-8 5 | straight 251, swing 8, ternary 22 | assez ; fills assez | B8 |
| rock/folk | 1 / 100 / 4.5 | — | 4-4 1 | straight 1 | trop peu | B8 |
| rock/groove8 | 4 / 60 / 3.9 | — | 4-4 4 | straight 4 | juste | B8 |
| rock/halftime | 1 / 125 / 3.6 | 36 / 41 / 1.2 | 4-4 37 | straight 37 | trop peu ; fills juste | B8 |
| rock/indie | 4 / 174 / 8.1 | 6 / 5 / 0.3 | 4-4 10 | straight 10 | juste ; fills trop peu | B8 |
| rock/prog | 3 / 226 / 8.8 | — | 4-4 2, 5-4 1 | straight 1, ternary 1 | trop peu | B8 |
| rock/rockabilly | 1 / 260 / 5.2 | — | 4-4 1 | ternary 1 | trop peu | B8 |
| rock/shuffle | 4 / 296 / 11.1 | — | 4-4 4 | straight 1, swing 1, ternary 2 | juste | B6 |
| soul | 8 / 221 / 8.9 | 23 / 28 / 1.1 | 4-4 31 | straight 31 | juste ; fills juste | B8 |
| soul/groove10 | 4 / 64 / 2.5 | — | 4-4 4 | straight 4 | juste | B8 |
| soul/groove3 | 4 / 64 / 3.0 | — | 4-4 4 | straight 4 | juste | B8 |
| soul/groove4 | 4 / 64 / 3.2 | — | 4-4 4 | straight 4 | juste | B8 |
| soul/groove9 | 4 / 64 / 2.4 | — | 4-4 4 | straight 4 | juste | B8 |
| soul/motown | 4 / 136 / 4.4 | 12 / 23 / 0.7 | 4-4 16 | straight 15, swing 1 | juste ; fills juste | B8 |
Total : 1 150 fichiers (12 couples style-type ont quelques fichiers sans mesure entière : colonne `n_files_with_measures` de `gmd-inventory.json`), 21 989 mesures entières (`beat` et `fill`), 815 minutes de fichiers. Familles les plus fournies : rock 341 fichiers (6 788 mesures), funk 160, jazz 101,
latin 97, hiphop 95, soul 63, afrocuban 60, punk 58, neworleans 53.

**Lecture rapide.** Fiabilité `assez` en `beat` : rock (4/4 droit et ternaire), funk, hiphop, jazz, neworleans/funk. Les styles que le plan 019 cible
spécifiquement sont maigres : `blues/shuffle` 4 fichiers (90 mesures, trop peu en séparant les feels), `neworleans/secondline` 3 fichiers (212 mesures, juste),
`latin/brazilian-bossa` 2 fichiers d'un seul batteur (631 mesures, 20 minutes : beaucoup de mesures, un seul idiome, trop peu), `latin/samba` 2 fichiers
(trop peu) à côté de `latin/brazilian-samba` 5 fichiers (juste), `afrocuban/bembe` 1 fichier et 29 fills (ternaire, trop peu en `beat`).

### 4.3 WJazzD (ODbL), basse, par sous-ensemble

Solos avec mesures valides (4/4, quatre `bass_pitch`, accord connu) ; IC à 95 % par bootstrap sur les solos. Référence swing (E7, 361 solos) : arrivée sur la basse de
l'accord 41 %, répétitions 20 %, passage sur une note d'accord 48 %.

| Sous-ensemble | Solos (avec mesures) | Mesures valides | Minutes | Chorus | Tempo (p50 ; min–max) | Arrivée sur la basse au changement | Répétitions de hauteur | Mesures `quarters` / `halves` | Mesures à un accord | Fiabilité | Tâche B |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `BALLAD` | 10 (9) | 294 | 20,1 | 12 | 57,9 ; 48,8–67,7 | 55 % [42–70] | 24 % [18–35] | 44 % / 11 % | 61 % [33–83] | **trop peu** (294 < 500 mesures) | B2 |
| `TWOBEAT` | 32 (30) | 752 | 20,1 | 46 | 183,9 ; 70,6–273,6 | 25 % [18–33] | 37 % [32–43] | 29 % / 10 % | 76 % [66–86] | **juste** | B2 (deux temps) |
| `LATIN` | 27 (23) | 1 639 | 40,0 | 87 | 152,7 ; 60,1–272,7 | 57 % [46–68] | 38 % [32–44] | 28 % / 8 % | 87 % [79–93] | **assez** | B3 |
| `FUNK` | 20 (16) | 928 | 31,3 | 32 | 117,8 ; 84,0–159,4 | 45 % [34–63] | 28 % [24–34] | 38 % / 7 % | 82 % [61–97] | **juste** | B4 |

Par classe de tempo (solos avec mesures / mesures valides) : `BALLAD` seule la classe < 120 est peuplée (48,8–67,7 BPM) ; `TWOBEAT` 3 / 121, 11 / 235, 15 / 364, 1 / 32 (toutes trop peu) ;
`LATIN` 1 / 39, 14 / 887 (**juste**), 7 / 564, 1 / 149 ; `FUNK` 10 / 623 (**juste**), 6 / 305, rien au-dessus de 180 BPM. **Aucune classe de tempo n'atteint `assez`** : la basse par tempo
n'est pas calibrable sur ces sous-ensembles, seulement le profil d'ensemble de `LATIN`.

Points à connaître (README de chaque sous-ensemble) :
- `BALLAD` : le solo étiqueté 6/8 (Sweet Sorrow) écrit ses temps en 4/4 et n'a aucune basse : il reste 9 solos exploitables, aucune mesure réellement en 6/8.
- `TWOBEAT` : les 32 solos sont `TRADITIONAL` ; 24 enregistrés en 1925–1928, 2 en 1938, 6 en 1941. C'est le deux-temps du jazz des années vingt (basse, tuba), pas celui d'un swing moderne.
- `FUNK` : 8 solos de forme `open` (vamps à 1–3 accords) font 55 % des mesures valides et gonflent la part de mesures à un accord (82 %) ; les parts « au changement » reposent sur 12 solos.
- `LATIN` : 4 solos n'ont aucune mesure 4/4 (trois en 3/4, un en 5/4) : 404 mesures écartées (20 %).
- Pas de croches : le rythme de la basse se lit à la noire seulement (voir § 3).

### 4.4 JTD (MIT), swing et micro-timing par tempo

Pistes mesurées / musiciens distincts ; médiane par piste puis médiane des pistes ; IC à 95 % par musicien. Tâche : **A6** (swing selon le tempo), B1, B5.

| Classe | Pistes (batterie) | Batteurs | Swing batterie, médiane [IC95 %] | Swing basse | Swing piano | Piano − batterie | Basse − batterie | Fiabilité |
|---|---|---|---|---|---|---|---|---|
| < 120 BPM (100–120) | 55 | 31 | 0,720 [0,712–0,732] | 0,713 | 0,695 | ≈ +20 ms | ≈ 0 ms | **juste** (55 < 60 pistes) |
| 120–180 | 369 | 75 | 0,708 [0,703–0,714] | 0,708 | 0,698 | ≈ +20 ms | ≈ 0 ms | **assez** |
| 180–240 | 379 | 73 | 0,656 [0,655–0,667] | 0,679 | 0,667 | ≈ +20 ms | ≈ 0 ms | **assez** |
| ≥ 240 (240–300) | 171 | 57 | 0,591 [0,583–0,609] | 0,654 | 0,619 | ≈ +11 ms | ≈ 0 ms | **assez** |

Courbe de la batterie : `swing = 0,7213 − 0,000976 × max(tempo − 140, 0)` (charnière 140 BPM, IC 130–150 ; pente −0,0976 par 100 BPM, IC −0,108 à −0,090 ; non croissante dans
100 % des rééchantillons ; valable de 102 à 299 BPM seulement). Le `default_swing_ratio` de 0,71 d'E7 convient jusqu'à ≈ 180 BPM, puis excède la mesure de 0,054 (180–240) et de 0,119 (≥ 240).
Basse et piano ont des courbes de même forme, plus plates (−0,048 et −0,066 de 120 à 240 BPM contre −0,098). Écarts relatifs : en dessous de la résolution des CSV (10 ms) pour la basse
(à traiter comme un décalage nul) ; piano environ 0,13 à 0,27 pas de retard sur la batterie. Les IC « par piste » sont trop étroits (largeur par musicien ÷ par piste jusqu'à 5,8 pour la basse
à 180–240 BPM) : reprendre ceux « par musicien ». Table à reprendre par A6 : `references/jtd-swing-tempo/README.md` et clé `a6_table` du JSON.

## 5. Styles iReal non couverts et pistes

Liste des styles de l'application : page « Backing track styles » d'iReal Pro, <https://www.irealpro.com/learn/backing-track-styles/> (« Updated July 2026 », lue le 2026-11-02) et
page « Style Packs », <https://www.irealpro.com/in-apps/> (lue le 2026-11-02) : 90 styles, Jazz 27, Latin 8, Pop 15, plus les packs Blues 12, Brazilian 11, Salsa 17. Ces pages ne nomment pas tous les styles : 15 des 27 de Jazz, aucun des 8 de Latin, 11 des 15 de Pop : le recensement exact est à faire dans l'application ou dans `harmonium_practice/src/ireal.rs` du dépôt training (non lu ici).
Couverture par les trois sources, sur les styles nommés :

| Style iReal (groupe) | Couvert par | Verdict | Manque |
|---|---|---|---|
| Slow / Medium / Medium Up / Up Tempo Swing (Jazz) | WJazzD `SWING` (E7), GMD `jazz`, JTD | oui (B1) | — |
| Swing Two/Four, Latin/Swing, Bossa/Swing (Jazz, deux feels) | WJazzD `TWOBEAT` (basse), `LATIN`, GMD | partiel | le changement de feel entre sections est un mécanisme moteur (A3) |
| Ballad Even / Melodic / Swing / Double Time Feel, Gypsy Jazz, Long Notes (Jazz) | WJazzD `BALLAD` : 9 solos, 294 mesures (trop peu) | **non** pour la batterie | **balais** : aucun fichier du GMD (kit électronique à baguettes) ; Gypsy Jazz (la pompe) : aucune source |
| Bossa Nova, Bossa Ballad, Bossa Cha (Brazilian) | GMD `latin/brazilian-bossa` (1 batteur), WJazzD `LATIN` | partiel (trop peu) | deuxième et troisième batteur |
| Samba, Samba Fast (Brazilian) | GMD `latin/brazilian-samba` (5 fichiers, juste), `latin/samba` | partiel | percussions de samba (surdo, tamborim, pandeiro) absentes du GMD |
| Baião, Afoxé (= ijexá), Maracatu (Brazilian) | GMD `brazilian-baiao` (3 + 29 fills, juste), `brazilian-ijexa` (3, juste), `brazilian-maracatu` (2, trop peu) | partiel | un seul batteur par style |
| Partido Alto, Samba Brush, Samba Percussion (Brazilian) | aucun | **non** | voir pistes |
| Funk, Glam Funk (Pop) | GMD `funk` (assez), `funk/*`, WJazzD `FUNK` (juste) | oui sauf Glam Funk | Glam Funk non identifié dans les sources |
| Rock, Rock 12/8, Reggae, Country, Disco, RnB (Pop) | GMD `rock` (assez, ternaire 19 fichiers), `reggae` (3, juste), `country` (2, trop peu), `dance/disco` (5, juste), `soul`, `hiphop` | oui sauf Country | Country : 2 fichiers `beat` |
| House, Bluegrass (Pop) | aucun (`dance/breakbeat` 2 fichiers ne couvre pas la house) | **non** | |
| Shuffle ; Chicago Shuffle, Muddy, Slo-Mo, Mo-Slo (Blues) | GMD `blues/shuffle` (4), `rock/shuffle` (4), `funk/purdieshuffle` (1 + 29 fills) | partiel (trop peu) | B6 le notait : 4 fichiers à compléter ; 12/8 lent absent |
| Gospel, Nola, Stax, Funky (Blues) | GMD `gospel` (1 + 18 fills), `neworleans` (53, assez), `soul/motown` (4) | partiel | gospel trop peu |
| Salsa : Son Montuno 2-3 et 3-2, Mambo, Guaracha, Timba, Cha-Cha-Chá, Bolero, Danzón, Guajira, Comparsa, Mozambique, Plena | aucun | **non** | clave et tumbao absents : WJazzD `LATIN` est du hard bop sur rythme latin, pas du salsa |
| Rumba Guaguancó, Afro 6/8, Merengue, Bomba, Songo (Salsa) | GMD `afrocuban/rhumba` (1 + 18 fills), `afrocuban/bembe` (1 + 29 fills, ternaire), `latin/dominican-merengue` / `merengue` (1 chacun), `latin/bomba` (1) ; `brazilian-songo` n'est pas le songo cubain | quasi non | un fichier par style |

**Pistes pour couvrir les manques** (licence lue à la source, le 2026-11-02) :
- **Samba, partido alto, samba-enredo, marcha, capoeira** : *Brazilian Rhythmic Instruments Dataset* (BRID), 367 pistes audio de dix instruments à percussion brésiliens, **CC BY 4.0** —
  <https://api.datacite.org/dois/10.5281/zenodo.14051323> (métadonnées DataCite, la page Zenodo répond 403). Audio, pas du symbolique : il faudrait détecter les attaques par instrument, donc une
  chaîne de plus et une fiabilité à mesurer ; usage commercial permis avec attribution. Couvre Samba, Partido Alto, Samba Percussion ; pas Bossa ni Maracatu.
- **Balais (ballades, Samba Brush)** : *ENST-Drums* contient des séquences aux balais mais sa licence est **CC BY-NC-ND 4.0** (« No commercial use is possible ») —
  <https://api.datacite.org/dois/10.5281/zenodo.7432188> : exclu, y compris au labo (ND). *MDB Drums* : CC BY-NC-SA 4.0 (<https://github.com/CarlSouthall/MDBDrums>, lu le 2026-11-02) : usage A (analyse au labo,
  décision 3 du propriétaire), rien dans un profil. Aucune source ouverte et distribuable de motifs de balais trouvée : piste réaliste = règles de métier (une phrase de balais est un balayage continu) plus
  une banque SoundFont à balais choisie en **L1**.
- **Salsa et Afro-Cuban** : aucune source symbolique ouverte trouvée en deux recherches (2026-11-02, mots-clés « salsa clave tumbao dataset MIDI license »). Les formules (clave, tumbao) sont des idiomes traditionnels ; les coder
  comme règles de métier relève du propriétaire (statut juridique d'un idiome rythmique non vérifié ici). Les fichiers `afrocuban/*` du GMD donnent la batterie d'un batteur, pas la section rythmique.
- **Shuffle et blues lents** : le GMD n'a que 4 fichiers `blues/shuffle` ; le 12/8 de `rock` (19 fichiers ternaires, juste à assez) peut servir de proxy de feel, pas de style.
- **House, Bluegrass, Glam Funk, Gypsy Jazz** : rien de vérifié ; non recherchés au-delà du GMD.

## 6. Ce qui manque au schéma du moteur pour exprimer un pattern mesuré (à transmettre à A1 et A6)

Constats tirés de `profiles/README.md` et de `harmonium_core/src/time_plan/mod.rs` (lus, rien exécuté côté moteur : à vérifier par un agent moteur).

1. **Feel ternaire sous swing** : `TimePlan::swing_quarter_steps` renvoie `None` (donc pas de swing) pour une grille impaire par noire ou une mesure composée ; `set_swing_ratio` borne à 0,5–0,75.
   Les patterns `ternary` (12 pas en 4/4, 3 par pulsation) s'écrivent donc en `steps_per_bar = 12`, `steps_per_pulse = 3`, swing droit, **si** le chargeur de `[[patterns]]` accepte une grille de 12 pas ; sinon
   ils tombent sur la grille 16 pas swinguée à r = 2/3 : pas `k` de la grille triolet → pas `4·(k div 3) + (k mod 3)`. **À vérifier par A6.** 6/8 : jamais de swing, 12 pas droits.
2. **Swing selon le tempo** : un seul `swing_ratio` scalaire pour toutes les pistes, réglé par `SetSwing`/`--swing`. JTD donne une courbe (batterie 0,7213 → 0,59 de 140 à 300 BPM) et des courbes plus plates pour la basse et le piano :
   il faut une fonction de tempo en données et, pour la fidélité, un swing par piste : au-delà de 180 BPM la basse et le piano restent plus ternaires que la batterie (0,654 et 0,619 contre 0,591 à ≥ 240 BPM).
3. **Micro-timing de la batterie par rôle** : `[performance.tracks.*]` existe pour `PercussionLow` et `PercussionHigh` seulement ; le GMD mesure 12 rôles (rock 4/4 droit, médianes : ride +9 ms sur le temps, +14 ms hors temps ; charleston fermé −7 ms ; pédale −14 ms ; caisse claire et grosse caisse −3 à −6 ms ; dispersion de 22 à 34 ms).
   Deux pistes ne séparent pas le charleston de la caisse claire (tous deux sur `PercussionHigh`) : un décalage par voix manque.
4. **Fills** : `[[cadence_patterns]]` est unique par densité et exclu du tirage pondéré ; le GMD donne des `fill` de 1 à 4 mesures avec une position (`fill_position` : premier temps de la mesure, pas de la dernière attaque, mesures touchées).
   A1 a besoin d'une banque pondérée de relances, avec longueur et position de départ (levée au temps 4).
5. **Probabilité par pas** : un pattern est une mesure fixe pondérée ; les mesures donnent des probabilités par pas et par rôle (ghost notes à 5–25 %). Seule l'énumération de patterns les reproduit : le schéma n'a pas de coup probabiliste.
6. **Phrases de plusieurs mesures** : les mesures sont ici statistiques par mesure ; les patterns de 2 et 4 mesures du GMD ne sont pas mesurés (les fichiers `beat` durent 30 à 40 mesures). À ajouter au labo quand A1 est lancée.
7. **Rôles latins** : le moteur n'a que deux pistes de percussion ; `sidestick`, `ride_bell`, `tom_*` y passent comme des notes GM d'un kit (banque 128). Les congas, claves et cloches du `latin_stand_in` supposent une banque SoundFont qui les contient : L1.
8. **Basse** : WJazzD ne donne que la hauteur au temps. Deux temps, notes tenues, répétitions se lisent à la noire ; croches de passage, notes fantômes et anticipations (A4) n'ont **aucune** source mesurée ici.
   `TWOBEAT` est un deux-temps des années vingt (arrivée sur la basse à 25 %), pas un modèle de ballade moderne.

## 7. Limites générales

- Dix batteurs au total dans le GMD, kit électronique Roland TD-11 : vélocités et micro-timing sont ceux du kit et des batteurs.
- Les sous-ensembles WJazzD sont petits (10 à 32 solos) et non représentatifs d'un style : ils nomment un corpus, pas une tradition (principe VII). Les IC par bootstrap sur moins d'une dizaine de solos restent optimistes.
- JTD : détection automatique des temps et des attaques sur audio séparé ; CSV arrondis à 10 ms ; seuls les écarts relatifs entre instruments sont fiables ; le piano mêle comping et solo.
- Les patterns proposés sont des construits sur probabilités par pas, jugés à l'écoute par l'orchestrateur ; ils ne sont pas validés contre le moteur (aucun profil n'a été généré ici).

## 8. Reproduire

```sh
make backing-l2              # fetch + GMD + WJazzD + JTD (≈ 2 minutes, cache corpus/*/raw/)
make backing-gmd             # corpus/gmd/manifest.jsonl, references/gmd-*/
make backing-wjazzd          # references/wjazzd-{ballad,twobeat,latin,funk}/
make backing-jtd-tempo       # references/jtd-swing-tempo/
make test                    # 500 réussis, 31 ignorés
```
