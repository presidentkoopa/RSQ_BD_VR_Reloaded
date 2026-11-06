// G9: LegenDoom's map start / respawn buffs (Agent A). LegenDoom's own ACS gives them: LD_ApplyStartBuffs
// (LEGENDFNC.acs:161) from its ENTER script "LDPlayerLoop" (after Delay(1)) and RESPAWN script "LDPlayerRespawn",
// with LD_HasEffectAny: any owned legendary, held or not. That script keeps running in LD mode; here:
//  - what it gives that is a LegenDoom class where BD22 has its own is turned into BD22's (Vanguard: LegenDoom's
//    LDBlueArmorPickup -> BD22's HeavyArmor, its own save amount / percent and HUD icon);
//  - LegenDoom's activation visuals keep their particles, their LegenDoom sounds (effects/restoring, vanguard,
//    wildfire, chronostrike, resupplying) are silenced and BD22's play (scope section 4): MEGAPKUP, Pickup/HeavyArmor,
//    misc/p_pkup (the invulnerability sphere's pickup), SLOWON, BACKPACK (BD22's AmmoSuply).
//  - each logs what the player got (the rig proof).
// Restoring (LDSoulspherePickup: +100 health to 200), Scrambling (LDScramblingEffect: a PowerInvisibility with
// +CANTSEEK, strength 0), Wildfire (PowerInvulnerable, 10 s per 1 + Sustained copies), Chronostrike (PowerTimeFreezer,
// 10 s per 1 + Sustained copies) are LegenDoom's items, unchanged (E).

class RSLD_StartBuff : RSLD_Effect
{
	virtual void Check(PlayerPawn p, int copies) {}
	// LegenDoom's script runs on ENTER after Delay(1) (and at RESPAWN): the handler calls OnMapStart at tic 6
	override void OnMapStart(PlayerPawn p, int copies) { Check(p, copies); }
}

class RSLD_Fx_Restoring : RSLD_StartBuff
{
	override void Check(PlayerPawn p, int copies) { Log(String.Format("start: health %d (LegenDoom's LDSoulspherePickup)", p.health)); }
}

class RSLD_Fx_Vanguard : RSLD_StartBuff
{
	override void Check(PlayerPawn p, int copies)
	{
		let ba = BasicArmor(p.FindInventory("BasicArmor"));
		Name was = ba ? ba.ArmorType : 'None';
		// LegenDoom's LDBlueArmorPickup records its armor as 'BlueArmor' (rig 11-06: "armor 200 BlueArmor (50%)"); BD22
		// replaces BlueArmor with its HeavyArmor, so a BlueArmor in a BD22 game came from LegenDoom
		if (ba && ba.Amount > 0 && (ba.ArmorType == 'LDBlueArmorPickup' || ba.ArmorType == 'BlueArmor'))
		{
			class<Inventory> ha = RSLD.IC("HeavyArmor");	// BD22's blue armor (brutal22test6 actors/MISC/Health2.dec)
			if (ha)
			{
				ba.Amount = 0;
				p.GiveInventory(ha, 1);
			}
		}
		ba = BasicArmor(p.FindInventory("BasicArmor"));
		Log(String.Format("start: armor %d %s (%.0f%%), was %s", ba ? ba.Amount : 0, ba ? ba.ArmorType : 'None', ba ? ba.SavePercent * 100 : 0, was));
	}
}

class RSLD_Fx_Scrambling : RSLD_StartBuff
{
	override void Check(PlayerPawn p, int copies)
	{
		class<Inventory> sc = RSLD.IC("LDScramblingEffect");
		let s = sc ? p.FindInventory(sc) : null;
		Log(String.Format("start: LDScramblingEffect %s, player +CANTSEEK %d", s ? "held" : "MISSING", p.bCANTSEEK));
	}
}

class RSLD_Fx_Wildfire : RSLD_StartBuff
{
	override void Check(PlayerPawn p, int copies)
	{
		let pw = Powerup(p.FindInventory("PowerInvulnerable", true));
		Log(String.Format("start: invulnerable %s, %d tics left (Sustained copies %d)", pw ? "yes" : "NO", pw ? pw.EffectTics : 0, RSLD.Count(p, "Sustained")));
	}
}

class RSLD_Fx_Chronostrike : RSLD_StartBuff
{
	override void Check(PlayerPawn p, int copies)
	{
		let pw = Powerup(p.FindInventory("PowerTimeFreezer", true));
		Log(String.Format("start: time freeze %s, %d tics left (Sustained copies %d)", pw ? "yes" : "NO", pw ? pw.EffectTics : 0, RSLD.Count(p, "Sustained")));
	}
}

// LegenDoom's start-buff visuals: particles kept, its sounds replaced with BD22's (handler WorldThingSpawned)
class RSLD_StartVisuals play
{
	static const string Vis[] = { "LDRestoringVisual", "LDVanguardVisual", "LDWildfireVisual", "LDChronostrikeVisual", "LDResupplyingVisual" };
	static const string Snd[] = { "MEGAPKUP", "Pickup/HeavyArmor", "misc/p_pkup", "SLOWON", "BACKPACK" };

	static bool Check(Actor a)
	{
		string n = a.GetClassName();
		for (int i = 0; i < RSLD_StartVisuals.Vis.Size(); i++)
		{
			if (!(n ~== RSLD_StartVisuals.Vis[i])) continue;
			RSLD_Silencer.Watch(a, 6);
			let p = a.master ? a.master : a;
			p.A_StartSound(RSLD_StartVisuals.Snd[i], CHAN_AUTO, CHANF_OVERLAP);
			RSLD.Log(String.Format("start visual %s: LegenDoom's sound silenced, BD22's %s", n, RSLD_StartVisuals.Snd[i]));
			return true;
		}
		return false;
	}
}
