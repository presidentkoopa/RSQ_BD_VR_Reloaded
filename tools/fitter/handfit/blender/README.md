# Handfit: hand fitting in Blender (step 1, 2026-11-08)

**Status: written, not verified.** Authored where Blender cannot run. Every part that does not need Blender was checked
against the kit it replaces (below); the Blender calls (FBX import, bone mapping, pose assignment, the evaluated mesh)
have not run yet. The first run on the owner's machine is `test_brutalpistol.py`; until it passes, nothing here is "working".

## Why
The 2.0 fitter (`tools/handfit/core/hands_tool`, 76 scripts, solve rounds 1-7) put the agent in the inner loop: solve,
render, look, adjust, re-solve, run the engine. Every pass cost tokens for a judgement a person makes in two seconds in
a viewport. Handfit moves the person and Blender into the inner loop and leaves the agent the outer one: the tool is
deterministic, the person poses, the agent reads one-line reports.

## What is here
| file | what |
|---|---|
| `handfit_addon.py` | the Blender add-on (4.x). Panel "Handfit" in the 3D view sidebar: Load card, Import hand, Apply pose, Export. Also usable as a module from `blender -b --python`. |
| `pose_library.json` | 29 approved BD22 2.0.1 holds + the FBX take's 5 poses x 2 hands, each as every joint's frame relative to `HANDPALM_joint` (FBX units), with each hold's placement (`hand_place`), its gun's six MODELDEF numbers (`gun_move`), the bind reference, the controller-grip reference and cuff, and the FK vertex cloud for BrutalPistol. Built by `build_pose_library.py`; rebuild when a hold changes. |
| `build_pose_library.py` | numpy, runs anywhere: reads the BD22 pose files (three shapes, one 30-vector: `[0:3]` hand rotvec, `[3:6]` hand translation cm, `[6:24]` the 18 handmodel parameters, `[24:30]` the gun move) and the FBX take. `RSQ_SET` names the BD22 checkout. |
| `test_brutalpistol.py` | the acceptance test (`blender -b --python tools/handfit/blender/test_brutalpistol.py -- --bd22 <RS_Brutal22WeaponsQ checkout>`). |

## The scene is the controller frame
1 Blender unit = 1 cm in the player's hand: F = +X, L = +Y, U = +Z (the kit's FLU). The gun is placed by its MODELDEF
numbers through the same chain QZD 17.3 draws with (`gun_chain`, = `gunplace.to_local_ao` + `gunview.to_fl`); the hand
by the hold's placement (`solve.hand_X`). Export reads the gun's six numbers back from where the gun object sits
(`gun_numbers_from_world`, exact for a moved gun), so "move the GUN to the hand" is: grab the gun object, move it,
export. The hand frame is written hook-0 / rot-0 (`flu_to_md3`, = `hook.flu_to_md3`): the frame is where the hand is
drawn, as BD22 2.0.1's `fbx_b1_R.md3`.

## Checked against the kit (numpy, 2026-11-08)
- `gun_chain` vs `gunplace.to_local_ao` + `gunview.to_fl`: max 0.000000 cm on 200 random vertices.
- `flu_to_md3` vs `hook.flu_to_md3`: max 0.000000.
- `gun_numbers_from_world(gun_chain(x))` = x to 3 decimals (BrutalPistol's six numbers).
- `read_md3` vs `tools/hqt/md3read.py`: identical; `write_md3` round trip: identical vertices and triangles.
- The library's BrutalPistol pose + its `hand_place` + `flu_to_md3` vs the shipped `fbx_b1_R.md3` frame 0: nearest-vertex
  mean 0.0085, max 0.240 md3 units. The max is the handful of per-vertex corrections BD22's bake kept outside the index
  finger (`vertex_correction` in its pose file); the shape is the same hold. **These are the acceptance numbers.**

## The acceptance test
`test_brutalpistol.py`: (0) the bone-axis correction K (a signed permutation) fits the imported rest pose to the
library's bind frames; (1) the posed mesh in the palm frame vs the FK reference cloud: max < 0.05 FBX units;
(2) the exported frame vs the shipped frame: mean < 0.02, max < 0.30 md3 units; (3) the gun's six numbers round-trip.
A failure in (0) or (1) is the bone mapping (Blender's FBX importer settings, bone roll, unit scale); fix it in
`HandRig`, not by loosening the numbers.

## Not in step 1 (step 2, on the owner's machine with Claude Code)
Finger snapping (IK: index pad to the trigger face; shrinkwrap: the other pads to the grip surface; a penetration
warning on the bone), the support hand through the same flow, textures in the viewport, the handtable rows (BD22's
`rsq_hands_gen` keeps writing those from the records this exports), the four holds the owner called off (pistol
trigger, flamethrower, shotgun, revolver), then the Project Brutality set (18 BD donors by carry-over, 11 fits).

## Both hands, one rig: the glove
The FBX hand is the rig and the pose source. Ermac's glove look is a skin: in Blender, bake Ermac's `hand.md3`
texture onto the FBX hand's UVs once (Bake, Selected to Active, the Ermac hand wrapped around the FBX hand at the
open pose), and the exported frames carry whichever skin the MODELDEF names. The poses never need to know.
