// LD mode: LegenDoom's non-gun sounds behind a run-time option (owner round 3; agent R3a).
//
// Why this way: SNDINFO is read once at start (no run-time switch), and LegenDoom plays these sounds from ACS
// (LocalAmbientSound in LEGNDLIB.acs EffectScreen: the pickup jingle) and from its monster sound generators
// (MonsterStats.dec LDLegendaryMonsterSoundGenerator*: the aura loop, its "transition" sound, the boss sting).
// So SNDINFO.rsld silences those sound NAMES (LegenDoom loads first, BD22 VR's definitions win) and this file plays
// LegenDoom's own LUMPS (rsld/ld/*) at the same moments, with the same channel, volume and attenuation, when the option
// "Mute LegenDoom Pickup & Aura Sounds" (rsld_mute_ld_sounds, default off) is off. Switching it in a level stops or
// restarts the aura of every legendary at once.

class RSLD_LDSounds play
{
	static bool Muted() { cvar c = cvar.FindCvar("rsld_mute_ld_sounds"); return c && c.GetBool(); }

	// pickup.zs: a legendary was picked up (LegenDoom's EffectScreen runs and plays its jingle: LEGNDLIB.acs:678-695)
	static void Jingle(Actor toucher, string effect, int rarity)
	{
		if (!toucher || !toucher.player || toucher.PlayerNumber() != consoleplayer) return;
		if (Muted()) { if (RSLD.Debug()) Console.Printf("RSLD %d sounds: LegenDoom pickup jingle muted (rsld_mute_ld_sounds)", level.maptime); return; }
		string s = "rsld/ld/newlegendarypickup";
		string e = effect.MakeLower();
		if (e == "mysterious" || e == "agitating" || e == "serious" || e == "desperate" || e == "beam" || e == "illegal" || e == "augmented")
			s = "rsld/ld/" .. e .. "pickup";
		else if (rarity == 3) s = "rsld/ld/epicnewlegendarypickup";
		S_StartSound(s, CHAN_AUTO, CHANF_UI, 1.0, ATTN_NONE);	// LocalAmbientSound(..., 127)
		if (RSLD.Debug()) Console.Printf("RSLD %d sounds: LegenDoom pickup jingle %s", level.maptime, s);
	}

	// handler.zs WorldThingSpawned: one of LegenDoom's aura generators
	static void Spawned(Actor a)
	{
		string n = a.GetClassName();
		if (n.Left(32) != "LDLegendaryMonsterSoundGenerator") return;
		RSLD_LDSoundReg.Get().Add(a);
	}
}

class RSLD_LDSoundReg : Thinker
{
	Array<Actor> gen;
	Array<int> born;
	Array<bool> playing;
	bool wasMuted;

	static RSLD_LDSoundReg Get()
	{
		let it = ThinkerIterator.Create("RSLD_LDSoundReg");
		let g = RSLD_LDSoundReg(it.Next());
		if (!g) g = new("RSLD_LDSoundReg");
		return g;
	}

	void Add(Actor a) { gen.Push(a); born.Push(level.maptime); playing.Push(false); }

	// MonsterStats.dec:221-250: loop on channel 6 (0.8, attenuation 1.2 / boss 0.4), transition on 7 (1.0, 0.6), boss sting on 5
	static void Start(Actor a, bool full)
	{
		string n = a.GetClassName();
		bool boss = n.IndexOf("Boss") >= 0;
		bool robot = n.IndexOf("Robot") >= 0;
		if (robot) return;	// LegenDoom 3.0's SNDINFO defines no legendaryrobot* sounds: they are silent there too
		a.A_StartSound("rsld/ld/legendaryenemyloop", 6, CHANF_LOOPING, 0.8, boss ? 0.4 : 1.2);
		if (!full) return;
		a.A_StartSound("rsld/ld/legendaryenemy", 7, 0, 1.0, 0.6);
		if (boss) a.A_StartSound("rsld/ld/legendaryenemyboss", 5, 0, 1.0, 0.1);
	}

	override void Tick()
	{
		bool m = RSLD_LDSounds.Muted();
		for (int i = gen.Size() - 1; i >= 0; i--)
		{
			let a = gen[i];
			if (!a) { gen.Delete(i); born.Delete(i); playing.Delete(i); continue; }
			// the generator's own (now silent) sounds start on its first tic: ours from its third, on the same channels, so
			// its Remove state (A_StopSound 5, 6, 7) still ends them
			if (level.maptime - born[i] < 2) continue;
			bool alive = a.master && a.master.health > 0;	// past its Remove state (the legendary died): nothing to restart
			if (!m && !playing[i] && alive) { Start(a, level.maptime - born[i] < 4); playing[i] = true; }
			else if (m && playing[i]) { a.A_StopSound(5); a.A_StopSound(6); a.A_StopSound(7); playing[i] = false; }
		}
		if (m != wasMuted && RSLD.Debug()) Console.Printf("RSLD %d sounds: LegenDoom pickup & aura sounds %s (%d auras)", level.maptime, m ? "muted" : "on", gen.Size());
		wasMuted = m;
	}
}
