// ld_g2_core.zs -- G2 (Agent C): LegenDoom 3.0's shot-shape effects on BD22 VR's bullet guns, the shared part.
//
// The pull and pellet machinery is the foundation's (handler.zs / core.zs: OnPellet on every player hitscan pellet
// before muzzle.zs / playerrounds.zs / recoil / flash, FirePellet, FireRail, OnPelletEnd, OnPullEnd, Refund, Take).
// This file adds what the G2 effects share: our guns' own volleys (ld_g2_spread.zs, parsed from src/actors/Weapons),
// so a pellet LegenDoom ADDS gets the spread of the volley it belongs to, rolled the way A_FireBullets rolls one
// (Random2 / 255, gzdoom stateprovider.zs:194-195), and the "pattern" pellets (the gun's spread volleys; not the SSG's
// 300-unit point-blank blast, SSG.dec:242, which BD22 fires with every SSG blast and which stays as it is).
// Nothing here runs without LegenDoom: the foundation only calls effect hooks in LD mode.
// Random numbers: only inside an effect's own pull, only from the rsld_g2 stream.

class RSLD_G2_Effect : RSLD_Effect
{
	RSLD_G2_Spread tab;
	RSLD_Pellet keep;

	override void Init()
	{
		tab = new("RSLD_G2_Spread");
		tab.Fill();
		keep = new("RSLD_Pellet");
	}

	// ---- the pull's fire sequence (ld_g2_spread.zs), cached in s.i2 (0 = not looked up, 1 = none, n + 2 = sequence n)
	int Seq(RSLD_Shot s, RSLD_Pellet p)
	{
		if (s.i2 == 0)
			s.i2 = FindSeq(s.weapon, p.damage, p.range, RSLD.Has(s.mo, "Zoomed") > 0) + 2;
		return s.i2 - 2;
	}

	int FindSeq(Weapon w, int dmg, double range, bool zoomed)
	{
		if (!w) return -1;
		for (int i = 0; i < tab.sName.Size(); i++)
		{
			class<Actor> c = tab.sClass[i];
			if (!c || !(w is c)) continue;
			if (tab.sDmg[i] != dmg) continue;
			double sr = tab.sRange[i];
			if (sr > 0 ? abs(range - sr) > 0.5 : range < MISSILERANGE) continue;
			if (tab.sZoom[i] >= 0 && (tab.sZoom[i] == 1) != zoomed) continue;
			return i;
		}
		return -1;
	}

	string SeqName(RSLD_Shot s) { int q = s.i2 - 2; return q >= 0 ? tab.sName[q] : "none"; }

	static bool Tactical(PlayerPawn mo) { return RSLD.Has(mo, "IsNOTTacticalClass") == 0; }

	static bool Enhanced(PlayerPawn mo)
	{
		let cv = CVar.GetCVar('rsq_pump_spread', mo ? mo.player : null);
		if (!cv) cv = CVar.FindCVar('rsq_pump_spread');
		return cv && cv.GetInt() == 1;
	}

	// the volley (spread xy, z, range; range 0 = full) that original pellet `index` of the pull belongs to
	double, double, double Volley(RSLD_Shot s, int index)
	{
		int q = s.i2 - 2;
		if (q < 0 || index < 0) return 0, 0, 0;
		bool tac = Tactical(s.mo), en = Enhanced(s.mo);
		string sq = tab.sName[q];
		int at = 0, last = -1;
		for (int i = 0; i < tab.vSeq.Size(); i++)
		{
			if (tab.vSeq[i] != sq || (tab.vTac[i] && !tac)) continue;
			last = i;
			at += tab.vN[i];
			if (index < at) break;
		}
		if (last < 0) return 0, 0, 0;
		return en ? tab.vHe[last] : tab.vH[last], en ? tab.vVe[last] : tab.vV[last], tab.vRange[last];
	}

	// the pellet's index among the pull's pattern pellets, -1 if it is not one (the SSG's blast; an unknown gun's
	// short-range pellet)
	int PatternIndex(RSLD_Shot s, RSLD_Pellet p)
	{
		int q = Seq(s, p);
		if (q < 0) return p.range >= MISSILERANGE ? p.index : -1;
		bool tac = Tactical(s.mo);
		string sq = tab.sName[q];
		int at = 0, skip = 0;
		for (int i = 0; i < tab.vSeq.Size(); i++)
		{
			if (tab.vSeq[i] != sq || (tab.vTac[i] && !tac)) continue;
			int n = tab.vN[i];
			if (p.index < at + n) return tab.vRange[i] == 0 ? p.index - skip : -1;
			if (tab.vRange[i] != 0) skip += n;
			at += n;
		}
		return p.index - skip;	// past the table (should not happen): count it
	}

	// pattern pellets in a whole pull of this sequence (Tactical counted)
	int PatternPellets(RSLD_Shot s)
	{
		int q = s.i2 - 2;
		if (q < 0) return 0;
		bool tac = Tactical(s.mo);
		string sq = tab.sName[q];
		int n = 0;
		for (int i = 0; i < tab.vSeq.Size(); i++)
			if (tab.vSeq[i] == sq && (!tab.vTac[i] || tac) && tab.vRange[i] == 0)
				n += tab.vN[i];
		return n;
	}

	// a fresh pellet in the same volley as original pellet `index`: our spread, rolled the A_FireBullets way
	double, double Fresh(RSLD_Shot s, int index)
	{
		double h, v, rg;
		[h, v, rg] = Volley(s, index);
		return s.aimAngle + RSLD_G2.RollH(h), s.aimPitch + RSLD_G2.RollH(v);
	}

	// FirePellet reuses the foundation's one RSLD_Pellet object (handler.zs Refire writes `pel`), and that object is the
	// `p` OnPellet was given: keep p's values across extra pellets, or the original is re-fired with the extra's.
	void Hold(RSLD_Pellet p)
	{
		keep.angle = p.angle; keep.pitch = p.pitch; keep.aimAngle = p.aimAngle; keep.aimPitch = p.aimPitch;
		keep.spreadMul = p.spreadMul; keep.range = p.range; keep.damage = p.damage; keep.flags = p.flags;
		keep.index = p.index; keep.rail = p.rail; keep.puff = p.puff; keep.damageType = p.damageType;
	}
	void Restore(RSLD_Pellet p)
	{
		p.angle = keep.angle; p.pitch = keep.pitch; p.aimAngle = keep.aimAngle; p.aimPitch = keep.aimPitch;
		p.spreadMul = keep.spreadMul; p.range = keep.range; p.damage = keep.damage; p.flags = keep.flags;
		p.index = keep.index; p.rail = keep.rail; p.puff = keep.puff; p.damageType = keep.damageType;
	}

	// an extra pellet of the pull, p kept as it was (see Hold); counted in s.i1
	void Extra(RSLD_Shot s, RSLD_Pellet p, double angle, double pitch, int damage, class<Actor> puff, double range)
	{
		Hold(p);
		s.FirePellet(angle, pitch, damage, puff, range);
		Restore(p);
		s.i1++;
	}
}

class RSLD_G2 play
{
	// a fresh spread roll inside +-h, as A_FireBullets rolls one (Random2 / 255)
	static double RollH(double h) { return h * Random2[rsld_g2]() / 255.; }

	// LegenDoom slot key: pi / sg / ss / cg (the four bullet slots), "" for the rest
	static string Key(int slot)
	{
		static const string k[] = { "", "", "pi", "sg", "ss", "cg", "", "", "" };
		return (slot >= 0 && slot < 9) ? k[slot] : "";
	}

	static string ResName(int r) { static const string n[] = { "nothing", "monster", "thing", "wall" }; return n[clamp(r, 0, 3)]; }

	// one of our own helper actors (explosions, flak): its damage is not a pellet's
	static bool Ours(Actor a)
	{
		if (!a) return false;
		String n = a.GetClassName();
		return n.Left(7) == "RSLD_G2";
	}

	// Perfect's jam (LegenDoom's own LDPerfectJammed on the player, RareSpecialEffects.dec:1423, 1 second): is this
	// hand's trigger blocked now? True only while the hand's gun carries Perfect, as LD checks it only in FirePerfect
	// (Pistol.dec:1439, Chaingun.dec:1262). For the FIRE hook in our guns' fire states (NEEDS_C.md 7).
	static bool Jammed(Actor a, int hand = 0)
	{
		let mo = PlayerPawn(a);
		if (!mo || !mo.player || !RSLD.On() || RSLD.Has(mo, "LDPerfectJammed") <= 0) return false;
		let w = hand == RSLD.OFF ? mo.player.OffhandWeapon : mo.player.ReadyWeapon;
		return RSLD.EffectOf(mo, RSLD.SlotOf(w)) ~== "Perfect";
	}

	// the muzzle and the drawn barrel's direction (angles) of a hand: muzzle.zs's own tables and wall guard
	static Vector3, double, double Muzzle(PlayerPawn mo, int hand, double angle, double pitch)
	{
		Vector3 at;
		bool ok;
		let w = hand == RSLD.OFF ? mo.player.OffhandWeapon : mo.player.ReadyWeapon;
		if (hand == RSLD.OFF)
			[at, ok] = RSQ_Muzzle.OffWhere(mo);
		else
			[at, ok] = RSQ_Muzzle.Where(mo);
		double da = 0, dp = 0;
		if (RSVR_VRHand.InVR(mo) && RSQ_Muzzle.HasBore(w))
			[da, dp] = RSQ_Muzzle.AimOffset(w, RSQ_Muzzle.FromFLU(w, ok));
		if (!ok && !mo.OverrideAttackPosDir)
			at = mo.pos + (0, 0, mo.Height * 0.5 - mo.Floorclip + mo.AttackZOffset * mo.player.crouchFactor);
		double a = angle + da, p = pitch + dp;
		if (mo.OverrideAttackPosDir)
		{
			Vector3 ap = hand == RSLD.OFF ? mo.OffhandDir(mo, a, p) : mo.AttackDir(mo, a, p);
			a = ap.x;
			p = ap.y;
		}
		return at, a, p;
	}
}
