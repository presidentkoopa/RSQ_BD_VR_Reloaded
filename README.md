![BD22 VR Weapons](renders/hero.gif)

# BD22 VR Weapons 2.0

**Brutal Doom v22 in VR. Your hands. Every gun.**

Grab the rifle by its handguard and the trigger is under your finger. Rip the magazine out, reach
to your belt, slam a fresh one home, and rack it. Break the Super Shotgun, thumb in two shells, flick
it shut. Hold the Ruger to your eye and the scope is a real 3x window, not a sticker. Pull the pin
with your other hand and throw. Choke up on the chainsaw by its top handle. Swing the Dragonslayer
two-handed. Every gun in Brutal Doom, held, aimed, fired and reloaded with your own two hands.

Project conceptualized, directed and coordinated by **PresidentKoopa**. All coding done by
agentic **Claude**.

A VR weapon pack for **Brutal Doom v22** (`brutal22test6.pk3`) on **QuestZDoom 17.3**, built for
**standalone Quest**. It runs on the stock engine with no engine changes. It's an add-on: Brutal
Doom stays Brutal Doom. It replaces none of its guns, every gun fires at Brutal Doom's own rate
and does its own damage, and with the options off it plays exactly as Brutal Doom shipped.

![Every weapon in hand, 2.0](renders/2.0_every_weapon_in_hand.png)

## Install

Download the pk3 from the Releases page and load, in this order:

```
doom2.wad  ->  brutal22test6.pk3  ->  BD_VoxelPack.pk3  ->  03_BD22_VR-Reloaded_2.0.3y.pk3
```

Use Doom 2, not Freedoom: the voxel pack names Doom 2's own sprites.

To build it yourself: `python build.py` zips `src/` into `BD22_VR-Reloaded_<VERSION>.pk3`.

## Changelog: 2.0.3h to 2.0.3y

Newest first. The current build is in [pk3/](pk3/) as `03_BD22_VR-Reloaded_2.0.3y.pk3`. Builds marked
*rig only* were tested on the development rig.

- **2.0.3y** (11-06, *rig only*, not headset-confirmed: loads on the full order with no script error from the pack; the
  off-hand versions, the off-hand pistol whip on a door, the pump, the Silvergun, No Trigger Punch and the grenade
  stand-down shown on Brutal Doom's own guns):
  - **One gun, either hand.** Picking up a gun that has an off-hand version gives you both (the off-hand one loaded). Whatever puts it in your off hand (a holster, the wheel, Distance Grab, switch hand) it is the
    off-hand version there, and back in the main hand it is the main gun, rounds and all. With its Dual Options row off,
    a gun is in one hand at a time. The off-hand versions now pass between hands, and stay in the off hand until you
    move them. An axe pulled with Distance Grab into the off hand is always the off-hand axe, equipped.
  - The pistol whip works in the off hand. The pistol whip and the butt strike work a switch or door they hit (like
    Use; the line's action counts, not its texture), with "Punch Switches Open".
  - Butt strike: reaches half as far again, a straight shove counts as well as the pivot, and **Butt Strike: Swing
    Needed** (2.4 m/s, was a fixed 3.6).
  - A Silvergun you pick up arrives loaded, and you start with 18 pistol rounds more (the Silvergun's ammo).
  - The off trigger no longer throws an automatic animated jab from the free off fist, and **No Trigger Punch** (On):
    in VR, BD22's fists throw no canned jab or cross on trigger / alt fire (throwing a grabbed enemy or barrel,
    the shield and fatalities still work). Punches are the ones you swing yourself.
  - The pump shotgun ejects no shell on the pump after you load it from empty.
  - **Use RSQ Grenade Instead** (Off): with RSQ Grenade loaded, Brutal Doom's grenade stands down.
- **2.0.3x** (11-05, *rig only*): with an RSQ series item in the off hand (the saber or Force hand, the Zippo or
  cigarette, the ShieldSaw, the flare or flashlight, the whip, a grenade or a glove), flicking the main gun down reloads
  it with BD22's own reload; the hand reload still needs the free off hand, as before.
- **2.0.3w** (11-04, *rig only*): on PCVR (SteamVR), walking and strafing with the hands still no longer swing the axe
  or any melee. 2.0.3s fixed this for the way Quest places the hands; PCVR places them off the eye, which trails the
  body by up to a step between frames.
- **2.0.3v** (11-04, *rig only*): Shoot Thrown Grenades tests only the ray of the hand that fired (a hand that was just
  pointing no longer sets a grenade off), and the kill goes to whoever shot the grenade.
- **2.0.3u** (11-03, *rig only*): **Ammo From the Rig's Pouch Only** (On). With RSQ Tactical Rig's ammo pouch (just
  left of the belt-buckle grenade), every belt reload takes from the pouch only: magazines, drums, boxes, shotgun
  shells, break-open and cylinder rounds, the underbarrel 40 mm. A press at a holster, the buckle or the flare holster
  never hands you ammo. Without the rig, reloads work exactly as before.
- **2.0.3t** (11-03, *rig only*): **Shot Grenade Reach** slider (0.10 to 0.35 m, default 0.35; it only tightens).
  Shooting a thrown grenade is more reliable: a projectile's whole path over the tic is checked, a bullet names the
  exact grenade it hit, and the railgun counts.
- **2.0.3s** (11-03, *rig only*): walking, strafing, stairs and snap turns no longer swing the axe, the pistol whip or
  any melee while your hands are still. The hands are now measured against the frame they were drawn in.
- **2.0.3r** (11-03, *rig only*):
  - **Shoot Thrown Grenades** (On, with "Only in Slow Motion", Off): your bullet or damaging projectile sets off your
    thrown grenade where it is. The kill is yours, and RSQ Score pays a skeet in the air.
  - **Faster Grenades in Slow Motion** (Off) with a speed slider.
  - The teeth pin pull now works: it reads your real mouth from the headset (lips to under the chin, "Teeth: Mouth
    Reach" 0.15 m), and grip plus trigger counts as the squeeze.
- **2.0.3q** (11-03): the off-hand axe cuts and throws like the main-hand axe (its blade was read upside down). The
  pump shotgun waits for your hand on the pump right after a reload from empty, without a dead trigger pull.
- **2.0.3p** (11-03): pull the grenade's pin with your teeth (RSQ Grenade's face pull, ported). The off-hand ring
  pull is unchanged.
- **2.0.3o** (11-03): the Incendiary Launcher is switched off unless "Extra weapons with cheats" is on; the Grenade
  Launcher takes its place.
- **2.0.3n** (11-02): Two-Hand Aim removed after the headset test showed the scripted gun turn lagging behind the
  hands. Two-handing is the engine's own Two-Hand Grip again, and shots go down the gun's own barrel.
- **2.0.3k to 2.0.3m** (11-02): Two-Hand Aim test builds (the Rifle first, then all 21 two-handed guns). Superseded
  by 2.0.3n.
- **2.0.3j** (11-01): the axe as a throwing weapon with RSQ Distance Grab. A pulled axe goes to the hand that pulled
  it, or is stored if that hand holds a gun. The berserk wall axe follows the one-axe-per-hand rule, and the door lift
  steps aside for Distance Grab's.
- **2.0.3i**: the off-hand axe is its own off-hand weapon. No free second axe (one per hand, from pickups),
  a thrown axe is gone until you pick one up, and axe cuts reach 33% further.
- **2.0.3h**: the Unmaker's firing loop stops when the skull empties mid-fire, and its reload sounds only the
  out and in clicks.

## What's new in 2.0
Everything here was checked on the test rig on the load order above, with no script errors from
the pack. It has not yet been confirmed in a headset.

### Hands on every gun
- **New hands on every weapon**, both hands: the hand that holds the gun, with the finger on the
  trigger, and a support hand that wraps the gun's forend, pump, handguard or foregrip. The gun is
  moved to fit your hand, and everything on it (muzzle, ejection port, reload points, scope) moves
  with it. Each grip started from the 1.92 hold on that gun.
- **Melee:** chainsaw (index on the real trigger, other hand on the top handle), sword (two hands
  on the hilt), axe (on the haft). Their hit points moved with them.
- **The FlameCannon** is worn: your hand goes in through the slit at the back, and the flame now
  starts at the nozzle (it used to start 27 cm away). Open palm under the barrel.
- **Fists, the free off hand, the grenade hand and all 25 reload holds** (every magazine, shell,
  rocket, the Unmaker skull, the Silvergun round) use the same hands.
- **Hand Skin Tone:** 18 steps, from porcelain to ebony, plus grey, green, blue, purple, red, gold
  and a black glove.

### Scopes
- **Ruger and Railgun: a live 3x view through the lens**, on by default. Alt fire turns the scope
  on and off, to save performance. On the Ruger this replaces Brutal Doom's zoom.

### Shooting
- **True Bullets: On / Off** (default On). On fires real rounds from the muzzle at 80 units a tic,
  with the same damage as Brutal Doom's hitscan, drawn with Dakka's bright tracers and impact sparks.
  Off is stock Brutal Doom: hitscan, its own tracers and puffs (and the Ruger's rail trail), no
  Dakka effects. (This one switch replaces "Player Ballistics" and "Shot Tracers".)
- **Pump Shotgun Spread: Stock / Enhanced:** Enhanced spreads up and down too. Same pellets and
  damage.
- **Ruger** (True Bullets On) fires a sniper round that pierces like Brutal Doom's rail, with the
  same damage. The beam is gone.
- **Dual wield:** off-hand shots now leave the off-hand gun's muzzle.

### Revolvers and ammo
- Two revolvers: the **Shotvolver** (its slug alt fire is now on by default) and the **Silvergun** (called the
  Moonlight until it was renamed). The Silvergun takes the Brutal Pistol's ammo (2.0.1): each shot costs 3 pistol rounds, so a full
  six-shot cylinder is 18. A reload moves 3 pistol rounds per chamber from your pistol reserve; two
  Silverguns share that reserve. Its HUD reads shots in the cylinder (0-6) | pistol rounds in reserve.
- Options: **Silvergun Replaces Pistol** (start, pickups, drops) and **Start With Two Silverguns**.
  Both are off by default.
- **HUD Ammo:** the magazine and the reserve (e.g. 24 | 120), or Reserve Only.
- **Ammo on top:** a loaded magazine never counts against what you can carry.
- **The Minigun has its own ammo:** 400 in reserve (800 with a backpack), plus its 200-round
  magazine.

### Fixes
- Giant shell casings when firing shotguns. Fixed.
- The dual Shotvolver stopped the main gun firing after one off-hand shot. Fixed.
- The Shotvolver's slug alt fire also fired a free pellet blast. Fixed.
- The Purist Sniper showed an empty hand. Fixed. The Purist Rifle shows its grenade tube, and its
  alt fire does nothing.
- Butt-strike and pistol-whip hits now land at the gun you see.
- The grenade was drawn 1.45 cm off. Fixed, and the throw now leaves from the grenade in your hand.

### Options and melee (2.0.2, rig only, not headset-confirmed)
- **Pistol Whip** (on by default): swing a pistol or revolver (Shotvolver or Silvergun) into something. It has its own
  option row. The kick-key "Gun Bash" is gone; the kick key is Brutal Doom's boot again.
- **Melee hit flash** is a small spark where the blow lands (about 38 cm across; it was 2.3 to
  2.8 m).
- **Two axes, never two hands.** The axe no longer goes two-handed. Get the axe and a second one
  comes with it; press the Dual key to hold one in each hand. Each axe swings, cuts and throws from
  its own hand (VR throwing: hold that hand's trigger, swing, let go). A thrown off-hand axe comes
  back when you pick an axe up. Dual Options > Axe turns it off. (Since 2.0.3i there is no free second axe: one
  per hand, from pickups.)
- **Sword:** a blow needs a deliberate swing: the blade's point must travel about a metre at
  speed, and after a swing there is a third of a second before the next one, so one swing is one
  attack. In VR the sword's trigger does nothing (no Brutal Doom combo, lunge or view turn); flat
  screen keeps the combo. On the rig: hand jitter, sliding and wrist turns gave 0 attacks; one swing gave exactly 1.
- **"Check the Chamber by Hand" is removed** (it was off by default and only let the off hand pull
  a loaded gun's handle back to look).
- **Two-Hand Grip (engine)** (was "Two-Handed Steadying"): QuestZDoom's own two-hand setting,
  unchanged. On: grip with your off hand near the gun to steady it with both hands.

### Two-handing is the engine's Two-Hand Grip (2.0.3n; rig only, not headset-confirmed)
- Hold a gun in two hands with QuestZDoom's own **Two-Hand Grip (engine)**: off hand near the gun, press the off
  grip. The engine points the gun from your gun hand through your off hand, the support hand shows on the gun, and
  the shots go down the gun's own barrel from its muzzle, exactly as in 2.0.3j. Let go of the grip to release.
- While the grip holds, the engine hides whatever the off hand itself holds and switches off an off-hand weapon (it
  doesn't fire). The support hand drawn on the gun is not affected.
- **Fix:** a magazine or break-open reload that started while you held the grip (the Rifle running dry, the SSG
  opening after both barrels) hid the support hand, and the engine hid the empty off hand: no off hand at all. Now the
  support hand stays on the gun until your off hand takes something.
- On the rig (QuestZDoom 17.3, the owner's load order) the support hand showed and released correctly on the Rifle,
  Shot_Gun, SSG, Minigun, Rocket Launcher, Railgun, pistol, sword, chainsaw and axe; the Shot_Gun's hand pump worked
  while held. Frames and log: `renders/2.0.3n/`.

### Switched-off guns (2.0.3o)
- Switched off in this pack, each replaced by a stand-in wherever it would appear: MP40 (SMG), MG42 (Minigun),
  Devastator and Hellish Missile Launcher (Rocket Launcher), Flame Cannon (Flamethrower), and now the **Incendiary
  Launcher** (Grenade Launcher, its neighbour in slot 5).
- **Extra weapons with cheats** (Options → BD22 VR Weapons) brings all six back, through cheats only (give all, idkfa,
  give). Maps always place the stand-ins. On the rig: `give IncendiaryLauncher` gave the Grenade Launcher; with the
  option on it gave the real launcher. Log: `renders/2.0.3o/`.

### Pin the grenade with your teeth (2.0.3p; rig only, not headset-confirmed)
- The grenade's pin pull now matches RSQ Grenade's. As well as the off-hand ring, you can **pull the pin with your teeth**:
  squeeze the grenade's trigger and hold the grenade at your face (within 0.47 m of your eyes) for 12 tics. The squeeze
  alone never cooks or throws. Once the pin is out, the trigger is your grip on the spoon, as always: let go while swinging
  to throw, or while still to cook. The teeth pull another pin only after your hand has been more than 0.71 m from your
  face, or after you let go of the trigger.
- The off-hand ring works exactly as before, and it can put a pin back in however it came out.
- Options → BD22 VR Weapons, next to VR Throwing: **Pin With Your Teeth** (On by default), **Teeth: At**, **Teeth: Again
  Beyond**, **Teeth: Hold**. These have RSQ Grenade's defaults.
- On the rig, on the owner's full load order: pin out on the 12th tic at the face; no pin with the option off; no second
  pin without leaving the face; the ring still pulls and re-pins. Log: `renders/2.0.3p/`.

### Off-hand axe and shotgun pump fixes (2.0.3q; rig only, not headset-confirmed)
- **The off-hand axe cuts like the main-hand axe.** The engine draws the left-hand weapon mirrored, and the swing code
  had the off axe's blade upside down: the edge and head were worked out below your wrist, so the edge-first rule threw
  out every real chop. Now the off hand cuts on the same swings as the main hand (chop, drop, wrist snap, lunging chop,
  edge-first side slash) at the same speed (about 4.5 m/s at the blade), and refuses the same spine-first ones. The off
  axe's throw now leaves from the drawn axe head, as the main hand's does (it used to leave from below the wrist).
- **The pump shotgun pumps straight after a reload from empty.** With Auto Reload off, an empty shotgun loaded with
  shells pushed into the port used to sit there until you pulled the trigger once (nothing happened), and only then
  could you pump. Now the last shell in puts the gun straight into the pump wait: rack it and fire. A gun that still
  has a round chambered loads exactly as before. The reload-button and auto-reload paths already waited for the pump.
- On the rig, on the owner's full load order. Logs: `renders/2.0.3q/`.

### Ammo From the Rig's Pouch Only (2.0.3u; rig only, not headset-confirmed)
- Options → BD22 VR Weapons, under New magazine from: **Ammo From the Rig's Pouch Only**, On. With RSQ Tactical Rig loaded
  and its Ammo Pouch on, every reload that fetches from the belt takes ONLY from the rig's pouch, the one just left of
  its belt buckle (the right for a left-hander): magazines, drums and boxes, shotgun shells, break-open and cylinder rounds,
  the 40 mm under the Rifle and the Machinegun. A press anywhere else, the buckle and every other rig holster included,
  gives nothing. Without the rig (or with the rig's pouch off, or this row off) every reload keeps its own rule exactly.
  Found by name (the rig's "pouch.at" service): BD22 VR needs nothing loaded.
- On the rig, the Brutal Doom order with RSQ Tactical Rig and RSQ FnF (TacticalRig `tools/rigtest/holsterprobe/evidence`,
  `trh_POUCH*`): a Rifle emptied, its magazine out; off-hand presses at the buckle, the off hip, the off chest holster and
  the flare holster each refused ("the rig's pouch only"), at the pouch a magazine taken (EMPTY -> CARRY); a Shot_Gun:
  the buckle refused, the pouch gave a shell. Left-handed the same. BD22 alone: every one of those presses took one, as
  2.0.3t did.

### Shot Grenade Reach (2.0.3t; rig only, not headset-confirmed)
- Options → BD22 VR Weapons, under Shoot Thrown Grenades: **Shot Grenade Reach (m)**, 0.35 by default (12 map units,
  as 2.0.3r), down to 0.10. It only tightens: a shot must pass this close to a thrown grenade to set it off. (BD22 VR's
  menu has no Reset All; the default is 0.35.)
- Two fixes to shooting thrown grenades: a fast shot or projectile is now caught along its whole path through the tic
  (it could pass between two tic-end positions unseen), and a shot names the grenade itself, not where it was (a fast
  grenade had moved on by the time the shot was handled). The railgun now sets grenades off too (it has its own hook).
- On the rig (`renders/2.0.3t/`): reach 0.10: a pistol shot 5 units (0.15 m) off the grenade's centre set nothing off,
  one dead on (0.7 units) did; the default 0.35: 8.5 units off set it off, 15.3 units off did not. A rocket at 20 a tic
  and one at 100 a tic crossing a grenade in flight both set it off (the fast one's tic-end positions were 50 units
  either side of it); the railgun set off a grenade held in the air.

### The teeth pin pull at your mouth; shoot thrown grenades (2.0.3r; rig only, not headset-confirmed)
- The owner never saw the teeth pull fire in his headset. It looked for the grenade within 0.47 m of `player.viewz`,
  the pawn's fixed eye (1.55 m for BD's player), not your headset; and it counted only the trigger. QuestZDoom's
  default button layout (`vr_secondary_button_mappings` on) makes the main grip a shift key, so squeezing grip and
  trigger together (a fist round the grenade) sends alt fire and never fire: that squeeze could never pull the pin.
  The ball round the pawn's eye also missed a seated player's mouth and caught a grenade held at the chest.
- Now: bring the grenade to your **mouth** (lips to just under the chin, measured from your headset, as RSQ Tactical
  Rig's cigarette does) and squeeze, with the trigger or with grip and trigger, for 12 tics. The controller, the drawn
  grenade or its ring may be the part at your mouth. A small wobble out of the zone no longer restarts the count.
- Options → BD22 VR Weapons: **Teeth: At** is now **Teeth: Mouth Reach** (0.15 m round the lips-to-chin line). Pin
  With Your Teeth, Teeth: Again Beyond and Teeth: Hold are unchanged. The off-hand ring is unchanged.
- **Shoot thrown grenades** (Options → BD22 VR Weapons, **Shoot Thrown Grenades**, On): a bullet or a projectile of
  yours (a rocket, plasma) passing within 0.35 m of a thrown grenade sets it off where it is, credited to you (in co-op
  anyone can shoot anyone's thrown grenade, and the shooter gets the kill); only the hand that fired counts; shot in
  the air it counts as a skeet for RSQ Score's Trap Shot. It must be 6 tics (0.17 s) out of your hand first. Punches
  never set one off; a grenade in your hand cannot be hit. **Only in Slow Motion** (Off): only while RSQ SlowMo has the
  world slowed.
- **Faster Grenades in Slow Motion** (Off) and **Grenade Speed in Slow Motion** (0.50): RSQ SlowMo slows a thrown
  grenade with the world; with this on it moves that much of the way from the world's speed up to real speed (at the
  world's 0.25: 0.625), still visibly slow, so you can throw and then shoot it. Its fuse stays slowed with the world.
- The grenade works in the main hand only, as before (BD22's VR grenade reads the main hand's weapon).
- On the rig (`renders/2.0.3r/`), each pose in its own run on brutal22test6 + voxels + this pk3 + XMVE, headset
  1.65-1.75 m, the controller 12 cm under and 10 cm in front of the eyes. 2.0.3q: the pin came out with the trigger
  alone standing, but not with grip and trigger together (the command carried alt fire only), not seated (headset
  1.20 m: 0.48 m from the pawn's eye), and it did come out with the grenade at the chest. 2.0.3r: out on the 12th tic
  at the mouth in all six poses (standing, chin, upright hold, grip and trigger, 1.75 m with `vr_height_adjust` 0.3,
  seated), never at the chest. A grenade put in the off hand (the engine's switch-hand) does nothing in BD22 VR, ring
  and throw included, as before. Shooting (`renders/2.0.3r/shoot_bd.log`, with RSQ SlowMo): a rocket through a
  grenade held in the air 3 tics after the throw set nothing off, one at 19 tics set it off (a skeet); a pistol shot
  set one off; Shoot Thrown Grenades off: a rocket set nothing off; slow motion at 0.25 took a thrown grenade from 20.8
  to 5.2 units a tic, Faster Grenades on to 12.8 (x0.63).

## What was new in 1.99

### Every gun reloads by hand
Every gun that isn't a melee weapon reloads with your hands: **23 guns**. The BFG and BFG10k stay
as Brutal Doom made them.

| How it reloads | Guns |
|---|---|
| Magazine | Rifle, Pistol, SMG, MP40, Assault Shotgun, Railgun, Plasma Gun, Ruger, Rocket Launcher, Machinegun (100-round box) |
| Drum, canister or box | MG42 belt drum, Flamethrower canister, Unmaker skull, Minigun ammo box, Hellish launcher's rear drum |
| Cylinder | Incendiary Launcher (six shots) |
| Bay or block | Devastator loading bay, Nuker warhead block |
| Pump | Shotgun |
| Break-open | Super Shotgun, Grenade Launcher, Shotvolver, Revolver (Silvergun), and the 40 mm under the Rifle and the Machinegun |

Pull the part out with your off hand, reach to your belt for a fresh one, and push it home.

Brutal Doom never reloads most of the heavy guns at all. On those, the part you swap was cut out
of the gun's own model, and it counts down Brutal Doom's own ammo. The ammo you carry and the
damage you do are still exactly Brutal Doom's.

### Throwing the axe
- Hold the throw and a **lock-on ring** goes on the monster your hand points at. It's the same
  mark as the ShieldSaw and the QuestSaber.
- If you let go without throwing, the ring **stays on for a second**. Pick the hold back up and
  you're still locked.
- The throw **blends your arm's swing with where your hand points**, as the ShieldSaw does.

### New guns from Brutal Doom 21
- **BD21 Machinegun** (M249 with an underbarrel 40 mm). Off by default:
  "Machinegun replaces MG42".

### Melee
- **Gun bash** (removed in 2.0.2): your kick key bashed with the gun you were holding.
- **Pistol whip**: swing a pistol or revolver into something.
- **Butt strike**: drive the stock forward with both hands. Works on all eight guns with a stock.
  Off by default.
- **Real punching** with either fist. Punching a switch or a door works it. Off by default.

### Every gun shoots like itself
These are behind the **Ballistics** switch. Stock is Brutal Doom's own.
- **Recoil** for 22 guns, each worked out from its own cartridge and weight. In VR it moves the
  gun in your hands, never your view.
- **Muzzle flash** light for 18 guns, and an echo for 14 that sounds different indoors and
  outdoors.
- **Visible rounds in flight** for 11 guns, at their real speed.
- **Impact sounds** per surface, **ricochets** off shallow angles, and **brass** from each gun's
  real ejection port, as 3D casings.

### Fixes
- **Guns no longer spin round your shoulder.** Recoil kept adding to itself during reloads and
  turned the gun. It now kicks and settles.
- **No muzzle flash or gunshot echo without a shot.** Footsteps, kicks and the reload buzz were being
  taken for gunshots.
- **Brutal Doom's own ricochet, glass, sparks and magazine-drop sounds are back.** Some of the
  pack's sound files had the same short names and were playing in their place.
- **Fire rates:** QuestZDoom 17.3 lets a held trigger re-fire some guns faster than Brutal Doom
  does on PC: the pistol, the pump shotgun, the Incendiary Launcher and the dual pistols. They're
  held to PC's rate now. The Ruger is one shot per pull.
- **Rounds you pull out stay yours:** pull a part-full magazine with no reserve left, and its
  rounds go back in when you seat it again.
- **Incendiary Launcher:** pressing reload did nothing. Fixed.
- **Flamethrower:** it returned to the wrong frame after firing. Fixed.
- **Dot scope:** it could stop the game's scripts running, on the Railgun and the Ruger. Fixed.
- **Ruger:** it drew 2D sprites while firing. Fixed.
- **Purist Rifle:** it fired the M203. Fixed.
- **Grip-mode charging handle:** a racked handle could not be grabbed. Fixed.
- **Axe alt-fire hold:** it did nothing for players upgrading from older builds. Fixed.
- The pk3 is about **30 MB**: models are LZMA-compressed, as 1.96b's were.

### Fixes from the owner's 1.99 headset pass
- **Recoil is gone.** It turned the gun model, so the gun spun around the shoulder and pulled
  away from the hands. Hold poses at rest match 1.92 again.
- **The Nuker uses the BFG's hands.** It is the same model, so it gets the same grip and trigger
  finger, fitted to its size.
- **Chainsaw** grip hand moved 2 cm left. **Incendiary Launcher** grip hand moved 2 cm forward.
- **Real magazines** on the Flamethrower (100), Machinegun (100), Unmaker (200) and Minigun (200):
  every shot comes out of the magazine, the reserve is what is left in your pouch, and a reload
  moves rounds from the pouch into the gun.
- **Machinegun:** the 40 mm round, its latch and the hands sat 5 cm high. Fixed.
- **MG42, Flamethrower, Unmaker:** the gun no longer jumps 5 cm when a reload starts.
- **Axe and sword** cut only on a down or side swing, never an upswing, and need a harder swing.
  Turn off "Two-Hand Grip (engine)" (then called "Two-Handed Steadying") to hold them with one controller: grip with your off hand near
  the blade and you get the two-handed pose. Guns lose steadying too while it is off.
- **Spent casings with the voxel pack** are normal size again (a shell was drawn at four times
  Brutal Doom's size).

## Everything else
- Posed VR hands on every weapon: hand on the grip, finger on the trigger, support hand.
- Slides, charging handles, bolts and pumps racked by hand. Pistol slides and rifle, SMG and
  assault shotgun bolts lock back when fired dry.
- Shotgun shells go in through the real loading port, and you can top off any time.
- Kitbash M4 + M203. In VR: unlatch the tube, slide it forward, push a round in, slide it shut.
- SMG alt fire toggles 3-round burst or full auto. Slug shots for the shotgun and the Shotvolver
  are menu options, off by default.
- Pistol Semi Auto option: one shot per trigger pull.
- Dual wield, with each gun fired independently. Flick a gun down to reload when you're using two.
- Grenades: pull the pin with your off hand, swing and release to throw, or release while still
  to cook it.
- Left-handed support. Purist mode gives you models and hands, without reloading.

## Options
**Options → BD22 VR Weapons.** Here you'll find reloading (VR or Brutal Doom's stock reload), what
grabs the ammo, where a new magazine comes from, the scopes, ballistics, real casings, throwing
and the grenade, punching (VR Punching, No Trigger Punch, Punch Switches Open), the pistol whip and
butt strike, the dual-wield and voxel pages, and a tuning and debug page for reloading.

Every option defaults to how Brutal Doom behaves, or to the gentler setting, except the VR hands
and reloading themselves, the live scopes, Shoot Thrown Grenades, Ammo From the Rig's Pouch Only (it
does nothing without RSQ Tactical Rig) and No Trigger Punch, which are on. Set Reloading to "Stock (BD22)" and every gun reloads the way it always
did.

## Known gaps
- Still open from the 1.99 headset pass: a bang when a map loads and the BFG's sounds.
- The off-hand dual Railgun has no live scope of its own yet: its alt fire is still Brutal Doom's
  zoom.
- On the Nuker, both BFGs and the Hellish launcher, the support hand cradles the body rather than
  wrapping it: their models have nothing narrower to hold.
- The Minigun's ammo box in your hand is the small box off the gun. A bigger one is planned.
- The Minigun throws its brass from the body: its model has no ejection port.
- QuestZDoom 17.3 can't do recoil roll or the backward shove. Those need engine support this pack
  doesn't have.

## Versions
Public releases are numbered 1.9x and are the only tags on this repo. `main` is always the latest
public release plus any fixes on their way to the next one. Work in progress lives on the `dev`
branch under internal 2.x numbers.

This build is generated by the RSQ Weapon Depot. Every number in it is measured off a model or
parsed out of Brutal Doom's own code, and `src/README.txt` (shipped inside the pk3) has the long
version.

## Credits
**BD22 VR Weapons Q**: project conceptualized, directed and coordinated by **PresidentKoopa** (Radiant Silvergun). All coding done by agentic **Claude** (Anthropic), working under his direction.

Weapon models: **br_vr** by ajantaju (Brutal Doom VR Weapons, BD v21), made from:
- Grenade by Gomuz; MP40 by Krystian; Shotgun by serg-654; Beretta M9 by damkung13
- Axe by martn00; M4A1 by seandxyz; Minigun by overlordchaos; DBS-2 by ironcladmax501
- SemiAuto Shotgun by Derak Derantick; Grenade Launcher 2 by watercat; RPS-6 by David Short
- KRISS Vector by Bandit; Chainsaw by 3DHaupt; M16A3/M203 by rubenve; M249 by Buce
- M79 by omgitstallin; Rorsch Mk-1 by CrazyRusEnginer; M13-Gaus (plasma) by DigitalTales
- RD-100 (BFGs) by Cameron Chung Art; Flamethrower (TF2) by arminalcapon
- Mancubus flame cannon by Arthur Manhaes; Dragonslayer by Jakob Pihl; MG42 by TastyTony
- Taurus Judge by Tori-nyan; Boot by Nicolas.KoiSculpt; Fingerless Glove by 3DMaesen
- Revenant missile launcher and Reaper by id Software (Doom 2016)

(All from Sketchfab; textures edited.)

- VR hands: Ermac (Force Unleashed / Rusted Legacy, MIT). The 2.0 hands were fitted starting
  from his 1.92 holds.
- Brutal Doom: Sergeant Mark IV
- QuestZDoom: Team Beef
- Shot tracers, impact sparks and their sprites (DPUF, shipped as RSDP): **Dakka** by ijon
  (https://github.com/0dot0repeating/dakka, WTFPL), ported to ZScript
- Player Ballistics (Bullet mode): ported from PresidentKoopa's RS_Ballistics `enemyfire.zs`

## Screenshots

![Hands on every reload](renders/2.0_reload_hands.png)
![Live 3x scope, toggled on alt fire](renders/2.0_scope_3x.png)

![Kitbash M4 + M203](renders/m4_m203.png)

![Hands on the guns](renders/hands_on_guns_1.png)
![Hands on the guns](renders/hands_on_guns_2.png)
![Hands on the guns](renders/hands_on_guns_3.png)
