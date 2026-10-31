# Next: finishing 2.0.2 (written 2026-10-28 19:26, in case this session stops)

Three branches carry the fixes for the owner's 2.0.1 headset pass (OWNER_REPORT_2026-10-27_r3.md items 31-39):

1. `fix-accuracy`: why every gun pulled right. The shot now leaves the drawn muzzle along the bore, and the Ruger and RailGun scopes agree with the bullet. Its early after-numbers: impacts within about 0.2 degrees of the bore line on most guns. See the ACCURACY_NOTES.md on that branch.
2. `fix-guns-202`:
   - the Ruger reload;
   - the reload after switching weapons;
   - the skin tone on the grenade hand;
   - the Moonlight's full animation;
   - the Unmaker click.
   See the notes file on that branch.
3. `fix-options-melee` (head 120f93d, done):
   - True Bullets On/Off;
   - the bolt-check option removed;
   - "Two-Hand Grip (engine)";
   - the kick bash removed, Pistol Whip added (the Moonlight uses the Shotvolver's points);
   - a small melee flash;
   - dual axes and no two-handing;
   - the sword trigger does nothing in VR, with a deliberate-swing gate.

**To finish:**
1. Merge all three into `main`. Resolve any overlap in playerrounds.zs: the accuracy direction fix and the True Bullets cvar must both be kept.
2. Set VERSION to 2.0.2 and run `python build.py 2.0.2`.
3. Boot on doom2 -> brutal22test6 -> BD_VoxelPack -> pack with a fresh default ini: zero script errors from the pack.
4. Give the pack to the owner.

**Queued after he tests 2.0.2 (items 40-42):**
- fit the Ruger glass to the octagon;
- scope alt fire cycles 1x, 2x, 3x, off;
- Assault Shotgun slug on alt fire.
