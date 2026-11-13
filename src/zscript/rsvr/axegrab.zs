// 2.0.3j (owner 2026-11-01): THE AXE IS A THROWING WEAPON THAT CAN ALSO CUT. "Throw axe (which gives me an empty
// hand after throwing), distancegrab it back into my hand, throw again, repeat."
//
// Only with RSQ_DistanceGrab loaded. DistanceGrab tells every Service whose class name has "GrabEventService" in it
// what its pulls do (RSQ_UBQSeries DistanceGrab/zscript/rsqdg/feel.zs RSQDG_Events.Tell):
//   GetInt("grab.event", <event>, hand, fromAir, <thing>, 'RSQ_DistanceGrab'), hand 0 the main, 1 the off.
// Without DistanceGrab nobody calls this, and the axe is exactly the axe.pk3 hotfix's.
//
// An axe pulled in (BrutalAxe, or BrutalAxeOnWall from a berserk throw) goes to THE HAND THAT PULLED IT:
//   - that hand has no axe: it is that hand's. A free hand (fists / off fist) holds it at once; a hand holding a gun
//     keeps the gun and the axe is stored (cycle to it).
//   - that hand has an axe already: the other hand's, by the same rule.
//   - both hands have one: DistanceGrab keeps it in the hand as a thing to carry or throw.
// DistanceGrab first tries the item's own pickup (CallTryPickup). The pickup gives the MAIN axe when there is none,
// so an off-hand pull that was taken that way is moved to the off hand here, and a pickup the engine refused
// (the main axe already owned) arrives as a carried thing and is turned into the off-hand axe.
class RSVR_AxeGrabEventService : Service play
{
	// per hand, from pull.start: an axe is on its way, and what the player had then
	bool coming[2];
	bool hadMain[2], hadOff[2];
	Weapon mainWas[2];

	static bool IsAxeItem(Object o)
	{
		let a = Actor(o);
		if (!a)
			return false;
		Name n = a.GetClassName();
		return n == 'BrutalAxe' || n == 'BrutalAxeOnWall';
	}

	static bool HasMain(PlayerPawn mo) { return mo.FindInventory(RSVR_MeleeHandler.Inv('BrutalAxe'), false) != null; }
	static bool HasOff(PlayerPawn mo) { return mo.FindInventory(RSVR_MeleeHandler.Inv('RSQ_Off_BrutalAxe')) != null; }

	static bool Logs(PlayerPawn mo) { return RSQ.PlayerInt(mo, 'rsq_switch_log', 0) > 0; }

	override int GetInt(String request, String stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		if (!(request ~== "grab.event"))
			return 0;
		let p = players[consoleplayer];
		let mo = p.mo;
		int h = intArg & 1;
		if (!mo || mo.health <= 0)
			return 0;
		// 2.0.4q (owner 2026-11-12: "when i try to distance grab my axe it says ammo full"; ONE axe per hand, the rhythm
		// throw -> distance-grab it back -> throw). The engine refuses a floor BrutalAxe to a player who carries the main
		// axe -- in the main hand, in a Tactical Rig holster or in the Wheel -- because it gives no ammo; since Distance
		// Grab's 11-10 AMMO FULL rule that refusal ended the grab ("AMMO FULL", dropped at the feet) before the carried path
		// below was ever reached, so the off hand's thrown axe could never be grabbed back. Distance Grab now asks first
		// ("pickup.claim", flight.zs TakeInto): with the main axe carried and the off-hand axe NOT (it is the one that was
		// thrown), this axe is the off hand's again: given (RSQ_Dual.GiveCopy: never a second copy), and
		//   - grabbed by the OFF hand: held in the off hand at once (2.0.3y "auto-equip every time");
		//   - grabbed by the MAIN hand: the main hand holds an axe -- its own, from wherever it was carried -- and the new
		//     one goes into the off hand if that hand is free (else it is carried, in the Wheel).
		// Both axes carried already: not claimed -- one per hand, so Distance Grab's AMMO FULL stands.
		if (stringArg == "pickup.claim")
		{
			if (!IsAxeItem(objectArg) || RSQ.PlayerInt(mo, 'rsq_dual_axe', 1) == 0)
				return 0;
			bool main = HasMain(mo), off = HasOff(mo);
			if (!main || off)
			{
				Say(mo, h, off && main ? "refused: both axes carried, one per hand (AMMO FULL)" : "not claimed (no main axe: the pickup itself gives it)");
				return 0;
			}
			if (h == 1)
				GiveOff(mo, true, true);
			else
			{
				let axe = Weapon(mo.FindInventory(RSVR_MeleeHandler.Inv('BrutalAxe'), false));
				GiveOff(mo, p.ReadyWeapon == axe);
				if (axe && p.ReadyWeapon != axe)
				{
					axe.bOffhandWeapon = false;
					p.PendingWeapon = axe;
				}
			}
			mo.A_StartSound("Axe/Draw", CHAN_ITEM);
			Actor(objectArg).Destroy();
			Say(mo, h, h == 1 ? "claimed: the off hand's axe again, held in the off hand" : "claimed: the main hand holds its axe, this one is the off hand's");
			return 1;
		}
		if (stringArg == "pull.start")
		{
			coming[h] = IsAxeItem(objectArg);
			if (coming[h])
			{
				hadMain[h] = HasMain(mo);
				hadOff[h] = HasOff(mo);
				mainWas[h] = p.ReadyWeapon;
			}
			return 0;
		}
		if (stringArg != "pull.caught")
		{
			// missed, blocked, aborted, unlocked: that pull is over (refused keeps flying: no change)
			if (stringArg != "pull.refused" && stringArg != "pull.lock")
				coming[h] = false;
			return 0;
		}
		if (!coming[h] && !IsAxeItem(objectArg))
			return 0;
		coming[h] = false;

		if (!objectArg)
		{
			// USED ON THE WAY IN: the item's own pickup took it, so the main hand got the axe (it had none)
			// or, from a wall, the off hand's was asked for (Axe.dec BrutalAxeOnWall Pickup, RSVR_GiveOffAxe)
			if (mo.CountInv('RSVR_GiveOffAxe') > 0)
			{
				mo.TakeInventory('RSVR_GiveOffAxe', 999);
				GiveOff(mo, true, h == 1);
				Say(mo, h, "off hand (main had one)");
				return 0;
			}
			if (!HasMain(mo) || hadMain[h])
				return 0;	// not an axe after all, or nothing new
			if (h == 1)
			{
				// 2.0.3y (owner, BUGS_1.0 item 16: "distance-grabbing the axe to the offhand must auto-equip every
				// time"; item 5: one axe picked up is both axes): pulled with the OFF hand, the off hand holds the
				// off-hand axe now, whatever it held; the main axe that came with it is stored, the main hand keeps its gun
				if (p.PendingWeapon && p.PendingWeapon.GetClassName() == 'BrutalAxe')
					p.PendingWeapon = WP_NOCHANGE;
				GiveOff(mo, true, true);
				Say(mo, h, "off hand (equipped)");
				return 0;
			}
			// the main hand's: held at once if the main hand was free, else stored and the gun kept
			MainTake(mo, h);
			Say(mo, h, "main hand");
			return 0;
		}

		// CAUGHT AND CARRIED: the pickup was refused because the main hand has an axe
		let a = Actor(objectArg);
		bool main = HasMain(mo), off = HasOff(mo);
		bool offOk = RSQ.PlayerInt(mo, 'rsq_dual_axe', 1) != 0;
		// 2.0.3y (owner, BUGS_1.0 item 16): an axe pulled with the OFF hand is always equipped there as the off-hand
		// axe (given if missing). Only when the off hand holds the off-hand axe already does Distance Grab keep carrying it.
		if (h == 1 && !(p.OffhandWeapon && p.OffhandWeapon.GetClassName() == 'RSQ_Off_BrutalAxe'))
		{
			GiveOff(mo, true, true);
			a.Destroy();
			Say(mo, h, off ? "off hand (equipped, carried -> held)" : "off hand (carried -> held)");
		}
		else if (h == 0 && main && !off && offOk)
		{
			GiveOff(mo, true);
			a.Destroy();
			Say(mo, h, "off hand (carried -> held)");
		}
		else if (!main)
		{
			mo.GiveInventory(RSVR_MeleeHandler.Inv('BrutalAxe'), 1);
			MainTake(mo, h);
			a.Destroy();
			Say(mo, h, "main hand (carried -> held)");
		}
		// both hands full: DistanceGrab keeps carrying it
		return 0;
	}

	// the main axe was just given: hold it if the main hand is free, else keep the gun
	void MainTake(PlayerPawn mo, int h)
	{
		let p = mo.player;
		let axe = Weapon(mo.FindInventory(RSVR_MeleeHandler.Inv('BrutalAxe'), false));
		Weapon was = mainWas[h] ? mainWas[h] : p.ReadyWeapon;
		bool free = !was || was is 'RSQ_Hands' || was.GetClassName() == 'Melee_Attacks' || was.GetClassName() == 'BrutalAxe';
		if (free && axe)
			p.PendingWeapon = axe;
		else if (p.PendingWeapon == axe)
			p.PendingWeapon = WP_NOCHANGE;	// the engine's switch-on-pickup: the gun stays
	}

	// the off-hand axe; equip: held in the off hand at once, whatever the off hand held (2.0.3y, owner BUGS_1.0 item 16:
	// "every time"; it was only into a free off hand). What it held stays in the inventory.
	// force false (a MAIN-hand pull handing the axe across): only into a free off hand, as before
	static void GiveOff(PlayerPawn mo, bool equip, bool force = false)
	{
		RSQ_Dual.GiveCopy(mo, RSQ_DualTable.AXE);
		if (!equip)
			return;
		let p = mo.player;
		let ow = p.OffhandWeapon;
		let w = Weapon(mo.FindInventory(RSVR_MeleeHandler.Inv('RSQ_Off_BrutalAxe')));
		if (w && ow != w && (force || !ow || ow is 'RSQ_Hands'))
		{
			w.bOffhandWeapon = true;
			p.PendingWeapon = w;
		}
	}

	static void Say(PlayerPawn mo, int h, String what)
	{
		if (Logs(mo))
			Console.Printf("RSQ axegrab t%d: hand %d pulled an axe -> %s", mo.Level.maptime, h, what);
	}
}

// the wall axe's off-hand gift, used by melee.zs (no equip: a floor or wall pickup keeps the hotfix's rule)
class RSVR_AxeGrab play
{
	static void GiveOff(PlayerPawn mo)
	{
		if (RSQ.PlayerInt(mo, 'rsq_dual_axe', 1) == 0)
			return;
		RSQ_Dual.GiveCopy(mo, RSQ_DualTable.AXE);
		mo.A_StartSound("Axe/Draw", CHAN_ITEM);
	}
}
