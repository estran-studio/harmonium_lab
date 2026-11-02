# wjazzd-latin : accompagnements `rhythmfeel = LATIN` de la Weimar Jazz Database (phase 019, L2)

Mesures de la **marche de basse** et de son **rythme au temps** sur un sous-ensemble non swing de WJazzD, pour une bibliothèque de styles. Comptes, parts et centiles uniquement : aucune phrase de solo, aucune suite de notes n'est conservée (principe VII).

## Provenance et licence

- Source : Weimar Jazz Database (WJazzD), WJazzD 2.1 (base 2.2, publiée le 2018-02-08), SHA256 `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` (vérifié avant toute lecture).
- Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus).
- Mention requise (ODbL §4.3) : « Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0). »
- Sous-ensemble : solo_info.rhythmfeel = 'LATIN' (valeur exacte) ; mesures 4/4 de chorus (bar >= 1) à quatre temps, basse complète et accord connu (NC et symboles non analysés écartés).
- Les mesures dérivées sont des faits agrégés ; la base elle-même reste dans `corpus/wjazzd/raw/` (cache gitignoré). Manifeste des solos : `corpus/wjazzd/manifest.jsonl` (champ `l2_subset`).

## Reproduction

```bash
python -m harmonium_lab.backing.wjazzd_subsets --subset LATIN
```

Écrit `references/wjazzd-latin/measures-bass.json` et ce `README.md` ; deux exécutions donnent des fichiers identiques (clés triées, arrondis fixes, bootstrap à graine fixe `wjazzd-subsets-v1`, 2000 rééchantillons).

## Effectifs

- **27 solos** `LATIN` (valeur exacte) ; 23 ont au moins une mesure valide. Hors sous-ensemble : 6 solos à `rhythmfeel` composé (`A:LATIN/B:SWING` 1, `FUNK/SWING` 1, `LATIN/FUNK` 3, `LATIN/SWING` 1).
- **2063 mesures** (chorus, toutes signatures) dont **1639 valides** (6556 temps) ; **40,0 min** de mesures valides (40,5 min de mesures 4/4). Méthode : minutes = mesures × 4 temps / avgtempo du solo (BPM, la noire est le temps), sommées sur les solos. Contrôle sur tous les temps de chorus, toutes signatures : 50,8 min à `avgtempo` contre 50,6 min (étendue des `onset`).
- **87 chorus** vus en 4/4 (69 sans le dernier chorus de chaque solo, qui peut être tronqué) ; longueurs des chorus conservés (mesures×effectif) : 8×31, 16×9, 24×9, 31×1, 32×9, 34×3, 40×1, 44×1, 48×3, 65×1, 95×1.
- Tempos (`avgtempo`) : min 60,1, p25 132,2, médiane 152,7, p75 192,1, max 272,7 BPM.
- Enregistrements : 1951–1997 (27 dates lues, 0 inconnues) ; par décennie : 1950s ×4, 1960s ×11, 1970s ×4, 1980s ×4, 1990s ×4.
- Signatures des solos : 3/4 ×3, 4/4 ×23, 5/4 ×1. Mesures non 4/4 (écartées par le lecteur E7) : 404 mesures dans 4 solo(s) (3/4 : 367 mesures / 3 solo(s), 5/4 : 37 mesures / 1 solo(s)) ; solos sans aucune mesure 4/4 : 4.

### Mesures écartées (toutes signatures)

| motif | mesures | part |
|---|---|---|
| signature ≠ 4/4 | 404 | 20 % |
| incomplète | 18 | 1 % |
| basse manquante | 0 | 0 % |
| accord absent / NC / non analysé | 2 | 0 % |
| valides | 1639 | 79 % |

Accords (temps 4/4 d'un chorus) : 6596 avec symbole, 0 sans symbole, 11 `NC`, 0 non analysés. 4 solo(s) n'ont aucune mesure valide.

## Principales mesures (tous solos du sous-ensemble, IC à 95 % par bootstrap par solo)

| indicateur | estimation [IC 95 %] | n événements | n solos | IC absent car |
|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 57 % [46–68 %] | 1420 | 22 |  |
| approche 4ᵉ temps (changement à la barre) : aucune | 60 % [51–66 %] | 1205 | 22 |  |
| approche 4ᵉ temps (changement à la barre) : chromatique | 22 % [17–26 %] | 1205 | 22 |  |
| approche 4ᵉ temps (changement à la barre) : diatonique | 19 % [11–29 %] | 1205 | 22 |  |
| approche (tous contextes) : aucune | 58 % [49–65 %] | 1831 | 23 |  |
| approche (tous contextes) : chromatique | 25 % [18–34 %] | 1831 | 23 |  |
| approche (tous contextes) : diatonique | 17 % [11–25 %] | 1831 | 23 |  |
| note de passage : note d'accord | 64 % [53–75 %] | 2848 | 23 |  |
| note de passage : degré de gamme | 15 % [10–21 %] | 2848 | 23 |  |
| note de passage : chromatique | 21 % [14–29 %] | 2848 | 23 |  |
| intervalles : répétitions (Δ = 0) | 38 % [32–44 %] | 6533 | 23 |  |
| mesures `quarters` (aucune répétition) | 28 % [20–36 %] | 1639 | 23 |  |
| mesures `halves` (t1=t2, t3=t4) | 8 % [5–12 %] | 1639 | 23 |  |
| mesures à un seul accord | 87 % [79–93 %] | 1639 | 23 |  |
| intervalle médian (demi-tons, valeur absolue) | 1,0 [1,0–2,0] | 6533 | 23 |  |
| intervalle p90 (demi-tons, valeur absolue) | 8,0 [7,0–9,0] | 6533 | 23 |  |

Le 1ᵉʳ temps de mesure sans changement et le détail des approches (haut/bas, distance) sont dans le JSON (`groups.all.arrival`, `.approach`, `.passage`, `.intervals`).

## Rythme de la basse (au temps)

Sur 1639 mesures valides. `bar_pattern` : égalités de hauteur entre temps consécutifs de la mesure. **Une hauteur répétée est soit une noire rejouée, soit une note tenue : indiscernable.**

| motif | mesures | part |
|---|---|---|
| quarters | 459 | 28 % |
| quarters_half | 172 | 10 % |
| quarter_half_quarter | 90 | 5 % |
| quarter_dotted_half | 87 | 5 % |
| half_quarters | 307 | 19 % |
| halves | 136 | 8 % |
| dotted_half_quarter | 125 | 8 % |
| whole | 263 | 16 % |

Longueur des suites de temps à hauteur identique (en temps, barres de mesure franchies) : 1 temps : 68 % (2770), 2 temps : 20 % (815), 3 temps : 5 % (218), 4+ temps : 7 % (299) ; moyenne 1,60 temps ; 58 % des temps sont dans une suite de 2 temps ou plus.
Attache sur la barre de mesure (dernier temps = 1ᵉʳ temps de la mesure suivante) : 25 % (400/1616). Répétitions par position : 1-2 51 %, 2-3 34 %, 3-4 40 %.
Hauteurs distinctes par mesure (1/2/3/4) : 16 % / 30 % / 38 % / 15 %.

**Les croches ne sont pas observables** (une note de basse par noire) : aucun motif de croches n'est déduit, et la longueur « 1 temps » ne dit pas si la note est brève ou répétée.

## Classes de tempo et fiabilité

Seuils (solos avec mesures valides ET mesures valides) : **assez** ≥ 20 solos et ≥ 1500 mesures ; **juste** ≥ 8 solos et ≥ 500 mesures ; sinon **trop peu**. Justification : le solo est l'unité de rééchantillonnage ; avec un écart-type d'environ 0,2 entre solos sur une part (ordre de grandeur relevé en E7), la demi-largeur de l'IC vaut ≈ 0,09 pour 20 solos, ≈ 0,14 pour 8, ≈ 0,20 pour 4.

| groupe (BPM) | solos | solos avec mesures | mesures valides | minutes | chorus | fiabilité | largeur médiane IC (parts) |
|---|---|---|---|---|---|---|---|
| tous | 27 | 23 | 1639 | 40,0 | 87 | **assez** | 0,15 |
| < 120 | 4 | 1 | 39 | 2,6 | 1 | **trop peu** | — |
| 120–180 | 15 | 14 | 887 | 24,2 | 31 | **juste** | 0,16 |
| 180–240 | 7 | 7 | 564 | 11,0 | 51 | **trop peu** | 0,26 |
| ≥ 240 | 1 | 1 | 149 | 2,2 | 4 | **trop peu** | — |

| indicateur | tous | < 120 | 120–180 | 180–240 | ≥ 240 |
|---|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 57 % [46–68 %] | 54 % [pas d'IC] | 61 % [42–78 %] | 60 % [42–73 %] | 35 % [pas d'IC] |
| approche 4ᵉ temps (changement à la barre) : chromatique | 22 % [17–26 %] | 33 % [pas d'IC] | 23 % [18–31 %] | 19 % [10–27 %] | 22 % [pas d'IC] |
| intervalles : répétitions (Δ = 0) | 38 % [32–44 %] | 16 % [pas d'IC] | 37 % [29–45 %] | 43 % [32–57 %] | 27 % [pas d'IC] |
| intervalle médian (demi-tons, valeur absolue) | 1,0 [1,0–2,0] | 5,0 [pas d'IC] | 1,0 [1,0–2,0] | 1,0 [0,0–2,0] | 2,0 [pas d'IC] |
| mesures `quarters` (aucune répétition) | 28 % [20–36 %] | 64 % [pas d'IC] | 28 % [20–35 %] | 21 % [8–37 %] | 46 % [pas d'IC] |
| mesures `halves` (t1=t2, t3=t4) | 8 % [5–12 %] | 0 % [pas d'IC] | 6 % [3–8 %] | 13 % [7–20 %] | 7 % [pas d'IC] |
| mesures à un seul accord | 87 % [79–93 %] | 18 % [pas d'IC] | 89 % [81–96 %] | 88 % [72–99 %] | 86 % [pas d'IC] |

Chaque cellule : estimation [IC 95 %] ; effectifs par groupe dans le JSON (`groups.<groupe>.indicators`, `n_events`, `n_solos`).

**Verdict du sous-ensemble : assez** (23 solos avec mesures valides, 1639 mesures valides).

## Limites

- Les croches ne sont PAS observables : `bass_pitch` n'a qu'une valeur par temps (une noire) ; aucune durée, aucune attaque, aucun silence de basse n'est dans la base. Le rythme de la basse se limite aux répétitions de hauteur d'un temps au suivant, aux suites de temps à hauteur identique et à l'attache sur la barre de mesure.
- Une hauteur répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les distingue pas. `halves` = deux blanches OU deux paires de noires répétées.
- Peu de solos par sous-ensemble (10 à 32) et par classe de tempo : les intervalles de confiance (bootstrap par solo, méthode des percentiles) sont larges et, avec moins de quelques solos, trop optimistes ; ils ne disent rien du biais de sélection de la base (choix des solos, solistes, morceaux).
- La basse annotée est peu cohérente avec la grille d'accords (voir E7, `bass_measures` : la basse de l'accord n'est jouée qu'à 41 % des changements d'accord en swing) : les parts d'arrivée sont celles de l'annotation, pas celles d'une marche idéale.
- Mesures hors 4/4, sans basse complète ou sans accord utilisable écartées (voir `discarded`) ; les intervalles et les approches ne franchissent jamais une mesure écartée. Les suites de temps à hauteur identique sont tronquées aux bords des suites de mesures valides.
- Aucune phrase de solo, aucune suite de notes n'est conservée : uniquement des comptes, parts et centiles.
- L'étiquette `LATIN` est celle du solo : la base ne distingue ni bossa nova, ni samba, ni afro-cubain ; 14 solos post-bop, 8 cool, 4 hard bop, 1 bebop (1951–1997).
- 4 solos sur 27 n'ont aucune mesure en 4/4 (trois en 3/4, un en 5/4) : 404 mesures, soit 20 % des mesures du sous-ensemble, sont écartées pour leur signature. Le groupe `< 120` ne compte donc qu'un solo avec mesures (39 mesures) et `≥ 240` un seul : inutilisables.
- Les figures caractéristiques de la basse latine (anticipations sur le « et » du 2 ou du 4, tumbao, clave) sont des CROCHES : non observables avec une note de basse par temps. Ce que l'on voit (repeat_share 38 %, mesures `whole` 16 %, `half_quarters` 19 %) est compatible avec des notes tenues ou répétées, mais n'établit pas un motif latin.
- Les 2 solos à forme `open` (vamp) sont en 3/4 : aucune mesure valide.

## Exploitable pour le moteur / non exploitable

- Plus gros sous-ensemble en mesures valides (1 639, environ 40 min) : parts globales exploitables comme cibles indicatives. La basse y est nettement plus alignée sur la grille qu'en swing : arrivée sur la basse de l'accord au changement 57 % (IC 46–68 %) contre 41 %, 87 % de mesures à un seul accord.
- Seule la classe `120–180` (14 solos, 887 mesures) atteint « juste » : à utiliser pour un latin mi-tempo ; `180–240` (7 solos) reste « trop peu ».
- NON exploitable : motifs rythmiques latins (croches), distinction bossa / samba, tempos lents ou très rapides.
- Exploitables : parts et centiles de la marche de basse au temps (arrivées, approches du 4ᵉ temps, notes de passage, intervalles, registre), rythme harmonique (accords par mesure), motifs de répétition de hauteur par mesure, tempos et formes, avec leurs IC par solo.
- Non exploitables : tout ce qui est plus fin que la noire (croches, anticipations, durées réelles des notes), les silences de basse, la dynamique et les timbres, les phrases ou suites de notes (non conservées).
- Un indicateur dont l'IC est absent ou très large (voir le tableau) ne sert pas de cible chiffrée.
