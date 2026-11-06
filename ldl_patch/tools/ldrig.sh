#!/bin/bash
# TEST ONLY (never ships). LD mode in BD22 VR on the real QuestZDoom 17.3 rig (rsq_weapondepot/tools/rig/bin),
# one engine at a time under /home/claude/rig.lock; the rig's qzdoom.ini is restored after every run.
#   ldl_patch/tools/ldrig.sh <name> <secs> "<console script>"
# Env:
#   PK3     the BD22 VR test build (default /tmp/ldrig/BD22_VR_ld.pk3: python3 build.py ld; mv BD22_VR-Reloaded_ld.pk3 there)
#   ORDER   full    doom2 -> brutal22test6 -> BD_VoxelPack -> BD22 VR -> XMVE 04-07 -> LegenDoom 3.0   (default)
#           nold    doom2 -> brutal22test6 -> BD_VoxelPack -> BD22 VR -> XMVE 04-07                    (no LegenDoom)
#           ldfirst doom2 -> LegenDoom 3.0 -> brutal22test6 -> BD_VoxelPack -> BD22 VR -> XMVE 04-07   (owner pick?)
#   EXTRA   more pk3s after the order (e.g. a probe)
#   FRAMES=n  dump every n-th frame (left eye) to /tmp/ldrig/frames/<name>/ as PNG; QZ_RES (default 200)
#   SNDLOG=1  the rig's sound log (QZSND lines: every sound start with its source class)
# Log: /tmp/ldrig/<name>.log. Prints the script-error count (BD_VoxelPack's 4 voxeldef lines not counted).
set -u
NAME=$1; SECS=$2; SCRIPT=$3
RIG=/home/claude/rsq_weapondepot/tools/rig/bin
G=/home/claude/gamedata
P=/home/claude/rs_brutal22weaponsq/pk3
LD=${LD:-/mnt/user-data/uploads/1f3eb79e-LegenDoom_3.0.pk3}
PK3=${PK3:-/tmp/ldrig/BD22_VR_ld.pk3}
XMVE="$P/04_XMVE_MonsterExpansion1.3.1-BD22.pk3 $P/05_XMVE_MonsterExpansion_TUD.pk3 $P/06_XMVE_MonsterExpansion_Doom2.pk3 $P/07_XMVE_MonstersNoDropGuns-BD22.pk3"
case ${ORDER:-full} in
  full)    L="$G/brutal22test6.pk3 $G/BD_VoxelPack.pk3 $PK3 $XMVE $LD";;
  nold)    L="$G/brutal22test6.pk3 $G/BD_VoxelPack.pk3 $PK3 $XMVE";;
  ldfirst) L="$LD $G/brutal22test6.pk3 $G/BD_VoxelPack.pk3 $PK3 $XMVE";;
  *) echo "ORDER?"; exit 2;;
esac
L="$L ${EXTRA:-}"
WARP="-warp ${MAP:-1}"; [ "${MAP:-1}" = "none" ] && WARP=""	# MAP=none: no -warp (the title map runs)
mkdir -p /tmp/ldrig; LOG=/tmp/ldrig/$NAME.log; rm -f $LOG $LOG.out
F=/tmp/ldrig/frames/$NAME; rm -rf $F
ENVX=""
if [ -n "${FRAMES:-}" ]; then mkdir -p $F; ENVX="QZ_DUMP_EVERY=$FRAMES QZ_DUMP_DIR=$F"; fi
[ -n "${SNDLOG:-}" ] && ENVX="$ENVX QZ_SNDLOG=1"
flock -o -x /home/claude/rig.lock bash -c "cd $RIG && env QZ_RES=${QZ_RES:-200} EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 $ENVX \
  timeout $SECS ./qz -iwad $G/doom2.wad -file $L -nosound ${ARGS:-} $WARP -skill 3 +logfile $LOG \"+$SCRIPT\" > $LOG.out 2>&1; \
  git -C /home/claude/rsq_weapondepot checkout tools/rig/bin/config/qzdoom.ini"
if [ -n "${FRAMES:-}" ]; then python3 -I -c "
import glob
from PIL import Image
for f in glob.glob('$F/*.ppm'):
    Image.open(f).save(f[:-4]+'.png')
"; rm -f $F/*.ppm; echo "frames: $(ls $F | wc -l) in $F"; fi
cat $LOG.out >> $LOG 2>/dev/null
E=$(grep -E -i 'script error|VM abort|[1-9][0-9]* errors|FATAL:|Execution could not continue|not implemented|Segmentation' $LOG | grep -v -i voxeldef | wc -l)
echo "== $NAME (${ORDER:-full}): script errors (not voxeldef): $E, voxeldef lines $(grep -c -i 'voxeldef' $LOG)"
grep -i -E "script error|VM abort|exception|Called from|while compiling|Unknown class|Execution could not continue|warning" $LOG | grep -v -i "voxeldef\|qzt_\|GL_EXT" | head -${SHOWERR:-15}
