// LD mode, G1 damage rules (Agent B, 2026-11-06): LegenDoom 3.0's damage effects on BD22 VR's guns.
// Numbers: numbers_g1.zs (ldl_patch/tools/numbers/g1.rules). LegenDoom writes each of these into its guns' Fire
// states (decorate/<Gun>/<Gun>.dec Fire<Effect>); here they act on our gun's own damage through ModifyDamage.

// Comrade: "Increases in damage the more players are in the game": LegenDoom's shot damage x PlayerCount()
// (Shotgun.dec FireComrade: (5 * random(1, 3)) * CallACS("PlayerCount")). Owner 2026-11-06 round 2: BD22's friendly
// marines near you count as players (RSLD.Allies). Counted once per pull.
class RSLD_Fx_Comrade : RSLD_Effect
{
	static int Players()
	{
		int n = 0;
		for (int i = 0; i < MAXPLAYERS; i++) if (playeringame[i]) n++;
		return n;
	}
	override void OnPull(RSLD_Shot s)
	{
		s.i1 = RSLD.AllyCount(s.mo);
		s.Log(String.Format("damage x%d (%d player(s) in game + %d friendly marine(s) within %d)", Players() + s.i1, Players(), s.i1, RSLD.ALLY_RADIUS));
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h) { h.mult *= Players() + (s.pull > 0 ? s.i1 : RSLD.AllyCount(s.mo)); }
}

// Thematic: "Does more damage the more Thematic weapons you have": damage x the Thematic legendaries owned
// (Shotgun.dec FireThematic: 5 * random(1, 3) * CallACS("LDEffectCount", EFFECT_THEMATIC)).
class RSLD_Fx_Thematic : RSLD_Effect
{
	override void OnPull(RSLD_Shot s) { s.Log(String.Format("damage x%d (Thematic legendaries owned)", RSLD.Count(s.mo, name))); }
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h) { h.mult *= max(1, RSLD.Count(s.mo, name)); }
}

// NanoCircuit: "Attacks have a chance of giving a health and armor bonus": per pull, A_Jump(174, 1) into
// A_GiveInventory("LDHealthBonus") + ("LDArmorBonus") (Shotgun.dec FireNanoCircuit). BD22's own bonuses stand in
// (HealthPlus +2, ArmorShard +2), with the bonus passives (Spiritual, Augmented, Resourceful) as LegenDoom's bonus
// items run them. Sound: BD22's health and armor bonus pickup sounds (scope 4), not effects/nanocircuit.
class RSLD_Fx_NanoCircuit : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		let p = s.mo;
		if (!p || random(0, 255) >= int(Num("chance"))) return;
		let st = RSLD_BState.Get();
		int h0 = p.health, a0 = p.CountInv("BasicArmor");
		RSLD_B.HealthBonusRule(st, p, false);
		RSLD_B.ArmorBonusRule(st, p, null);
		s.Sound("misc/health_pkup");
		s.Sound("misc/armor_pkup");
		s.Log(String.Format("bonus (chance %d/256): health %d -> %d, armor %d -> %d", int(Num("chance")), h0, p.health, a0, p.CountInv("BasicArmor")));
	}
}

// Convincing: "Does no damage, but can mindcontrol enemies you hit". LegenDoom's own token items are given to the
// monster, as its puffs/projectiles do (EpicSpecialEffects.dec:1417-1840): LDConvincingEffect (30 tokens) per bullet,
// saw or fist hit, LDConvincingEffectBerserk (400) for a berserk fist, LDConvincingEffectPlasma (80) per plasma ball,
// LDConvincingEffectBFG (1600) per BFG ball + LDConvincingEffectBFGTracer (240) in 256, LDConvincingEffectRocket (456)
// in 160 around a rocket. The item turns the monster FRIENDLY when its tokens reach its health (not BOSS, not a
// transformed legendary, not already friendly: LegenDoom's own checks). Our damage is set to 0.
class RSLD_Fx_Convincing : RSLD_Effect
{
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		h.setDamage = 0;
		let t = h.target;
		let inf = h.inflictor;
		bool direct = inf && inf != s.mo && inf.bMISSILE && !(h.flags & DMG_EXPLOSION);
		if (s.slot == 6 || s.slot == 8)
		{
			if (!inf || inf == s.mo) return;
			let st = RSLD_BState.Get();
			for (int i = 0; i < st.doneInfl.Size(); i++) if (st.doneInfl[i] == inf) return;
			for (int i = st.doneInfl.Size() - 1; i >= 0; i--) if (!st.doneInfl[i]) st.doneInfl.Delete(i);
			st.doneInfl.Push(inf);
			if (s.slot == 6) { RadiusGive(s, inf, "LDConvincingEffectRocket", Num("rocket_r")); return; }
			if (direct && Convertible(t)) Give(s, t, "LDConvincingEffectBFG");
			RadiusGive(s, inf, "LDConvincingEffectBFGTracer", Num("bfg_r"));
			return;
		}
		if (!Convertible(t)) return;
		if (s.slot == 7) { if (direct) Give(s, t, "LDConvincingEffectPlasma"); return; }
		bool berserk = s.slot == 0 && s.mo && s.mo.FindInventory("PowerStrength", true);
		Give(s, t, berserk ? "LDConvincingEffectBerserk" : "LDConvincingEffect");
	}

	static bool Convertible(Actor t)
	{
		return t && t.bIsMonster && t.health > 0 && !t.bFRIENDLY && !t.bBOSS && !RSLD_B.IsA(t, "ExplosiveBarrel");
	}

	void Give(RSLD_Shot s, Actor t, string item)
	{
		int k0 = RSLD.Has(t, "LDConvincingToken");
		RSLD.Give(t, item, 1);
		s.Log(String.Format("%s on %s: tokens %d -> %d / health %d%s", item, t.GetClassName(), k0, RSLD.Has(t, "LDConvincingToken"), t.health, t.bFRIENDLY ? ": CONVERTED (friendly)" : ""));
	}

	// LegenDoom's A_RadiusGive(item, r, RGF_MONSTERS): monsters within r that the missile can see
	void RadiusGive(RSLD_Shot s, Actor at, string item, double r)
	{
		let bi = BlockThingsIterator.Create(at, r);
		while (bi.Next())
		{
			let t = bi.thing;
			if (!Convertible(t) || at.Distance3D(t) > r || !at.CheckSight(t)) continue;
			Give(s, t, item);
		}
	}
}

// Marksman / Decaying on BD22's fixed-damage guns: owner 2026-11-06 round 2 (scope Q13 b, fixed behaviour; the
// rsld_q13 switch is gone): LegenDoom's average gain as a ratio on hitscan / melee: Marksman x15/10 = x1.5 (its max 15
// vs LegenDoom's average 5 x random(1,3) = 10), Decaying x random(1,30)/10 per pull. A direct projectile hit: the top of
// its x random(1,8) roll (Marksman; LDMarksmanRocket 160 = 20 x 8) / random(1, 2 x that) (Decaying), as LegenDoom.
class RSLD_Fx_Marksman : RSLD_Effect
{
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		let inf = h.inflictor;
		if (inf && inf != s.mo && inf.bMISSILE && !(h.flags & DMG_EXPLOSION))
		{
			h.setDamage = inf.GetMissileDamage(0, 8);	// the top of the x random(1,8) roll
			s.Log(String.Format("%s hit: max roll %d (event %d)", inf.GetClassName(), h.setDamage, h.damage));
			return;
		}
		double mx = Num("dmg"), nm = Num("normal");
		double avg = nm * (1.0 + (nm > 0 ? mx / nm : 0)) / 2.0;	// LegenDoom's average: 5 * random(1, 3) -> 10
		if (avg > 0) h.mult *= mx / avg;
	}
}

class RSLD_Fx_Decaying : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		s.i1 = random(1, max(1, int(Num("hi"))));	// one roll per pull (LegenDoom's expression is read once per call)
		double mk = RSLD.Num("Marksman", "dmg"), nm = RSLD.Num("Marksman", "normal");
		double avg = nm * (1.0 + (nm > 0 ? mk / nm : 0)) / 2.0;
		s.Log(String.Format("roll %d of %d: damage x%.2f (%d / LegenDoom's average %g)", s.i1, int(Num("hi")), avg > 0 ? s.i1 / avg : 1, s.i1, avg));
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull == 0 || s.i1 <= 0) return;
		double hi = max(1.0, Num("hi"));
		double r = s.i1 / (hi / 2.0);			// random(1, 2 x max) over the max
		let inf = h.inflictor;
		if (inf && inf != s.mo && inf.bMISSILE && !(h.flags & DMG_EXPLOSION))
		{
			h.setDamage = max(1, int(inf.GetMissileDamage(0, 8) * r + 0.5));
			return;
		}
		double mk = RSLD.Num("Marksman", "dmg"), nm = RSLD.Num("Marksman", "normal");
		double avg = nm * (1.0 + (nm > 0 ? mk / nm : 0)) / 2.0;
		if (avg > 0) h.mult *= s.i1 / avg;
	}
}

// Favoured: dropped by the owner (2026-11-06 round 2): it never rolls (pickup.zs RSLD_Reroll.IsDropped); no class.
