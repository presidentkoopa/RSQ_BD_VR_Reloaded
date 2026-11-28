fitter_lib: the batch 1-4 fitter modules that tools/handfit imports. They used to live only in the cloud run folders
/home/claude/lane_b_b1run/tools (gunmove, mdblocks), lane_b_b2run/tools (revindex, revlm), lane_b_b3run/tools (fit3, m192,
rigid3, curl3) and lane_b_b4run/tools (st2_b4, curl4); those folders were deleted 2026-10-27. Rebuilt from the fit farm's packed
mirror (work/fitfarm/home/lane_b_b*run/tools, packed from those folders before the deletion) with the paths changed back:
sibling modules from this folder, data under env RS_FITTER_HOME (default /home/claude). Importers find this folder through env
RS_FITTER_LIB (default: tools/handfit/fitter_lib next to them).
Data the modules read or write in the old run folders (st2_*.npy, curl3_*.json, fit3_*.json, revindex_*.json) is NOT here:
on the cloud it was deleted with them; the farm still has its copies under work/fitfarm/home/lane_b_b*run/.
