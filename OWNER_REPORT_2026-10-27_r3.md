# Owner's headset report on BD22_VR-Reloaded_1.99x-lb-r3 (2026-10-27 05:03)

Worked in this repo (lane-b-1.99x). Owner's words are kept where the meaning matters.

## Works / liked
- Dual flick to reload: "quite nice".
- Voxels look good.
- The grenade throw is nice. Throwing in general is probably okay; the axe throw waits for the axe changes below.
- Punching is good, both forward and side to side.
- The two-handed butt strike works and he likes the knockback.
- Minigun: barrels, frame and hand shake when firing. "Whole thing looks damn good".
- He has been getting ammo with Use.

## Bugs
1. **Over-under machine gun:** the casings come out of the barrel, not the port.
2. **Ruger 14 / sniper:** the bullets leave from below the barrel, as if from the magazine.
3. **Minigun:** after firing, the frame stops shaking and the barrels keep spinning a little (correct), but the hand keeps shaking. The hand shake is tied to the barrel spin; it must follow the frame shake.
4. **Unmaker carve:** only the top half of the skull pops out. The RS VR Weapons version (the same mesh) has the whole skull come out.
5. **IDKFA gives neither the revolver nor the shotvolver.** So the shotvolver's slug-shot alt fire can't be verified yet.
6. **Butt strike range:** too short. Enemies back away as you close in, so extend the range. This is the two-handed rifle with a "punch" from the grip hand, i.e. a stock hit.

## Changes
7. **Chainsaw:** remove its swing animation. The player swings it physically. It damages whatever comes into range, not by velocity or momentum like the other melee weapons.
8. **Axe lock-on:** it locks onto one enemy, using the same indicator icon as the Shieldsaw and the saber.
9. **Axe blade orientation:** hits count only when the blade edge leads the motion, judged from the controller's rotation. In the normal ready pose (pointing like a gun) the blade faces out, so a swing down cuts and an arm raised is the flat of the head, not an attack. Side to side counts only when the controller is rotated so the edge faces the way it moves.
10. **Two-handed sword:**
    - stop the weapon snapping to the off hand;
    - the off-hand mesh snaps to the handle below the main hand, and the main hand still drives the attack;
    - possibly more damage in this mode.
11. **Rename the option "Slugrevolver replaces Shotvolver"** to "Shotvolver Swap for Revolver", On/Off.
12. **Revolver and shotvolver:**
    - they should be different meshes;
    - the owner has a measured, reloadable candidate mesh for the normal revolver (ASK HIM FOR IT).
13. **Reloads for guns that have no idea of a magazine** (weapon code changed to add ammo use and magazines):
    - Unmaker: 200;
    - Flamethrower: 100;
    - over-under machine gun: 100;
    - chaingun: 200.
14. **Options to dual-wield every gun,** most of them off by default.
15. **Ruger scope:** today it is a fake glass texture, and the dot doesn't work. It needs one of:
    - a truly see-through red-dot sight, with no magnification and a red dot in it;
    - a real scope that renders a 3x zoom.

## Questions answered (in the reply)
- **"Gun bash"** is a BUTTON: BD22's kick button with a gun in hand does a gun hit instead of the boot. The swing-down gesture with a pistol is the **pistol whip**, a different move. The naming is confusing; consider a rename.

## Added by the owner (2026-10-27 06:50)
16. **Pistol whip (the one-handed downstroke) only works with the OFF hand,** not the main hand. Fix it so the main hand's downstroke whips.
17. **The impact hit flash on EVERY melee hit:** punch, butt strike, pistol whip and gun bash all get the RS_CombatFX hit-flash graphic, with its colour assignable (the RSH0 tint options Original/Blue/Green/Amber/White already exist in TRNSLATE.rsq). Today only the gun bash has it (F4).

## For 2.0 (owner, 2026-10-27 08:15)
18. **A skin-tone slider for the FBX hands,** in both BD22 Weapons Q 2.0 and ModelSwapper 2.0.
    - **Feasible on QuestZDoom 17.3 with no engine change:** a slider of discrete steps. Each step is a pre-recoloured copy of the hand texture, swapped by the option (MODELDEF skin / A_ChangeModel). Gloves could be one of the steps.
    - **To be checked:** whether a smooth slider is possible through a GLDEFS material shader on 17.3. Prove it on the rig before promising it.

## For 2.0 (owner, 2026-10-27 11:21)
19. **Option "Player Ballistics: Hitscan / Bullet":** the player can choose to fire real bullets instead of hitscan.
    - **Source to build from:** the owner's RS_Ballistics (E:\DOOMWork\RS_Ballistics) already turns MONSTERS' hitscans into real flying rounds: `zscript/rsb/enemyfire.zs`, cvar `sv_rsb_enemy_rounds`, speed `sv_rsb_enemy_round_speed` = 80 map units a tic. Port that to the player's hitscans in BD22Q, with a WorldHitscanPreFired hook as recoil.zs already uses.
    - **Rules:**
      - it is a server cvar (it decides where shots go);
      - a round leaves from the drawn muzzle (RSQ_Muzzle);
      - same damage as BD22's hitscan;
      - the kill is credited to the player.

## Revolvers (owner, 2026-10-27 16:00)
20. "I don't need two revolvers and one shotvolver." Keep exactly two:
    - the **Revolver** (BrutalRevolver, the Moonlight);
    - the **Shotvolver** (BD22 `Revolver`).

    Drop `Revolver2` (BD21's slug revolver) and the "Shotvolver Swap for Revolver" option that swaps it in. The Shotvolver's slug alt fire, if any, stays on the Shotvolver.

## FlameCannon hands (owner, 2026-10-27 16:08)
21. The FlameCannon is worn on the arm, so it gets no grip pose.
    - **Measured** (FlameCannon.md3, 1 surface, 5085 verts): the housing runs x 11.9 to 78.5. A forearm-shaped mesh sits inside it, with a hose running back from it.
    - **Gun hand: none is drawn** (owner, 18:46-18:48). The mesh's back is solid. Its texture shows a fleshy slit the hand slides into, and the forearm inside is the arm you see. The wrist is pinned, and the cannon moves so the controller sits at that rear slit with the barrel running along the forearm.
    - **Support hand:** open palm, cupped under the big barrel.

## Bullet visuals (owner, 2026-10-27 20:02-20:24)
22. The bullet look comes from Dakka (ijon, WTFPL): its shotgun's additive tracers, puffs and sparks.
    - It is used for every player shot, including Bullet-mode rounds.
    - Menu: "Shot Tracers: Off / Dakka" and "Pump Shotgun Spread: Stock / Enhanced".
    - The Ruger fires a piercing sniper bullet, with the rail's damage and piercing; the Railgun stays a rail.
    - Round speed is fixed at 80. Skin tone gets 16+ steps, from human tones to blue, purple and green.
    - **Later:** more bullet styles for Player Ballistics, added over time. Each one is the owner's pick; none is built by default.

## Variants share fits (owner, 2026-10-27 20:30, standing rule)
23. The Purist, Tactical and any other variant of a gun use the same mesh as the Brutal gun, so they use the same pose.
    - Never fit a variant. Copy the Brutal gun's hand, support and dependent rows to it.
    - Farm records so far: no Purist or Tactical fit was ever run. One PuristRifle support job was briefed by mistake on 2026-10-27 at 20:26. The lane was told at 20:30 to drop it and kill it if already queued.

## Open calls answered (owner, 2026-10-27 20:45-20:47)
24. **Revolvers:**
    - The Shotvolver stays, with its slug alt fire. No slug revolver ever replaces it.
    - New option "Moonlight Replaces Pistol" (default Off): the Moonlight replaces the Brutal Pistol at the start, in map pickups and in drops.
    - New option "Start With Two Moonlights" (default Off): you start dual, with a 72-round cap.
    - SUPERSEDED 2026-10-28 06:46 (owner, headset, 2.0): "Change Moonlight to take BrutalPistol ammo, consume 3 ammo per shot,
      reloads after 18 ammo consumption." No Moonlight rounds or 36 / 72 cap any more (2.0.1, HANDOFF "Moonlight on pistol ammo").
    - The Moonlight-replaces-Shotvolver option is gone.
25. **HUD ammo:** shows the magazine and the reserve by default, with a "Reserve only" option.
26. **Ammo balance:** the loaded magazine counts on top of the max carry; the cap is the reserve only.
27. **Recoil:** a design session with the owner after the 2.0 headset pass. Not part of 2.0.

## Melee fits approved (owner, 2026-10-27 22:43)
28. The owner saw the offline fit sheets for the chainsaw and the sword and is happy with them.
    - **Chainsaw:** rear handle with the index finger on the trigger, plus the top-handle support.
    - **Sword:** two hands on the hilt.
    - Port both as fitted (branch lane-melee-hands, fitfarm_results/Chain_saw and DSweap).
    - Still open: the axe (pen 0.71 cm) and the grenade (not ready, needs a re-solve).

## Hands approved from the sheets (owner, 2026-10-28 00:03)
29. The owner approves these from the sheets:
    - Unmaker gun hand: a fist on the rear hook (r4).
    - MiniGun support: a fist on the side handle (r4 refined, pen 0.09).
    - FlameCannon: no gun hand, placed at the rear slit, open palm under the barrel (r4 under40).
    - Rifle support (support fix batch 1).
    - Rocket_Launcher support (redone, batch 3) and RailGun support (palm under the box, batch 3). The RailGun barrel redo is cancelled.
    The Unmaker support (a flat palm) is still being redone.

## For later (owner, 2026-10-28 06:27)
30. **The Ruger scope looks bad; the RailGun scope is fine.**
    - The RailGun's lens edge is smooth and round.
    - The Ruger's (XM21.md3, glass surface 10) has a jagged, broken inner ring, and the live picture shows square-cut corners inside it (seen in scope_toggle.png).
    - Fix later: rebuild or smooth the Ruger's lens ring and glass surface so the picture fills a clean circle, matching the RailGun. Not part of 2.0.

## Headset pass on 2.0.1 (owner, 2026-10-28 18:24)
**Now:**
31. **Every gun pulls to the right** (horizontal), for both true bullets and the Dakka tracers: chaingun, RailGun, Ruger and the rest. The scopes are useless while the shot misses their centre. The scope and the bullet must agree.
32. **Ruger:** hand poses are bad, it fires skewed right, and it does not reload.
33. **Rifle:**
    - The hand inserting a grenade does not take the selected skin tone (same on the over-under MG).
    - Empty the mag, switch weapons without inserting a new one, switch back: you can no longer grab ammo to insert.
34. **Moonlight:** the mesh doesn't animate and the reload is missing a lot of frames. Use all the model's animation frames.
35. **Unmaker:** the skull insert makes a horrid noise; replace it with a click like the rifle's.
36. **Melee impact flash** is way too large.
37. **Axe:** no two-handing (or behave like the sword); the owner wants dual-wielded axes and never to two-hand them.
38. **Sword (DSweap):** fires several attacks all the time; it should respond to a deliberate swing.
39. **Options:**
    - "Shot Tracers" should not be its own option. True Bullet On = our rounds with the Dakka look; Off = stock BD22 hitscan and tracers.
    - "Check the Chamber by Hand" is confusing: explain or rename it.
    - "Two-Handed Steadying" is confusing (it is the engine's own two-hand cvar).
    - "Gun Bash (kick key)": the owner asked twice for a pistol whip, not a kick-key bash.

**Good:** Shotvolver, SMG (mostly), axe (awesome), SSG, pump (almost excellent), assault shotgun (lovely), RailGun scope (beautiful), flamethrower reload (good surprise).

**Later:**
- Revolver hand a little low; Shotvolver hand a tad higher.
- SMG support fingers should close more.
- SSG: the off hand closes the breach.
- Pump: the grip hand's middle finger should close more.
- Over-under MG: the support thumb's wrap; the MG doesn't rack.

## Queued: NOT to start until the owner has tested 2.0.2 (owner, 2026-10-28 18:29)
40. **Ruger scope glass.** Its glass texture is round but the scope housing is octagonal, so the picture isn't centred and looks rough. Fit the glass and picture to the octagon (see item 30).
41. **Scope alt fire on the Ruger and the RailGun cycles 1x, 2x, 3x, off, then repeats.**
42. **Assault Shotgun:** add a slugshot as its secondary fire.

## 2.0.2a (owner 2026-10-28 19:47-20:11)
Shown on the rig:
- Instant Weapon Switch (option, default On): every switch is ready the tic it is asked (log sw5).
- Pump slug alt fire now takes a shell and needs the pump (log slug6). The main-hand jump skipped the Fire path.
- The Moonlight is renamed Silvergun (pickup, tag, menus). Settings keep their names, so saved options carry over.
- Booted on the load order: only BD_VoxelPack's 4 errors.
Built, not shown: grenade pin by off trigger only; axe lock (8 deg pick, mark above the head, the thrown
axe homes on the lock); the Unmaker skull-out click.
- SSG flick reload (owner 20:22, rebuilt as 2.0.2a): every SSG flick goes to SSG.dec RSQ_FlickReload, from ready or while
  it waits open for the hand reload. Rig flick5: empty, flicked, 2 shells in and 2 taken from the reserve, shut, fired again.
  One SSG shown; dual SSGs use the same path, not shown.
- Assault Shotgun slug alt fire (option, default On): one slug per pull of alt fire, down the Fire path. It takes
  a shell from the gun and uses the pump's slug sound (rig rl1: 20 -> 18 for two slugs).
- Rocket Launcher lock-on alt fire (option, default On): hold alt and up to 3 DIFFERENT enemies within 10 deg of the
  barrel are locked (QuestSaber mark); let go and one rocket per lock goes down Fire, each homing on its lock.
  Rig: the hold loop and the search run (rl2-rl10: no ammo used, no misfire). Lock + salvo NOT shown: the rig
  could not put an enemy in front of the gun (summon made none). Headset check.
- 2.0.3c (owner 20:59, "both"): the salvo is always 3 rockets, shared round the locks (3 locks: one each; 2: A B A; 1: all three). Booted on the load order: only BD_VoxelPack's 4 errors. Rocket lock-on is still to be checked in the headset.
- 2.0.3d (owner 21:53): "Melee Hit Flash" On/Off (rsq_bash_flash, default On); the old picker is now "Melee Hit Flash Style". Booted with only the 4 BD_VoxelPack errors. Not run on the rig (an option: owner checks).
- 2.0.3e (owner 22:23): the axe TAGS an enemy. A tag stays wherever the hand points (it was dropped beyond 12 deg, so winding up lost it). It goes when the enemy dies, leaves range, or is out of sight for 2 s; it is kept 3 s after a let-go that was not a throw. Boot only; headset check.
- 2.0.3f (owner 00:24): doors lifted by hand, ported from RSQ_UBQSeries DistanceGrab door.zs (d8b4150). How to: an empty hand on the door face (off hand without a gun; main hand bare or fists), take hold with the off grip, Use, or the palm turned out, then lift. Let go past 40% open and the door finishes by its own special; earlier, it drops shut. Option "Lift Doors by Hand". Boot only (zero pack errors); headset check.
- 2.0.3g (owner 00:42): pistol whip needs a harder swing: 5.0 (was 3.2), with a slider "Pistol Whip: Swing Needed" (2-10). Boot only.
- 2.0.3h (owner 02:05): the Unmaker's firing loop (Unmaker/Loop, looping on channel 6) kept playing through the reload when the skull emptied mid-fire (Hold jumps to Reload without NoAmmo's stops). Reload and RSR_Start now stop it. Boot only.
  Also: the skull hitting the floor (rsr/bigdrop) is silent; the Unmaker reload now sounds only the out click and the in click.
- 2.0.3i / axe.pk3 hotfix (owner 07:00-07:04): the off-hand axe is its own off-hand weapon. No free second axe; the second comes from picking one up (max one per hand). With the axe in the main hand the Dual key puts the off axe in the off hand; it also cycles with the off fist (slot 1). It is put away when the main hand switches to a gun. A thrown axe (either hand) is gone until an axe is picked up. Axe cuts reach 33% further from the hand. Rig: on 2.0.3h + axe.pk3 one axe gives no off copy (2.0.3h alone gives one); zero pack errors. Throws, cycling and reach are a headset check.
