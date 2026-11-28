# ModelSwapper_Hands prototype: FBX-skeleton hand fitter (report, 2026-10-26)

Research prototype. Nothing here ships or is committed. Written by the coordinator from Lane C's final
round-2 report (the lane's harness could not write this file).

## The FBX hand
DXR `models/hands/hand_final.fbx`: Maya 2019 (2020-06-24), binary FBX 7.5. Two hand meshes (left/right),
a 22-joint rig (palm, 4 joints per finger, 4 for the thumb), one take of 1279 frames at 60 fps holding
7 distinct poses; base colour, roughness and normal textures embedded. Read in pure numpy
(`hands_tool/fbxbin.py`, `fbxhand.py`; frame 0 reproduces the bind mesh exactly); assimp 5.4.3 built
from source to cross-check. Blender/bpy could not be installed (proxy refuses pypi.org and
download.blender.org).

## Method
Gun landmarks from the mesh; grip rules G1-G9 (gun hand) and S1-S5 (support hand); tolerances from
1.92's measured poses (22 guns). Round 2: the displayed wrist is pinned to the controller grip
(G8 threshold = 1.92 median, 7.5 deg / 7.3 cm) and the GUN moves to the hand, expressed exactly
(residual < 1e-13 cm) as the gun's existing MODELDEF Offset/ZOffset/Angle/Pitch/RollOffset; a
bar-wrap term closes a support fist around a bar. Poses baked to MD3 vertex frames (no skeletal
runtime). Pipeline: see README.md.

## Results (rules green/yellow/red)
| Gun | FBX round 1 | FBX round 2 | 1.92 | current ModelSwapper |
|---|---|---|---|---|
| BrutalPistol | 13/1/0 | 14/0/0 | 12/1/1 | - |
| Flamethrower2 | 11/2/1 | 13/1/0 | 3/2/9 | 1/3/10 |

- Pistol G8: 14.6 deg / 6.8 cm -> 6.0 deg / 0.3 cm. Web 1.26 cm off the backstrap, index 0.04 cm off
  the trigger, grip diagonal 21 deg (1.92: 23).
- Flamethrower G8: 13.5 deg / 8.8 cm -> 6.0 deg / 0.5 cm. S4 0.39 -> 0.99: all four fingers loop the
  bar (341-484 deg each); deepest penetration 0.55 cm (1.92 median 0.95). G9 still yellow: forearm
  20 deg off the bore (1.92 median 12, max 31).
- Gun MODELDEF offsets: pistol Offset -0.049 -3.510, ZOffset -1.513, Angle/Pitch/Roll 2.634/4.880/5.265;
  Flamethrower Offset -4.371 -8.313, ZOffset -5.669, Angle/Pitch/Roll -3.798/1.805/0.100.
- Engine: the 17.3 rig ran the test pack on the owner's load order, clean (only BD_VoxelPack's own
  voxeldef lines). Test pack (NOT for the headset): out/BD22Q_192_fbx_r2.pk3.

## RS Avatar standard (UZDXREMA GUNS_IN_AVATAR_HANDS.md)
Same hand, same references: their fbx_open (frame 1) = our open; their fbx_fist (319) within 2.4 deg
of ours. Their wrap/cup frames (820/837/985) match only when read from rig B, as their file does;
fbx_twohand_gun (985, rig A) is not a gun hand. Nearest named poses: gun hands ~ `pointing`
(27-31 deg), Flamethrower fist ~ `hold_foregrip` (20 deg), pistol cup ~ `gun_grip` (26.5 deg).
Card fields per gun (palm, triggerat, seat, supportat, rake, supportaxis, supporthold):
results/cards_round2.json. Only their rake convention is reused; their grip frame was not cross-checked.

## Left before it could replace the current fitter
- Gun-relative layers (flash, casings, reload/pump/break layers, other MODELDEF blocks) were not moved
  with the new gun offsets: the main integration risk.
- The test pack reuses frame letters other guns use (RQGT E, RQSP B); a real set needs its own.
- Reconcile the gun-to-hand move with REMA's anchor frame and grip socket (one card for both).
- Support-hand wrist not tied to the off controller; `squeeze` (trigger pulled) not solved.
- No headset pass.

## Risks
- FBX source and licence unknown. `handcurl.txt` (RS Avatar) derives from FRIK 0.79.1: licence open;
  nothing here uses it.
- Look: renders as bare skin tone (median colour 171,113,94 vs Ermac's glove 33,33,33). Retexturing is
  a one-PNG + MODELDEF Skin swap (UVs survive the bake), but a glove texture for the FBX UV layout
  doesn't exist yet. The normal/roughness maps are not used by QZD's MD3 path.
- Quest cost: 15,552 bytes per MD3 frame vs Ermac's 8,224; 1937 verts / 3330 tris (about 2x Ermac).
  Frame rate not measured on a Quest.
