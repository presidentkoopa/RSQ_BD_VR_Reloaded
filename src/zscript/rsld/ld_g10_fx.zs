// LD mode, G10 alerts and cosmetics (Agent B, 2026-11-06). Numbers: numbers_g10.zs (g10.rules).

// Agitating: LegenDoom's every attack runs LDAgitatingScreaming = SetMugShotState("Ouch") (LEGNDLIB.acs:207) and plays
// its effects/agitating* screams; its projectiles scatter bone casings. Owner 11-06: mechanics only, silent, until
// he picks a sound. The mechanic left is the status bar face's "Ouch" on every pull; the bone casings are a visual
// (scope Q4) and not carried.
class RSLD_Fx_Agitating : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (!s.mo) return;
		s.mo.A_SetMugshotState("Ouch");
		s.Log("mugshot Ouch (LDAgitatingScreaming); silent (owner 11-06)");
	}
}

// Stealth: "Attacks do not alert enemies at long range". LegenDoom's stealth fire states call A_AlertMonsters(64)
// instead of A_AlertMonsters and play the gun's fire sound at volume 0.1 (Shotgun.dec FireStealth). BD22's guns alert
// in their own fire states (A_AlertMonsters before the shot in the same tic, e.g. Shotgun.dec:468) and fire an
// invisible Alerter missile (RocketLauncher.dec:384, Minigun.dec:274, ...) and a DistantFireSound* echo (Tracers.dec).
// At the pull (the same tic, before any monster has looked): the sector sound alert of this player is taken back
// and LegenDoom's A_AlertMonsters(64) made instead, the Alerter missiles are removed, the far echoes stopped, and
// our gun's own fire sound turned down to 0.1 (our sound, quiet: scope 4). Again the tic after (a late Alerter).
class RSLD_Fx_Stealth : RSLD_Effect
{
	override void OnPull(RSLD_Shot s) { Quiet(s, "pull"); }
	// an Alerter / DistantFireSound* spawned after the pull began (the handler destroys it; NEEDS_B 4b)
	override bool OnAlerter(RSLD_Shot s, Actor a) { return true; }
	override void AfterPull(RSLD_Shot s) { Quiet(s, "after"); }

	override void OnMissile(RSLD_Shot s, Actor m)
	{
		double v = Num("vol");
		m.A_SoundVolume(CHAN_VOICE, v);		// a projectile's SeeSound plays on CHAN_VOICE
		m.A_SoundVolume(CHAN_BODY, v);
	}

	// LegenDoom's A_AlertMonsters(64): the sound flood that crosses only two-sided, open lines within 64 units of the
	// emitter. Measured on the QZD 17.3 rig: the engine's own A_AlertMonsters(maxdist) floods the same sectors for any
	// maxdist (MAP01 start: 32 of 211 sectors for 0, 16, 64 and 1000: /tmp/ldrig/b_alert.log), so the distance limit
	// LegenDoom asks for is applied here (scope Q: see Agent B's report).
	static int AlertWithin(Actor mo, double maxdist)
	{
		Array<int> todo;
		Array<int> seen;
		todo.Push(mo.CurSector.Index());
		while (todo.Size() > 0)
		{
			int si = todo[todo.Size() - 1];
			todo.Pop();
			if (seen.Find(si) != seen.Size()) continue;
			seen.Push(si);
			Sector sec = level.Sectors[si];
			sec.SoundTarget = mo;
			for (int i = 0; i < sec.Lines.Size(); i++)
			{
				Line ln = sec.Lines[i];
				if (!ln.sidedef[1] || !(ln.flags & Line.ML_TWOSIDED)) continue;
				Sector other = ln.frontsector == sec ? ln.backsector : ln.frontsector;
				if (!other || other == sec || seen.Find(other.Index()) != seen.Size()) continue;
				vector2 a = ln.v1.p, d = ln.delta, m = mo.pos.xy;
				double len2 = d dot d;
				double t = len2 > 0 ? clamp(((m - a) dot d) / len2, 0.0, 1.0) : 0.0;
				if ((a + d * t - m).Length() > maxdist) continue;
				vector2 c = a + d * 0.5;
				double open = min(sec.ceilingplane.ZatPoint(c), other.ceilingplane.ZatPoint(c)) - max(sec.floorplane.ZatPoint(c), other.floorplane.ZatPoint(c));
				if (open <= 0) continue;	// a closed door
				todo.Push(other.Index());
			}
		}
		return seen.Size();
	}

	void Quiet(RSLD_Shot s, string when)
	{
		let mo = s.mo;
		if (!mo) return;
		int cleared = 0;
		for (int i = 0; i < level.Sectors.Size(); i++)
		{
			let sec = level.Sectors[i];
			if (sec.SoundTarget == mo) { sec.SoundTarget = null; cleared++; }
		}
		int near = AlertWithin(mo, Num("alert"));
		int killed = 0, echoes = 0;
		let ac = RSLD.AC("Alerter");
		if (ac)
		{
			let it = ThinkerIterator.Create(ac);
			Actor a;
			while (a = Actor(it.Next())) if (a.target == mo) { a.Destroy(); killed++; }
		}
		let tc = RSLD.AC("Tracer");
		if (tc)
		{
			let it = ThinkerIterator.Create(tc);
			Actor a;
			while (a = Actor(it.Next()))
			{
				if (a.target != mo) continue;
				string cn = a.GetClassName();
				if (cn.Left(16) != "DistantFireSound") continue;
				a.A_StopSound(CHAN_WEAPON);
				a.Destroy();
				echoes++;
			}
		}
		mo.A_SoundVolume(CHAN_WEAPON, Num("vol"));
		if (cleared || killed || echoes || when == "pull")
			s.Log(String.Format("%s: alert taken back from %d sector(s), A_AlertMonsters(%d) -> %d sector(s); %d Alerter, %d far echo removed; fire sound x%.1f",
				when, cleared, int(Num("alert")), near, killed, echoes, Num("vol")));
	}
}
