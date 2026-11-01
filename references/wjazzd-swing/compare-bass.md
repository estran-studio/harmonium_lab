# Distance de la basse générée à WJazzD (swing)

Référence : Weimar Jazz Database (WJazzD) — WJazzD 2.1 (base 2.2, publiée le 2018-02-08) (references/wjazzd-swing/measures-bass.json), 361 solos, 23224 mesures valides.

Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus). Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0).

Commande : `python -m harmonium_lab.backing.bass_compare --truth target/backing_truth/grille_accompagnee_seed1.json --truth target/backing_truth/grille_accompagnee_seed2.json --truth target/backing_truth/grille_accompagnee_seed3.json --truth target/backing_truth/grille_accompagnee_seed4.json --truth target/backing_truth/grille_accompagnee_seed5.json --truth target/backing_truth/grille_accompagnee_seed6.json --truth target/backing_truth/grille_accompagnee_seed7.json --truth target/backing_truth/grille_accompagnee_seed8.json --label grille_accompagnee --reference references/wjazzd-swing/measures-bass.json --group all --group blues --group reliable -o references/wjazzd-swing/compare-bass.json --markdown`

Généré :
- `grille_accompagnee` : 8 fichier(s), 632 mesures valides sur 632 (sans basse complète : 0, accord non analysé : 0)

## Groupe de référence `all` (361 solos, 23224 mesures valides)

| famille | critère | d(grille_accompagnee) |
|---|---|---|
| arrival | arrival_classes_at_change | 0.588 |
| arrival | arrival_bass_share_at_change | 0.588 |
| arrival | bar_start_no_change_classes | 0.767 |
| arrival | bar_start_no_change_bass_share | 0.767 |
| approach | approach_weights | 0.511 |
| approach | approach_weights_bar_change | 0.542 |
| approach | approach_weights_mid_change | 0.468 |
| approach | approach_classes | 0.511 |
| approach | approach_distance | 0.522 |
| approach | approach_above_share | 0.239 |
| approach | approach_same_side_share | 0.324 |
| passage | passage_classes | 0.060 |
| passage | passage_engine_classes | 0.089 |
| intervals | interval_histogram | 0.329 |
| intervals | interval_repeat_share | 0.184 |
| intervals | interval_keep_direction_share | 0.068 |
| intervals | interval_toward_target_share | 0.119 |
| intervals | interval_percentiles | 0.233 |
| register | register_percentiles | 0.158 |
| register | register_percentiles_relative_to_tonic | 0.262 |
| register | walk_window | 0.253 |
| register | arrival_window | 0.000 |
| harmonic_rhythm | chords_per_bar | 0.105 |
| harmonic_rhythm | chord_duration | 0.298 |
| harmonic_rhythm | change_beat | 0.153 |
| **agrégée** | moyenne des critères | **0.326** |

Par famille : `grille_accompagnee` : approach 0.446, arrival 0.678, harmonic_rhythm 0.185, intervals 0.187, passage 0.074, register 0.168

Valeurs comparées (référence puis étiquettes) :

| critère | référence | grille_accompagnee |
|---|---|---|
| arrival_classes_at_change | bass=0.41 fifth=0.11 other=0.27 root=0.00 seventh=0.10 third=0.10 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.412 | 1.000 |
| bar_start_no_change_classes | bass=0.23 fifth=0.16 other=0.38 root=0.00 seventh=0.10 third=0.13 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.233 | 1.000 |
| approach_weights | chromatic=0.21 diatonic=0.19 none=0.59 | none=0.08 chromatic=0.69 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.24 diatonic=0.18 none=0.57 | none=0.03 chromatic=0.59 diatonic=0.38 |
| approach_weights_mid_change | chromatic=0.19 diatonic=0.22 none=0.59 | none=0.18 chromatic=0.66 diatonic=0.16 |
| approach_classes | chord_tone=0.20 chromatic_above=0.10 chromatic_below=0.11 diatonic=0.19 fifth=0.07 other=0.26 same=0.06 | same=0.00 chromatic_below=0.53 chromatic_above=0.16 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.06 1=0.21 10=0.02 11=0.03 12=0.01 2=0.14 3=0.08 4=0.09 5=0.13 6=0.07 7=0.07 8=0.03 9=0.02 >12=0.04 | 0=0.00 1=0.69 2=0.18 3=0.05 4=0.01 5=0.06 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.526 | 0.286 |
| approach_same_side_share | 0.661 | 0.985 |
| passage_classes | chord_tone=0.48 chromatic=0.27 scale_step=0.25 | chord_tone=0.51 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.48 chromatic=0.29 scale_step=0.23 | chord_tone=0.53 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.20 1=0.22 10=0.02 11=0.02 12=0.02 2=0.14 3=0.08 4=0.07 5=0.08 6=0.05 7=0.06 8=0.02 9=0.02 >12=0.02 | 0=0.01 1=0.36 2=0.26 3=0.08 4=0.11 5=0.10 6=0.03 7=0.03 8=0.00 9=0.02 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.196 | 0.012 |
| interval_keep_direction_share | 0.423 | 0.491 |
| interval_toward_target_share | 0.444 | 0.325 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=33.00 p25=38.00 p5=34.75 p50=42.00 p75=45.00 p95=49.00 p99=52.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=50.00 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=33.00 p5=28.00 p50=37.00 p75=40.00 p95=45.00 p99=49.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=45.00 |
| walk_window | high=50.00 low=33.00 | low=36.00 high=46.92 |
| arrival_window | high=46.00 low=36.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.76 2=0.22 3=0.01 4=0.00 | 1=0.70 2=0.19 3=0.11 4=0.00 |
| chord_duration | 1=0.03 2=0.45 3=0.00 4=0.39 5=0.00 6=0.00 7=0.00 8=0.10 >8=0.02 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.75 beat3=0.23 other=0.02 | beat1=0.59 beat3=0.30 other=0.11 |

## Groupe de référence `blues` (87 solos, 5725 mesures valides)

| famille | critère | d(grille_accompagnee) |
|---|---|---|
| arrival | arrival_classes_at_change | 0.583 |
| arrival | arrival_bass_share_at_change | 0.583 |
| arrival | bar_start_no_change_classes | 0.785 |
| arrival | bar_start_no_change_bass_share | 0.785 |
| approach | approach_weights | 0.494 |
| approach | approach_weights_bar_change | 0.520 |
| approach | approach_weights_mid_change | 0.410 |
| approach | approach_classes | 0.494 |
| approach | approach_distance | 0.512 |
| approach | approach_above_share | 0.212 |
| approach | approach_same_side_share | 0.348 |
| passage | passage_classes | 0.092 |
| passage | passage_engine_classes | 0.126 |
| intervals | interval_histogram | 0.299 |
| intervals | interval_repeat_share | 0.149 |
| intervals | interval_keep_direction_share | 0.065 |
| intervals | interval_toward_target_share | 0.148 |
| intervals | interval_percentiles | 0.233 |
| register | register_percentiles | 0.202 |
| register | register_percentiles_relative_to_tonic | 0.248 |
| register | walk_window | 0.295 |
| register | arrival_window | 0.083 |
| harmonic_rhythm | chords_per_bar | 0.222 |
| harmonic_rhythm | chord_duration | 0.480 |
| harmonic_rhythm | change_beat | 0.296 |
| **agrégée** | moyenne des critères | **0.347** |

Par famille : `grille_accompagnee` : approach 0.427, arrival 0.684, harmonic_rhythm 0.333, intervals 0.179, passage 0.109, register 0.207

Valeurs comparées (référence puis étiquettes) :

| critère | référence | grille_accompagnee |
|---|---|---|
| arrival_classes_at_change | bass=0.42 fifth=0.14 other=0.24 root=0.00 seventh=0.10 third=0.10 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.417 | 1.000 |
| bar_start_no_change_classes | bass=0.21 fifth=0.15 other=0.37 root=0.00 seventh=0.10 third=0.17 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.215 | 1.000 |
| approach_weights | chromatic=0.23 diatonic=0.20 none=0.57 | none=0.08 chromatic=0.69 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.26 diatonic=0.19 none=0.55 | none=0.03 chromatic=0.59 diatonic=0.38 |
| approach_weights_mid_change | chromatic=0.25 diatonic=0.18 none=0.57 | none=0.18 chromatic=0.66 diatonic=0.16 |
| approach_classes | chord_tone=0.16 chromatic_above=0.10 chromatic_below=0.13 diatonic=0.20 fifth=0.06 other=0.31 same=0.05 | same=0.00 chromatic_below=0.53 chromatic_above=0.16 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.05 1=0.23 10=0.02 11=0.03 12=0.01 2=0.14 3=0.09 4=0.12 5=0.10 6=0.08 7=0.06 8=0.02 9=0.02 >12=0.04 | 0=0.00 1=0.69 2=0.18 3=0.05 4=0.01 5=0.06 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.499 | 0.286 |
| approach_same_side_share | 0.638 | 0.985 |
| passage_classes | chord_tone=0.45 chromatic=0.30 scale_step=0.25 | chord_tone=0.51 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.44 chromatic=0.33 scale_step=0.23 | chord_tone=0.53 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.16 1=0.25 10=0.02 11=0.02 12=0.01 2=0.14 3=0.08 4=0.07 5=0.08 6=0.05 7=0.06 8=0.03 9=0.02 >12=0.03 | 0=0.01 1=0.36 2=0.26 3=0.08 4=0.11 5=0.10 6=0.03 7=0.03 8=0.00 9=0.02 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.162 | 0.012 |
| interval_keep_direction_share | 0.426 | 0.491 |
| interval_toward_target_share | 0.473 | 0.325 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=32.00 p25=38.00 p5=34.00 p50=42.00 p75=45.00 p95=50.00 p99=53.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=50.00 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=32.00 p5=27.00 p50=36.00 p75=39.00 p95=44.00 p99=48.81 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=45.00 |
| walk_window | high=51.00 low=33.00 | low=36.00 high=46.92 |
| arrival_window | high=46.00 low=34.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.92 2=0.08 3=0.00 4=0.00 | 1=0.70 2=0.19 3=0.11 4=0.00 |
| chord_duration | 1=0.01 2=0.21 3=0.00 4=0.52 5=0.00 6=0.00 7=0.00 8=0.20 >8=0.05 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.89 beat3=0.11 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |

## Groupe de référence `reliable` (75 solos, 5192 mesures valides)

| famille | critère | d(grille_accompagnee) |
|---|---|---|
| arrival | arrival_classes_at_change | 0.369 |
| arrival | arrival_bass_share_at_change | 0.369 |
| arrival | bar_start_no_change_classes | 0.637 |
| arrival | bar_start_no_change_bass_share | 0.637 |
| approach | approach_weights | 0.475 |
| approach | approach_weights_bar_change | 0.496 |
| approach | approach_weights_mid_change | 0.417 |
| approach | approach_classes | 0.475 |
| approach | approach_distance | 0.478 |
| approach | approach_above_share | 0.247 |
| approach | approach_same_side_share | 0.352 |
| passage | passage_classes | 0.069 |
| passage | passage_engine_classes | 0.059 |
| intervals | interval_histogram | 0.318 |
| intervals | interval_repeat_share | 0.149 |
| intervals | interval_keep_direction_share | 0.043 |
| intervals | interval_toward_target_share | 0.163 |
| intervals | interval_percentiles | 0.233 |
| register | register_percentiles | 0.179 |
| register | register_percentiles_relative_to_tonic | 0.262 |
| register | walk_window | 0.295 |
| register | arrival_window | 0.042 |
| harmonic_rhythm | chords_per_bar | 0.095 |
| harmonic_rhythm | chord_duration | 0.312 |
| harmonic_rhythm | change_beat | 0.126 |
| **agrégée** | moyenne des critères | **0.292** |

Par famille : `grille_accompagnee` : approach 0.420, arrival 0.503, harmonic_rhythm 0.178, intervals 0.181, passage 0.064, register 0.194

Valeurs comparées (référence puis étiquettes) :

| critère | référence | grille_accompagnee |
|---|---|---|
| arrival_classes_at_change | bass=0.63 fifth=0.09 other=0.13 root=0.00 seventh=0.07 third=0.07 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.631 | 1.000 |
| bar_start_no_change_classes | bass=0.36 fifth=0.28 other=0.17 root=0.00 seventh=0.09 third=0.09 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.363 | 1.000 |
| approach_weights | chromatic=0.27 diatonic=0.17 none=0.56 | none=0.08 chromatic=0.69 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.32 diatonic=0.16 none=0.53 | none=0.03 chromatic=0.59 diatonic=0.38 |
| approach_weights_mid_change | chromatic=0.24 diatonic=0.21 none=0.55 | none=0.18 chromatic=0.66 diatonic=0.16 |
| approach_classes | chord_tone=0.22 chromatic_above=0.14 chromatic_below=0.14 diatonic=0.17 fifth=0.09 other=0.19 same=0.06 | same=0.00 chromatic_below=0.53 chromatic_above=0.16 diatonic=0.22 fifth=0.00 chord_tone=0.06 other=0.02 |
| approach_distance | 0=0.06 1=0.27 10=0.02 11=0.03 12=0.01 2=0.13 3=0.06 4=0.07 5=0.13 6=0.06 7=0.09 8=0.02 9=0.02 >12=0.03 | 0=0.00 1=0.69 2=0.18 3=0.05 4=0.01 5=0.06 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.533 | 0.286 |
| approach_same_side_share | 0.634 | 0.985 |
| passage_classes | chord_tone=0.58 chromatic=0.19 scale_step=0.23 | chord_tone=0.51 scale_step=0.28 chromatic=0.21 |
| passage_engine_classes | chord_tone=0.58 chromatic=0.21 scale_step=0.21 | chord_tone=0.53 scale_step=0.27 chromatic=0.20 |
| interval_histogram | 0=0.16 1=0.23 10=0.02 11=0.02 12=0.02 2=0.13 3=0.07 4=0.07 5=0.09 6=0.05 7=0.07 8=0.03 9=0.02 >12=0.02 | 0=0.01 1=0.36 2=0.26 3=0.08 4=0.11 5=0.10 6=0.03 7=0.03 8=0.00 9=0.02 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.161 | 0.012 |
| interval_keep_direction_share | 0.448 | 0.491 |
| interval_toward_target_share | 0.488 | 0.325 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=31.00 p25=38.00 p5=34.00 p50=42.00 p75=45.00 p95=48.00 p99=52.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=50.00 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=33.00 p5=28.00 p50=37.00 p75=41.00 p95=45.00 p99=48.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=45.00 |
| walk_window | high=51.00 low=33.00 | low=36.00 high=46.92 |
| arrival_window | high=46.00 low=35.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.71 2=0.26 3=0.02 4=0.01 | 1=0.70 2=0.19 3=0.11 4=0.00 |
| chord_duration | 1=0.06 2=0.46 3=0.00 4=0.38 5=0.00 6=0.00 7=0.00 8=0.07 >8=0.01 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.72 beat3=0.25 other=0.03 | beat1=0.59 beat3=0.30 other=0.11 |
