// twohand.zs (2.0.3k, owner-approved proof 2026-11-02): TWO-HAND AIM, Rifle only, our own (script), OFF by default.
// Rig only, not headset-confirmed.
//
// WHAT IT DOES. With "Two-Hand Aim (Rifle, test)" on (rsq_twohand_rifle) and the engine's own two-handing OFF
// (vr_two_handed_weapons 0), bring the off hand's palm to the Rifle's handguard and press the off grip: the support
// hand shows on the gun (RSVR_VRHand.TwoHands) and every Rifle shot goes down the TWO-HAND LINE instead of the plain
// bore. Let go of the grip and the shots go down the plain bore again.
//
// THE TWO-HAND LINE. In the main controller's frame (F L U, cm) the support hand's place on the gun is the hand table's
// SupportPoint (row 18, the Rifle: (33.6, 3.3, 8.0) cm, measured off the fitted support hand, rsq/handtable.zs). The
// line is the plain bore (muzzle.zs Bore: 0.99602 0.06710 0.05866) turned by the rotation, about the main controller,
// that takes SupportPoint onto where the off palm is now. The gun hand stays the pivot; the roll is the main
// controller's (the shot's direction is handed to the engine as a yaw / pitch in the controller's frame, AimOffset).
// The shot still STARTS at the drawn muzzle (muzzle.zs Where); the drawn gun is not turned (see README).
//
// THE PALM. The off controller's origin is not the palm: the palm is RSR.PalmGrab() (-1.5, 2.0, -4.5) cm in the off
// controller's frame, the same point every reload grab measures from (rsr/vreload.zs). The grab takes the palm within
// GRAB_CM of SupportPoint.
//
// WHEN. A rising edge of the off grip (rsr_grip, the synchronised event vreload.zs sends) with the palm within
// GRAB_CM latches; letting go of the grip unlatches. Never: with vr_two_handed_weapons on (the engine two-hands; ours
// stands down, the two are never applied together), with a gun in the off hand (dual wield), while a reload or the
// M203 has the off hand (a reload that starts while latched drops the latch; grab again after it).
// rsq_twohand_debug prints the latch and, for each shot, the angle between the two-hand line and the plain bore.

class RSQ_TwoHandRifle : RSVR_Token {}	// two hands on the Rifle (ours): RSVR_VRHand.TwoHands ORs it in

class RSQ_TwoHand : EventHandler
{
	const ROW = 18;			// RSQ_HandTable row of the Rifle
	const GRAB_CM = 15.0;	// the palm this close to SupportPoint at the grip's press: two hands on the gun

	bool offGrip[MAXPLAYERS];
	bool gripPrev[MAXPLAYERS];

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

	static bool IsRifle(Weapon w)
	{
		return w && w is 'Rifle' && RSQ_HandTable.Index(w) == ROW;
	}

	// everything but the grip: may two hands go on the Rifle now
	static bool Allowed(PlayerPawn mo)
	{
		if (!mo || !mo.player || mo.player.playerstate != PST_LIVE || !RSVR_VRHand.InVR(mo))
			return false;
		let p = mo.player;
		if (RSR.PlayerInt(p, 'rsq_twohand_rifle', 0) == 0 || EngineTwoHanded() || RSVR_VRHand.Steadied(mo))
			return false;
		if (!IsRifle(p.ReadyWeapon) || p.PendingWeapon != WP_NOCHANGE)
			return false;
		let off = p.OffhandWeapon;
		if (off && !(off is 'RSQ_Hands'))
			return false;	// a gun in the off hand (rsq/dualhands.zs)
		int n = mo.PlayerNumber();
		let rs = RSR_ReloadHandler.StateOf(mo);
		if (rs && rs.phase != RSR.IDLE)
			return false;
		if (RSP_Handler.Busy(n) || RSB_Handler.Busy(n) || RSK_M203Handler.Busy(n))
			return false;
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

	// the Rifle's support point, cm F L U (measured: rsq/handtable.zs SupportPoint, metres)
	static Vector3 Support()
	{
		return RSQ_HandTable.SupportPoint(ROW) * 100.0;
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			bool g = offGrip[n];
			bool edge = g && !gripPrev[n];
			gripPrev[n] = g;
			if (!playeringame[n] || !players[n].mo)
				continue;
			let mo = PlayerPawn(players[n].mo);
			bool had = mo.CountInv('RSQ_TwoHandRifle') > 0;
			bool on = had && g && Allowed(mo);
			double d = -1;
			if (!had && edge && Allowed(mo))
			{
				d = (PalmInMain(mo) - Support()).Length();
				on = d < GRAB_CM;
			}
			if (on != had)
				mo.SetInventory('RSQ_TwoHandRifle', on ? 1 : 0);
			if (Debug(mo.player) && (on != had || edge))
				Console.Printf("twh t%d grip %s, palm %.1f cm from the support point: %s", Level.maptime,
					edge ? "pressed" : g ? "held" : "released", d >= 0 ? d : (PalmInMain(mo) - Support()).Length(),
					on ? "two hands on the Rifle" : had ? "let go" : "not on the Rifle");
		}
	}

	// muzzle.zs AimOffset: the two-hand line (F L U, unit), or false when two hands are not on the gun
	static Vector3, bool Aim(PlayerPawn mo, Weapon w, Vector3 bore)
	{
		if (!mo || !mo.player || w != mo.player.ReadyWeapon || !IsRifle(w) || mo.CountInv('RSQ_TwoHandRifle') <= 0)
			return bore, false;
		if (EngineTwoHanded() || !mo.OverrideAttackPosDir)
			return bore, false;	// never both; the frames below need a live controller (vrhand.zs)
		Vector3 s = Support(), o = PalmInMain(mo);
		if (s.Length() < 1 || o.Length() < 1)
			return bore, false;
		Vector3 t = RSQ_Muzzle.Turn(bore, s.Unit(), o.Unit()).Unit();
		if (Debug(mo.player))
			Console.Printf("twh shot t%d two-hand line %.5f %.5f %.5f, %.2f deg off the plain bore (palm %.1f %.1f %.1f cm, support %.1f %.1f %.1f)",
				mo.Level.maptime, t.x, t.y, t.z, acos(clamp(t dot bore, -1, 1)), o.x, o.y, o.z, s.x, s.y, s.z);
		return t, true;
	}
}
