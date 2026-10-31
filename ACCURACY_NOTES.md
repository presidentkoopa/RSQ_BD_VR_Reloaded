# fix-accuracy (owner report item 31-32, 2026-10-28): "all the guns pull to the right"

Rig only, not headset-confirmed. Depot rig, QZD 17.3, doom2 -> brutal22test6 -> BD_VoxelPack -> pack; 0 pack script errors.

## Cause (measured)
- In VR every shot goes down the engine's AttackDir = the CONTROLLER's forward (hw_vrmodes.cpp MapWeaponDir).
- The 2.0 hand ports turned every gun in the hand (MODELDEF AngleOffset 3.854 / PitchOffset 3.363 / RollOffset 10.974,
  the approved pistol's r5 aim) and moved muzzle, scope, casings, reloads with the gun (Depot port_gun.py) -- but never
  the shot direction. Port records (Depot sets/bd22q/handfit/fits/ported_*.json) R @ (1,0,0) = (0.99602, 0.06710, 0.05866):
  the drawn barrel points 3.85 deg LEFT and 3.36 deg UP of every shot. 1.92 bores run along the controller's forward
  (tools/accuracy/bore.py, mesh-measured: Rifle, RailGun, Plasma, Machinegun, MG42, Ruger within 0.35 deg).
- Code: src/zscript/rsq/muzzle.zs WorldHitscanPreFired re-fired with e.AttackAngle/e.AttackPitch unchanged (controller
  forward); rails and player missiles were not turned at all; scope.zs Axis = the glass axis turned with the gun.
- Before (2.0.1), every gun, Hitscan and Bullet: ~3.8 deg right, ~2.8 deg low of the drawn bore (17 units at 256,
  ~70 units right at 1024). Ruger: 63 right / 53 low of the scope centre at 1024. RailGun: 84 right / 72 low.

## Fix
- muzzle.zs: RSQ_Muzzle.Bore / AimOffset: every shot of a gun with a bore is turned onto the drawn barrel: hitscans and
  pellets (angle/pitch), rails (angle/pitch offsets, re-fired by the player so damage stays his), player missiles
  (velocity turned, started at the muzzle: plasma, RailGun beam missiles, BD22 DecorativeTracers, rockets...).
  BD22 helper missiles (casing spawners, flashlight/alert probes, melee strikes) are left alone.
- Scoped guns zeroed: shot aimed at the scope camera's centre line 30 m out (ZERO_M); scope.zs Axis = the bore.
- MP40 muzzle row added (it had none). Off-hand (dual) shots get the same turn (NOT yet tested on the rig).

## After (tools/accuracy/results/after_fix.txt)
Mean impact from the bore line, both modes, 256 and 1024: within BD22's own spread (|mean| <= ~1 deg, most < 0.3 deg);
shots start at the drawn muzzle (start_cm 0.0). Plasma 0.00/0.00. Ruger at 1024: 0.01 right 0.03 up of the scope
centre; RailGun 0.00 / 0.20. At 256 (inside the 30 m zero) scoped shots land 0.8 (Ruger) / 2.3-3.3 (RailGun) units low.
Scope frames (tools/accuracy/results/frames, left eye 8 cm behind the lens, wall 1024 units, 4x lens crops):
green dot = drawn bore meets the wall, red = scope camera centre line, blue = where the shot landed (probe).
- before Ruger: green and red in the lens, the impact (63 right, 53 low) out of the lens. after Ruger: the impact sits on them.
- before RailGun: red 19 units above / 12 left of green, impact out of the lens. after: red, green and the impact together
  (log: 0.00 right, 0.20 up of the scope centre).
Known gap: the Ruger lens ring is rough (item 30, unchanged).
