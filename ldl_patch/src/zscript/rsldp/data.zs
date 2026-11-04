// LDL x BD22 VR patch: which BD22 VR weapons stand in for LegenDoom 3.0's nine weapons.
// Slot order is LegenDoom's own (decorate constants WEAPON_FISTS..WEAPON_BFG, ACS weaponActors[]).
// Family: every BD22 / BD22 VR weapon class that carries that slot's legendary effect while held.
//   From brutal22test6 WeaponSpawners.dec (parsed): Fist->Melee_Attacks (replaces Fist), ChainsawSpawner->Chain_Saw,
//   PistolSpawner->BrutalPistol, ShotgunSpawner->Shot_Gun, SSGSpawner->SSG, ChaingunSpawner->Minigun,
//   RocketLauncherSpawner->Rocket_Launcher, PlasmagunSpawner->Plasma_Gun, BFG9000Spawner->BIG_FUCKING_GUN;
//   plus their Purist/Dual variants (KEYCONF setslot), BD22's starting Rifle in the Chaingun family (the bullet
//   gun of BD22's slot 4, which every player starts with) and BD22 VR's Moonlight (BrutalRevolver, which takes the
//   pistol's place with "Moonlight Replaces Pistol").
// Give: what a legendary pickup hands over when the player owns no gun of the family yet (the spawner's gun).
class RSLDP_Data
{
	static const string Slots[] = { "Fists", "Chainsaw", "Pistol", "Shotgun", "SuperShotgun", "Chaingun", "RocketLauncher", "PlasmaRifle", "BFG9000" };
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
		"8|BIG_FUCKING_GUN", "8|PuristBIG_FUCKING_GUN"
	};
	static const string Rarities[] = { "Common", "Uncommon", "Rare", "Epic" };
	// LegenDoom's rarityColors[] (LEGENDINF.acs): CR_GREEN, CR_BLUE, CR_PURPLE, CR_ORANGE
	static const int RarityColor[] = { Font.CR_GREEN, Font.CR_BLUE, Font.CR_PURPLE, Font.CR_ORANGE };
	// a class by name at run time (BD22, BD22 VR and LegenDoom classes are DECORATE: unknown when ZScript compiles)
	clearscope static class<Actor> AC(string n) { class<Actor> c = n; return c; }

	// LegenDoom's per-slot variant suffix of some death items (LDMurderousEffectDeathRocket etc.)
	static const string DeathVariant[] = { "", "", "", "", "", "", "Rocket", "Plasma", "BFG9000" };

}
