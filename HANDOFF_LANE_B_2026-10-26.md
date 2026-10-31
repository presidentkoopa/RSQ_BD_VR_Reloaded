# Lane B handoff, 2026-10-26: bd22q 1.99x (branch `lane-b-1.99x`)

Base: `main` 70b0574 (1.99). NOT merged, NOT tagged, NOT released: those wait for the owner.
Every rig result below is from the **QuestZDoom 17.3 rig** (`tools/rig/build/rig`, log line
"QZDoom version 4.14.3", "qz: engine OK"), on doom2 -> brutal22test6 -> BD_VoxelPack -> pack.
Runs from the earlier wrong engine (bin/, 4.15pre) were thrown away and redone.
Evidence (renders, logs) is in `/home/claude/lane_b_out/` and `/home/claude/lane_b_rig/logs/`.

First check: the Depot's `sets/bd22q_1.97/src` and `main`'s `src/` are **byte-identical**
(`diff -rq`: 0 files). No Depot fix is missing from main.

## 1. Done (measured)

### Item 18: "a bang sound when I load into a map". FIXED (`76185df`)
- The sound is **ours**: `Melee/Swing` from our real-punch detector, about 15 tics into every map.
- Cause: about 15 tics into a map the engine re-syncs its VR yaw (`gl_openvr.cpp`,
  `resetDoomYaw`). The hand's world position swings round the body **in one tic**. Measured in
  the rig (body frame): lf -10.2 -> +10.2, ll -8.5 -> +8.5, about 27 m/s. `RSQ_FistHand` read that
  as a jab and played Melee/Swing plus a punch. It happens only with `rsq_punch 1`.
- Fix: a one-tic step over 0.5 m (17.5 m/s, faster than any arm) is treated as the frame
  moving, and the punch history starts again.
- Second, related regression found on the way: `OffPunch` (hands.zs) **ignored `rsq_punch`**.
  With punching off, an off-trigger press away from the gun still swung and punched; 1.92
  never did. The owner's call (2026-10-25) is "off-hand punch stays behind rsq_punch". It is
  now gated.
- Rig, QZ_SNDLOG, map01 -> map02 -> map03 (-> map04), Rifle/Axe/Pistol, rsq_punch 1:
  1.99 gives 2 Melee/Swing per run, this build gives 0. Off trigger 60 cm from the gun:
  rsq_punch 0 gives 1.92 none, 1.99 a swing, this build none; rsq_punch 1 swings. A deliberate
  punch still lands (`lb_fix18_punchlive`).
- No other pack sound at map load. With no pack, 1.92 and 1.99 compared over map changes,
  save/load and all six BD22 classes, the remaining differences are BD22's own select or reload
  sounds, which the pack's VR reload replaces by design.
- If the owner hears a bang with `rsq_punch 0`, it is not this. Ask what he holds and which class he plays.

### Item 10: magazine-in-hand poses for the F10 guns. 3 of 9 refitted (`7ba55d7`); 6 need an owner look
- Method: Ermac's authored ammo_hand holds (Rusted Legacy, MIT; `ammo_hand.md3` frames 0-8,
  the same file we ship, byte-identical). For each frame, the hand's contact patch is the hand
  vertices within 1.5 cm of **his** part in that frame. Our part is fitted onto that patch by
  trimmed ICP, translation only, because `Place(HANDMAG)` adds only `HandHook` and the part keeps
  its seated orientation. The fit is penalised for hand vertices inside our part (ray parity).
  All 9 parts x 9 frames were scored. Tools: scratchpad `fit10b.py` and `rend_cand.py`
  (Depot's kit rgeo/hudrender, read-only).
- Changed:
  - Flamethrower canister: frame 3, contact gap 0.82 cm. Before, it floated under the hand.
  - Nuker block: frame 6 (Ermac's BFG pod hold), gap 0.81 cm. Before, 18 cm above the palm.
  - Hellish drum: frame 6, gap 1.11 cm. Before, 28 cm off.
  - New `RsrHoldPod` state (RQHN M -> ammo_hand frame 6), chosen per gun by
    `RSR_ReloadHandler.HoldState` (15, 16).
  - `TopInHand` / `HandHook` rows in `rsr_guns.bd.zs` (HandHook = shift_hook(TopInHand - Well), checked).
- In-engine CARRY renders, main vs this build: `carry_main_vs_lb.png` (Flamethrower, Hellish)
  and `carry_nuker_main_vs_lb.png` (Nuker, 3 angles; this build shows the block in the off hand,
  main shows the hand under it). Offline 3-view sheets: `item10_candidates.png` (now / frame-3
  fit / best frame, per gun).
- Not changed, deliberately: MG42 drum, M32 cylinder, Unmaker skull, Devastator bay, Minigun box,
  Machinegun box. They already sit in the frame-3 palm, 2.4 to 5.7 cm off Ermac's magazine
  centre, measured. Their best-scoring alternatives are visual judgement calls (see Owner questions).

### "Reload Non-Standard Guns" option. BUILT (`7ba55d7`)
- `rsq_reload_nonstd`, **user** bool, default **on**. The row is on the BD22 VR Weapons page,
  right after "Reloading". It is `user` like `rsr_reload` because it is read per player with
  `RSQ.PlayerInt` and gates only that player's own reload and counters.
- Non-standard, parsed from brutal22test6 `actors/Weapons/*.dec`:
  - No `Reload:` state at all: MG42, MiniGun, IncendiaryLauncher, Unmaker, Devastator,
    NukeLauncher, HellishMissileLauncher.
  - Flamethrower2: its `Reload:` label is only its dry-ready loop, and BD22 never jumps to it
    (0 references).
  - BD21 Machinegun (docs/BD21_Machinegun.txt): its Reload reloads only the underbarrel grenade.
  - That is exactly `RSQ_Counters.GUN[]`, the 9 counter guns.
- Standard, untouched: every gun with a reachable BD22 Reload: Rifle, Pistol, SMG, MP40,
  AssaultShotgun, RailGun, Plasma, Sniper, Rocket_Launcher, Shotgun, SSG, GrenadeLauncher,
  Revolver(2).
- Off: the counter idles (no `RSQ_Empty`, and a magazine left out is put back) and `RSR_Start`
  refuses the gun, so its Reload falls through to Ready.
- Rig, all 9 guns, `+reload` then fire held 150 tics:
  - Off: no reload phase, no script error, shot counts equal to `rsr_reload 0` (BD22 stock path):
    Minigun 54/54, Machinegun 54/54, Flamethrower 168/168, Devastator 36/36, Hellish 23/23,
    M32 2/2, Nuker 1/1, MG42 110/114, Unmaker 150/151 (one-shot jitter from timing under load).
  - On: IDLE -> EMPTY -> DROP as before.
  - Logs: `logs/lb_ns0_*`, `lb_ns1_*`, `lb_nsstock_*`.

### Items 13 / 15 (Machinegun box, M32 in the headset): the weapon code path, tested
- Owner's lead: "our chaingun weapon code hasn't been written to support reloading". Checked
  per gun. Every non-standard gun's Ready loop has the posefix line
  `A_JumpIfInventory("Reloading",1,"Reload")`. That is the path BD22 itself uses: its ACS
  "CheckWeaponAction" gives `Reloading` on a BT_RELOAD edge. The Machinegun also has
  `WRF_ALLOWRELOAD`.
- The rig drives reload with `+reload`, which is BT_RELOAD, the same usercmd bit a bound
  controller button sends. So the rig does **not** bypass the real path. `+oh_reload`
  (BT_OFFHANDRELOAD, `rsr_magrelease`) also works.
- **Found and fixed (`589353a`): the Minigun did not reload while spun up.** BD22's spun idle
  loop `Ready2` calls A_WeaponReady but never reads `Reloading`. After alt-fire spin, the button
  did nothing (rig: main no reload; this build IDLE -> EMPTY -> DROP). That fits "we cannot
  reload it". The other spun or dry loops (Machinegun IdleNoAmmo, Flamethrower ReadyDry) are
  reached only with no reserve, where there is nothing to reload.
- With the 17.3 rig, BDoomer class, realistic reserves: Machinegun reloads on the button at a
  full reserve and at 50 rounds, and auto-reloads when the box empties (Clip2 160).
  M32 reloads on the button with 3 rounds; Minigun at 50.
- **What still blocks the M32 / MG42 in the headset is the capacity (owner question below),
  not the input path.** Measured: AmmoM202 MaxAmount 4 vs M32 cylinder 6, so a full reserve of
  4 makes a full cylinder of 4 and `Reload` jumps to Ready ("full"). M32 fired to empty from 4
  then +reload: no reload (`lb_auto_m32_4`), because the counter and the reserve empty together
  and there is nothing left to load. MG42: Clip2 MaxAmount 200 vs drum 200; at a full reserve
  the drum is "full" and the button does nothing.
- Quest input facts (VrInputDefault.cpp + engine/vr/defbind*.txt): off trigger = KEY_LSHIFT
  (`+oh_attack`); off grip = KEY_PAD_RTHUMB (443, rsr_grip_keys); in the owner's own layout
  (defbind3) reload is **R grip + R stick down** (`axis8minus +reload`). There is no single
  reload button, so a missed reload in the headset may also be the input. Ask him (below).

### Item 11 (weapons coming apart when grabbed). Rig evidence for his next pass
- Steadied grab (off grip within 50 cm, so the engine re-aims) rendered side-on, main vs this
  build: pistol after its last shot (slide locked), pistol at rest, SSG during its reload.
  `item11_pistol_locked_steadied_main_vs_lb.png`, `item11_steady_main_vs_lb.png`.
  The parts stay on the gun in every shot. Recoil (the cause of the earlier splits) is out since
  1.99. Not reproduced in the rig.

### Regression pass vs 1.92 (cmp2, 1.92 left, this build right)
- `cmp2_a.png`: Pistol, Rifle, SMG, Shotgun, SSG, AssaultShotgun, Plasma, Railgun are identical.
- `cmp2_b.png`, `cmp2_c.png`:
  - BFG, BFG10k (the 1.92 frame caught it mid-raise), Nuker, Chainsaw, Axe and GrenadeLauncher
    match.
  - Sniper and M32 differ on purpose: 1.92 had no model for them (it drew a Rifle); 1.93+ has
    the XM21 and M32 meshes.
  - Revolver, Rocket_Launcher, Minigun, Unmaker, Flamethrower2, DSweap and MG42 show the default
    rifle on one side: those are rig select-timing misses, not pose changes. Re-shoot them
    before calling them; hand tables are byte-identical to 1.92 for every 1.92 gun (Depot doc A6).
- Full give/select/fire/alt-fire/reload sweep, all 31 classes, class BDoomer, ballistics 2:
  **no pack script error, no VM abort** (`logs/sw_lb_*`). Only BD22's own `Deh_Actor_153` and
  BD_VoxelPack's `DeathSphereHealth` / voxeldef lines, also present with no pack.
- Reload paths:
  - **All 18** magazine reloads go IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE (mags.py).
    The Nuker's harness needs the blast to clear and a nuke re-given first (it carries one).
  - Rifle and Machinegun M203: "shut: loaded".
  - Spin test: psp x/y stay 0/32 through walk, fire and reload; one flash per shot.
- RailGun and Sniper with Real scope mode, eye at the eyepiece: no VM abort. No `out Vector`
  parameter anywhere in our zscript (Lane A's REGT_ADDROF crash does not apply).
- RQLK lock-ring art: RQLKA0-D0.png **are in main's pk3** (src/sprites). The Depot's "no lump"
  note is stale.

## 2. Not done
- Items 10's other six parts (above): need the owner's eye on `item10_candidates.png`.
- Item 19 (BFG sounds): no pack change. Audit: none of BD22's 8 BFG / BFG10k sound names
  (BFG/Charge, BFG/Draw, BFG/Fire, BFG10K/*, FAREXPL) is redefined by our SNDINFO. Globally, 0
  sound names of BD22 are redefined and 0 of our sound files share an 8-char lump with BD22
  (the A4 fix holds). Nothing of ours can change a BFG sound, so we need his description.
- Item 21 (Ruger scope default): not changed (owner call).
- Item 14 (Machinegun 40 mm height), 16 / 17 (melee), 20 (voxel shells), 8 / 9 (grip nudges):
  the Depot's fixes are in main and unchanged here. M203 load passes on both guns. No new
  headset evidence beyond the cmp2 sheets.
- Dual wield and flick reload: not driven this session.
- Minigun's bigger in-hand box: owner-later, not built.

## 3. Open
- cmp2 re-shoot of the seven "default rifle" tiles (select timing).
- The rig's `qz_lgrip` steadying could not be confirmed from the probe (no "steadied" log line);
  the renders show the re-aim happened.

## 4. Owner questions
1. **Capacities (do not change without you):** M32 cylinder 6 vs BD22's AmmoM202 max 4, and MG42
   drum 200 vs Clip2 max 200. A counter is a real magazine only below the reserve max: at a full
   reserve the gun reads "full" and the reload button does nothing. Options: M32 cylinder 4 (or
   3), MG42 drum 100 (as the Minigun and Machinegun now), or leave them.
2. Which button do you press to reload on the Quest? Your layout puts `+reload` on R grip +
   R stick down. Is that what you used on the Machinegun and the M32?
3. Item 10: the six parts not refitted (MG42 drum, M32 cylinder, Unmaker, Devastator, Minigun
   box, Machinegun box). Are they right as they are? Sheet `item10_candidates.png`, row "now".
4. Item 19: which BFG sound is wrong (charge, fire, draw, explosion), and does it still happen
   after 1.99's A4 lump fix? The pack has none of the BFG's sounds.
5. Item 21: Ruger scope default Dot or Real? Real is a second full scene render (mono, 256x256
   camera texture) **only while your eye is behind the eyepiece** (scope_real.zs gate), one
   frame stale. Off the scope it costs nothing.
6. Free charge default and PuristSniper model: still yours to call. PLAN records free charge
   "stays off"; PuristSniper "stays out".

---

# Round 2/3 (2026-10-26, afternoon/evening): branch `lane-b-1.99x`

Rig: QuestZDoom 17.3 (`tools/rig/build/rig`, "QZDoom version 4.14.3"), doom2 -> brutal22test6 ->
BD_VoxelPack -> pack, `flock -o -s /home/claude/rig.lock`, at most 2 engines. Evidence in
`/home/claude/lane_b_out/` (r3_*, r3fix_*), logs in `/home/claude/lane_b_rig/logs/` (r3*, cmp3_r3fix_*).
Round 2 was interrupted at 14:06 and the container restarted once mid round 3: every run in flight
then was voided and re-run.

## 1. Done (measured)

### "All of the hand poses are off": FOUND and FIXED (`44792ab`)
- The round-2 1.92 comparison (`pose_vs_192_*.png`) showed real, deterministic differences on 21 of
  26 guns at rest. They were not bob phase: the last 3 settled frames of each build are 0-8 px apart,
  1.92 vs ours 360-4328 px.
- Ruled out, file by file: handtable rows (identical for every 1.92 gun except the deliberate ones
  below), MODELDEF hand blocks, `hand.md3` (frames 0-43 vertex-identical; 1.95 only appended 44-45),
  the free hand's MODELDEF and layer state (probe: same sprite/frame on every layer).
- Bisected in the rig (the `1.92` tag is byte-identical to `BD22Q_192.pk3`): already present in 1.95.
  1.95 with 1.92's `MODELDEF.*` still differs; **1.95 with 1.92's `gunmoves.zs` alone renders the
  Plasma pixel-identical to 1.92** (0 px).
- Cause: 1.95 (413b3cc) switched off the Sniper's six recoil rows in `RSQ_GunMoves.Frame` by keying
  them to gun 0. A probe that called `Frame()` for every (gun, sprite, frame) in the table showed
  670 of 2680 lookups for OTHER guns returning a different row than 1.92 (e.g. Plasma at rest:
  turn 3.10 / move 9.18 instead of 0). `FollowGun` feeds that to the gun and support hand layers,
  so every hand sat off its fit. Measured, not explained: why key 0 does this on 17.3's VM was not
  isolated (same loop, same arrays). Keyed to 99 (no gun) all 2680 lookups equal 1.92's.
- After (`r3fix_<Class>.png` = this build alone; comparison numbers vs the round-2 1.92 frames):
  19 guns 0-1 px from 1.92 (were 360-4328). Remaining differences are all deliberate (table below).

### Flamethrower (owner: "the flamethrower is wrong")
- At rest, steadied (off grip at the gun), firing and after firing, this build vs 1.92:
  rest 8 px, steadied 3 px, i.e. identical. Firing / after firing differ only in the flame and
  smoke particles (random), the hand and gun are the same (`r3_flamethrower_{rest,steady,firing,afterfire}.png`).
- Round 2's Flamethrower2_* tiles were rendered BEFORE the fix, with the gunmoves bug present; their
  hand differences are this bug.
- So what the owner sees is **1.92's own Flamethrower pose** (a separate prototype scored it 3 of 12
  grip rules: support hand 5 cm inside the gun, index 8 cm off the trigger) plus, in builds up to
  9ab84cb, the gunmoves offset. Not re-posed here (no new hand poses; the hand fitter is for that).

### Item 3: dual wield and flick reload, driven in the rig (real input: +user3, +attack/+oh_attack, controller pitch)
- Pistol Start gives the off-hand pistol; Dual key -> `RSQ_Off_BrutalPistol` in the off hand; both
  fire per hand (mag 16 -> 12 each); off controller snapped from +30 to -30 deg in one tic -> the OFF
  pistol alone reloads (BD22 Reload, offmag 12 -> 16, reserve Clip1 60 -> 56); main controller the
  same -> the MAIN pistol alone (12 -> 16, 56 -> 52); Dual key again -> fist. Identical to 1.92 on the
  same input (reserve 60/56/52). No VM abort, no crash. `r3_dual_flick.png`, `r3_dual_flick.log`.
- Machinegun launcher (M203): rig `m203.py GUN=mg` on this build: latch, open 9.7 cm, round in,
  "shut: loaded" (log `m203mg.log`, `r3_m203mg_side_lb3.log`).

### Item 14 (Machinegun 40 mm height): headset evidence
- Side view with the tube open and the round home, main 1.99 vs this build
  (`r3_item14_mg_m203_seated.png`, sequence `r3_item14_mg_m203_sequence.png`). The round sits on
  the tube's bore line (RSM_Geo gun 2: bore U -6.517, from the mesh with ZOffset -5, `41d1c3b`).
  No change this round; main and this build are the same here.

### Items 16/17 (axe and sword): headset evidence
- Rig, Two-Handed Steadying OFF (`vr_two_handed_weapons false`), off grip held 22 cm from the
  weapon: axe `RSVR_MeleeTwo 1, RSVR_AxeTwo 1`, engine steadying 0; sword `RSVR_MeleeTwo 1`,
  steadying 0. Released: all 0. One controller drives it. `r3_item16_melee_twohand.png`.
  With steadying ON the axe also reports steadied 1 (the engine's grab, as documented: menu row).
- Swings (0.3 m/tic, 3 directions): UP: no swing sound, no cut, axe and sword; DOWN: Axe/Swing,
  Melee/SwingStrong; SIDE: the same. Logs `r3_item16_17_{axens,swordns}.log` (QZSND lines).

### Item 20 (voxel casing scale): headset evidence
- Rifle, "Spent casings" voxels ON: EmptyBrass scale 0.153 (BD22 with no pack: 0.150); OFF (3D
  mesh lend): 1.000 with the real-size mesh, as designed. `r3_item20_vox1.log`, `r3_item20_nopack.log`.

## 2. Not done
- No new hand poses for guns whose 1.92 pose is itself bad (Flamethrower, see above): for the fitter.
- Round 1's seven "wrong gun" cmp2 tiles: superseded by the r3fix set (every gun's held class is
  printed on its tile and logged by LBW), not re-shot separately.
- The six un-refitted in-hand parts (item 10) and the other owner calls: unchanged.

## 3. Open
- Why gun key 0 misreads on 17.3 is not explained (measured only). `gunmoves.zs` now says so; keep 0 out of `key[]`.
- The gunmoves generator (`rsq_gunmoves_gen.py`, depot_import) was not re-run; 413b3cc's key edit was by hand.

## 4. Owner questions (unchanged unless noted)
1. Item 10: the six un-refitted in-hand parts (`item10_candidates.png`, row "now").
2. Free-charge default; PuristSniper model.
3. Item 19: which BFG sound is wrong.
4. NEW: the Flamethrower at rest is now exactly 1.92's. Is it 1.92's pose you dislike (then it goes
   to the hand fitter), or was it the offset this round fixed?

## Every gun at rest vs 1.92 (this build, `r3fix_*`)
| Gun | Result |
|---|---|
| AssaultShotgun, BFG10k, BIG_FUCKING_GUN, BrutalPistol, BrutalSMG, Devastator, Flamethrower2, GrenadeLauncher, HellishMissileLauncher, MG42, MP40, Minigun, Plasma_Gun, Revolver, Rifle, Rocket_Launcher, SSG, Shot_Gun, Unmaker | same as 1.92 (0-1 px); 16 of them were off before `44792ab` (gunmoves key 0) |
| IncendiaryLauncher | differs on purpose: grip 2 cm forward (item 9, owner) |
| NukeLauncher | differs on purpose: hands from the BFG (item 7) |
| RailGun | grip same; scope glass / dot (1.96b) |
| Sniper | 1.92 had no Sniper (drew a Rifle); XM21 mesh since 1.95 |
| BrutalAxe | 1.95 two-handed placement tables (164 px, owner 2026-10-23) |
| Chain_saw | 2 cm left + trigger finger (item 8, 1.95) |
| DSweap | not a 1.92 weapon fit (Dragonslayer fit 2026-10-23) |
| Flamethrower2 (1.92 itself) | 1.92's pose is the one a prototype scored 3/12: for the hand fitter |

## Gated test pk3 (round 3)
`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r3.pk3`, built from `1953013` (src identical to
`44792ab`), sha256 `7061efe3ab4e948214cdf32b659e3bfab69f9702e736c1c847d6457d57e150d9`.
Gate (`lane_b_rig/sweep.sh`, logs `sw_r3_*`): all 31 classes given, selected (held class logged),
fired, alt-fired, reload button pressed, fired again; class BDoomer, rsr_reload 1, ballistics 2.
0 pack script errors, 0 VM aborts, 0 crashes. The only error lines are BD_VoxelPack's own (four
voxeldef lines, DeathSphereHealth), present with no pack too. Not yet on the owner's headset.

---

# Round 4 (2026-10-27): branch `lane-b-1.99x`, the owner's r3 headset report items 1-7

Rig: QuestZDoom 17.3 (`/home/claude/rsq_weapondepot/tools/rig/bin`, "qz: engine OK"), doom2 ->
brutal22test6 -> BD_VoxelPack -> pack, `flock -o -s /home/claude/rig.lock`, one engine at a time.
Driver `/home/claude/lane_b_r4/run.sh`, test-only probe `/home/claude/lane_b_r4/r4probe.pk3` (logs
casings, shot origins, hand-follow rows, damage, all in the controller frame, cm). Logs in
`/home/claude/lane_b_r4/logs/`. Sheet: `/home/claude/lane_b_out/r4_fixes.png`. r3 = the delivered
`BD22_VR-Reloaded_1.99x-lb-r3.pk3` (7061efe3), r4 = this round.

## 1. Done (measured)

### Item 1: over-under machine gun (Machinegun) casings out of the barrel. FIXED (`1769b47`)
- Port re-measured off `Machinegun.md3` frame 4 with the Depot's own `bd22_plus.eject_port`
  (boundary loop, 18 verts): mesh (43.41, -0.27, -4.20) -> controller F 14.3 L -0.3 U -4.3 cm.
  The shipped number was right.
- Cause was timing. BD22's casing spawner (`50CaseSpawn2`, Casing.dec) is a Speed 20 projectile;
  the case is born where the spawner has flown to. `casings.zs` moved it to the port on the NEXT
  WorldTick, so every case was drawn for one tic out in front. Rig, first shot: r3 EmptyBrass age 0
  at F 91.5, MGLinks at 155.3 (the gun ends at 68.8); age 1 at the port.
- Fix: place in `WorldThingSpawned`, which the engine calls from the fresh-thinker pass with target
  and vel already set (dthinker.cpp: CallPostBeginPlay, then the first Tick, same tic).
  r4: EmptyBrass and MGLinks age 0 at F 14.9 L -0.3 U -6.0 (the port; the probe's own
  pixelstretch round trip reads U about 1.3 low), then down the chute. Applies to every gun's brass.
- Rig frames at 480 px do not resolve a 5 cm case at arm's length (tried four poses, casing size
  x4); the sheet plots the rig-logged positions on the mesh instead.

### Item 2: Ruger/XM21 bullets from below the barrel. FIXED (`02f433e`)
- Muzzle measured off `XM21.md3` (frame 0, surface 9 = body and barrel) through MODELDEF.rsr's chain
  (Depot `tools/kit/rgeo.py to_flu`): tip F 62.34, bore L 0.28 U 5.03 (constant from F 45 to the
  tip). The controller, where QZD 17.3 starts every player shot (AttackPos), is 62 cm behind and
  5 cm under it.
- New `zscript/rsq/muzzle.zs` (`RSQ_Muzzle`): hitscans re-fired with `LineAttack(LAF_ABSPOSITION)`
  from the muzzle, same angle/pitch/damage/puff/range/flags, direction still the engine's AttackDir;
  BD22's trail-only rail (damage 0, "Gray") redrawn by `Actor.RailAttack` from a mount at the muzzle
  with the same FRailParams. Wall guard: if the hand-to-muzzle line hits geometry, nothing moves.
- Rig: r3 all three hitscans and both rails from (0, 0, 0); r4 hitscans and trail from
  (62.5, 0.3, 3.8). The damaging rail (30, colour None, invisible) still starts at the controller
  on purpose: fired from a mount its kills would not be the player's.
- The rig does not draw particle rail trails in its frame dumps (none visible on r3 either), so the
  evidence is the log, plotted on the mesh in the sheet.

### Item 3: Minigun hand keeps shaking with the barrel spin. FIXED (`a347fb5`)
- Measured per surface vs ready frame 4 (`Minigun.md3`, Scale -1 1 1, ZOffset -5): in frames
  5, 6, 7, 9, 11 the body (`Runko` x3, `Grip`) moves 0.00 cm and only `Pipe` (the barrels) turns;
  in frames 8 and 10 the body moves 2.04 cm straight back, no turn.
- `gunmoves.zs` rows 46-48 and 50-52 had been fitted to the whole mesh, barrels included, and read
  the spin as a 0.5-1.9 degree turn. Now 5-7/9/11 are zero and 8/10 are the 2.04 cm kick (row 49
  already was).
- Rig, fire 20 tics then release, spin-down tics 294-360: hand turned in 45 of 57 tics (r3), 0 of 57
  (r4). While firing the hand still kicks 2.04 cm with the frame.

### Item 4: Unmaker, only the top half of the skull comes out. FIXED (`0a9f677`)
- The RS VR Weapons version: Depot `sets/plus_0.7` `unmaker_wm.md3` (MODELDEF.rsr `WM_VP_Unmaker`).
  Same mesh: surfaces of 10931 / 361 / 249 verts, as ours. It draws surfaces 1 (flap) AND 2 (lever)
  as the part. Ours drew only 1 (`magazine`); 2 (`magazine#2`, the jaw) stayed on the gun.
  bd22_plus.py's card meant both (`ref_parts skull, skull2 -> magazine`).
- MODELDEF.rsr: gun = surface 0 only; part, hand and dropped skull = 1 + 2.
- Rig, reload to CARRY with the skull held clear of the gun: r3 vs r4 differ in exactly two places,
  the gun's socket (about 300 px) and the hand (about 280 px): the jaw moved from gun to hand.

### Item 5: IDKFA gives neither revolver. FIXED (`1534fd7`)
- Cause: with "Shotvolver Swap" on, the Revolver class was replaced (roster.zs), and the engine's
  give-weapons cheat skips any replaced weapon (player_cheat.zs); Revolver2 had CHEATNOTWEAPON.
  Rig r3: swap off gives Revolver only; swap on gives neither (the owner's report).
- Also found: the swap never reached map pickups. BD22's `RevolverSpawner` gives "Revolver" with
  A_GiveInventory (NO_REPLACE). Rig r3, swap on: the pickup gave the BD22 Revolver.
- Fix: Revolver2 not CHEATNOTWEAPON (it is in slot 2 via KEYCONF.rsq); the swap now replaces
  `RevolverSpawner` with `RSQ_ShotvolverSpawner` (DECORATE.rsqrev: Revolver2 + 6 Clip2, the same 6
  rounds BD22's spawner gives and one full cylinder, RevolverAmmo MaxAmount 6).
- Rig r4: idkfa gives Revolver AND Revolver2, swap on or off, on all five BD22 classes (Purist,
  Doomer2 pistol, BDoomer rifle, Doomer3 melee, TacticalDoomer). PuristRevolver stays
  CHEATNOTWEAPON (BD22's own). Pickup, swap on: Revolver2 + Clip2 30 -> 36; swap off: BD22 Revolver.
- Not swapped: a Revolver placed directly by editor number 5874 (no Doom 2 map has one).
- For the owner's slug check: the menu row is "Shotvolver Slugshot Alt Fire" (`rsa_rev_magnum`,
  default off).

### Item 6: butt strike range. EXTENDED (`fc43821`)
- Old: the hit volume was the gun itself, the stock-to-forward segment, padded 5 map units (15 cm).
- New: plus a sweep 60 units ahead of the stock along the stock's motion, padded 12. Why those:
  BD22's own kick (Melee.dec `KickAttack`: FastProjectile Speed 30, lives 2 tics `TNT1 AA 1`,
  Radius 12, fired from the controller in VR), i.e. 72 units (2.1 m) of reach. The blow gates
  (speed, butt leading, two hands) and the hand-to-target `Clear` line are unchanged.
- Rig, steadied two-handed Rifle stroke (off grip 35 cm ahead, gun hand swept 15 cm/tic about it),
  frozen zombieman ahead: r3 hits at 40 units only (55, 70, 90, 105, 120: miss); r4 hits at 40, 55,
  70, 90, 105, misses at 120 (stock about 13 units ahead of the pawn + 60 + 12 + radius 16).

### Item 7: option renamed. DONE (`d10b3c2`)
- MENUDEF.rsq: "Shotvolver Swap for Revolver" (On/Off). Cvar `rsq_slug_replaces_shotvolver` kept so
  saved settings carry over. README updated.
- Rig: `openmenu RSQ_Options` renders the row "Shotvolver Swap for Revolver  OFF"
  (`/home/claude/lane_b_out/r4_item7_menu.png`).

### Gated test pk3 (round 4)
`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r4.pk3`, built from `d10b3c2`, sha256
`0ce5ec20c329397764880c88a4918efe408d9b0d54e6614b235c85e2b5e452cc`.
Gate (`/home/claude/lane_b_r4/sweep.sh`, logs `logs/sw_r4_*`, one engine at a time): all 31 classes
given, selected, fired, alt-fired, reload button, fired again; BDoomer, rsr_reload 1, ballistics 2.
0 pack script errors, 0 VM aborts. The only error lines are BD_VoxelPack's 4 voxeldef lines (baseline).
Every gun's shot count and reload phases equal r3's, except the Unmaker (r3 20 shot tics, r4 16):
re-run twice per build, it is 16 or 20 on BOTH builds (trigger-release jitter), so not a regression.
Not yet on the owner's headset.

## 2. Not done
- Items 8-15 of the report (chainsaw, axe, sword, reload capacities, dual-wield options, Ruger
  scope, revolver mesh): out of this round's scope.
- No rig frame shows a casing or the particle rail trail (see items 1-2); those two are evidenced by
  the rig log plotted on the mesh.
- Butt strike through a wall: not driven; the unchanged hand-to-target `Clear` trace gates it.

## 3. Open
- Item 2 moves the hitscans and the visible trail only. Should the Ruger's damaging rail also start
  at the muzzle? Possible only from a mount, which would take the kill credit off the player.
- Item 5: the swap's map-pickup half never worked before r4 (BD22's spawner bypasses class
  replacement). Worth the owner checking a revolver pickup with the swap ON.
- Item 6: 72 units (2.1 m) is the kick's reach; if it feels too long in the headset, BUTT_REACH
  (melee.zs) is the one number.
- Queued after r4 (coordinator): the Moonlight revolver as BD22's normal revolver mesh with a
  break-open speedloader reload (reference/moonlight/README.md). Not started.

---

# Moonlight revolver (queued task), time box 05:59-06:44 2026-10-27

## Done (measured)
- 41-frame contact sheet, side view, per surface: `reference/moonlight/moonlight_41frames.png`.
- The frames DO contain a break-open, an eject and a speedloader (no blocker). Frame map,
  surfaces, placement, hinge, chambers, cylinder and loader seat: `reference/moonlight/README.md`
  "Measured", reproducible with `measure_moonlight.py` (output `measured.txt`).
- The Depot's hand-fitted `rev_wm.md3` is rev.md3 frame 0 moved rigidly (residual 0), so the fit carries to
  all 41 frames: `Scale 1.35 / Offset 0.0262 0.9224 / ZOffset 0.5878`. Rig (QZD 17.3, test-only
  pk3, not in src): frame 0 sits in the existing revolver hand fit (row 17), frame 26 shows the open
  break-top (`moonlight_rig_frame0_vs_26.png`); 0 script errors of ours.

## Half done
- Speedloader baked into frame 0 at its seat (closed-part frame), test asset only
  (`/home/claude/lane_b_r4/moon/bake.py` -> `moontest/models/moon/rev_seat.md3`, normals not
  re-baked). Not in src.

## Not done (next, in order)
1. Meshes into src: `models/bd/Moonlight/rev.md3` + a reload copy with the loader baked at the seat
   (bake.py) -> gun = surfaces 0+2, part = 1+3, loader = 10 (+ rounds 4-9 for per-round mode).
2. RSB: new rows in `rsb_guns.zs` cloned from the BD22 Revolver's speedloader entry (index 3; per
   round 7) with the measured Hinge (8.46, 0, -1.14), Axis (0, 1, 0), OpenDeg 63.3, seat
   Base/Tip/Bore on the loader axis, Scale/Offset of the new placement; MODELDEF.rsb gun/part/loader
   blocks (RBRG/RBRP/RBRW pattern). Revolver2 (the Shotvolver) keeps index 8/9 and Revolver.md3.
3. MODELDEF: BD22 Revolver's sprite frames -> rev.md3 (ready 0; fire recoil 1-14), replacing the
   411-line Revolver.md3 map.
4. `gunmoves.zs` Revolver rows are fitted to Revolver.md3's recoil frames: re-fit them to the
   Moonlight's frame body only (the item 3 lesson), or the hand moves against a still gun.
5. Rig: `tools/rig/brk.py` (break, load, flick shut) on the Revolver, speedloader and per-round feed;
   then the 31-gun sweep.

## Moonlight, box 2 (06:28-07:28): `BrutalRevolver` built (`6f65af6`)
Owner decisions: reference/moonlight/README.md (named "Revolver", class BrutalRevolver; own ammo;
BD21 firing rules; one shot per pull, 5-6/s max; no recoil work).

### Done (rig-checked, QZD 17.3)
- New files only, plus one line in `handtable.zs`: `actors/Weapons/BrutalRevolver.dec`, `DECORATE.rsqmoon`,
  `KEYCONF.rsqmoon` (slot 2), `MODELDEF.rsqmoon`, `models/bd/Moonlight/rev.md3` (sha1 81e48872) +
  `WPN-REV.png`, `sprites/RVMAA0.png`, and in `handtable.zs` BrutalRevolver -> row 17.
- Ammo: `RevolverRounds` (reserve) and `BrutalRevolverCylinder` (6, the gun). Never shares
  RevolverAmmo with the Shotvolver.
- Firing: `A_FireBullets(1, 1, 1, 100, "ShotgunPuff2", FBF_NORANDOM)` (Revolver2.dec, parsed),
  `RSQ_SemiLock`, 7-tic cycle. Rig: trigger held 40 tics = 1 shot; taps every 2 tics = shots
  7 and 15 tics apart (never under 7 = 5/s). Some 1-tic taps do not register (BD22's FiredPrimary).
- Mesh: rev.md3 at the measured placement, in the Revolver's hand fit (`r5_moon_inhand.png`).
- Reload (stock, button): plays the mesh's own frames: open, speedloader in, away, shut
  (`r5_moon_reload.png`). Fills the cylinder to 6 (rig: reserve 12 -> 6).
- `Weapon.TryPickup` needs the Ready sprite to exist as a lump (weapons.zs ValidateSpriteFrame):
  `RVMAA0.png` is BD22's REVOA0 (so 2D play shows BD22's revolver too).
- IDKFA gives Revolver (Shotvolver), Revolver2 and BrutalRevolver.

### Gated test pk3 (r5-moon)
`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r5-moon.pk3`, built from `6f65af6`, sha256
`2588120d60708a29b7359a4a5a220372259794207247ea439cc6fcf4253d45e5`. Gate (`lane_b_r4/sweep.sh`, logs
`sw_r5m_*`): 32 classes (the 31 + BrutalRevolver), one engine at a time: 0 pack script errors, 0 VM
aborts; every gun's shots and reload phases equal r3's (Unmaker 40/40 this run). Not on the headset yet.

### Placeholders (owner's call, marked in the .dec)
- RevolverRounds: 6 a pickup, max 60, backpack 120.
- Pickup art: BD22's shell / revolver sprites; the six-round speedloader art is not made.
- Map spawns: none yet.

### Not done (next)
1. Hand-driven VR reload: RSB rows (clone index 3 with the measured hinge 8.46/0/-1.14, axis +L,
   63.3 deg, seat, Scale 1.35 / Offset 0.0262 0.9224 / ZOffset 0.5878) plus the gun/part/loader
   models; the loader bake is ready (`lane_b_r4/moon/bake.py`).
2. Muzzle origin (`muzzle.zs` table) and casings: not measured for this mesh yet.
3. The pickup art (shell cut down, nosed, six in a ring, recoloured).

### Coordination note
- The hands lane shares this working tree. A checkout or stash on their side reverted my uncommitted
  `handtable.zs` line once mid-box; it was re-added and committed. Keep uncommitted edits to shared
  files short.

---

# BD 2.0 hands lane, batch 1 (2026-10-27, box 06:28-07:28): FBX hands on 1.99 r4

Worktree `/home/claude/lane_b_b1` (branch `b1-hands`, pushed to `lane-b-1.99x`). Port script and its
transform: `/home/claude/lane_b_b1run/tools/` (copies of the scratch `port_b1.py`, `gunmove.py`).
Rig driver, logs, shots: `/home/claude/lane_b_b1run/`. Pack: `/home/claude/lane_b_out/BD22_VR-Reloaded_2.0-b1.pk3`.
Sheet: `/home/claude/lane_b_out/b1_hands.png`.

## 1. Done (measured)
### BrutalPistol and Flamethrower2: lane_c r5's hands, exactly
- Hands: r5's baked MD3s byte-identical (`models/rsq/fbx/fbx_b1_R.md3`, `fbx_b1_L.md3`, `fbx_hand.png`),
  new sprites RQFG (gun hand: A pistol trigger, B pistol squeeze, C flamer lever, D flamer squeeze) and
  RQFS (A pistol cup, B flamer open palm under the tank). Neither sprite exists elsewhere in 1.99.
- Wiring = r5's: hands.zs labels (squeeze on the gun's own fire frames), dualhands.zs, handtable rows
  4/7 hooks 0, and also 1.99's new `GunHookTwo` rows 4/7 (it defaulted to the old one-hand hook).
- The gun move (r5's MODELDEF offsets) on EVERY block that draws the gun on the gun controller, found
  by parsing all MODELDEF files (11 block groups, counts asserted): bd.txt, purist, rsqoff, rsr pistol
  RQPM/RQPP, and, new in 1.99, the Flamethrower canister reload blocks RQYM (gun) / RQYP (canister in
  the gun). Off-hand (RSQ_Hands) and dropped/world blocks deliberately not moved.
- One rigid transform per gun (`gunmove.py`: the QZD 17.3 MODELDEF chain from lane_c `gunplace.to_local_ao`,
  base Offset 0 0 / ZOffset -5 -> r5). Check: it reproduces r5's own moved pistol numbers (well, axis,
  mag centre, grab, pull, casing port) to <= 0.04 cm.
  - Reload tables: pistol case 2 = r5's values; Flamethrower2 case 11 (not in 1.92) moved by the same
    transform: Well (36.788, 0.507, -3.364), Axis (-0.032, 0, 1.000), MagCentre (36.189, 0.560, -9.220),
    WellHook (0, -1, -0.032), Offset (-4.371, -8.313, -5.669). TopInHand/HandHook are hand-frame: kept.
  - Casing port (pistol): (7.2, -0.1, 6.4) (r5; transform gives 7.24, -0.11, 6.38).
  - Muzzle: the pistol joins r4's `RSQ_Muzzle` at its drawn muzzle (23.3, 2.2, 6.3): slide face of
    BrutalPistol.md3 frame 3 (F 15.18, U 0.10 before the move). r5 had reported the 10.5 cm gap and left it.
  - Flame at the spout: lane_c r6's `flamespout.zs` (RSA_FlameSpout, in ZSCRIPT.rsvr + MAPINFO.rsvr),
    tip recomputed for the r5 move: (91.25, -2.94, -4.47). r6's own tip point through the same chain
    gives r6's 88.39 -5.14 -1.42 to 0.001 cm with r6's offsets.
- Gate (QZD 17.3 rig, doom2 -> brutal22test6 -> BD_VoxelPack -> pack, base probe only):
  - 0 script errors from our pack in every run (only BD_VoxelPack's own voxeldef / sphere.txt lines).
  - Sweep, all 31 classes (give, select, fire, alt-fire, reload, fire): identical to r4's sweep on every
    class: same held / shots / phases, apart from shot-count jitter (Rifle 12 vs 14, FlameCannon 16 vs 14).
    Chain_Saw, Revolver and RailGun read "held False" in r4's sweep too: that is the probe's class-name
    match, not a regression. `python3 /home/claude/lane_b_b1run/tools/sweepcheck_b1.py`.
  - Off-hand reload (Depot `tools/rig/mags.py 2 11`): BrutalPistol and Flamethrower2 both go
    IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE (load 2.5).
  - Sheet `/home/claude/lane_b_out/b1_hands.png`: rest / steadied / firing for both guns, in-engine,
    from the eye. Pistol: gun hand on the grip, cup on steady. Flamer: lever hand, and the flame starts at the spout.
    The palm under the tank is hidden from this eye height.
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_2.0-b1.pk3`, sha256
  13d1f5b6f2a042f6fdefb2b094e6693fa3b6aebe6f205d167b88d664fc8907f0 (`python3 build.py 2.0-b1`;
  the build is byte-reproducible).

## 2. Flagged (first measurement, not ground on)
- **Revolver / Revolver2 (Shotvolver, same Revolver.md3, hand row 17).** These are the only other
  one-hand pistol-grip guns in 1.99 (the handtable's other cup-support row is the pistol). Measurement:
  ready frame, 1.99 placement. The grip rake matches the pistol's (backstrap 16.5 deg vs 17.4). But the
  trigger is 2.8 cm further from the backstrap (10.2 cm vs 7.4), and the grip is about 1.5 cm deeper.
  So the pistol's approved pose cannot put the web on the backstrap AND the index on the trigger.
  - Adapting it means re-solving the index (a squeeze-style pad move of 2.8 cm), not just moving the gun.
  - Also: the Moonlight lane is about to replace this mesh (above). A hand fitted to Revolver.md3
    now would be refitted.
  - Owner's call: (a) wait for Moonlight and fit that mesh, or (b) pistol grip on the old mesh with
    the index re-solved.
- Not reached: nothing else in batch 1.

## 3. Open
- Two blockers, said here and in the report:
  - Another lane writes into the SHARED checkout `/home/claude/rs_brutal22weaponsq` mid-session
    (untracked `src/*.rsqmoon`, `src/models/bd/Moonlight/`, `src/actors/Weapons/BrutalRevolver.dec`
    appeared at 06:30). `build.py` zips src/, so a build from that tree carries them. b1 was moved to its
    own worktree and built there.
  - `/home/claude/lane_b_r4/r4probe.pk3` now references BrutalRevolver and fails to compile without
    those files, so b1's gate used the base `probe.pk3` only.
- The rig lock is `flock -s` (shared), so it does not serialize engines. Lane A runs engines
  continuously. My sheet queue also started 1 min early and overlapped two sweep runs (06:37-06:38).
  Those two runs passed, and the sheet was re-shot afterwards.
- The pistol now fires from its drawn muzzle (RSQ_Muzzle). That is a VR shot-origin change on a
  BD22 gun, per CLAUDE.md's "code fits the mesh" rule. Worth the owner's eye in the headset.
- No headset pass yet. The hands still render as bare skin (lane_c REPORT: no glove texture for the FBX UVs).

---

# Hands lane, batch 2 (2026-10-27, box 07:12-08:12): BrutalSMG done, five guns flagged at the first measurement

Worktree `/home/claude/lane_b_b2` (branch `b2-hands`, pushed to `lane-b-1.99x`). Tools, logs, shots: `/home/claude/lane_b_b2run/`
(`tools/revlm.py` landmarks, `revindex.py` index re-solve, `move_b2.py` MODELDEF placement, `bake_b2.py`, `follow_b2.py`
gunmoves rows, `port_b2.py` the edits, `sheet_b2.py` / `compose_b2.py`, `sweepcheck_b2.py`). Named "batch 2", not 2.0 (owner).

## 1. Done (measured; rig only, not headset-confirmed)
### BrutalSMG: the pistol's approved hand, index re-solved; the FBX palm under the forend
- Gun hand = lane_c r5's pistol trigger pose (fbx_b1_R frame 0). Only the index's 3 pose parameters were re-solved
  (squeeze.py's method), first to the SMG trigger, then to a squeeze 0.6 cm back along the bore (the pistol's rule).
  - Before: pad 1.92 cm from the trigger face. After: 0.58 cm (spread at its joint limit, 20 deg). Squeeze: 0.14 cm.
  - Index penetration 0.26 cm. Whole hand 0.65 cm, which is the unchanged pistol fingers on the SMG grip (lane_c TOL 0.5; 1.92 median 0.95).
  - Non-index vertices moved at most 0.13 cm.
- Why it fits: the grip rake equals the pistol's (19 deg rear axis). The trigger sits 7.0 cm in front of the web and 1.5 cm below it;
  the pistol's is 7.3 cm and 0.4 cm above.
- Gun placement: the pistol's r5 orientation (same aim as the approved pistol, including its 11 deg roll), translated so
  the SMG's web point (grip top, rear profile U -3.7) sits on the pistol's. The MODELDEF chain gives Offset 0.908 -4.560,
  ZOffset -3.413, Angle/Pitch/Roll 3.854/3.363/10.974, with a residual of 0.0000 cm.
  - Applied to all 12 gun-controller blocks: bd.txt, purist (VSMG + RQBM x2), rsqoff (VSMG + RQBM x3), rsr (RQBM x3, RSR_GunParts RQBP x2).
  - The count is asserted. RSQ_Hands RQBP (off hand) and RQBW (dropped) are not moved.
- Moved with the gun (same rigid move, controller frame):
  - rsr case 3: Well (22.384, 3.230, -0.313), Axis (0.255, -0.164, 0.953), MagCentre (18.329, 4.780, -10.081), WellHook, Grab (26.687, 5.480, 2.471), Pull, HandleHook, Offset.
  - The casing port, (18.7, -0.8, 2.6).
  - gunmoves pivot row 5 (-0.908, 6.587, 19.440) and fire rows 18-20. The refit reproduces the shipped rows AND b1's pistol rows to 0.01.
- Bake: `models/rsq/fbx/fbx_b2_R.md3` holds frame 0 (trigger), frame 1 (squeeze) and frame 2 (the pistol re-bake check,
  identical to fbx_b1_R frame 0, 0.0000; unused). New sprite RQFH A/B, free in the pack, BD22 and VoxelPack. Hook 0.
- Support: the existing FBX open palm under (RQFS B, the flamer's) is moved under the SMG forend: SupportHook row 5 (-4.436, 10.601, 9.638),
  SupportRot (-7.927, 2.302, 10.732). The SupportPoint moves with the gun to (0.305, 0.038, 0.003).
  - Contact: the palm was lowered until the hand cleared the gun (pen 0.50 cm), so it sits 1.2 cm under the forend.
- Wiring: hands.zs `FbxTrgS/FbxSqzS` (squeeze on SMGF/2MGF A-C, SMGZ G-I or fullbright), `FbxSupF` for row 5;
  dualhands.zs and rsqdual/rsqoff/purist blocks for dual wield. handtable GunHook/GunHookTwo row 5 = 0.
- Gate: QZD 17.3 rig, doom2 -> brutal22test6 -> BD_VoxelPack -> pack, exclusive lock.
  - Smoke run: 0 pack script errors, BrutalSMG held and firing.
  - `mags.py 3`: IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE (`mags_b2.out`).
  - Sweep of the 32 classes: see section 3.
- Sheet `/home/claude/lane_b_out/b2_hands.png`: rest / steadied / firing, from the eye and from the side.
  - The eye pose needs pitch -25 today; b1's +25 showed the ceiling in this run (not explained).
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-hands.pk3` (`python3 build.py 1.99x-lb-r6-hands`, head 54fe2b7),
  sha256 15a1fecf968c0eee376d7d48992be2fa1ea9e1ec91cf82efc1bbf80263f4952f.

## 2. Flagged at the first measurement (not ground on). Figure: `/home/claude/lane_b_out/b2_flagged.png`
- **Revolver (Shotvolver), BrutalRevolver (Moonlight).** The problem is height, not reach. Each trigger sits well BELOW the web:
  - Revolver: 5.0 cm below and 8.8 cm in front.
  - BrutalRevolver: 4.1 cm below and 6.7 cm in front.
  - Pistol, for comparison: 0.4 cm above and 7.3 cm in front.
  - With the web on the backstrap top, the pistol pose's pad is 5.4 / 4.4 cm from the trigger. Index-only re-solve leaves 3.8 / 3.2 cm, at the joint limits.
  - Sliding the hand down the backstrap until the index reaches would need about 4-5 cm. The hand would then hang below the butt.
  - This corrects b1's "2.8 cm further" reading: the gap is mainly vertical.
  - Owner's call: a new revolver grip pose (solve from scratch), or accept a low hand.
- **MP40, Rifle.** The pistol grip pose fits the trigger reach (8.8 / 7.5 cm vs 7.3), but the grip rake is 36 / 35 deg against the pistol's 19.
  - That is 16-17 deg, about 2.5 cm at the butt, so the fingers would sink in or float.
- **Sniper (Ruger).** It has no pistol grip: a sporter stock wrist. The pistol grip pose does not apply.
- No gun files were changed for these five.

## 3. Open
- **Sweep (32 classes) still running at the box.** The rig lock alternates with the Moonlight lane's sweep, at about 1.5 min a class.
  - Done and equal to b1 / r4 so far: Melee_Attacks, BrutalAxe, Chain_Saw, DSweap, BrutalPistol (+ BrutalSMG, MP40, read by the same check).
  - Check: `python3 /home/claude/lane_b_b2run/tools/sweepcheck_b2.py` (logs `logs/sw_b2_*`).
- melee.zs SMG contact points (muzzle 18.6/-0.3/-1.2, butt 0.6/0/-10.4) are not moved. b1 did not move the pistol's either; their frame is unclear.
- SMG has no `RSQ_Muzzle` row, so its shot origin is unchanged (BD22's). The drawn muzzle moved with the gun.
- The palm under sits 1.2 cm below the forend (clearance rule). Worth the owner's eye.
- The Moonlight reload (other lane) places BrutalRevolver at Scale 1.35 / Offset 0.0262 0.9224 / ZOffset 0.5878. Any future
  revolver hand move must move their RSB rows too.
## r6-scope (2026-10-27, lane B scope): why the scope never worked, and the fix. RIG ONLY, NOT HEADSET-CONFIRMED

Done (measured on the QZD 17.3 rig, OpenXR path, left eye 8.0 cm behind the ocular; sheet `lane_b_out/scope_fix.png`):
- **Sniper REAL 3x:** the lens shows a live view down range at 3x (camera fov 6.44 deg). **DOT:** the lens shows
  the same live view at 1x (fov 19.26 deg; best fit against the naked eye from the same pose: scale 1.00)
  with the red dot on the bore line. **Eye away:** plain glass, skin off, camera texture drawn nowhere.
- Pass: no script error from the pack (only the BD_VoxelPack voxeldef lines and DeathSphereHealth). Sniper
  and RailGun selected and fired (+attack) on the rig. Reload was NOT exercised in this round.

The failing steps, with evidence (rig logs `/home/claude/lane_b_scope_rig/r1..r7.txt`):
1. **Gate, eye height** (both modes): the eye was `(pawn XY, viewz)`. With `vr_crouch_use_button` on (QZD
   default, hw_vrmodes.cpp:122) viewz does not follow the head; the renderer adds
   `(hmdY + vr_height_adjust)*vu/ps - ViewHeight` later (hw_openxrdevice.cpp:219), while the hand uses the
   controller's absolute height (`weaponoffset = ctrl - hmd`, VrInputDefault.cpp:148; AttackPos.Z :595).
   On the rig the eye came out 16 cm above where the HMD was. QZD does expose the head:
   `Actor.HmdPosition` (actor.zs:277, set each frame at hw_vrmodes.cpp:445). Now `RSQ_Scope.EyeWorld`.
2. **Gate, which eye** (both modes): the gate tested the centre between the eyes; each eye is vr_ipd/2 =
   3.2 cm off it, against a 1.35 cm lens. It could never open with an eye at the glass. Now each eye is tested.
3. **DOT basis** (ui `RSQ_Scope.Basis`): `r0` was the LEFT vector and AttackPitch was negated (on 17.3 it is
   positive up). The dot was computed on the mirror point, off the glass: never drawn. Fixed; it now matches
   the play side's AttackDir axes to 4 decimals at three logged yaw/pitch/roll poses.
4. **Dot quad edge-on:** `rsq_dot.md3` lies in the md3 y=0 plane, which the HUD chain turns edge-on to an eye
   behind the scope. `AngleOffset 90` (MODELDEF.rsq). The dot also sat exactly on the glass plane: now
   `DOT_LIFT` 0.25 cm toward the eye.
5. **Picture upside down and mirrored:** the carved glass UVs put (0,0) in the opposite corner. Camera roll 180.
6. **Magnification:** was 90/mag (mag 6), about 1.3x at 8 cm eye relief. Now `fov = 2*atan((r/relief)/mag)`
   (`FovFor`); the camera-texture fov is horizontal (mono render, VREyeInfo::GetProjection
   hw_vrmodes.cpp:343) and the glass UVs span the disc 0..1. Mag 3 (owner).
7. **DOT see-through:** clear glass cannot be see-through (the tube and the objective cap are behind it).
   DOT now renders the same camera picture at 1x under the dot: one extra render, only while an eye is at
   the eyepiece, the same cost as REAL.
Not broken: the mesh (XM21.md3 surface 10 ScopeGlass, UV 0..1, bound by MODELDEF.rsr), the table lens
(matches the glass centroid), A_ChangeModel/CMDL_USESURFACESKIN (swaps on 17.3), SetCameraToTexture.

Not done:
- **RailGun lens is covered:** the gate, skin swap and camera all run (log: skinOn=1 cam=1 fov 8.49), but
  the RailGun.md3 "Scope" surface (0) has its own lens-cap faces 0.1-0.6 mm in front of ScopeGlass
  (surface 1), covering 3 of 7 eye rays (ray cast through rgeo.py's chain at ready frame 3). Neither the
  picture nor the dot can show until those faces leave surface 0. That is a mesh job; the kit carve tool's
  selector is axis-aligned and this disc is tilted 45 deg in md3 space. Owner's call.
- The table radius (Sniper 1.35 cm) is larger than the mesh disc (about 1.23 cm from the md3 bounds), so
  the true mag is about 2.7-3x. The fit says 1.00 for DOT. Re-check in the headset.
- `rsq_scope_sniper` is an archived user cvar: an old 0 survives the 1.99x default of 1 (the rig's ini
  held 0, and the owner's may too). The menu shows the actual mode.
- Headset pass.
# Moonlight reload, lane B moon-reload (2026-10-27, 60-min box): the hand-driven VR reload on BrutalRevolver

Worktree `/home/claude/lane_b_moon` (branch `moon-reload`, pushed to `lane-b-1.99x`). Run dir, drivers, logs, dumps:
`/home/claude/lane_b_moonrun/` (`run.sh` takes the rig lock EXCLUSIVE, `drive.py` = brk.py's moves + firing after,
`mprobe.pk3` test-only ammo/pieces probe, `sweep.sh`, `sweepcheck_r6m.py`).

## Done (measured, rig-checked on QZD 17.3, doom2 -> brutal22test6 -> BD_VoxelPack -> pack)
- **Meshes** (`reference/moonlight/bake_reload.py`, output `bake_reload.txt`): `src/models/bd/Moonlight/rev_rsb.md3` =
  rev.md3 with frames 1-3 baked into the CLOSED gun (hinged part's frame-0 pose): 1 = rounds 4-9 and the speedloader
  (10) seated, 2 = the empty cage (its six 18-vertex rounds collapsed), 3 = the loader's six rounds only. Normals of
  every moved vertex turned with it. Firing still uses rev.md3. Pieces by clear skins: gun 0+2, part 1+3, loader 10.
- **RSB rows** (`rsb_guns.zs`, hand-patched like row 3; header says so): `BrutalRevolver` -> 10 (speedloader) or
  11 (a round at a time, `rsb_revolver_feed 1`).
  - Hinge (8.4556, -0.0262, -1.1446) about +L, opening 63.4 deg (frame 26 fit).
  - Seat (10): base (-2.2256, -0.1653, 1.7203), tip (8.0759, -0.169, 1.8839), bore (0.9999, -0.0004, 0.0159).
    LoaderDepth 6.23 (rounds' front 8.08 to the cylinder face 1.85).
  - Rounds (11): surfaces 4-9 from frame 20, slid along their own axis to the loader rounds' rear (F 1.735);
    6 chambers, depth 4.90.
  - Ammo: RevolverRounds / BrutalRevolverCylinder, cap 6.
  - Hold: (10) = VR_Revolver's (5) RsbCell, with the empty cage left in the hand. (11) = BD22 Revolver's (7)
    RsbShell. Each is re-anchored on the new rear (HandT).
  - Push band and push face = row 5 (the same mesh at the same placement); PushEdge maps 10/11 to row 5.
- **MODELDEF.rsqmoon**: RBMG (gun), RBMP (loader mode: A part, B seated rounds, I loader going in, H/J full/empty
  in hand), RBNP (per round: A part, B-G chambers, H one round in hand), RBMW/RBNW world (cage, loader, thrown round;
  Scale 1.35 x MODELDEF.rsb's 0.3468, centred).
- **BrutalRevolver.dec**: Reload -> RSB_Start (BD22 Revolver.dec's protocol), the r5 animation kept as RSB_Stock
  (not in VR / Real reload off). RSB_Load fills to 6 (speedloader) or one round (`GetCVar("rsb_revolver_feed")`).
  Bug found and fixed: the reserve check's +1 jump skipped a Goto and landed in the stock animation.
- **Muzzle** (`muzzle.zs`): (27.2, -0.03, 4.61). CONSTRUCTED: the mesh has no bore. It is the centre of the barrel
  box's muzzle face (F 27.02-27.38, U 4.04-5.18). Rig: both hitscans from F 27.2 L 0.0 (the probe reads U 5.5;
  its pixelstretch round trip is known to be off by about 1).
- **Casings**: a revolver ejects nothing on firing. When the gun is broken open, the six rounds are thrown as the
  mesh's own round (WorldEject, RSB_Casing): rig, 6 x RSB_Casing at full open (speedloader mode). Per round, the
  spent rounds only (1 here: one shot fired).
- **Rig, Depot `tools/rig/brk.py` moves** (open dump `open_BrutalRevolver`, then `drive.py`):
  - Speedloader: OPENING > OPEN, 6 thrown > CARRY > INSERT (7.2 cm out, 0 off the bore) > loaded >
    EMPTYLOADER > FREE (cage dropped) > flick 467 deg/s > CLOSING > DONE.
    Ammo: cylinder 0 -> 6, reserve 60 -> 54. Then 2 shots: cylinder 6 -> 4.
  - A round at a time: all 6 chambers CARRY > INSERT > loaded; cylinder 0 -> 6 one by one (reserve 60 -> 54);
    flick shut; 2 shots after.
  - 0 script errors from our pack (only BD_VoxelPack's voxeldef lines and DeathSphereHealth).
- **Sheet**: `/home/claude/lane_b_out/moon_reload.png` (in engine, left eye): closed; broken open; loader in the off
  hand; loader pushed home; rounds seated with the gun still open; flick shut.
- **Pack**: `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-moon.pk3`, built from pushed `38bc7e2` (this head;
  it carries batch 2 and the scope commit too), sha256 `5bdd0bd6105475b228f33cf25a4d7dc81cc5b8bf3734a1486fc79fadf2dde632`.
  On this pack, both reload modes were driven again: 0 script errors of ours, reserve capped at 72,
  speedloader 72 -> 66 / cylinder 0 -> 6, a round at a time 6 x loaded, 2 shots after each.
  **Rig only, not headset-confirmed.**
- **Sweep**: `sw_r6m_*` on `7b6708f` (before the ammo numbers and the rebase) covered 30 of 32 classes, then hit
  its 40-min limit (rig lock shared by 4+ lanes); Flamethrower2 and HandGrenades were not reached. Every class
  matches r5m (err 0, vm 0, same shots and phases). Chain_Saw / Revolver / RailGun read "held False" in both,
  which is the probe's name match. BrutalRevolver now opens the break reload on the button (rsb OPENING/OPEN); with
  no hand in the sweep it stays open, so 2 shots instead of r5m's 4. That is expected.
  A full sweep on the final pack (`sw_r6mf_*`, `sweep_r6mf.out`, check with `sweepcheck_r6m.py` after
  changing its tag) was started at the end of the box.

- **Ammo (owner, 2026-10-27)**: RevolverRounds 6 a pickup, carry 72. Backpack max 144, from BD22's rule for all
  four of its ammo types (Ammo.dec, parsed: backpack max = 2 x max). Backpack amount stays 6 (one speedloader).
  BD22 has no single rule for that number (shells 8 = 2x the pickup, Clip2 30 = 3x, rockets 6 = 6x, cells
  20 = 1x), so it is the owner's call. Map spawns: none (unchanged).

## Not done / open
- Machine: the root volume showed 0 MB free during this box (df: 252G size, 42G used, ~500M available). My frame
  dumps were deleted after the sheet was made. Something outside this lane is holding the space.
- Frame dumps slow the rig, so the scripted hand needed retries (`SLOW=3`). Without dumps, every capture is first-try.
- The loader's rounds sit 0.3 cm off the cylinder axis (L -0.17 U 1.82 vs chambers L -0.01 U 2.15): the mesh's own
  animation. It is kept as measured.
- Shut without loading: the cylinder count keeps its live rounds although all six were thrown (the same as rows 3/5).
- Push-shut uses row 5's face table (VR_Revolver), not re-measured on this hinge (1 cm apart). The flick is what was
  driven.
- Dual wield, recoil, `gunmoves.zs` re-fit, the hand pose (batch 2's call), and the pickup art are all not touched.

## Melee lane r6 (2026-10-27, owner report items 16, 17, 7, 8, 9, 10)
Everything here is **rig only, not headset-confirmed** (QZD 17.3 rig, doom2 -> brutal22test6 ->
BD_VoxelPack -> pack). Logs: `lane_b_out/melee_r6_logs/` (`MT` lines from the test driver, which is
`driver_ZSCRIPT.txt` there: it writes `qzt_rhand` / `qzt_rtrigger` each tic). Sheet: `lane_b_out/melee_fixes.png`.
Pack: `lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-melee.pk3` (+ `.sha256`). No script error from the pack
in any run (only BD_VoxelPack's voxeldef lines and DeathSphereHealth).

### 1. Done (shown on the rig)
- **16 pistol whip, main hand.** Cause (code): `RSVR_Hand.ReadyPose` required sprite frame A, and
  BrutalPistol's Ready holds PIST E (loaded), PIST I (empty) or 2IST E, so the whip was never armed.
  The off hand's "downstroke" was its free fist (fists.zs). Fix: accept those frames. MODELDEF binds
  them to model frames 7 and 3; a rigid fit of BrutalPistol.md3 frame 3 onto 7 (6828 vertices) moves
  the whip points 0.1 unit, so the measured points stand. Rig, same 0.21 m/tic down-stroke:
  before (71957b2) `PIST frm=4 ready=0`, no hit; after `ready=1`, MeleeStrikeNormal 13 at t170.
- **9 axe edge.** A cut needs cos(edge, motion) >= `rsvr_axe_edge` (0.5, the cosine the two-handed
  bite already used); edge = BladeOut - BladeIn in the body frame, motion = the edge point's velocity.
  The old "rises > 0.15 = wind-up" rule is kept as well. Rig (pure translations, 0.21 m/tic):
  down roll 0 cos +0.60 HIT; up -0.60 none; side roll 0 0.00 none; side left roll +90 +0.96 HIT;
  side right roll +90 -0.96 none; side left roll -90 -0.96 none; side right roll -90 +0.96 HIT.
- **7 chainsaw.** In VR the trigger runs `Saw.dec RSVR_SawRun` (SAWG A/B, no swing animation, BD22's
  loop sound and shake); `melee.zs` kind SAW cuts whatever the bar touches, moving or still, with
  BD22's SawDamageHorizontal (5-6 Cut) every 2 tics per body. Bar measured from Chain_saw.md3 frame 11,
  surface Cube.002_Cube, x 56.0..103.8, centre y -2.1 z -5.15, x MODELDEF Scale 1.5, Offset y 10.
  Rig: bar in the body, trigger off 35 tics: 0 hits; trigger on: a hit every 2 tics.
- **8 axe lock-on** was already built (F11): `RSVR_AxeLock`, sprite RQLK, one target, kept 1 s after a
  release. Rig: trigger held pointing at a zombie, RSVR_AxeLock on PistolZombie at t524, held to t566.

### 2. Flagged
- **17 hit flash.** Code: `RSVR_MeleeHandler.WorldThingDamaged` spawns `RSQ_BashFX` wherever a
  player's MeleeStrike1-family or KickAttack-family actor damages something (punch, whip, butt strike;
  the bash keeps its own spawn; KickAttackDetectDowned excluded). The tint now applies to all five
  effects. Menu row "Bash Impact" renamed "Melee Hit Flash"; the colour row keeps its old name
  because the colour is NOT proved. Shown: the flash spawns on every whip hit (log, 5 hits, translation
  set for tints 1-4). NOT shown: the frames draw RSH0 at the gun hand rather than at its spawn point,
  and tints 1-4 look white rather than blue/green/amber. Needs a look at RSH0's sprite offsets and the
  `%[...]` ramp on this renderer. Punch and butt strike were not driven on the rig (same code path).
- **7, out of range.** The test zombie walked after the bar, so "no cut once the bar leaves" is not
  cleanly shown. One chainsaw frame (sheet row 2, third) draws the saw in a different pose: not traced.
- **10 two-handed sword: not built.** Cause (engine source, VrInputDefault.cpp 131-175): with
  `vr_two_handed_weapons` on, an off grip pressed within 50 cm sets weaponStabilised and the engine
  re-aims the weapon from the main hand AT the off hand. On a sword the off hand is below/behind the
  main hand, so the blade swings onto the off hand. ZScript cannot clear that cvar outside a menu
  (vmnatives.cpp 951) and the main controller's own orientation is lost while stabilised.
  Proposed (owner's call): when the sword is steadied, draw it from a second sprite whose MODELDEF
  block is turned 180 degrees, so the handle runs from the main hand toward the off hand and the blade
  points away from it (both hands then genuinely drive it), place the off-hand mesh on the handle at
  the hands' measured distance, flip BladeIn/BladeOut the same way, and add a quarter strength
  (DSAttack + DSAttack2 + a 0.25x actor, 1.25x). Needs a sprite lump and rig frames to place.

### 3. Open
- The shared disk filled to 0 MB twice during this session (other lanes' output); one frame dump was
  cut short by it.
- No sweep of all classes was run (time box); the four driven weapons and the whole pack compile clean.
## r6-scope2 (2026-10-27, lane B scope): the RailGun scope. RIG ONLY, NOT HEADSET-CONFIRMED

Done (QZD 17.3 rig, OpenXR path, left eye 8.0 cm behind the ocular at eyeL (-9.71, -0.09, 11.81);
sheet `lane_b_out/scope_fix2.png`, pack `BD22_VR-Reloaded_1.99x-lb-r6-scope2.pk3`):
- **REAL 3x** (rsq_scope_railgun 1): live view down range in the lens, upright (camera fov 8.49 deg).
  **DOT** (0): the same view at 1x with the red dot. **Eye away** (10 cm back, 6 up, 4 left): plain glass.
- Selects, fires (zombie killed on the rig), reloads: Depot rig `mags.py` gun 6 ran
  IDLE > EMPTY > DROP > CARRY > INSERT > SEATED > DONE > IDLE. No script error from the pack (only
  voxeldef lines and DeathSphereHealth).
- Magnification by the camera fov: exactly 3x of DOT. An image fit of REAL against DOT at rig resolution
  (lens about 26 px in radius) is too flat to confirm it (shallow minimum at 2.7). Re-check in the headset.

**Correction of r6-scope:** the RailGun's lens was NOT covered by a lens cap. The 24-triangle fan in
surface 0 (tris 2131-2154) lies behind the glass from every eye pose tried (ray cast: 0 of 77 rays at 5
poses, including both eyes and eye-away poses). The real fault was MODELDEF: the block that draws the
RailGun's Ready frames (MODELDEF.bd.txt, RAIL A/B/C) had a whole-model `Skin 0 "RailGun.png"`. A
whole-model Skin wins over every SurfaceSkin AND over A_ChangeModel's surface-skin swap
(models_md3.cpp:359-369), so the glass showed the whole atlas squeezed into its 0..1 UVs and the camera
picture could never land. Now per-surface skins (0, 2, 3, 4 RailGun.png; 1 scope_glass.png). The same
whole-model Skin / atlas-on-glass was in PuristRailGun (MODELDEF.purist) and RSQ_Off_RailGun
(MODELDEF.rsqoff, dual-wield): their glass is scope_glass.png now (plain glass; no camera, as before).
**RailGun.md3 is unchanged.** The Depot has the tilted-disc selector now (tools/kit/md3_carve_disc.py),
dry-run-checked on this mesh, if a real cap is ever found.

Not done: headset pass.
# r6 reloads lane (2026-10-27, box 07:31-08:46): owner r3 report items 13 and 14, branch `newreloads`

## Done (rig only, NOT headset-confirmed)
### Item 13: real magazines on Flamethrower2 (100), Unmaker (200), Machinegun (100), chaingun = `MiniGun` (200)
- What was there (1.97): `RSQ_Counters` gave these guns a COUNTER that is a share of the reserve
  (mag <= reserve). So a magazine as large as the whole reserve (Minigun 200 vs Clip2 200, see the README's
  old Minigun note) can never run dry before the reserve, and never asks for a reload.
- Now (`counters.zs` `REAL[]`, `RealTick`): a separate magazine (`RSQ_Mag_<gun>`), a pouch (BD22's own
  reserve item: Gas, SoulAmmo, Clip2; unchanged) and up to 10 rounds lent from the magazine into the
  reserve item (`RSQ_Lent_<gun>`, inventory, so it survives maps and saves) so BD22's own fire code
  (A_JumpIfNoAmmo, DepleteAmmo) still has ammo to spend. Every round BD22 takes is charged to the magazine.
  Seated: min(cap - mag, pouch) moves from the pouch into the magazine (a top-up; the rounds stay in the
  magazine while it is out, none are lost). Empty magazine (`RSQ_Empty`) jumps Fire/Hold to Reload (the
  existing posefix lines). Reload starts only with rounds in the pouch (`RSQ_Pouch_<gun>` token), or to put
  an out magazine back (`RSQ_NoMag` line added to each gun's Reload).
- Off (rsq_reload_nonstd 0, rsr_reload 0 or not in VR) and the gun held: the magazine's rounds go back
  to the reserve (as far as its MaxAmount holds them), lent rounds are taken back: Brutal Doom's gun.
  Not held: lent rounds are taken back so the Rifle etc. never spend them on Clip2.
- Flamethrower2: its Reload was already a real path in this pack (BD22's shared ReadyDry/Reload label
  was split in 1.99, `ca47d85`); unchanged apart from the lines above. Grip/hand rows and flamespout untouched.
- Parts carried: the existing F10 parts (canister, Unmaker skull, Minigun box, Machinegun box), unchanged.
- Trap found: ZScript names are case-insensitive. `int m = min(d, M)` re-declared `M`; the counter never
  went down. Fixed by naming (`fromMag`).
- Rig evidence, QZD 17.3, load order doom2 -> brutal22test6 -> BD_VoxelPack -> pack + probe,
  `/home/claude/lane_b_out/r6_reloads_evidence/` (evidence_r6.txt, logs/, r6_reload_frames.png, drivers):

| gun | start | fire held to empty | trigger on empty | hand reload (off hand, Depot mags.at poses) | fire again (80 tics) |
|---|---|---|---|---|---|
| Flamethrower2 | mag 100, pouch 150 | 100 spent, empty t370 | 0 spent | EMPTY>CARRY>INSERT>SEATED, mag 0->100, pouch 150->50 | 84 spent |
| Unmaker | mag 200, pouch 250 | 200 spent (100 shots x 2) | 0 | mag 0->200, pouch 250->50 | 152 |
| MiniGun | mag 200, pouch 200 (backpack) | 200 spent, empty t871 | 0 | mag 0->200, pouch 200->0 | 27 |
| Machinegun | mag 100, pouch 300 (backpack) | 100 spent | 0 | mag 0->100, pouch 300->200 | 28 |

- Class sweep (`r6_classes.log`): all 37 weapon classes given, selected, fired, alt-fired, reloaded in one
  run: no script error or VM abort; only BD_VoxelPack voxeldef lines and DeathSphereHealth (baseline).
  The six Dual* classes were not selected by `use` (they need BD22's dual pickup); not a regression check of dual.
- pk3 `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-reloads.pk3`, sha256
  ff62c686a40c36f9ef0042a70b974aac2d7350b5886affe8e5a2e112a2f05583 (build.py reproduces it byte for byte
  from this branch before the rebase).

## Flagged
- Frames (`r6_reload_frames.png`): the canister is shown in the off hand and seated. The Unmaker skull is
  drawn off the hand (mid-air, ~10 cm off) during the carry; the Minigun's carried part draws as a small
  dark piece by the hand; the Machinegun box is not visible in these camera angles. These are the F10
  carry poses (item 10: "not refitted" for skull/box), not the magazine code; the logs show each part
  taken and seated.
- The HUD shows BD22's reserve item = pouch + up to 10 lent rounds, not the magazine count.
- Balance: like BD22's own Rifle (RifleAmmo + Clip2), the magazine is carried on top of the reserve:
  the chaingun can now carry 200 + Clip2's 200/400. That is what the owner's 200 needs; his call to confirm.
- Each new map starts with a top-up (the handler is per level), as the 1.97 counters did.

## Not reached
- Item 14 (dual options for every gun): not started in this box.


## Melee lane r6b (2026-10-27): item 10 built, item 17 fixed, item 7 out-of-range shown
**Rig only, not headset-confirmed.** Pack `lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-melee2.pk3` (+ `.sha256`),
sheet `lane_b_out/melee_fixes2.png`, logs `lane_b_out/melee_r6b_logs/` (`fin2` = the shipped pack on the
load order: no script error from the pack, no abort).

### 1. Done (shown on the rig)
- **10 two-handed sword (owner-approved plan, 2.0x).** While the engine steadies the Dragonslayer
  (WF_TWOHANDSTABILIZED: off grip within 50 cm), `RSVR_SwordTwo` is set and Dragonslayer.dec draws
  `DSL2 A` (TwoHand state). MODELDEF.bd.txt's DSL2 block is the same mesh with PitchOffset 110 about the
  main hand's grip point, md3 (30/ws, 0, 0) (Offset y -40.26, ZOffset -33.19): DSweap.md3 frame 0's
  handle (guard t=-14 to pommel t=-62 along (0.342, 0, 0.940), measured) then runs along the engine's
  aim, i.e. toward the off hand, and the blade away from it. melee.zs Place applies the same turn
  (rig: handle . forward = 1.00). The main hand's motion still drives the swing; the hit
  is the same pair fired twice (DSAttack and DSAttack2 are fixed damage: Damage (random(200,200))).
  Rig, same downswing into the same zombie: one hand DSAttack 1x200 + DSAttack2 55 = 255; two hands
  2x200 + 110 = 510. Hands: the support hand is hidden; the off hand shows as the free fist at the off
  controller, which is on the handle line by construction. The gun hand takes the same 110-degree turn
  about the grip (hands.zs). The placement is eyeballed on rig frames, not measured.
  A change of placement (one hand <-> two) now resets the swing history (it read as a swing).
- **17 flash at its spawn point.** The 52 RS* FX PNGs had no grAb offsets, so they hung down-right of
  the hit point. Centred grAb (w/2, h/2) added. Rig: probe at 60 u straight ahead draws centred there.
- **17 tints.** A translation did nothing on these truecolor PNGs on this renderer. Now RSQ_BashFX
  sets STYLE_AddShaded + SetShade (TRNSLATE ramps' top colours). Rig: blue, green, amber shown.
  Menu row renamed "Melee Hit Flash Colour".
- **7 bar leaves.** Zombie pinned (SetOrigin each tic), trigger held throughout: cuts every 2 tics while
  in, last cut t760 while the bar was being pulled back, 0 cuts over 40 tics with the bar clear.

### 2. Flagged
- Tint 4 (white) was not captured in a frame (the probe frame missed it); 0-3 were.
- The first sword test swing was marginal: the blade crossed the zombie at about z 111-115 against its
  112 top, so whether it cut depended on which pose sample landed (m3, fin3: swing, no cut). The test
  now swings 28 cm lower: `fin4` (the shipped pack after the rebase) cut on all 4 swings, two hands
  510 and one hand 255 both times. The sword numbers in the sheet are from `fin2` (same code, pre-rebase).
- Saw, fin3: one cut landed on the first tic of the bar-clear hold (pose lag of a tic); fin2 was clean.
---

# Hands lane, batch 3 (2026-10-27, box 08:11-09:26): MP40 done from 1.92's hold; Rifle fitted, not ported; three not reached

Worktree `/home/claude/lane_b_b3` (branch `b3-hands`, pushed to `lane-b-1.99x`). Tools, logs, shots: `/home/claude/lane_b_b3run/`
(`tools/m192.py` 1.92 landmarks, `rigid3.py` stage 1/2 placement, `curl3.py` finger curls + squeeze, `fit3.py` gun landmarks
(Rifle/MP40 added to revlm), `bake_b3.py`, `port_b3.py`, `sheet_b3.py`, `compose_b3.py`, `sweepcheck_b3.py`). Everything below is
RIG ONLY, NOT HEADSET-CONFIRMED.

## The method (new in batch 3): start from where 1.92's hand sits on the gun
1. `m192.py`: 1.92's displayed gun hand (Ermac hand.md3, the handtable row and trigger frame from lane_c `rows192.json`) on each gun,
   in 1.92's controller frame. All four guns are drawn at Offset 0 0 / ZOffset -5 in 1.92 and 1.99 (meshes md5-equal), so this is
   the hand's placement relative to the gun. Landmarks: web, palm, cuff, the four knuckles (lane_c `ermaclm`).
   - T = rigid fit of 1.92's pistol hand onto 1.92's hand on that gun. Rifle and MP40 use 1.92 frame 106: 10.6 deg off the
     pistol hand (yaw 9.2, pitch -2.0, roll -5.1). Fit residual 0.1-1.0 cm. 1.92's Revolver uses the pistol's own frame 6,
     moved 3.25 cm forward with no turn: 1.92 does NOT hold the revolver lower.
2. The approved FBX pistol hand (lane_c r5 frame 0) is moved by T, then re-placed rigidly onto the grip (`rigid3.stage2`):
   no penetration past 0.25 cm, palm and web onto the grip, index pad to the trigger, turn kept near 1.92's.
3. `curl3.py`: middle, ring and pinky curls closed to 0.2 cm; the squeeze moves the index pad 0.6 cm back along the bore.
4. The gun keeps the pistol's r5 aim and moves to the hand, so the cuff stays where the approved pistol hand's cuff is.
   The hand turns on the wrist the way 1.92's does. That is a choice; the alternative is to tilt the gun, which would move the drawn bore off the shot line.

## 1. Done (measured; rig only, not headset-confirmed)
### MP40 (row 12)
- Fit, in cm. Before the curls: palm 0.29, web 0.09, index pad 0.51 from the trigger face, penetration 0.29.
  After the curls: M/R/P pads 0.20, thumb 0.02. Squeeze: travel 0.60, pad 1.10 from the trigger face.
  Turned 10.3 deg vs the pistol hand (euler Z/Y/X 6.2 / 3.0 / -7.5). 1.92 had 10.6.
- Gun: Offset -0.982 -4.470, ZOffset -2.213, Angle/Pitch/Roll 3.854/3.363/10.974, residual 0.0000 cm.
  - Applied to all 11 gun-controller blocks (count asserted): bd.txt 1, purist 3, rsqoff 3, rsr MP40 RQMM 2, RSR_GunParts RQMP 2.
  - Not moved: RSQ_Hands RQMP (off hand) and RSR_DroppedMag RQMW.
- Moved with the gun:
  - rsr case 4: Well (35.546, 4.753, 8.153), Axis (-0.045, -0.195, 0.980), MagCentre (35.775, 5.987, 1.812), WellHook, Grab (26.725, 5.073, 9.243), Pull, HandleHook, Offset.
  - The casing port, (38.9, 2.5, 9.4).
  - gunmoves pivot row 12 (0.98, 7.79, 19.53) and fire rows 42-45. The original placement reproduces the shipped rows exactly.
- Bake: `models/rsq/fbx/fbx_b3_R.md3` (0 trigger, 1 squeeze, 2 = the pistol re-bake check, identical to fbx_b1_R frame 0, unused).
  - New sprite RQFI A/B, free in the pack, BD22 and VoxelPack. Hook 0.
  - Squeeze on MP40 B D E Q R S / PP40 B D E (the gunmoves fire frames) or fullbright. Dual wield wired.
- Support: RQFS B (the FBX palm-under) under the barrel at 1.92's SupportPoint (40, 0, 3.3), moved with the gun to (0.440, 0.050, 0.101) m.
  Penetration 0.47 cm, palm gap 0.40 cm.
### BrutalSMG: RSQ_Muzzle row (batch 2 left it open)
- (39.6, 4.4, 0.8): the centre of the front-most face of BrutalSMG.md3 frame 3 (surface 1, F 35.07, L +-1.02, U -5.74..-3.71
  at the 1.99 placement: the barrel end), moved by batch 2's move. The pistol's row check through the same transform: 23.33 2.19 6.34.

## 2. Fitted but not ported: Rifle (row 18)
- Same method. Before the curls: palm 0.28, web 0.04, index pad 0.28 from the trigger face, penetration 0.26.
  After the curls: M/R/P pads 0.20, thumb 0.51. Squeeze: travel 0.60, pad 0.76 from the trigger face.
  Turned 8.9 deg vs the pistol hand (euler 4.5 / 3.0 / -6.9). Gun shift in the 1.99 frame (-2.40, 0.57, -0.38).
  Numbers and vertices: `/home/claude/lane_b_b3run/curl3_Rifle.json`, `st2_Rifle.npy`.
- So the 35 deg rake does not stop the FBX hand: 1.92's placement plus a rigid re-seat closes palm, web and index without changing the pistol curl.
- Not ported in the box. The Rifle draws through about 25 MODELDEF blocks: bd, purist, rsm, rsqoff and rsr, each with M203.md3 as model 1,
  plus `RSR_GunParts` M203 RQ2P. The M203 reload (RSK_M203Handler) has its own controller-frame points, and hands.zs special-cases
  row 18 for the M203 trigger grip.
  - Moving all of that with the gun is the next job: `port_b3.py` generalised, plus the RSK tables.
  - I did not start a half-move.

## 3. Not reached (measured only, no files changed)
- **Revolver (Shotvolver).** 1.92 holds it with the PISTOL's hand frame, 3.25 cm further forward, not lower.
  `rigid3.stage2`: palm 0.02, web 0.01, penetration 0.34, turned 7.4 deg. The index pad is still 1.93 cm from the trigger
  (pistol curl), with M/R/P gaps 1.3-1.4. Next: index re-solve plus curl3. Expect it to close: batch 2 had 3.2-3.8 cm left at the joint limits from the web-on-backstrap start.
- **BrutalRevolver (Moonlight):** not in 1.92 (no reference hold). Not started. Its reload rows (Moonlight lane) would move with the gun.
- **Sniper (Ruger/XM21):** not started. The Depot's `Sniper.json` is from BD22_main (a different mesh), so there is no 1.92 Ruger hold to measure.

## 4. Gate (QZD 17.3 rig, doom2 -> brutal22test6 -> BD_VoxelPack -> pack, exclusive lock)
- MP40 and BrutalSMG: give, select, fire, alt-fire, reload, fire. 0 pack script errors (only BD_VoxelPack's lines and
  DeathSphereHealth). Held, shots 12 / 16, phases DROP,EMPTY: equal to r4 / b1 / b2 (`tools/sweepcheck_b3.py`).
- Off-hand reload (Depot `tools/rig/mags.py 4 3`): MP40 and BrutalSMG both go IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE (`mags_b3.out`).
- Sheet `/home/claude/lane_b_out/b3_hands.png`: the MP40 at rest, steadied and firing, from the eye and the side, beside 1.92's
  eye and side renders. Side view: hand around the grip, index at the trigger, palm under the barrel when steadied.
- The BrutalSMG muzzle row is NOT shown working. The rig sweep logs carry no shot-origin line, and the muzzle path runs only
  in VR (`RSVR_VRHand.InVR`). It is the same code path as the pistol's and the Ruger's rows.
- 32-class sweep: batch 2's sweep reached 25 classes on its own pack (all equal to b1/r4). This batch did not finish the rest.
  - The rig lock rotates between 4 lanes, about 3 minutes per engine run here; the sheet and gates came first.
  - The 7 left: BIG_FUCKING_GUN, HellishMissileLauncher, Unmaker, FlameCannon, Flamethrower2, HandGrenades, BrutalRevolver.
  - Run them with `/home/claude/lane_b_b3run/sweep3.sh <pk3> b3`.
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r6-hands3.pk3`, sha256
  850b1c40d3f2033f55d169e9d8189711da7617e3aa82aceb50091b508116fed2. Built with `python3 build.py 1.99x-lb-r6-hands3` at the head
  rebased onto origin as it stood at 09:02 (it includes r6 reloads ec08cf6, the RailGun scope and melee r6; NOT melee r6b 19f0203,
  which landed after the build).
  - Gated on this exact pack: MP40 and BrutalSMG give / select / fire / alt-fire / reload. 0 pack script errors, held, shots 12 / 16,
    phases DROP,EMPTY (`logs/fin_b3_*`).
  - The sheet and `mags.py` ran on the pre-rebase build of the same hands code (`t.pk3`).
- Next, in order:
  1. Port the Rifle (numbers ready).
  2. Shotvolver: index + curls (`curl3.py +Revolver`; it was still solving at the box).
  3. Finish the sweep.
  4. BrutalRevolver and Sniper: no 1.92 hold to start from. Owner's call on the reference.

---

# Hands lane, batch 4 (2026-10-27, box 10:02-11:32): port_gun.py; Rifle, Shotvolver, BrutalRevolver ported; Sniper flagged. RIG ONLY, NOT HEADSET-CONFIRMED

Worktree `/home/claude/lane_b_b4` (pushed to `lane-b-1.99x`). Tools in the repo: `tools/handfit/port/` (README section "port/port_gun.py").
One method for every gun (owner): the drawn wrist stays pinned where the approved pistol hand's is, and the GUN moves to the hand.

## 1. Done (measured; rig only, not headset-confirmed)
- **`port_gun.py <Class> <fit.json>`** (`2a503ff`, later commits extend it): applies the gun move to every gun-controller MODELDEF block
  (counts asserted) and moves every table that hangs off the gun: gunmoves Pivot + fire rows (found from `key[]`; the original
  placement must reproduce the shipped rows), rsr reload case, rsb break-open rows, casing port, RSQ_Muzzle, RSQ_ScopeTable, the M203;
  optional FBX gun-hand wiring. Writes nothing unless every step passes. Lists what it moved (`fits/ported_<Class>.json`).
  - Verified: `port/verify_mp40.sh` re-applies batch 3's MP40 move on 19f0203 and diffs against bdf3fae: byte-identical except
    the BrutalSMG muzzle row that commit also added.
- **Stopped run reverted** (`94f990e`): its Shotvolver and BrutalRevolver baked the hand on the UNMOVED gun (hand-to-gun shortcut).
  All three of its guns were redone with the tool.
- **Rifle** (row 18, `4c54425`): batch 3's fit. Gun Offset 0.348 -5.912, ZOffset -1.812, Angle/Pitch/Roll 3.854/3.363/10.974 (chain residual 0.0000 cm).
  - 26 MODELDEF blocks incl. M203 and the M203 parts. Also moved: gunmoves pivot + rows 93-95, reload case 1, casing port (15.7, 1.2, 8.0),
    muzzle row added at the drawn tip (71.18, 6.06, 11.42), purist handguard hook, and support pose C under the tube.
  - M203: its tables stay in the rifle's original frame; `RSM_Geo.ToGun/DirToGun/FromGun` carry points across, and FwdHook is the moved axis.
  - The numbers equal the stopped run's independent port (a28201d).
  - The hands.zs M203 TriggerGrip special case is dead code (`TriggerGrip()` returns false since 1.32), so it was not touched.
- **Shotvolver** (Revolver / Revolver2, row 17): batch 3's re-seat + `curl3 +Revolver`: index pad 0.48 cm from the trigger, M/R/P 0.20, pen 0.34,
  palm 0.02, web 0.01, squeeze 0.60. Gun Offset 0.466 -5.416, ZOffset -2.801, same angles.
  - 14 MODELDEF blocks, gunmoves pivot + rows 71-92, RSB rows 3/7/8/9, casing ports (Revolver, Revolver2), muzzle row added (26.67, 2.61, 7.04).
  - Rule found: RSB.Hook uses `Offset(i)` for the hinged parts AND for the round in the off hand. So the off-hand RSQ_Hands RBRP block
    moves too, and the hold rows are re-expressed (Hand0-2 = g R^T, HandT = HandT - g R^T t), so the hand's hold is unchanged.
- **BrutalRevolver** (Moonlight, shared row 17, own hand RQFL selected by class): the Shotvolver's solved hold re-seated on its grip
  (`reseat_from.py`) + index/curls: pad 0.00, M 0.20, R 0.17, P 0.25, pen 0.38 (rigid-only pen 0.61), palm 0.36.
  - Gun Offset 0.843 -7.091, ZOffset 1.059, Angle/Pitch/Roll -3.854/3.363/-10.974 (positive mesh scale; residual 0.0000).
  - 15 MODELDEF.rsqmoon blocks, RSB rows 10/11 (incl. the off-hand round), muzzle row 27.2/-0.03/4.61 -> 35.03/3.24/8.51.
- **Poses as data** (`tools/handfit/poses/<Class>.json`, `port/rebake.py`): full joint vectors (trigger, squeeze), solved fingers,
  wrist placement, gun move, FBX source. Rebake from the JSON reproduces all three committed MD3s exactly (0.0000).
- **Gate on the delivered pack** (QZD 17.3 rig, doom2 -> brutal22test6 -> BD_VoxelPack -> pack, exclusive lock, `port/gate_gun.py`, logs `/home/claude/lane_b_b4run/g4/`):
  - smoke (give, select, steady, fire, alt-fire, reload, fire), 0 pack script errors:
    - Rifle: held, 14 shots, phases DROP,EMPTY.
    - Revolver: 2 shots; "held False" is the probe's class-name match, as in r4.
    - Revolver2: held, 12 shots.
    - BrutalRevolver: held, 2 shots.
  - Hand reloads:
    - Rifle magazine (`mags.py 1`): IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE.
    - Rifle M203 on the moved gun: latch > open > round in the breech > round home > shut: loaded.
    - Revolver break (`brk.py`): OPEN > CARRY > INSERT (0.0 cm off the bore) > chamber loaded. This equals the unmoved baseline pack (same script, `g3/`).
    - BrutalRevolver speedloader: loaded > flick 457 deg/s > CLOSING > DONE.
    - BrutalRevolver per round: each chamber loaded, 0.0 cm off the bore, flick shut, loaded 6.
- Sheet `/home/claude/lane_b_out/b4_hands.png`: Rifle, Revolver and BrutalRevolver at rest, steadied and firing, from the eye and the side,
  each beside its 1.92 render (BrutalRevolver has none). Shots come from the test packs of the same src.
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r8-hands.pk3`, built at `8a3d0e5` (src unchanged since; includes the shotgun lane's AssaultShotgun),
  sha256 1d97467a7e2696e2f1d04b77a5de64e6d2a57534583e9757e7c4673ebc166b76.

## 2. Not done / flagged
- **Sniper (Ruger/XM21): flagged, not ported.** The Rifle's hold moved to the Ruger trigger and re-seated rigidly
  (stopped run, the same tool) leaves pen 1.65 cm, palm 1.18, index pad 1.84 from the trigger, and M/R/P 3.0/5.1/7.2 cm.
  The stock wrist is not a pistol grip. A 400-iteration re-seat (`sniper_fit.py`) hit its 20-min limit. Registry and scope/muzzle/rsr
  movers are ready (`GUNS['Sniper']`); the eye-at-eyepiece scope re-check was not reached.
- **Support hands are still Ermac's** on the Rifle (pose C under the M203 tube, moved with the gun) and on both revolvers (the cup;
  unchanged because it cups the pinned gun hand). The owner asked for the FBX support poses as on the MP40/SMG/Flamethrower. Not done in this box.
- The Revolver side-view rest frame on the sheet is framed off (the camera, not the gun). Steady and fire side frames show the hand on the grip.
- BrutalRevolver has no gunmoves rows of its own (RVMA is not in the table) and shares Pivot row 17 with the Revolver. Dual wield for it is not wired (it had none).
- Revolver2 does not inherit Revolver: its shots keep BD22's origin (no Revolver2 muzzle row).
- The fitter snapshot in `tools/handfit/fbx_fitter/` lacks its lane data. `bake_gun.py` and `rebake.py` need `RSQ_HANDS_TOOL` = a full checkout.
- Item 5 (Shot_Gun etc.) was dropped by the coordinator: the shotgun and heavy lanes have them.

# Hands lane: SHOTGUNS (2026-10-27, 10:07-11:45; rig only, not headset-confirmed)
Method: batch 3's, unchanged (m192 -> rigid3.stage2 -> curl3 M/R/P + index), the drawn wrist pinned and the GUN moved to
the hand with port_gun.py (wrapped by `tools/handfit/shotguns/port_sg.py`, which adds Shot_Gun / AssaultShotgun / SSG to
its registry, the pump tables and the case-form break-open rows). Support = the FBX palm-under / pump grip (fbx_b1_L
frame 1, RQFS B, label FbxSupF), never Ermac's glove. Pose data per gun: `tools/handfit/poses/<Class>.json`.

## Done (measured; rig only, not headset-confirmed)
- **AssaultShotgun (row 1, hand sprite RQFQ, fbx_sg_AssaultShotgun_R.md3).** 1.92 hold carried over (m192 residual
  <= 0.99 cm); hand turned 33 deg on the wrist vs the pistol (1.92's own turn), gun shift (-3.8, 3.7, -11.3) cm.
  Index re-solved: pad 0.15 cm from the trigger, squeeze 0.45 cm, M/R/P gaps 0.20, max penetration 0.49 cm.
  Moved: 13 MODELDEF blocks, gunmoves Pivot + rows 0-5, RSR case 5 (Well/MagCentre/Grab/Axis/WellHook/Pull/HandleHook/Offset),
  casing port, muzzle row (added). Rig: no script errors outside BD_VoxelPack; give/select/fire/alt/reload held,
  10 shots; hand mag reload (mags.py 5) IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE. ~25 min.
  Pose data: tools/handfit/poses/AssaultShotgun.json.
- **Shot_Gun (row 21, hand sprite RQFP, fbx_sg_Shot_Gun_R.md3).** m192 residual <= 0.5 cm; hand 2.5 deg from 1.92's
  placement (30 deg vs the pistol), gun shift (-4.2, 3.1, -8.1) cm. Index on the trigger (0.0 cm), squeeze 0.60 cm,
  M/R/P 0.20, max penetration 0.55 cm (0.05 over the 0.5 tolerance). Moved: MODELDEF (bd, purist x2, rsqoff x2,
  rsrpump gun + pump/bolt/shell parts), gunmoves Pivot + its fire rows, the pump table (rsr_pump_guns case 1: Grab,
  Port, Pull, Push, PumpHook, SupportHook, PortHook, Offset), the side port's literals in rsr_pump.zs (PortK, PushK,
  new BoreK, casing-out point), casing port, muzzle row (added). Rig: no script errors; give/select/fire held, 4 shots;
  pump test (pump_sg.py, the Depot pump.py with moved numbers): two shells through the port, pump grabbed at 0.0 cm,
  full stroke, "ready". ~35 min (two fits OOM-killed in the shared 8 GB cgroup; fit now collides against the gun
  behind F = 25 cm only, fit_sg.py `crop`).
- Sheet: /home/claude/lane_b_out/hands_shotguns.png (at rest, steadied, firing; eye and side; next to 1.92).
  Side views match 1.92's layout (gun hand on the grip, FBX palm on the pump / forend).

## Flags (open)
- Shot_Gun support palm on the pump: no drop within 4 cm clears 0.5 cm; the least-penetrating one is used (0.70 cm).
- Eye tiles: at rest the gun hand is below the frame; steadied eye tiles show the gun pointing back at the camera
  (both guns). Not judged; needs the owner's headset or a better eye pose. Shot_Gun eye-at-rest shows a large striped
  object at the lower right: not identified.
- Squeeze frames: AssaultShotgun 2SAS B-E, 3SAR I, USAS J N O; Shot_Gun SHTN/2HTN B-H (from the gunmoves rows;
  not shown squeezing on the rig).
- Hand sprites RQFP / RQFQ are new: free in the pack, BD22 and BD_VoxelPack at 10:30; check against the other lanes.
- Fit JSONs point at the baked md3 in /home/claude/lane_b_sgrun (cloud path); the md3s are committed in src.

## Not reached
- **SSG (row 20):** fit not run to the end (OOM, then time). port_sg registers it and moves Hinge/Axis/PushRef/Offset
  (dry run passes), but its Base/Tip/Bore/Rest rows and PushZ/PushR scalars are NOT moved yet: do not port it as is.
- **Revolver2:** shares row 17 and Revolver.md3 with the Revolver (Shotvolver), which the other lane re-ports with
  port_gun.py (Revolver entry has casing2='Revolver2'); not touched here to avoid two moves of one mesh.

# Hands lane, batch 5 (2026-10-27, box 11:22-12:37): FBX support hands on Rifle / Shotvolver / BrutalRevolver; Sniper wrist hold solved, NOT ported (flag). RIG ONLY, NOT HEADSET-CONFIRMED

Worktree `/home/claude/lane_b_b5` (branch `b5-hands`, pushed to `lane-b-1.99x`). One method: the gun hands and guns are batch 4's, unchanged;
only the support hand is new, and it is placed on the PORTED gun (nothing moves the gun or the gun hand).

## 1. Done (measured; rig only, not headset-confirmed)
- **`port/support_gun.py <Class> <A|B> <out.json>`**: the FBX support pose (`fbx_b1_L.md3`: A = RQFS A the pistol cup, B = RQFS B the open palm under)
  at 1.92's SupportPoint (parsed from the 1.92 pack's handtable) moved with the gun (`ported_<Class>.json` R, t), lowered in 1 mm steps
  until clear (pen <= 0.5 cm, lane_c TOL). The contact under a long polygon is found on the sampled surface (the Rifle mesh has no vertex there).
  **`port_gun.py <Class> x --support <sup.json>`** writes the handtable row (hook / rot / point) and the hands.zs label. Data: `port/fits/b5/`.
- **Rifle** (row 18, ~15 min): RQFS B under the M203 tube; the MP40's solved palm-under rotation carried by R_rifle R_mp40^T. Contact (32.12, 4.71, -2.68) cm,
  lowered 0.2 cm: pen 0.45, palm 0.14 cm from the tube. Hook (-3.232, 11.358, 6.741), rot (-7.927, 2.302, 10.732) (= the MP40's: same r5 aim).
  The purist rifle keeps its Ermac handguard grip (label condition excludes PuristRifle; see open).
- **Revolver, Revolver2, BrutalRevolver** (shared row 17, ~20 min): RQFS A, the BrutalPistol's cup (row 4, hook 0) carried from the pistol's 1.92
  SupportPoint to the Revolver's (rotation R_rev R_pistol^T = identity: same aim), lowered 1.4 cm until clear of BOTH revolvers and BOTH gun hands
  (`--also BrutalRevolver`): pen 0.50 (Revolver hand) / 0.39 (BrutalRevolver gun) / 0.48 (BrutalRevolver hand), gun 0.00. Hook (0.458, -2.521, -0.373), rot 0.
  The shared row alone was 0.60 into BrutalRevolver's hand before the joint solve.
- Sheet `/home/claude/lane_b_out/b5_hands.png` (checked by eye against 1.92): the Rifle's steadied hand is the FBX palm under the tube where 1.92's black
  glove was; both revolvers show the FBX cup under the gun hand where 1.92's glove cupped. BrutalRevolver has no 1.92 render.
- **Poses as data:** `poses/Rifle|Revolver|BrutalRevolver.json` now carry `support` (the solve + measurements; BrutalRevolver points at the shared Revolver
  solve). `rebake.py bake` reproduces all three gun-hand bakes exactly (0.0000 md3 units); the support is a hook on the unchanged fbx_b1_L frames (hook check 0.0000).
- **Gate** (QZD 17.3 rig, doom2 -> brutal22test6 -> BD_VoxelPack -> pack, `gate_gun.py`, exclusive lock, ini restored; logs `/home/claude/lane_b_b5run/g5`, `g5f`):
  - smoke and hand reloads re-run on the DELIVERY pack (`g5f`, after the rebase): identical results, 0 pack script errors.
    (gate_gun.py has no PuristRifle or Shot_Gun entry: those two were not smoked here.)
  - smoke on the test pack, 0 pack script errors (only BD_VoxelPack's voxeldef lines): Rifle held, 14 shots, DROP/EMPTY; Revolver 2 shots (held False = the
    probe's class-name match, as r4); Revolver2 held, 12 shots; BrutalRevolver held, 2 shots. Same as batch 4.
  - hand reloads: Rifle mag IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE; M203 latch > open > round in the breech > round home > shut: loaded;
    Revolver break chamber 0 loaded, 0.0 cm off the bore; BrutalRevolver speedloader loaded > flick 457 deg/s > DONE; per round loaded 6, 0.0 cm off the bore.
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r8-hands5.pk3` (`python3 build.py 1.99x-lb-r8-hands5`, rebased on c32650c incl. Shot_Gun),
  sha256 3021ae33f5a317c9a8df2dc6c75347dd35dfb208f93cd80777536b1d520fbee7.

## 2. Not done / flagged
- **Sniper (Ruger/XM21): the rifle-wrist hold is SOLVED but NOT ported: owner's call.** (`port/sniper_wrist.py`, ~35 min, mostly solver time)
  - Measured wrist: ~3.3 cm wide; its underside drops from z -1.7 (x -1.8) to -5.5 (x -5.8) behind the trigger; the Rifle's pistol grip runs to z -16.
  - Start = the Rifle's hold pitched about the trigger; scan 0/20/40/60/-20 deg: 40 best (pen 0.38, M/R/P 1.22/0.23/0.02 rigid).
    Rigid re-seat: pen 0.18, index pad 0.03, palm 0.30, web 0.29. Curls (index + M/R/P): **pen 0.31, index pad 0.00 on the trigger, M/R/P 0.20/0.20/0.13,
    thumb 0.06 (over the wrist), palm 0.30**, squeeze 0.60 cm travel. Data: `fits/st2_Sniper.npy`, `fits/curl3_Sniper.json`.
  - Why not ported: the hand is **39.5 deg** off the approved pistol hand (38 deg pitch; Rifle 8.9, Revolver 7.4, BrutalRevolver 11.7) and the gun
    would drop 15.6 cm (shift -2.92, 2.43, -15.59). port_gun keeps the pistol's aim, so the drawn hand would sit ~38 deg off the real controller hand;
    keeping the hand on the controller instead tilts the barrel ~38 deg off the aim. Either is a feel change the owner decides. Port is one command once decided
    (write `fits/Sniper.json` as Rifle.json: `shift` from curl3, sprite RQFN, squeeze X21F/P21F A-C, support `move` frame 4; then `bake_gun.py`, `port_gun.py`).
  - Scope: `port/scope_eye.py` puts the left eye 8 cm behind the eyepiece (target from scope.zs, corrected from the probe's logged eye). On the UNMOVED
    Sniper (test pack): REAL on (skinOn 1, cam 1, fov 4.62) at 11.2 cm eye relief after 2 iterations. Not re-run on a ported Sniper (none).
- **Purist rifle support:** still Ermac's handguard grip. The same solve on Rifle.md3 alone gave palm 1.59 cm off the handguard after lowering 1.6 cm: not good enough to ship.
- The revolver cup is lowered 1.4 cm to clear both gun hands; it supports the gun HAND (as 1.92 and the pistol), 2.4 cm from the gun at the palm.
# r8 Unmaker reload lane (2026-10-27, branch `unmaker` off `lane-b-1.99x`). RIG ONLY, NOT HEADSET-CONFIRMED

Owner: "the unmaker better reload in bd22 like how it does in rs vr vanilla+". Coordinator, mid-lane: the skull must be
VISIBLE in the off hand while carried, never hidden inside the fist (his RS VR Reload does it right).

## What was wrong (measured)
- The skull WAS drawn on the off hand (probe: layer 2201, caller RSQ_Hands, sprite RQWP, every tic of CARRY), but
  inside Ermac's closed frame-3 fist (RsrHold): the skull's box lies wholly inside the fist's box (F -7..5, L -1..8,
  U -8..-2 vs fist F -13..6, L -4..10, U -12..2). On the rig no frame from any camera showed it (before or after the
  Plus numbers alone). The r6 "mid-air" note was the pouch reach: the hand was at the pouch, not at the skull.
- The seat/travel came from a gen run on the `magazine` surface only: Well 0.86 cm off, Mouth 4.61 vs Plus 5.47.

## What changed (`src/zscript/rsr/rsr_guns.bd.zs` row 13, `vreload.zs` HoldState, `MODELDEF.rsr` dropped skull)
- Transform Plus -> BD22 (tools/handfit/unmaker/plus_row.py): Plus `unmaker_wm.md3` (same bytes in RS_VR_Weapons_Plus.pk3
  and Depot sets/plus_0.7) = BD22 `Unmaker_rsr.md3` frame 0 + (56.5156, -0.0156, 2.5469) md3 units; scale fit 1.000000,
  position match max 0.0000 over 11541 verts. In the controller frame (both MODELDEF placements, rgeo chain):
  d = (4.017, -0.025, 1.035) cm F L U, spread 0.0000.
- Plus row 1 (WM_VP_Unmaker) through d: Well (11.026, 0.794, 6.467), Axis (0,0,-1), Mouth 5.47, MagLen 5.41,
  MagCentre (10.481, -0.144, 9.345). Checked: BD22's own skull surfaces seated = Plus seat + d, max 0.0000 cm.
- Carry: Plus's carry put the skull in the same buried frame-3 fist (9% of its surface inside the hand mesh, 197 hand
  vertices inside it). RS VR Reload (E:\DOOMWork\RS_VR_Reload, staged read-only) holds the Unmaker skull on its `bfg`
  hand set (wm_ha_bfg_off_mag: ofs -0.34 0.68 -0.85, yaw -75, pitch 15), a loose skull re-origined on its centroid
  (RS_VR_Weapons WMCARD.11_bfg magcenter -16.83 -0.13 6.61). Our in-hand layer cannot turn the part, so the match is:
  Ermac's open BFG pod hold (ammo_hand frame 6, `RsrHoldPod`, as the Nuker/Hellish), skull fitted to his pod's contact
  patch (skull_hold.py: frames 0-8 scored; frame 6 best: gap 0.98 cm, 4% buried), then moved +2 F +2 L -2 U
  (visible.py) so it touches the fingers (nearest 0.26 cm, 2 hand verts in it, 0% buried) and 83 / 96 / 100% of it is
  seen from three head positions. TopInHand (3.464, 8.784, -11.859), HandHook (7.990, -18.326, 7.562).
- Dropped skull: Plus's world offset carried through the same translation (Offset -13.7636 0.0490, ZOffset -2.7949).
- The 200-round magazine (counters.zs REAL[], RSQ_Mag_Unmaker) is untouched.

## Shown on the rig (QZD 17.3, doom2 -> brutal22test6 -> BD_VoxelPack -> pack + probe)
- `rig_reload.py`: magazine emptied, trigger on empty does nothing, by-hand reload with the off-hand driver (mags.at):
  EMPTY > DROP > EMPTY > CARRY > INSERT > SEATED > DONE, mag 0 -> 200 from the pouch, fires again. No script errors.
- Frames: `/home/claude/lane_b_out/unmaker_reload.png` (before: buried; now: skull in the open hand from the head and
  close up, at the well, seated, firing).
- Sweep (`sweep.py`): Unmaker, Devastator, Plasma_Gun, RailGun, Flamethrower2, IncendiaryLauncher, NukeLauncher,
  Minigun, Machinegun given, selected, fired, alt-fired, reloaded on the final build: no script error or VM abort,
  only BD22's own DeathSphereHealth lines; each reached its reload phases. Coarse: the probe's selection line comes
  every 35 tics, so the Unmaker's first window still reads the start Rifle, and RailGun / IncendiaryLauncher print no
  magazine-shot line. Identical to the same sweep before the hold change.

## Not done / open
- Side-by-side with Vanilla Plus on the rig: RS_VR_Weapons_Plus.pk3 is a DoomXR pack (PlacementCVars, FollowMainHand),
  not runnable on QZD 17.3. The Depot's RSQ_plus.pk3 loads on the rig with no errors and holds the Unmaker, but its
  reload never started from `rig_plus.py` (+reload gave no RSR_Start and no "refused" line); not chased.
- The skull keeps its seated orientation in the hand (RS VR Reload turns it yaw -75 / pitch 15): turning it needs a
  rotation on the HANDMAG layer in Place(), a code change the owner may want; not built.
- HUD still shows SoulAmmo (pouch + lent), not the magazine (r6 note).
- pk3 `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r8-unmaker.pk3`, sha256
  8a52ba6f573bc3e3bf68f2f52262d878aef7e93dd251c022b51b19166a285119 (build.py from this branch, rebased on ceddb85).
  Re-run on it after the rebase: phases as above, RELOAD magazine 0 -> 200, pouch 250 -> 50, fires again
  (200 -> 94 in 80 tics); script errors only BD_VoxelPack's voxeldef lines.

# r9 port lane (2026-10-27, box 14:00-15:30, branch `port9` pushed to `lane-b-1.99x`): fit-farm guns + Sniper pistol-style. RIG ONLY, NOT HEADSET-CONFIRMED

Worktree `/home/claude/lane_b_p9`. One method (wrist pinned, the GUN moves to the hand) with `port/port_gun.py`, via `heavies/port_hv.py`
for the heavies. Inputs: the owner's PC fit farm (batch hv1), copied unchanged to `tools/handfit/port/fits/farm_hv1/<Gun>/`.
The heavies lane's commits did not cherry-pick onto lane-b (generated files conflicted), so only its tools/fits/poses were taken
and GrenadeLauncher was re-ported by the tool on the current base.

## 1. Done (measured; rig only, not headset-confirmed)
| gun (row) | source | gun hand | support (FBX RQFS B palm-under, support_gun.py) | moved |
|---|---|---|---|---|
| GrenadeLauncher (8) | heavies fit (farm's gun hand is the same to 1/64 md3 unit) | pad 0.39, pen 0.67, squeeze 0.60 | pen 0.48, palm 1.50 cm under (= support_gun.py's result; the farm's lay ~10 cm off 1.92's SupportPoint) | 6 MODELDEF blocks incl. the off-hand round, Pivot + rows, rsb case 2 Hinge/Axis/PushRef/Offset/Bore + hold rows re-expressed, muzzle |
| Rocket_Launcher (19) | farm, index re-solved | pad 0.48 (was 2.05), pen 0.88 (FLAG > 0.5) | pen 0.49, palm 0.10 (farm 2.43) | 6 blocks, Pivot + 11 rows, rsr case 9, muzzle |
| RailGun (16) | farm | pad 0.23, pen 0.58 | pen 0.45, palm 1.10 under (farm 1.76) | 7 blocks, Pivot + 6 rows, rsr case 6, muzzle, scope row 1 |
| Plasma_Gun (15) | farm (MP40 start) | pad 0.57, pen 0.55 | pen 0.50, palm 0.20 (farm 1.57) | 7 blocks, Pivot + 8 rows, rsr case 7, muzzle |
| MiniGun (13) | farm | pad 0.28, pen 0.41 | FLAG: no FBX pose clears the side handle (pen 2.12 after 3 cm); Ermac's handle grip (pose E) moved with the gun | 4 blocks incl. Minigun_rsr.md3, Pivot + 7 rows (barrels left out), rsr case 17, muzzle |
| Sniper (22) | owner: pistol-style. Rifle's st2 hold, translated to the Ruger trigger (`port/sniper_pistol.py`), curls | pad 0.00, squeeze 0.60, M/R/P 0.20/0.65/1.42; FLAG thumb + palm heel 1.61 cm into the stock wrist (x -8.4) | pen 0.50, palm 0.39 | 6 rsr blocks, Pivot 22, rsr case 8, muzzle, scope row 2 |
(pad = index pad to the trigger face, pen = max penetration, cm.) Poses as data: `tools/handfit/poses/<Class>.json` for all six (FK fit <= 2e-5 cm).

Tool fixes (all in the repo):
- `port_hv.py`: the MiniGun and M32 reload drawings (`Minigun_rsr.md3`, `m32_rsr.md3`) were not in the registry: they would not have moved.
- `port_hv.py`: the M79 break-open now follows batch 4's rule. The heavies commit moved Offset(i) but not the off-hand round block,
  leaving the round ~11 cm off the hand; now RSQ_Hands RBGP H moves, Hand0-2/HandT are re-expressed, and Bore turns.
- `port_gun.py rsr()`: WellHook / HandleHook keep their row length (the Sniper's rows are 1/scale = 0.0954; it wrote unit vectors).
  Every earlier row is unit: unchanged.
- New: `heavies/sup_hv.py`, `heavies/gate_hv.py` (port tools with the heavies registry), `port/sniper_pistol.py`;
  `scope_eye.py` takes the gun; `unmaker/rig_reload.py` takes ROW/GUN/AMMO.

## 2. Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, exclusive lock, ini restored)
- Smoke (give/select/steady/fire/alt/reload/fire): 0 pack script errors, 0 VM aborts; all six held.
- Hand reloads on the moved guns: RailGun, Plasma_Gun, Rocket_Launcher, Sniper magazine IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE;
  MiniGun (fire to empty) EMPTY>CARRY>INSERT>SEATED>DONE, box 0 -> 200, fires again; M79 break: open, round in 0.0 cm off the bore, loaded, flick shut.
- 37-class sweep on r9 vs r7: 37/37 SAME, no pack script error, no VM abort.
- Scopes: the probe's state is REAL on both moved scopes with the eye 8 cm behind the ocular (Sniper: skinOn 1, cam 1, fov 7.17, eye 1.38 cm
  from target; RailGun: skinOn 1, cam 1, fov 8.17, eye 0.32 cm). **The lens picture is NOT shown:** on this rig pose the rendered camera
  sits several cm above the probe's eye, so the frames see the ocular from above. Needs r6-scope's rig pose (lane_b_scope_rig) to show it.
- Pack **`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r9.pk3`** (`python3 build.py 1.99x-lb-r9` at pushed head `558494c`),
  sha256 `1bbab982784f3aa46e2a7834b5cbc5ffcd0f3e2f4987b4e27b87f9f948328d1c`. Spot checks on THIS pack:
  - Hands sheet `/home/claude/lane_b_out/r9_hands.png` (six guns, side view, steadied and firing, 0 script errors in the 12 runs):
    FBX gun hand on the grip on all six; FBX palm-under on M79, RPG, RailGun, Plasma, Sniper; MiniGun's handle grip is on the far side (hidden).
  - Unmaker hand reload: EMPTY > CARRY > INSERT > SEATED > DONE, 200 from the pouch (250 -> 50), fires again, no script error.
    **Skull visibility NOT re-shown on r9** (the rig's default head view never sees the off hand, also with a clear carry pose);
    vreload.zs, rsr row 13 and the Unmaker MODELDEF blocks are byte-identical to r8 (`594098c`), where it was shown.
  - BrutalRevolver speedloader (rsb case 10, `rsb_revolver_feed 0`): OPEN > CARRY > INSERT (0.0 cm off the bore) > loaded > EMPTYLOADER >
    flick 457 deg/s > CLOSING > DONE. Note: `gate_gun.py hands brkBrutalRevolver:...:1` is the PER-ROUND feed (case 11), not the
    speedloader; batch 5's "speedloader" line came from that per-round run (loaded 6). Per round on r9 is identical to batch 5.
  - Sniper and RailGun scopes: probe REAL, lens picture not shown (see above).
  - Logs: `/home/claude/lane_b_p9run/{gate,gate2,sweep,spot,spot2}`.

## 4. BD22 guns with / without FBX hands after r9
- **FBX gun hand (14 rows):** BrutalPistol, BrutalSMG, Flamethrower2, MP40, Rifle (+ PuristRifle), Revolver, Revolver2, BrutalRevolver,
  AssaultShotgun, Shot_Gun, GrenadeLauncher, Rocket_Launcher, RailGun, Plasma_Gun, MiniGun, Sniper.
  FBX support on all of them except MiniGun (Ermac's handle grip, flag) and PuristRifle (Ermac's handguard grip).
- **No FBX hand:** SSG, MG42, Machinegun, IncendiaryLauncher, FlameCannon, Unmaker, Devastator, NukeLauncher, HellishMissileLauncher,
  BIG_FUCKING_GUN, BFG10k; melee/thrown: BrutalAxe, Chain_saw, DSweap, HandGrenades. Dual-wield classes use the dualhands labels of
  their rows; not shown on the rig (the sweep never holds them, as in r7).

## 3. Not done / flagged
- **IncendiaryLauncher not ported:** farm fit has the index 5.22 cm from the trigger, pen 1.30, web 1.26. Needs a farm re-fit (better start).
  Its support placement is ready (`fits/r9/sup_IncendiaryLauncher.json`, pen 0.43), and port_hv now moves `m32_rsr.md3`.
- MG42 and Machinegun: not in the farm batch's results (status "final": false). Machinegun's M203-style launcher tables need ToGun/FromGun (heavies note).
- MiniGun support is Ermac's glove (no FBX handle-grip pose exists): needs one fitted on the farm.
- Rocket_Launcher gun-hand penetration 0.88 cm (> 0.5 tolerance); its support palm turns up under the tube on the side view: owner look.
- Sniper: the thumb sinks 1.61 cm into the stock wrist (the owner's grip choice); ring/pinky 0.65/1.42 cm short of the wood.
- Scope lens pictures not shown (above).

# r10 port lane (2026-10-27, branch `port10` pushed to `lane-b-1.99x`): fit-farm r2/r3 guns. RIG ONLY, NOT HEADSET-CONFIRMED

Worktree `/home/claude/lane_b_p10`, run dir `/home/claude/lane_b_p10run`. Same one method (wrist pinned, the GUN moves to the hand) via
`heavies/port_hv.py`. Inputs: `/home/claude/fitfarm_results` (PICKS_r2.md, PICKS_r3.md), copied unchanged to `tools/handfit/port/fits/farm_r2/<Gun>/`.

## 1. Done (measured; rig only, not headset-confirmed)
| gun (row) | farm fit | gun hand (trigger pose) | support (FBX RQFS B palm-under) | moved |
|---|---|---|---|---|
| MG42 (11) | MG42_fromMinigun | pad 0.27, pen 0.40, palm 0.09 | farm placement: pen 0.44, palm 1.38 (support_gun.py: 0.45 / 1.37) | 4 blocks incl. HitlersBuzzsaw_rsr.md3, Pivot + 4 rows, rsr case 10, casing, muzzle added (barrel tip) |
| Machinegun (27) | Machinegun_fromMP40 | pad 0.22, pen 0.35, palm 0.30 | farm placement: pen 0.44, palm 0.70 (support_gun.py identical) | 5 blocks incl. Machinegun_rsr.md3 and MODELDEF.rsm (tube, no-tube twins), rsr case 18, casing, muzzle added on the M249 barrel (surface 5), **launcher (RSM gun 2)**: FwdHook(2), ToGun/DirToGun/FromGun gun-2 branch, seated round block RQ3P B re-placed (residual 0.0000 cm). No gunmoves rows exist for it. |
| NukeLauncher (14) | NukeLauncher_fromMinigun | pad 0.43, pen 0.60, palm 0.29 | support_gun.py: pen 0.45, palm 1.30 (farm had 0.47 / 1.87) | 4 blocks incl. Nuker_rsr.md3, Pivot + 4 rows, rsr case 15, muzzle added |
| BFG10k (2) | BFG10k_fromMinigun (r3, landed 15:35) | pad 0.00, pen 0.58, palm 0.49 | farm placement: pen 0.44, palm 1.45 (support_gun.py: 0.49 / 1.11) | 4 blocks (2 bd + 2 purist), Pivot + 5 rows, muzzle added; no rsr/rsb case |
Hand sprites: RQV1 MG42, RQV2 Machinegun, RQV9 NukeLauncher, RQVA BFG10k (free in the pack, brutal22test6, BD_VoxelPack). Poses as data:
`poses/{MG42,Machinegun,NukeLauncher,BFG10k}.json` (FK fit <= 6e-10 cm). Per-gun port logs and support jsons: `port/fits/r10/`.

Tool changes: `port_hv.py`: MG42 / Machinegun `*_rsr.md3` reload drawings were not moved (same bug as the MiniGun's in r9); NukeLauncher,
BFG10k registered; `m203mg()` moves the Machinegun's launcher. `gate_gun.py`: job `m203mg` (launcher reload on the moved Machinegun).
Finding: the Depot `m203.py GUN=mg` aims the round at bore U -1.517, 5 cm above the table's AxisU(2) -6.517; it scraped in at ENTER_SIDE 5
on the unmoved gun (r9: loaded) and fails on the moved one (round never enters). With the table's bore line the moved gun loads; the gate uses that.

## 2. Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, exclusive lock, ini restored, frame dumps deleted)
- Smoke (test build of the same tree, 3 guns): 0 pack script errors, 0 VM aborts, all held.
- Hand reloads: MG42 and Machinegun magazines IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE. Machinegun launcher (moved):
  latch > took the tube > open > took a round > round in the breech > round home > shut: loaded, no script error.
  **NukeLauncher hand reload NOT shown:** the rig driver (unmaker/rig_reload.py ROW=15, mags.py 15) reaches no rsr phase on r10 AND on r9 (unmoved): a driver/test gap, not a port change. Needs a Nuke-specific driver.
- Pack **`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r10.pk3`** (`python3 build.py 1.99x-lb-r10` at pushed head `6115102`),
  sha256 `6acd9cad6fe8914deb745a3056e0d4c77b8a043a0048f1f5c4e6f928def9962f`.
- 37-class sweep r10 vs r9: 0 script errors, 0 VM aborts; 35 SAME, 2 DIFF on shot count only (BrutalSMG 9 vs 10, untouched by r10:
  run-to-run timing; MG42 16 vs 18); held and reload phases identical on all 37. Log `/home/claude/lane_b_p10run/sweep/`.
- Sheet `/home/claude/lane_b_out/r10_hands.png` (r10 pack; 12 runs, 0 script errors): FBX gun hand on the grip and the FBX palm under the gun on
  all four, side steady / side fire / eye fire. Owner look: MG42's support palm sits beside the barrel jacket (1.92 SupportPoint 30 cm out);
  the blocky brown arm in the MG42/Machinegun fire frames is a world sprite in front of the rig camera, not the hands.

## 3. Pending / flagged
- Not ported (no fit landed by 16:05): SSG, BIG_FUCKING_GUN (r2b still running), Devastator (needs a re-run from a finished hold),
  IncendiaryLauncher (r1 fit pad 5.22: needs a re-fit). NukeLauncher hand reload not shown (above). Gun-hand pen 0.58-0.60 on BFG10k / Nuke (> 0.5).

## 4. BD22 guns with / without FBX hands after r10
- **FBX gun hand:** BrutalPistol, BrutalSMG, Flamethrower2, MP40, Rifle (+ PuristRifle), Revolver, Revolver2, BrutalRevolver, AssaultShotgun,
  Shot_Gun, GrenadeLauncher, Rocket_Launcher, RailGun, Plasma_Gun, MiniGun, Sniper, **MG42, Machinegun, NukeLauncher, BFG10k**.
  FBX support on all except MiniGun (Ermac's handle grip) and PuristRifle (Ermac's handguard grip).
- **No FBX hand:** SSG, IncendiaryLauncher, FlameCannon, Unmaker, Devastator, HellishMissileLauncher, BIG_FUCKING_GUN; melee/thrown:
  BrutalAxe, Chain_saw, DSweap, HandGrenades.

# Lane rev-unmaker (2026-10-27, branch `lane-rev-unmaker` off `lane-b-1.99x` a4b0eb7). RIG ONLY, NOT HEADSET-CONFIRMED

Owner r3 item 20 (two revolvers only), the Revolver's own ammo (owner, 19:06 cap correction), the Unmaker reload
"like RS VR Vanilla+". No hand placement rows touched (one class-mapping line removed from handtable.zs: `Revolver2 -> 17`).

## 1. Done (measured)
- **Revolver2 is gone.** Removed: `actors/Weapons/Revolver2.dec`, `DECORATE.rsqrev` (its include + `RSQ_ShotvolverSpawner`),
  KEYCONF slot-2 line, the menu option "Shotvolver Swap for Revolver", cvar `rsq_slug_replaces_shotvolver`, the
  RevolverSpawner swap in `roster.zs`; class lookups in handtable / casings / casemodels / melee / rsb_guns Index().
  rsb rows 8/9 retired (Cls 'None', numbers kept so BrutalRevolver keeps 10/11). README, README.txt, port_gun.py,
  gate_gun.py lists. The Shotvolver keeps its own slug alt fire (`rsa_rev_magnum`).
- **RevolverRounds (the Moonlight's reserve):** 6 a pickup. Cap **36 with one Revolver, 72 once a second Revolver is
  picked up** (owner 19:06). How: BrutalRevolver is `+INVENTORY.ALWAYSPICKUP`; a BrutalRevolver world pickup destroyed
  within reach of a player who already owned one (the dual.zs rule) gives `RSQ_MoonPair`; `RSQ_Roster.WorldTick` sets the
  player's RevolverRounds MaxAmount to 36 or 72 every tic. The backpack does not raise it (BackpackMaxAmount 36). There is
  NO off-hand Moonlight copy (RSQ_DualTable has none), so "two" means two picked up, not dual-wielded.
- **Pickup art:** `tools/moonammo/make_pickup.py` (numbers it prints): the pack's `shell_12ga.md3`, its mouth (`inner`, 36 tris)
  deleted with the Depot's `md3_carve_disc.py --delete`, hull cut to 62% so case + nose = the Moonlight round (rev.md3 f20,
  surfaces 4-9 PCA: 3.542 x r 0.599 mesh units = 4.88 x r 0.82 cm), a round nose (12 segments = the hull's, 6 rings,
  length = case radius), uniform scale 0.05929, six in a ring at the chamber radius (1.9 cm = 1.380 u). Colours from
  WPN-REV.png: brass (179,129,5) = the Moonlight round's own texels; nose blue (23,103,169) = the sheet's commonest
  saturated hue. World size: ring diameter = BD22's SHELA0 (16 px x 0.9 = 14.4 map units) -> MODELDEF Scale 3.5348.
  2D sprite RVRDA0.png = a render of the mesh. Files: `models/rsq/moonammo/*`, `MODELDEF.rsqmoonammo`, `sprites/RVRDA0.png`.
- **Map spawns (rule):** one RevolverRounds beside 1 in 4 of the map's own bullet pickups (the Clip2 family: Doom's Clip and
  ClipBox, which BD22 spawns as Clip2 / ClipBox2 / EasyClip2) present at tic 0, not dropped, not owned; 14 units away
  (on the same spot if that is blocked). It replaces nothing. Chosen because the Revolver is a slot-2 pistol-class gun and
  bullets are the commonest small ammo; the Shotvolver's shells were left alone.
- **Unmaker reload:** no code change. lane-b already carries r8's port, which is the same source and method as ModelSwapper
  round 5 (`port_plus_rows.py`): MS row 84 (brt_Unmaker, the same bd/Unmaker mesh) Well (11.025, 0.794, 6.466), Axis
  (0,0,-1), Mouth 5.47, MagLen 5.41, MagCentre (10.481,-0.144,9.345) = our rsr row 13. Re-shown below on this pack.

## 2. Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, exclusive /home/claude/rig.lock, ini restored)
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm.pk3` (build.py at `7ab88d0`; src unchanged after),
  sha256 `1f6d7d9d0b96cbd662432348e16b91aa6505561a2825fc17cc97a6c68f37315d`. Every run: `script errors (not BD_VoxelPack voxeldef): none`;
  the only `Script error` lines are BD_VoxelPack's own `voxeldef.txt` lines 66/72/77/892.
- `tools/moonammo/rig_rev.py` (logs in scratchpad `out/final/build/logs`):
  - roster: after `idkfa` the player holds `BrutalRevolver` and `REVOLVER` (the Shotvolver); `give Revolver2` ->
    `Unknown item "Revolver2"`; `summon Revolver2` -> `Unknown actor or visual thinker 'Revolver2'`; the old cvar is unset.
  - cap: one Revolver `RevolverRounds #51 (36/36)` after giving 100; second Revolver walked onto (left stick) ->
    `RSQ moon t115: second Revolver picked up`, `RSQ moon t116: RevolverRounds cap 36 -> 72 (two Revolvers), holding 36`;
    100 more -> `(72/72)`; backpack + 100 more -> still `(72/72)`.
  - spawn: `MAP07: 6 map-placed bullet pickups (Clip2 family), RevolverRounds put beside 2` (also MAP01 1-2 of 2,
    MAP03 1 of 2, MAP11 1 of 6 in that run; random per run).
  - frame: `/home/claude/lane_b_out/revunm_pickup.png` (the six-round pickup on MAP07 next to a bullet box, and RVRDA0).
- gate_gun.py smoke Revolver / BrutalRevolver: 0 errors, 0 VM aborts, 2 shots each (Revolver "held false" = same on r10).
  hands: Shotvolver break-open (rsb 3) and Moonlight (rsb 10) open > carry > insert 0.0 cm off the bore > loaded;
  Moonlight flick shut 457 deg/s.
- Unmaker (`tools/handfit/unmaker/rig_reload.py`, CARRYP 20 25 -5, head 0 1.6 0 -35 15 0): IDLE>EMPTY>DROP>EMPTY>CARRY>
  INSERT>SEATED>DONE>IDLE, `RELOAD magazine 0 -> 200, 200 from the pouch, pouch 250 -> 50`, fires again, `ERRORS: none`.
  Frames `/home/claude/lane_b_out/revunm_unmaker_reload.png` and `revunm_unmaker_skull_zoom.png`: the skull is seen at the
  fingers while carried from this head pose.

## 3. Not done / open
- From a head pose that sees the BACK of the off hand (run 2: CARRYP 0 20 15, head yaw 25) the skull is hidden behind the
  hand. RS VR Reload turns the skull in the hand (yaw -75, pitch 15); ours cannot turn the HANDMAG layer without a code
  change in vreload.zs Place() (r8's open item). Not built: owner's call.
- Owner questions: backpack rule for RevolverRounds (doubles like BD22's ammo, i.e. 72 / 144, or none as built);
  where the Revolver itself spawns on maps (nowhere today, so a second one only comes from give/summon or a future spawn);
  dual-wielding the Moonlight (README "Dual Revolvers, of course") is not built; spawn rate 1 in 4 is a first pick.
- The Shotvolver's own map spawn is BD22's (RevolverSpawner via the commented-out shotgun replacer: effectively none).

# Lane rev-unmaker, round 2 (owner's answers 19:40; branch `lane-rev-unmaker`). RIG ONLY, NOT HEADSET-CONFIRMED

## 1. Done (measured)
- **Backpack:** does not raise the Moonlight cap (kept as built; owner 1).
- **Menu "Moonlight Revolver"** (BD22 VR WEAPONS menu; server int `rsq_moonlight`): Off / 50% Replaces Shotvolver / Replaces
  Shotvolver. **Default: 50%** -- both revolvers stay findable wherever BD22 places a Shotvolver, and the Moonlight's rounds
  are on (they need the option not Off). roster.zs CheckReplacement swaps BD22's `RevolverSpawner` (the Shotvolver's only
  world pickup) for `BrutalRevolver` (the gun + its 6 rounds); the `Revolver` class is never replaced (give/idkfa, r4).
  The Moonlight's floor pickup is now its own mesh (rev.md3 frame 0 on its side, MODELDEF.rsqmoonammo `RVMP A`; size from
  BD22's REVPA0 34 px x 0.9; `RVMPA0.png` = REVPA0 for 2D).
- **RevolverRounds map spawns only when the option is not Off** (owner 3).
- **Dual Moonlight** (owner 5): `RSQ_Off_BrutalRevolver` (end of BrutalRevolver.dec, by hand on DECORATE.rsqdual's pattern;
  gen_dual.py is not in this repo), cylinder `BrutalRevolverCylinderOff`, off-trigger one-shot lock `RSQ_SemiLockOff`
  (roster.zs), flick reload = the mesh's own reload animation. dualtable.zs index 10 (`BrutalRevolver` pickup), dual.zs
  MAXGUNS 11, dualhands.zs DFbxTrgBru/DFbxSqzBru, MODELDEF.rsqmoondual (gun block COPIED from MODELDEF.rsqmoon's first
  BrutalRevolver block -- re-copy it if that placement is refitted -- and the existing FBX hand). Dual Options: "Revolver
  (Moonlight)" (`rsq_dual_moonlight`, on) and "Revolver" renamed "Shotvolver". **Cap rule: 72 while the off-hand copy is
  held, 36 otherwise** (RSQ_MoonPair removed; the copy is what "two held" means).
- **Unmaker skull turned** (owner 4): RS VR Reload CVARINFO (parsed) `wm_ha_bfg_off_mag_yaw -75.0`, `_pitch 15.0`,
  `_roll 0.0`, applied as GZDoom angles (yaw + left, pitch + nose down) in the off controller frame about the skull's centre,
  then re-seated -4 F +4 L +6 U cm on Ermac's pod hold (`tools/handfit/unmaker/skull_turn.py`, search: touch <= 0.6 cm, <= 40
  hand verts inside). Offline (hudrender, 4 head positions): before 83/96/100/32% of the skull seen, after 100/100/100/93%;
  hand verts inside 2 -> 17, buried 0.0 -> 0.2%, nearest hand 0.08 cm. Code: vreload `RSR.HandRot` (75, -15, 0) and
  `RSR.HandAxis` (-0.0670, 0.2500, -0.9659) for row 13 only; rsr row 13 HandHook (31.144, -13.249, 43.532), TopInHand
  (-0.231, 12.300, -5.902). Offline sheet `/home/claude/lane_b_out/revunm_skull_turn_offline.png`.

## 2. Rig evidence (pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm2.pk3`, build.py at `0e0df42`,
sha256 `4fbaedc4ba78a584ce9e8be8021333fbce2792033b047beb18eb60428710102b`; load order doom2 > brutal22test6 > BD_VoxelPack > pack,
exclusive /home/claude/rig.lock, ini restored). Every run `script errors (not BD_VoxelPack voxeldef): none`; the only
`Script error` lines are BD_VoxelPack's voxeldef.txt 66/72/77/892.
- modes (20 RevolverSpawner summoned on MAP01 each): `rsq_moonlight 0: in the world Shotvolver 20, Moonlight 0`;
  `rsq_moonlight 1: ... Shotvolver 9, Moonlight 11`; `rsq_moonlight 2: ... Shotvolver 0, Moonlight 20`.
- spawn: Off -> `RevolverRounds put beside 0` on MAP01/03/07/11 (2/2/6/6 bullet pickups); 50% -> beside 2, 0, 0, 2.
- roster: idkfa holds `BrutalRevolver` + `REVOLVER`; Revolver2 unknown to give and summon.
- cap: `RevolverRounds (36/36)` with one; second walked onto -> `cap 36 -> 72 (two Moonlights)`, `RSQ_Off_BrutalRevolver`,
  `(72/72)`; backpack + 100 -> `(72/72)`.
- dual (`/home/claude/lane_b_out/revunm2_dual_moonlight.png`): both held; main fired (empty -> its reload, then 6 -> 5),
  off fired twice (`BrutalRevolverCylinderOff (4/6)`); off flick -> off cylinder 6/6, reserve 6 -> 4; main flick -> main
  cylinder 6/6, reserve 4 -> 3. The probe's `B22 SHOT 434` during the off flick is its own count, not a round spent (the
  cylinders say so).
- Unmaker reload on this pack, poses A and C: EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE, `ERRORS: none`: the turned skull
  still goes in. Before/after, same head poses: `/home/claude/lane_b_out/revunm2_unmaker_skull_before_after.png`.
- Moonlight floor pickup: `/home/claude/lane_b_out/revunm2_moonlight_world_pickup.png`; rounds: `revunm2_pickup_frame.png`.

## 3. Not done / open
- In stock BD22 the Shotvolver hardly reaches a Doom 2 map: RevolverSpawner comes only from ShotgunSpawnerReplacer with a
  map-set arg (its random branch is commented out, BD_ShotgunSpawner's menu line too) and from NewGunsSpawner (backpack
  extras option). So the Moonlight option rarely puts a Moonlight on a stock map. Owner's call whether the Moonlight should
  also take some other spawn (e.g. a share of the pistol's / shotgun's).
- Head pose B (left hand crossed to the right of the face, the back of the hand toward the eyes) hides the skull before
  and after; poses A and C (hand ahead / hand to the left) show it, bigger and turned after.
- The off-hand Moonlight copies the gun block by hand (MODELDEF.rsqmoondual): a refit of MODELDEF.rsqmoon's first block needs
  the copy updated. dualtable.zs and DECORATE copy are hand-made (no gen_dual.py here).
- Dual Moonlight hands use the existing FBX hand (RQFL); not re-fitted for the off hand. Default 50% is my pick.

# Lane rev-unmaker, round 3 (owner 20:15; branch `lane-rev-unmaker`). RIG ONLY, NOT HEADSET-CONFIRMED

## 1. Done
- **Default stays 50%** (`rsq_moonlight = 1`).
- **"Can it not 50% drop from enemies that carry revolvers?": no BD22 enemy carries or drops a revolver.** Checked in
  brutal22test6.pk3 (read only, `python3 -I`), all 172 `actors/` files, 47 of them enemies (actors/Enemies/*):
  - no `DropItem` names Revolver / RevolverSpawner (every DropItem in actors/ was listed: health/armor bonuses, runes, CLIP1Drop,
    RifleDrop, Clip, Shells, ShotgunDrop, ChaingunDrop, SMGDrop, PistolDrop, GrenadeAmmo, spawners for SSG/ASG/RL/plasma/
    rifle/railgun, ...);
  - no A_SpawnItem / A_SpawnItemEx / A_DropItem of a revolver in any enemy file, and no "Revolver"/"Revolver/" sound or REVP
    sprite outside actors/Weapons/REVOLVER.dec and WeaponSpawners.dec.
  - The only revolver drops in BD22 are not enemies: `src/Options.acs:796-815` script "DropItems" (DEATH, i.e. the PLAYER's
    death, option bd_dropitems) drops the player's own guns from the list `src/ACSFunc.acs:353-384` ("Revolver" at :359);
    and `src/EviEnh.acs:163` spawns a RevolverSpawner on Eviternity MAP30 -- that one is a RevolverSpawner, so the Moonlight
    option already applies to it. Item stopped, nothing invented.
- **Unmaker skull 1.4x while carried, normal when inserted** (owner 3): MODELDEF.rsr `RSQ_Hands` (the off hand's HANDMAG
  layer only) Scale -1.4 1.4 1.4; RSR_GunParts (in the gun) and RSR_DroppedMag stay 1. The bigger skull keeps the RS VR
  Reload turn and is re-seated -6 F +6 L +6 U cm (skull_turn.py `SKULL_SCALE=1.4`): nearest hand 0.28 cm, 22 hand verts
  inside, 0.0% buried, seen 100/100/100/93% from the four heads; extent 17.4 x 11.5 x 8.4 cm (normal 12.4 x 8.2 x 6.0).
  rsr row 13 HandHook (21.277, -12.586, 44.350); TopInHand (-2.231, 14.300, -5.902) = the NORMAL skull's top about the same
  centre, so the insert check uses the normal size.

## 2. Rig evidence (pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm3.pk3`, build.py at `9e1d4f0`,
sha256 `08d2ed3414e88f5812938dcbd7c331a5939e52b46ee4aed3689242df416ebb8b`; doom2 > brutal22test6 > BD_VoxelPack > pack, lock, ini restored)
- Every run `script errors (not BD_VoxelPack voxeldef): none` / `ERRORS: none`; only BD_VoxelPack's voxeldef 66/72/77/892.
- Unmaker poses A, C and the seated run: EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE, `RELOAD magazine 0 -> 200, 200 from the
  pouch, pouch 250 -> 50`. Sheets: `revunm3_unmaker_skull_carried_vs_seated.png` (r2 1.0x vs r3 1.4x carried, same poses),
  `revunm3_unmaker_carried_then_seated_same_run.png` (one run, one head pose: carried 1.4x, then seated 1.0x with the off hand
  moved away).
- Moonlight modes re-run on this pack: 0 -> Shotvolver 20 / Moonlight 0; 1 -> 8 / 12; 2 -> 0 / 20.
- All PNGs: `/home/claude/lane_b_out/` (sheets) and `/home/claude/lane_b_out/revunm_work/` (scans); raw .ppm dumps deleted.

## 3. Open
- With no enemy carrying a revolver, the Moonlight reaches stock Doom 2 maps only where BD22 spawns a RevolverSpawner
  (mapper-set ShotgunSpawnerReplacer arg 2, backpack extras, Eviternity MAP30). Owner's call if he wants another source.

# Lane rev-unmaker, round 4 (owner 20:45; branch `lane-rev-unmaker`). RIG ONLY, NOT HEADSET-CONFIRMED
Owner: "Shotvolver and our Slug secondary shot are back. No slugvolver replaces shotvolver. New option to have revolver
replace brutal pistol, option to start with two."

## 1. Done
- **Shotvolver + slug alt fire:** round 1 removed nothing it needs (Revolver.dec AltFire / RSA_MagnumShot, alts.zs
  RSA_Opt_Rev, menu "Shotvolver Slugshot Alt Fire" `rsa_rev_magnum` all untouched). Shown below.
- **Nothing replaces the Shotvolver:** the rsq_moonlight option, its OptionValue and the RevolverSpawner replacement are
  removed. Revolver2 stays gone.
- **"Moonlight Replaces Pistol"** (server `rsq_moonlight_pistol`, default **Off**) and **"Start With Two Moonlights"**
  (server `rsq_moonlight_two`, default **Off**, needs the first). Defaults Off because On changes BD22's own start and its
  pistol pickups. How (roster.zs): BD22's map pistols (WeaponSpawners.dec PistolSpawnerReplacer -> PistolSpawner) and the
  pistol zombie's drop (ZombiemenVariations.dec:3 `DropItem "PistolDrop"` -> Dropables.dec DropedPistol Death
  `A_SpawnItem("PistolSpawner")`) both arrive as PistolSpawner, which is replaced by BrutalRevolver. A Brutal Pistol the
  player gets anyway (the class start item, give, idkfa) is swapped for the Moonlight the tic it arrives (selected if it was
  in hand; the pistol's off-hand copy goes too). In the map's first second (a new game / pistol start) the Moonlight's
  cylinder is full, and with Start With Two the off-hand Moonlight comes too (full) and the Dual key is pressed once.
  Slot: the Moonlight is already in slot 2, the pistol's (KEYCONF.rsqmoon; BD22 KEYCONF setslot 2 has the pistols).
  RevolverRounds map spawns only while Moonlight Replaces Pistol is On.

## 2. Rig evidence (pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm4.pk3`, build.py at `8147745`,
sha256 `b129b363c07a662885676c40e596cecf3e2439613d639ebaee31ee76f6153d5b`; doom2 > brutal22test6 > BD_VoxelPack > pack, lock, ini restored)
- 8 jobs + a frames run, every one `script errors (not BD_VoxelPack voxeldef): none`; only BD_VoxelPack voxeldef 66/72/77/892.
- slug (test-only `tools/moonammo/slugprobe`, puffs per tic): alt fire `RSA_Magnum 0 -> 1`, `1 -> 0`, then `REVOLVER: 1 bullet
  puffs` (the slug: one bullet); fire `7` + `2` puffs (the shell's pellets); alt fire again: 1 puff.
- combos (BD22 Pistol class, `map map01` = new game): Off/Off -> `BrutalPistol`, `RSQ_Off_BrutalPistol`; Off/two On -> the
  same (needs the first); On/Off -> `Brutal Pistol -> Moonlight`, `BrutalRevolver`, `BrutalRevolverCylinder (6/6)`,
  `RevolverRounds (6/36)`; On/On -> `Brutal Pistol -> Moonlight, start with two`, `cap 36 -> 72`, `RSQ_Off_BrutalRevolver`,
  both cylinders 6/6, `RevolverRounds (6/72)`, probe `main BrutalRevolver off RSQ_Off_BrutalRevolver`.
- drops (10 PistolSpawner summoned + 5 PistolZombie summoned, `kill monsters`, 24 killed incl. the map's): Off -> in the
  world `Pistol 22, Moonlight 0`; On -> `Pistol 0, Moonlight 21`.
- spawn: rounds beside bullet pickups 0 with the option Off on MAP01/03/07/11; On -> they spawn (e.g. MAP11 3 in the world).
- cap / dual: unchanged (36 -> 72 with the second; dual fire / flick reloads as round 2).
- Frames: `revunm4_menu.png` (the menu, both options Off), `revunm4_moonlight_pistol_options.png` (start Off/Off pistol,
  On/Off one Moonlight, On/On two; MAP07 a pistol pickup as the Moonlight; a pistol zombie killed). Work PNGs in
  `/home/claude/lane_b_out/revunm_work/`; .ppm dumps deleted.

## 3. Open
- With the option On the player keeps BD22's pistol start ammo (Clip1 45) unused; the Moonlight starts with 6 rounds + a full
  cylinder (two: 6 + both full). Owner's call if the start should give more rounds.
- Purist class pistols (PuristPistol) are not swapped (purist has no reloading; BD22's own gun).

# Lane rev-unmaker, round 5 (owner 20:47 + 20:5x; branch `lane-rev-unmaker`). RIG ONLY, NOT HEADSET-CONFIRMED

## 1. How ammo was drawn and carried (found)
- HUD: BD22's `SBARINFO.BD` (brutal22test6.pk3) draws, in every style (classic bar 8-57, fullscreen sbartype1 184+,
  sbartype2 460+, sbartype3 749+, sbartype4 958+), `ammo2` as the magazine and `ammo1` as the reserve when the gun
  `UsesSecondaryAmmo` and reloading is on (e.g. SBARINFO.BD:21-28). The pack had no SBARINFO. That is right for the guns whose
  magazine is AmmoType2 (Pistol BDPistolAmmo, Rifle RifleAmmo, SMG, MP40, Shot_Gun ShotgunAmmo, ASG, Plasma, Railgun,
  Rocket_Launcher RocketRounds, Sniper xm21Ammo, Revolver RevolverAmmo, Moonlight cylinder, SSG), wrong for this pack's
  magazines (counters.zs: Unmaker, Minigun, Flamethrower2, Machinegun -- whose AmmoType2 is its 40 mm --, MG42,
  IncendiaryLauncher, Devastator, NukeLauncher, HellishMissileLauncher: RSQ_Mag_<gun>), and it could not be switched off.
- Carry: AmmoType2 magazines are separate items, so their loaded rounds were already on top of the reserve's cap. The five
  COUNTER guns (MG42, Incendiary, Devastator, Nuke, Hellish) counted their magazine inside the reserve: loaded rounds ate the
  cap. The four REAL guns lent up to 10 magazine rounds into the reserve item: those ate up to 10 of the cap.

## 2. Done
- **HUD Ammo** (user `rsq_hud_ammo`, menu "HUD Ammo": Magazine + Reserve (default) / Reserve Only). `src/SBARINFO.rsq` is
  generated (`tools/hud/make_sbarinfo.py`) from BD22's SBARINFO.BD, every style: `ammo2` -> `RSQ_HudMag`, `ammo1` ->
  `RSQ_HudRes`, `UsesSecondaryAmmo` -> `InInventory RSQ_HudHasMag, 1` (22 / 23 / 6 places). counters.zs `RSQ_Counters.Hud`
  sets them every tic: magazine = the REAL gun's RSQ_Mag_<gun> (while its magazine is live) else AmmoType2; reserve =
  AmmoType1 minus the lent rounds; HasMag only in Magazine + Reserve mode and when the gun has a magazine (guns with none:
  reserve only). **Dual: both hands** -- the off-hand copy's own magazine (`RSQ_HudMagOff`) is drawn above the main one on the
  classic bar and left of it on the ZDoom-style fullscreen (BD22's default sbartype1); the other three fullscreen styles
  show the main hand only.
- **On top:** the five counter guns are REAL magazines now (counters.zs REAL[] all 1; their .dec Reload / RSR_Out as the
  Minigun's: the magazine's rounds stay with it). A REAL gun's reserve item cap is BD22's cap + exactly the rounds it lends
  (CapBase: MaxAmount, BackpackMaxAmount with a backpack, AmmoM202 48), so a pickup fills the pouch to BD22's cap; every
  other reserve is put back to its base the same tic. Bug found and fixed on the rig: a gun handing its lent rounds back
  read as another gun on the same Clip2 firing (MG42 100 -> 90): reserve-last-tic is now read after all nine ran.
- **Moonlight start** (owner): with Moonlight Replaces Pistol a new game gives a full cylinder + 18 spare RevolverRounds
  (two: both cylinders full + 18). Purist keeps BD22's pistol (unchanged).

## 3. Rig evidence (pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm5.pk3`, build.py at `05b82ed`,
sha256 `9e549f3460e66af3814879653c1221353b77d560295ebb8c8fe2aa061fe5ab9f`; its members are byte-identical to the test build
the HUD / on-top / sweep / MG42 runs used; doom2 > brutal22test6 > BD_VoxelPack > pack, lock, ini restored)
- Every run `script errors (not BD_VoxelPack voxeldef): none` / `ERRORS: none`; only BD_VoxelPack voxeldef 66/72/77/892.
- On top (`netevent rsq_ontop`, rig job ontop; reserve at cap, magazine full, a pickup walked onto, then 30 taken and a
  second pickup walked onto): Rifle `Clip2 200 / cap 200; magazine 31` -> pickup stays (1 within 256), below cap `170 -> 180`
  (taken); Minigun `Clip2 210 / cap 210, lent 10; magazine 200; pouch 200` -> stays, below cap pouch `170 -> 180`; MG42
  `lent 10; magazine 100; pouch 200` -> stays, below cap `170 -> 180`. Shot_Gun `AmmoShell 50 / cap 50; magazine 9` at cap,
  but its summoned shell pickup was not taken below the cap either (the walk never picked it up): not shown for it.
- HUD (`revunm5_hud_ammo_modes.png`, classic bar, both modes; log `HUD: mag N (shown 1|0), reserve N`): Rifle 31|200 ->
  200; Minigun 200|120 -> 120; MG42 100|200 -> 200; Shot_Gun 9|30 -> 30; Moonlight 0|36 -> 36; dual BrutalPistol 16|60 with
  the off hand's 16 above -> 60. `revunm5_hud_full_frames.png` (full frames), `revunm5_menu.png` (the option).
- Sweep of the converted + REAL guns (give/select/fire/alt/reload): no script error; first fills e.g. `Devastator: RELOAD
  magazine 0 -> 50, 50 from the pouch, pouch 99 -> 49`, Nuke 0 -> 1, Hellish 0 -> 6, Incendiary 0 -> 4. MG42 hand reload:
  IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE, `MG42: RELOAD magazine 0 -> 100, 100 from the pouch`, fires again.
  Unmaker hand reload unchanged (0 -> 200, pouch 250 -> 50).
- Moonlight start: `Brutal Pistol -> Moonlight; cylinder 6, spare RevolverRounds 18` (`RevolverRounds (18/36)`); two:
  `start with two; cylinder 6, spare RevolverRounds 18`, both cylinders 6/6, `(18/72)`.
- Slug, drops, dual, cap: as round 4 (re-run, no errors).

## 4. Open
- Machinegun's ammoicon2 on the fullscreen styles is BD22's rocket icon next to its magazine count (the number is right).
- The Shot_Gun pickup test (above). Any old save: the five converted guns start their magazine fresh from the pouch.

# Lane rev-unmaker, round 6 (30-min box; branch `lane-rev-unmaker`). RIG ONLY, NOT HEADSET-CONFIRMED
- **The shell pickup: a test artifact, not a bug.** Test-only `tools/moonammo/pickprobe` (positions, counts) on MAP01's
  start: the player stands on a ledge (z 56); `summon` puts the pickup 56 units ahead, past the ledge's edge, and it drops to
  the floor below (z 8). After the walk the player is at y 841 still at z 56 (its box still over the ledge) with the shell at
  z 8 under it: no touch. Stock BD22 (no pack) does exactly the same, Clip2 too. On MAP07's flat yard (-1010 -1138) both are
  taken, with the pack and in stock BD22 (`Picked up 4 Shotgun Shells`, AmmoShell 20 -> 24; Clip2 130 -> 140).
  So round 5's at-cap "refused" lines for Rifle / Minigun / MG42 were artifacts too: the ontop job now runs on MAP07's yard.
- **On top, re-shown (MAP07, same walk at and below cap):** Rifle `Clip2 200 / cap 200; magazine 31` -> the pickup stays;
  below cap 170 -> 200 (both taken). Minigun `Clip2 210 / cap 210, lent 10; magazine 200; pouch 200` -> stays; below cap pouch
  170 -> 190. MG42 `lent 10; magazine 100; pouch 200` -> stays; below 170 -> 190. Shot_Gun `AmmoShell 50 / cap 50; magazine 9`
  -> stays; below 20 -> 28 (`Picked up 4 Shotgun Shells` x2).
- **Machinegun HUD icon:** make_sbarinfo.py keeps `drawimage ammoicon2` off the Machinegun (8 places); frame
  `/home/claude/lane_b_out/revunm6_machinegun_hud_icon_before_after.png` (rocket icon by 100 before, none after).
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-revunm6.pk3`, sha256
  `7b08db6af3d2f854d7b305552316c3242cf746b8eb234097d90bdd930c58385b`; runs: no script error of ours (BD_VoxelPack voxeldef only).

## lane-ballistics-skin (2026-10-27, branch `lane-ballistics-skin` off `lane-b-1.99x` a4b0eb7). RIG ONLY, NOT HEADSET-CONFIRMED
Owner items 19 (Player Ballistics) and 18 (hand skin tone) from OWNER_REPORT_2026-10-27_r3.md.
Evidence: `/home/claude/lane_ballskin_out/`. Rig: QuestZDoom 17.3 (Depot `tools/rig`, build/rig), exclusive `rig.lock`,
private ini copy; load order doom2 -> brutal22test6 -> BD_VoxelPack -> `BD22_VR-Reloaded_2.0-ballskin.pk3`
(+ the TEST-ONLY logger `rsqt.pk3` for the damage runs; source in `rsqt_src/`, never ships).

### 1. Done (measured)
- **"Player Ballistics: Hitscan / Bullet"** (`src/zscript/rsq/playerrounds.zs`, server cvar `sv_rsq_player_ballistics`, default 0 = Hitscan).
  The source is the owner's RS_Ballistics `zscript/rsb/enemyfire.zs` (github presidentkoopa/rs_ballistics, cloned read-only): it uses
  WorldHitscanPreFired to cancel a monster's hitscan and fly a round at `sv_rsb_enemy_round_speed` (80 a tic). It is ported to the player's
  hitscans, speed 80. RSB_Bullet itself is not ported: its looks (PARTICLEDEFS bursts, SpawnEffectLight, heat) are REMA renderer features.
  - **How the numbers stay BD22's:** one event per pellet, with BD22's spread already in its angles. The round flies the engine's own
    line (AttackDir / OffhandDir). When its per-tic trace finds something, it fires **the original hitscan** (the event's damage, damage
    type and puff, LAF_TARGETISSOURCE) from 2 units short of the hit, for the rest of the range. So the puff damage type, BLOODLESSIMPACT,
    MTHRUSPECIES, decals, blood and kill credit all come from the engine's own P_LineAttack.
  - **Start:** RSQ_Muzzle (its re-fire with LAF_ABSPOSITION is the event taken, or `RSQ_Muzzle.Where`). `SetOrder(1000)` puts it after
    recoil, the flash and the muzzle.
  - **Left as hitscan on purpose:** anything under MISSILERANGE (melee; the SSG's 300-unit 40-damage point-blank blast, SSG.dec
    `A_FireBullets(0,0,1,40,"shotpuff",FBF_NORANDOM,300)`), rails (the Ruger's damaging rail, the Railgun) and non-player shots.
  - **Look:** superseded at 20:09: rounds now look like Dakka's shotgun tracer (round 2 below).
  - **Damage, logged** (`damage_table.txt`, logs `fin_{A,B}_{0,1}.log`). 12 guns, two hand poses, both modes. Per pellet the damage,
    damage type and inflictor are identical in both modes, and match the BD22 code (parsed from this pack's `src/actors/Weapons`):
    | gun | damage | puff (type) | source |
    |---|---|---|---|
    | BrutalPistol | 14 | WeakPuff (Minor) | Pistol.dec:341 |
    | BrutalSMG | 12 | WeakPuff (Minor) | SubMachinegun.dec:379 |
    | Rifle | 20 | HitPuff (Bullet) | Rifle.dec:344 |
    | Shot_Gun | 4 x 13 + 5 x 13 | ShotgunPuff / ShotgunPuff2 (Shotgun) | Shotgun.dec, the A_FireBullets(5,1,4,13) and (2.5,2.5,5,13) lines |
    | SSG | 18 x 13 | ShotgunPuff (Shotgun) | SSG.dec:217-218 |
    | AssaultShotgun | 9 x 11 | MachineGunBulletPuff (Minigun) | AssaultShotgun.dec:272 |
    | Revolver (Shotvolver) | 7 x 22 + 2 x 22 | ShotgunPuff (Shotgun) | Revolver.dec:268-269 |
    | BrutalRevolver | 100 | ShotgunPuff2 (Shotgun) | BrutalRevolver.dec:131 |
    | Minigun | 20 | MachineGunBulletPuff (Minigun) | Minigun.dec:292 |
    | MG42 | 24 | ExtremeBulletPuff (Saw) | MG42.dec:119 |
    | Machinegun | 20 | HitPuff (Bullet) | Machinegun.dec:218 |
    | MP40 | 18 | WeakPuff (Minor) | Mp40.dec:366 |
    The pellet and shot counts are equal in both modes. The number of pellets that land differs between runs only where the spread is
    wide (Revolver 7 pellets at 20 deg against a 48-radius dummy). MG42 shot counts follow the trigger timing. The one 26 in `fin_A_1` is
    a pellet that hit a RifleZombie (its Shotgun damage factor), credited to the player.
  - **Frames:** `bullet_rounds_6guns.png` shows the rounds in flight from BrutalPistol, Rifle, Shot_Gun, AssaultShotgun, Minigun and MG42,
    four frames each. Those runs used the TEST-ONLY slow-motion (`netevent rsqt_slow 4` in the logger) so the camera catches them; play
    speed is 80. `menu_player_ballistics.png` shows the row reading Hitscan (cvar 0) and Bullet (cvar 1).
  - **Bug found and fixed on the rig:** with the hand 35-45 cm to the right, the pistol's drawn muzzle sits inside the player's own box,
    so the round's first trace hit its owner. The round now traces as the shooter, as P_LineAttack does.
  - **Load:** `clean_load.log` (no test pk3, Bullet mode, shotgun fired): the only script errors are BD_VoxelPack's own four
    (`Script error, "BD_VoxelPack.pk3:voxeldef.txt" line 66` / 72 / 77 / 892). There are 0 lines naming the pack and 0 VM aborts.
- **Diff:** one line in `MENUDEF.rsq` (the row under "Ballistics"). Everything else is new lumps, `*.rsx`, sorting after the `.rsvr`
  ones: ZSCRIPT, MAPINFO (AddEventHandlers), CVARINFO, MENUDEF (OptionValue), MODELDEF. Plus `zscript/rsq/playerrounds.zs`.

### 2. Not done (round 1; the skin tone is DONE in round 2 below)
- **Hand skin-tone slider (round 1 smooth attempt): blocked on the rig.** I tried a smooth slider with no engine change and pulled it from the
  branch (the attempt is in `handtone_experiment/`).
  - **The idea:** an ANIMDEFS `canvastexture` named with the full skin path `models/rsq/fbx/fbx_hand.png`. MODELDEF's LoadSkin then
    resolves every FBX hand to the canvas (verified: `TexMan` lookup == canvas, `GetCanvas` non-null). A UI handler paints a copy of the
    texture into the canvas with DTA_Color.
  - **What the rig shows:**
    - With the first paint at tone 0, the hand stays exactly as drawn: (174,120,96) at tones 0 / 0.33 / 0.66 / 1. Later paints never
      show (`handtone_canvas_no_change_tone0_to_1.png`).
    - With the first paint at tone 1, or with any paint every tic (Clear, DrawTexture plain or tinted, Dim), the hand renders black,
      (8,7,5) (`handtone_canvas_black_tone1.png`).
  - **Diagnosis:** the 2D canvas render (Draw2D into the FBO, hw_entrypoint.cpp) is unusable on this 17.3 build. Camera textures, which
    the scope uses, do work.
  - Not tried: a GLDEFS material shader (it has no runtime uniform from ZScript), and psprite translations (they palette-quantise a
    truecolor skin).
  - **The feasible route (the owner's "discrete steps"):** pre-tinted copies of fbx_hand.png, one per step, and per-step copies of every
    MODELDEF block that names fbx_hand.png, swapped with `A_ChangeModel(modeldef)`. Those blocks are in RSQ_GunSide, RSQ_Hands,
    RSQ_Off_*, the rsqdual weapon classes and Purist*. A per-actor skin override cannot do it: the same actor also draws Ermac's
    hand.png meshes, and in rsqdual the gun itself. The copies would have to be generated at build time, because the hand rows they copy
    are being edited by other lanes right now. That is a design change for the coordinator and owner, so it was not built.
- Off-hand (dual) guns in Bullet mode: the code path exists (OffhandPos/OffhandDir), but no dual gun was fired on the rig. Not shown.
- The non-VR (flat) start point: not exercised; the rig is always VR.

### 3. Open (owner)
- Round speed: fixed at 80 (RS_Ballistics' enemy default). Does he want a speed slider, as sv_rsb_enemy_round_speed has?
- Should the Ruger's damaging rail (and the Railgun) also fly as a round in Bullet mode? Today they stay instant: a rail pierces, a round
  does not.
- The shotgun pellets are the small "pellet" calibre (10 x 1.2 units) and are hard to see. Should they draw bigger?
- Skin tone: OK to go the discrete way (generated per-step MODELDEF copies + A_ChangeModel), and how many steps? Gloves as one step?

## lane-ballistics-skin round 2 (2026-10-27 20:02-21:00, owner requests 20:02 / 20:05 / 20:09). RIG ONLY, NOT HEADSET-CONFIRMED
Evidence `/home/claude/lane_ballskin_out/`. Every pack run: 0 lines naming the pack, 0 VM aborts; the only script errors are
BD_VoxelPack's four voxeldef lines (`clean_load2.log`: no test pk3; Bullet + Dakka + Enhanced + tone 13; Shot_Gun and Ruger fired).

### 1. Done (measured)
- **"Shot Tracers: Off / Dakka"** (`zscript/rsq/shotfx.zs`, server cvar `rsq_shot_tracers`, **default Off**: it adds up to 600
  live sprites and 96 bouncing sparks, which is unmeasured on Quest, and Off keeps BD22 as it ships; one click turns it on).
  - Port of Dakka (ijon, WTFPL; read from the clone): `acs/dakka_tracers.h` Dakka_Tracer_Client (dot every 12 units, 256
    units a tic, alpha by the tic's fraction); `decorate/main/puffs.dec` DakkaTracer (scale/alpha 0.4+a*0.1, then -0.1 a tic),
    DakkaPuff (Floor/Ceiling/Wall by 8 units; 1 DakkaBulletSpark + 3 Spark2 at its velocity ranges; DPUF AB 4 CD 2 puff),
    DakkaBulletSpark (gravity 0.5, Doom bounce 0.1, 105 tics, Add). Sprites DPUF A-E shipped as RSDP A-E. No ACS.
  - Starts at the drawn muzzle (the hitscan's own start: RSQ_Muzzle re-fires from there). BD22's puffs, blood, decals stay.
  - **Bullet mode:** the round IS Dakka's shotgun tracer (owner 20:09): a DPUF A head laying Dakka dots at its own 80 a tic,
    always (it is the round's look); the btracer.obj streak and MODELDEF.rsx are gone.
  - Frames: `dakka_tracers_5guns_normal_speed.png` (BrutalPistol, Rifle, Shot_Gun, Minigun, Sniper; Hitscan and Bullet; normal
    speed), `dakka_tracer_ruger_hitscan.png`, `dakka_vs_ours_shotgun.png` (Dakka itself on the rig, doom2 + dakka.pk3 built from
    the clone, next to ours), `dakka_standalone_shotgun.png`.
- **Ruger (Sniper) as a rifle** (owner 20:05). BD22 code, `actors/Weapons/Sniper.dec:261-266`: 50 point-blank (ShotgunPuff,
  range 500), 2 x 50 SniperPuff (range 15000), a damage-0 Gray "trail effect only" rail (14000), and the piercing rail
  `A_RailAttack(30, ..., "None", RGF_SILENT, 0, "sniperpuff", 0, 0, 500, 15, 1)`: 30 to everything on the line within 500,
  damage type SniperDamage (puff), colour None = invisible.
  - The trail-only rail is commented out (lines 265, 348): no beam. One Dakka tracer per shot, always, whatever the option.
  - Hitscan mode keeps the 30 rail as is (it IS the instant piercing shot). Bullet mode: `RSQ_PiercingRound` flies it at 80,
    deals 30 once to every shootable thing its trace reaches (hitscan from 2 units short, sniperpuff, credited to the player),
    stops at walls, range 500.
  - **Parity log** (`ruger/ruger_{old,new0,new1}.log`, 3 dummies in a line at 150/270/390): old pack (a4b0eb7) = new Hitscan =
    new Bullet: front dummy 50 Shotgun + 50 + 50 SniperDamage + 30 SniperDamage; second and third 30 SniperDamage each.
    Bullet's piercing hits land 2 and 4 tics later (flight).
- **"Pump Shotgun Spread: Stock / Enhanced"** (server cvar `rsq_pump_spread`, default Stock). Stock = BD22
  `actors/Weapons/Shotgun.dec:472-475` (and the DM/zoom copies 521-524, 604-607, 644-647): (5, 1) x 4 + (2.5, 2.5) x 5
  [+ (6, 3) x 5 tactical only]. Enhanced = Dakka `decorate/weapons/30_shotgun.dec:53` spread (3, 2.5) on every volley;
  pellets 4 + 5 (+5) and 13 damage unchanged (`spread_{0,1}.log`: 9 per shot, 13 each, both modes).
  Image `pump_spread_stock_vs_enhanced.png`: wall decals from the same spot (122 units: they merge into one blob) and the
  27-pellet pattern from the log (Stock: the ShotgunPuff 4 on a flat 1-deg line; Enhanced: all 9 in a 3 x 2.5 box).
- **"Hand Skin Tone", 18 steps** (`zscript/rsq/handtone.zs`, user cvar `rsq_hand_tone`, option list).
  - Tones: `tools/handtones.py` (committed) writes `src/models/rsq/fbx/tones/fbx_hand_t01..17.png` from fbx_hand.png in CIE
    Lab (L scaled by Lt/Lm, a/b moved to the tone keeping 0.6 of the texture's own variation). 10 human tones Porcelain ..
    Ebony, Undead grey, Green, Blue, Purple, Demon red, Gold, Black glove; 0 = as drawn. Swatches `handtone_texture_swatches.png`.
  - **Measured first:** A_ChangeModel's skin args (skinindex 0, skinpath, skin) on RSQ_GunSide DO re-skin the HUD hand on 17.3
    (rig frame), so **no MODELDEF block is copied**. The override is per actor, and RSQ_GunSide / RSQ_Hands also draw Ermac's
    hands, so it is switched on only while every layer that actor draws is an FBX frame. The FBX frames are read at startup
    from the loaded MODELDEF lumps (Skin 0 "fbx_hand.png" blocks of RSQ_GunSide / RSQ_Hands; 80 frames now), so r11's hand-row
    edits are picked up with no regeneration.
  - Frames: `hand_tones_14_rig.png` (Rifle, 14 tones incl. Blue and Purple, changed live), `hand_tone_ermac_untouched.png`
    (SSG's Ermac hand stays as drawn at tone 13), `menu_bd20_options.png`.
- **Damage regression, final build** (`damage_table_final.txt`, `fin2_A_{0,1}.log`, Dakka on): 13 guns incl. the Ruger,
  identical per-pellet damage/type/inflictor in both modes.

### 2. Not done / limits
- Hand tone is not applied to the dual-wield and Purist weapon classes (their MODELDEFs hang hands and gun on one actor) or to
  Ermac's hands and the fists. A frame pairing an FBX gun hand with an Ermac support (MiniGun handle grip) shows as drawn.
- Dakka cost on Quest unmeasured (caps: 600 dots, 96 sparks). The rig cannot measure Quest frame time.
- Off-hand (dual) shots still not fired on the rig in either mode.
- One rig run (Enhanced, 480 res) fired 3 of 6 trigger pulls; a re-run fired 6 of 6 in both modes (`sp2` logs). Not reproduced.

### 3. Open
- Default for Shot Tracers (Off chosen above): owner's call after the headset.
- **Disk:** at about 20:25 an unthrottled frame dump of Dakka standalone (it renders at hundreds of fps) briefly filled the
  shared disk. It was deleted at once; other lanes may have seen a write failure around then. Dumps are now deleted as soon
  as the PNGs are made (owner's rule, 20:31).

## lane-ballistics-skin round 3 (2026-10-27, owner 21:2x). RIG ONLY, NOT HEADSET-CONFIRMED
### 1. Done (measured)
- **Shot Tracers default = Dakka (1)** (CVARINFO.rsx). The owner judges the Quest cost in the headset.
- **Skin tone on EVERY FBX hand** (dual-wield off-hand guns, the rsqdual and Purist weapon classes, RSQ_GunSide, RSQ_Hands).
  - Measured approach: per model SLOT. `tools/handtone_build.py`, called by `build.py` on each MODELDEF lump, moves every
    FBX-hand block (Skin 0 "fbx_hand.png", 79 blocks in 43 classes today) from model slot 0 to slot 7 in the BUILT pk3 only;
    src/ is not rewritten, so r11's rows are re-derived on every build. No MODELDEF here uses an index above 1 (the build
    refuses if 7 is taken). `handtone.zs` sets A_ChangeModel's skin override on slot 7 of every actor whose class has such a
    block (read at startup from the loaded MODELDEF lumps), for the player's inventory and psprite callers.
  - Guns (slot 0, and slot 1 for the M203) and Ermac's hands (slot 0) are never touched; the round-2 per-frame
    FBX detection is gone. The renderer draws slot 7 only for frames whose block defines it (models.cpp
    CalcModelOverrides: no MODELDEF mesh and no mesh override in a slot = nothing drawn).
  - Frames: `hand_tone_dual_purist_support.png` (tones 0 / 5 / 9 / 13 / 14: dual-wield off hand RSQ_Off_BrutalPistol with
    the main pistol, the PuristRifle gun hand, BrutalPistol gun hand + FBX support cup steadied). `hand_tone_ermac_never_tinted.png`
    (SSG's Ermac hand as drawn at tone 14; Minigun steadied: FBX gun hand purple, Ermac grip as drawn).
### 2. Not done
- Fists and Ermac's hands are not toned (they are not FBX; by the owner's rule they are never tinted).

## lane-ballistics-skin round 4 (time-boxed 30 min): off-hand (dual-wield) shots. RIG ONLY, NOT HEADSET-CONFIRMED
- **Fixed:** off-hand shots started at the off CONTROLLER (muzzle.zs moves only the main hand). `RSQ_PlayerRounds.OffWhere`
  (playerrounds.zs) is RSQ_Muzzle's table in the off controller's frame (OffhandPos, OffhandDir; the RSQ_Off_* copies subclass
  their guns with the same MODELDEF placement, checked for pistol/SMG/rifle). Hitscan mode re-fires the off-hand hitscan from
  there (LAF_ISOFFHAND | LAF_ABSPOSITION, like muzzle.zs); Bullet mode launches the round there. Dakka tracers follow (they
  start at the shot's own start). Wall guard as muzzle.zs.
- **Shown** (logs `/home/claude/lane_ballskin_out/offhand/`, Dakka on, dummy at 384):
  - RSQ_Off_BrutalPistol, both modes: controller (-101.1 795.9 97.1) -> off muzzle (-100.4 803.8 98.9); Hitscan re-fire from
    there (flags 384), Bullet round spawned there; damage 14 Minor WeakPuff = the main pistol's 14 (`offf_{0,1}.log`, `off_{0,1}.log`).
  - RSQ_Off_Rifle, both modes (`off_{0,1}.log`, first combined run): off muzzle (-99.0 820.1 100.3), main rifle muzzle
    (-93.0 820.1 100.3): mirrored about the body; damage 20 Bullet HitPuff(DM) = main 20.
  - Frames `offhand_pistol_dakka_both_modes.png`: the Dakka tracer leaving the LEFT (off-hand) pistol, Hitscan and Bullet.
- **Not shown:** off-hand SMG and Shotvolver: in fresh runs the scripted dual toggle (`give StartDualWield`) did not put the
  copy in the off hand for them (off=rsq_hands, and the main gun then did not fire either), so their off-hand shot never
  happened on the rig. Stopped at the time box; a rig-driver problem or a dual.zs one, not diagnosed.
  The Moonlight (BrutalRevolver) is not in RSQ_DualTable, so it has no off-hand copy.

# r11 port lane (2026-10-27, branch `r11-port` merged into `lane-b-1.99x`): BIG_FUCKING_GUN, IncendiaryLauncher, Devastator, SSG. RIG ONLY, NOT HEADSET-CONFIRMED

Same one method as r10 (wrist pinned, the GUN moves to the hand; every dependent table moves with it) via `heavies/port_hv.py`.
Inputs: `/home/claude/fitfarm_results` (PICKS_r3.md), copied unchanged to `tools/handfit/port/fits/farm_r3/<Gun>/`.
Commits: BIG_FUCKING_GUN / IncendiaryLauncher / Devastator, then SSG (both from the stopped lane, rebased onto the owner-report
commits), then poses (support as data). Port logs and support checks: `port/fits/r11/`.

## 1. Done (measured; rig only, not headset-confirmed)
| gun (row) | farm fit | gun hand (trigger pose, cm) | support (FBX RQFS B palm-under, farm placement) | moved |
|---|---|---|---|---|
| BIG_FUCKING_GUN (3) | _fromMinigun (r2b) | pad 0.00, pen 0.60, palm 0.69 | pen 0.44, gap 1.45 (support_gun.py 0.49 / 1.11) | bd + purist blocks, Pivot + 4 rows, muzzle added; no rsr/rsb case |
| IncendiaryLauncher (10) | _fromGrenadeLauncher (r3) | pad 0.44, **pen 0.95** | pen 0.43, gap 1.10 (support_gun.py identical) | bd + purist + m32_rsr.md3 blocks, Pivot + 1 row, rsr case 12, muzzle added |
| Devastator (6) | _fromRocket_Launcher (r3) | **pad 1.32**, pen 0.58, palm 0.02 | pen 0.49, gap 1.69 (support_gun.py 0.46 / 1.89) | bd + purist + sidewinder_rsr.md3 blocks, Pivot + 7 rows, rsr case 14, muzzle added |
| SSG (20) | own 1.92 hold (r2) | pad 0.00, pen 0.45, palm 0.34 | pen 0.44, gap 1.30 (support_gun.py identical) | 10 MODELDEF blocks (bd, purist, rsb, rsqoff RSQ_Off_SSG), Pivot + 8 rows, rsb case 1 (Hinge / Axis / Offset / PushRef / Bores; off-hand shell block moved, Hand0-2 / HandT re-expressed), casing port, muzzle added |
Hand sprites RQVB BFG, RQV8 Incendiary, RQVC Devastator, RQVD SSG. Shipped md3s are byte-identical to the farm bakes.
**Variants (owner rule 23):** PuristBIG_FUCKING_GUN / PuristIncendiaryLauncher / PuristDevastator / PuristSSG subclass the Brutal guns
(`is` lookups in handtable / gunmoves / muzzle / rsr / rsb inherit the rows); their MODELDEF.purist gun blocks carry the same move and
their dual hand blocks the same FBX md3. No variant was fitted. No Tactical class exists in the pack or brutal22test6.
**Poses as data:** `poses/<Gun>.json` for all four; `rebake.py bake` reproduces the shipped bakes: 0.0000 / 0.0156 / 0.0000 / 0.0000 md3
units (Incendiary 1 md3 quantum). The JSONs now also hold `support` (the shipped handtable SupportHook / Rot / Point row, the farm's
sup_pen / gap, support_gun.py's check). r10's four pose JSONs still lack `support` (their numbers are in `port/fits/r10/sup_*.json`).

## 2. Rig evidence (QZD 17.3 "QZDoom version 4.14.3", doom2 > brutal22test6 > BD_VoxelPack > pack, rig.lock, ini restored, ppm dumps deleted)
- Pack **`/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r11.pk3`** (`python3 build.py 1.99x-lb-r11` at f8fefcf; `src/` byte-identical at the pushed head (git diff f8fefcf HEAD -- src: empty)),
  sha256 `69c01a94cac563eb745273d4eaa4cb7723e9842ced08c5e43baaa5909b4ddba8`.
- Script errors: the only `Script error` lines in every log are BD_VoxelPack's own four (`Script error, "BD_VoxelPack.pk3:voxeldef.txt" line 66:`
  / 72 / 77 / 892); 0 from the pack, 0 VM aborts (smoke x4, hand reloads, 16 + 2 sheet runs, sweep).
- Smoke (give, select, steady, fire, alt, reload, fire): all four held; shots BFG 4, Incendiary 2, Devastator 24, SSG 2.
- Hand reloads on the moved guns: IncendiaryLauncher and Devastator magazines IDLE>EMPTY>DROP>EMPTY>CARRY>INSERT>SEATED>DONE>IDLE;
  SSG break-open: open, ejected 2, round into chamber 0 (0.0 cm off the bore), flick 457 deg/s, "shut (flick), loaded 2 this reload".
  (The first SSG run loaded but missed the scripted flick by 3 tics of timing; the rerun shut. Same tables, same chamber geometry.)
- Sheet **`/home/claude/lane_b_out/r11_hands.png`** (side steady / side fire / eye fire per gun; all frames incl. eye steady in
  `/home/claude/lane_b_out/r11_frames/`): FBX gun hand on the grip and the FBX palm under the gun on all four in the steady frames.
  SSG fire frames are a `kill monsters` retake (the first had gore / a monster sprite in front of the camera: kept as `*_withgore.png`).
- 37-class sweep on the r11 pack: 0 pack script errors, 0 VM aborts; held weapons and reload phases identical to r10's sweep on all 37;
  shots identical except BrutalSMG 10 (r10 9) and MG42 18 (r10 16), the same run-to-run timing DIFFs r10 recorded. Table:
  `/home/claude/lane_b_out/r11_frames/sweep_r11.txt` (r10's run dir has since been removed from the box; compared against its recorded table).

## 3. Not done / flagged (open)
- **Devastator: index pad 1.32 cm off the trigger** (over the fitter's 1 cm threshold; best of three farm starts).
- **IncendiaryLauncher: gun-hand pen 0.95 cm** (> 0.5); the round-1 alternative had pen 1.53.
- Look for the owner: Incendiary's support palm sits about 1 cm under the tube (gap 1.10); SSG's support palm is hidden in the fire
  frames (the gun pitched mid-kick), shown in the steady frame.
- Nothing here is headset-confirmed.

## 4. BD22 guns with / without FBX hands after r11
- **FBX gun hand:** r10's list + **SSG, IncendiaryLauncher, Devastator, BIG_FUCKING_GUN** (and their Purist variants). FBX support on all
  except MiniGun (Ermac's handle grip) and PuristRifle (Ermac's handguard grip).
- **No FBX hand:** FlameCannon (owner item 21: no gun hand, arm-worn), Unmaker, HellishMissileLauncher; melee/thrown: BrutalAxe,
  Chain_saw, DSweap, HandGrenades.

# 2.0 integration (2026-10-27, branch `lane-int-2.0` cut from origin/lane-b-1.99x 9238187). RIG ONLY, NOT HEADSET-CONFIRMED

Merged, in order: lane-rev-unmaker db5156f, lane-ballistics-skin 8c1c268 then its final head f41b04c (off-hand muzzle
shots), lane-b-1.99x after r11 + rebake, then support192 batches 1, 2 and 3 (d9aa0ea). Final-pk3 reruns: boot, Rocket_Launcher / Plasma_Gun / RailGun / Machinegun, Devastator / IncendiaryLauncher / GrenadeLauncher / Rocket_Launcher / SSG / Shot_Gun / AssaultShotgun / Rifle fire + held, Purist held: all as below. Conflicts were only this HANDOFF (both sides
kept) and the src/README.txt credits (the slug revolver line dropped per owner item 20; the Dakka credit kept).
build.py's skin-tone step catches every lane's FBX hand blocks (100 blocks to slot 7, including rev-unmaker's dual Moonlight).

## 1. Done (measured on the rig: QZD 17.3 9afc750, doom2 > brutal22test6 > BD_VoxelPack > pack, rig.lock -x, pristine ini)
- **Script errors:** none from the pack. The only lines are BD_VoxelPack's own four:
  `Script error, "BD_VoxelPack.pk3:voxeldef.txt" line 66:` (and 72, 77, 892).
- **Weapon list (measured in-engine, not typed):** idkfa gives 22 guns, now including REVOLVER (Shotvolver) and
  BrutalRevolver (Moonlight) (owner item 5). Revolver2 is gone. rsq_extra_weapons adds MP40, MG42, Devastator,
  HellishMissileLauncher, FlameCannon.
- **Select / fire / alt fire, every gun, Hitscan mode, Dakka tracers on by default (31 guns):** every gun selects and fires
  (ammo drop, projectiles, Dakka dots/lines or a melee swing). Alt fire is shown on all guns that have one, except as listed in 2.
  HandGrenades was worked in real VR play: the off hand pulled the ring, then the trigger released mid-swing; GrenadeAmmo 1>0, the blast hit 7 targets for 53 damage.
- **Player Ballistics = Bullet** (BrutalPistol, Moonlight, Shotvolver, SMG, Shot_Gun, Sniper, Rifle, Minigun, Machinegun):
  real RSQ_PlayerRounds fly from every gun (1 / 1 / 9 / 3 / 9 / 2 / 3 / 3 / 4 per window). The Sniper also fires 1
  RSQ_PiercingRound. In Hitscan mode no round is ever spawned.
- **Hand reloads (Depot drivers, geometry from the probe's live tables):** magazine guns: Rifle, BrutalPistol, BrutalSMG, MP40,
  AssaultShotgun, RailGun, Plasma_Gun, Sniper, Rocket_Launcher, MG42 (92>100), Flamethrower2 (88>100), Unmaker (184>200),
  Devastator, HellishMissileLauncher, Machinegun (96>100) and Minigun (197>200, needs a backpack, see 2) all go
  EMPTY>DROP>CARRY>INSERT>SEATED>DONE with the magazine refilled. Break/cylinder guns: SSG 0>2, GrenadeLauncher 0>1,
  Shotvolver 4>6, Moonlight 0>6. Pump: Shot_Gun takes 2 shells through the port ("shell home") and finishes a full pump stroke.
- **Dual wield, real play (all 11 dual guns):** own the gun, touch its map pickup (spawner), press the Dual key (+user3),
  pull the off trigger, 40 tics hands-off, then the main trigger. Every gun gets its RSQ_Off_ copy into the off hand. The off hand fires once
  per pull, with no self-refire, and the main gun still fires afterwards.
  - The lane's earlier "dual SMG/Shotvolver fail" was mostly the script: BD22 spawners are THRUACTORS for their first 10 tics, a
    standing player never touches anything, and +forward does nothing in VR mode (use qz_lstick).
  - **A real bug in the Shotvolver copy, now fixed (eca5bac):** RSQ_Off_Revolver (DECORATE.rsqdual) still had the 1.85 layout. Its numeric
    +2 jump after the kick landed in the slug block, so every off-hand shot re-fired forever with the trigger up and
    NeedToHammer was never taken. The main Shotvolver then sat at its hammer frame and never fired again. Hammering now
    follows the jump, as in Revolver.dec since 1.92. Rig: off 6>5>4, main 6>5>4, NeedToHammer 0 after each shot.
- **Variants:** there are no Tactical weapon classes; Tactical is a player class that uses the Brutal guns. Every Purist gun with a
  per-class block carries exactly its Brutal gun's rows (tools/int20_rig/variants.py). Helper-drawn hands (RSQ_Hands /
  RSQ_GunSide) follow RSQ_HandTable.Index, which uses `is`, so the Purist subclasses inherit them. All 24 Purist guns were held on the rig.
  - **Fixed (8e461be): PuristSniper had no MODELDEF blocks at all** ("Sniper stays out" from 2026-10-16), so it showed an
    empty FBX hand. Sniper's 7 blocks are now copied to it. Rig frame: the XM21 is in the hand.

## 2. Not done / flagged
- (round 2: done, default ON as `rsa_rev_slug`, see round 2 below) **Shotvolver slug alt fire is OFF by default** (`rsa_rev_magnum`, server, default false), while owner item 24 says the
  Shotvolver keeps its slug alt. With it on, the rig shows the slug (470 Dakka dots, 2 hits for 88 damage). Owner call: default on?
- **M203 alt fire (Rifle, Machinegun) not shown.** It needs a hand-loaded tube (RFGLoaded). The Depot's m203.py opens the tube
  and takes a round, but the round never seats (stale driver geometry, not refit here). An empty-tube alt is a dry click, as designed.
- (round 2: shown starting and completing, see round 2 below) **IncendiaryLauncher, NukeLauncher hand reload never starts.** The counters show the whole reserve sitting in the magazine
  (pouch 4>0, 1>0), even with a backpack. This is the cap issue the r6 reloads lane already noted; owner call on caps.
- (round 2: no longer, Clip2 cap 400, see round 2 below) **Minigun reload needs a backpack** (magazine 200 = Clip2 cap 200), as the r6 lane says.
- **MP40 dual:** the MP40 is cheat-only (maps spawn the SMG instead), so no in-play pickup gives its copy. Tested with BD22's own
  HasDualMP40 token: works.
- **Moonlight:** a picked-up or given Moonlight arrives with an empty cylinder (BrutalRevolverCylinder 0); the first trigger opens it for the hand reload.
- **Pump driver:** tools/rig/pump.py's constants are stale (the port is now at L 7.33 cm). The sweep used the probe's live table instead.
- **The ballistics lane's $S/rig/ini.pristine and probe.pk3** in the shared session scratchpad were overwritten by this lane by
  mistake (my rig now lives in its own dir). If that lane runs again, re-make its pristine ini.

## 3. Files
pk3: /home/claude/lane_b_out/int20/BD22_VR-Reloaded_2.0-int.pk3 sha256 c4b609b1fb0b8b6bc1df363b2b84651697587998c6fdcb1858f2b8654ba3a6e8 (not byte-reproducible: build.py writes the MODELDEF lumps with writestr, current time) (src/ as at the branch head; `python build.py 2.0-int`; the VERSION file still says 1.99).
Sheets: /home/claude/lane_b_out/int20_sweep.png (every gun held), /home/claude/lane_b_out/int20_purist.png (24 Purist guns);
per-gun frames in /home/claude/lane_b_out/int20/ (hs_*, pu_*). No .ppm left. Test-only tools: tools/int20_rig/ (never in src/).

## Round 2 (2026-10-28, worktree branch `lane-int-2.0-r2`, pushed to origin `lane-int-2.0`). RIG ONLY, NOT HEADSET-CONFIRMED
Rig: QZD 17.3 Depot rig, doom2 > brutal22test6 > BD_VoxelPack > pack, every run `flock -o -x /home/claude/rig.lock` with a 4 s
yield (tools/int20_rig/run.sh), the lane's pristine ini. No .ppm left. The old agent's uncommitted work (slug default, caps)
was kept and finished.

### Done (measured)
1. **Giant shell casing (owner HIGH).** What it was: BD22's own casing SPRITE drawn at scale 1.0. RSA_Casings lends the real
   12 ga hull / rifle case (casemodels.zs) and sets the actor to scale 1.0 (the mesh is real-size); RSQ_Voxels, the next handler,
   then called `A_ChangeModel('None')` on every fresh casing because Spent casings voxels are off by default, which took the mesh
   back and left C4S2 / C4S3 at 1.0: 4x the hull (BD 0.25, a 21 x 10 px sprite), 6.7x the rifle brass (BD 0.15). Not our
   casings.zs port, not BD_VoxelPack's voxel, not the spawn point. **All of AssaultShotgun, Shot_Gun (its pump hull), SSG,
   Shotvolver and Rifle did it** (rig before frames); Minigun / Machinegun / MG42 share EmptyBrass and the same path.
   Fix (voxels.zs): only an option CHANGE takes a model back, and casings are left as thrown when the option changes. Nothing in
   BD_VoxelPack touched. Rig after: normal-size hull / brass leaving each gun, eye + side.
   Frames: /home/claude/lane_b_out/int20/casings_r2/ (before_<Gun>_<view>.png + before_*_maxred.png = the giant; after_* on the
   r2test2 build, final_AssaultShotgun_* / final_Shot_Gun_* on the final pk3; each strip = 8 consecutive frames from the casing's
   spawn, the bottom row a 3x zoom box).
2. **Shotvolver slug alt fire ON by default.** The cvar is renamed `rsa_rev_slug` (default true): an ini saved by any older
   build holds `rsa_rev_magnum=false`, which would have kept the new default from the owner. **Real bug found and fixed:** the
   main hand's AltFire used a numeric +2 jump that ran past `Goto Fire` into `DM:` (Revolver.dec and the RSQ_Off_Revolver copy),
   so every secondary press fired BD22's DM 7 + 2 pellet shot without taking a shell, went through kick + hammer, and only then
   the slug (trace: 9 rounds at t262, slug at t284). Named jumps now. Rig, the old ini (rsa_rev_magnum=false in it), Player
   Ballistics Bullet: one press = 1 round, 1 shell (6>5); a summoned Baron in front: 1 hit for 300 damage. Fresh ini: same.
   The sweep's Revolver alt: RevolverAmmo 5>4. (tools/int20_rig/slugtest.py, logs slughit2 / slugtrace3.)
3. **Reserve caps (parsed: magazines from counters.zs CAP[], BD22 caps from brutal22test6 Ammo.dec / IncendiaryLauncher.dec).**
   Reserve = 2 magazines on top of the loaded one: NukeLauncher magazine 1 -> Nuke cap 2 (BD22 1/1, its backpack adds nothing, so 2
   with one too); Minigun magazine 200 -> Clip2 cap 400, 800 with a backpack (BD22 200/400: x2 kept); IncendiaryLauncher magazine 6
   -> 12 needed, already 48 (AmmoM202, 2026-10-26 owner call), unchanged. Ammo on top kept (RealTick lends above CapBase).
   **Clip2 is shared: the Rifle, Sniper, MG42 and Machinegun carry 400 / 800 too** (owner: say if the rifle must stay at 200).
   Rig, no backpack, gun then a 400 pickup (tools/int20_rig/rl3.py): every one EMPTY>DROP>CARRY>INSERT>SEATED>DONE;
   Incendiary magazine 0>6 (pouch 48>42), reload 5>6 (pouch 42>41), a pickup refills the pouch to 48; Nuke 0>1 (pouch 2>1), reload
   0>1 (1>0), pickup back to 2; Minigun 0>200 (pouch 400>200), reload 197>200 (200>197), pickup to 400. No errors.
4. **PuristRifle.** MODELDEF.purist: the three PuristRifle blocks that draw Rifle.md3 now carry the M203 (model 1) exactly as the
   Rifle's matching blocks (bd.txt main block, rsr RQRM A, RQRM B; tools/int20_rig/purist_m203.py matches each by text), plus the
   Rifle's RQRM C reload block, which the copy was missing. No fitting. Rifle.dec: PuristRifle's AltFire and FireGrenade hold one
   tic and return (no grenade, no dry click, no purist warning). Rig (eye + side, off hand gripped at the Rifle's SupportPoint):
   before = no tube, support hand under the handguard, alt plays Weapon/Empty; after = tube drawn with the hand on it, the same
   frame as the Rifle's; alt: no sound, no projectile, ammo and inventory unchanged.
   /home/claude/lane_b_out/int20/purist_r2/purist_before_after.png (top before, bottom after), r2_Rifle.png (reference).
5. **Merges:** origin/lane-b-1.99x f3674cf (owner approvals), b1225c4 (FBX grenade hand) and 5e6944e (r12 port); lane-scope
   8e6c737 (real 3x scope + alt-fire scope toggle, cvars rsq_scope2_*). Conflicts only in HANDOFF (all sections kept) and
   MODELDEF.purist (PuristSniper and the r12 Purist hand blocks: both kept). PuristHandGrenades synced to the moved grenade and its
   FBX hand (tools/int20_rig/purist_sync.py; tools/int20_rig/variants_all.py: every Purist block now equals its Brutal block).
6. **Script error from the r12 port, fixed (blocker on the owner's load order):** `"MODELDEF.rsq" line 118: Too many models in
   RSQ_Hands`. The free-hand ring block lists the FBX hand as Model 0 then the ring as Model 1; build.py moves the hand to Model 7,
   and QZD sizes a block by its LAST Model line (models.cpp: modelsAmount = index + 1), so the block had 2 slots. The ring line now
   comes first. tools/int20_rig/mdslots.py checks a built pk3 (0 bad blocks). **origin/lane-b-1.99x still has this error.**
7. **Butt strike / pistol whip hit points moved with the guns (port lane bug).** RSVR_MeleeMove.Apply rows for Rifle, Shot_Gun,
   SSG, AssaultShotgun, MP40, BrutalSMG, Machinegun, MG42 (butt) and BrutalPistol, Revolver (whip): each gun's gun_move
   (tools/handfit/poses/<Class>.json) as port_gun.rigid_move from the original placement (Scale -1 1 1, ZOffset -5: the chain
   Place() assumes); equals the json's own R / t where it has one (diff 0). The moves are 5 to 9 cm. tools/int20_rig/butt_move.py.
   Rig: the butt point drawn as a blue dot (buttprobe.pk3) floats behind the stock before and sits on the drawn stock after,
   Rifle / Shot_Gun / MG42 (/home/claude/lane_b_out/int20/butt_r2/butt_marks_side.png, left before, right after). Butt strike on
   the final pk3 (both hands on, gun hand swung forward over the front hand, tools/int20_rig/butt.py): Rifle, Shot_Gun and MG42
   each land BD22's Kickattack on a summoned Cyberdemon (14 damage), 45-66 map units ahead of the butt point, inside the 60-unit
   BUTT_REACH envelope the sweep runs ahead of the stock.
8. **Final pk3 checks (after 6 and 7):** boot: no pack script errors (only BD_VoxelPack voxeldef.txt 66, 72, 77, 892). Sweep, 31
   guns held and fired, no errors: /home/claude/lane_b_out/int20_sweep.png (Sniper and Railgun rows included). Alt "nothing seen"
   on Shot_Gun, SSG, Sniper, Rifle, Machinegun, GrenadeLauncher, NukeLauncher, HandGrenades: the sweep counts only ammo / projectiles /
   tokens. The Sniper's alt now toggles the scope, which none of those count. Shot_Gun and Nuke vary from run to run (their round-1
   rows were FAIL too, and neither file changed this round). The others are as in round 1. Scope 3x on this pk3 (scope3x drive.py,
   eye 8.2 cm behind the eyepiece): the lens target is 50 x 55 px against 15 x 18 px outside, about 3.3x across and 3.06x up, both
   guns: /home/claude/lane_b_out/int20/scope3x_r2.png.

### Not done / open
- Clip2 400 applies to every Clip2 gun (shared reserve): owner call.
- The off-hand RSQ_Off_RailGun still has BD22's zoom alt fire (scope lane flag, owner call).
- The Shotvolver slug refires while the secondary stays held through the hammer (designed in 1.37: held 40 tics = 2 slugs).
- The pump driver constants in the Depot's pump.py are still stale (casecap.py uses the live table, as rsweep.py).

### Files
pk3: /home/claude/lane_b_out/int20/BD22_VR-Reloaded_2.0-int-r2.pk3 (`python build.py 2.0-int-r2`, 127 FBX hand blocks to slot 7;
sha256 bbf220293c816bf71d3e8bb7113f17505898e53ef29972e35d2f5f0d795cd17b; not byte-reproducible). Test-only tools:
tools/int20_rig/ casecap.py, slugtest.py, rl3.py, puristcap.py, purist_m203.py, purist_sync.py, variants_all.py, mdslots.py,
butt_move.py (writes melee.zs rows), butt.py, buttmark.py, buttprobe/, final.sh, final2.sh, logger/ (INT CASE / INT SPAWN /
per-frame B22 FRAME lines added).


# r12 port lane (2026-10-28, branch `port-r12` merged into `lane-b-1.99x`): FlameCannon, MiniGun support, Unmaker, HellishMissileLauncher, BFG10k / NukeLauncher re-fit, Chain_saw, DSweap, BrutalAxe, FBX free off hand. RIG ONLY, NOT HEADSET-CONFIRMED

Same one method (wrist pinned, the weapon moves to the hand, every dependent table moves with it). Inputs: `/home/claude/fitfarm_results`
(PICKS_r4.md, PICKS_melee.md), copied unchanged to `tools/handfit/port/fits/farm_r4/` and `fits/farm_melee/`; logs in `fits/r12/`.
Merged in: origin/lane-hands-r4 (8265683) and origin/lane-melee-hands (72f4391); origin/lane-b-1.99x merged (not rebased: the two lane
merges made a commit-by-commit rebase conflict on handtable.zs in every commit) with handtable.zs merged row by row (theirs: the
support192 rows 11 / 22; ours: the r12 rows). No support row of MG42 / Nuke / BFG10k / BFG9000 / Sniper was written.

## 1. Done (measured; rig only, not headset-confirmed)
| weapon (row) | what | numbers |
|---|---|---|
| FlameCannon (28, NEW row) | no gun hand; place (0.070, -13.155, -6.744, -3.368, -7.292, -0.038) (fc_place, exact); support FBX L open palm under the barrel (r4 under40, RQXB / FbxSupFC) | handtable row 28 added (25 tables), gunmoves Pivot 28 + 6 recoil rows ADDED (its recoil is in md3 frames 1-6, up to 22.6 cm: without them the palm stayed put while the cannon kicked); muzzle = nozzle tip (bore axis at the nozzle ring's front lip, 49.90 -0.31 -2.67 -> 61.92 -5.02 -14.53); flamespout.zs: flames + sparks start at the tip, flames fly along the drawn barrel. Log: start-to-nozzle 0.00 cm (BD22 start was 27-28 cm off), stream-to-barrel 0.00 deg. Support pen 0.33, palm gap 0.30 |
| MiniGun (13) support | FBX fist on the side handle (r4 support_r4_bar_ref, RQXA / FbxSupMini), replaces Ermac pose E | pen 0.09, wrap 183-202 deg; thumb 1.32 cm off (farm flag) |
| Unmaker (23) | FBX fist on the rear hook (r4wrap), place (1.308, -6.492, 0.083, pistol aim) | pen 0.41, palm 0.37; Pivot + 7 rows, rsr case 13 (+ Unmaker_rsr.md3 blocks), muzzle added. Hand reload: EMPTY>CARRY>INSERT>SEATED>DONE, 200 from the pouch (250 -> 50), fires again, no script error. Old support kept: Ermac pose D moved with the gun |
| HellishMissileLauncher (9) | FBX hand on the hose loop (r4wrap), place (3.610, -7.537, 2.891) | pen 0.18, palm 0.68; Pivot + 6 rows, rsr case 16, muzzle added; old Ermac support D moved with the gun |
| BFG10k (2) / NukeLauncher (14) | gun hand re-fit r4dense, `port/reseat_gun.py` (moves an already ported gun again, every table by the relative move) | pen 0.20 / 0.21; relative move pure translation 0.683 / 0.369 cm; MODELDEF x4 / x4, Pivot + fire rows, Nuke rsr case 15, muzzles. Support rows NOT touched |
| Chain_saw (25) | FBX rear-handle hand, index on the trigger (squeezes on its fire frames); FBX L top-handle support (RQXC / FbxSupSaw) | place (3.195, 9.817, -13.640); 24 swing rows refit; gun-hand pen 0.77 (farm flag); support pen 0.39 |
| DSweap (26) | two hands on the hilt: FBX gun hand + FBX L support (RQXD / FbxSupDS); the DSL2 two-handed block = K . M . DSL1 (K = its 110 deg turn about the controller, measured), the support takes the same turn in hands.zs, the free fist is hidden then | place (2.723, -1.541, -4.336); DSL2 -> (2.7233, -39.1092, -31.9687, -9.6221, 113.6676, 20.0265), residual 0.0000 cm; pen 0.48 / support 0.44 |
| BrutalAxe (24) | FBX hand on the haft; AXE2 (two hands) = M . AXE2; GunHookTwo = M (H2 H1^-1) M^-1 (the regrip conjugated) | place (2.308, -13.113, -2.195); AXE2 -> (-0.4368, -4.9611, -19.6389, 3.854, 3.363, 10.974); GunHookTwo (-0.926, 9.703, -12.156); 14 swing rows; pen 0.71 (farm flag); support = old Ermac pose E moved |
Melee hit points: `melee.zs` `RSVR_MeleeMove.Apply(k, poseFrame, p)` (the per-weapon rigid move, in Place()). Rig swings (test driver
`lane_b_out/r12_logs/mtdriver_zscript.txt`, from r6b + a moved/unmoved print): axe AxeAttack 25 at the moved edge (edge moved 4.5 map units),
saw SawDamageHorizontal 5-6 every 2 tics at the moved bar (1.8 / 3.1 units), sword DSAttack 200 one-handed and two-handed (tip moved 9.8 units).
Purist variants: PuristFlameCannon / PuristUnmaker / PuristHellishMissileLauncher inherit the rows (`is`), their MODELDEF.purist blocks carry
the same move; no variant fitted. HandGrenades skipped (not ready; another lane has since ported its gun hand).
Hand sprites RQVE Unmaker, RQVF HML, RQVG Chain_saw, RQVH DSweap, RQVI BrutalAxe; supports RQXA-RQXD (free in pack, brutal22test6, BD_VoxelPack, doom2).

## FBX free off hand (coordinator item, 2026-10-28)
`port/offhand_r12.py` bakes `fbx_r12_free_L.md3` (in place at the off controller, hook 0; the approved FBX pistol wrist mirrored to the left):
frame 0 relaxed open (RQHN A, FreeHand), 1 fist (RQHN H, AmmoH: the idle free hand and the off-hand trigger punch), 2 index-thumb pinch
(RQHR A, pads 0.0007 cm apart) + `rsq_ring_fbx.md3` (BD22's ring moved 7.86 cm to the pinch point). Rig eye frames: idle, ring pull, ring pull
from the side, after the throw. **Stays Ermac (not swapped, each needs its own fit round an object or an owner call):** the reload holds
RQHN I / J / L / M (magazine, shell, cell, pod: MODELDEF.rsr / .rsb), RQUN (pump shell), RQ2H (M203 round), the Ermac support poses RQSP
(Unmaker, HML, BrutalAxe until the support lane redoes them), RQGF (the Fists weapon / BD22 punches in the gun hand and DFist in dual wield:
hands.zs notes the owner's 2026-10-16 rule "fists are Ermac's, both hands": needs the owner's call against the FBX-only rule).

## 2. Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, rig.lock exclusive, ini restored, ppm dumps deleted)
- Pack `/home/claude/lane_b_out/BD22_VR-Reloaded_1.99x-lb-r12.pk3` (after the origin merge), sha256 `ff1e84eb3656d90b9185f6749d083fd960c3a6b08da5ae93ebc6cf5684a1d4a7`.
- Smoke on it (give, select, steady, fire, alt, reload, fire), all nine held, 0 pack script errors, 0 VM aborts. Only BD_VoxelPack's own 4 voxeldef lines.
- Sheet `/home/claude/lane_b_out/port_r12.png`: per weapon eye held / eye fire-swing / side held / side fire-swing, the off hand before/after, the Unmaker reload.
- `rebake.py check`: 30 poses, every md3 identical (<= 0.0156 md3 units), every MODELDEF / Pivot / fire row regenerated equal; FlameCannon placement only (no hand), HandGrenades now from its lane.
- Logs `/home/claude/lane_b_out/r12_logs/`.

## 3. Flags (open)
- **BFG10k / NukeLauncher support:** the gun moved 0.68 / 0.37 cm (pure translation) and the support rows were not touched, so the support sits that far off the gun until the support lane fits at `poses/<Gun>.json` gun_move (r4dense).
- Unmaker: its old support (Ermac D, moved) is not visible in the side / eye steady frames, same as on the r11 pack (not a regression). The skull in the hand reload is carried by Ermac's reload hold; the skull itself is not clearly seen in these frames.
- Gun-hand pen > 0.5: Chain_saw 0.77, BrutalAxe 0.71 (farm). HML index lies along the body (farm look). BrutalAxe support is still Ermac's glove (no FBX axe support fitted).
- After-throw frame on the final pack: the scripted swing did not release the grenade (the grenade lane changed the throw); the sheet's after-throw cell is from the pre-merge r12b pack (same off-hand blocks), where it threw.
- Butt-strike points (melee.zs RIFLEBUTT etc.) of guns moved in earlier ports were never moved with their guns (pre-existing; not in r12's scope).

## scope-3x (2026-10-28, scope lane, branch `lane-scope`): RailGun and Sniper real 3x scope, always on while held. RIG ONLY, NOT HEADSET-CONFIRMED
Owner 00:05: "Railgun scope does not seem to be zooming see-through ... renders 3x at all times."

### What was wrong (each shown on the rig, QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack)
1. **RailGun defaulted to Dot (1x)**: `rsq_scope_railgun = 0` in CVARINFO.rsq. Sniper defaulted to Real, but the cvars are
   archived, so an old saved 0 kept Dot (the rig ini held railgun 0; the owner's menu showed Dot on both).
2. **Eye gate**: the picture was only swapped onto the glass with an eye within 12 cm behind the eyepiece. Not "at all times".
3. **Picture tilted ~13 deg** (Sniper and RailGun): the r9 port turned both guns in the hand (AngleOffset 3.854, PitchOffset
   3.363, RollOffset 10.974) and moved Lens/Axis (checked: port_gun.rigid_move reproduces both rows to 4 decimals), but the
   camera roll was a fixed 180, so the glass rolled and the picture did not.
4. **Picture squashed vertically to 0.8**: the engine renders a camera texture at ratio aspectRatio/pixelstretch
   (hw_entrypoint.cpp:400); a square cameratexture gave 0.833 (target 45 px wide, 43 tall in the lens vs 15 x 18 outside).
5. **Magnification ~2.8x**: Radius was the disc's outer bound (1.78 / 1.35), not the glass UV half-extent the picture spans.
The lens rows themselves moved with the gun correctly (Lens, Axis), and the glass still gets the camera texture (MODELDEF per-surface skins intact).

### What changed
- CVARINFO.rsq: `rsq_scope2_sniper = 1`, `rsq_scope2_railgun = 1` (renamed so no old ini value can hide 3x); MENUDEF labels "Dot (1x)" / "Real (3x)".
- scope_real.zs: no eye gate; camera + glass skin on for as long as a scoped gun is the ready weapon in VR (off, zero cost, otherwise).
  FovFor uses the sighting eye's distance (nearer the bore line, either eye; 8 cm if neither is behind the glass; capped 40 cm).
  Camera roll = 180 + the glass's roll, measured in render space (view matrix scales z by pixelstretch before roll).
- scope.zs RSQ_ScopeTable: new `Up(i)` (glass up after the port, (-0.0447, -0.1938, 0.98), port_gun.rigid_move @ (0,0,1)),
  `Radius` from the mesh UV extent (RailGun 1.544, Sniper 1.251 cm), `GlassSurface(i)` moved into the table (all per-gun data in one place).
- ANIMDEFS.rsq: `cameratexture RSQSCOPE 256 256 fit 240 200` (ratio 1.2 = pixelstretch -> square render).
- tools/scope3x/: rig driver + probe (two identical 8-unit magenta targets at 256 units: one on the bore, one 0.27*D right), blob/tilt measure, sheet.

### Measured (left eye 8.0 cm behind the eyepiece, 960x960 dumps, default cvars; sheet `/home/claude/lane_b_out/scope_3x.png`)
| gun | in lens | outside | magnification | picture tilt |
|---|---|---|---|---|
| Sniper | 46 x 55 px | 15 x 18 px | 3.07x across, 3.06x up, 2.98x by area | < 0.3 deg |
| RailGun | 48 x 54 px | 15 x 18 px | 3.2x across, 3.0x up, 2.92x by area | ~1 deg (glass UV axes 89 deg, 2% anisotropic) |
- Bore target sits in the lens picture centre to ~0.6 deg. Turning 10 deg: lens picture tracks the gun, one frame behind (camera is
  placed per tic and rendered before the main view; engine limit, ~11-14 ms at 72-90 Hz).
- Picture is up at rest pose too (probe skinOn=1, eye 33 cm away, fov 1.55).
- Frame time (rig, llvmpipe CPU render, same gun and view, scope texture on vs taken off by the probe): Sniper 280 vs 242 ms,
  RailGun 185 vs 155 ms per frame: about +16-19%. Software rendering; NOT a Quest number. On the Quest it is one extra 256x256
  mono scene render per frame (BSP walk + draw), every frame a scoped gun is held. If the headset shows a drop, the owner's
  fallback (scope only while alt-fire held / toggled) is a small change in scope_real.zs WorldTick (gate `want` on a button).
- 0 pack script errors, 0 VM aborts in every run (only BD_VoxelPack voxeldef lines). Fire: RailGun fired in the smoke run.
- Not shown: right-eye frames (the rig dumps the left eye only; the picture is mono, the same texture for both eyes); a rolled-hand
  pose (the rig's rolled controller also changed AttackPitch/Angle between runs; the roll path is the same Place() transform as the
  glass tilt, which is shown). Reload with the always-on scope not exercised this round.

### The scope, file by file (to lift it out as a universal mod)
zscript/rsq/scope.zs (RSQ_ScopeTable = every per-gun number, RSQ_Scope, RSQ_ScopeLayers), zscript/rsq/scope_real.zs
(RSQ_ScopeReal handler, RSQ_ScopeCam), ANIMDEFS.rsq (RSQSCOPE), CVARINFO.rsq (rsq_scope2_*), MENUDEF.rsq (RSQ_ScopeMode + 2
options), MAPINFO.rsvr ("RSQ_ScopeReal" handler), ZSCRIPT.rsvr (2 includes), MODELDEF.rsq (dot quad RQRT A/B, rsq_dot.md3,
RQRTA0/RQRTB0.png), per-gun MODELDEF SurfaceSkin on the glass (scope_glass.png; never a whole-model Skin), meshes with the glass as
its own surface. Borrowed: RSVR_VRHand (rsvr/vrhand.zs: InVR/HandPos/HandDir) and the dot layer in rsq/hands.zs (RSQ_GunSide,
RSQ_Layers.Taken). The manifest is also at the top of scope.zs.

## scope-toggle (2026-10-28, scope lane round 2, branch `lane-scope`): alt fire toggles the live scope. RIG ONLY, NOT HEADSET-CONFIRMED
Owner 01:55: "I want alt fire on the Ruger and RailGun to toggle the scope, for performance."

### Behaviour
- Alt fire on the Sniper (Ruger) and the RailGun toggles the live scope picture. **ON** whenever the gun is selected; the state
  holds while that gun stays the ready weapon (reselect = ON again; rig: off at t=665, Rifle, Sniper back at t=910 -> on).
- **OFF:** the glass gets its own skin back (plain glass) and the camera texture is drawn nowhere, so the engine does not
  render it (hw_entrypoint.cpp only re-renders camera textures drawn last frame). The Dot reticle (Dot mode) still works.
- Toggle cue: BD22's own "ads/in" (on) / "ads/out" (off) sounds, and the lens visibly changes picture <-> glass.
- Read off the alt-fire button (BT_ALTATTACK rising edge) by RSQ_ScopeReal, for every gun with `RSQ_ScopeTable.AltToggle`;
  the handler keeps its own last-tic copy (player.oldbuttons already equals this tic's buttons in WorldTick: first try missed presses).

### What alt fire did before, and what is replaced
- **Sniper (Sniper.dec AltFire, after the integration lane's piercing change d79f10d):** BD22's aim-down-sights zoom:
  A_ZoomFactor 6.0 on the whole view, crosshair 41, "ads/in", X21A raise, then Ready2 / Fire2 with the 2D SNIP frames while
  "Zoomed". **Replaced** by the toggle. No attack is lost: the shot (2 x A_FireBullets 50 + the 30-damage piercing
  A_RailAttack) is the same zoomed or not; Fire2 only added zoomed recoil. The old entry is kept verbatim as `ZoomAltFire`
  (unreachable), so labels and relative jumps are unchanged. Purist keeps PuristWarning.
- **RailGun (Railgun.dec AltFire):** already a swallow state since 2026-10-23 (BD22's 5x zoom + light-amp night vision was
  removed then, kept as `ZoomAltFire`). Alt fire did nothing; now it toggles the scope.
- Neither gun had a real alt attack, so nothing needed to stay reachable.
- **Off-hand / dual copy:** only `RSQ_Off_RailGun` exists (DECORATE.rsqdual; no off-hand Sniper). It has **no live scope**
  (plain scope_glass.png, not in RSQ_ScopeTable: the one camera texture serves the main hand), so there is nothing to toggle.
  Its alt fire is still **BD22's zoom** (A_ZoomFactor 5.0 on the whole view + PowerLightAmp), unchanged. Owner's call:
  leave it, swallow it, or give the off-hand a live scope (second camera texture + off-hand transform; not done).

### Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, exclusive lock, ini restored)
- Sheet `/home/claude/lane_b_out/scope_toggle.png`: per gun ON -> alt fire -> OFF (plain glass) -> alt fire -> ON. Lens target
  46x55 (Sniper) / 48x54 (RailGun) px both times ON, i.e. the same 3x; the outside target stays 15x18 px (no view zoom).
- Fire after each toggle: Sniper magazine 11 -> 10 (scope off) -> 9 (on); RailGun 5 -> 4 -> 3. `Zoomed` stays 0.
- Frame time, same gun and view, ON / OFF / ON again (RenderOverlay count over MSTime, medians; llvmpipe, NOT Quest):
  main view 200x200: Sniper 35.2 / 28.2 / 35.0 ms, RailGun 20.8 / 17.5 / 21.3 ms (off saves 16-20%).
  main view 960x960: Sniper 131 / 121.5 / 125.6, RailGun 126.8 / 126.0 / 127.7 (the eyes' pixel fill dominates the rig there).
  The earlier scope-3x "+16-19% at 960" was measured ON-then-OFF only and is withdrawn as a load-drift artefact.
- 0 pack script errors, 0 VM aborts in all runs. Rig note: a press shorter than one rendered frame is lost on the slow rig
  (console +altattack; wait 3), so the tests hold alt fire 40 tics; real input does not have that problem.

# Off-hand FBX lane (2026-10-28, branch `lane-oh-fbx` merged into `lane-b-1.99x`): fists FBX, every off-hand reload hold FBX. RIG ONLY, NOT HEADSET-CONFIRMED
Owner decisions 2026-10-28: the fists become FBX (overrides 2026-10-16 "fists are Ermac's, both hands"); every off-hand reload hold becomes FBX for 2.0.
FBX hand only (DXR hand_final.fbx through the lane_c fitter); never Ermac's glove, never the DXR IQM hands. Tools: `tools/handfit/offhand/`.

## 1. Done (measured)
- **Frame convention found:** in the drawn frame Ermac's free-hand mesh is a RIGHT hand on both controllers (the engine mirrors the off
  controller). r12's `fbx_r12_free_L.md3` (the right hand mirrored to L) therefore drew as a RIGHT hand on the left controller (rig:
  `lane_b_out/offhand_gate/shots/hand0_left.png` vs Ermac `hand0_left_r11.png`). Every off-hand frame is now the FBX RIGHT rig, baked side R.
- **Free hand + fists** (`free_oh.py`, `mk_free.py`, `fbx_oh_free_R.md3`): FBX fitted IN PLACE of Ermac's frames (landmarks + chamfer):
  open = hand.md3 0 (RQHN A), fist = hand.md3 1 pulled to the tight fist (RQHN H free fist / off punch, RQGF Fists weapon + BD22 punches on
  RSQ_GunSide, dual DFist on Melee_Attacks): landmark rms 1.99 cm, chamfer median 0.57 cm, palm-to-knuckle (0.98, 0.03, -0.18) = knuckles
  forward; ring pinch = ammo_hand 1 with the pads closed (0.002 cm), ring moved 2.05 cm (`rsq_ring_oh.md3`). Punch code untouched.
- **Reload holds** (`objects.py`, `hold_fit.py`, `wire_holds.py`, `fbx_oh_hold_R.md3` RQHF A-Y, labels `OhHold<letter>`): each object as the
  pack draws it (MODELDEF part block + vreload / rsb / rsp chains, parsed), the FBX hand from the Ermac hold closed round it.
  rsr 1-18 (A-R), SSG pair (S), M79 (T), Revolver loader rows 3/7/8/9 (U), Moonlight loader (V), Moonlight round (W), pump shell (X), M203
  round (Y). vreload / rsb HoldState name each gun's frame; all Ermac hold blocks left (RQHN I J L M, RQUN A, RQ2H A B) point at FBX frames.
  Parts moved so the FBX hand can grip them, rows moved with them (rsr HandHook + TopInHand; rsb HandT + HandBase + HandTip):
  Rocket_Launcher 7.61 cm, MG42 6.27, Incendiary 3.00, Unmaker 2.27 (1.4x skull + RS VR Reload turn kept; lane-rev rows brought in,
  cad4023), Hellish 3.72, Minigun 7.52, Moonlight round 2.89 (a thumb-index pinch so the round shows: seen 0.31-0.47 vs Ermac 0.01-0.43).
  Fit numbers per hold: `tools/handfit/poses/offhand/holds.json` (pen cm, pads touching, share of the part seen from three eye points).
- M203 fix: its hold block keeps `Path "models/rsq"` (model 1, the round, did not load once the hand pointed at models/rsq/fbx).
- `python3 tools/handfit/offhand/ohbake.py check`: free (3 frames) + holds (25 frames) rebake to 0 md3 units, bake check 0.008 cm.

## 2. Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, rig.lock exclusive, ini restored, ppm deleted)
- Packs `lane_b_out/BD22_VR-Reloaded_lb-oh5.pk3` (all runs) and `lb-oh6.pk3` (final; sha256 in the commit / report).
- Fists: idle eye frame; main punches logged landing t263/293/324/354, off-hand punches (rsq_punch 1) t254/285/314/344 (test probe
  `tools/handfit/offhand/dmgprobe`: OHT DMG on a PistolZombie with speed 0); frames at the hit tic.
- Each hold mid-reload from the eye (the hand held still in front of the head), then completed: rsr EMPTY>CARRY>INSERT>SEATED>DONE for
  16 magazine guns, rsb shut/loaded for SSG (2), M79 (1), Revolver (chamber loaded), Moonlight loader and round (6), pump (2 shells,
  stroke done), M203 (shut: loaded). 0 pack script errors, 0 VM aborts in every run.
- Sheet `lane_b_out/offhand_fbx.png`; logs `lane_b_out/offhand_gate/logs`; driver `rig_holds.py`, `rig_fists.py`.

## 3. Flags (open)
- NukeLauncher and Minigun: the rig driver reaches no hand reload (Nuke: known since r9/r10; Minigun: the rig drains magazine and pouch
  together). Their FBX holds are fitted (offline renders on the sheet) but not shown in-engine.
- Devastator part (a thin open plate) is held by a middle-finger + thumb pinch; Minigun part is an open plate (pen number unreliable).
- One IncendiaryLauncher run aborted the engine at t215 before any input ("terminate called without an active exception"); the rerun on
  the same pack completed (rig flake).
- Merge note for lane-int-2.0: rsr row 13 TopInHand / HandHook now differ from lane-rev-unmaker's (the skull moved 2.27 cm into the FBX
  grip): keep lane-b's lines.
- Still Ermac anywhere: see the lane report (gun-hand RQGS/RQGT/RQGU in MODELDEF.rsq / .rsqdual / .rsqoff / .purist, support RQSP,
  PuristHandGrenades RQGN).

# 2.0 final (2026-10-28, branch `lane-int-2.0`, also fast-forwarded into `lane-b-1.99x`). RIG ONLY, NOT HEADSET-CONFIRMED
Merged origin/lane-b-1.99x e9640f1 (support192 batches 4-6, FBX fists, FBX free off hand, 25 FBX reload holds) into lane-int-2.0
aead932. Conflicts: MODELDEF.rsq free-hand ring block (int's ring-first slot order kept with lane-b's `fbx_oh_free_R.md3` +
`rsq_ring_oh.md3`), rsr_guns.bd.zs rows 12 / 13 (lane-b's moved parts, per its merge note), HANDOFF (both kept). VERSION = 2.0.
Owner decisions 05:0x applied: heavy C-grip supports (Nuke, BFG10k, BFG9000, HML) accepted; the Minigun gets its own ammo pool.

## Done (measured)
Rig: QZD 17.3 (Depot rig binary, PINS 9afc750), doom2 > brutal22test6 > BD_VoxelPack > pack, every run `flock -o -x /home/claude/rig.lock`,
a FRESH default ini (`int20_rig/ini.f20`: written by the engine on a boot with no ini; only `playerclass` set to Rifle Start, as the
New Game menu does: with the engine default "Fighter" every run got a random class, Purist included, so the sweep's Brutal guns came up
as Purist guns). Test tools: tools/int20_rig/f20all.sh (all steps), f20held.py, f20sheet.py, f20wrap.py (fresh ini for the Depot-driver
tools), mini20.py. No .ppm left.
1. **Pack:** /home/claude/lane_b_out/BD22_VR-Reloaded_2.0.pk3 (`python build.py 2.0`, 134 FBX hand blocks to slot 7; sha256 in the
   commit / report; not byte-reproducible). mdslots.py: 0 blocks with a slot past their size (no "Too many models").
2. **Script errors:** none from the pack, 0 VM aborts, in every run. Only BD_VoxelPack's own `voxeldef.txt` lines 66, 72, 77, 892
   (and BD22's own "Unknown class name 'DeathSphereHealth'", present on the r2 pack too).
3. **Sweep (31 guns, select / fire / alt):** all select and fire. FAIL rows are the sweep's own limits, the same set as round 1 / 2:
   alt "nothing seen" on Shot_Gun, SSG, Sniper (alt = scope toggle, shown in 6), Rifle / Machinegun (M203 alt needs a loaded tube: dry
   click; the M203 hand load is shown in 7), GrenadeLauncher, NukeLauncher; HandGrenades "no shot" (thrown by the off hand's ring pull,
   not the trigger). Per-gun frames `lane_b_out/final20/f20_<Gun>.png`.
4. **Hand reloads:** all 18 magazine guns EMPTY>DROP>CARRY>INSERT>SEATED>DONE with the magazine refilled (IncendiaryLauncher, NukeLauncher,
   Minigun by rl3.py: reserve picked up after the gun). Break guns SSG 0>2, GrenadeLauncher 0>1, Shotvolver 4>6, Moonlight 0>6. Pump
   (rig_holds pump job, live table): 2 shells through the port, stroke done. M203: round in the breech, shut: loaded.
   - First pass showed Rocket_Launcher CARRY>EMPTY: the TEST driver's geometry came from a stale boot.log (r2 pack, before the off-hand
     lane moved the rocket 7.61 cm). Re-booted on 2.0: PASS. Not a pack regression.
5. **Dual wield (player-style, 11 guns):** every gun gets its RSQ_Off_ copy; off fires once per pull, no self-refire, main fires after:
   10 PASS. SSG reads FAIL only because its off pull fires both barrels (2>0), so the script's second off pull has nothing; main 2>0 after.
6. **Scope:** Sniper and RailGun, alt fire held 40 tics: ON > OFF (plain glass, camera off) > ON, `Zoomed` 0. Lens target 50 x 55 px vs 15 x 18
   outside (3.3x across, 3.06x up), both guns. `lane_b_out/final20/scope_toggle_f20.png`. (Rig note: the scope driver now needs hand
   pitch 30 to sit 8 cm behind the eyepiece, as rig.lpose assumes; with 0 the gun pointed 30 deg down and the eye missed the lens.)
7. **Held frames, every weapon** (`lane_b_out/final20_sweep.png`, per gun `final20/held/held_<Gun>.png`; off hand at the gun's
   SupportPoint with the grip pressed, cup guns / axe / fists / grenade by closeness): **every visible hand is the FBX hand, no Ermac
   glove in any of the 31 frames**, nor in the dual frames (`final20/dual_MP40.png`, `dual_Rifle.png`, both hands FBX on both guns) or the
   hold frames. Supports on the gun in all two-handed frames. FlameCannon: the cannon body hides its support palm from this eye point.
8. **One reload per hold family, FBX hand gripping** (`lane_b_out/final20/holds_f20.png`, frames in `final20/holds/`): magazine (Rifle,
   Unmaker skull), SSG pair, M79 round, Shotvolver shell, Moonlight speedloader and single round, pump shell, M203 round; each completed.
   The SSG frame was caught at the breech (hand above the gun), not at the eye pose.
9. **Minigun own ammo pool (owner 05:0x).** `RSQ_MinigunAmmo` (Minigun.dec): reserve 400, 800 with a backpack, magazine 200 on top
   (counters.zs RES row 8, rsr row 17 reserve). Clip2 is back at BD22's 200 / 400 (the shared 400 / 800 reverted). Pickup rule (least
   invasive, the Moonlight-rounds pattern in roster.zs): one Minigun ammo box (50 rounds, BD22's bullet-box art, "Picked up a box of
   Minigun ammo.") beside EVERY map-placed bullet box (ClipBox2) and 1 in 4 map-placed clips, always on; a backpack gives 50; picking
   up the Minigun gives 200 (one magazine; BD22 gave 0). The HUD's magazine | reserve reads the new pool (RSQ_Counters.Hud via Ammo1).
   Rig (mini20.py, f20mini.txt): Rifle Clip2 999 given -> 200 / cap 200; with a backpack 400 / 400. Minigun picked up -> magazine 200,
   pouch 0; a dropped box walked over -> pouch 50 ("Picked up a box of Minigun ammo."); 999 given -> pouch 400 (cap 400 + 10 lent);
   burst 200 -> 197, hand reload EMPTY>...>DONE, "RELOAD magazine 197 -> 200, 3 from the pouch, pouch 400 -> 397"; backpack -> 800.
   HUD mag / reserve = 200 / 400 etc. MAP01: 2 map bullet pickups, 1 Minigun box put beside. Re-swept after the change: Minigun, MG42,
   Machinegun, Rifle, Sniper fire as before; their hand reloads PASS; 0 pack errors.

## Not done
- Dual SSG off-hand second pull not shown (the copy fires both barrels on the first pull, by design).
- Nothing was run on the owner's headset.

## Open
- Ermac meshes are still REFERENCED in MODELDEF (RQGS / RQGT / RQGU gun-hand frames in MODELDEF.rsq / .rsqdual / .rsqoff / .purist,
  RQSP supports): not drawn in any rig frame here (every row has an FBX override), but not deleted.
- Minigun ammo box uses BD22's bullet-box art unchanged: on the floor it looks like a Clip2 box (the pickup message tells them apart).
- Purist-class guns not re-shot this round (MODELDEF.purist equals the Brutal blocks: variants_all.py, 0 differing).
- The off-hand RSQ_Off_RailGun still has BD22's zoom alt (scope lane flag, owner call).

# 2.0.1: the Moonlight on pistol ammo (2026-10-28, branch `moonlight-pistol-ammo`, fast-forwarded into `main`). RIG ONLY, NOT HEADSET-CONFIRMED
Owner 06:46 (headset, 2.0): "Moonlight -- your ammo model is not meshing well with the voxels. Change Moonlight to take
BrutalPistol ammo, consume 3 ammo per shot, reloads after 18 ammo consumption."

## Done (measured)
- **Reserve = BD22's Brutal Pistol's, `Clip1`** (parsed: brutal22test6 `actors/Weapons/Pistol.dec:3` `Weapon.AmmoType1 "Clip1"`,
  this pack's copy `src/actors/Weapons/Pistol.dec:4`; class `actors/MISC/Ammo.dec:50`, cap 100, backpack 200).
  `BrutalRevolverCylinder` / `...Off` stay the gun's SHOTS (0-6). Every load of one chamber takes 3 Clip1 and needs 3
  (stock speedloader Fill, RSB_TopUp1, RSB_LoadOne, off-hand Fill; the "anything to load?" checks are `Clip1 >= 3`).
  A full cylinder = 18. Firing takes one shot from the cylinder; the reserve moves only at a reload (as BD22's own pistol:
  BDPistolAmmo in the gun, Clip1 in reserve). Pickup `AmmoGive1` 18 (one cylinder; was 6 own rounds).
- Hand reload: `rsb_guns.zs` rows 10 / 11 reserve -> "Clip1" and new `RSB_Guns.ReservePer(i)` (3 for rows 10/11, else 1);
  `rsr_break.zs` CanTakeRound / the pair check need `need * ReservePer`. Patched by hand (header note; re-apply after gen_rsb.py).
- **RevolverRounds removed:** the actor, its ring model (`models/rsq/moonammo/*`), `RVRDA0.png`, its MODELDEF block
  (`MODELDEF.rsqmoonammo` keeps only the gun's world pickup), roster.zs's 36 / 72 cap tick, the 1-in-4 spawn beside map
  Clip2 and the 18-spare start grant. `RSQ_Roster.SwapPistol` now restores Clip1 after giving the Moonlight, so with
  "Moonlight Replaces Pistol" the player keeps BD22's pistol start ammo exactly (rig: 45 with the option off, 45 on).
  Options, dual wield, FBX holds, damage, fire rate untouched. HUD (counters.zs GunAmmo, generic): cylinder SHOTS | Clip1.
- README (Revolvers and ammo), OWNER_REPORT item 24 marked superseded. VERSION 2.0.1.

## Rig evidence (QZD 17.3, doom2 > brutal22test6 > BD_VoxelPack > pack, `flock -o -x /home/claude/rig.lock`, fresh default ini
`int20_rig/ini.f20` copied in per run; driver `tools/moonammo/rig_moonpistol.py`; full log `/home/claude/lane_b_out/m201_rig_moonpistol.txt`)
- Boot: 0 pack script errors (only BD_VoxelPack's own voxeldef errors and its DeathSphereHealth warning, as on 2.0).
- Fire: `Clip1=60 Cylinder=6` -> one shot -> `Clip1=60 Cylinder=5` -> five more -> `Clip1=60 Cylinder=0`.
- Hand reload, speedloader (rsb gun 10, IDLE>OPENING>OPEN>CLOSING>DONE): `Clip1=60 Cyl=0` -> `Clip1=42 Cyl=6`.
  Only 9 in reserve: `Clip1=9 Cyl=0` -> `Clip1=0 Cyl=3`. A round at a time (gun 11, 6 chambers driven), 9: -> `Clip1=0 Cyl=3`.
- Stock reload (rsr_reload 0): 60/0 -> 42/6; 10/0 -> 1/3.
- Dual (both Moonlights, shared Clip1 60): off hand fired empty, flick -> `Clip1=42`, off cylinder 6; main emptied, flick -> `Clip1=24`.
- Gone: `summon RevolverRounds` -> "Unknown actor or visual thinker 'RevolverRounds'"; `give` -> "Unknown item"; MAP01 / MAP07 with
  the option on: no such class can exist; no "RevolverRounds" string in the pk3's text lumps.
- Start (Pistol class): option off Clip1 45; on: `Brutal Pistol -> Moonlight; cylinder 6 shots, pistol reserve Clip1 45`; two: both 6, 45.
- HUD: 2 shots fired, Clip1 57: bar reads `4 | 57` (`/home/claude/lane_b_out/m201_hud_moonlight.png`, `..._bar.png`).
- pk3 `/home/claude/lane_b_out/BD22_VR-Reloaded_2.0.1.pk3`.

## Not done / open
- Nothing run on the owner's headset.
- The speedloader mesh still shows six rounds when the reserve only fills 3 shots (as before with a short reserve).
- `tools/moonammo/make_pickup.py`, `rig_rev.py` (workshop tools) still name the removed class; they are history, not shipped.
- Read of "consume 3 ammo per shot": the pistol reserve does NOT drop on a shot; it drops 3 per chamber loaded. Total pistol
  rounds held (reserve + 3 x cylinder) drop 3 a shot. If the owner wants the reserve itself to tick down per shot, say so.

# fix-guns-202 (2026-10-28, branch `fix-guns-202` off origin/main e6c586b): owner 2.0.1 headset items 32-35 (gameplay only). RIG ONLY, NOT HEADSET-CONFIRMED
Owner 18:26 (via coordinator): no hand-pose corrections in this update. The Ruger hand / support re-fit was DROPPED before any
pose was touched (no pose, md3 or hand row changed; rebake check below). Shot direction (muzzle.zs / playerrounds.zs / shotfx.zs /
scope direction) is another lane's and was not touched.
Rig: QZD 17.3 (Depot rig, PINS 9afc750), doom2 > brutal22test6 > BD_VoxelPack > pack, every run `flock -o -x /home/claude/rig.lock`
(Depot int20_rig/run.sh with the fresh default ini, or rig_holds/gate_gun with the ini restored). No .ppm left by this lane.
Pack `/home/claude/lane_b_out/fix202/BD22_VR-Reloaded_2.0.2-fixguns.pk3` (sha256 9ec318cf8ec6778df9f7422d18c85b11fd0bcf2451aefdaba556a417798baf7d,
`python build.py 2.0.2-fixguns`, VERSION file left at 2.0.1). Evidence: `/home/claude/lane_b_out/fix202/` (PNG + logs/).
Test drivers (TEST ONLY, never ship): `tools/fix202/` (rl_switch.py, rl_key.py, tone_m203.py, moon_rig.py + moonprobe/, strip.py);
mesh tools: `tools/fix202/moon_frames.py` (measure every frame), `moon_bake.py` (makes rev_vr.md3).

## Done (measured)
1. **Ruger does not reload (item 32): FOUND and FIXED** (`Sniper.dec`). Its Ready loop ended `RSQ_SemiWait: ... A_WeaponReady / Loop`
   (posefix F11 semi-auto, 1.99). In DECORATE `Loop` goes to the LAST label, RSQ_SemiWait, so after one pass Ready's checks
   (Reloading, Unload, AltFire, Kicking) never ran again: the reload key / mag release did nothing until a shot's own states ran.
   Now `Goto Ready`. A scan of every Ready block in the pack finds no other label in front of a Loop.
   Rig (`rl_key.py`, two single shots, gun resting, reload key): **2.0.1: nothing** (the reload only starts at t642, after the next
   shot); **fixed: IDLE>EMPTY>DROP at the key (t387)**, pouch > CARRY > INSERT > SEATED > DONE, then fires (`logs/key_Sniper_*.log`).
   Full empty -> switch -> back -> grab -> insert -> CHARGE > PULL > RELEASED > DONE -> fires 10 > 9 (`logs/sw_Snipert3.log`).
   Scope toggle still works (alt fire now reaches its swallow state each tic): lens target 50x55 px ON (f90-144), plain glass OFF
   after alt (f150-168), ON again (f174+), outside target 15x18 (`scope_toggle_fixguns.png`).
2. **M203 / 40 mm round hand ignored the Hand Skin Tone (item 33): FIXED.** The round-hold block (MODELDEF.rsm, RQ2H A) names its
   skin `fbx/fbx_hand.png` (Path models/rsq so the round loads), which `tools/handtone_build.py` did not match, so its hand stayed in
   slot 0. The build regex and `handtone.zs` Parse now accept the folder form (135 hand blocks to slot 7, was 134). The block's hand
   Model line moved LAST (QZD sizes a block by its last Model line: with the round's line last it was "Too many models in rsq_hands",
   caught on the first boot); handtone_build.py now refuses to build such a block. `mdslots.py`: 0 bad blocks.
   Rig (Depot rig_holds M203 job, the round in front of the eye): Rifle tones 0 / 8 / 16 and Machinegun 0 / 8 / 16: the round hand
   takes each tone like the gun hand; 2.0.1 at tone 8: round hand still the default pink (`tone_rifle.png`, `tone_mg_and_201.png`).
3. **Reload lost across a weapon switch (item 33), every magazine gun: FIXED** (`vreload.zs` RSR_ReloadHandler.Resume). Switching
   away aborts the reload, but the gun keeps its no-magazine token (RSR_Guns.NoMag), so it came back empty with no reload to grab
   into. Now, once per selection, when a magazine gun with no magazine reaches its Ready frame (RSR.IsReadyFrame + WF_WEAPONREADY;
   earlier the select animation eats the token: Rifle SelectAnimation), its reload restarts the way the mag-release button starts
   it; RSR_Out sees the token and waits at EMPTY (no second drop). Up to 4 tries, 8 tics apart; off VR / Real reload off: unchanged.
   Rig (`rl_switch.py`: empty, reload, switch to the pistol, back, pouch, insert, handle, fire; `logs/sw_all.txt`):
   resumed at EMPTY and completed to DONE: Rifle, BrutalPistol, BrutalSMG, MP40, AssaultShotgun, RailGun, Plasma_Gun, Sniper (t3 run),
   Rocket_Launcher, MG42, Flamethrower2 (its own empty logic restarts it), Unmaker, Devastator, HellishMissileLauncher, Minigun,
   Machinegun. Rifle fires after (30 > 29). NOT SHOWN: IncendiaryLauncher and NukeLauncher (this driver never empties them; the
   same driver limit the 2.0 lanes hit: rl3.py).
4. **Moonlight (item 34): the mesh animates, every frame used.** Measured (`moon_frames.py`, rev.md3 41 frames, 11 surfaces):
   1-2 hammer cocks (22, 54 deg) and the cylinder turns (22.5, 45 deg), 3 hammer falls, 4-14 the kick (whole gun 6.6 deg) and
   recovery, 15 rest; 16-18 latch, 19 break-top snaps open, 20-29 rounds eject, 21-30 speedloader in, 30-33 close, 33-38 loader away,
   39-40 rest. The mesh moved the WHOLE gun (grip up to 4.6 units in the reload): in VR that tears it from the hand.
   `rev_vr.md3` (`moon_bake.py`): shot frames keep the kick pivoted at the grip (grip moved 0.93 -> 0.00); reload frames hold the body
   in the hand (body fitted on its rigid vertices, residual <= 0.08); frame 0 identical. MODELDEF.rsqmoon / .rsqmoondual: rev_vr.md3,
   NoInterpolation removed (frames blend tic to tic). Fire (main + off-hand copy): frames 1-15 in order: pull B C, shot at D (2 tics
   after the pull, double action), E-H, then I-P where a new pull may cut in (7 tics a shot at most = 5/s, as before). Stock / flick
   reload already used 16-40; now on the in-hand mesh. The hand-driven reload (rsb rows 10/11, rev_rsb.md3) is unchanged and still
   drives the cylinder.
   Rig: every shot frame 1-15 one per tic, shot at t187 (pull t185) (`moon_fire_strip.png`); stock reload 16-40 with the grip in the
   hand (`moon_stock_strip.png`, all 25 frames in the states; the rig draws ~1 frame per 1.3 tics, so 18 and 39 fell between frames).
   Regression (2.0.1's `tools/moonammo/rig_moonpistol.py`): 6 shots 6 > 0; hand reload 0 > 6 (Clip1 60 > 42); stock 60/0 > 42/6 and
   10/0 > 1/3; dual: off fired empty, flick > 6, main flick > 6, shared Clip1 60 > 42 > 24.
5. **Unmaker skull insert noise (item 35): FIXED.** rsr row 13 SndIn was `Unmaker/Start` (UNMSTA, the spin-up); now `Rifle/Reload2`
   (RIFLER2, the Rifle's magazine seat: BD22 Rifle.dec plays it at mag in; rsr row 1 SndIn). Engine sound log (QZ_SNDLOG): seat t488
   `Rifle/Reload2`; `Unmaker/Start` only on firing (`logs/key_Unmaker_snd.log.out`). The skull-out sound stays `Unmaker/Stop`.
6. **Gate:** boot of the final pack: 0 pack script errors, 0 VM aborts (only BD_VoxelPack's voxeldef 66/72/77/892), MAP01 started.
   sweep_f20 (Sniper, Rifle, Machinegun, BrutalRevolver, Unmaker, RailGun): all select and fire; FAIL rows are the sweep's own
   "alt: nothing seen" on Sniper / Rifle / Machinegun (as in 2.0). Rebake: the Depot's `rebake.py check` with RSQ_SET = this worktree:
   SHA256SUMS ok, 30 poses, modeldef_mismatch 0 everywhere, 25 bytes identical + rest max 0.0156 md3 units.

## Not done / open
- Nothing run on the owner's headset.
- Ruger hand poses: dropped by the owner (18:26). Ruger "fires skewed right": the shot-accuracy lane's.
- IncendiaryLauncher / NukeLauncher switch-resume: code path is the same as the 16 shown, but not shown on the rig.
- The Moonlight shot now leaves 2 tics (57 ms) after the pull (the mesh's double action). If the owner wants it on the pull,
  move the shot block above `RVMA B 1` (frames 1-2 then play after the shot).
- The Moonlight's mesh kick (frames 4-14, 6.6 deg, pivoted at the grip) is the mesh's own animation, not RECOIL_DESIGN recoil:
  owner's call to keep it.
- The BD22 repo's own `tools/handfit/port/rebake.py` fails here (its fbx_fitter wants `tools/handfit/ref192_pistol.json`); the
  Depot's copy runs. rsr_guns.bd.zs row 13 SndIn edited by hand (its header says generated).
