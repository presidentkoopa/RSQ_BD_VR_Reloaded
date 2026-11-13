// 2.0.4r THE AXE POOL (owner 2026-11-12 20:42-20:5x; replaces 2.0.3j..2.0.4q's two separate axes, one per hand).
//
//   1. Axes are a count, up to 10 (RSVR_Axes, the axe's own ammo: Axe.dec), shared by both hands. One axe in the Wheel;
//      either or both hands can hold one at once. Holding costs nothing, each throw from either hand spends one
//      (melee.zs HoldOrThrow); at 0 the hand that threw goes to its fist, and so does a hand still holding one
//      (melee.zs AxePool). Gun Bonsai VR treats the axe as one weapon (RSQ_UBQSeries GunBonsaiOffhandVR).
//   2. A pickup is +1, like any weapon you own giving its ammo -- walked over, or grabbed with Distance Grab (an axe you
//      did NOT throw: a map axe, an enemy's drop).
//   3. YOUR THROWN AXE lies on the ground 5 s: from 2 s it blinks RED, faster and faster, and at 5 s it is gone (no
//      litter). Distance-grabbed back before then: that throw HIT something (a monster, anything shootable) -> +2, and
//      with MK Crits loaded the NEXT axe throw is a guaranteed critical; it hit nothing -> +1. Never above 10.
//   4. (RSQ Tactical Rig) the axe's holster gives an axe while you have axes, and is unassigned at 0.
//   5. AMMO FULL for axes only at 10.
//
// Distance Grab asks before the pickup ("pickup.first", grab.event; RSQ_UBQSeries DistanceGrab flight.zs TakeInto): an
// axe is ours to give -- +1, or +2 for your own thrown axe after a hit -- into the hand that grabbed it; -1 at 10 (AMMO
// FULL). Without Distance Grab nothing asks, and every axe is the engine's own pickup (+1).
//
// 2.0.4s THE COUNT IS THE AXES YOU HAVE, THE ONES IN YOUR HANDS INCLUDED (owner 2026-11-12 21:36, in his headset: "why do i
// have 0 axes but still an axe in hand?"). 2.0.4r let both hands hold an axe on a count of 1 (the throwing hand took "the
// next axe" while the other hand still held the last one; the Wheel, a slot key or a holster put the axe in the second
// hand), so the next throw left the count at 0 with an axe still in the other hand until its switch-away played out (and
// longer while that hand was winding up a throw -- which then threw an axe from nothing). Now, everywhere:
//   - axes in hands <= the count. A throw spends one; the throwing hand takes the next axe only if one is left that the
//     other hand is not holding (RSVR_MainAxeNext / RSVR_OffAxeNext, Axe.dec AxeRearm / OffAxeRearm); otherwise it is
//     empty AT ONCE (ToEmpty: its empty hand, the tic of the throw, no lowering).
//   - anything else that puts an axe in a second hand the count cannot cover (the Wheel, a slot key, a holster) moves the
//     axe: the hand that held it is empty at once (melee.zs AxePool, every tic, before the weapons tick);
//   - at 0 no hand holds an axe, none is on its way to one, and no throw is made.
// 2.0.4s DISTANCE GRAB ALWAYS EQUIPS (owner 21:36: "lets have axe always switch to when distance grabbed"): an axe caught by
// Distance Grab (a pull or the walk-up grip) goes INTO the hand that grabbed it -- a main hand holding a gun switches to it
// too -- whatever neverswitchonpickup says. Walking over an axe stays Doom's own pickup (your neverswitchonpickup).

class RSVR_Axes : Ammo
{
	Default
	{
		Inventory.MaxAmount 10;
		Ammo.BackpackAmount 0;
		Ammo.BackpackMaxAmount 10;
		Inventory.PickupMessage "";
		Inventory.Icon "AXE9A0";	// 2.0.4s: BD22's own floor axe, so a HUD that draws the ammo's picture has one
		Tag "Axes";
		+INVENTORY.IGNORESKILL		// a pickup is one axe on every skill
		+INVENTORY.KEEPDEPLETED		// 0 is a count too (melee.zs AxePool: no item = a game from before 2.0.4r)
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
	}
}

class RSVR_AxeCritNext : RSVR_Token {}	// the next axe throw is a guaranteed critical (MK Crits)
class RSVR_MainAxeNext : RSVR_Token {}	// 2.0.4s: the main hand threw and an axe is left for it (Axe.dec AxeRearm)
class RSVR_OffAxeNext : RSVR_Token {}	// 2.0.4s: the off hand threw and an axe is left for it (Axe.dec OffAxeRearm)
class RSVR_AxePoolInit : RSVR_Token {}	// melee.zs AxePool: a game from before 2.0.4r was given its count (once)

// one thrown axe of one player: in the air, then on the ground (or in a wall)
class RSVR_ThrownAxe play
{
	PlayerPawn who;
	Actor proj;		// ThrowedAxe / ThrowedAxeStrong in flight
	Actor item;		// what it left: a BrutalAxe on the floor, a BrutalAxeOnWall
	Vector3 lastPos;	// where the flight was last seen (what it leaves is spawned as it ends, and first seen a tic later)
	int goneTic;		// the tic the flight ended with nothing found yet
	bool hit, crit, critDone;
	int id, landTic, flipTic;	// flipTic 0: not blinking yet
	bool red, wall;		// wall: it lies as BrutalAxeOnWall (which drops a BrutalAxe when shot)
	int origStyle;
	double origAlpha;
	bool origBright;
	Color origShade;
}

class RSVR_AxePool : EventHandler
{
	const MAXAXES = 10;
	const LIFE = 175;	// 5 s on the ground
	const BLINK = 70;	// red from 2 s
	Array<RSVR_ThrownAxe> axes;
	int nextId;

	static RSVR_AxePool Get() { return RSVR_AxePool(EventHandler.Find('RSVR_AxePool')); }
	static bool Logs(PlayerPawn mo) { return RSQ.PlayerInt(mo, 'rsq_switch_log', 0) > 0; }
	static bool IsAxeItem(Actor a)
	{
		if (!a || (Inventory(a) && Inventory(a).Owner))
			return false;
		Name n = a.GetClassName();
		return n == 'BrutalAxe' || n == 'BrutalAxeOnWall';
	}

	// MK Crits (mk-crits, csh_*) is loaded and its criticals are on
	static bool CritsLoaded()
	{
		Name cn = 'csh_critController';
		class<Inventory> c = cn;
		if (!c)
			return false;
		let cv = CVar.FindCVar('csh_critical_enabled');
		return !cv || cv.GetBool();
	}

	static void Thrown(PlayerPawn mo, Actor proj)
	{
		let h = Get();
		if (!h || !mo || !proj)
			return;
		let t = new('RSVR_ThrownAxe');
		t.who = mo;
		t.proj = proj;
		t.landTic = -1;
		t.id = ++h.nextId;
		if (mo.CountInv('RSVR_AxeCritNext') > 0)
		{
			// THE GUARANTEED CRITICAL (after a hit and a catch): where this throw lands in a monster, MK Crits' critical
			// (Crit, below). Spent on this throw, hit or miss.
			mo.TakeInventory('RSVR_AxeCritNext', 999);
			t.crit = true;
			if (Logs(mo))
				Console.Printf("RSQ axes t%d: throw #%d carries the guaranteed critical", mo.Level.maptime, t.id);
		}
		h.axes.Push(t);
	}

	static void Spent(PlayerPawn mo, int hand, bool next)
	{
		if (Logs(mo))
			Console.Printf("RSQ axes t%d: hand %d threw an axe: %d left, %s", mo.Level.maptime, hand, mo.CountInv('RSVR_Axes'),
				next ? "the next one comes to this hand" : (mo.CountInv('RSVR_Axes') > 0 ? "the one left is in the other hand: this hand is empty" : "this hand is empty"));
	}

	// ---- 2.0.4s: AXES IN HANDS NEVER MORE THAN THE COUNT --------------------------------------------------------------
	static bool IsAxeW(Weapon w)
	{
		if (!w)
			return false;
		Name n = w.GetClassName();
		return n == 'BrutalAxe' || n == 'RSQ_Off_BrutalAxe';
	}

	// the hand holds an axe now (either version), or one is on its way to it (PendingWeapon, flagged for that hand)
	static bool HandHasAxe(PlayerPawn mo, bool off)
	{
		let p = mo.player;
		if (!p)
			return false;
		if (IsAxeW(off ? p.OffhandWeapon : p.ReadyWeapon))
			return true;
		let pend = p.PendingWeapon;
		return pend && pend != WP_NOCHANGE && IsAxeW(pend) && pend.bOffhandWeapon == off;
	}

	// the hand is empty AT ONCE: its empty hand (BD22's Melee_Attacks in the main hand, RSQ_Hands in the off hand) put
	// straight into its slot, no lowering (as RSQ_Dual.Become swaps a gun's versions in place); an axe on its way to that
	// hand is called off. False when there is no empty hand to give it.
	static bool ToEmpty(PlayerPawn mo, bool off, String why)
	{
		let p = mo.player;
		if (!p)
			return false;
		let pend = p.PendingWeapon;
		if (pend && pend != WP_NOCHANGE && IsAxeW(pend) && pend.bOffhandWeapon == off)
			p.PendingWeapon = WP_NOCHANGE;
		let w = off ? p.OffhandWeapon : p.ReadyWeapon;
		if (!IsAxeW(w))
			return true;
		let e = RSQ_Dual.EmptyHandOf(mo, off);
		if (!e)
			return false;
		e.bOffhandWeapon = off;
		if (off)
		{
			p.OffhandWeapon = e;
			if (p.ReadyWeapon == e)
				p.ReadyWeapon = null;
			mo.TakeInventory('RSVR_OffAxeHolding', 999);
			mo.TakeInventory('RSVR_OffAxeThrown', 999);
			mo.TakeInventory('RSVR_OffAxeNext', 999);
		}
		else
		{
			p.ReadyWeapon = e;
			if (p.OffhandWeapon == e)
				p.OffhandWeapon = null;
			p.SetPsprite(PSP_FLASH, null);
			mo.TakeInventory('RSVR_AxeHolding', 999);
			mo.TakeInventory('RSVR_AxeThrown', 999);
			mo.TakeInventory('RSVR_AxeTrig', 999);
			mo.TakeInventory('RSVR_MainAxeNext', 999);
			Name hc = 'HasCutingWeapon';	// BD22's mark of a blade in hand (the axe's Deselect takes it)
			class<Inventory> hcc = hc;
			if (hcc)
				mo.TakeInventory(hcc, 999);
		}
		p.SetPsprite(off ? PSP_OFFHANDWEAPON : PSP_WEAPON, e.GetUpState(), false, e);
		if (p.PendingWeapon == e)
			p.PendingWeapon = WP_NOCHANGE;
		if (Logs(mo))
			Console.Printf("RSQ axes t%d: the %s hand's axe is gone at once (%s): %d axes, it holds %s now", mo.Level.maptime,
				off ? "off" : "main", why, mo.CountInv('RSVR_Axes'), e.GetClassName());
		return true;
	}

	RSVR_ThrownAxe FindItem(Actor a)
	{
		for (int i = 0; i < axes.Size(); i++)
			if (axes[i] && axes[i].item == a)
				return axes[i];
		return null;
	}

	override void WorldThingSpawned(WorldEvent e)
	{
		let a = e.Thing;
		if (!IsAxeItem(a))
			return;
		// the axe a thrown axe leaves: spawned where it ends (ThrowedAxe's Death / XDeath, the wall axe), or a wall axe
		// that falls (BrutalAxeOnWall's SpawnAxe) -- the same throw, the same clock
		for (int i = 0; i < axes.Size(); i++)
		{
			let t = axes[i];
			if (!t)
				continue;
			Actor from = t.proj ? t.proj : t.item;
			if (from == a)
				continue;
			// (a thing is "spawned" for these events on its first tic: the flight that left it is usually gone by then)
			Vector3 at = from ? from.pos : t.lastPos;
			if (!from && t.landTic >= 0 && !t.wall)
				continue;
			if ((at - a.pos).Length() > (from ? 64 : 96))	// (lastPos is up to one tic of flight behind)
				continue;
			if (t.item && t.item != a && t.item.GetClassName() != 'BrutalAxeOnWall')
				continue;
			t.item = a;
			t.proj = null;
			t.goneTic = 0;
			t.wall = a.GetClassName() == 'BrutalAxeOnWall';
			t.red = false;
			t.origStyle = a.GetRenderStyle();
			t.origAlpha = a.Alpha;
			t.origBright = a.bBRIGHT;
			t.origShade = a.fillcolor;
			if (t.landTic < 0)
				t.landTic = level.maptime;
			if (t.who && Logs(t.who))
				Console.Printf("RSQ axes t%d: throw #%d lies as %s (it %s)", level.maptime, t.id, a.GetClassName(), t.hit ? "HIT something" : "hit nothing");
			return;
		}
	}

	override void WorldThingDamaged(WorldEvent e)
	{
		if (!e.Inflictor || !e.Thing)
			return;
		for (int i = 0; i < axes.Size(); i++)
		{
			let t = axes[i];
			if (!t || t.proj != e.Inflictor || e.Thing == t.who)
				continue;
			if (!t.hit && t.who && Logs(t.who))
				Console.Printf("RSQ axes t%d: throw #%d HIT %s (%d damage)", level.maptime, t.id, e.Thing.GetClassName(), e.Damage);
			t.hit = true;
			if (t.crit && !t.critDone && e.Thing.bIsMonster)
			{
				t.critDone = true;
				Crit(t, e.Thing, e.Inflictor, e.Damage);
			}
			return;
		}
	}

	// MK Crits' critical, as MK Crits itself deals and shows it (csh_classes/core.txt csh_Brain / csh_critController): the
	// blow times csh_critical_factor (the rest dealt now as MK Crits' own 'critical' damage, which its code never counts
	// again), its sound on the thrower, its hit effect where the blow landed, and its 50-tic stun on a monster that
	// lives. MK Crits has no way for another mod to ask for a critical (no token, flag, service or damage type: its
	// critical is only a hit in the first 10 tics of a monster's attack), so its classes and sounds are named here, never
	// compiled against (it is optional), and its own settings (csh_critical_*) are read.
	static void Crit(RSVR_ThrownAxe t, Actor m, Actor inf, int dmg)
	{
		static const String sounds[] = { "", "criticalshots/mmz/clash", "criticalshots/cod/hitmark", "criticalshots/dks/dink",
			"criticalshots/dks/kill1", "criticalshots/dks/kill2", "criticalshots/dks/meat", "criticalshots/tf2/crit",
			"criticalshots/tf2/rec", "criticalshots/tf2/mini", "criticalshots/csz/headshot", "criticalshots/csg/helmet",
			"criticalshots/csg/headshot", "criticalshots/re1/slash", "criticalshots/re1/pop", "criticalshots/nmc/cutbody",
			"criticalshots/htd/splat" };
		static const Name fxs[] = { 'None', 'csh_visual_SmallBloodSplatter', 'csh_visual_LargeBloodSplatter',
			'csh_visual_SharpBlueFlash', 'csh_visual_RoundRedFlash', 'csh_visual_RoundBlueRedFlash', 'csh_visual_BloodSplat',
			'csh_visual_TF2Crit' };
		int si = 1, ei = 3;
		double vol = 1.0;
		let c1 = CVar.FindCVar('csh_critical_sound');
		if (c1) si = c1.GetInt();
		let c2 = CVar.FindCVar('csh_critical_effect');
		if (c2) ei = c2.GetInt();
		let c3 = CVar.FindCVar('csh_critical_vol');
		if (c3) vol = c3.GetFloat();
		String fxName = "none";
		if (ei > 0 && ei < fxs.Size())
		{
			class<Actor> fc = fxs[ei];
			let fx = fc ? Actor.Spawn(fc, inf.pos, NO_REPLACE) : null;
			if (fx && (ei <= 2 || ei == 6))
				fx.Translation = m.BloodTranslation;
			if (fx)
				fxName = fx.GetClassName();
		}
		double f = 2.0;
		let fc = CVar.FindCVar('csh_critical_factor');
		if (fc)
			f = max(1.0, fc.GetFloat());
		int extra = int(dmg * (f - 1.0));
		if (m.health > 0 && extra > 0)
			m.DamageMobj(inf, t.who, extra, 'critical', DMG_THRUSTLESS);
		String snd = (si > 0 && si < sounds.Size()) ? sounds[si] : "";
		if (t.who && snd != "")
			t.who.A_StartSound(snd, 99, 0, vol);
		bool stun = m.health > 0;
		if (stun)
		{
			RSVR_AxeStun.Start(m);
			Name jn = 'csh_JustStunned';	// MK Crits' own mark of a fresh critical (its stun damage is not doubled on it)
			class<Inventory> jc = jn;
			if (jc)
				m.GiveInventory(jc, 1);
		}
		if (t.who && Logs(t.who))
			Console.Printf("RSQ axes t%d: CRITICAL -- throw #%d into %s: %d + %d (x%.1f, MK Crits' factor), health now %d; MK Crits' sound %s, effect %s, %s", level.maptime, t.id,
				m.GetClassName(), dmg, extra, f, m.health, snd == "" ? "(none)" : snd, fxName, stun ? "stunned 50 tics" : "killed");
	}

	override void WorldTick()
	{
		bool calm = false;
		let pc = CVar.FindCVar('rsqa_photosafe');	// RSQ Accessibility's Photosensitive Mode: steady red, no blinking
		if (pc)
			calm = pc.GetInt() != 0;
		for (int i = axes.Size() - 1; i >= 0; i--)
		{
			let t = axes[i];
			if (!t || !t.who)
			{
				axes.Delete(i);
				continue;
			}
			if (t.proj)
			{
				t.lastPos = t.proj.pos;		// still flying
				continue;
			}
			if (!t.item && t.landTic < 0)
			{
				// the flight just ended: what it leaves is seen in the next tics (WorldThingSpawned)
				if (t.goneTic == 0)
					t.goneTic = level.maptime;
				if (level.maptime - t.goneTic < 4)
					continue;
			}
			if (t.item)
				t.lastPos = t.item.pos;
			if (!t.item && t.wall && t.landTic >= 0)
			{
				// the wall axe was shot down: the axe it drops is seen in the next tics
				if (t.goneTic == 0)
					t.goneTic = level.maptime;
				if (level.maptime - t.goneTic < 4)
					continue;
			}
			if (!t.item || (Inventory(t.item) && Inventory(t.item).Owner))
			{
				// picked up (walked over, grabbed), or it left nothing behind
				if (t.landTic >= 0 && Logs(t.who))
					Console.Printf("RSQ axes t%d: throw #%d %s", level.maptime, t.id, t.item ? "picked up" : "gone");
				axes.Delete(i);
				continue;
			}
			int age = level.maptime - t.landTic;
			if (age >= LIFE)
			{
				if (Logs(t.who))
					Console.Printf("RSQ axes t%d: throw #%d faded after %d tics on the ground", level.maptime, t.id, age);
				t.item.Destroy();
				axes.Delete(i);
				continue;
			}
			if (age < BLINK)
				continue;
			if (calm)
			{
				// Photosensitive Mode: red, steady, until it is gone
				if (!t.red)
				{
					t.red = true;
					Look(t);
					if (Logs(t.who))
						Console.Printf("RSQ axes t%d: throw #%d on the ground %d tics: RED, steady (Photosensitive Mode)", level.maptime, t.id, age);
				}
				continue;
			}
			// faster and faster: a flip every 10 tics at 2 s, every 2 tics at the end
			if (t.flipTic > 0 && level.maptime < t.flipTic)
				continue;
			int period = max(2, int(10.0 - 8.0 * double(age - BLINK) / double(LIFE - BLINK) + 0.5));
			t.red = t.flipTic == 0 ? true : !t.red;
			t.flipTic = level.maptime + period;
			Look(t);
			if (Logs(t.who))
				Console.Printf("RSQ axes t%d: throw #%d on the ground %d tics: %s (period %d)", level.maptime, t.id, age, t.red ? "RED" : "plain", period);
		}
	}

	static void Look(RSVR_ThrownAxe t)
	{
		let a = t.item;
		if (!a)
			return;
		if (t.red)
		{
			a.A_SetRenderStyle(1.0, STYLE_Stencil);
			a.SetShade(Color(255, 255, 32, 32));
			a.bBRIGHT = true;
		}
		else
		{
			a.A_SetRenderStyle(t.origAlpha, t.origStyle);
			a.SetShade(t.origShade);
			a.bBRIGHT = t.origBright;
		}
	}

	// ---- DISTANCE GRAB (pickup.first) -----------------------------------------------------------------------------------
	// 1 taken (given to the hand that grabbed it), -1 AMMO FULL (10 axes), 0 not an axe
	int Claim(PlayerPawn mo, int h, Actor a)
	{
		if (!IsAxeItem(a))
			return 0;
		let pool = mo.FindInventory('RSVR_Axes');
		int have = pool ? pool.Amount : 0;
		let t = FindItem(a);
		bool own = t && t.who == mo;
		if (have >= MAXAXES)
		{
			if (Logs(mo))
				Console.Printf("RSQ axes t%d: hand %d grabbed %s: 10 axes already -- AMMO FULL", mo.Level.maptime, h, own ? String.Format("its thrown axe #%d", t.id) : "an axe");
			return -1;
		}
		int add = own && t.hit ? 2 : 1;
		bool crit = own && t.hit && CritsLoaded();
		bool hit = own && t.hit;
		int tid = t ? t.id : 0;
		if (t)
			axes.Delete(axes.Find(t));	// before Give (no "picked up" line: this one is said here)
		Give(mo, h, add);
		if (crit)
			mo.SetInventory('RSVR_AxeCritNext', 1);
		mo.A_StartSound("Axe/Draw", CHAN_ITEM);
		if (Logs(mo))
			Console.Printf("RSQ axes t%d: hand %d grabbed %s -> +%d, %d axes%s", mo.Level.maptime, h,
				own ? String.Format("its own thrown axe #%d (%s)", tid, hit ? "it hit" : "it missed") : "an axe it did not throw",
				add, mo.CountInv('RSVR_Axes'), crit ? "; the next throw is a guaranteed critical (MK Crits)" : (hit ? " (no MK Crits: no critical)" : ""));
		a.Destroy();
		return 1;
	}

	// add axes (never above 10) and put one in the hand that grabbed, ALWAYS (2.0.4s, owner 2026-11-12 21:36: "lets have
	// axe always switch to when distance grabbed ... the axe should auto switch on distance grab"): the off hand as since
	// 2.0.3y, and now the main hand too whatever it holds -- a gun there goes back to the Wheel / its holster as any switch
	// does. Not the player's neverswitchonpickup: that is for walking over things (the engine's own pickup, untouched).
	// (2.0.4r: a main hand holding a gun kept it and the axe went to the Wheel.)
	static void Give(PlayerPawn mo, int h, int add)
	{
		let p = mo.player;
		mo.GiveInventory('RSVR_Axes', add);
		let mainW = RSQ_Dual.GiveBare(mo, 'BrutalAxe');
		let offW = RSQ_Dual.GiveBare(mo, 'RSQ_Off_BrutalAxe');
		mo.TakeInventory('RSVR_MainAxeGone', 999);
		mo.TakeInventory('RSVR_OffAxeGone', 999);
		let w = h == 1 ? offW : mainW;
		let held = h == 1 ? p.OffhandWeapon : p.ReadyWeapon;
		if (!w || IsAxeW(held))
			return;		// that hand holds an axe already: the count went up, nothing to switch
		w.bOffhandWeapon = h == 1;
		p.PendingWeapon = w;
		if (Logs(mo))
			Console.Printf("RSQ axes t%d: Distance Grab -- hand %d switches from %s to the axe (always, whatever neverswitchonpickup says)",
				mo.Level.maptime, h, held ? String.Format("%s", held.GetClassName()) : "nothing");
	}
}

// MK Crits' stun (csh_critController.initStun / endStun), for the guaranteed critical: the monster held in its pain
// state 50 tics, then let go with its own NOPAIN back
class RSVR_AxeStun : Thinker
{
	Actor m;
	int left;
	bool noPain;

	static void Start(Actor m)
	{
		let s = new('RSVR_AxeStun');
		s.m = m;
		s.left = 50;
		s.noPain = m.bNOPAIN;
		m.bNOPAIN = true;
		let ps = m.FindState("Pain");
		if (ps)
			m.SetState(ps);
		m.tics = -1;
	}

	override void Tick()
	{
		if (!m || m.health <= 0)
		{
			if (m)
				m.bNOPAIN = noPain;
			Destroy();
			return;
		}
		if (level.isFrozen())
			return;
		if (--left > 0)
		{
			m.tics = -1;
			return;
		}
		m.tics = 1;
		m.bNOPAIN = noPain;
		Destroy();
	}
}

// Distance Grab's door (DistanceGrab/zscript/rsqdg/feel.zs RSQDG_Events): "pickup.first" before the pickup, and the old
// "pickup.claim" after a refusal (answered the same way, never refused there)
class RSVR_AxeGrabEventService : Service play
{
	override int GetInt(String request, String stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		if (!(request ~== "grab.event"))
			return 0;
		if (stringArg != "pickup.first" && stringArg != "pickup.claim")
			return 0;
		let mo = players[consoleplayer].mo;
		let h = RSVR_AxePool.Get();
		if (!mo || mo.health <= 0 || !h)
			return 0;
		int r = h.Claim(mo, intArg & 1, Actor(objectArg));
		return stringArg == "pickup.claim" ? max(r, 0) : r;
	}
}
