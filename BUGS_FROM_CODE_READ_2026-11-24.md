# BD22 VR Weapons: bugs and questions from the code read (2026-11-24)

Found while reading the whole of `src/` at 2.0.5l to write the README. Row names are the old menu's; 2.0.5m renamed and regrouped the rows without changing a setting. **Nothing here was run, and no code was changed.** Each
line says what a player would see, then where it is in the code (paths are under `src/`). The last column is for the
owner: **fix**, **log**, **fine as is**, or an answer. "Invisible" means a player would never notice. "Not verified"
means the reader did not check that part.

## Questions

Also from the owner on 11-24: no merge. The Series is a game mode of its own, designed with Brutal Doom in mind but not dependent on it, and putting the two together takes away from both. The HUD rows (Remove HUD Health and Armor, Remove HUD Ammo) stay on Gun Cards' page for now.

| # | Question | Owner |
|---|---|---|
| Q1 | Out of the box, with no RSQ Melee, bare fists cannot punch in VR: **No Trigger Punch** is on and **VR Punching** is off. Turn VR Punching on by default? |See SH1: waits on the merge decision | Yes: on by default in 2.0.5n |
| Q2 | Recoil is on and has no menu row (its setting's comment says "its own row"). Give it one? |Yes: a Recoil row is added in 2.0.5n |
| Q3 | Three working options have no menu row: the SSG's two-shells-at-once, the shotgun's side port, and the flick-shut speed. Add rows, or leave them console only? |"recoil, ssg, and shotgun side load, not the flick": two rows added in 2.0.5n; the flick-shut speed stays console only |
| Q4 | The quit sounds are silenced for everyone, LegenDoom loaded or not. Intended? |Answered under LD7 |
| Q5 | **Legendary Guns Only From Minibosses** and its two rows only do anything with Champions and RSQ Miniboss both loaded. Grey them out without those, or leave them? Should the rows say Boss? |Owner: "champions, or RSQ Miniboss (we built champions into it)" and "we have minibosses and big bosses now". The rows keep "Miniboss"; no note added |
| Q6 | Never legendary: Revolver (Shotvolver), SMG, MP40, Machinegun, MG42, Assault Shotgun, Railgun, Ruger, the launchers, Flamethrower, Axe, Unmaker. As intended? |**Give them a slot.** Not built: a job for a coding session. Plan: each gun joins its nearest LegenDoom slot (SMG, MP40, Machinegun, MG42 with the chaingun; Assault Shotgun with the shotgun; Shotvolver with the pistol; Railgun and Ruger with the plasma or chaingun; launchers with the rocket launcher; Flamethrower and Unmaker with plasma or BFG; the Axe with the fists or chainsaw). The owner picks the pairings |

## Reloading, hands, grenade, axe, doors (`zscript/rsr`, `rsvr`, `rsg`)

| # | What a player would see | Where | Owner |
|---|---|---|---|
| RL1 | A round pushed into the open under-barrel tube is paid for at once, and is thrown away with no refund if you switch weapons, die or change map before pulling the tube shut | `zscript/rsr/rsr_m203.zs` 533-536, 263-271, 915-918, 852 |**Give it back.** Changed in 2.0.5n (code only, not run) |
| RL2 | **Lift Doors by Hand** with the off grip only works when **Grab ammo with** is set to Off-hand grip. On the default (trigger) the grip never takes a door; only Use or a turned palm does | `zscript/rsvr/door.zs` 169; `zscript/rsr/vreload.zs` 1325 |Owner: "this might be solved by my suggested mod merge". Waits on that | No merge. **The grip takes a door whatever Grab Ammo With says**, 2.0.5n (code only, not run) |
| RL3 | With the pump shotgun's tube full you can still take a shell and push it in: you hear and feel it load and nothing changes | `zscript/rsr/rsr_pump.zs` 246, 331-339; `actors/Weapons/Shotgun.dec` 33 |**Refuse the shell.** Changed in 2.0.5n (code only, not run) |
| RL4 | **New magazine from: Low** is ignored by the under-barrel launcher; its round only needs taking 20 cm away | `zscript/rsr/rsr_m203.zs` 477 |**Fix both.** Changed in 2.0.5n (code only, not run) |
| RL5 | "Low, 40 cm below the eyes" is measured from the pawn's fixed eye height, not the headset, so a tall player must reach lower. Not verified in a headset | `zscript/rsr/vreload.zs` 383; `rsr_break.zs` 510; `rsr_pump.zs` 590 |**Fix both.** Measured from the headset in 2.0.5n (code only, not run) |
| RL6 | **Dual Reload Gesture** off also removes the lone SSG's gesture reload and the lone rifle's launcher gesture | `zscript/rsq/flick.zs` 145-159 |**Only switch off dual.** Changed in 2.0.5n (code only, not run) |
| RL7 | With RSQ Grenade loaded, Brutal Doom's grenade stands down even with **Use RSQ Grenade Instead** off, because RSQ Grenade's own "Replace Brutal Doom's Grenade" also triggers it | `zscript/rsg/grenade.zs` |**Remove this row.** Removed in 2.0.5n |
| RL8 | Not verified: MK Crits is detected by casting `csh_critController` to an Inventory class; if it is not one, the caught-axe critical never arms | `zscript/rsvr/axegrab.zs` 94-96 |**Rig check list:** confirm on the rig |
| RL9 | Invisible: `rsvr_melee_down` is documented for the axe and sword but only affects the pistol whip; the "reload finishes by itself" code can no longer be reached; the "ScopeRing" pose is never selected; the Use key is still reported to the grenade ring, which only accepts the off trigger; `CVARINFO.rsr` 15-16 says the assist slider is on the debug page (it is on the main page) | `CVARINFO.rsvr` 6-8; `zscript/rsvr/melee.zs` 1139-1143; `zscript/rsq/flick.zs` 374-379; `hands.zs` 236; `vreload.zs` 1381 |**Clean it all.** Comment fixed in 2.0.5n; the unreachable reload code and the ScopeRing pose are left in place (no compile check) |

## Shooting, dual wield, roster (`zscript/rsq`)

| # | What a player would see | Where | Owner |
|---|---|---|---|
| SH1 | With defaults and no RSQ Melee, bare fists cannot punch in VR: the trigger punch is cancelled (No Trigger Punch on) and the swing punch is off (VR Punching off) | rsq/fists.zs 130, 277-290; CVARINFO.rsq 7, 11 |Owner: "considering merging the rsq melee, wheel, tacrig, lasersight, and gitd into BD22 for release". Waits on that | No merge: the series stays its own game mode. **VR Punching on by default** in 2.0.5n (code only, not run) |
| SH2 | "Pistol Start: Start with Dual Pistols" does nothing | rsq/dual.zs 359-366, 392 | "this option should go if it does nothing". The row is removed in 2.0.5n, on top of the rewritten menu |
| SH3 | With True Bullets on (default), bullet guns all throw the same wall chips and never ricochet or light metal: the landing round has no gun name. The round mesh and rsq_round_speed are dead for the same reason | ballistics.zs 144-147, 191; muzzle.zs 205-207; bullet.zs 127 |**Fix it.** The impacts changed in 2.0.5n (code only, not run); the round mesh and `rsq_round_speed` are still unused |
| SH4 | Firing only the left gun makes the right gun kick; the left gun never kicks | recoil.zs 225, 311 |**Fix it.** Changed in 2.0.5n (code only, not run) |
| SH5 | No recoil on the Silvergun, Sniper, Nuke, Devastator or Incendiary (no rows) | recoil.zs 74-208 |**Add them.** Borrowed profiles in 2.0.5n (code only, not run); numbers to tune |
| SH6 | "Machinegun replaces MG42" probably never shows: map MG42 spots are already Miniguns. Not verified against BD22's drops | roster.zs 60-62; nosniper.zs 11, 79 |**Make it work.** Changed in 2.0.5n (code only, not run) |
| SH7 | "Dual Reload Gesture" off also removes the lone SSG's and lone rifle launcher's gesture | flick.zs 145-159 |Same as RL6: changed in 2.0.5n |
| SH8 | "Melee Hit Flash Style" lists raw sprite codes (RSS3, RSU1, RSU4, RSU5, RSH0) | MENUDEF.rsq 165-172 |**Name them plainly.** Style 1 to Style 5 in 2.0.5n |
| SH9 | Recoil has no menu row though its comment says "its own row" | CVARINFO.rsq 56-58 |Row added in 2.0.5n (Recoil, Test and Debug) |
| SH10 | Nearly invisible: with True Bullets on, an off-hand point-blank shot is not turned onto the barrel | playerrounds.zs 234 |**Rig check list:** confirm on the rig |
| SH11 | Invisible: rsq_twohand_rifle and rsvr_butt_lead read by nothing; "Find a second ..." can never print; RSA_Opt_SMG never given; stale comments (alts.zs 2, CVARINFO.rsq 46, handtone.zs 20); dead code (counters.zs, hands.zs 902) | CVARINFO.rsq 77, 53; dual.zs 473-476; alts.zs 4 |**Clean it all.** `rsq_twohand_rifle`, `rsvr_butt_lead`, `RSA_Opt_SMG` and the dead jab removed in 2.0.5n, two comments fixed; the counter branch and the dual guard left in place |

## LegenDoom mode (`zscript/rsld`)

| # | What a player would see | Where | Owner |
|---|---|---|---|
| LD1 | Likely, not run: damage with no trigger pull of its own gets the main-hand gun's legendary: a non-legendary off-hand gun, an off-hand gun with the off-hand row off, kicks, grenades, barrels you set off. Annoying in the main hand -> 1 damage, Convincing -> 0, DemonSlayer -> x4 | handler.zs 714-726; fx_g0.zs 490; ld_g1_fx.zs 62 |**Fix it.** Changed in 2.0.5n (code only, not run) |
| LD2 | "Slug Legendary: Primary Fire Only" off: a Slug legendary does nothing. The cvar comment says it is re-rolled; the code does not | CVARINFO.rsld 9-10; ld_g2_fx.zs 196-197; pickup.zs 242-247 |**Re-roll it.** Changed in 2.0.5n (code only, not run) |
| LD3 | "Re-roll Effects Not Carried Yet" changes nothing either way (only Favoured is not carried, and it is re-rolled regardless) | pickup.zs 233-247, 289-291 |"whatever you think is best": the row is removed in 2.0.5n (code only, not run) |
| LD4 | With "Legendary Guns Only From Minibosses" off, "Miniboss Drop Rarity By Tier" and "Legendary Champions Drop Too" do nothing | pickup.zs 35, 46, 68 |Logged. Owner: RSQ Miniboss has Champions built in, so the rows need RSQ Miniboss |
| LD5 | Patient charges only in the main hand, but an off-hand shot still spends the charge | fx_g0.zs 504, 510-515 |**Fix it.** Changed in 2.0.5n (code only, not run) |
| LD6 | "Mute LegenDoom Pickup & Aura Sounds" also swaps the menu and info-screen sounds | ldsounds.zs 20-29, 113-120 |**Fine as is** |
| LD7 | The game's quit sounds are silenced with or without LegenDoom | SNDINFO.rsld 26-27 |Owner: "i just want the normal doom or BD sounds, not the goofy LD ones". Doom's quit sounds restored in 2.0.5n (code only, not run) |
| LD8 | Not verified: if LegenDoom loads after this pack, jingles and auras would play twice | SNDINFO.rsld 1-5 |**Rig check list:** confirm on the rig |
| LD9 | Nearly invisible: reloading one gun pauses the speed-up effect on the other (the pause checks the player, not the hand) | ld_g5_core.zs 97-104 |**Rig check list:** confirm on the rig |
| LD10 | Invisible: Debug Log is On/Off on a 0-2 setting; the top champion row's weights sum to 110 | MENUDEF.rsld 20; pickup.zs 259 |Left as is: invisible |
| LD11 | With LegenDoom loaded, BD22's own Dual Pistols weapon is taken away unless the pistol's legendary is DualWield | handler.zs 1037-1065 |Owner: "dualweild seems like a pointless legendary in a vr game". DualWield never rolls from 2.0.5n; the Dual Pistols weapon stays put away |
| LD12 | LegenDoom's screen shake is switched off at every map start whatever its menu says | handler.zs 140-149 |**Fine as is** |

## What was not read line by line

- The generated tables (hand poses, gun moves, voxel and sprite tables, LegenDoom's number tables) were sampled.
- LegenDoom's effect files were read by their headers and class lists, apart from the core, the pickup, the handler,
  the kiosk and the first effect groups, which were read in full.
- Per-gun alt fires came from a search of `actors/Weapons/*.dec`, not a full read.
- LegenDoom's own pk3 is not in the repo, so nothing about what LegenDoom itself does was checked.
