#!/bin/bash
# TEST ONLY: refresh the LD-mode lumps in the test build without a full build.py (zip updates those entries).
#   ldl_patch/tools/ldpatchpk3.sh [pk3]   (default /tmp/ldrig/BD22_VR_ld.pk3)
PK3=${1:-/tmp/ldrig/BD22_VR_ld.pk3}
cd /home/claude/rs_brutal22weaponsq/src && zip -q "$PK3" ZSCRIPT.rsz CVARINFO.rsld MAPINFO.rsld MENUDEF.rsld zscript/rsld/*.zs && echo "updated $PK3"
