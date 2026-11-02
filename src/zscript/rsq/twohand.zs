// twohand.zs: TWO-HAND AIM, our own (script), OFF by default. Rig only, not headset-confirmed.
// 2.0.3k: the Rifle-only proof (owner-approved 2026-11-02). 2.0.3l (owner 2026-11-02): every two-handed BD22 gun, each on
// the measured grip point of its own drawn support hand (RSQ_TwoHandTable below). 2.0.3m (owner's first headset test,
// 2026-11-02): THE DRAWN GUN NOW TURNS WITH THE TWO HANDS, and the shots go down the barrel as it is drawn.
//
// WHAT IT DOES. With "Two-Hand Aim (test)" on (rsq_twohand_rifle: the 2.0.3k name, kept so the owner's ini still works) and
// the engine's own two-handing OFF (vr_two_handed_weapons 0), bring the off hand's palm to where the support hand is drawn on
// the gun in hand and press the off grip: the support hand shows on the gun (RSVR_VRHand.TwoHands), the drawn gun swings
// about the gun hand so that its support hand points at the off palm, and every shot of that gun leaves down that drawn
// barrel, from its drawn muzzle. Let go of the grip and the gun eases back onto the gun hand alone (a few tics), the shots
// following it. Every shot muzzle.zs turns onto the bore is turned this way: hitscans and each shotgun pellet (by angle, so a
// spread keeps BD22's own spread round the new line), rails, the player's missiles. Primary and alt fire alike: what a gun
// fires is BD22's, only the line it leaves along follows both hands.
//
// 2.0.3l's FAULT (owner's headset, 2026-11-02, PCVR): the shots followed the two-hand line but the drawn gun stayed on the
// gun hand, so the Rifle faced forward and fired sideways. The direction maths was right (the owner held the line to his
// left on purpose); the gun did not follow it.
//
// HOW THE GUN IS TURNED (stock QZD 17.3, no engine change). In VR the held model's one rotation input that reaches BD22's
// own (DECORATE) weapon classes is its weapon layer's offset: hw_weapon.cpp:108 renders it with
//     RenderHUDModel(..., rotation + (psp.x / 4, (psp.y - WEAPONTOP) / -4, 0), pivot, ...)
// and models.cpp RenderHUDModel applies that turn (yaw about the controller's up, then pitch about its left; no roll) about
// the pivot, Weapon.BobPivot3D (hw_weapon.cpp:347-358, read off the weapon actor each frame), AFTER the controller transform
// and the MODELDEF scale and offsets. (Weapon.ModifyBobLayer3D would give roll too, but the engine resolves it on the
// psprite caller's class, BD22's DECORATE weapon, which cannot override a ZScript virtual.) So each tic, after the weapon has
// had its say (WorldTick is the last writer before the frame), the turn is ADDED to the weapon layer's x / y -- never
// assigned: A_WeaponReady resets them every tic it runs and BD22's Offset() kicks land there too -- and the weapon's
// BobPivot3D is set to the main controller's origin in the gun's own MODELDEF turn space (Pivot below, parsed by
// tools/twohand/support_points.py), so the gun swings about the gun hand. The engine interpolates the layer offset
// (oldx / oldy), so a tic-rate write is smooth at headset rate. The hands drawn on the gun (rsq/hands.zs) already take the
// gun layer's turn; while the pivot is ours they turn about the same point (HandGrip), so they stay where they hold it.
//
// THE TURN (yaw a, pitch b, controller frame: a + left, b + up). With S the gun's support point and P the off palm, both
// in the main controller's frame (F L U, cm), it is the turn about the controller, pitch b about L and then yaw a about U
// (the order models.cpp applies them), that takes the direction of S onto the direction of P; times the gun's Steer, eased
// toward each tic (half the gap a tic) and clamped to MAXTURN. The shots use exactly that turn, the one written into the
// layer (Aim, Turned), and start at the turned muzzle (muzzle.zs Where, OnGun), so they never leave the line the gun is
// drawn along. The weapon's own Offset() kicks are BD22's and are left as they were. No roll: the gun keeps the gun
// hand's roll (the channel has none).
//
// THE PALM. The off controller's origin is not the palm: the palm is RSR.PalmGrab() (-1.5, 2.0, -4.5) cm in the off
// controller's frame, the same point every reload grab measures from (rsr/vreload.zs). The grab takes the palm within the
// gun's Grab radius of S.
//
// WHEN. A rising edge of the off grip (rsr_grip, the synchronised event vreload.zs sends) with the palm within Grab latches
// on the gun in hand; letting go of the grip, or another gun coming up, unlatches. Never: with vr_two_handed_weapons on (the
// engine two-hands; ours stands down, the two are never applied together), with a gun in the off hand (dual wield), while a
// reload, shell loading, a break-open or the M203 has the off hand. One that starts while latched drops the latch; if the grip
// is still held when it ends and the palm is back within Grab, two hands go back on the gun (no new press needed).
// THE PUMP (Shot_Gun): working the pump does NOT drop the latch. With the engine's two-handing off, the same grip press takes
// the pump (rsr/rsr_pump.zs: a grab), the support hand rides the pump as it does under the engine's steadying
// (RSP_Handler.SupportShift), and the next shot goes down the two-hand line again without letting go.
// rsq_twohand_debug prints the latch and, for each shot, the turn and the angle between the shot line and the plain line.

class RSQ_TwoHandAimed : RSVR_Token {}	// two hands on the gun (ours): RSVR_VRHand.TwoHands ORs it in

// Per hand-table row (rsq/handtable.zs Index): Gun (Two-Hand Aim applies), Support (cm F L U, main controller), Grab (cm),
// Steer. The rows left out and why: tools/twohand/support_points.py prints them (the pistol cups, guns without a bore, melee).
class RSQ_TwoHandTable abstract
{
// twohand-table BEGIN: generated by tools/twohand/support_points.py --write (do not edit by hand)
// row 1 AssaultShotgun: FbxWrapAS (fbx_s192_L.md3 frame 2), point 44.86 9.48 -8.63 cm (open-hand check 0.26 cm off), fit rms 0.08 cm over 780 vertices <= 0.3 cm, grab 15.0 cm
// row 2 BFG10k: FbxWrapBFG10k (fbx_s192_L.md3 frame 14), point 21.32 8.92 -1.20 cm (open-hand check 0.33 cm off), fit rms 0.54 cm over 190 vertices <= 0.3 cm, grab 12.8 cm
// row 3 BIG_FUCKING_GUN: FbxWrapBFG9 (fbx_s192_L.md3 frame 15), point 22.49 8.72 -1.72 cm (open-hand check 0.33 cm off), fit rms 0.55 cm over 193 vertices <= 0.3 cm, grab 13.2 cm
// row 5 BrutalSMG: FbxSupF (fbx_b1_L.md3 frame 1), point 31.82 0.76 -4.60 cm (open-hand check 1.22 cm off), fit rms 0.19 cm over 438 vertices <= 0.3 cm, grab 15.0 cm
// row 6 Devastator: FbxWrapDevastator (fbx_s192_L.md3 frame 4), point 42.06 8.85 0.52 cm (open-hand check 0.82 cm off), fit rms 0.21 cm over 391 vertices <= 0.3 cm, grab 15.0 cm
// row 8 GrenadeLauncher: FbxWrapGL (fbx_s192_L.md3 frame 6), point 27.44 9.38 -9.60 cm (open-hand check 1.15 cm off), fit rms 0.27 cm over 317 vertices <= 0.3 cm, grab 15.0 cm
// row 9 HellishMissileLauncher: FbxWrapHML (fbx_s192_L.md3 frame 17), point 30.82 6.95 -11.05 cm (open-hand check 0.62 cm off), fit rms 0.69 cm over 99 vertices <= 0.3 cm, grab 15.0 cm
// row 10 IncendiaryLauncher: FbxWrapInc (fbx_s192_L.md3 frame 5), point 46.57 13.21 -11.32 cm (open-hand check 0.75 cm off), fit rms 0.08 cm over 625 vertices <= 0.3 cm, grab 15.0 cm
// row 11 MG42: FbxWrapMG42 (fbx_s192_L.md3 frame 11), point 31.33 -0.28 6.30 cm (open-hand check 0.34 cm off), fit rms 0.18 cm over 455 vertices <= 0.3 cm, grab 15.0 cm
// row 12 MP40: FbxSupF (fbx_b1_L.md3 frame 1), point 45.23 2.85 6.90 cm (open-hand check 1.22 cm off), fit rms 0.19 cm over 438 vertices <= 0.3 cm, grab 15.0 cm
// row 13 Minigun: FbxSupMini (fbx_r4_Minigun_bar_L.md3 frame 0), point 37.91 22.58 8.98 cm (open-hand check 1.66 cm off), fit rms 0.28 cm over 287 vertices <= 0.3 cm, grab 15.0 cm
// row 14 NukeLauncher: FbxWrapNukeLauncher (fbx_s192_L.md3 frame 13), point 20.59 7.91 1.23 cm (open-hand check 0.48 cm off), fit rms 0.38 cm over 249 vertices <= 0.3 cm, grab 12.4 cm
// row 15 Plasma_Gun: FbxWrapPlasmaGun (fbx_s192_L.md3 frame 8), point 45.47 8.10 -3.37 cm (open-hand check 0.34 cm off), fit rms 0.06 cm over 617 vertices <= 0.3 cm, grab 15.0 cm
// row 16 RailGun: FbxWrapRailGun (fbx_s192_L.md3 frame 9), point 46.38 6.82 -1.17 cm (open-hand check 1.23 cm off), fit rms 0.50 cm over 113 vertices <= 0.3 cm, grab 15.0 cm
// row 18 Rifle: FbxWrapRifle (fbx_s192_L.md3 frame 3), point 44.04 6.13 1.07 cm (open-hand check 0.31 cm off), fit rms 0.45 cm over 134 vertices <= 0.3 cm, grab 15.0 cm
// row 19 Rocket_Launcher: FbxWrapRL (fbx_s192_L.md3 frame 7), point 25.26 -2.02 10.89 cm (open-hand check 1.54 cm off), fit rms 0.24 cm over 342 vertices <= 0.3 cm, grab 15.0 cm
// row 20 SSG: FbxWrapSSG (fbx_s192_L.md3 frame 0), point 21.42 7.35 -7.59 cm (open-hand check 0.32 cm off), fit rms 0.42 cm over 149 vertices <= 0.3 cm, grab 12.5 cm
// row 21 Shot_Gun: FbxWrapShotGun (fbx_s192_L.md3 frame 1), point 43.25 8.04 -3.85 cm (open-hand check 0.38 cm off), fit rms 0.09 cm over 746 vertices <= 0.3 cm, grab 15.0 cm
// row 22 Sniper: FbxWrapSniper (fbx_s192_L.md3 frame 10), point 32.68 4.31 3.96 cm (open-hand check 0.08 cm off), fit rms 0.21 cm over 391 vertices <= 0.3 cm, grab 15.0 cm
// row 23 Unmaker: FbxWrapUnmaker (fbx_s192_L.md3 frame 16), point 31.64 4.55 -1.21 cm (open-hand check 0.09 cm off), fit rms 0.44 cm over 214 vertices <= 0.3 cm, grab 15.0 cm
// row 27 Machinegun: FbxWrapMachinegun (fbx_s192_L.md3 frame 12), point 42.03 3.49 -3.07 cm (open-hand check 0.16 cm off), fit rms 0.19 cm over 438 vertices <= 0.3 cm, grab 15.0 cm
	const ROWS = 28;
	clearscope static bool Gun(int i)
	{
		static const int v[] = { 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1 };
		return i > 0 && i < ROWS && v[i] != 0;
	}
	// the support point, cm F L U in the main controller's frame
	clearscope static Vector3 Support(int i)
	{
		static const double x[] = { 0.00, 44.86, 21.32, 22.49, 0.00, 31.82, 42.06, 0.00, 27.44, 30.82, 46.57, 31.33, 45.23, 37.91, 20.59, 45.47, 46.38, 0.00, 44.04, 25.26, 21.42, 43.25, 32.68, 31.64, 0.00, 0.00, 0.00, 42.03 };
		static const double y[] = { 0.00, 9.48, 8.92, 8.72, 0.00, 0.76, 8.85, 0.00, 9.38, 6.95, 13.21, -0.28, 2.85, 22.58, 7.91, 8.10, 6.82, 0.00, 6.13, -2.02, 7.35, 8.04, 4.31, 4.55, 0.00, 0.00, 0.00, 3.49 };
		static const double z[] = { 0.00, -8.63, -1.20, -1.72, 0.00, -4.60, 0.52, 0.00, -9.60, -11.05, -11.32, 6.30, 6.90, 8.98, 1.23, -3.37, -1.17, 0.00, 1.07, 10.89, -7.59, -3.85, 3.96, -1.21, 0.00, 0.00, 0.00, -3.07 };
		return Gun(i) ? (x[i], y[i], z[i]) : (0, 0, 0);
	}
	// the palm within this of Support at the grip's press: two hands on the gun (cm)
	clearscope static double Grab(int i)
	{
		static const double v[] = { 0.0, 15.0, 12.8, 13.2, 0.0, 15.0, 15.0, 0.0, 15.0, 15.0, 15.0, 15.0, 15.0, 15.0, 12.4, 15.0, 15.0, 0.0, 15.0, 15.0, 12.5, 15.0, 15.0, 15.0, 0.0, 0.0, 0.0, 15.0 };
		return Gun(i) ? v[i] : 0;
	}
	// how much of the turn from the barrel line onto the two-hand line the shots take (1 = all of it, as the Rifle test)
	clearscope static double Steer(int i)
	{
		static const double v[] = { 0.00, 1.00, 1.00, 1.00, 0.00, 1.00, 1.00, 0.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.00, 0.00, 0.00, 1.00 };
		return Gun(i) ? v[i] : 0;
	}
	// 2.0.3m: where the gun model turns (Weapon.BobPivot3D) so that it turns about the main controller: the controller's origin in
	// the gun's MODELDEF turn space, parsed from its block (vr_3dweaponOffset 0); and the same for the hand meshes
	//   row 1 AssaultShotgun: MODELDEF.bd.txt models/bd/AssaultShotgun (115 frames) Scale [-1.0, 1.0, 1.0] Offset [-4.701, -4.805, -12.031], pivot -4.701 7.031 -25.195 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 2 BFG10k: MODELDEF.bd.txt models/bd/BFG (22 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.826, -2.653, -0.272], pivot -0.826 -4.728 -27.347 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 3 BIG_FUCKING_GUN: MODELDEF.bd.txt models/bd/BFG (39 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.338, -2.964, -0.782], pivot -0.338 -4.218 -27.036 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 5 BrutalSMG: MODELDEF.bd.txt models/bd/BrutalSMG (85 frames) Scale [-1.0, 1.0, 1.0] Offset [0.908, -4.56, -3.413], pivot 0.908 -1.587 -25.440 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 6 Devastator: MODELDEF.bd.txt models/bd/Sidewinder (26 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.518, -15.473, 3.456], pivot -0.518 -8.456 -14.527 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 8 GrenadeLauncher: MODELDEF.bd.txt models/bd/M79 (102 frames) Scale [-1.0, 1.0, 1.0] Offset [-4.954, -4.624, -14.013], pivot -4.954 9.013 -25.376 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 9 HellishMissileLauncher: MODELDEF.bd.txt models/bd/HellishMissile (34 frames) Scale [-1.0, 1.0, 1.0] Offset [3.61, -7.537, 2.891], pivot 3.610 -7.891 -22.463 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 10 IncendiaryLauncher: MODELDEF.bd.txt models/bd/M32 (2 frames) Scale [-0.62, 0.62, 0.62] Offset [-8.579, -35.927, -12.45], pivot -13.837 12.016 9.560
	//   row 11 MG42: MODELDEF.bd.txt models/bd/HitlersBuzzsaw (21 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.73, -2.859, -0.442], pivot -0.730 -4.558 -27.141 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 12 MP40: MODELDEF.bd.txt models/bd/MP40 (121 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.982, -4.47, -2.213], pivot -0.982 -2.787 -25.530 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 13 Minigun: MODELDEF.bd.txt models/bd/Minigun (107 frames) Scale [-1.0, 1.0, 1.0] Offset [-1.156, -5.106, -1.923], pivot -1.156 -3.077 -24.894 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 14 NukeLauncher: MODELDEF.bd.txt models/bd/Nuker (25 frames) Scale [-1.1, 1.1, 1.1] Offset [0.118, -2.391, 4.448], pivot 0.107 -8.589 -25.099
	//   row 15 Plasma_Gun: MODELDEF.bd.txt models/bd/Plasma_Gun (95 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.978, -4.369, -0.265], pivot -0.978 -4.735 -25.631 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 16 RailGun: MODELDEF.bd.txt models/bd/RailGun (110 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.895, -5.099, -1.747], pivot -0.895 -3.253 -24.901 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 18 Rifle: MODELDEF.bd.txt models/bd/Rifle (318 frames) Scale [-1.0, 1.0, 1.0] Offset [0.348, -5.912, -1.812], pivot 0.348 -3.188 -24.088 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 19 Rocket_Launcher: MODELDEF.bd.txt models/bd/RPG (136 frames) Scale [-1.0, 1.0, 1.0] Offset [0.259, -4.608, 0.657], pivot 0.259 -5.657 -25.392 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 20 SSG: MODELDEF.bd.txt models/bd/SSG (147 frames) Scale [-1.0, 1.0, 1.0] Offset [-3.813, -3.959, -12.773], pivot -3.813 7.773 -26.041 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 21 Shot_Gun: MODELDEF.bd.txt models/bd/ShotGun (99 frames) Scale [-1.0, 1.0, 1.0] Offset [-3.502, -4.257, -8.973], pivot -3.502 3.973 -25.743 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 22 Sniper: MODELDEF.rsr models/bd/XM21 (79 frames) Scale [-10.485, 10.485, 10.485] Offset [-4.31, -51.099, -4.224], pivot -0.411 -0.074 2.012
	//   row 23 Unmaker: MODELDEF.bd.txt models/bd/Unmaker (40 frames) Scale [-1.0, 1.0, 1.0] Offset [1.308, -6.492, 0.083], pivot 1.308 -5.083 -23.508 (gunmoves.zs Pivot agrees to 0.000 cm)
	//   row 27 Machinegun: MODELDEF.bd.txt models/bd/Machinegun (37 frames) Scale [-1.0, 1.0, 1.0] Offset [-0.612, -3.967, -2.037], pivot -0.612 -2.963 -26.033 (gunmoves.zs Pivot agrees to 21.566 cm)
	clearscope static Vector3 Pivot(int i)
	{
		static const double x[] = { 0.000, -4.701, -0.826, -0.338, 0.000, 0.908, -0.518, 0.000, -4.954, 3.610, -13.837, -0.730, -0.982, -1.156, 0.107, -0.978, -0.895, 0.000, 0.348, 0.259, -3.813, -3.502, -0.411, 1.308, 0.000, 0.000, 0.000, -0.612 };
		static const double y[] = { 0.000, 7.031, -4.728, -4.218, 0.000, -1.587, -8.456, 0.000, 9.013, -7.891, 12.016, -4.558, -2.787, -3.077, -8.589, -4.735, -3.253, 0.000, -3.188, -5.657, 7.773, 3.973, -0.074, -5.083, 0.000, 0.000, 0.000, -2.963 };
		static const double z[] = { 0.000, -25.195, -27.347, -27.036, 0.000, -25.440, -14.527, 0.000, -25.376, -22.463, 9.560, -27.141, -25.530, -24.894, -25.099, -25.631, -24.901, 0.000, -24.088, -25.392, -26.041, -25.743, 2.012, -23.508, 0.000, 0.000, 0.000, -26.033 };
		return Gun(i) ? (x[i], y[i], z[i]) : (0, 0, 0);
	}
	clearscope static Vector3 HandGrip() { return (0.000, 5.000, -6.000); }	// hook.PL {'scale': [-1.0, 1.0, 1.0], 'off': [0.0, -24.0, -10.0]}
// twohand-table END
}

class RSQ_TwoHand : EventHandler
{
	bool offGrip[MAXPLAYERS];
	bool gripPrev[MAXPLAYERS];
	int held[MAXPLAYERS];	// the hand-table row two hands are on, 0 none
	int retake[MAXPLAYERS];	// the row a reload took the hand from while the grip stayed held, 0 none
	// 2.0.3m: the drawn turn
	const MAXTURN = 60.0;	// degrees, either way
	const EASE = 0.5;		// of the gap to the target, a tic
	const SETTLE = 0.02;	// degrees: below this, released, the turn is over
	double turnYaw[MAXPLAYERS], turnPitch[MAXPLAYERS];	// degrees, + left / + up, the turn written into the layer this tic
	double addX[MAXPLAYERS], addY[MAXPLAYERS];		// what we added to the weapon layer's x / y
	double wroteX[MAXPLAYERS], wroteY[MAXPLAYERS];	// the layer's x / y as we left them
	Weapon turnedGun[MAXPLAYERS];		// the weapon whose layer and BobPivot3D are ours, null none
	Vector3 savedPivot[MAXPLAYERS];	// its own BobPivot3D, given back when the turn is over

	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.Name == "rsr_grip" && e.Player >= 0 && e.Player < MAXPLAYERS)
			offGrip[e.Player] = e.Args[0] != 0;
	}

	static bool Debug(PlayerInfo p)
	{
		return p && RSR.PlayerInt(p, 'rsq_twohand_debug', 0) != 0;
	}

	static bool EngineTwoHanded()
	{
		let cv = CVar.FindCVar('vr_two_handed_weapons');
		return cv && cv.GetBool();
	}

	// the gun's row when Two-Hand Aim applies to it, else 0
	static int Row(Weapon w)
	{
		int i = w ? RSQ_HandTable.Index(w) : 0;
		return RSQ_TwoHandTable.Gun(i) ? i : 0;
	}

	// everything but the grip: may two hands go on the gun in hand now
	static bool Allowed(PlayerPawn mo)
	{
		if (!mo || !mo.player || mo.player.playerstate != PST_LIVE || !RSVR_VRHand.InVR(mo))
			return false;
		let p = mo.player;
		if (RSR.PlayerInt(p, 'rsq_twohand_rifle', 0) == 0 || EngineTwoHanded() || RSVR_VRHand.Steadied(mo))
			return false;
		if (Row(p.ReadyWeapon) <= 0 || p.PendingWeapon != WP_NOCHANGE)
			return false;
		let off = p.OffhandWeapon;
		if (off && !(off is 'RSQ_Hands'))
			return false;	// a gun in the off hand (rsq/dualhands.zs)
		int n = mo.PlayerNumber();
		let rs = RSR_ReloadHandler.StateOf(mo);
		if (rs && rs.phase != RSR.IDLE)
			return false;
		if (RSB_Handler.Busy(n) || RSK_M203Handler.Busy(n))
			return false;	// (RSP_Handler.Busy: a pump stroke keeps the hand on the gun; its shell loading shows in FreeHand)
		if (RSR_ReloadHandler.FreeHand(mo) != "" || RSP_Handler.FreeHand(mo) != "" || RSB_Handler.FreeHand(mo) != ""
			|| RSK_M203Handler.FreeHand(mo) != "")
			return false;	// the same "a reload has the hand" test rsq/hands.zs makes
		return true;
	}

	// the off palm, cm in the MAIN controller's frame (F L U), as rsr/vreload.zs RSR_State.OffPoint(RSR.PalmGrab())
	static Vector3 PalmInMain(PlayerPawn mo)
	{
		double ps = mo.Level.pixelstretch;
		if (ps <= 0)
			ps = 1.2;
		let cv = CVar.FindCVar('vr_vunits_per_meter');
		double vu = cv ? cv.GetFloat() : 34;
		if (vu <= 0)
			vu = 34;
		Vector3 F = RSVR_VRHand.HandDir(mo, 0, 0, ps);
		Vector3 L = RSVR_VRHand.HandDir(mo, 90, 0, ps);
		Vector3 U = RSVR_VRHand.HandDir(mo, 0, 90, ps);
		Vector3 oF = RSVR_VRHand.OffDir(mo, 0, 0, ps);
		Vector3 oL = RSVR_VRHand.OffDir(mo, 90, 0, ps);
		Vector3 oU = RSVR_VRHand.OffDir(mo, 0, 90, ps);
		Vector3 w = RSVR_VRHand.OffPos(mo) - RSVR_VRHand.HandPos(mo);
		w.z *= ps;
		w *= 100.0 / vu;
		Vector3 pg = RSR.PalmGrab();
		Vector3 pw = oF * pg.x + oL * pg.y + oU * pg.z;
		return (w dot F + pw dot F, w dot L + pw dot L, w dot U + pw dot U);
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			bool g = offGrip[n];
			bool edge = g && !gripPrev[n];
			gripPrev[n] = g;
			if (!playeringame[n] || !players[n].mo)
			{
				held[n] = retake[n] = 0;
				continue;
			}
			let mo = PlayerPawn(players[n].mo);
			int row = Row(players[n].ReadyWeapon);
			int had = mo.CountInv('RSQ_TwoHandAimed') > 0 ? held[n] : 0;
			bool ok = Allowed(mo);
			int on = had > 0 && had == row && g && ok ? had : 0;
			if (!g || row != retake[n])
				retake[n] = 0;
			if (had > 0 && had == row && g && !ok)
				retake[n] = row;	// a reload (or the like) took the hand; the grip is still held
			double d = -1;
			bool back = retake[n] > 0 && ok;
			if (had == 0 && (edge || back) && ok)
			{
				d = (PalmInMain(mo) - RSQ_TwoHandTable.Support(row)).Length();
				if (d < RSQ_TwoHandTable.Grab(row))
				{
					on = row;
					retake[n] = 0;
				}
			}
			held[n] = on;
			if ((on > 0) != (mo.CountInv('RSQ_TwoHandAimed') > 0))
				mo.SetInventory('RSQ_TwoHandAimed', on > 0 ? 1 : 0);
			if (Debug(mo.player) && (on != had || edge) && row > 0 && (edge || on > 0 || had > 0))
				Console.Printf("twh t%d %s (row %d) grip %s, palm %.1f cm from the support point (grab %.1f): %s", Level.maptime,
					players[n].ReadyWeapon.GetClassName(), row, edge ? "pressed" : g ? "held" : "released",
					d >= 0 ? d : (PalmInMain(mo) - RSQ_TwoHandTable.Support(row)).Length(), RSQ_TwoHandTable.Grab(row),
					on > 0 ? (back && !edge ? "two hands back on the gun" : "two hands on the gun") : had > 0 ? (retake[n] > 0 ? "the hand is busy (grip held)" : "let go") : "not on the gun");
			TurnGun(mo, n, on);
		}
	}

	// the player's (-vr_3dweaponOffsetX, Y, Z): models.cpp RenderHUDModel translates every HUD model by it after the MODELDEF
	// offsets and before the turn, so a turn point in that space moves back by it
	clearscope static Vector3 VrShift()
	{
		let cx = CVar.FindCVar('vr_3dweaponOffsetX');
		let cy = CVar.FindCVar('vr_3dweaponOffsetY');
		let cz = CVar.FindCVar('vr_3dweaponOffsetZ');
		return (cx ? -cx.GetFloat() : 0, cy ? cy.GetFloat() : 0, cz ? cz.GetFloat() : 0);
	}

	// the turn about the main controller (pitch about L, then yaw about U) that takes the support point's direction onto
	// the off palm's (degrees, + left, + up), times the gun's Steer, clamped
	static double, double Target(PlayerPawn mo, int row)
	{
		Vector3 sp = RSQ_TwoHandTable.Support(row), pm = PalmInMain(mo);
		if (sp.Length() < 1 || pm.Length() < 1)
			return 0, 0;
		Vector3 s = sp.Unit(), o = pm.Unit();
		// pitch first (about L): S's height onto P's
		double r = sqrt(s.x * s.x + s.z * s.z);
		if (r < 1e-6)
			return 0, 0;
		double b = asin(clamp(o.z / r, -1, 1)) - atan2(s.z, s.x);
		double f = s.x * cos(b) - s.z * sin(b);
		// then yaw (about U)
		double a = atan2(o.y, o.x) - atan2(s.y, f);
		while (a > 180)
			a -= 360;
		while (a < -180)
			a += 360;
		double k = RSQ_TwoHandTable.Steer(row);
		return clamp(a * k, -MAXTURN, MAXTURN), clamp(b * k, -MAXTURN, MAXTURN);
	}

	// v (F L U) turned by pitch b (+ up, about L) and then yaw a (+ left, about U): the drawn turn
	clearscope static Vector3 Rotate(Vector3 v, double a, double b)
	{
		double cb = cos(b), sb = sin(b), ca = cos(a), sa = sin(a);
		double f = v.x * cb - v.z * sb, u = v.x * sb + v.z * cb;
		return (f * ca - v.y * sa, f * sa + v.y * ca, u);
	}

	// THE DRAWN TURN, each tic: eased toward the target while two hands are on the gun, home when not; added to the
	// weapon layer's x / y about the controller (BobPivot3D); given back when it is over or the gun changes.
	void TurnGun(PlayerPawn mo, int n, int on)
	{
		let p = mo.player;
		let w = p.ReadyWeapon;
		if (turnedGun[n] && turnedGun[n] != w)
			EndTurn(p, n);	// another gun came up: the old one's turn is dropped at once
		double ty = 0, tp = 0;
		if (on > 0)
			[ty, tp] = Target(mo, on);
		turnYaw[n] += (ty - turnYaw[n]) * EASE;
		turnPitch[n] += (tp - turnPitch[n]) * EASE;
		if (on <= 0 && abs(turnYaw[n]) < SETTLE && abs(turnPitch[n]) < SETTLE)
		{
			if (turnedGun[n] || addX[n] != 0 || addY[n] != 0)
				EndTurn(p, n);
			turnYaw[n] = turnPitch[n] = 0;
			return;
		}
		let psp = p.FindPSprite(PSP_WEAPON);
		int row = Row(w);
		if (!psp || row <= 0)
		{
			EndTurn(p, n);
			return;
		}
		// the weapon did not rewrite its layer since our last write: take that turn back out first
		if (turnedGun[n] == w && psp.x == wroteX[n] && psp.y == wroteY[n])
		{
			psp.x -= addX[n];
			psp.y -= addY[n];
		}
		if (turnedGun[n] != w)
		{
			savedPivot[n] = w.BobPivot3D;
			turnedGun[n] = w;
		}
		w.BobPivot3D = RSQ_TwoHandTable.Pivot(row) - VrShift();
		// hw_weapon.cpp:108: yaw (right +) = x / 4, pitch (up +) = (y - WEAPONTOP) / -4
		addX[n] = -4.0 * turnYaw[n];
		addY[n] = -4.0 * turnPitch[n];
		psp.x += addX[n];
		psp.y += addY[n];
		wroteX[n] = psp.x;
		wroteY[n] = psp.y;
	}

	void EndTurn(PlayerInfo p, int n)
	{
		let w = turnedGun[n];
		if (w)
		{
			w.BobPivot3D = savedPivot[n];
			let psp = p.FindPSprite(PSP_WEAPON);
			if (psp && psp.Caller == w && psp.x == wroteX[n] && psp.y == wroteY[n])
			{
				psp.x -= addX[n];
				psp.y -= addY[n];
			}
		}
		turnedGun[n] = null;
		addX[n] = addY[n] = 0;
		turnYaw[n] = turnPitch[n] = 0;
	}

	// the turn drawn on the gun w of player mo now (degrees, + left, + up), or false
	clearscope static double, double, bool Turned(Actor mo, Weapon w)
	{
		if (!mo || !mo.player || !w)
			return 0, 0, false;
		let h = RSQ_TwoHand(EventHandler.Find('RSQ_TwoHand'));
		int n = mo.PlayerNumber();
		if (!h || n < 0 || n >= MAXPLAYERS || h.turnedGun[n] != w || (h.turnYaw[n] == 0 && h.turnPitch[n] == 0))
			return 0, 0, false;
		return h.turnYaw[n], h.turnPitch[n], true;
	}

	// a point or direction on the gun in hand (F L U, the main controller's frame) where the turned gun now draws it
	// (muzzle.zs: the muzzle; scope.zs / scope_real.zs: the lens, its axis and its up)
	clearscope static Vector3 OnGun(Actor mo, Vector3 v)
	{
		double a, b;
		bool t;
		[a, b, t] = Turned(mo, mo && mo.player ? mo.player.ReadyWeapon : null);
		return t ? Rotate(v, a, b) : v;
	}

	// rsq/hands.zs: the point the hands drawn on the gun turn about with it, in the hand meshes' turn space; while the gun
	// is turned by us it turns about the controller (HandGrip), otherwise about its own origin (gunmoves.zs Pivot)
	clearscope static Vector3, bool HandPivot(PlayerPawn mo)
	{
		let w = mo && mo.player ? mo.player.ReadyWeapon : null;
		let h = RSQ_TwoHand(EventHandler.Find('RSQ_TwoHand'));
		int n = mo ? mo.PlayerNumber() : -1;
		if (!w || !h || n < 0 || n >= MAXPLAYERS || h.turnedGun[n] != w)
			return (0, 0, 0), false;
		return RSQ_TwoHandTable.HandGrip() - VrShift(), true;
	}

	// rsq/hands.zs: a layer the pack draws ON the gun (the pump's fore-end, bolt and shells, the break-open and M203 parts,
	// a magazine in the well), placed by RSQ_Hands.ModifyBobLayer3D in the gun's own MODELDEF space with no turn of its own
	// from the gun layer: while Two-Hand Aim turns the gun, the gun layer's drawn turn (its interpolated x / y, the same
	// numbers the renderer turns the gun by, hw_weapon.cpp:108) about the gun's BobPivot3D is put in front of the layer's
	// own (t, r), so the part stays on the turned gun. RenderHUDModel draws a point p of the layer at R (p + t) (pivot 0);
	// turned by Q about c that is (QR) (p + t + (QR)^-1 (c - Qc)).
	ui static Vector3, Vector3 OnGunLayer(PlayerPawn mo, int layer, Vector3 t, Vector3 r, double ticfrac)
	{
		Vector3 hp;
		bool on;
		[hp, on] = HandPivot(mo);
		if (!on)
			return t, r;
		PSprite gp, lp;
		for (let s = mo.player.psprites; s; s = s.Next)
		{
			if (s.ID == PSP_WEAPON)
				gp = s;
			else if (s.ID == layer)
				lp = s;
		}
		if (!gp || !lp || lp.Caller == mo.player.OffhandWeapon || lp.Caller == mo.player.ReadyWeapon)
			return t, r;	// a layer on the off controller, or one of the gun's own (it turns with the gun layer already)
		Vector2 g = RSQ_Hands.LayerOffset(gp, ticfrac);
		Vector3 q0, q1, q2, r0, r1, r2, n0, n1, n2;
		[q0, q1, q2] = RSQ_Turn.Rows((g.x / 4, (g.y - 32) / -4, 0));
		[r0, r1, r2] = RSQ_Turn.Rows(r);
		[n0, n1, n2] = RSQ_Turn.Mul(q0, q1, q2, r0, r1, r2);
		Vector3 c = mo.player.ReadyWeapon.BobPivot3D;
		Vector3 qc = (q0 dot c, q1 dot c, q2 dot c);
		return t + RSQ_Turn.Back(n0, n1, n2, c - qc), RSQ_Turn.Angles(n0, n1, n2);
	}

	// muzzle.zs AimOffsetMo: the line the drawn gun's barrel takes now (F L U, unit), or false when the gun is not turned.
	// Exactly the turn written into the weapon layer (TurnGun): shots never leave the line the gun is drawn along.
	static Vector3, bool Aim(PlayerPawn mo, Weapon w, Vector3 bore)
	{
		if (!mo || !mo.player || w != mo.player.ReadyWeapon || !mo.OverrideAttackPosDir)
			return bore, false;	// the frames need a live controller (vrhand.zs)
		double a, b;
		bool tn;
		[a, b, tn] = Turned(mo, w);
		if (!tn)
			return bore, false;
		Vector3 t = Rotate(bore, a, b).Unit();
		if (Debug(mo.player))
		{
			int row = Row(w);
			Vector3 sp = RSQ_TwoHandTable.Support(row), pm = PalmInMain(mo);
			Console.Printf("twh shot t%d %s (row %d) turn yaw %.2f pitch %.2f, line %.5f %.5f %.5f, %.2f deg off the plain line (palm %.1f %.1f %.1f cm, support %.1f %.1f %.1f)",
				mo.Level.maptime, w.GetClassName(), row, a, b, t.x, t.y, t.z, acos(clamp(t dot bore, -1, 1)),
				pm.x, pm.y, pm.z, sp.x, sp.y, sp.z);
		}
		return t, true;
	}
}
