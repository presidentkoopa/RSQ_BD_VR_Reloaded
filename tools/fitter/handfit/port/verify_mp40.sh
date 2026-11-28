#!/bin/sh
# Re-applies batch 3's MP40 move with port_gun.py on the tree before it (19f0203) and diffs against the committed result (bdf3fae).
# Expected: identical except the BrutalSMG RSQ_Muzzle row, which that commit also added (not part of the MP40 move).
set -e
HERE=$(cd "$(dirname "$0")" && pwd); DEPOT=$(cd "$HERE/../../.." && pwd); T=${TMPDIR:-/tmp}/port_gun_verify.$$
# the two commits live in the BD22 repo (presidentkoopa/RS_Brutal22WeaponsQ), not in the Depot
REPO=${RSQ_BD22_REPO:-$DEPOT/../rs_brutal22weaponsq}; FITS=${RSQ_FITS_DIR:-$REPO/handfit/fits}
mkdir -p "$T/clean" "$T/ref"; cd "$REPO"
git archive 19f0203 src | tar -x -C "$T/clean"; git archive bdf3fae src | tar -x -C "$T/ref"
python3 "$HERE/port_gun.py" MP40 "$FITS/MP40_b3.json" --src "$T/clean/src" --tag "batch 3"
echo "--- diff against bdf3fae (expect only the BrutalSMG muzzle row):"; diff -r "$T/clean/src" "$T/ref/src" || true
rm -rf "$T"
