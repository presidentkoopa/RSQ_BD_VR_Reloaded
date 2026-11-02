// RS VR melee -- where the weapon hand is (QuestZDoom 17.3 fields, read only).
//
// QZD sets these on the player every frame (hw_openxrdevice.cpp / gl_openvr.cpp):
//   AttackPos            the weapon controller, world position
//   AttackDir(mo, a, p)  a direction in the controller's own frame, returned as
//                        (angle, pitch, 0); relative yaw 0 / pitch 0 = forward,
//                        yaw +90 = left, pitch +90 = up (MapWeaponDir)
//   OffhandPos           the other controller, world position
//   OverrideAttackPosDir true while playing in VR
// The held model hangs off the same transform (models.cpp RenderHUDModel), so a
// point of the model can be placed in the world exactly where it is drawn.
// This is the only file that touches QZD's own fields (OffDir, Buttons, Steadied and
// SteadyGap added for rsr/vreload.zs; the headless test stands in for this file).

class RSVR_VRHand play
{
	// playing in VR with the weapon following the controller
	static bool InVR(PlayerPawn mo)
	{
		return mo && mo.player && mo.player.PlayInVR && mo.OverrideAttackPosDir;
	}

	// the weapon controller, world position
	static Vector3 HandPos(PlayerPawn mo)
	{
		return mo.AttackPos;
	}

	// the other controller, world position (rsq/reload.zs, rsq/hands.zs)
	static Vector3 OffPos(PlayerPawn mo)
	{
		return mo.OffhandPos;
	}

	// unit vector of a direction in the controller's frame (yaw 0 pitch 0 =
	// forward, yaw 90 = left, pitch 90 = up), with the hand transform's vertical
	// squash (1 / pixelstretch) taken back out
	static Vector3 HandDir(PlayerPawn mo, double yaw, double pitch, double ps)
	{
		// 2026-10-27: the engine sets the pointer behind AttackDir only while it renders a frame
		// (hw_vrmodes.cpp). A pawn restored from a save thinks before its first frame, and an
		// unguarded call there segfaulted (save/load crash). Only call it when it is live.
		Vector3 ap = mo.OverrideAttackPosDir ? mo.AttackDir(mo, mo.angle + yaw, mo.pitch + pitch)
			: (mo.angle + yaw, mo.pitch + pitch, 0);
		double cp = cos(ap.y);
		Vector3 v = (cp * cos(ap.x), cp * sin(ap.x), -sin(ap.y) * ps);
		double l = v.Length();
		if (l <= 0)
			return (1, 0, 0);
		return v / l;
	}

	// the same for the off controller (rsr/vreload.zs). The engine mirrors the left
	// controller's frame (hw_vrmodes GetWeaponTransform); OffhandDir and AttackDir
	// include that, so these are the axes the layers on each hand are drawn in.
	static Vector3 OffDir(PlayerPawn mo, double yaw, double pitch, double ps)
	{
		// 2026-10-27: the engine sets the pointer behind OffhandDir only while it renders a frame
		// (hw_vrmodes.cpp). A pawn restored from a save thinks before its first frame, and an
		// unguarded call there segfaulted (save/load crash). Only call it when it is live.
		Vector3 ap = mo.OverrideAttackPosDir ? mo.OffhandDir(mo, mo.angle + yaw, mo.pitch + pitch)
			: (mo.angle + yaw, mo.pitch + pitch, 0);
		double cp = cos(ap.y);
		Vector3 v = (cp * cos(ap.x), cp * sin(ap.x), -sin(ap.y) * ps);
		double l = v.Length();
		if (l <= 0)
			return (1, 0, 0);
		return v / l;
	}

	// this tic's usercmd buttons (BT_OFFHANDATTACK: the off-hand trigger)
	static int Buttons(PlayerPawn mo)
	{
		return mo.player.cmd.buttons;
	}

	// the engine is steadying the gun with both hands (an off grip pressed within 50 cm
	// of the gun controller while vr_two_handed_weapons is on; p_pspr.cpp sets the flag)
	static bool Steadied(PlayerPawn mo)
	{
		return (mo.player.WeaponState & WF_TWOHANDSTABILIZED) != 0;
	}

	// F11: two hands on the weapon as the player SEES it. Guns: the engine's steadying. The axe
	// and the sword: RSVR_MeleeTwo (melee.zs), the off grip held near them -- the engine's
	// steadying is switched off while they are in hand, so one controller still drives them.
	static bool TwoHands(PlayerPawn mo)
	{
		return mo && mo.player && (Steadied(mo) || mo.CountInv('RSVR_MeleeTwo') > 0);
	}

	// the distance between the two controllers, real cm: the engine's own steadying
	// distance (OffhandPos - AttackPos; heights are divided by pixelstretch,
	// hw_openxrdevice.cpp, so they are multiplied back)
	static double SteadyGap(PlayerPawn mo)
	{
		double ps = mo.Level.pixelstretch;
		if (ps <= 0)
			ps = 1.2;
		let cv = CVar.FindCVar('vr_vunits_per_meter');
		double vu = cv ? cv.GetFloat() : 34;
		if (vu <= 0)
			vu = 34;
		Vector3 w = mo.OffhandPos - mo.AttackPos;
		w.z *= ps;
		return w.Length() * 100.0 / vu;
	}
}
