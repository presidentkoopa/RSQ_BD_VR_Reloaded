// LD mode: which BD22 VR weapons stand in for LegenDoom 3.0's nine weapons.
// Slot order is LegenDoom's own (decorate constants WEAPON_FISTS..WEAPON_BFG, ACS weaponActors[]).
// Family: every BD22 / BD22 VR weapon class that carries that slot's legendary effect while held.
//   From brutal22test6 WeaponSpawners.dec (parsed): Fist->Melee_Attacks (replaces Fist), ChainsawSpawner->Chain_Saw,
//   PistolSpawner->BrutalPistol, ShotgunSpawner->Shot_Gun, SSGSpawner->SSG, ChaingunSpawner->Minigun,
//   RocketLauncherSpawner->Rocket_Launcher, PlasmagunSpawner->Plasma_Gun, BFG9000Spawner->BIG_FUCKING_GUN;
//   plus their Purist/Dual variants (KEYCONF setslot), BD22's starting Rifle in the Chaingun family (the bullet
//   gun of BD22's slot 4, which every player starts with) and BD22 VR's Silvergun (BrutalRevolver, which takes the
//   pistol's place with "Silvergun Replaces Pistol").
// Give: the gun a legendary pickup shows and hands over when the player does not have it yet (the spawner's gun; Same).
class RSLD_Data
{
	static const string Slots[] = { "Fists", "Chainsaw", "Pistol", "Shotgun", "SuperShotgun", "Chaingun", "RocketLauncher", "PlasmaRifle", "BFG9000" };
	// "LD" .. Slots[s] .. "Effect_" and "LD" .. Slots[s] .. "Legendary", written out (performance, 2026-11-27: the handler's
	// RefreshSlots built both for every slot and every LD item in the player's inventory, every 17 tics)
	static const string EffectPrefix[] = { "LDFistsEffect_", "LDChainsawEffect_", "LDPistolEffect_", "LDShotgunEffect_", "LDSuperShotgunEffect_",
		"LDChaingunEffect_", "LDRocketLauncherEffect_", "LDPlasmaRifleEffect_", "LDBFG9000Effect_" };
	static const string LegendaryPrefix[] = { "LDFistsLegendary", "LDChainsawLegendary", "LDPistolLegendary", "LDShotgunLegendary", "LDSuperShotgunLegendary",
		"LDChaingunLegendary", "LDRocketLauncherLegendary", "LDPlasmaRifleLegendary", "LDBFG9000Legendary" };
	static const string LDWeapons[] = { "LDFists", "LDChainsaw", "LDPistol", "LDShotgun", "LDSuperShotgun", "LDChaingun", "LDRocketLauncher", "LDPlasmaRifle", "LDBFG9000" };
	static const string Give[] = { "Melee_Attacks", "Chain_Saw", "BrutalPistol", "Shot_Gun", "SSG", "MiniGun", "Rocket_Launcher", "Plasma_Gun", "BIG_FUCKING_GUN" };
	static const string Family[] =
	{
		"0|Melee_Attacks",
		"1|Chain_Saw",
		"2|BrutalPistol", "2|DualPistols", "2|PuristPistol", "2|BrutalRevolver",
		"3|Shot_Gun", "3|PuristShot_Gun",
		"4|SSG", "4|PuristSSG",
		"5|MiniGun", "5|PuristMiniGun", "5|Rifle", "5|DualRifles", "5|PuristRifle",
		"6|Rocket_Launcher", "6|PuristRocket_Launcher",
		"7|Plasma_Gun", "7|DualPlasmaRifles", "7|PuristPlasma_Gun",
		"8|BIG_FUCKING_GUN", "8|PuristBIG_FUCKING_GUN",
		// 2.0.5o EVERY GUN CAN BE LEGENDARY (owner 2026-11-24: "the bd22 set isn't fully covered by legendoom"; 18:15 "get this
		// done"): LegenDoom has nine slots, so the rest of BD22's guns join the slot whose job they share and carry its
		// legendary while held. Drops still hand over the slot's own gun (Give); owning one of these does not count as
		// owning it (Same is unchanged). Hand grenades stay out: they are thrown, not held.
		"0|BrutalAxe", "0|DSweap",
		"1|Flamethrower2", "1|PuristFlamethrower2", "1|FlameCannon", "1|DualFlameCannon", "1|PuristFlameCannon",
		"2|BrutalSMG", "2|DualSMG", "2|PuristSMG", "2|MP40", "2|DualMP40", "2|PuristMP40",
		"3|AssaultShotgun", "3|PuristAssaultShotgun", "3|Revolver", "3|PuristRevolver",
		"5|Machinegun", "5|MG42", "5|PuristMG42", "5|Sniper", "5|PuristSniper",
		"6|GrenadeLauncher", "6|PuristGrenadeLauncher", "6|IncendiaryLauncher", "6|PuristIncendiaryLauncher", "6|Devastator", "6|PuristDevastator",
		"7|RailGun", "7|PuristRailGun",
		"8|BFG10k", "8|PuristBFG10k", "8|NukeLauncher", "8|PuristNukeLauncher", "8|Unmaker", "8|PuristUnmaker",
		"8|HellishMissileLauncher", "8|PuristHellishMissileLauncher"
	};
	// Same: the guns that count as already owning the gun a legendary pickup SHOWS (Give, or the Silvergun): the given
	// gun and its own Purist/Dual copies. The Family's stand-ins are left out (the Rifle stands in for the Chaingun
	// family, the Silvergun for the pistol): owning a Rifle must not stop a legendary Minigun drop giving the Minigun
	// (owner 11-04 22:20, "when I pick up weapons ... I cannot switch to them": every BD22 class starts with the Rifle,
	// so a legendary chaingun never gave its Minigun; rig wb_wr1). The legendary still powers the whole Family.
	static const string Same[] =
	{
		"Melee_Attacks", "Chain_Saw", "BrutalPistol|DualPistols|PuristPistol", "Shot_Gun|PuristShot_Gun", "SSG|PuristSSG",
		"MiniGun|PuristMiniGun", "Rocket_Launcher|PuristRocket_Launcher", "Plasma_Gun|DualPlasmaRifles|PuristPlasma_Gun",
		"BIG_FUCKING_GUN|PuristBIG_FUCKING_GUN"
	};
	// 2.0.5p EACH GUN ITS OWN LEGENDARY (owner 2026-11-24 18:26: a legendary drop should be "a Legendary MG42 pickup",
	// each gun dropping as its own legendary). A legendary drop is one of LegenDoom's nine slots; it now SHOWS and GIVES a
	// random gun of that slot's group (DropGuns, the guns' own classes; the Purist and Dual copies are its variants), and
	// its power is BOUND to that gun (RSLD_GunBind): held, that gun and its Purist / Dual / off-hand copies carry it; the
	// rest of the group do not. A legendary from before 2.0.5p (no binding) still powers the whole group, as it did.
	static const string DropGuns[] =
	{
		"Melee_Attacks|BrutalAxe|DSweap",
		"Chain_Saw|Flamethrower2|FlameCannon",
		"BrutalPistol|BrutalSMG|MP40",
		"Shot_Gun|AssaultShotgun|Revolver",
		"SSG",
		"MiniGun|Rifle|MG42|Sniper",
		"Rocket_Launcher|GrenadeLauncher|IncendiaryLauncher|Devastator",
		"Plasma_Gun|RailGun",
		"BIG_FUCKING_GUN|BFG10k|NukeLauncher|Unmaker|HellishMissileLauncher"
	};
	// a gun and the copies that are the same gun (the first is the gun a binding names). One row per gun, rows ended by "".
	// (performance, 2026-11-27: this was one "a|b|c" string per row, Split on every call; SameGun and BaseGun run several
	// times a tic with LD mode on -- SyncLegends, SlotOf for both hands, the HUD name every frame -- and a gun that is in
	// no row split all 24 rows each time. Same rows, same order, so every answer is the one the split rows gave.)
	static const string VariantList[] =
	{
		"BrutalPistol", "DualPistols", "PuristPistol", "",
		"BrutalSMG", "DualSMG", "PuristSMG", "",
		"MP40", "DualMP40", "PuristMP40", "",
		"Shot_Gun", "PuristShot_Gun", "",
		"AssaultShotgun", "PuristAssaultShotgun", "",
		"Revolver", "PuristRevolver", "",
		"SSG", "PuristSSG", "",
		"MiniGun", "PuristMiniGun", "",
		"Rifle", "DualRifles", "PuristRifle", "",
		"MG42", "PuristMG42", "Machinegun", "",
		"Sniper", "PuristSniper", "",
		"Rocket_Launcher", "PuristRocket_Launcher", "",
		"GrenadeLauncher", "PuristGrenadeLauncher", "",
		"IncendiaryLauncher", "PuristIncendiaryLauncher", "",
		"Devastator", "PuristDevastator", "",
		"Plasma_Gun", "DualPlasmaRifles", "PuristPlasma_Gun", "",
		"RailGun", "PuristRailGun", "",
		"BIG_FUCKING_GUN", "PuristBIG_FUCKING_GUN", "",
		"BFG10k", "PuristBFG10k", "",
		"NukeLauncher", "PuristNukeLauncher", "",
		"Unmaker", "PuristUnmaker", "",
		"HellishMissileLauncher", "PuristHellishMissileLauncher", "",
		"Flamethrower2", "PuristFlamethrower2", "",
		"FlameCannon", "DualFlameCannon", "PuristFlameCannon", ""
	};
	// is class name cn (an off-hand copy's RSQ_Off_ taken off) the gun g or one of its copies? (the first row whose gun is g)
	clearscope static bool SameGun(string cn, Name g)
	{
		if (cn.Left(8) == "RSQ_Off_") cn = cn.Mid(8);
		string gs = g;
		if (cn ~== gs) return true;
		int n = RSLD_Data.VariantList.Size();
		int i = 0;
		while (i < n)
		{
			bool mine = RSLD_Data.VariantList[i] ~== gs;	// i: a row's gun
			i++;
			while (i < n && RSLD_Data.VariantList[i] != "")	// its copies, up to the row's ""
			{
				if (mine && cn ~== RSLD_Data.VariantList[i]) return true;
				i++;
			}
			if (mine) return false;
			i++;	// past the row's ""
		}
		return false;
	}
	// the gun a class is: its off-hand copy's RSQ_Off_ taken off, a Purist / Dual copy read as its gun (VariantList)
	clearscope static Name BaseGun(string cn)
	{
		if (cn.Left(8) == "RSQ_Off_") cn = cn.Mid(8);
		int head = 0;	// the first entry of the row i is in
		for (int i = 0; i < RSLD_Data.VariantList.Size(); i++)
		{
			if (RSLD_Data.VariantList[i] == "") { head = i + 1; continue; }
			if (cn ~== RSLD_Data.VariantList[i]) return RSLD_Data.VariantList[head];
		}
		return cn;
	}
	// a random gun of slot s's group that exists in this load order (the slot's own gun when none other does)
	static Name PickDropGun(int s)
	{
		Array<string> l; RSLD_Data.DropGuns[s].Split(l, "|");
		Array<string> ok;
		for (int i = 0; i < l.Size(); i++) { class<Actor> c = l[i]; if (c) ok.Push(l[i]); }
		if (ok.Size() == 0) return RSLD_Data.Give[s];
		return ok[random[rsldgun](0, ok.Size() - 1)];
	}
	static const string Rarities[] = { "Common", "Uncommon", "Rare", "Epic" };
	// LegenDoom's rarityColors[] (LEGENDINF.acs): CR_GREEN, CR_BLUE, CR_PURPLE, CR_ORANGE
	static const int RarityColor[] = { Font.CR_GREEN, Font.CR_BLUE, Font.CR_PURPLE, Font.CR_ORANGE };
	// a class by name at run time (BD22, BD22 VR and LegenDoom classes are DECORATE: unknown when ZScript compiles)
	clearscope static class<Actor> AC(string n) { class<Actor> c = n; return c; }

	// LegenDoom's per-slot variant suffix of some death items (LDMurderousEffectDeathRocket etc.)
	static const string DeathVariant[] = { "", "", "", "", "", "", "Rocket", "Plasma", "BFG9000" };

}
