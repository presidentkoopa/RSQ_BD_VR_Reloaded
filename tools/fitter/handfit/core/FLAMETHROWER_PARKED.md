# Flamethrower2 hand: PARKED (owner, 2026-10-27 05:30)

- **Current Flamethrower hand: r5.** Pistol-style grip with the finger on the lever, which the owner liked. The off hand is an open palm under the tank, and the trigger squeezes on fire.
  - Pack: out/BD22Q_192_fbx_headset_r5.pk3, sha ff355a24...
- **r6 was rejected:** the hand sits beside the handle.
- **r7 was stopped:**
  - a true gas-pump wrap with a level nozzle needs the drawn hand turned 78.5 deg off the controller;
  - that breaks the support hand (S6 red, 22.5 cm);
  - the round took more than an hour with no pack.
- **Carry forward into BD22 2.0:** r6's flame-at-the-spout code (zscript/rsq/flamespout.zs). Its tip position must be recomputed for the r5 gun move.
- **Lesson:** a grip whose handle axis is far from the controller's grip axis (here 58 deg) is flagged at the first measurement and parked or decided by the owner. It is never ground on.
- **Rule for every batch from now on:** a fixed time box, and the sheet goes to the owner at the box, whatever its state.

## The owner's correction (2026-10-27 05:36)
"The flamethrower grip thing is the same pose as the shotgun support / pump pose."
- The gas-pump grip IS the pump-shotgun support grip: palm sideways, wrapped round a bar along the bore, fingers under. In VR the off controller is held pistol-style while the drawn hand wraps the pump, so the 58 deg "conflict" is the normal pump case, not a blocker.
- When the Flamethrower is revisited: the gun hand = the pump/foregrip pose (from the 1.92 pump rows or the FBX `hold_foregrip`) on the handle, with the index moved onto the lever. The gun hand's wrist pin is relaxed the same way support hands relax theirs.
- **Rule for every batch:** start from the existing named poses (grip, trigger, squeeze, wrap/vgrip, pump, under, cup) and solve a new grip from scratch only when none fits.
