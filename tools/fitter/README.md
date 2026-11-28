# tools/fitter: the hand fitter that works (moved here 2026-11-27)

This is the copy of the FBX hand fitter that can rebuild every hand in BD22 VR Reloaded. It came from RS_ModelSwapper
(`tools/handfit` + `tools/depot.py`, commit 7c1207f) when that repo was retired. The older snapshot in
`tools/handfit/` stays where it is: it holds the DATA this fitter reads (`tools/handfit/poses`, `tools/handfit/port/fits`)
but cannot run on its own (no FBX hand, no `ref192_pistol.json`).

## Check that it works
```
python3 tools/fitter/handfit/port/rebake.py check
```
Expected: 30 poses, every hand md3 `bytes identical` to what `src/models/rsq/fbx/` ships, `"modeldef_mismatch": 0` on all 30.
Run from this repo on 2026-11-27 against 2.0.6b: exactly that.

## What is here
- **The FBX hand** (`handfit/core/fbx_hand/hand_final.fbx` and its two textures), committed on the owner's word
  (2026-11-27: "did i ask you to leave the hand model out?"). The fitter finds it by default; `RSQ_FBX` overrides.

## What is NOT here
- **The Linux test rig.** It is in RSQ_UBQSeries `tools/rig`. Check that repo out beside this one, or set `RSQ_RIG`.
  Only the tools that render in the engine need it (`gate_gun.py`, the sheets); `rebake.py` does not.

`tools/fitter/depot.py` is the one place every path is set. How the method works, gun by gun: `handfit/core/README.md`,
`handfit/core/REPORT.md` and each folder's own header comments.
