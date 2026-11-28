// lane_c R6 (owner, 2026-10-27): in VR the Flamethrower2's flame starts at the DRAWN spout tip. BD22's fire states
// (brutal22test6 Flamethrower.dec, not ours to edit there) spawn FlamethrowerProjectileNew/New2/New3 at the
// controller (AttackPos, p_mobj.cpp OverrideAttackPosDir) plus BD22's own offsets; the drawn spout is ~95 cm ahead.
// This only MOVES where each flame projectile starts, once, the tic after it is spawned: timing, damage, speed and
// direction stay BD22's. If the spout position is blocked (inside a wall), the projectile is left where BD22 put it.
// Tip: the drawn spout tip in the weapon controller's frame, cm (F, L, U), measured on the mesh as drawn (round 6).
class RSA_FlameSpout : EventHandler
{
	Array<Actor> pend;
	const TIPF = %TIPF%;
	const TIPL = %TIPL%;
	const TIPU = %TIPU%;

	static PlayerPawn Shooter(Actor c)
	{
		return c ? PlayerPawn(c.target) : null;
	}

	override void WorldThingSpawned(WorldEvent e)
	{
		let c = e.Thing;
		if (!c)
			return;
		Name n = c.GetClassName();
		if (n != 'FlamethrowerProjectileNew' && n != 'FlamethrowerProjectileNew2' && n != 'FlamethrowerProjectileNew3')
			return;
		let mo = Shooter(c);
		if (!mo || !mo.player || !RSVR_VRHand.InVR(mo) || !(mo.player.ReadyWeapon is 'Flamethrower2'))
			return;
		pend.Push(c);
	}

	override void WorldTick()
	{
		for (int i = 0; i < pend.Size(); i++)
		{
			let c = pend[i];
			if (c)
				Place(c);
		}
		pend.Clear();
	}

	void Place(Actor c)
	{
		let mo = Shooter(c);
		if (!mo || !mo.player)
			return;
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
		Vector3 w3 = (F * TIPF + L * TIPL + U * TIPU) * (vu / 100.0);
		w3.z /= ps;
		Vector3 tip = RSVR_VRHand.HandPos(mo) + w3;
		Vector3 was = c.pos;
		Vector3 to = tip + c.vel * c.GetAge();
		c.SetOrigin(to, false);
		if (!c.TestMobjLocation())
			c.SetOrigin(was, false);
		let lg = CVar.FindCVar('lanec_flamelog');
		if (lg && lg.GetInt() != 0)
		{
			Vector3 back = c.pos - c.vel * c.GetAge();
			Vector3 bdstart = was - c.vel * c.GetAge();
			Console.Printf("LANEC FLAME t %d %s age %d start-to-tip %.2f cm (BD22 start was %.1f cm from the tip) blocked %d", Level.maptime, c.GetClassName(), c.GetAge(), (back - tip).Length() * 100.0 / vu, (bdstart - tip).Length() * 100.0 / vu, c.pos == was ? 1 : 0);
		}
	}
}
