# Revue des échantillons de pieds (SK1, reprise SK1b) — 2026-10-20

20 enregistrements Freesound, tous **CC0-1.0** (sélection via recherche
filtrée `license:"Creative Commons 0"`, badge « Creative Commons 0 »
vérifié par résultat ; page source citée par fichier dans
`manifest.jsonl`). Prévisualisations HQ (`-hq.mp3`, 128 kb/s) :
suffisantes pour des placeholders appelés à être remplacés par les
enregistrements du propriétaire. Mesures : attaques `librosa`
(`delta=0.2`), centroïde et rapport d'énergie 70–400 Hz / 2–9 kHz.

SK1b : chaque échantillon est une **monofrappe** (début ≤ 5 ms avant
l'attaque, pic < 20 ms, durée ≤ 250 ms, aucune remontée > 30 % du pic
après 25 ms — proéminence `scipy`, qui ignore l'ondulation naturelle
des graves). `feet-prepare` refuse toute frappe non conforme (et nomme
le fichier fautif dans `own/`). Balayage : 113 frappes conformes sur
les 20 sources.

## Retenus (8 frappes, 8 sources)

| Rôle | Source (Freesound / auteur) | t | Pic | Durée | Grave/aigu | Pourquoi |
|---|---|---|---|---|---|---|
| talon | Theatre stomping / wolfdoctor (555116) | 27,11 s | 12 ms | 250 ms | 3,2 | claque mate isolée |
| talon | Footsteps on wood / doctorphil (536770) | 2,40 s | 6 ms | 250 ms | 3,4 | pas mat, gap 0,8 s |
| talon | Hollow wood / florianreichelt (459970) | 6,33 s | 16 ms | 250 ms | 7,5 | le plus sourd sauf 565703 |
| talon | Wood walk mono / Nox_Sound (543685) | 6,84 s | 8 ms | 250 ms | 6,7 | pas rond, gap 1,6 s |
| pointe | sapateio1 / Escola_ORT (632070) | 9,97 s | 10 ms | 250 ms | 0,12 | sapateado sec |
| pointe | Footsteps tap / gpag1 (392482) | 2,16 s | 4 ms | 77 ms | 0,18 | claquette courte et propre |
| pointe | High heels on wood / vicleb (712874) | 13,13 s | 9 ms | 149 ms | 0,22 | clic marqué |
| pointe | foot stompin / itinerantmonk108 (740039) | 0,67 s | 12 ms | 250 ms | 0,96 | claque brillante (titre « stomp » mais mesure aiguë → pointe) |

Le rôle suit la mesure, pas le titre.

## Niveau (mesuré sur `reel_complet`, tiges non normalisées)

Gain `FEET_VEL_SCALE = 0,55` sur les vélocités (`render.py`, option
`--feet-gain`), humanisation déterministe `±12` (graine `FEET_SEED`,
options `--feet-humanize`, `--feet-seed` via `render_midi`) : talon
≈ 55 ± 12 (couches L2/L3), pointe ≈ 38 ± 12 (couches L1/L2).
RMS global : pieds −52,5 dBFS contre violon −43,3 dBFS, soit
**9,2 dB sous le violon** (cible ≥ 8 dB). Pics RMS / 100 ms : −43,7
contre −36,5 dBFS. Sans la banque des pieds, repli percussions GM
(vélocités d'origine, sans gain).

## Écartés (secours dans le manifeste)

- 841145 (stewadosan, Thump 4) : le plus sourd du lot mais frappes à
  < 0,2 s d'écart — aucune ne passe le test monofrappe.
- 565703 (ralph.whitehead) : talons très mats mais marche dense
  (gaps ~0,2 s), une seule frappe conforme — écarté.
- 464125 (takeabeat, Stomping on wood) : 30 frappes régulières mais
  réverbération claire — échos > 30 % après 25 ms partout.
- 707566 (lenayrossouw), 766212 (kgopong) : pic ≤ 0,025, SNR trop
  faible pour une normalisation propre (artefacts mp3 amplifiés).
- 273416 (sturmankin), 389792 (krnash), 119914 (ftpalad),
  463670 (alec_mackay), 523273 (MrFossy), 753292 (Vrymaa),
  784295 (dilly_deelin) : frappes conformes en secours, écartées pour
  limiter à 8 sources distinctes.
- Crissements de plancher (ex. 523273 t≈1,8 s, centroïde ~7–9 kHz) :
  exclus frappe par frappe — un crissement tonal ne fait pas un pied.

## Point d'entrée des enregistrements du propriétaire

Déposer des WAV (44,1 kHz mono de préférence, sinon convertis) dans
`samples/feet/own/heel/` et/ou `samples/feet/own/toe/`, un fichier par
variante. Au prochain `feet-prepare`, le rôle concerné est reconstruit
depuis ces fichiers (même découpe/normalisation) et les libres sont
écartés pour ce rôle — sans changer le code ni les noms de sortie
(`prepared/{heel,toe}/NN.wav`, banque identique).
