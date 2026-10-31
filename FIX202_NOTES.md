# fix-guns-202: status (2026-10-28). RIG ONLY, NOT HEADSET-CONFIRMED
Full detail: HANDOFF_LANE_B_2026-10-26.md, section "fix-guns-202". Evidence: /home/claude/lane_b_out/fix202/.
| job | status |
|---|---|
| 1 Ruger reload (Sniper.dec Ready loop) | DONE, proven on rig (2.0.1 key does nothing; fixed starts at once, full reload, fires; scope toggle still works) |
| 1 Ruger hand/support re-fit | DROPPED by the owner (18:26); nothing changed |
| 2 Hand Skin Tone on M203 round hold (Rifle, Machinegun) | DONE, proven (tones 0/8/16, 2.0.1 baseline shows the bug) |
| 3 Reload across a weapon switch, all magazine guns | DONE, proven for 16 guns; IncendiaryLauncher, NukeLauncher not shown (driver limit) |
| 4 Moonlight uses all mesh frames (rev_vr.md3, interpolation, fire 1-15, reload 16-40) | DONE, proven (frame strips; hand/stock/dual regressions pass) |
| 5 Unmaker skull seat sound -> Rifle/Reload2 | DONE, proven (engine sound log) |
| Gate | boot 0 pack errors, sweep fires, rebake 30 poses 0 mismatch |
