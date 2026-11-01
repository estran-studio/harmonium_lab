# Distance de la basse générée à WJazzD (swing)

Référence : Weimar Jazz Database (WJazzD) — WJazzD 2.1 (base 2.2, publiée le 2018-02-08) (references/wjazzd-swing/measures-bass.json), 361 solos, 23224 mesures valides.

Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus). Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0).

Commande : `python -m harmonium_lab.backing.bass_compare --truth target/backing_truth/wjazzd_swing_b88_s11.json --truth target/backing_truth/wjazzd_swing_b88_s12.json --truth target/backing_truth/wjazzd_swing_b88_s13.json --truth target/backing_truth/wjazzd_swing_b88_s14.json --truth target/backing_truth/wjazzd_swing_b88_s15.json --truth target/backing_truth/wjazzd_swing_b88_s16.json --truth target/backing_truth/wjazzd_swing_b88_s17.json --truth target/backing_truth/wjazzd_swing_b88_s18.json --truth target/backing_truth/wjazzd_swing_b88_s19.json --truth target/backing_truth/wjazzd_swing_b88_s20.json --truth target/backing_truth/wjazzd_swing_b88_s21.json --truth target/backing_truth/wjazzd_swing_b88_s22.json --truth target/backing_truth/wjazzd_swing_b88_s23.json --truth target/backing_truth/wjazzd_swing_b88_s24.json --truth target/backing_truth/wjazzd_swing_b88_s25.json --truth target/backing_truth/wjazzd_swing_b88_s26.json --label wjazzd_swing --truth target/backing_truth/grille_accompagnee_b88_s11.json --truth target/backing_truth/grille_accompagnee_b88_s12.json --truth target/backing_truth/grille_accompagnee_b88_s13.json --truth target/backing_truth/grille_accompagnee_b88_s14.json --truth target/backing_truth/grille_accompagnee_b88_s15.json --truth target/backing_truth/grille_accompagnee_b88_s16.json --truth target/backing_truth/grille_accompagnee_b88_s17.json --truth target/backing_truth/grille_accompagnee_b88_s18.json --truth target/backing_truth/grille_accompagnee_b88_s19.json --truth target/backing_truth/grille_accompagnee_b88_s20.json --truth target/backing_truth/grille_accompagnee_b88_s21.json --truth target/backing_truth/grille_accompagnee_b88_s22.json --truth target/backing_truth/grille_accompagnee_b88_s23.json --truth target/backing_truth/grille_accompagnee_b88_s24.json --truth target/backing_truth/grille_accompagnee_b88_s25.json --truth target/backing_truth/grille_accompagnee_b88_s26.json --label grille_accompagnee --reference /Users/william.quintal/orca/workspaces/harmonium_lab/e7-wjazzd-swing/references/wjazzd-swing/measures-bass.json -o references/wjazzd-swing/validation-bass-heldout.json --group all --markdown`

Généré :
- `wjazzd_swing` : 16 fichier(s), 1392 mesures valides sur 1408 (sans basse complète : 16, accord non analysé : 0)
- `grille_accompagnee` : 16 fichier(s), 2032 mesures valides sur 2048 (sans basse complète : 16, accord non analysé : 0)

## Groupe de référence `all` (361 solos, 23224 mesures valides)

| famille | critère | d(wjazzd_swing) | d(grille_accompagnee) |
|---|---|---|---|
| arrival | arrival_classes_at_change | 0.588 | 0.588 |
| arrival | arrival_bass_share_at_change | 0.588 | 0.588 |
| arrival | bar_start_no_change_classes | 0.767 | 0.767 |
| arrival | bar_start_no_change_bass_share | 0.767 | 0.767 |
| approach | approach_weights | 0.110 | 0.501 |
| approach | approach_weights_bar_change | 0.130 | 0.531 |
| approach | approach_weights_mid_change | 0.107 | 0.460 |
| approach | approach_classes | 0.218 | 0.501 |
| approach | approach_distance | 0.216 | 0.526 |
| approach | approach_above_share | 0.206 | 0.231 |
| approach | approach_same_side_share | 0.192 | 0.332 |
| passage | passage_classes | 0.112 | 0.072 |
| passage | passage_engine_classes | 0.154 | 0.103 |
| intervals | interval_histogram | 0.313 | 0.334 |
| intervals | interval_repeat_share | 0.167 | 0.180 |
| intervals | interval_keep_direction_share | 0.107 | 0.065 |
| intervals | interval_toward_target_share | 0.013 | 0.114 |
| intervals | interval_percentiles | 0.117 | 0.233 |
| register | register_percentiles | 0.128 | 0.158 |
| register | register_percentiles_relative_to_tonic | 0.214 | 0.262 |
| register | walk_window | 0.125 | 0.292 |
| register | arrival_window | 0.000 | 0.000 |
| harmonic_rhythm | chords_per_bar | 0.340 | 0.109 |
| harmonic_rhythm | chord_duration | 0.389 | 0.301 |
| harmonic_rhythm | change_beat | 0.177 | 0.155 |
| **agrégée** | moyenne des critères | **0.250** | **0.327** |

Par famille : `wjazzd_swing` : approach 0.168, arrival 0.678, harmonic_rhythm 0.302, intervals 0.143, passage 0.133, register 0.117 ; `grille_accompagnee` : approach 0.440, arrival 0.678, harmonic_rhythm 0.188, intervals 0.185, passage 0.088, register 0.178

Valeurs comparées (référence puis étiquettes) :

| critère | référence | wjazzd_swing | grille_accompagnee |
|---|---|---|---|
| arrival_classes_at_change | bass=0.41 fifth=0.11 other=0.27 root=0.00 seventh=0.10 third=0.10 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| arrival_bass_share_at_change | 0.412 | 1.000 | 1.000 |
| bar_start_no_change_classes | bass=0.23 fifth=0.16 other=0.38 root=0.00 seventh=0.10 third=0.13 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 | bass=1.00 root=0.00 third=0.00 fifth=0.00 seventh=0.00 other=0.00 |
| bar_start_no_change_bass_share | 0.233 | 1.000 | 1.000 |
| approach_weights | chromatic=0.21 diatonic=0.19 none=0.59 | none=0.50 chromatic=0.20 diatonic=0.30 | none=0.09 chromatic=0.69 diatonic=0.22 |
| approach_weights_bar_change | chromatic=0.24 diatonic=0.18 none=0.57 | none=0.47 chromatic=0.22 diatonic=0.31 | none=0.04 chromatic=0.61 diatonic=0.35 |
| approach_weights_mid_change | chromatic=0.19 diatonic=0.22 none=0.59 | none=0.48 chromatic=0.19 diatonic=0.33 | none=0.17 chromatic=0.65 diatonic=0.18 |
| approach_classes | chord_tone=0.20 chromatic_above=0.10 chromatic_below=0.11 diatonic=0.19 fifth=0.07 other=0.26 same=0.06 | same=0.06 chromatic_below=0.16 chromatic_above=0.04 diatonic=0.30 fifth=0.12 chord_tone=0.18 other=0.12 | same=0.01 chromatic_below=0.51 chromatic_above=0.18 diatonic=0.22 fifth=0.00 chord_tone=0.05 other=0.02 |
| approach_distance | 0=0.06 1=0.21 10=0.02 11=0.03 12=0.01 2=0.14 3=0.08 4=0.09 5=0.13 6=0.07 7=0.07 8=0.03 9=0.02 >12=0.04 | 0=0.06 1=0.20 2=0.22 3=0.09 4=0.03 5=0.17 6=0.00 7=0.12 8=0.02 9=0.04 10=0.03 11=0.02 12=0.00 >12=0.00 | 0=0.01 1=0.69 2=0.19 3=0.04 4=0.01 5=0.05 6=0.00 7=0.00 8=0.00 9=0.00 10=0.00 11=0.00 12=0.00 >12=0.00 |
| approach_above_share | 0.526 | 0.320 | 0.295 |
| approach_same_side_share | 0.661 | 0.853 | 0.994 |
| passage_classes | chord_tone=0.48 chromatic=0.27 scale_step=0.25 | chord_tone=0.48 scale_step=0.36 chromatic=0.16 | chord_tone=0.52 scale_step=0.28 chromatic=0.20 |
| passage_engine_classes | chord_tone=0.48 chromatic=0.29 scale_step=0.23 | chord_tone=0.57 scale_step=0.29 chromatic=0.14 | chord_tone=0.54 scale_step=0.27 chromatic=0.19 |
| interval_histogram | 0=0.20 1=0.22 10=0.02 11=0.02 12=0.02 2=0.14 3=0.08 4=0.07 5=0.08 6=0.05 7=0.06 8=0.02 9=0.02 >12=0.02 | 0=0.03 1=0.20 2=0.38 3=0.06 4=0.04 5=0.11 6=0.01 7=0.08 8=0.03 9=0.03 10=0.02 11=0.01 12=0.00 >12=0.00 | 0=0.02 1=0.35 2=0.25 3=0.07 4=0.13 5=0.11 6=0.03 7=0.03 8=0.00 9=0.01 10=0.00 11=0.00 12=0.00 >12=0.00 |
| interval_repeat_share | 0.196 | 0.029 | 0.016 |
| interval_keep_direction_share | 0.423 | 0.530 | 0.487 |
| interval_toward_target_share | 0.444 | 0.431 | 0.330 |
| interval_percentiles | p50=2.00 p75=5.00 p90=8.00 p95=11.00 p99=14.00 | p50=2.00 p75=5.00 p90=7.00 p95=9.00 p99=10.00 | p50=2.00 p75=4.00 p90=5.00 p95=6.00 p99=9.00 |
| register_percentiles | p1=33.00 p25=38.00 p5=34.75 p50=42.00 p75=45.00 p95=49.00 p99=52.00 | p1=33.00 p5=34.00 p25=38.00 p50=41.00 p75=43.00 p95=46.00 p99=48.00 | p1=36.00 p5=36.00 p25=39.00 p50=41.00 p75=43.00 p95=46.00 p99=50.00 |
| register_percentiles_relative_to_tonic | p1=24.00 p25=33.00 p5=28.00 p50=37.00 p75=40.00 p95=45.00 p99=49.00 | p1=28.00 p5=29.00 p25=33.00 p50=36.00 p75=38.00 p95=41.00 p99=43.00 | p1=31.00 p5=31.00 p25=34.00 p50=36.00 p75=38.00 p95=41.00 p99=45.00 |
| walk_window | high=50.00 low=33.00 | low=34.00 high=48.00 | low=36.00 high=46.00 |
| arrival_window | high=46.00 low=36.00 | low=36.00 high=46.00 | low=36.00 high=46.00 |
| chords_per_bar | 1=0.76 2=0.22 3=0.01 4=0.00 | 1=0.44 2=0.56 3=0.00 4=0.00 | 1=0.69 2=0.19 3=0.12 4=0.00 |
| chord_duration | 1=0.03 2=0.45 3=0.00 4=0.39 5=0.00 6=0.00 7=0.00 8=0.10 >8=0.02 | 1=0.00 2=0.81 3=0.00 4=0.06 5=0.00 6=0.02 7=0.00 8=0.12 >8=0.00 | 1=0.23 2=0.41 3=0.00 4=0.12 5=0.00 6=0.06 7=0.00 8=0.12 >8=0.05 |
| change_beat | beat1=0.75 beat3=0.23 other=0.02 | beat1=0.59 beat3=0.41 other=0.00 | beat1=0.59 beat3=0.30 other=0.11 |
