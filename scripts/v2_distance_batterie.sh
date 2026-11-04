#!/usr/bin/env bash
# V2 : distance de la batterie des profils `gmd_*` et `wjazzd_ballad` au Groove MIDI Dataset, avec les scripts des
# comptes rendus B du moteur (Bray-Curtis des fréquences d'attaque par pas, 16 graines × 48 mesures).
#
#   scripts/v2_distance_batterie.sh <worktree du moteur> <labo> <python du labo> <dossier de sortie> [<moteur pour assets/>]
#
# - le binaire est `<worktree du moteur>/target/release/harmonium-cli` (compilé : `cargo build --release -p harmonium-cli`) ;
# - les scripts B3, B25 (b25_distance.py) supposent le moteur et le labo sous `~/Project/bascanada/` : le script les
#   lance avec un HOME factice (`<sortie>/home`) dont ces deux chemins sont des liens vers le moteur (pour `assets/`,
#   5e argument, défaut `~/workspace/harmonium`) et vers le labo donné ; rien n'est écrit dans ces deux dossiers ;
# - le GMD (`corpus/gmd/raw/groove-v1.0.0-midionly.zip`) doit être lisible depuis le labo (cache hors dépôt) ;
# - B3 et B25 écrivent leurs rendus sous `/tmp/harmonium-019/{b3,b25}/` (chemins codés dans les scripts) : à supprimer après.
set -u
ENG=$(realpath "$1"); LAB=$(realpath "$2"); PY=$3; OUT=$(realpath -m "$4"); ASSETS=$(realpath "${5:-$HOME/workspace/harmonium}")
S=$ENG/specs/019-bibliotheque-accompagnements
mkdir -p "$OUT/home/Project/bascanada" "$OUT/b8work"
ln -sfn "$ASSETS" "$OUT/home/Project/bascanada/harmonium"
ln -sfn "$LAB" "$OUT/home/Project/bascanada/harmonium_lab"
export PYTHONPATH=$LAB/src H019_GMD_CACHE=$OUT/results.pkl HARMONIUM_CLI=$ENG/target/release/harmonium-cli HARMONIUM_CWD=$ASSETS
[ -x "$HARMONIUM_CLI" ] || { echo "binaire absent : $HARMONIUM_CLI" >&2; exit 2; }

run() {   # nom, puis la commande ; HOME factice pour les chemins `~/Project/bascanada/…`
  name=$1; shift
  echo "== $name" >&2
  HOME="$OUT/home" "$@" > "$OUT/$name.log" 2>&1 || { echo "échec $name, voir $OUT/$name.log" >&2; return 1; }
}
HARMONIUM_DISTANCE_WORK=$OUT/b8work run b8 "$PY" "$S/b8/distance_gmd.py" --lab "$LAB" --out "$OUT/b8.json"
run b6 "$PY" "$S/b6/distance_gmd.py" --lab "$LAB" --out "$OUT/b6.json"
run b25 "$PY" "$S/b25_distance.py" --out "$OUT/b25.json"
run bossa "$PY" "$S/b3/gmd_latin_brazilian_bossa_distance.py" --out "$OUT/bossa.json"
run samba "$PY" "$S/b3/gmd_latin_brazilian_samba_distance.py" --out "$OUT/samba.json"
run baiao "$PY" "$S/b3/gmd_latin_brazilian_baiao_distance.py" --out "$OUT/baiao.json"
run afrocuban "$PY" "$S/b3/gmd_afrocuban_distance.py" --out "$OUT/afrocuban.json"
