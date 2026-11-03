// TEST ONLY (never ships): prints the BD22 VR grenade's state (RSG_State) for the teeth pin pull rig test.
// TTP lines: every change of pin / spoon / ammo / thrown grenades, and with ttp_trace 1 every tic of a held trigger.
class TTP_Probe : EventHandler
{
	int pArmed, pSpoon, pAmmo, pNades, pFace;
	bool primed;

	override void WorldTick()
	{
		let h = RSG_Handler(EventHandler.Find('RSG_Handler'));
		let mo = players[consoleplayer].mo;
		if (!h || !mo || !h.st[consoleplayer]) return;
		let s = h.st[consoleplayer];
		class<Inventory> amc = 'GrenadeAmmo';
		int ammo = mo.CountInv(amc);
		int nades = 0;
		let it = ThinkerIterator.Create('HandGrenade');
		while (it.Next()) nades++;
		bool trig = (mo.player.cmd.buttons & BT_ATTACK) != 0;
		bool chg = !primed || s.armed != pArmed || s.spoonOff != pSpoon || ammo != pAmmo || nades != pNades;
		bool trace = CVar.GetCVar('ttp_trace', mo.player).GetInt() != 0 && trig;
		if (chg || trace)
			Console.Printf("TTP t%d trig=%d face=%.2fm faceTic=%d ready=%d | pin=%s teeth=%d ring=%d spoon=%d | ammo=%d thrownNades=%d rsg_face=%d | ready=%s vr=%d RSG_VR=%d",
				level.maptime, trig, s.FaceDist(mo), s.faceTic, s.faceReady, s.armed ? "OUT" : "in", s.teethPin, s.ringKept,
				s.spoonOff, ammo, nades, CVar.GetCVar('rsg_face', mo.player).GetInt(),
				mo.player.ReadyWeapon ? mo.player.ReadyWeapon.GetClassName() : 'none', RSVR_VRHand.InVR(mo), mo.CountInv('RSG_VR'));
		pArmed = s.armed; pSpoon = s.spoonOff; pAmmo = ammo; pNades = nades; primed = true;
	}
}
