// RSR-M203 (1.31): the M203 under BD22's rifle, worked by hand (QuestZDoom 17.3 / UZDXREMA, no
// engine changes). The launcher is the machine gun's own M203, kitbashed onto the rifle
// (kitbash/fit.py, gen_m203.py); numbers in rsr_m203_geo.zs.
//
// The owner's rules (1.33, 2026-10-17). One rifle, in the main hand:
//   the rifle's SECONDARY FIRE launches the underbarrel (BD22's own FireGrenade); empty, a dry
//     click. BD22's own launcher key does nothing (Rifle.dec swallows its RFGrenade);
//   stabilized (the off grip: the engine's two-hand hold), the OFF TRIGGER is the latch: hold it
//     and push the off hand forward, the tube follows the hand and opens at the front (BD22's
//     open sound; a spent case falls out);
//   let go, take a 40 mm round away from the gun (the "Grab ammo with" button), tilt its nose
//     into the breech and push it home (BD22's load sound, one round of the chosen ammo taken);
//   stabilize and pull back: the tube follows the hand and locks shut (BD22's close sound).
// While the tube is open the rifle is drawn without it in every frame it shows (the tube is its
// own layer), so firing or anything else never snaps it shut. Nothing loads the launcher by
// itself (BD22's own reload animation only runs out of VR or with Real reload off).
// Two rifles (or a rifle in the off hand): a flick (rsq/flick.zs) loads the empty launcher with
// the magazine, and each hand's secondary fire is its launcher (Rifle.dec RSM_ states).
//
// Netplay: everything that decides runs in the playsim from the synced hand poses and usercmd
// buttons; the layers and the hand's pose are drawn from that state.

class RSM abstract play
{
	const TUBE = 2130;			// RSR_GunParts (main controller): the tube, off its rest
	const ROUND = 2131;			// RSR_GunParts: the round going in / in the open tube
	const LAYER_FIRST = 2130;
	const LAYER_LAST = 2131;

	// what the hand has
	const EMPTY = 0;
	const CARRY = 1;			// a round in the hand
	const INSERT = 2;			// the round in the breech, as far as the hand pushes it

	// cm, degrees
	const NEAR = 9.0;			// the palm this close to the tube's track: on the tube
	const LEAVE = 13.0;			// ...further than this: off it
	const OPEN_FRAC = 0.92;		// of the travel: open (the click, the case out)
	const SHUT_FRAC = 0.06;		// of the travel: shut again
	const RELOCK = 0.6;			// let go this close to shut and the latch takes it again
	const POUCH_MIN = 20.0;		// a round is taken at least this far from the breech
	const ENTER_SIDE = 5.0;		// the round's middle this close to the bore's line goes in
	const LEAVE_SIDE = 7.5;		// ...further off than this: back in the hand
	const ENTER_ANGLE = 40.0;	// ...nose within this of the bore
	const SEAT = 0.6;			// home within this
	const KINDS = 9;			// 2.0.5d: RSQ Grenade's kinds (kinds.zs): frag, impact, incendiary, freeze, stun, smoke, flash, charm, infight

	clearscope static bool IsRifle(Weapon w)
	{
		return w && w.GetClassName() == 'Rifle';
	}

	// 1.97: the guns with a launcher the module works: 1 the rifle, 2 the BD21 Machinegun (c2q/bd22_mg.py)
	clearscope static int GunOf(Weapon w)
	{
		if (!w) return 0;
		Name n = w.GetClassName();
		if (n == 'Rifle') return 1;
		if (n == 'Machinegun') return 2;
		return 0;
	}

	clearscope static bool IsAnyRifle(Weapon w)
	{
		return w && (w.GetClassName() == 'Rifle' || w.GetClassName() == 'RSQ_Off_Rifle');
	}

	// the option (Underbarrel ammo): 0 rockets (as BD22), 1 hand grenades. A server setting: it
	// decides what is taken.
	// 2.0.5b (owner 2026-11-17: "i cannot load bd22 overunder with the RSQ grenade"): Hand grenades
	// means the hand grenades you carry. With RSQ Grenade's grenade replacing Brutal Doom's
	// (RSG_Handler.StandDown: rsqgn_replace_bd, on by default, or rsg_rsq_nade), those are RSQ
	// Grenade's (RSQGN_Ammo, by name at run time: nothing of it is named when this compiles), not
	// BD22's GrenadeAmmo, which nothing shows or throws then: the launcher took no round. Without RSQ
	// Grenade, or with it standing down, GrenadeAmmo as before.
	static class<Inventory> AmmoClass()
	{
		let cv = CVar.FindCVar('rsm_ammo');
		Name n = cv && cv.GetInt() == 1 ? 'GrenadeAmmo' : 'AmmoRocket';
		if (n == 'GrenadeAmmo' && RSG_Handler.StandDown())
		{
			Name rn = 'RSQGN_Ammo';
			class<Inventory> rc = rn;
			if (rc)
				return rc;
		}
		class<Inventory> c = n;
		return c;
	}

	// 2.0.5d RSQ GRENADE'S GRENADES IN THE LAUNCHER (owner 2026-11-17: "we grab grenade, alt fire cycle to the one we want
	// (i assume the tacticalrig remembers the type of grenade stored) and we load it into the launcher. So, we could load a
	// charm grenade into the rifle, but still switch to a different kind of throwable grenade later"). While RSQ Grenade's
	// grenade is the one you carry (RSG_Handler.StandDown, as AmmoClass), the open launcher takes a grenade from RSQ Tactical
	// Rig's GRENADE SPOT too (the rig's "nade.at"): a small grenade of your kind (RSQ Grenade's "kind": the rig keeps no kind of
	// its own, the one you picked is the one you get) in the off hand, in its kind's skin (MODELDEF.rsmnade); the off hand's
	// alt trigger cycles it with RSQ Grenade's own rules, and that is your kind ("kind.next"); pushed home it costs one of
	// RSQ Grenade's grenades (RSQGN_Ammo) and the round keeps ITS kind (RSM_State.loadedNade) whatever kind you pick after.
	// Fired, it flies as the launcher's own round (RSM_KindRound, DECORATE.rsm: ShortGrenade's flight) and bursts as that
	// kind's grenade, through RSQ Grenade's own blast ("burst"). The ammo pouch's round is the launcher's plain round, as before.
	// Everything of RSQ Grenade and the rig is asked by name: without them nothing here happens.
	static bool RsqNades()
	{
		Name rn = 'RSQGN_Ammo';
		class<Inventory> rc = rn;
		return rc && RSG_Handler.StandDown();
	}

	static class<Inventory> NadeAmmo()
	{
		Name rn = 'RSQGN_Ammo';
		class<Inventory> rc = rn;
		return rc;
	}

	static Service GnSvc()
	{
		let it = ServiceIterator.Find("RSQGN_Service");
		Service s;
		while (s = it.Next())
			if (s.GetClassName() == 'RSQGN_Service')
				return s;
		return null;
	}

	// the player's grenade kind now (RSQ Grenade's own choice), 0 the frag
	static int CurKind(PlayerPawn mo)
	{
		let s = GnSvc();
		return s ? clamp(s.GetInt("kind", "", mo.PlayerNumber()), 0, KINDS - 1) : 0;
	}

	// the off hand's alt trigger on the small grenade: RSQ Grenade's own cycle; the kind now, or -1 (no answer)
	static int NextKind(PlayerPawn mo)
	{
		let s = GnSvc();
		if (!s)
			return -1;
		int k = s.GetInt("kind.next", "", mo.PlayerNumber(), 1, mo);
		return k >= 0 && k < KINDS ? k : -1;
	}

	// the off hand at the rig's grenade spot: 1 at it, 0 not, -1 no grenade spot (as RSR.RigPouch)
	static int RigNadeSpot(PlayerPawn mo)
	{
		let it = ServiceIterator.Find("RSQTR_RigService");
		Service s;
		while (s = it.Next())
			return s.GetInt("nade.at", "", 1, 0, mo);
		return -1;
	}

	// real reload in VR (as RSR_ReloadHandler.Wanted, but the off hand may hold a gun: dual)
	static bool VRReload(PlayerPawn mo)
	{
		return mo && mo.player && RSR.PlayerInt(mo.player, 'rsr_reload', 0) == 1 && RSVR_VRHand.InVR(mo)
			&& mo.CountInv('IsPlayingAsPurist') <= 0;
	}

	// rsq/flick.zs: a flick reloads this hand's empty launcher too (dual)
	static void FlickLoad(PlayerPawn mo, bool offHand)
	{
		if (!VRReload(mo))
			return;
		Name loaded = offHand ? 'RSM_LoadedOff' : 'RFGLoaded';
		if (mo.CountInv(loaded) > 0)
			return;
		let ac = AmmoClass();
		if (!ac || mo.CountInv(ac) <= 0)
			return;
		mo.TakeInventory(ac, 1);
		mo.TakeInventory(offHand ? 'RSM_FiredOff' : 'FiredMGGrenade', 0x7FFFFFFF);
		mo.GiveInventory(loaded, 1);
		mo.A_StartSound("GrenadeLauncher/Load", CHAN_AUTO, CHANF_OVERLAP);
	}
}

class RSM_State play
{
	int gun;					// 1.97: RSM.GunOf (1 rifle, 2 machinegun)
	double pull, pullPrev;		// cm the tube is forward
	bool unlatched;
	bool held;					// the hand has the tube
	double grabS;
	bool isOpen;				// it reached the front (clicked open) this cycle
	int hand;
	double rr, rrPrev;			// INSERT: the round's rear, F
	bool roundIn;				// a round home in the open tube
	bool trigPrev, grabPrev;
	bool active;				// the rifle is up and the hand works it (drawn)
	bool steadied;
	RSR_State geo;
	Vector3 palm;
	Array<int> noTubeFrom, noTubeTo;	// rifle sprite -> its no-tube twin (1.33)
	// 2.0.5d RSQ Grenade's grenades (RSM.RsqNades): 0 the launcher's plain round, else 1 + an RSQ Grenade kind
	int roundNade;				// the round in the hand, in the breech or home in the open tube
	int loadedNade;				// the round in the shut launcher (beside RFGLoaded; kept over a gun switch and a new map, as
								// RFGLoaded is; gone with it)
	bool altPrev;				// the off hand's alt trigger last tic (cycles the small grenade's kind)
	bool rfgWas;				// RFGLoaded at the last WorldTick

	void Log(PlayerPawn mo, String what)
	{
		if (RSR.Debug(mo.player))
			Console.Printf("rsm t%d pull %.1f hand %d: %s", mo.Level.maptime, pull, hand, what);
	}

	void Snd(PlayerPawn mo, Sound s)
	{
		mo.A_StartSound(s, CHAN_AUTO, CHANF_OVERLAP);
	}

	// the palm's distance from the tube (where it is now)
	double TubeDist(Vector3 p)
	{
		double f0 = RSM_Geo.TubeRear(gun) + pull;
		double f1 = RSM_Geo.TubeFront(gun) + pull;
		double f = clamp(p.x, f0, f1);
		return (p - (f, RSM_Geo.AxisL(gun), RSM_Geo.AxisU(gun))).Length();
	}

	double Side(Vector3 p)
	{
		return ((0, p.y, p.z) - (0, RSM_Geo.AxisL(gun), RSM_Geo.AxisU(gun))).Length();
	}

	void Reset()
	{
		pull = pullPrev = 0;
		unlatched = held = isOpen = roundIn = false;
		hand = RSM.EMPTY;
		roundNade = 0;
		rr = rrPrev = 0;
	}

	void Tick(PlayerPawn mo)
	{
		let p = mo.player;
		pullPrev = pull;
		rrPrev = rr;
		if (!geo)
			geo = new('RSR_State');
		geo.Frames(mo);
		palm = RSM_Geo.ToGun(gun, geo.OffPoint(RSR.PalmGrab()));	// batch 4: in the rifle's original frame
		steadied = RSVR_VRHand.Steadied(mo);
		bool trig = (p.cmd.buttons & BT_OFFHANDATTACK) != 0;
		bool trigPress = trig && !trigPrev;
		trigPrev = trig;
		let rs = RSR_ReloadHandler.StateOf(mo);
		bool grab = rs && rs.Grip(mo);
		bool grabPress = grab && !grabPrev;
		grabPrev = grab;
		// 2.0.5d: the off hand's alt trigger. QuestZDoom's grip can shift the trigger to alt fire (RSQ Grenade hand.zs: a
		// hand closed round a grenade and squeezing sends alt fire), so while it holds a small grenade, alt fire held is
		// holding it too, and its press cycles the kind
		bool alt = (p.cmd.buttons & BT_OFFHANDALTATTACK) != 0;
		bool altPress = alt && !altPrev;
		altPrev = alt;
		bool holding = grab || (roundNade > 0 && alt);
		// a magazine reload has the hand
		if (rs && rs.phase != RSR.IDLE && rs.weap == p.ReadyWeapon)
		{
			held = false;
			if (hand != RSM.EMPTY)
			{
				hand = RSM.EMPTY;
				roundNade = 0;
			}
			return;
		}

		bool loaded = mo.CountInv('RFGLoaded') > 0;
		// 1.33 (owner): stabilized, the OFF TRIGGER is the latch (the launcher fires from the
		// rifle's secondary fire: Rifle.dec AltFire)
		if (steadied && trigPress && pull <= 0 && !unlatched && hand == RSM.EMPTY)
		{
			unlatched = true;
			Snd(mo, "Weapon/Empty");
			geo.Buzz(mo);
			Log(mo, "latch");
		}

		// the tube. Opening: stabilized with the latch, the hand pushes it out. Open: 1.35 (owner:
		// "gripping empty space is disorienting") the hand takes the tube itself, where it is now:
		// at it, the off trigger or the grip (stabilized) holds it, and the hand pulls it shut.
		bool onTube = TubeDist(palm) < (held ? RSM.LEAVE : RSM.NEAR);
		bool wants;
		if (isOpen)
			wants = hand == RSM.EMPTY && onTube && (trig || steadied);
		else
			wants = steadied && hand == RSM.EMPTY && (unlatched || pull > 0);
		if (held && !wants)
		{
			held = false;
			Log(mo, "let go of the tube");
		}
		else if (!held && wants)
		{
			held = true;
			grabS = palm.x - pull;
			Log(mo, "took the tube");
		}
		if (held)
		{
			double np = palm.x - grabS;
			if (np < 0)
			{
				grabS = palm.x;
				np = 0;
			}
			else if (np > RSM_Geo.TravelOf(gun))
			{
				grabS = palm.x - RSM_Geo.TravelOf(gun);
				np = RSM_Geo.TravelOf(gun);
			}
			pull = np;
		}
		if (!isOpen && pull >= RSM.OPEN_FRAC * RSM_Geo.TravelOf(gun))
		{
			isOpen = true;
			Snd(mo, "GrenadeLauncher/Open");
			geo.Buzz(mo);
			if (mo.CountInv('FiredMGGrenade') > 0)
			{
				mo.TakeInventory('FiredMGGrenade', 0x7FFFFFFF);
				CaseOut(mo);
			}
			Log(mo, "open");
		}
		if (isOpen && pull <= RSM.SHUT_FRAC * RSM_Geo.TravelOf(gun))
		{
			pull = 0;
			isOpen = held = unlatched = false;
			Snd(mo, "GrenadeLauncher/Close");
			geo.Buzz(mo);
			if (roundIn)
			{
				roundIn = false;
				mo.GiveInventory('RFGLoaded', 1);
				loadedNade = roundNade;		// 2.0.5d: the round keeps its own kind (0: the plain round)
				roundNade = 0;
				Log(mo, loadedNade > 0 ? String.Format("shut: loaded (RSQ Grenade kind %d)", loadedNade - 1) : "shut: loaded");
			}
			else
				Log(mo, "shut: empty");
		}
		if (!isOpen && pull < RSM.RELOCK && !trig)
		{
			// back at rest without opening, the latch let go: it locks again
			pull = 0;
			unlatched = false;
		}

		// the round
		Vector3 mid = RSM_Geo.ToGun(gun, geo.OffPoint(RSM_Geo.RoundInHand()));	// batch 4: in the rifle's original frame
		Vector3 nose = RSM_Geo.DirToGun(gun, geo.OffDirInGun(RSM_Geo.RoundAxisInHand()));
		double rear = mid.x - nose.x * RSM_Geo.RoundLen(gun) / 2;
		double seatF = RSM_Geo.TubeRear(gun) + pull + RSM_Geo.RoundSeat(gun);
		switch (hand)
		{
		case RSM.EMPTY:
		{
			if (!grabPress || !isOpen || roundIn || loaded)
				break;
			// 2.0.5d: at the rig's grenade spot, RSQ Grenade's grenade of your kind (RSM.RsqNades); none carried, nothing
			if (RSM.RsqNades() && RSM.RigNadeSpot(mo) == 1)
			{
				let nc = RSM.NadeAmmo();
				if (!nc || mo.CountInv(nc) <= 0)
				{
					Log(mo, "grenade spot: no grenades");
					break;
				}
				roundNade = 1 + RSM.CurKind(mo);
				hand = RSM.CARRY;
				geo.Buzz(mo);
				Log(mo, String.Format("took a grenade from the grenade spot (kind %d)", roundNade - 1));
				break;
			}
			let ac = RSM.AmmoClass();
			if (!ac || mo.CountInv(ac) <= 0)
				break;
			Vector3 breech = ((RSM_Geo.FrameFront(gun) + seatF) / 2, RSM_Geo.AxisL(gun), RSM_Geo.AxisU(gun));
			int rp = RSR.RigPouch(mo);		// 2.0.3u: the rig's ammo pouch only (vreload.zs RSR.RigPouch)
			if (rp == 0)
				break;
			if (rp < 0 && (palm - breech).Length() < RSM.POUCH_MIN)
				break;
			roundNade = 0;				// the pouch: the launcher's plain round
			hand = RSM.CARRY;
			geo.Buzz(mo);
			Log(mo, "took a round");
			break;
		}
		case RSM.CARRY:
		{
			if (!holding || !isOpen)
			{
				hand = RSM.EMPTY;		// back in the pouch (nothing was taken)
				roundNade = 0;
				Log(mo, "let the round go");
				break;
			}
			// 2.0.5d: the small grenade's kind, cycled by the off hand's alt trigger (RSQ Grenade's own cycle: your kind)
			if (roundNade > 0 && altPress)
			{
				int nk = RSM.NextKind(mo);
				if (nk >= 0 && nk != roundNade - 1)
				{
					roundNade = 1 + nk;
					Log(mo, String.Format("grenade kind %d", nk));
				}
			}
			double ang = acos(clamp(nose.x, -1, 1));
			if (Side(mid) < RSM.ENTER_SIDE && ang < RSM.ENTER_ANGLE
				&& mid.x > RSM_Geo.FrameFront(gun) - 4 && mid.x < seatF + RSM_Geo.RoundLen(gun) / 2 + 2)
			{
				hand = RSM.INSERT;
				rr = rrPrev = clamp(rear, RSM_Geo.FrameFront(gun) - RSM_Geo.RoundLen(gun), seatF);
				geo.Buzz(mo);
				Log(mo, "round in the breech");
			}
			break;
		}
		case RSM.INSERT:
		{
			rr = clamp(rear, RSM_Geo.FrameFront(gun) - RSM_Geo.RoundLen(gun), seatF);
			bool home = rr >= seatF - RSM.SEAT;
			if (!holding && rr >= seatF - RSM_Geo.RoundLen(gun) / 2)
				home = true;			// let go half in: it slides home
			if (home)
			{
				let ac = roundNade > 0 ? RSM.NadeAmmo() : RSM.AmmoClass();	// 2.0.5d: a grenade from the grenade spot is one of RSQ Grenade's
				if (ac)
					mo.TakeInventory(ac, 1);
				roundIn = true;
				hand = RSM.EMPTY;
				Snd(mo, "GrenadeLauncher/Load");
				geo.Buzz(mo);
				Log(mo, "round home");
				break;
			}
			if (!holding || !isOpen)
			{
				hand = RSM.EMPTY;
				roundNade = 0;
				Log(mo, "let the round go");
				break;
			}
			if (Side(mid) > RSM.LEAVE_SIDE || mid.x < RSM_Geo.FrameFront(gun) - 10)
			{
				hand = RSM.CARRY;
				Log(mo, "round out of the breech");
			}
			break;
		}
		}
	}

	// 1.36 (owner): the fired round's spent case, the round cut down and darker, drops out of the
	// breech to the ground when the tube opens
	void CaseOut(PlayerPawn mo)
	{
		Vector3 at = (RSM_Geo.FrameFront(gun) + 3, RSM_Geo.AxisL(gun), RSM_Geo.AxisU(gun) - 1);
		Vector3 pos = RSVR_VRHand.HandPos(mo) + geo.FromGun(RSM_Geo.FromGun(gun, at));	// batch 4: the moved breech
		let a = Actor.Spawn('RSM_SpentCase', pos);
		if (!a)
			return;
		a.angle = atan2(geo.F.y, geo.F.x);
		a.pitch = -asin(clamp(geo.F.z, -1, 1));
		a.vel = mo.vel + geo.FromGun((0, -25, -40)) * 0.06;
		a.target = mo;
	}

	// after the psprites tick: the gun without its tube while the tube is off its rest
	void Draw(PlayerPawn mo)
	{
		let p = mo.player;
		let psp = p.FindPSprite(PSP_WEAPON);
		bool shown = active && pull > 0.01;
		bool swapped = false;
		if (shown && psp)
		{
			// 1.33: whatever rifle frame is showing, its twin without the tube (MODELDEF.rsm)
			if (noTubeFrom.Size() == 0)
			{
				Array<Name> f, t;
				if (gun == 2) RSM_NoTube.NamesMG(f, t); else RSM_NoTube.Names(f, t);
				for (int k = 0; k < f.Size(); k++)
				{
					noTubeFrom.Push(Actor.GetSpriteIndex(f[k]));
					noTubeTo.Push(Actor.GetSpriteIndex(t[k]));
				}
			}
			int s = psp.Sprite;
			int k = noTubeFrom.Find(s);
			if (k < noTubeFrom.Size())
			{
				psp.Sprite = noTubeTo[k];
				swapped = true;
			}
			else if (noTubeTo.Find(s) < noTubeTo.Size())
				swapped = true;
		}
		bool round = active && (hand == RSM.INSERT || roundIn && pull > 0.5);
		let parts = RSR_GunParts(mo.FindInventory('RSR_GunParts'));
		if (!parts && (swapped || round))
		{
			mo.GiveInventory('RSR_GunParts', 1);
			parts = RSR_GunParts(mo.FindInventory('RSR_GunParts'));
		}
		RSR.SetPart(p, RSM.TUBE, parts, swapped, gun == 2 ? 'RQ3P' : 'RQ2P', 0);
		// 2.0.5d: an RSQ Grenade round is its kind's small grenade (MODELDEF.rsmnade frames C..K: 2 + the kind)
		RSR.SetPart(p, RSM.ROUND, parts, round, gun == 2 ? 'RQ3P' : 'RQ2P', roundNade > 0 ? roundNade + 1 : 1);
	}
}

// 1.36: the spent 40 mm case on the ground (MODELDEF.rsm)
class RSM_SpentCase : RSR_DroppedMag
{
	Default
	{
		Radius 1;
		Height 1;
		BounceFactor 0.35;
		WallBounceFactor 0.35;
		BounceSound "GrenadeLauncher/Casing";
	}

	States
	{
	Spawn:
		RQ2C A 1;
		Loop;
	Death:
		RQ2C A 0 { pitch = 0; roll = 90; }
		RQ2C A 350;
		RQ2C A 1 A_FadeOut(0.05);
		Wait;
	}
}

// the tokens (the weapon reads them)
class RSM_VR : RSVR_Token {}			// the launcher is loaded by hand (VR, Real reload)
class RSM_Dual : RSVR_Token {}
class RSM_Steady : RSVR_Token {}		// one rifle, the off hand on it: main secondary fire is the launcher			// the off hand holds a gun: alt fire is each rifle's launcher
class RSM_LoadedOff : RSVR_Token {}		// the off-hand rifle's launcher has a round
class RSM_FiredOff : RSVR_Token {}		// ...and a spent case
class RFGrenadeOff : RSVR_Token {}		// fire the off-hand rifle's launcher

// 2.0.5d RSQ GRENADE'S GRENADE FIRED FROM THE LAUNCHER (RSM.RsqNades). With one loaded (RSM_KindLoaded) the Rifle and the
// Machinegun fire RSM_KindRound in place of BD22's ShortGrenade (Rifle.dec FireGrenade / FireGrenade2, Machinegun.dec
// RSM_Fire); on its first think it takes the kind loaded (RSK_M203Handler.WorldThingSpawned, Arm). RSM_KindRound
// (DECORATE.rsm) is ShortGrenade itself -- its speed, fall, trail, sprite, direct hit -- with only its burst changed, which is
// RSQ Grenade's grenade of the round's kind going off there (RSQGN_Service "burst": its look, blast and effect: the freeze,
// the fire, the stun, the smoke, the flash, the charm, the infight). The direct hit keeps the round's own damage unless the
// kind does no blast damage (RSQ Grenade's "kind.share" 0: freeze, smoke, flash, charm, infight), when it hits for none, so a
// charm round does not kill the monster it charms. RSQ Grenade gone: Brutal Doom's own 40 mm explosion, as a plain round.
class RSM_Nades play
{
	// the fired round (RSM_KindRound) takes its kind; a kind that does no blast damage hits for none
	static void Arm(Actor r, int kind)
	{
		r.SetInventory('RSM_RoundKind', kind + 1);
		if (Share(kind, r.target) <= 0)
			r.SetDamage(0);
		if (r.target && r.target.player && RSR.Debug(r.target.player))
			Console.Printf("rsm t%d: fired RSQ Grenade kind %d", r.Level.maptime, kind);
	}

	static double Share(int kind, Actor by)
	{
		let s = RSM.GnSvc();
		return s ? s.GetDouble("kind.share", "", kind, 0, by) : 1.0;
	}

	// the kind's burst where `at` is, `at.target`'s (kind -1, or no RSQ Grenade: Brutal Doom's own 40 mm explosion's
	// damage, UGBLExplosion)
	static void Burst(Actor at, int kind)
	{
		let s = kind >= 0 ? RSM.GnSvc() : null;
		if (s && s.GetInt("burst", "", kind, 0, at) == 1)
			return;
		String un = "UGBLExplosion";
		class<Actor> uc = un;
		let e = uc ? Actor.Spawn(uc, at.pos, ALLOW_REPLACE) : null;
		if (e)
			e.target = at.target;
	}
}

// the round's kind, carried by the fired round (1 + the kind)
class RSM_RoundKind : Inventory
{
	Default
	{
		Inventory.MaxAmount 16;
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
	}
}

// given to RSM_KindRound by its own explosion frame (DECORATE.rsm): the burst, at once, where the round is
class RSM_KindBurst : Inventory
{
	Default
	{
		Inventory.MaxAmount 1;
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
	}

	override void AttachToOwner(Actor other)
	{
		Super.AttachToOwner(other);
		if (other)
			RSM_Nades.Burst(other, other.CountInv('RSM_RoundKind') - 1);
	}
}

// the player's launcher holds an RSQ Grenade grenade (RSM_State.loadedNade): its weapon fires RSM_KindRound
class RSM_KindLoaded : RSVR_Token {}

// RSQ Tactical Rig asks, by name: while the launcher is open for loading, that hand's press at the grenade spot is the
// launcher's (the rig hands out no hand grenade then). "ubl.loading" intArg the hand (1 the off hand, the one that loads),
// objectArg the pawn -> 1 / 0.
class RSM_LauncherService : Service
{
	override int GetInt(String request, String stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		if (request != "ubl.loading" || intArg != 1)
			return 0;
		let mo = Actor(objectArg);
		return mo && RSK_M203Handler.Busy(mo.PlayerNumber()) ? 1 : 0;
	}
}

// every sprite name MODELDEF.rsm keys, so the engine knows them; never spawned
class RSM_Sprites : Actor
{
	States
	{
	Spawn:
		RQ2T A 0;
		RQ2P AB 0;
		RQ3P AB 0;	// 1.97: the Machinegun's tube and round
		RQ2P CDEFGHIJK 0;	// 2.0.5d: RSQ Grenade's small grenade in the tube, a frame a kind (MODELDEF.rsmnade)
		RQ3P CDEFGHIJK 0;
		QU00 A 0;
		QU01 A 0;
		QU02 A 0;
		RQ2H AB 0;
		RQ2H CDEFGHIJK 0;	// 2.0.5d: ...and in the off hand
		RQ2S AB 0;
		RQ2C A 0;
		Stop;
	}
}

class RSK_M203Handler : EventHandler
{
	RSM_State st[MAXPLAYERS];

	clearscope static RSK_M203Handler Get()
	{
		return RSK_M203Handler(EventHandler.Find('RSK_M203Handler'));
	}

	clearscope static RSM_State Peek(Actor mo)
	{
		let h = Get();
		if (!h || !mo || !mo.player)
			return null;
		int n = mo.PlayerNumber();
		return n >= 0 && n < MAXPLAYERS ? h.st[n] : null;
	}

	// rsr/vreload.zs InputProcess: while the tube is open (or a round is in the hand) the off hand
	// is loading, so "Grab ammo with" Use / grip is taken over for the grab, as in a reload (1.34)
	clearscope static bool Busy(int n)
	{
		let h = Get();
		let s = h && n >= 0 && n < MAXPLAYERS ? h.st[n] : null;
		return s && s.active && (s.isOpen || s.hand != RSM.EMPTY);
	}

	// rsq/hands.zs: the free hand while it works the launcher ("" = the hands' own)
	clearscope static String FreeHand(Actor mo)
	{
		let s = Peek(mo);
		if (!s || !s.active)
			return "";
		if (s.hand == RSM.CARRY)
			return s.roundNade > 0 ? "RsmNade" .. (s.roundNade - 1) : "RsmRound";	// Ermac's open grip round a 40 mm round; 2.0.5d: or round RSQ Grenade's small grenade, its kind's skin
		if (s.hand == RSM.INSERT)
			return "RsmGrip";			// the same grip; the round is on the gun (layer RSM.ROUND)
		if (s.held && !s.steadied)
			return "AmmoH";				// 1.35: a closed hand on the open tube
		return "";						// stabilized: the support hand (on the launcher, rsq/hands.zs)
	}

	// rsq/hands.zs: stabilized with the launcher shut, the support hand holds it with its finger on
	// the launcher's trigger (MODELDEF.rsm RQ2S, baked in place: no hook); working the tube, it
	// holds the tube (the hand table's grip) and rides it
	clearscope static bool TriggerGrip(Actor owner)
	{
		return false;	// 1.32 (owner, option 2): the off hand stays on the tube; the off trigger fires the launcher
	}

	// rsq/hands.zs: the support hand rides the tube (hand-model hook units)
	clearscope static Vector3 SupportShift(Actor owner, double ticfrac)
	{
		let s = Peek(owner);
		if (!s || !s.active)
			return (0, 0, 0);
		return RSM_Geo.FwdHook(s.gun) * (s.pullPrev + (s.pull - s.pullPrev) * ticfrac);
	}

	clearscope static bool Places(Actor owner, int layer)
	{
		return layer >= RSM.LAYER_FIRST && layer <= RSM.LAYER_LAST;
	}

	clearscope static Vector3, Vector3 Place(Actor owner, Vector3 t, Vector3 r, int layer, double ticfrac)
	{
		let s = Peek(owner);
		if (!s)
			return t, r;
		double pl = s.pullPrev + (s.pull - s.pullPrev) * ticfrac;
		if (layer == RSM.TUBE)
			return t + RSM_Geo.FwdHook(s.gun) * pl, r;
		if (s.hand == RSM.INSERT)
		{
			double rv = s.rrPrev + (s.rr - s.rrPrev) * ticfrac;
			return t + RSM_Geo.FwdHook(s.gun) * (rv - RSM_Geo.TubeRear(s.gun) - RSM_Geo.RoundSeat(s.gun)), r;
		}
		return t + RSM_Geo.FwdHook(s.gun) * pl, r;
	}

	// 2026-10-23 (owner): a new map starts clean. Level.maptime restarts at 0, so anything
	// still half-done across an exit is timed against a clock that no longer exists, and some
	// of it could never finish. This is the quiet put-away -- NOT Abort(), which drops the
	// magazine or shell into the world and would litter the new map. Fires for a loaded
	// savegame too, which is wanted.
	override void WorldLoaded(WorldEvent e)
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n] || !players[n].mo || !st[n])
				continue;
			st[n].Reset();
		}
	}

	// 2.0.5d: a launcher just fired an RSQ Grenade grenade (Rifle.dec / Machinegun.dec: RSM_KindLoaded held, RSM_KindRound
	// fired): the round takes the kind loaded (RSM_RoundKind). WorldThingSpawned comes on the round's first think, before it
	// moves, with its target (the shooter) set (RSQ_Muzzle relies on the same).
	override void WorldThingSpawned(WorldEvent e)
	{
		let a = e.thing;
		if (!a || a.GetClassName() != 'RSM_KindRound')
			return;
		let pmo = PlayerPawn(a.target);
		int n = pmo && pmo.player ? pmo.PlayerNumber() : -1;
		let s = n >= 0 && n < MAXPLAYERS ? st[n] : null;
		if (!s || s.loadedNade <= 0)
			return;					// no kind: it bursts as the plain round (RSM_KindBurst)
		RSM_Nades.Arm(a, s.loadedNade - 1);
		s.loadedNade = 0;
		pmo.TakeInventory('RSM_KindLoaded', 1);
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n] || !players[n].mo)
				continue;
			let mo = players[n].mo;
			let p = mo.player;
			if (!st[n])
				st[n] = new('RSM_State');
			let s = st[n];
			// 2.0.5d: the round left the launcher another way (death, BD22's own reload): RFGLoaded gone for a whole tic. (On the
			// tic it is fired, RFGLoaded is gone here already and the round has not thought yet: WorldThingSpawned takes it then.)
			bool rfg = mo.CountInv('RFGLoaded') > 0;
			if (s.loadedNade > 0 && !rfg && !s.rfgWas)
				s.loadedNade = 0;
			s.rfgWas = rfg;
			bool vr = RSM.VRReload(mo);
			bool dual = p.OffhandWeapon && !(p.OffhandWeapon is 'RSQ_Hands');
			Sync(mo, 'RSM_VR', vr);
			Sync(mo, 'RSM_Dual', dual);
			if (mo.health <= 0)
				s.Reset();
			int gn = RSM.GunOf(p.ReadyWeapon);	// 1.97
			if (gn != s.gun)
			{
				s.Reset();
				s.gun = gn;
				s.noTubeFrom.Clear(); s.noTubeTo.Clear();
			}
			s.active = vr && !dual && gn > 0 && RSR_ReloadHandler.Wanted(mo);
			if (s.active)
				s.Tick(mo);
			else
			{
				s.held = false;
				s.pullPrev = s.pull;
				if (s.hand != RSM.EMPTY)
				{
					s.hand = RSM.EMPTY;
					if (!s.roundIn)
						s.roundNade = 0;
				}
			}
			Sync(mo, 'RSM_Steady', s.active && s.steadied);
			Sync(mo, 'RSM_KindLoaded', s.loadedNade > 0);	// 2.0.5d: the weapon fires RSM_KindRound (Rifle.dec, Machinegun.dec)
			s.Draw(mo);
		}
	}

	static void Sync(PlayerPawn mo, Name tok, bool on)
	{
		if (on && mo.CountInv(tok) <= 0)
			mo.GiveInventory(tok, 1);
		else if (!on && mo.CountInv(tok) > 0)
			mo.TakeInventory(tok, 1);
	}
}
