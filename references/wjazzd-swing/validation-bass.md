# Distance de la basse générée à WJazzD (swing)

Référence : Weimar Jazz Database (WJazzD) — WJazzD 2.1 (base 2.2, publiée le 2018-02-08) (references/wjazzd-swing/measures-bass.json), 361 solos, 23224 mesures valides.

Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus). Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0).

Commande : `python -m harmonium_lab.backing.bass_compare --truth target/backing_truth/wjazzd_swing_b88_s1.json --truth target/backing_truth/wjazzd_swing_b88_s2.json --truth target/backing_truth/wjazzd_swing_b88_s3.json --truth target/backing_truth/wjazzd_swing_b88_s4.json --truth target/backing_truth/wjazzd_swing_b88_s5.json --truth target/backing_truth/wjazzd_swing_b88_s6.json --truth target/backing_truth/wjazzd_swing_b88_s7.json --truth target/backing_truth/wjazzd_swing_b88_s8.json --label wjazzd_swing --truth target/backing_truth/grille_accompagnee_b88_s1.json --truth target/backing_truth/grille_accompagnee_b88_s2.json --truth target/backing_truth/grille_accompagnee_b88_s3.json --truth target/backing_truth/grille_accompagnee_b88_s4.json --truth target/backing_truth/grille_accompagnee_b88_s5.json --truth target/backing_truth/grille_accompagnee_b88_s6.json --truth target/backing_truth/grille_accompagnee_b88_s7.json --truth target/backing_truth/grille_accompagnee_b88_s8.json --label grille_accompagnee --reference /Users/william.quintal/orca/workspaces/harmonium_lab/e7-wjazzd-swing/references/wjazzd-swing/measures-bass.json -o references/wjazzd-swing/validation-bass.json --group all --group blues --group other_forms --group reliable --markdown`

Généré :
- `wjazzd_swing` : 8 fichier(s), 696 mesures valides sur 704 (sans basse complète : 8, accord non analysé : 0)
- `grille_accompagnee` : 8 fichier(s), 1016 mesures valides sur 1024 (sans basse complète : 8, accord non analysé : 0)

## Groupe de référence `all` (361 solos, 23224 mesures valides)

| famille | critère | d(wjazzd_swing) | d(grille_accompagnee) |
|---|---|---|---|
| arrival | arrival_classes_at_change | 0.588 | 0.588 |
| arrival | arrival_bass_share_at_change | 0.588 | 0.588 |
| arrival | bar_start_no_change_classes | 0.767 | 0.767 |
| arrival | bar_start_no_change_bass_share | 0.767 | 0.767 |
| approach | approach_weights | 0.110 | 0.493 |
| approach | approach_weights_bar_change | 0.128 | 0.531 |
| approach | approach_weights_mid_change | 0.112 | 0.448 |
| approach | approach_classes | 0.221 | 0.493 |
| approach | approach_distance | 0.215 | 0.518 |
| approach | approach_above_share | 0.202 | 0.234 |
| approach | approach_same_side_share | 0.192 | 0.329 |
| passage | passage_classes | 0.116 | 0.067 |
| passage | passage_engine_classes | 0.158 | 0.097 |
| intervals | interval_histogram | 0.315 | 0.333 |
| intervals | interval_repeat_share | 0.167 | 0.181 |
| intervals | interval_keep_direction_share | 0.105 | 0.065 |
| intervals | interval_toward_target_share | 0.017 | 0.116 |
| intervals | interval_percentiles | 0.117 | 0.233 |
| register | register_percentiles | 0.128 | 0.173 |
| register | register_percentiles_relative_to_tonic | 0.214 | 0.277 |
| register | walk_window | 0.125 | 0.292 |
| register | arrival_window | 0.000 | 0.000 |
| harmonic_rhythm | chords_per_bar | 0.340 | 0.109 |
| harmonic_rhythm | chord_duration | 0.389 | 0.301 |
| harmonic_rhythm | change_beat | 0.177 | 0.155 |
| **agrégée** | moyenne des critères | **0.250** | **0.326** |

Par famille : `wjazzd_swing` : approach 0.169, arrival 0.678, harmonic_rhythm 0.302, intervals 0.144, passage 0.137, register 0.117 ; `grille_accompagnee` : approach 0.435, arrival 0.678, harmonic_rhythm 0.188, intervals 0.186, passage 0.082, register 0.185

Valeurs comparées (référence puis étiquettes) :

| critère | référence | wjazzd_swing | grille_accompagnee |
|---|---|---|---|
| arrival_classes_at_change | bass=0.41 fifth=0.11 other=0.27 root=0.00 seventh=0.10 third=0.10 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.412 | 1.000 | 1.000 |
| bar_start_no_change_classes | bass=0.23 fifth=0.16 other=0.38 root=0.00 seventh=0.10 third=0.13 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.233 | 1.000 | 1.000 |
| approach_weights | chromatic=0.21 diatonic=0.19 none=0.59 | none=0.49 chromatic=0.20 diatonic=0.30 | none=0.10 chromatic=0.68 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.24 diatonic=0.18 none=0.57 | none=0.47 chromatic=0.22 diatonic=0.31 | none=0.04 chromatic=0.59 diatonic=0.37 |
| approach_weights_mid_change | chromatic=0.19 diatonic=0.22 none=0.59 | none=0.47 chromatic=0.19 diatonic=0.34 | none=0.19 chromatic=0.64 diatonic=0.17 |
| approach_classes | chord_tone=0.20 chromatic_above=0.10 chromatic_below=0.11 diatonic=0.19 fifth=0.07 other=0.26 same=0.06 | same=0.06 chromatic_below=0.16 chromatic_above=0.04 diatonic=0.30 fifth=0.13 chord_tone=0.18 other=0.12 | same=0.01 chromatic_below=0.50 chromatic_above=0.18 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.06 1=0.21 10=0.02 11=0.03 12=0.01 2=0.14 3=0.08 4=0.09 5=0.13 6=0.07 7=0.07 8=0.03 9=0.02 >12=0.04 | 0=0.06 1=0.20 2=0.23 3=0.08 4=0.03 5=0.17 6=0.00 7=0.13 8=0.02 9=0.04 10=0.03 11=0.02 12=0.00 >12=0.00 | 0=0.01 1=0.68 2=0.20 3=0.04 4=0.01 5=0.05 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.526 | 0.324 | 0.292 |
| approach_same_side_share | 0.661 | 0.854 | 0.991 |
| passage_classes | chord_tone=0.48 chromatic=0.27 scale_step=0.25 | chord_tone=0.49 scale_step=0.36 chromatic=0.16 | chord_tone=0.52 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.48 chromatic=0.29 scale_step=0.23 | chord_tone=0.58 scale_step=0.29 chromatic=0.14 | chord_tone=0.54 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.20 1=0.22 10=0.02 11=0.02 12=0.02 2=0.14 3=0.08 4=0.07 5=0.08 6=0.05 7=0.06 8=0.02 9=0.02 >12=0.02 | 0=0.03 1=0.20 2=0.38 3=0.06 4=0.05 5=0.11 6=0.01 7=0.08 8=0.02 9=0.03 10=0.02 11=0.01 12=0.00 >12=0.00 | 0=0.01 1=0.35 2=0.26 3=0.07 4=0.12 5=0.11 6=0.03 7=0.03 8=0.00 9=0.01 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.196 | 0.029 | 0.015 |
| interval_keep_direction_share | 0.423 | 0.528 | 0.488 |
| interval_toward_target_share | 0.444 | 0.428 | 0.328 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=5.00 p90=7.00 p95=9.00 p99=10.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=33.00 p25=38.00 p5=34.75 p50=42.00 p75=45.00 p95=49.00 p99=52.00 | p1=33.00 p5=34.00 p25=38.00 p50=41.00 p75=43.00 p95=46.00 p99=48.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=48.74 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=33.00 p5=28.00 p50=37.00 p75=40.00 p95=45.00 p99=49.00 | p1=28.00 p5=29.00 p25=33.00 p50=36.00 p75=38.00 p95=41.00 p99=43.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=43.74 |
| walk_window | high=50.00 low=33.00 | low=34.00 high=48.00 | low=36.00 high=46.00 |
| arrival_window | high=46.00 low=36.00 | low=36.00 high=46.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.76 2=0.22 3=0.01 4=0.00 | 1=0.44 2=0.56 3=0.00 4=0.00 | 1=0.69 2=0.19 3=0.12 4=0.00 |
| chord_duration | 1=0.03 2=0.45 3=0.00 4=0.39 5=0.00 6=0.00 7=0.00 8=0.10 >8=0.02 | 1=0.00 2=0.81 3=0.00 4=0.06 5=0.00 6=0.02 7=0.00 8=0.12 >8=0.00 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.75 beat3=0.23 other=0.02 | beat1=0.59 beat3=0.41 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |

## Groupe de référence `blues` (87 solos, 5725 mesures valides)

| famille | critère | d(wjazzd_swing) | d(grille_accompagnee) |
|---|---|---|---|
| arrival | arrival_classes_at_change | 0.583 | 0.583 |
| arrival | arrival_bass_share_at_change | 0.583 | 0.583 |
| arrival | bar_start_no_change_classes | 0.785 | 0.785 |
| arrival | bar_start_no_change_bass_share | 0.785 | 0.785 |
| approach | approach_weights | 0.108 | 0.476 |
| approach | approach_weights_bar_change | 0.120 | 0.509 |
| approach | approach_weights_mid_change | 0.157 | 0.389 |
| approach | approach_classes | 0.248 | 0.476 |
| approach | approach_distance | 0.274 | 0.508 |
| approach | approach_above_share | 0.175 | 0.207 |
| approach | approach_same_side_share | 0.216 | 0.353 |
| passage | passage_classes | 0.149 | 0.100 |
| passage | passage_engine_classes | 0.194 | 0.134 |
| intervals | interval_histogram | 0.314 | 0.304 |
| intervals | interval_repeat_share | 0.132 | 0.147 |
| intervals | interval_keep_direction_share | 0.102 | 0.062 |
| intervals | interval_toward_target_share | 0.046 | 0.145 |
| intervals | interval_percentiles | 0.117 | 0.233 |
| register | register_percentiles | 0.155 | 0.217 |
| register | register_percentiles_relative_to_tonic | 0.200 | 0.263 |
| register | walk_window | 0.167 | 0.333 |
| register | arrival_window | 0.083 | 0.083 |
| harmonic_rhythm | chords_per_bar | 0.483 | 0.225 |
| harmonic_rhythm | chord_duration | 0.608 | 0.483 |
| harmonic_rhythm | change_beat | 0.304 | 0.298 |
| **agrégée** | moyenne des critères | **0.283** | **0.347** |

Par famille : `wjazzd_swing` : approach 0.185, arrival 0.684, harmonic_rhythm 0.465, intervals 0.142, passage 0.172, register 0.151 ; `grille_accompagnee` : approach 0.417, arrival 0.684, harmonic_rhythm 0.335, intervals 0.178, passage 0.117, register 0.224

Valeurs comparées (référence puis étiquettes) :

| critère | référence | wjazzd_swing | grille_accompagnee |
|---|---|---|---|
| arrival_classes_at_change | bass=0.42 fifth=0.14 other=0.24 root=0.00 seventh=0.10 third=0.10 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.417 | 1.000 | 1.000 |
| bar_start_no_change_classes | bass=0.21 fifth=0.15 other=0.37 root=0.00 seventh=0.10 third=0.17 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.215 | 1.000 | 1.000 |
| approach_weights | chromatic=0.23 diatonic=0.20 none=0.57 | none=0.49 chromatic=0.20 diatonic=0.30 | none=0.10 chromatic=0.68 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.26 diatonic=0.19 none=0.55 | none=0.47 chromatic=0.22 diatonic=0.31 | none=0.04 chromatic=0.59 diatonic=0.37 |
| approach_weights_mid_change | chromatic=0.25 diatonic=0.18 none=0.57 | none=0.47 chromatic=0.19 diatonic=0.34 | none=0.19 chromatic=0.64 diatonic=0.17 |
| approach_classes | chord_tone=0.16 chromatic_above=0.10 chromatic_below=0.13 diatonic=0.20 fifth=0.06 other=0.31 same=0.05 | same=0.06 chromatic_below=0.16 chromatic_above=0.04 diatonic=0.30 fifth=0.13 chord_tone=0.18 other=0.12 | same=0.01 chromatic_below=0.50 chromatic_above=0.18 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.05 1=0.23 10=0.02 11=0.03 12=0.01 2=0.14 3=0.09 4=0.12 5=0.10 6=0.08 7=0.06 8=0.02 9=0.02 >12=0.04 | 0=0.06 1=0.20 2=0.23 3=0.08 4=0.03 5=0.17 6=0.00 7=0.13 8=0.02 9=0.04 10=0.03 11=0.02 12=0.00 >12=0.00 | 0=0.01 1=0.68 2=0.20 3=0.04 4=0.01 5=0.05 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.499 | 0.324 | 0.292 |
| approach_same_side_share | 0.638 | 0.854 | 0.991 |
| passage_classes | chord_tone=0.45 chromatic=0.30 scale_step=0.25 | chord_tone=0.49 scale_step=0.36 chromatic=0.16 | chord_tone=0.52 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.44 chromatic=0.33 scale_step=0.23 | chord_tone=0.58 scale_step=0.29 chromatic=0.14 | chord_tone=0.54 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.16 1=0.25 10=0.02 11=0.02 12=0.01 2=0.14 3=0.08 4=0.07 5=0.08 6=0.05 7=0.06 8=0.03 9=0.02 >12=0.03 | 0=0.03 1=0.20 2=0.38 3=0.06 4=0.05 5=0.11 6=0.01 7=0.08 8=0.02 9=0.03 10=0.02 11=0.01 12=0.00 >12=0.00 | 0=0.01 1=0.35 2=0.26 3=0.07 4=0.12 5=0.11 6=0.03 7=0.03 8=0.00 9=0.01 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.162 | 0.029 | 0.015 |
| interval_keep_direction_share | 0.426 | 0.528 | 0.488 |
| interval_toward_target_share | 0.473 | 0.428 | 0.328 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=5.00 p90=7.00 p95=9.00 p99=10.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=32.00 p25=38.00 p5=34.00 p50=42.00 p75=45.00 p95=50.00 p99=53.00 | p1=33.00 p5=34.00 p25=38.00 p50=41.00 p75=43.00 p95=46.00 p99=48.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=48.74 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=32.00 p5=27.00 p50=36.00 p75=39.00 p95=44.00 p99=48.81 | p1=28.00 p5=29.00 p25=33.00 p50=36.00 p75=38.00 p95=41.00 p99=43.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=43.74 |
| walk_window | high=51.00 low=33.00 | low=34.00 high=48.00 | low=36.00 high=46.00 |
| arrival_window | high=46.00 low=34.00 | low=36.00 high=46.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.92 2=0.08 3=0.00 4=0.00 | 1=0.44 2=0.56 3=0.00 4=0.00 | 1=0.69 2=0.19 3=0.12 4=0.00 |
| chord_duration | 1=0.01 2=0.21 3=0.00 4=0.52 5=0.00 6=0.00 7=0.00 8=0.20 >8=0.05 | 1=0.00 2=0.81 3=0.00 4=0.06 5=0.00 6=0.02 7=0.00 8=0.12 >8=0.00 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.89 beat3=0.11 other=0.00 | beat1=0.59 beat3=0.41 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |

## Groupe de référence `other_forms` (274 solos, 17499 mesures valides)

| famille | critère | d(wjazzd_swing) | d(grille_accompagnee) |
|---|---|---|---|
| arrival | arrival_classes_at_change | 0.590 | 0.590 |
| arrival | arrival_bass_share_at_change | 0.590 | 0.590 |
| arrival | bar_start_no_change_classes | 0.759 | 0.759 |
| arrival | bar_start_no_change_bass_share | 0.759 | 0.759 |
| approach | approach_weights | 0.110 | 0.498 |
| approach | approach_weights_bar_change | 0.131 | 0.538 |
| approach | approach_weights_mid_change | 0.112 | 0.453 |
| approach | approach_classes | 0.220 | 0.498 |
| approach | approach_distance | 0.201 | 0.521 |
| approach | approach_above_share | 0.210 | 0.242 |
| approach | approach_same_side_share | 0.185 | 0.322 |
| passage | passage_classes | 0.109 | 0.053 |
| passage | passage_engine_classes | 0.144 | 0.084 |
| intervals | interval_histogram | 0.316 | 0.343 |
| intervals | interval_repeat_share | 0.178 | 0.193 |
| intervals | interval_keep_direction_share | 0.106 | 0.067 |
| intervals | interval_toward_target_share | 0.004 | 0.104 |
| intervals | interval_percentiles | 0.117 | 0.233 |
| register | register_percentiles | 0.131 | 0.170 |
| register | register_percentiles_relative_to_tonic | 0.226 | 0.289 |
| register | walk_window | 0.125 | 0.292 |
| register | arrival_window | 0.000 | 0.000 |
| harmonic_rhythm | chords_per_bar | 0.293 | 0.106 |
| harmonic_rhythm | chord_duration | 0.359 | 0.325 |
| harmonic_rhythm | change_beat | 0.148 | 0.122 |
| **agrégée** | moyenne des critères | **0.245** | **0.326** |

Par famille : `wjazzd_swing` : approach 0.167, arrival 0.674, harmonic_rhythm 0.267, intervals 0.144, passage 0.126, register 0.121 ; `grille_accompagnee` : approach 0.439, arrival 0.674, harmonic_rhythm 0.185, intervals 0.188, passage 0.069, register 0.188

Valeurs comparées (référence puis étiquettes) :

| critère | référence | wjazzd_swing | grille_accompagnee |
|---|---|---|---|
| arrival_classes_at_change | bass=0.41 fifth=0.10 other=0.28 root=0.00 seventh=0.10 third=0.11 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.410 | 1.000 | 1.000 |
| bar_start_no_change_classes | bass=0.24 fifth=0.16 other=0.39 root=0.00 seventh=0.10 third=0.11 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.241 | 1.000 | 1.000 |
| approach_weights | chromatic=0.21 diatonic=0.19 none=0.60 | none=0.49 chromatic=0.20 diatonic=0.30 | none=0.10 chromatic=0.68 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.24 diatonic=0.18 none=0.58 | none=0.47 chromatic=0.22 diatonic=0.31 | none=0.04 chromatic=0.59 diatonic=0.37 |
| approach_weights_mid_change | chromatic=0.18 diatonic=0.23 none=0.59 | none=0.47 chromatic=0.19 diatonic=0.34 | none=0.19 chromatic=0.64 diatonic=0.17 |
| approach_classes | chord_tone=0.21 chromatic_above=0.10 chromatic_below=0.11 diatonic=0.19 fifth=0.07 other=0.25 same=0.06 | same=0.06 chromatic_below=0.16 chromatic_above=0.04 diatonic=0.30 fifth=0.13 chord_tone=0.18 other=0.12 | same=0.01 chromatic_below=0.50 chromatic_above=0.18 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.06 1=0.21 10=0.02 11=0.03 12=0.01 2=0.14 3=0.08 4=0.09 5=0.13 6=0.07 7=0.07 8=0.03 9=0.02 >12=0.03 | 0=0.06 1=0.20 2=0.23 3=0.08 4=0.03 5=0.17 6=0.00 7=0.13 8=0.02 9=0.04 10=0.03 11=0.02 12=0.00 >12=0.00 | 0=0.01 1=0.68 2=0.20 3=0.04 4=0.01 5=0.05 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.534 | 0.324 | 0.292 |
| approach_same_side_share | 0.668 | 0.854 | 0.991 |
| passage_classes | chord_tone=0.49 chromatic=0.26 scale_step=0.25 | chord_tone=0.49 scale_step=0.36 chromatic=0.16 | chord_tone=0.52 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.49 chromatic=0.28 scale_step=0.23 | chord_tone=0.58 scale_step=0.29 chromatic=0.14 | chord_tone=0.54 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.21 1=0.22 10=0.02 11=0.02 12=0.02 2=0.14 3=0.08 4=0.06 5=0.08 6=0.05 7=0.06 8=0.02 9=0.02 >12=0.02 | 0=0.03 1=0.20 2=0.38 3=0.06 4=0.05 5=0.11 6=0.01 7=0.08 8=0.02 9=0.03 10=0.02 11=0.01 12=0.00 >12=0.00 | 0=0.01 1=0.35 2=0.26 3=0.07 4=0.12 5=0.11 6=0.03 7=0.03 8=0.00 9=0.01 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.208 | 0.029 | 0.015 |
| interval_keep_direction_share | 0.422 | 0.528 | 0.488 |
| interval_toward_target_share | 0.432 | 0.428 | 0.328 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=5.00 p90=7.00 p95=9.00 p99=10.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=33.00 p25=38.00 p5=35.00 p50=42.00 p75=45.00 p95=49.00 p99=52.00 | p1=33.00 p5=34.00 p25=38.00 p50=41.00 p75=43.00 p95=46.00 p99=48.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=48.74 |
| register_percentiles_relative_to_tonic | p1=25.00 p25=33.00 p5=28.00 p50=37.00 p75=41.00 p95=46.00 p99=49.00 | p1=28.00 p5=29.00 p25=33.00 p50=36.00 p75=38.00 p95=41.00 p99=43.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=43.74 |
| walk_window | high=50.00 low=33.00 | low=34.00 high=48.00 | low=36.00 high=46.00 |
| arrival_window | high=46.00 low=36.00 | low=36.00 high=46.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.71 2=0.27 3=0.01 4=0.01 | 1=0.44 2=0.56 3=0.00 4=0.00 | 1=0.69 2=0.19 3=0.12 4=0.00 |
| chord_duration | 1=0.04 2=0.50 3=0.00 4=0.36 5=0.00 6=0.00 7=0.00 8=0.08 >8=0.02 | 1=0.00 2=0.81 3=0.00 4=0.06 5=0.00 6=0.02 7=0.00 8=0.12 >8=0.00 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.71 beat3=0.26 other=0.02 | beat1=0.59 beat3=0.41 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |

## Groupe de référence `reliable` (75 solos, 5192 mesures valides)

| famille | critère | d(wjazzd_swing) | d(grille_accompagnee) |
|---|---|---|---|
| arrival | arrival_classes_at_change | 0.369 | 0.369 |
| arrival | arrival_bass_share_at_change | 0.369 | 0.369 |
| arrival | bar_start_no_change_classes | 0.637 | 0.637 |
| arrival | bar_start_no_change_bass_share | 0.637 | 0.637 |
| approach | approach_weights | 0.135 | 0.458 |
| approach | approach_weights_bar_change | 0.154 | 0.485 |
| approach | approach_weights_mid_change | 0.125 | 0.396 |
| approach | approach_classes | 0.203 | 0.458 |
| approach | approach_distance | 0.242 | 0.473 |
| approach | approach_above_share | 0.209 | 0.241 |
| approach | approach_same_side_share | 0.220 | 0.357 |
| passage | passage_classes | 0.121 | 0.060 |
| passage | passage_engine_classes | 0.076 | 0.058 |
| intervals | interval_histogram | 0.297 | 0.318 |
| intervals | interval_repeat_share | 0.132 | 0.146 |
| intervals | interval_keep_direction_share | 0.080 | 0.040 |
| intervals | interval_toward_target_share | 0.061 | 0.160 |
| intervals | interval_percentiles | 0.117 | 0.233 |
| register | register_percentiles | 0.131 | 0.194 |
| register | register_percentiles_relative_to_tonic | 0.214 | 0.277 |
| register | walk_window | 0.167 | 0.333 |
| register | arrival_window | 0.042 | 0.042 |
| harmonic_rhythm | chords_per_bar | 0.300 | 0.099 |
| harmonic_rhythm | chord_duration | 0.402 | 0.316 |
| harmonic_rhythm | change_beat | 0.163 | 0.127 |
| **agrégée** | moyenne des critères | **0.224** | **0.291** |

Par famille : `wjazzd_swing` : approach 0.184, arrival 0.503, harmonic_rhythm 0.288, intervals 0.137, passage 0.098, register 0.138 ; `grille_accompagnee` : approach 0.410, arrival 0.503, harmonic_rhythm 0.181, intervals 0.179, passage 0.059, register 0.211

Valeurs comparées (référence puis étiquettes) :

| critère | référence | wjazzd_swing | grille_accompagnee |
|---|---|---|---|
| arrival_classes_at_change | bass=0.63 fifth=0.09 other=0.13 root=0.00 seventh=0.07 third=0.07 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.631 | 1.000 | 1.000 |
| bar_start_no_change_classes | bass=0.36 fifth=0.28 other=0.17 root=0.00 seventh=0.09 third=0.09 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.363 | 1.000 | 1.000 |
| approach_weights | chromatic=0.27 diatonic=0.17 none=0.56 | none=0.49 chromatic=0.20 diatonic=0.30 | none=0.10 chromatic=0.68 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.32 diatonic=0.16 none=0.53 | none=0.47 chromatic=0.22 diatonic=0.31 | none=0.04 chromatic=0.59 diatonic=0.37 |
| approach_weights_mid_change | chromatic=0.24 diatonic=0.21 none=0.55 | none=0.47 chromatic=0.19 diatonic=0.34 | none=0.19 chromatic=0.64 diatonic=0.17 |
| approach_classes | chord_tone=0.22 chromatic_above=0.14 chromatic_below=0.14 diatonic=0.17 fifth=0.09 other=0.19 same=0.06 | same=0.06 chromatic_below=0.16 chromatic_above=0.04 diatonic=0.30 fifth=0.13 chord_tone=0.18 other=0.12 | same=0.01 chromatic_below=0.50 chromatic_above=0.18 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.06 1=0.27 10=0.02 11=0.03 12=0.01 2=0.13 3=0.06 4=0.07 5=0.13 6=0.06 7=0.09 8=0.02 9=0.02 >12=0.03 | 0=0.06 1=0.20 2=0.23 3=0.08 4=0.03 5=0.17 6=0.00 7=0.13 8=0.02 9=0.04 10=0.03 11=0.02 12=0.00 >12=0.00 | 0=0.01 1=0.68 2=0.20 3=0.04 4=0.01 5=0.05 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.533 | 0.324 | 0.292 |
| approach_same_side_share | 0.634 | 0.854 | 0.991 |
| passage_classes | chord_tone=0.58 chromatic=0.19 scale_step=0.23 | chord_tone=0.49 scale_step=0.36 chromatic=0.16 | chord_tone=0.52 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.58 chromatic=0.21 scale_step=0.21 | chord_tone=0.58 scale_step=0.29 chromatic=0.14 | chord_tone=0.54 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.16 1=0.23 10=0.02 11=0.02 12=0.02 2=0.13 3=0.07 4=0.07 5=0.09 6=0.05 7=0.07 8=0.03 9=0.02 >12=0.02 | 0=0.03 1=0.20 2=0.38 3=0.06 4=0.05 5=0.11 6=0.01 7=0.08 8=0.02 9=0.03 10=0.02 11=0.01 12=0.00 >12=0.00 | 0=0.01 1=0.35 2=0.26 3=0.07 4=0.12 5=0.11 6=0.03 7=0.03 8=0.00 9=0.01 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.161 | 0.029 | 0.015 |
| interval_keep_direction_share | 0.448 | 0.528 | 0.488 |
| interval_toward_target_share | 0.488 | 0.428 | 0.328 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=5.00 p90=7.00 p95=9.00 p99=10.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=31.00 p25=38.00 p5=34.00 p50=42.00 p75=45.00 p95=48.00 p99=52.00 | p1=33.00 p5=34.00 p25=38.00 p50=41.00 p75=43.00 p95=46.00 p99=48.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=48.74 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=33.00 p5=28.00 p50=37.00 p75=41.00 p95=45.00 p99=48.00 | p1=28.00 p5=29.00 p25=33.00 p50=36.00 p75=38.00 p95=41.00 p99=43.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=43.74 |
| walk_window | high=51.00 low=33.00 | low=34.00 high=48.00 | low=36.00 high=46.00 |
| arrival_window | high=46.00 low=35.00 | low=36.00 high=46.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.71 2=0.26 3=0.02 4=0.01 | 1=0.44 2=0.56 3=0.00 4=0.00 | 1=0.69 2=0.19 3=0.12 4=0.00 |
| chord_duration | 1=0.06 2=0.46 3=0.00 4=0.38 5=0.00 6=0.00 7=0.00 8=0.07 >8=0.01 | 1=0.00 2=0.81 3=0.00 4=0.06 5=0.00 6=0.02 7=0.00 8=0.12 >8=0.00 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.72 beat3=0.25 other=0.03 | beat1=0.59 beat3=0.41 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |
