# Evidence (rig only, not headset-confirmed)

Real QuestZDoom 17.3 rig (RSQ_UBQSeries/tools/rig17), doom2.wad, MAP01, `tools/rig.sh` + the test probe `tools/probe`
(never ships). Logs are full engine logs; probe lines start with PROBE/MON/WHO/HIT/DIED/SPAWN/INV/AMMO/WCARD, patch lines
with RSLDP (rsldp_debug 1). Load order "full" = doom2 -> brutal22test6 -> BD_VoxelPack -> BD22 VR (03_*) -> XMVE 04-07
-> LegenDoom 3.0 -> Champions (mk-champions20210309) -> LDL_BD22VR_Patch.

| Log | Order | BD22 VR | What it shows |
|---|---|---|---|
| base_nold.log | no LegenDoom | 2.0.3q | replacement table before LegenDoom (REPL lines) |
| base_nopatch.log | full, no patch | 2.0.3q | LegenDoom takes 51 of the 56 (REPL), LD pistol+fists given to the BD22 player (WHO) |
| meas_nold_hard.log, meas_bdonly_hard.log | no LD, skill Hard | 2.0.3q | the tables the patch is generated from |
| t1.log | full | 2.0.3r | patched REPL identical to base_nold for all 56; LD weapons taken from the player |
| pA.log | full | 2.0.3r | legendary + champion imp (hp 240/80, LDLegendaryMonsterToken + champion_BlueToken) and a natural legendary bronze champion Imp3 (hp 702 vs 117); kill, drop converted, pickup gives BrutalPistol + Exorcist tokens + LD pickup screen |
| pB.log | full | 2.0.3r | Exorcist x3 on a zombie (`RSLDP group ... +28`), Unlikely refund |
| pC.log | full | 2.0.3t | Vampiric (health 40 -> 100), Replicating hook, drop legendary + pick it back up |
| pD.log | no Champions | 2.0.3u | natural flow with the final patch: drop moved from the map origin to the death spot, re-roll (Marksman -> Scrapper), Fists Unstoppable picked up, Murderous kills -> LDMurderousDamageBuff (tics=1953), Replicating ammo 100 -> 103 |
| pE.log | full | 2.0.3u | final patch: natural legendary NamiDarkImp + Cyan champion (hp 378, both tokens) beside plain champion Imp3 (117) and plain Imp (80); drops, re-rolls, pickup, Violent on hit |
| pW.log, pW2.log | full + RSQ Wheel | 2.0.3u | Wheel's LegenDoom reader finds no rarity/effects on a legendary BD22 gun; with the patch's RSLDP_Service prefix it finds Epic Murderous (WCARD) |

Key frames (`key/`, 200 px rig renders unless named): legendary champion imp glow, kill, LegenDoom's pickup screen on
"Exorcist's Pistol", the BD22 pistol in hand with the HUD line, a BD22 fists legendary pickup on the floor, HUD lines
"Murderous Shotgun" / "Replicating Plasma Gun", and the Wheel ring open (480 px; the held card is hidden behind the gun).

Script errors (not counting BD_VoxelPack's 4 accepted "No sprites specified for voxel" lines): 0 in every log above.
