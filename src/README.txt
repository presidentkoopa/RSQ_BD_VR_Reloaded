RS_Brutal22WeaponsQ -- BD22 VR Reloaded 2.0.4r
=====================================

BRUTAL DOOM v22, IN VR, ON A QUEST. As an addon, on the stock engine.

Not a port and not a fork. Brutal Doom stays Brutal Doom: this loads after it, replaces none of
its guns, and with its options off behaves exactly as it shipped. What it adds is hands -- you
reload by pulling the magazine out and pushing a fresh one home, you bash with the gun you are
holding, and the brass leaves the port it is supposed to leave.

AND IT RUNS ON STOCK QUESTZDOOM 17.3. No engine changes, no patched build, no fork required.
That constraint is the point of the whole thing, and it is why anything here runs on your
headset instead of on one machine.


WHERE THIS CAME FROM
--------------------
TeamBeef brought Doom to VR and built the community that made the rest of it possible. Everyone
here found it through them.

Emawind's QuestZDoom is the engine this targets -- the one that put GZDoom on a standalone
headset.

Ermac is the genesis of this whole line of work. His Force Unleashed pack is what made hands in
Doom VR possible at all -- before it there was no proof the thing could be done, and everything
since is downstream of that pack. DoomXR is his. And the hands you are wearing are his twice
over: he modelled them AND he posed them, every pose, by hand. That is not a weekend's work and
nobody should read this pack and think it came for free. It did not. It came from him.

REMA, our own GZDoom fork, is named for the two of them -- eRmac and EMAwind. REMA is where VR
reloading was worked out: real magazines, measured wells, a hand that takes hold of a part and
moves it. REMA can do things stock QuestZDoom cannot, because we wrote them into it.

This pack is that work coming BACK. Everything REMA taught us, carried to the stock engine and
made to run there -- a little more of it each release. Where stock cannot do what REMA does, it
says so plainly here rather than faking it.


LOAD ORDER
----------
    doom2.wad  ->  brutal22test6.pk3  ->  BD_VoxelPack.pk3  ->  03_BD22_VR-Reloaded_2.0.4r.pk3

Doom 2, not Freedoom: BD_VoxelPack's voxeldef names Doom 2's own sprites and Freedoom fails on it.

With LegenDoom 3.0 (the LD mode below), LegenDoom goes right after doom2, so Brutal Doom's title map, HUD and
sounds win:
    doom2.wad  ->  LegenDoom_3.0.pk3  ->  brutal22test6.pk3  ->  BD_VoxelPack.pk3  ->  03_BD22_VR-Reloaded_2.0.4r.pk3


RELOADING, WITH YOUR HANDS
--------------------------
EVERY GUN THAT ISN'T A MELEE WEAPON RELOADS BY HAND -- 23 of them. (The BFG and the BFG10k
stay as Brutal Doom made them.)

  magazine    Rifle, Pistol, SMG, MP40, Assault Shotgun, Railgun, Plasma, Ruger,
              Rocket Launcher, and the Machinegun's 100-round box
  drum / can  the MG42's belt drum, the Flamethrower's canister, the Unmaker's skull,
              the Minigun's ammo box, the Hellish launcher's rear drum
  cylinder    the Incendiary Launcher's six-shot cylinder
  bay / block the Devastator's loading bay, the Nuker's warhead block
  pump        the Shotgun
  break-open  the SSG, the Grenade Launcher, the Shotvolver, and the Revolver (Silvergun),
              plus the Rifle's and the Machinegun's underbarrel 40 mm

Take the part out with your off hand, reach to your belt for a fresh one, push it home. Break
guns swing open, take a round at a time or a speedloader, and a flick of the wrist shuts them.
Rounds left in a magazine you pulled are kept and go back in, even with no ammo left in reserve.

Brutal Doom never reloads most of the heavy guns at all. Each of their parts was carved out of
the gun's own mesh so it could come off; on those guns the "magazine" counts down Brutal Doom's
own ammo, so the ammo you carry and the damage you do are exactly Brutal Doom's.


MELEE
-----
  GUN BASH          your kick key, with a gun in your hands, bashes with the gun instead of
                    kicking. Brutal Doom's own kick damage; the boot is simply not drawn.
                    Pick its impact effect and its colour in the menu.
  PISTOL WHIP       swing a pistol or a revolver and it hits what it passes through.
  BUTT STRIKE       drive the stock forward with both hands on it. All eight stocked guns:
                    Rifle, Shotgun, SSG, Assault Shotgun, MP40, SMG, Machinegun, MG42.
                    OFF by default -- two hands on a rifle is also how you aim one, so this is
                    the one most likely to go off when you did not mean it. Turn it on and judge.
  FISTS             a real punch with either hand, and punching a switch works it.
  AXE / DRAGONSLAYER  swing them; two hands and the edge leading bite harder.

It reads your arm, not your body. Walking, strafing and turning move the gun and are subtracted;
only the swing counts.

Out of VR, or with these turned off, Brutal Doom's own melee is untouched.


EVERY GUN SHOOTS LIKE ITSELF
----------------------------
Behind the Ballistics switch -- Stock / Low / Max. Stock is Brutal Doom's own and nothing of ours.

  RECOIL        22 guns, each from its own cartridge: bullet weight, muzzle velocity, powder and
                the loaded gun's weight. An MG42 and a Kar98k fire the same round out of a 25 lb
                gun and a 9 lb gun, and the numbers say so. In VR this moves the GUN IN YOUR
                HANDS, never your aim and never the camera.
  MUZZLE FLASH  18 guns, each with its own light. The SSG throws 760 units of near-white; the
                SMG throws a sixth of that; the Unmaker throws red.
  FLASH TAIL    14 guns -- the room answering the shot, with separate indoor and outdoor
                recordings. Your rifle cracks differently in a corridor than it does under sky.
  THE ROUND     11 guns draw the round in flight, at the size and the speed its cartridge says.
                340 m/s for a 9mm, 900 for 5.56 -- which is fast, so you see a streak.
  IMPACT        a sound for the material you hit -- concrete, metal, wood, glass, pipe, tech,
                lava. A ricochet, per gun, when the round comes in shallow: a magnum skips off
                stone inside 20 degrees where a rifle needs 14. Buckshot never ricochets, because
                nine pellets would be nine ricochets. A light on the hot surfaces.
  BRASS         out of the gun's own ejection port, measured off the mesh, for 9 guns -- and
                three different ways: flicked from a side port, thrown down a chute (the MG42
                ejects through the floor of its receiver, which is what an MG42 does), or tipped
                out by hand from a cylinder or a broken breech. Sized to the round it fired.


OPTIONS
-------
Options -> BD22 VR Weapons. 33 rows, including Reloading (VR or Stock), what grabs the
ammo, where a new magazine comes from, reload assist, the per-gun scopes, the dual-wield and
voxel pages, and "Reload: tuning and debug" for the capture zones and a step-by-step print.

Every option defaults to how Brutal Doom behaves, or to the gentler setting, except the VR hands
and reloading themselves. Turn Reloading to "Stock (BD22)" and the guns reload as they always did.

Every gun fires at Brutal Doom's own rate and does its own damage. (QuestZDoom 17.3 lets a held
trigger re-fire the pistol, the pump shotgun, the Incendiary Launcher and the dual pistols faster
than Brutal Doom does on PC; this pack holds them to PC's rate. Want the pistol one shot per pull?
That's "Pistol Semi Auto".)


LEGENDOOM MODE (in progress, rig only, not headset-confirmed)
--------------------------------------------------------------
With LegenDoom 3.0 loaded, BD22 VR switches on an LD mode (it finds LegenDoom by name; without LegenDoom
nothing changes). LegenDoom's legendary monsters drop legendary BD22 VR guns, and the legendary power works on
our guns, hands, reloads and sounds. Carried: 179 of LegenDoom's 180 effects (all but Favoured, dropped), shown on
the test rig round by round (2.0.4a; not yet shown there: Energizing's heal, Hyper / Spamtastic on the plasma rifle,
Perfect on dual guns). 2.0.4b / 2.0.4c: the chainsaw's legendary effects work in VR (Lacerating, RazorEdge, Extended,
Imaginary), Quickdraw fires one shot per press, Burst fires its three shots. With LegenDoom the main menu stays
Brutal Doom's with a LegenDoom Options button, and Options is QuestZDoom's (VR Options included).
Options: Options -> LegenDoom x BD22 VR. Do not also load LD_BD22VR_Patch.pk3: this replaces it.

CREDITS
-------
Brutal Doom v22 is Sergeant_Mark_IV's. It is the mod that reinvented Doom and brought a
generation back to it, and this is an addon to it that ships none of its guns.

Ermac started this. His Force Unleashed pack is what made hands in Doom VR possible, and the
hands in this pack are his work end to end -- modelled by him, and posed by him, every pose
(Rusted Legacy, MIT -- models/rsq/LICENSE_RustedLegacy_MIT.txt). DoomXR is his. None of this
exists without that.
TeamBeef built Doom VR and the community around it.
Emawind's QuestZDoom is the engine.
The BD21 Machinegun is Brutal Doom 21's, brought forward.
The shot tracers, impact sparks and their sprites (DPUF, here RSDP) are from Dakka by ijon
(github.com/0dot0repeating/dakka, WTFPL), ported to ZScript; the pump shotgun's Enhanced spread
is Dakka's shotgun pattern.
Reload foley, impact and tail sounds the mod itself has none of come from RS_Ballistics and
RS_VR_Weapons.


WHAT STOCK CANNOT DO, SAID PLAINLY
----------------------------------
Some of what REMA does has not crossed, and will not until the engine does:

  * Recoil's ROLL and its backward shove. The one hook that carries roll is resolved on the
    weapon's own class, and this pack does not own Brutal Doom's weapons; ZScript cannot add an
    override to them. Tested, not assumed. Yaw and pitch are the whole channel here.
  * Impact PARTICLE BURSTS, heat shimmer, volumetric smoke, wall damage, flash blindness and
    ear ringing. All of them are REMA renderer or engine features with no stock equivalent.
  * Per-part motion at runtime -- a slide that rides back under its own power. On stock a part
    moves only if the motion is baked into the mesh's frames.


KNOWN GAPS
----------
  * A dropped partial drum costs the reserve nothing.
  * The Shotvolver's cylinder has five chambers and a capacity of six; that is how Brutal Doom
    counts it, and loading a round at a time inherits it.
  * The Machinegun's HUD is its model: its sprite lumps are placeholders.
  * The Minigun throws its brass from the body: there is no ejection port modelled in its mesh.
  * The Minigun's ammo box in your hand is the small box off the gun; a bigger one is planned.

Built from the RSQ Weapon Depot. Every number in it is measured off a mesh or parsed out of the
parent mod -- sets/bd22q_1.97/PROVENANCE.txt says what came from where and how to rebuild it.
