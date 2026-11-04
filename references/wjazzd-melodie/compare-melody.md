# Distance de la mélodie générée à WJazzD (swing)

Référence : WJazzD 2.1 (base 2.2, publiée le 2018-02-08) (references/wjazzd-melodie/measures-melody.json), 348 solos, 26086 mesures, 124348 attaques.

Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus). Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0).

Commande : `python -m harmonium_lab.backing.melody_compare --truth /tmp/h019-e12/t/old1.json --truth /tmp/h019-e12/t/old2.json --truth /tmp/h019-e12/t/old3.json --truth /tmp/h019-e12/t/old4.json --truth /tmp/h019-e12/t/old5.json --truth /tmp/h019-e12/t/old6.json --truth /tmp/h019-e12/t/old7.json --truth /tmp/h019-e12/t/old8.json --label bouche_trou --truth /tmp/h019-e12/t/new1.json --truth /tmp/h019-e12/t/new2.json --truth /tmp/h019-e12/t/new3.json --truth /tmp/h019-e12/t/new4.json --truth /tmp/h019-e12/t/new5.json --truth /tmp/h019-e12/t/new6.json --truth /tmp/h019-e12/t/new7.json --truth /tmp/h019-e12/t/new8.json --label banque_swing --truth /tmp/h019-e12/t/lvl1-1.json --truth /tmp/h019-e12/t/lvl1-2.json --truth /tmp/h019-e12/t/lvl1-3.json --truth /tmp/h019-e12/t/lvl1-4.json --truth /tmp/h019-e12/t/lvl1-5.json --truth /tmp/h019-e12/t/lvl1-6.json --truth /tmp/h019-e12/t/lvl1-7.json --truth /tmp/h019-e12/t/lvl1-8.json --label niveau1 --truth /tmp/h019-e12/t/lvl2-1.json --truth /tmp/h019-e12/t/lvl2-2.json --truth /tmp/h019-e12/t/lvl2-3.json --truth /tmp/h019-e12/t/lvl2-4.json --truth /tmp/h019-e12/t/lvl2-5.json --truth /tmp/h019-e12/t/lvl2-6.json --truth /tmp/h019-e12/t/lvl2-7.json --truth /tmp/h019-e12/t/lvl2-8.json --label niveau2 --truth /tmp/h019-e12/t/lvl3-1.json --truth /tmp/h019-e12/t/lvl3-2.json --truth /tmp/h019-e12/t/lvl3-3.json --truth /tmp/h019-e12/t/lvl3-4.json --truth /tmp/h019-e12/t/lvl3-5.json --truth /tmp/h019-e12/t/lvl3-6.json --truth /tmp/h019-e12/t/lvl3-7.json --truth /tmp/h019-e12/t/lvl3-8.json --label niveau3 --level niveau1=1 --level niveau2=2 --level niveau3=3 --level banque_swing=3 -o references/wjazzd-melodie/compare-melody.json --markdown`

Généré :
- `bouche_trou` : 8 fichier(s), 1408 mesures, 11208 attaques (0 sur un pas impair ou un créneau pris)
- `banque_swing` : 8 fichier(s), 1408 mesures, 6884 attaques (0 sur un pas impair ou un créneau pris)
- `niveau1` : 8 fichier(s), 1408 mesures, 3838 attaques (0 sur un pas impair ou un créneau pris)
- `niveau2` : 8 fichier(s), 1408 mesures, 4019 attaques (0 sur un pas impair ou un créneau pris)
- `niveau3` : 8 fichier(s), 1408 mesures, 6134 attaques (0 sur un pas impair ou un créneau pris)

| famille | critère | d(bouche_trou) | d(banque_swing) | d(niveau1) | d(niveau2) | d(niveau3) |
|---|---|---|---|---|---|---|
| intervals | interval_histogram | 0.494 | 0.326 | 0.376 | 0.400 | 0.329 |
| intervals | cross_bar_interval_histogram | 0.571 | 0.254 | 0.428 | 0.273 | 0.363 |
| intervals | interval_repeat_share | 0.321 | 0.015 | 0.044 | 0.007 | 0.047 |
| intervals | interval_keep_direction_share | 0.118 | 0.152 | 0.163 | 0.188 | 0.172 |
| intervals | biggest_leap_percentiles | 0.292 | 0.146 | 0.333 | 0.271 | 0.229 |
| rhythm | attacks_per_bar | 0.857 | 0.278 | 0.657 | 0.640 | 0.284 |
| rhythm | slot_attack_shares | 0.028 | 0.118 | 0.352 | 0.352 | 0.121 |
| rhythm | legato_duration | 0.233 | 0.194 | 0.772 | 0.772 | 0.275 |
| rhythm | anticipation_share | 0.416 | 0.208 | 0.579 | 0.579 | 0.216 |
| chord | strong_beat_relations | 0.489 | 0.475 | 0.141 | 0.144 | 0.164 |
| chord | beat_relations | 0.473 | 0.473 | 0.141 | 0.130 | 0.137 |
| chord | offbeat_relations | 0.523 | 0.508 | 0.343 | 0.228 | 0.136 |
| chord | strong_beat_chord_share | 0.470 | 0.470 | 0.014 | 0.016 | 0.032 |
| chord | offbeat_chord_share | 0.508 | 0.508 | 0.268 | 0.001 | 0.046 |
| register | register_percentiles | 0.472 | 0.315 | 0.407 | 0.407 | 0.343 |
| register | ambitus_percentiles | 0.375 | 0.168 | 0.458 | 0.396 | 0.250 |
| phrasing | phrase_length_beats | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| phrasing | silent_beats_share | 0.198 | 0.198 | 0.198 | 0.198 | 0.198 |
| **agrégée** | moyenne des critères | **0.435** | **0.323** | **0.371** | **0.333** | **0.241** |

Par famille : `bouche_trou` : chord 0.493, intervals 0.359, phrasing 0.599, register 0.424, rhythm 0.383 ; `banque_swing` : chord 0.487, intervals 0.179, phrasing 0.599, register 0.241, rhythm 0.200 ; `niveau1` : chord 0.181, intervals 0.269, phrasing 0.599, register 0.433, rhythm 0.590 ; `niveau2` : chord 0.104, intervals 0.228, phrasing 0.599, register 0.402, rhythm 0.586 ; `niveau3` : chord 0.103, intervals 0.228, phrasing 0.599, register 0.296, rhythm 0.224

Valeurs comparées (référence puis étiquettes) :

| critère | référence | bouche_trou | banque_swing | niveau1 | niveau2 | niveau3 |
|---|---|---|---|---|---|---|
| interval_histogram | -1=0.11 -10=0.00 -11=0.00 -12=0.00 -2=0.14 -3=0.10 -4=0.06 -5=0.04 -6=0.01 -7=0.02 -8=0.01 -9=0.01 0=0.07 1=0.11 10=0.00 11=0.00 12=0.00 2=0.12 3=0.08 4=0.04 5=0.04 6=0.01 7=0.02 8=0.01 9=0.01 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.00 -4=0.06 -3=0.17 -2=0.04 -1=0.00 0=0.39 1=0.00 2=0.10 3=0.14 4=0.09 5=0.00 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.01 -11=0.00 -10=0.01 -9=0.00 -8=0.01 -7=0.04 -6=0.03 -5=0.09 -4=0.07 -3=0.13 -2=0.06 -1=0.01 0=0.09 1=0.00 2=0.07 3=0.10 4=0.08 5=0.07 6=0.03 7=0.04 8=0.01 9=0.02 10=0.00 11=0.00 12=0.02 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.00 -4=0.14 -3=0.11 -2=0.20 -1=0.01 0=0.11 1=0.01 2=0.13 3=0.12 4=0.17 5=0.00 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.11 -4=0.14 -3=0.06 -2=0.10 -1=0.01 0=0.08 1=0.01 2=0.16 3=0.06 4=0.12 5=0.16 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.05 -6=0.01 -5=0.09 -4=0.10 -3=0.10 -2=0.13 -1=0.00 0=0.02 1=0.00 2=0.15 3=0.07 4=0.11 5=0.11 6=0.01 7=0.05 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 |
| cross_bar_interval_histogram | -1=0.15 -10=0.00 -11=0.00 -12=0.00 -2=0.13 -3=0.08 -4=0.05 -5=0.03 -6=0.01 -7=0.02 -8=0.01 -9=0.01 0=0.06 1=0.13 10=0.00 11=0.00 12=0.00 2=0.10 3=0.08 4=0.04 5=0.04 6=0.01 7=0.02 8=0.01 9=0.01 | -12=0.00 -11=0.01 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.03 -4=0.16 -3=0.01 -2=0.03 -1=0.31 0=0.35 1=0.09 2=0.01 3=0.00 4=0.00 5=0.00 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.01 -11=0.01 -10=0.01 -9=0.01 -8=0.01 -7=0.04 -6=0.01 -5=0.03 -4=0.08 -3=0.03 -2=0.11 -1=0.08 0=0.18 1=0.13 2=0.05 3=0.07 4=0.08 5=0.07 6=0.00 7=0.00 8=0.01 9=0.00 10=0.01 11=0.00 12=0.00 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.00 -4=0.13 -3=0.12 -2=0.12 -1=0.03 0=0.24 1=0.01 2=0.11 3=0.13 4=0.11 5=0.00 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.00 -6=0.00 -5=0.11 -4=0.05 -3=0.08 -2=0.16 -1=0.08 0=0.19 1=0.04 2=0.09 3=0.08 4=0.05 5=0.06 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 | -12=0.00 -11=0.00 -10=0.00 -9=0.00 -8=0.00 -7=0.10 -6=0.00 -5=0.03 -4=0.05 -3=0.06 -2=0.17 -1=0.01 0=0.23 1=0.04 2=0.12 3=0.13 4=0.03 5=0.02 6=0.00 7=0.02 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 |
| interval_repeat_share | 0.070 | 0.390 | 0.085 | 0.113 | 0.077 | 0.023 |
| interval_keep_direction_share | 0.554 | 0.672 | 0.402 | 0.392 | 0.367 | 0.382 |
| biggest_leap_percentiles | p10=2.00 p50=4.00 p90=9.00 p99=14.00 | p10=3.00 p50=4.00 p90=4.00 p99=6.00 | p10=4.00 p50=6.00 p90=12.00 p99=14.00 | p10=2.00 p50=3.00 p90=4.00 p99=4.00 | p10=2.00 p50=4.00 p90=5.00 p99=5.00 | p10=3.00 p50=5.00 p90=7.00 p99=7.00 |
| attacks_per_bar | 0=0.05 1=0.05 2=0.08 3=0.12 4=0.14 5=0.14 6=0.15 7=0.13 8=0.14 | 0=0.00 1=0.01 2=0.00 3=0.00 4=0.00 5=0.00 6=0.00 7=0.00 8=0.99 | 0=0.00 1=0.01 2=0.02 3=0.18 4=0.19 5=0.25 6=0.20 7=0.14 8=0.01 | 0=0.00 1=0.04 2=0.30 3=0.56 4=0.11 5=0.00 6=0.00 7=0.00 8=0.00 | 0=0.00 1=0.02 2=0.27 3=0.55 4=0.16 5=0.00 6=0.00 7=0.00 8=0.00 | 0=0.00 1=0.01 2=0.08 3=0.23 4=0.22 5=0.22 6=0.16 7=0.07 8=0.00 |
| slot_attack_shares | 0=0.13 1=0.11 2=0.13 3=0.12 4=0.14 5=0.12 6=0.13 7=0.12 | 0=0.13 1=0.12 2=0.12 3=0.12 4=0.12 5=0.12 6=0.12 7=0.12 | 0=0.20 1=0.10 2=0.12 3=0.11 4=0.19 5=0.09 6=0.12 7=0.08 | 0=0.37 1=0.00 2=0.14 3=0.05 4=0.20 5=0.07 6=0.17 7=0.00 | 0=0.35 1=0.00 2=0.16 3=0.06 4=0.20 5=0.06 6=0.17 7=0.00 | 0=0.23 1=0.08 2=0.12 3=0.12 4=0.17 5=0.09 6=0.11 7=0.08 |
| legato_duration | 1=0.77 2=0.14 3=0.04 4=0.02 5=0.01 6=0.01 7=0.00 8=0.00 | 1=1.00 2=0.00 3=0.00 4=0.00 5=0.00 6=0.00 7=0.00 8=0.00 | 1=0.59 2=0.25 3=0.09 4=0.06 5=0.00 6=0.00 7=0.00 8=0.00 | 1=0.00 2=0.53 3=0.17 4=0.22 5=0.04 6=0.03 7=0.00 8=0.02 | 1=0.00 2=0.57 3=0.17 4=0.19 5=0.04 6=0.02 7=0.00 8=0.01 | 1=0.50 2=0.29 3=0.11 4=0.07 5=0.02 6=0.00 7=0.00 8=0.00 |
| anticipation_share | 0.579 | 0.994 | 0.371 | 0.000 | 0.000 | 0.362 |
| strong_beat_relations | chromatic=0.21 fifth=0.14 root=0.15 scale=0.26 seventh=0.09 third=0.13 tone=0.02 | root=0.29 third=0.24 fifth=0.26 seventh=0.21 tone=0.00 scale=0.00 chromatic=0.00 | root=0.35 third=0.30 fifth=0.19 seventh=0.15 tone=0.01 scale=0.00 chromatic=0.00 | root=0.16 third=0.09 fifth=0.13 seventh=0.10 tone=0.02 scale=0.37 chromatic=0.12 | root=0.20 third=0.10 fifth=0.12 seventh=0.07 tone=0.03 scale=0.35 chromatic=0.14 | root=0.23 third=0.09 fifth=0.10 seventh=0.12 tone=0.03 scale=0.31 chromatic=0.13 |
| beat_relations | chromatic=0.21 fifth=0.14 root=0.14 scale=0.26 seventh=0.09 third=0.13 tone=0.02 | root=0.27 third=0.35 fifth=0.20 seventh=0.14 tone=0.03 scale=0.00 chromatic=0.00 | root=0.31 third=0.33 fifth=0.18 seventh=0.15 tone=0.03 scale=0.00 chromatic=0.00 | root=0.16 third=0.09 fifth=0.13 seventh=0.09 tone=0.02 scale=0.39 chromatic=0.12 | root=0.17 third=0.10 fifth=0.16 seventh=0.06 tone=0.02 scale=0.35 chromatic=0.14 | root=0.18 third=0.10 fifth=0.12 seventh=0.11 tone=0.03 scale=0.34 chromatic=0.13 |
| offbeat_relations | chromatic=0.24 fifth=0.14 root=0.14 scale=0.27 seventh=0.09 third=0.11 tone=0.02 | root=0.34 third=0.38 fifth=0.19 seventh=0.08 tone=0.02 scale=0.00 chromatic=0.00 | root=0.33 third=0.26 fifth=0.19 seventh=0.18 tone=0.04 scale=0.00 chromatic=0.00 | root=0.28 third=0.06 fifth=0.11 seventh=0.28 tone=0.03 scale=0.13 chromatic=0.11 | root=0.14 third=0.08 fifth=0.11 seventh=0.13 tone=0.04 scale=0.44 chromatic=0.06 | root=0.17 third=0.09 fifth=0.16 seventh=0.10 tone=0.02 scale=0.34 chromatic=0.12 |
| strong_beat_chord_share | 0.530 | 1.000 | 1.000 | 0.516 | 0.515 | 0.562 |
| offbeat_chord_share | 0.492 | 1.000 | 1.000 | 0.760 | 0.491 | 0.538 |
| register_percentiles | p1=49.00 p10=56.00 p25=61.00 p5=53.00 p50=65.00 p75=70.00 p90=75.00 p95=77.00 p99=83.00 | p1=62.00 p5=63.00 p10=64.00 p25=67.00 p50=71.00 p75=74.00 p90=77.00 p95=79.00 p99=82.00 | p1=55.00 p5=58.00 p10=60.00 p25=62.00 p50=65.00 p75=68.00 p90=71.00 p95=73.00 p99=75.00 | p1=55.00 p5=58.00 p10=60.00 p25=62.00 p50=65.00 p75=67.00 p90=68.00 p95=70.00 p99=72.00 | p1=55.00 p5=58.00 p10=59.00 p25=62.00 p50=64.00 p75=67.00 p90=68.20 p95=70.00 p99=71.82 | p1=55.00 p5=58.00 p10=60.00 p25=62.00 p50=65.00 p75=68.00 p90=70.00 p95=72.00 p99=74.00 |
| ambitus_percentiles | p10=2.00 p50=7.00 p90=13.00 p99=20.00 | p10=9.00 p50=11.00 p90=12.00 p99=14.00 | p10=4.00 p50=9.00 p90=12.00 p99=16.93 | p10=2.00 p50=4.00 p90=6.00 p99=7.00 | p10=2.00 p50=5.00 p90=7.00 p99=9.00 | p10=4.00 p50=7.00 p90=11.00 p99=12.00 |
| phrase_length_beats | p10=1.50 p25=2.50 p50=5.50 p75=10.00 p90=16.50 | p10=701.00 p25=701.00 p50=701.00 p75=701.00 p90=701.00 | p10=701.00 p25=701.00 p50=701.00 p75=701.00 p90=701.00 | p10=701.00 p25=701.00 p50=701.00 p75=701.00 p90=701.00 | p10=701.00 p25=701.00 p50=701.00 p75=701.00 p90=701.00 | p10=701.00 p25=701.00 p50=701.00 p75=701.00 p90=701.00 |
| silent_beats_share | 0.202 | 0.004 | 0.004 | 0.004 | 0.004 | 0.004 |

Conformité aux bornes de difficulté E10 :

| étiquette | niveau | mesures | hors bornes | saut | attaques | durée | ambitus | pires (saut / attaques / durée / ambitus) |
|---|---|---|---|---|---|---|---|---|
| banque_swing | 3 | 1400 | 461 | 454 | 0 | 0 | 86 | 21 / 8 / 1 / 22 |
| niveau1 | 1 | 1400 | 0 | 0 | 0 | 0 | 0 | 4 / 4 / 2 / 7 |
| niveau2 | 2 | 1400 | 0 | 0 | 0 | 0 | 0 | 5 / 4 / 2 / 9 |
| niveau3 | 3 | 1400 | 0 | 0 | 0 | 0 | 0 | 7 / 8 / 1 / 12 |
