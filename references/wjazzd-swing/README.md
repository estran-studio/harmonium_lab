# `wjazzd-swing` — mesures d'accompagnement pour le profil `wjazzd_swing` (phase 018, E7)

Mesures agrégées de la basse, de la batterie et du timing d'un accompagnement swing, qui fixent
les paramètres du profil distribué `wjazzd_swing` du moteur (`harmonium/profiles/wjazzd_swing/`).
Décision F3 (plan 018) : combinaison 1 de `corpus/sources-jazz.md` ; sources NC/SA absentes ;
**aucune phrase de solo** ni transcription copiée (principe VII). Les bruts restent en cache
gitignoré (`corpus/*/raw/`), seuls les manifestes, les `VERSION` et les dérivés agrégés sont versionnés.

## Sources, licences, empreintes

| Source | Version, empreinte vérifiée avant toute lecture | Licence | Mention portée par le profil |
|---|---|---|---|
| Weimar Jazz Database (WJazzD), `jazzomat.hfm-weimar.de` | v2.1 (base 2.2), SHA256 `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` (identique à `sources-jazz.md`) | ODbL 1.0 (base) + DbCL 1.0 (contenus) | ODbL §4.3 : « Contains information from the Weimar Jazz Database… » |
| Groove MIDI Dataset (GMD), Google LLC | v1.0.0 midi-only, SHA256 `651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e` (identique) | CC BY 4.0 | Gillick, Roberts, Engel, Eck, Bamman, ICML 2019 |
| Jazz Trio Database (JTD) | v0.2, `jazz-trio-database-v02.zip` (release GitHub `v02-zenodo`), SHA256 `42c3df0700e0cd6e73231b9ed111283600750305e2e9cf451f80664d1ec90025`, MD5 `43f543fb…` (celui de `mirdata`) | MIT | Cheston, Schlichting, Cross, Harrison, TISMIR 2024 |

Seules les annotations CSV/JSON de JTD sont lues (jamais `piano_midi.mid`, usage A). Le `manifest.jsonl`
de chaque source (`corpus/{wjazzd,gmd,jtd}/`) porte un champ `licence` et aucune note.

## Commandes

```sh
make backing-fetch       # télécharge et vérifie les trois sources (cache corpus/*/raw/)
make backing-measures    # manifestes + measures-bass.json, measures-drums.json, measures-timing.json
make backing-values OUT=/chemin/percussion.toml HEADER=references/wjazzd-swing/percussion-header.txt
                         # percussion.toml du profil + poids de basse, depuis les mesures
make backing-validate ENGINE_DIR=… ENGINE_BIN=…/harmonium-cli BACKING_BARS=88 BACKING_GROUPS="all blues other_forms reliable" \
     PROFILES="wjazzd_swing=…/profiles/wjazzd_swing grille_accompagnee=…/tests/fixtures/profiles/grille_accompagnee"
                         # basse générée (vérité terrain du moteur) contre WJazzD → validation-bass.{json,md}
```

Relancer `backing-measures` deux fois donne des fichiers identiques (clés triées, arrondis fixes, pas
d'horodatage ; la date de relevé n'est que dans `VERSION`). Les tests du labo (`make test`) ne lisent
aucun brut : fixtures synthétiques générées dans les tests.

## Fichiers

| Fichier | Contenu |
|---|---|
| `measures-bass.json` | WJazzD, sous-ensemble `rhythmfeel = SWING` (361 solos, 104 772 temps, 26 317 mesures, 23 224 valides : 4/4, quatre `bass_pitch`, accord connu) : arrivée, approche, passage, intervalles, registre, rythme harmonique, tempos, formes ; groupes `all`, `blues` (87 solos), `other_forms`, `reliable` (75 solos dont ≥ 80 % des arrivées sur une note d'accord), quatre tranches de tempo |
| `measures-drums.json` | GMD, `jazz` et `jazz/swing` (cœur, 55 fichiers, 1 229 mesures `beat`, 22 `fill`), autres groupes à part (`blues/shuffle` 4 fichiers, 90 mesures) : rapport de swing du ride, probabilités par pas, figures de ride, `proposed_patterns` construits sur les probabilités agrégées |
| `measures-timing.json` | JTD, 976 pistes retenues sur 1 294 (4 temps, 60 à 330 BPM, ≥ 60 % de temps appariés basse et batterie), huit tranches de tempo : rapport de swing, placement relatif basse/piano/batterie, dispersion, rythme du piano (indicatif), basse hors pulsation |
| `validation-bass.{json,md}` | distance de la basse générée à WJazzD, `wjazzd_swing` et ligne de base `grille_accompagnee` (fixture non calibrée), 8 graines × 88 mesures |
| `validation-bass-heldout.{json,md}` | même validation sur 16 autres graines (11 à 26), jamais vues par la calibration |
| `percussion-header.txt` | commentaire d'en-tête du `percussion.toml` généré |

## Ce que les mesures disent (sous-ensemble swing de WJazzD)

| Mesure | Valeur (n) |
|---|---|
| Tempo moyen par solo, centiles 10 / 25 / 50 / 75 / 90 | 93 / 132 / 177,5 / 242,6 / 284,5 BPM (blues : médiane 147,4) |
| Hauteur de basse, centiles 1 / 25 / 50 / 75 / 99 (MIDI) | 33 / 38 / 42 / 45 / 52 ; arrivées (centiles 10–90) 36..46 ; meilleure fenêtre de 12 demi-tons 36..47 |
| Approche : note du temps qui précède une arrivée, `none` / chromatique / diatonique | 59 / 21 / 19 % (n = 27 931) ; avant la barre 57 / 24 / 18 ; à mi-mesure 59 / 19 / 22 |
| Passage : classe de la note de passage (hors arrivée et approche), accord / gamme / chromatique | 48 / 23 / 29 % (n = 52 041) |
| Intervalles entre notes consécutives, centiles 50 / 75 / 90 / 95 / 99 | 2 / 5 / 8 / 11 / 14 demi-tons ; 20 % de répétitions ; 42 % poursuivent le sens ; 44 % se rapprochent de la cible |
| Rythme harmonique | 76 % de mesures à un accord, 22 % à deux ; changement au temps 1 : 75 %, au temps 3 : 23 % ; blues : 92 % à un accord |
| Chorus | 12 mesures : 387 ; 16 : 109 ; 32 : 296 ; autres : 203 (226 des 296 chorus de 32 mesures sont A1 A2 B1 A3) |
| Arrivée sur la basse de l'accord au changement | 41 % (63 % dans le groupe `reliable`) |

**Limite des données.** `bass_pitch` de WJazzD ne colle pas bien à la grille : seuls 41 % des changements
d'accord tombent sur la basse de l'accord, 23 % des premiers temps sans changement sur la fondamentale,
avec 17 % à 70 % d'un solo à l'autre (centiles 10 et 90). Aucun décalage d'un temps ni erreur d'octave ne
l'explique (intervalles sans pic à 12, plage 28–53). Le moteur arrive toujours sur la basse publiée : ces
critères d'arrivée ne se règlent pas (distance 0,59 à 0,77, identique pour le profil calibré et la ligne de
base) ; ils sont séparés dans le rapport (famille `arrival`).

JTD (976 pistes) : rapport de swing de la batterie par tranche de tempo, médiane (p10–p90 de 0,69–0,75 à 100–125 BPM à 0,55–0,63 à 275–330) : 100–125 BPM 0,720 ; 125–150 0,718 ; 150–175 0,700 ; 175–200 0,677 ; 200–225 0,655 ;
225–250 0,625 ; 250–275 0,591 ; 275–330 0,577. Piano moins batterie : +0,226 pas (≈ +20 ms) ;
basse moins batterie : 0,000 pas (médiane ; moyenne tronquée +0,048) ; écart-type par piste 0,22 pas
(basse) et 0,33 pas (piano), les CSV étant arrondis à 10 ms (≈ 0,13 pas à 200 BPM). Seuls les écarts
RELATIFS entre instruments sont fiables (les écarts au temps dépendent de la détection du temps).

GMD : rapport de swing du ride par fichier, cœur : médiane 0,646 (18 fichiers mesurés sur 33 ; les autres
retombent sur 0,667) ; `blues/shuffle` 0,639. Sur le cœur, ride sur les temps (pas 0, 4, 8, 12) dans 32 à 36 %
des mesures, croche swinguée (pas 6 puis 14) 30 à 33 %, pédale de charleston aux temps 2 et 4 (pas 4 et 12)
39 à 45 %, grosse caisse au temps 1 dans 44 % ; 52 % des mesures `jazz`
n'ont pas de ride (charleston ou balais).

## Validation : basse générée contre WJazzD

`validation-bass.md` : la calibration n'a vu que les graines 1 à 6 ; sur les graines 11 à 26
(`validation-bass-heldout.md`) la distance est la même (0,250 contre 0,326 pour la ligne de base).
Distance aux 361 solos swing (0 = identique, 1 = disjoint), famille par famille :

| Famille | `wjazzd_swing` | `grille_accompagnee` (non calibrée) |
|---|---|---|
| approche (poids, distances, côté) | 0,169 | 0,435 |
| intervalles | 0,144 | 0,186 |
| registre | 0,117 | 0,185 |
| passage | 0,137 | 0,082 |
| rythme harmonique (propriété de la grille, non réglée) | 0,302 | 0,188 |
| arrivée (fixe : le moteur arrive toujours sur la basse de l'accord) | 0,678 | 0,678 |
| **moyenne des critères** | **0,250** | **0,326** |

La calibration a un coût mesuré : le passage s'éloigne de WJazzD (0,082 → 0,137) pour que l'approche et
les intervalles s'en rapprochent. Le rythme harmonique est plus dense que la moyenne du corpus parce que
la forme AABA en *rhythm changes* a deux accords dans 24 de ses 32 mesures.

## Mentions de licence à reprendre

> Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made
> available here under the Open Database License (ODbL) 1.0, <https://opendatacommons.org/licenses/odbl/1-0/>;
> individual contents under the Database Contents License (DbCL) 1.0.
> Groove MIDI Dataset v1.0.0, CC BY 4.0: J. Gillick, A. Roberts, J. Engel, D. Eck, D. Bamman, « Learning to Groove
> with Inverse Sequence Transformations », ICML 2019.
> Jazz Trio Database v0.2, MIT License: H. Cheston, J. L. Schlichting, I. Cross, P. M. C. Harrison, TISMIR 2024,
> <https://doi.org/10.5334/tismir.186>.
