# wjazzd-ballad : accompagnements `rhythmfeel = BALLAD` de la Weimar Jazz Database (phase 019, L2)

Mesures de la **marche de basse** et de son **rythme au temps** sur un sous-ensemble non swing de WJazzD, pour une bibliothèque de styles. Comptes, parts et centiles uniquement : aucune phrase de solo, aucune suite de notes n'est conservée (principe VII).

## Provenance et licence

- Source : Weimar Jazz Database (WJazzD), WJazzD 2.1 (base 2.2, publiée le 2018-02-08), SHA256 `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` (vérifié avant toute lecture).
- Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus).
- Mention requise (ODbL §4.3) : « Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0). »
- Sous-ensemble : solo_info.rhythmfeel = 'BALLAD' (valeur exacte) ; mesures 4/4 de chorus (bar >= 1) à quatre temps, basse complète et accord connu (NC et symboles non analysés écartés).
- Les mesures dérivées sont des faits agrégés ; la base elle-même reste dans `corpus/wjazzd/raw/` (cache gitignoré). Manifeste des solos : `corpus/wjazzd/manifest.jsonl` (champ `l2_subset`).

## Reproduction

```bash
python -m harmonium_lab.backing.wjazzd_subsets --subset BALLAD
```

Écrit `references/wjazzd-ballad/measures-bass.json` et ce `README.md` ; deux exécutions donnent des fichiers identiques (clés triées, arrondis fixes, bootstrap à graine fixe `wjazzd-subsets-v1`, 2000 rééchantillons).

## Effectifs

- **10 solos** `BALLAD` (valeur exacte) ; 9 ont au moins une mesure valide. Hors sous-ensemble : 6 solos à `rhythmfeel` composé (`A:LATIN/B:SWING` 1, `FUNK/SWING` 1, `LATIN/FUNK` 3, `LATIN/SWING` 1).
- **342 mesures** (chorus, toutes signatures) dont **294 valides** (1176 temps) ; **20,1 min** de mesures valides (23,4 min de mesures 4/4). Méthode : minutes = mesures × 4 temps / avgtempo du solo (BPM, la noire est le temps), sommées sur les solos. Contrôle sur tous les temps de chorus, toutes signatures : 23,5 min à `avgtempo` contre 23,3 min (étendue des `onset`).
- **12 chorus** vus en 4/4 (11 sans le dernier chorus de chaque solo, qui peut être tronqué) ; longueurs des chorus conservés (mesures×effectif) : 1×1, 16×1, 17×1, 29×1, 32×2, 33×1, 34×1, 35×1, 36×1, 73×1.
- Tempos (`avgtempo`) : min 48,8, p25 53,0, médiane 57,9, p75 64,0, max 67,7 BPM.
- Enregistrements : 1945–1994 (10 dates lues, 0 inconnues) ; par décennie : 1940s ×2, 1960s ×1, 1970s ×2, 1980s ×2, 1990s ×3.
- Signatures des solos : 4/4 ×9, 6/8 ×1. Mesures non 4/4 (écartées par le lecteur E7) : 2 mesures dans 1 solo(s) (5/4 : 2 mesures / 1 solo(s)) ; solos sans aucune mesure 4/4 : 0.

### Mesures écartées (toutes signatures)

| motif | mesures | part |
|---|---|---|
| signature ≠ 4/4 | 2 | 1 % |
| incomplète | 4 | 1 % |
| basse manquante | 36 | 11 % |
| accord absent / NC / non analysé | 6 | 2 % |
| valides | 294 | 86 % |

Accords (temps 4/4 d'un chorus) : 1353 avec symbole, 0 sans symbole, 25 `NC`, 0 non analysés. 1 solo(s) n'ont aucune mesure valide.

## Principales mesures (tous solos du sous-ensemble, IC à 95 % par bootstrap par solo)

| indicateur | estimation [IC 95 %] | n événements | n solos | IC absent car |
|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 55 % [42–70 %] | 409 | 9 |  |
| approche 4ᵉ temps (changement à la barre) : aucune | 67 % [59–72 %] | 243 | 8 |  |
| approche 4ᵉ temps (changement à la barre) : chromatique | 19 % [10–25 %] | 243 | 8 |  |
| approche 4ᵉ temps (changement à la barre) : diatonique | 14 % [9–21 %] | 243 | 8 |  |
| approche (tous contextes) : aucune | 72 % [66–77 %] | 366 | 9 |  |
| approche (tous contextes) : chromatique | 14 % [8–21 %] | 366 | 9 |  |
| approche (tous contextes) : diatonique | 13 % [9–18 %] | 366 | 9 |  |
| note de passage : note d'accord | 67 % [58–82 %] | 364 | 8 |  |
| note de passage : degré de gamme | 20 % [10–26 %] | 364 | 8 |  |
| note de passage : chromatique | 13 % [8–18 %] | 364 | 8 |  |
| intervalles : répétitions (Δ = 0) | 24 % [18–35 %] | 1166 | 9 |  |
| mesures `quarters` (aucune répétition) | 44 % [31–55 %] | 294 | 9 |  |
| mesures `halves` (t1=t2, t3=t4) | 11 % [6–17 %] | 294 | 9 |  |
| mesures à un seul accord | 61 % [33–83 %] | 294 | 9 |  |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [2,0–3,0] | 1166 | 9 |  |
| intervalle p90 (demi-tons, valeur absolue) | 8,0 [8,0–10,0] | 1166 | 9 |  |

Le 1ᵉʳ temps de mesure sans changement et le détail des approches (haut/bas, distance) sont dans le JSON (`groups.all.arrival`, `.approach`, `.passage`, `.intervals`).

## Rythme de la basse (au temps)

Sur 294 mesures valides. `bar_pattern` : égalités de hauteur entre temps consécutifs de la mesure. **Une hauteur répétée est soit une noire rejouée, soit une note tenue : indiscernable.**

| motif | mesures | part |
|---|---|---|
| quarters | 128 | 44 % |
| quarters_half | 23 | 8 % |
| quarter_half_quarter | 7 | 2 % |
| quarter_dotted_half | 5 | 2 % |
| half_quarters | 63 | 21 % |
| halves | 31 | 11 % |
| dotted_half_quarter | 12 | 4 % |
| whole | 25 | 8 % |

Longueur des suites de temps à hauteur identique (en temps, barres de mesure franchies) : 1 temps : 78 % (697), 2 temps : 16 % (145), 3 temps : 3 % (23), 4+ temps : 3 % (27) ; moyenne 1,32 temps ; 41 % des temps sont dans une suite de 2 temps ou plus.
Attache sur la barre de mesure (dernier temps = 1ᵉʳ temps de la mesure suivante) : 7 % (20/284). Répétitions par position : 1-2 45 %, 2-3 17 %, 3-4 29 %.
Hauteurs distinctes par mesure (1/2/3/4) : 8 % / 22 % / 40 % / 29 %.

**Les croches ne sont pas observables** (une note de basse par noire) : aucun motif de croches n'est déduit, et la longueur « 1 temps » ne dit pas si la note est brève ou répétée.

## Classes de tempo et fiabilité

Seuils (solos avec mesures valides ET mesures valides) : **assez** ≥ 20 solos et ≥ 1500 mesures ; **juste** ≥ 8 solos et ≥ 500 mesures ; sinon **trop peu**. Justification : le solo est l'unité de rééchantillonnage ; avec un écart-type d'environ 0,2 entre solos sur une part (ordre de grandeur relevé en E7), la demi-largeur de l'IC vaut ≈ 0,09 pour 20 solos, ≈ 0,14 pour 8, ≈ 0,20 pour 4.

| groupe (BPM) | solos | solos avec mesures | mesures valides | minutes | chorus | fiabilité | largeur médiane IC (parts) |
|---|---|---|---|---|---|---|---|
| tous | 10 | 9 | 294 | 20,1 | 12 | **trop peu** | 0,14 |
| < 120 | 10 | 9 | 294 | 20,1 | 12 | **trop peu** | 0,14 |
| 120–180 | 0 | 0 | 0 | 0,0 | 0 | **trop peu** | — |
| 180–240 | 0 | 0 | 0 | 0,0 | 0 | **trop peu** | — |
| ≥ 240 | 0 | 0 | 0 | 0,0 | 0 | **trop peu** | — |

| indicateur | tous | < 120 | 120–180 | 180–240 | ≥ 240 |
|---|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 55 % [42–70 %] | 55 % [41–71 %] | n/a | n/a | n/a |
| approche 4ᵉ temps (changement à la barre) : chromatique | 19 % [10–25 %] | 19 % [10–25 %] | n/a | n/a | n/a |
| intervalles : répétitions (Δ = 0) | 24 % [18–35 %] | 24 % [18–34 %] | n/a | n/a | n/a |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [2,0–3,0] | 2,0 [2,0–3,0] | n/a | n/a | n/a |
| mesures `quarters` (aucune répétition) | 44 % [31–55 %] | 44 % [31–55 %] | n/a | n/a | n/a |
| mesures `halves` (t1=t2, t3=t4) | 11 % [6–17 %] | 11 % [6–18 %] | n/a | n/a | n/a |
| mesures à un seul accord | 61 % [33–83 %] | 61 % [34–84 %] | n/a | n/a | n/a |

Chaque cellule : estimation [IC 95 %] ; effectifs par groupe dans le JSON (`groups.<groupe>.indicators`, `n_events`, `n_solos`).

**Verdict du sous-ensemble : trop peu** (9 solos avec mesures valides, 294 mesures valides).

## Limites

- Les croches ne sont PAS observables : `bass_pitch` n'a qu'une valeur par temps (une noire) ; aucune durée, aucune attaque, aucun silence de basse n'est dans la base. Le rythme de la basse se limite aux répétitions de hauteur d'un temps au suivant, aux suites de temps à hauteur identique et à l'attache sur la barre de mesure.
- Une hauteur répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les distingue pas. `halves` = deux blanches OU deux paires de noires répétées.
- Peu de solos par sous-ensemble (10 à 32) et par classe de tempo : les intervalles de confiance (bootstrap par solo, méthode des percentiles) sont larges et, avec moins de quelques solos, trop optimistes ; ils ne disent rien du biais de sélection de la base (choix des solos, solistes, morceaux).
- La basse annotée est peu cohérente avec la grille d'accords (voir E7, `bass_measures` : la basse de l'accord n'est jouée qu'à 41 % des changements d'accord en swing) : les parts d'arrivée sont celles de l'annotation, pas celles d'une marche idéale.
- Mesures hors 4/4, sans basse complète ou sans accord utilisable écartées (voir `discarded`) ; les intervalles et les approches ne franchissent jamais une mesure écartée. Les suites de temps à hauteur identique sont tronquées aux bords des suites de mesures valides.
- Aucune phrase de solo, aucune suite de notes n'est conservée : uniquement des comptes, parts et centiles.
- Dix solos de 7 solistes (Murray ×3 et Pepper ×2 font la moitié), tous à 48,8–67,7 BPM : une seule classe de tempo (`< 120`) est peuplée, les trois autres sont vides ; rien sur les ballades à 70–100 BPM.
- Le solo `Sweet Sorrow` (melid 246) est étiqueté 6/8 au niveau du solo, mais ses temps écrivent 4/4 (quatre temps par mesure, à `avgtempo`) : le lecteur E7 le lit en 4/4 (36 mesures) ; il n'a AUCUNE basse annotée, donc aucune mesure valide (ses 36 mesures sont toutes les mesures « sans basse » du sous-ensemble). Il n'y a donc en pratique que 9 solos exploitables et aucune mesure réellement en 6/8. Un solo a 2 mesures en 5/4 (écartées).
- Trop peu de mesures (294, 20 min) pour toute part conditionnelle (par contexte d'approche, par temps) ; les IC par solo sur 8–9 solos restent larges (arrivée sur la basse : 55 %, IC 42–70 %, compatible avec les 41 % du swing : on ne peut pas dire que la ballade diffère).
- Enregistrements de 1945 à 1994 et styles mêlés (post-bop 6, cool 2, bebop 1, swing 1) : pas un style de ballade homogène.

## Exploitable pour le moteur / non exploitable

- Ordre de grandeur de la marche de basse d'une ballade lente : parts d'approche aucune / chromatique / diatonique, notes de passage (note d'accord largement majoritaire), répétitions de hauteur (24 %), intervalle médian de 2 demi-tons, p90 de 8, registre de 31 à 51 (MIDI, p1–p99).
- Rythme harmonique : 61 % de mesures à un accord, 32 % à deux (le changement tombe surtout au 1ᵉʳ ou au 3ᵉ temps).
- NON exploitable : les effectifs ne permettent aucun réglage par classe de tempo ni par forme ; les valeurs sont des indications, pas des cibles de test.
- Exploitables : parts et centiles de la marche de basse au temps (arrivées, approches du 4ᵉ temps, notes de passage, intervalles, registre), rythme harmonique (accords par mesure), motifs de répétition de hauteur par mesure, tempos et formes, avec leurs IC par solo.
- Non exploitables : tout ce qui est plus fin que la noire (croches, anticipations, durées réelles des notes), les silences de basse, la dynamique et les timbres, les phrases ou suites de notes (non conservées).
- Un indicateur dont l'IC est absent ou très large (voir le tableau) ne sert pas de cible chiffrée.
