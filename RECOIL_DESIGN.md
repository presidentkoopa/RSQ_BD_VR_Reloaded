# BD22 recoil: design with the owner (started 2026-10-27)

**Recoil lives ONLY in this BD22 mod, never in ModelSwapper (owner).**

## Lessons from the past (owner's old notes, an older engine)
- **Never accumulate onto psprite offsets.** The engine rewrites them every tic. Writing onto them piled up until the gun spun 360 deg round the player. The current recoil.zs adds its kick last each tic and takes back its own previous addition (the F11 guard).
- **Recoil never changes where a shot goes.** A trajectory kick applied before the bullet reads its trajectory, and biggest on the fresh shot, sent the first shot into the ceiling every pull. The first shot is always clean, and any climb lands after the bullet leaves.

## Current model (recoil.zs, F5)
- **Per gun:** rise (deg) over riseTics, climb per shot up to maxPitch, a yaw drift that reverses every driftPeriod shots, and a linear recover in deg/s after `delay` tics.
- **Where the numbers come from:** REMA's WMSHEET.bd22 / RS_Ballistics, worked out from free-recoil physics.
- **Channel:** psp.x/psp.y tilt the drawn model, yaw and pitch only. No roll, no backward shove. The aim is never touched.
- **Problem:** the curve is the wrong SHAPE: a slow rise over up to 18 tics and a linear drift back. It reads as floating, not kicking.

## Proposed model
- **Spring impulse per shot:** kick (deg of muzzle flip), snap 1-2 tics, then a springy settle with a slight overshoot.
- **Rapid fire:** stacks up to a cap.
- **Side jitter:** small and random.
- **Bracing with the off hand reduces recoil (owner).** When the off hand supports the gun (the pack's existing two-hand steady state), the kick, climb and jitter are scaled down; the factor is tuned with the owner (for example x0.5 to start). REMA's `brace` was dropped in F5 as having "nothing to act on". It does have something here: the size of the visible kick.
- **Sizes scaled down for VR:** the player's wrist absorbs it. The physics sets each gun's rank and ratio; the absolute size is the owner's, tuned by feel.
- **Options:** one strength slider, plus a per-gun table.
- **Proof on the rig:** log tilt per tic over 50 shots and show it returns exactly to zero.

## Real-world equivalents (owner, 2026-10-27): the reference each gun's feel is judged against
| BD22 class | Real gun | Note |
|---|---|---|
| BrutalPistol | Beretta 92FS (or Colt M1911) | the mesh is a Beretta 92 |
| BrutalSMG / MP40 | H&K MP5 / MP40 | |
| Shot_Gun | 12-gauge pump: Remington 870 / Mossberg 500 | |
| AssaultShotgun | Atchisson AA-12 | the AA-12 is known for LOW felt recoil for a 12-gauge (constant-recoil spring), so it kicks far less per shot than the pump and stays steady on full auto |
| Revolver (the shell-firing one, the Shotvolver) | S&W Governor / Taurus Judge | |
| BrutalRevolver (Moonlight) | six-shooter, break action, speedloader | one shot per pull, max 5-6/s |
| Rifle (assault rifle) | Bushmaster M17S | |
| MiniGun | GE M134 Minigun | |
| MG42 | MG42 | |
| Sniper (Ruger 14 mesh, coded XM21) | M21 Sniper Weapon System (DMR / battle rifle) | |
| Rocket_Launcher | Carl Gustaf M4 / RPG-7 | |
| GrenadeLauncher / IncendiaryLauncher (M32) | Milkor MGL or M79 | |
| Flamethrower2 | M2 flamethrower | |
| Plasma_Gun | heavily modified M60 frame (styled on the reversed M60 toy); behaves like a sci-fi directed-energy particle accelerator | |
| RailGun | experimental magnetic-induction railgun | |
| BFG9000 / BFG10k / others | none given: invent a sci-fi feel with the owner, or leave without kick | |
