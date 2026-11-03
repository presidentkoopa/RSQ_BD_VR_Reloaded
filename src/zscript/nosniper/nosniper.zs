// Guns switched off in this pack (owner, 2026-10-16). Each row: the gun, then its stand-in.
// TO TURN A GUN BACK ON: put // in front of its row here AND its spawner line in
// CheckReplacement below. Anything that would spawn a switched-off gun spawns its stand-in,
// and a player given one (pickup, give all) has it swapped for the stand-in the next tic.
// Class names are looked up at run time: BD22's classes are DECORATE, unseen when this compiles.
class RSQ_NoSniper : EventHandler
{
	static const Name gone[] = {
	//	'Sniper', 'PuristSniper',									// 1.93: BACK ON (and its instead[] row below)
		'MP40', 'PuristMP40',										// MP40
		'MG42', 'PuristMG42',										// MG42 "buzzsaw"
		'Devastator', 'PuristDevastator',							// Devastator
		'HellishMissileLauncher', 'PuristHellishMissileLauncher',	// Hellish missile launcher
		'FlameCannon', 'PuristFlameCannon', 'DualFlameCannon',		// flame cannon
		'IncendiaryLauncher', 'PuristIncendiaryLauncher'			// 2.0.3o (owner 2026-11-03): incendiary launcher
	};
	static const Name instead[] = {
	//	'Rifle', 'PuristRifle',										// 1.93: the sniper's stand-in, off with it
		'BrutalSMG', 'PuristSMG',
		'Minigun', 'PuristMinigun',
		'Rocket_Launcher', 'PuristRocket_Launcher',
		'Rocket_Launcher', 'PuristRocket_Launcher',
		'Flamethrower2', 'PuristFlamethrower2', 'Flamethrower2',
		'GrenadeLauncher', 'PuristGrenadeLauncher'		// slot 5 next to it (BD22 KEYCONF setslot 5, SelectionOrder 2700 vs 2600)
	};

	// 1.6 (owner): "Allow extra weapons with cheats" (rsq_extra_weapons, menu). On, these come
	// back through cheats (give all, idkfa, give <name>): the MP40, the MG42 "buzzsaw", the flame cannon, the
	// Devastator, the Hellish missile launcher and (2.0.3o) the incendiary launcher. Maps still spawn the
	// stand-ins either way.
	// 1.93 (owner): the SNIPER IS BACK ON. Its rows in gone[] / instead[] and its SniperAmmo
	// line are commented out, so it is a normal weapon again and needs no cheat. It was only
	// switched off on 2026-10-16 because its model had gone from the pack.
	static const Name extra[] = { 'MP40', 'PuristMP40', 'MG42', 'PuristMG42', 'Devastator', 'PuristDevastator',
		'HellishMissileLauncher', 'PuristHellishMissileLauncher', 
		'FlameCannon', 'PuristFlameCannon', 'DualFlameCannon',
		'IncendiaryLauncher', 'PuristIncendiaryLauncher' };

	static bool ExtraOn()
	{
		let cv = CVar.FindCVar('rsq_extra_weapons');
		return cv && cv.GetBool();
	}

	bool IsExtra(Name n)
	{
		for (int i = 0; i < extra.Size(); i++)
			if (extra[i] == n)
				return true;
		return false;
	}

	class<Actor> Find(Name n) { return FindS(n); }
	static class<Actor> FindS(Name n) { class<Actor> c = n; return c; }

	override void CheckReplacement(ReplaceEvent e)
	{
		if (!e.Replacee) return;
		Name n = e.Replacee.GetClassName();
		// extras allowed: the gun itself is never replaced (give all skips a replaced weapon, and
		// BD22's own spawners replace two of them), so the cheats hand out the real thing
		if (ExtraOn() && IsExtra(n))
		{
			e.Replacement = null;
			e.IsFinal = true;
			return;
		}
		for (int k = 0; k < gone.Size(); k++)
		{
			if (n == gone[k])
			{
				let r = Find(instead[k]);
				if (r) e.Replacement = r;
				return;
			}
		}
	//	if (n == 'SniperAmmo')				e.Replacement = Find('Clip2');			// 1.93: sniper ammo is itself again
		if (n == 'MP40Spawner')				e.Replacement = Find('BrutalSMG');		// MP40 (1.93: chain head now)
		else if (n == 'MG42Spawner')		e.Replacement = Find('Minigun');		// MG42
		else if (n == 'DevastatorSpawner')	e.Replacement = Find('Rocket_Launcher');	// Devastator
		else if (n == 'HMLSpawner')			e.Replacement = Find('Rocket_Launcher');	// Hellish
		else if (n == 'FlameCannonSpawner')	e.Replacement = Find('Flamethrower2');	// flame cannon
		else if (n == 'ILSpawner')			e.Replacement = Find('GrenadeLauncher');	// incendiary launcher (2.0.3o)
		// BD22 swaps the Nuker for a pickup spawner, and give all skips any replaced weapon.
		// Keep it as itself so give all / idkfa include it (maps place the spawner directly).
		// (The incendiary launcher had this line too until 2.0.3o; it is in gone[] / extra[] now.)
		else if (n == 'NukeLauncher')
		{ e.Replacement = null; e.IsFinal = true; }	// null + final = no replacement (events.cpp)
	}

	override void WorldTick()
	{
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo) continue;
			let mo = players[i].mo;
			for (int k = 0; k < gone.Size(); k++)
			{
				if (ExtraOn() && IsExtra(gone[k]))
					continue;
				class<Inventory> g = (class<Inventory>)(Find(gone[k]));
				if (!g || mo.CountInv(g) <= 0) continue;
				mo.TakeInventory(g, 999);
				class<Inventory> r = (class<Inventory>)(Find(instead[k]));
				if (r && mo.CountInv(r) == 0)
					mo.GiveInventory(r, 1);
			}
		}
	}
}
