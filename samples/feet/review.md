# Revue des échantillons de pieds (SK1) — 2026-10-20

20 enregistrements Freesound, tous **CC0-1.0** (sélection via recherche
filtrée `license:"Creative Commons 0"`, badge « Creative Commons 0 »
vérifié par résultat ; page source citée par fichier dans
`manifest.jsonl`). Prévisualisations HQ (`-hq.mp3`, 128 kb/s) :
suffisantes pour des placeholders appelés à être remplacés par les
enregistrements du propriétaire. Mesures : attaques `librosa`
(`delta=0.2`), centroïde et rapport d'énergie 70–400 Hz / 2–9 kHz par
fenêtre de 0,3 s.

## Retenus (8 frappes, 8 sources)

| Rôle | Source (Freesound / auteur) | t | Centroïde | Grave/aigu | Pourquoi |
|---|---|---|---|---|---|
| talon | Thump 4 / stewadosan (841145) | 0,13 s | 770 Hz | 9,3 | le plus sourd du lot |
| talon | Footsteps on a wooden floor / doctorphil (536770) | 1,61 s | 2209 Hz | 6,3 | pas mat, isolé (gap 0,8 s) |
| talon | Heels fast pace / ralph.whitehead (565703) | 4,33 s | 473 Hz | 32 | talon très mat (titre « heels » mais mesure grave) |
| talon | Theatre stomping / wolfdoctor (555116) | 10,02 s | 991 Hz | 8,8 | claque de théâtre, isolée (gap 6,3 s) |
| pointe | Footsteps tap / gpag1 (392482) | 0,15 s | 3180 Hz | 0,14 | claquettes, 9 frappes propres |
| pointe | sapateio1 / Escola_ORT (632070) | 6,28 s | 2571 Hz | 0,17 | sapateado brésilien, sec |
| pointe | High heels on wood / vicleb (712874) | 1,86 s | 3409 Hz | 0,10 | le clic le plus marqué, pic 0,82 |
| pointe | foot stompin / itinerantmonk108 (740039) | 0,67 s | 7285 Hz | 0,48 | claque brillante (titre « stomp » mais mesure aiguë → pointe) |

Surprises assumées : 565703 (« heels ») est le talon le plus grave,
740039 (« stompin ») la pointe la plus brillante. Le rôle suit la
mesure, pas le titre.

- 464125 (takeabeat, Stomping on wood) : 30 frappes régulières mais
  réverbération claire de la pièce — grave/aigu 0,6–1,0 après découpe
  complète contre 5–20 pour les talons retenus (secours écarté).

- 707566 (lenayrossouw), 766212 (kgopong) : pic ≤ 0,025, SNR trop
  faible pour une normalisation propre (artefacts mp3 amplifiés).
- 273416 (sturmankin, highheels) : alternance talon/pointe dans le
  même fichier, attaques à < 0,2 s d'écart — indécoupable proprement.
- 389792 (krnash, barefeet) : claques brillantes correctes mais
  redondantes avec les pointes retenues (secours pointe).
- 119914 (ftpalad), 459970 (florianreichelt), 463670 (alec_mackay),
  523273 (MrFossy), 536770 (doctorphil), 543685 (Nox_Sound),
  753292 (Vrymaa), 784295 (dilly_deelin) : exploitables (secours
  talon/pointe), écartés pour limiter à 8 sources distinctes.
- Crissements de plancher (ex. 523273 t≈1,8 s, centroïde ~7–9 kHz) :
  exclus frappe par frappe — un crissement tonal ne fait pas un pied.

## Point d'entrée des enregistrements du propriétaire

Déposer des WAV (44,1 kHz mono de préférence, sinon convertis) dans
`samples/feet/own/heel/` et/ou `samples/feet/own/toe/`, un fichier par
variante. Au prochain `feet-prepare`, le rôle concerné est reconstruit
depuis ces fichiers (même découpe/normalisation) et les libres sont
écartés pour ce rôle — sans changer le code ni les noms de sortie
(`prepared/{heel,toe}/NN.wav`, banque identique).
