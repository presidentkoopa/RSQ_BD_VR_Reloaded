// LDL x BD22 VR patch: LegenDoom 3.0's legendary effects on BD22 VR weapons.
// LegenDoom writes each effect into its own weapons' states and puffs, so they cannot fire from BD22's guns as they
// are. The bridge reads LegenDoom's own tokens (LD<Slot>Effect_<Name>, the ones its HUD and info screen read) for
// the slot of the gun in hand and applies the effect through hooks that work for any weapon. Where LegenDoom has a
// self-contained item for the effect (death rewards, debuffs, powerup givers), the bridge gives that item, so the
// numbers are LegenDoom's. Where it does not, the numbers come from LegenDoom's code or description and are noted.
// Effects that change how a weapon fires (spread, projectiles, fire rate, beams...) are not carried; a drop that
// rolls one is re-rolled within the same slot and rarity (option "Re-roll effects BD22 VR can't use", default on).

class RSLDP_Effects
{
	// the effect name of slot s that actor a carries ("" if none): LegenDoom's LD<Slot>Effect_<Name> token
	static string EffectOf(Actor a, int s)
	{
		if (!a || s < 0) return "";
		string pre = "LD" .. RSLDP_Data.Slots[s] .. "Effect_";
		int n = pre.Length();
		for (let i = a.Inv; i; i = i.Inv)
		{
			string c = i.GetClassName();
			if (c.Length() > n && c.Left(n) ~== pre) return c.Mid(n);
		}
		return "";
	}

	static int RarityOf(Actor a, int s)
	{
		if (!a || s < 0) return -1;
		for (int r = 3; r >= 0; r--)
		{
			class<Inventory> c = "LD" .. RSLDP_Data.Slots[s] .. "Legendary" .. RSLDP_Data.Rarities[r];
			if (c && a.CountInv(c) > 0) return r;
		}
		return -1;
	}

	static bool IsImplemented(string e)
	{
		if (e == "") return false;
		for (int i = 0; i < RSLDP_Tables.Implemented.Size(); i++) if (RSLDP_Tables.Implemented[i] ~== e) return true;
		return false;
	}

	// keep e if the bridge carries it; else pick one the bridge carries from LegenDoom's own roll list for that slot
	// and rarity (tables.zs Rolls, parsed from LD<Slot>RandomLegendary)
	static string Reroll(int s, int r, string e)
	{
		if (IsImplemented(e) || r < 0) return e;
		cvar cv = cvar.FindCvar("rsldp_reroll");
		if (cv && !cv.GetBool()) return e;
		Array<string> pool;
		string key = RSLDP_Data.Slots[s] .. "|" .. RSLDP_Data.Rarities[r] .. "|";
		for (int i = 0; i < RSLDP_Tables.Rolls.Size(); i++)
		{
			string row = RSLDP_Tables.Rolls[i];
			if (row.Left(key.Length()) != key) continue;
			string eff = row.Mid(key.Length());
			if (IsImplemented(eff)) pool.Push(eff);
		}
		if (pool.Size() == 0) return e;
		string pick = pool[random(0, pool.Size() - 1)];
		if (RSLDP_Handler.Debug()) Console.Printf("RSLDP reroll: %s %s %s -> %s", RSLDP_Data.Slots[s], RSLDP_Data.Rarities[r], e, pick);
		return pick;
	}

	// target groups of LegenDoom's x3 effects (their descriptions name the monsters; LegenDoom's own monsters carry
	// the DamageFactor). BD22/XMVE monsters are matched by the vanilla class they derive from or replace, then by name.
	static bool InGroup(Actor t, string e)
	{
		if (!t) return false;
		string n = t.GetClassName();
		class<Actor> root = Actor.GetReplacee(t.GetClass());
		if (e ~== "Exorcist") return IsAny(t, root, "Zombieman|ShotgunGuy|ChaingunGuy|WolfensteinSS") || Has(n, "Zombie|Sergeant|Commando|Former|Trooper");
		if (e ~== "Extinguishing") return IsAny(t, root, "DoomImp|Archvile") || Has(n, "Imp|Vile");
		if (e ~== "Wrangler") return IsAny(t, root, "Demon|Spectre") || (Has(n, "Demon|Spectre|Spectro|Pinky") && !Has(n, "Cyber|Caco"));
		if (e ~== "Antiair") return IsAny(t, root, "LostSoul|Cacodemon|PainElemental") || Has(n, "Caco|LostSoul|PainElemental");
		if (e ~== "Scrapper") return IsAny(t, root, "Arachnotron|Revenant|Fatso") || Has(n, "Arachno|Revenant|Mancub|Fatso");
		if (e ~== "Blessed") return IsAny(t, root, "HellKnight|BaronOfHell") || Has(n, "Knight|Baron");
		if (e ~== "Heroic") return t.bBOSS || IsAny(t, root, "Cyberdemon|SpiderMastermind") || Has(n, "Cyberdemon|Mastermind");
		if (e ~== "DemonSlayer") { class<Inventory> tok = (class<Inventory>)(RSLDP_Data.AC("LDLegendaryMonsterToken")); return tok && t.CountInv(tok) > 0; }
		return false;
	}

	static bool IsAny(Actor t, class<Actor> root, string list)
	{
		Array<string> l; list.Split(l, "|");
		for (int i = 0; i < l.Size(); i++)
		{
			class<Actor> c = l[i];
			if (!c) continue;
			if (t is c || root == c) return true;
		}
		return false;
	}

	static bool Has(string n, string list)
	{
		Array<string> l; list.Split(l, "|");
		n = n.MakeLower();
		for (int i = 0; i < l.Size(); i++) if (n.IndexOf(l[i].MakeLower()) >= 0) return true;
		return false;
	}

	// LegenDoom's multiplier for the target-independent damage effects (applied by RSLDP_Amp to the owner's damage)
	static double OwnerMult(Actor o, string e, RSLDP_Handler h, int pn)
	{
		let pl = o.player;
		if (e ~== "Pristine") return o.health >= 100 ? 2.0 : 1.0;	// "While at 100+ health, does double damage"
		if (e ~== "Raging") return o.FindInventory("PowerStrength", true) ? 3.0 : 1.0;	// "tripled while berserk"
		if (e ~== "Rampaging") return (pl && pl.cmd.forwardmove > 0) ? 2.0 : 1.0;	// "holding forwards, 2x"
		if (e ~== "Serious") return (pl && pl.cmd.forwardmove < 0) ? 2.0 : 1.0;	// "holding backwards, 2x"
		if (e ~== "ProStrat") return (pl && pl.cmd.sidemove != 0) ? 2.0 : 1.0;	// "while strafing, 2x"
		if (e ~== "SteadyShot") return (pl && (pl.crouchfactor < 1.0 || (pl.cmd.buttons & BT_CROUCH))) ? 3.0 : 1.0;	// "crouching, triple"
		if (e ~== "Machine") return 2.0;	// "does double damage" (its fire rate part is not carried)
		if (e ~== "CQC") return 3.0;	// "Triple damage" (its accuracy penalty is not carried)
		if (e ~== "Lucky") return random(0, 255) < 58 ? 5.0 : 1.0;	// LD shotgun FireLucky: A_Jump(58) to a 5x shot
		if (e ~== "Berserker")	// LD shotgun FireBerserker: 5 damage at 100+ health, +1 per 10 health below (to 15)
			return 1.0 + 0.2 * clamp(int(ceil((100 - o.health) / 10.0)), 0, 10);
		if (e ~== "AntiTree")	// LDTreesDamageDisplay holds LegenDoom's tree damage percent (LEGENDWRD.acs)
		{
			class<Inventory> c = (class<Inventory>)(RSLDP_Data.AC("LDTreesDamageDisplay"));
			int pc = c ? o.CountInv(c) : 0;
			return pc > 0 ? pc / 100.0 : 1.0;
		}
		if (e ~== "Patient")	// LDPatientCount: (LDPatientCounter + 10) / 10, built up while not firing
		{
			class<Inventory> c = (class<Inventory>)(RSLDP_Data.AC("LDPatientCounter"));
			double m = ((c ? o.CountInv(c) : 0) + 10) / 10.0;
			return max(m, h ? h.patientMult[pn] : 1.0);
		}
		return 1.0;
	}
}

// Held by every player. Outgoing damage (passive == false) of the slot effect in hand.
class RSLDP_Amp : Inventory
{
	Default
	{
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
		+INVENTORY.UNCLEARABLE
		Inventory.MaxAmount 1;
	}

	override void ModifyDamage(int damage, Name damageType, out int newdamage, bool passive, Actor inflictor, Actor source, int flags)
	{
		if (passive || !Owner || !Owner.player || damage <= 0) return;
		let h = RSLDP_Handler(EventHandler.Find("RSLDP_Handler"));
		if (!h) return;
		int pn = Owner.PlayerNumber();
		string e = h.curEffect[pn];
		if (e == "") return;
		if (e ~== "Annoying") { newdamage = 1; return; }	// "only does 1 damage"
		double m = RSLDP_Effects.OwnerMult(Owner, e, h, pn);
		class<Inventory> bc = (class<Inventory>)(RSLDP_Data.AC("LDBloodyCounter"));	// Bloody: (LDBloodyCounter + 5) / 5, the counter fills per kill
		if (e ~== "Bloody" && bc) m *= (Owner.CountInv(bc) + 5) / 5.0;
		if (m != 1.0)
		{
			newdamage = int(newdamage * m);
			if (h.debugHits) Console.Printf("RSLDP amp: %s x%.2f %d -> %d", e, m, damage, newdamage);
		}
	}
}

// Battlerage's attack speed on BD22 guns (handler.zs Battlerage keeps it as long as LegenDoom's own timer)
class RSLDP_Haste : PowerDoubleFiringSpeed
{
	Default { Powerup.Duration 0x7FFFFFFD; +INVENTORY.NOSCREENBLINK }
}

// A soft bridge for other mods (RSQ Wheel's LegenDoom reader, docs/WHEEL_LEGENDARY_PROPOSAL.md): LegenDoom names its
// tokens after its own weapon classes (LDShotgunLegendaryRare, LDShotgunEffect_Vampiric); BD22 VR guns are not those
// classes. Found with ServiceIterator.Find("RSLDP_Service"), so a caller compiles and runs without this patch.
//   GetString[UI]("ld_prefix", "<weapon class>")  -> "LDShotgun" (the token prefix for that gun), "" if none
class RSLDP_Service : Service
{
	static string Prefix(string weaponClass)
	{
		for (int i = 0; i < RSLDP_Data.Family.Size(); i++)
		{
			Array<string> p; RSLDP_Data.Family[i].Split(p, "|");
			if (p[1] ~== weaponClass) return "LD" .. RSLDP_Data.Slots[p[0].ToInt()];
		}
		return "";
	}

	override String GetString(String request, string stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		return request ~== "ld_prefix" ? Prefix(stringArg) : "";
	}

	override String GetStringUI(String request, string stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		return request ~== "ld_prefix" ? Prefix(stringArg) : "";
	}
}
