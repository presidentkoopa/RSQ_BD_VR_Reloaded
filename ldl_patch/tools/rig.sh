#!/bin/bash
# TEST ONLY (never ships). Runs the LDL/BD22 VR patch on the real QuestZDoom 17.3 rig
# (RSQ_UBQSeries/tools/rig17/run17.sh, shared with other lanes: serialized with flock on /home/claude/rig.lock).
#   tools/rig.sh <name> <secs> "<console script>"
# ORDER selects the load order (default full):
#   full   doom2 -> brutal22test6 -> voxels -> BD22 VR -> XMVE 04-07 -> LegenDoom 3.0 -> Champions -> patch
#   nochamp  same without Champions;   nold  without LegenDoom, Champions and the patch (the pre-LegenDoom baseline)
#   nopatch  full order without the patch (what LegenDoom does to BD22 VR on its own)
#   bdonly   doom2 -> brutal22test6 -> voxels -> BD22 VR (no XMVE, no LegenDoom)
# The probe (tools/probe) is appended last. FRAMES=n dumps every n-th frame (left eye) to evidence/frames/<name>/.
# WHEEL=1 adds RSQ_UBQSeries/pk3/RSQ_Wheel.pk3 (read-only use) and tools/probe_wheel after the patch.
# Log: /home/claude/scratch/logs/<name>.log (copied to evidence/logs/<name>.log).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; PATCH="$(cd "$HERE/.." && pwd)"; REPO="$(cd "$PATCH/.." && pwd)"
RIG17=/home/claude/RSQ_UBQSeries/tools/rig17/run17.sh
SC=/tmp/claude-0/-home-claude/01ebc270-3953-5301-831b-c73a8b1320ca/scratchpad/ldp
NAME=$1; SECS=$2; SCRIPT=$3
LD=${LD:-/mnt/user-data/uploads/Desktop/LegenDoom_3.0.pk3}
CH=${CH:-/mnt/user-data/attachments/01ebc270-3953-5301-831b-c73a8b1320ca/a09b1892-mk-champions20210309.pk3}
VR=${VR:-$(ls $REPO/pk3/03_BD22_VR-Reloaded_*.pk3 | sort | tail -1)}
BASE="/home/claude/scratch/lo2/01_brutal22test6.pk3 $REPO/pk3/02_BD22_VoxelPack.pk3 $VR $REPO/pk3/04_XMVE_MonsterExpansion1.3.1-BD22.pk3 $REPO/pk3/05_XMVE_MonsterExpansion_TUD.pk3 $REPO/pk3/06_XMVE_MonsterExpansion_Doom2.pk3 $REPO/pk3/07_XMVE_MonstersNoDropGuns-BD22.pk3"
PP=${PP:-$REPO/pk3/LDL_BD22VR_Patch.pk3}
case ${ORDER:-full} in
  full)    L="$BASE $LD $CH $PP";;
  nochamp) L="$BASE $LD $PP";;
  nold)    L="$BASE";;
  bdonly)  L="/home/claude/scratch/lo2/01_brutal22test6.pk3 $REPO/pk3/02_BD22_VoxelPack.pk3 $VR";;
  nopatch) L="$BASE $LD $CH";;
esac
mkdir -p $SC/probe; rm -f $SC/probe/probe.pk3; (cd "$HERE/probe" && zip -q -r -X $SC/probe/probe.pk3 .)
F=$PATCH/evidence/frames/$NAME; rm -rf $F
if [ -n "${FRAMES:-}" ]; then mkdir -p $F; export QZ_DUMP_EVERY=$FRAMES QZ_DUMP_DIR=$F; fi
if [ -n "${WHEEL:-}" ]; then rm -f $SC/probe/probew.pk3; (cd "$HERE/probe_wheel" && zip -q -r -X $SC/probe/probew.pk3 .); L="$L /home/claude/RSQ_UBQSeries/pk3/RSQ_Wheel.pk3 $SC/probe/probew.pk3"; fi
export IWAD=/home/claude/iwad/doom2/doom2.wad PK3S="$L $SC/probe/probe.pk3" MAP=${MAP:-1}
flock -o -x /home/claude/rig.lock bash -c "sed -i -E '/^(rsldp_|rsldpp_|ld_|champion_)/d' /home/claude/g9/rig/config/qzdoom.ini; bash \"\$0\" \"\$@\"" "$RIG17" "$NAME" "$SECS" "$SCRIPT" >/dev/null
if [ -n "${FRAMES:-}" ]; then python3 -I -c "
import glob
from PIL import Image
for f in glob.glob('$F/*.ppm'):
    Image.open(f).save(f[:-4]+'.png')
"; rm -f $F/*.ppm; echo "frames: $(ls $F | wc -l) in $F"; fi
LG=/home/claude/scratch/logs/$NAME.log; mkdir -p $PATCH/evidence/logs; cp $LG $PATCH/evidence/logs/$NAME.log 2>/dev/null
echo "== $NAME (${ORDER:-full}): script errors (not voxeldef): $(grep -i -E 'script error|VM abort|exception|errors while compiling|Execution could not continue|not implemented|Segmentation' $LG | grep -v -i voxeldef | wc -l), voxeldef lines $(grep -c -i 'No sprites specified for voxel' $LG)"
grep -i -E "script error|VM abort|exception|Called from|errors while compiling|Unknown class|not found|Execution could not continue" $LG | grep -v -i voxeldef | head -${SHOWERR:-12}
