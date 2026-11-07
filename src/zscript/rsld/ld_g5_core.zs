// ld_g5_core.zs -- G5 (R3b, round 3, 2026-11-06): LegenDoom 3.0's fire cadence effects on BD22 VR's own guns, the
// shared part. The effects themselves: ld_g5_fx.zs. Numbers: numbers_g5.zs (ldl_patch/tools/numbers/g5.rules).
//
// Owner's Q6 (2026-11-06): "the trigger cycle gets faster; the gun's own shot counter decides, and the hand action stays
// where it is in the cycle. A burst pump shotgun isn't unreasonable, and a break-action burst super shotgun should
// still work": a burst fires its shots from what's loaded, then the pump / break waits for the hand as now.
//
// THE CADENCE (Cadence below). A gun's trigger cycle is the run of its own weapon states from a shot (the hand's pull,
// handler.zs) until the gun is back in Ready (or in any state of the stop list). Inside it, and only there, a speed
// factor is applied to that hand's weapon layer (PSP_WEAPON main, PSP_OFFHANDWEAPON off):
//   faster (x > 1): every tic x - 1 extra tics are taken off the layer: a frame of 2+ tics loses one, a 1-tic frame is
//     advanced to its next state at once (that state's own action runs, as the engine runs it: PSprite.SetState), at
//     most MAXSTEP extra a tic. Never into a stop state, never while a hand action has the gun.
//   slower (x < 1): a frame is stretched to its tics / x when it starts (the remainder carried to the next frame).
// Nothing is skipped: every state of the gun still runs, in order, with its action (the engine's own
// PowerDoubleFiringSpeed does the same thing, psprite.Tick, at x2 and with no limits on what it shortens).
// The hand actions are never touched: the pump the hand works (RSP: rsr_pump.zs, waits in RSP_P*Wait), the hand's shell
// loading (RSP LOAD), the break-action reload (RSB: rsr_break.zs), the magazine reload (RSR: vreload.zs), BD22's own
// Reload / Unload / NoAmmo / Select / Deselect / Inspect / kick / grenade / sprint states (STOPLABELS below). BD22's own canned
// pump (the hand is off the pump: RSP hands the gun back to Pump1) is the gun's own cycle and is sped like any frame.
//
// THE TRIGGER HOLD (Block below): Chargeup (charging) and Overkill (cooldown, or fewer than 5 rockets loaded) keep a
// hand's trigger from firing. Tokens RSLD_G5BlockMain / RSLD_G5BlockOff, read by the first line of the guns' Fire (and
// Hold) states (src/actors/Weapons/*.dec, DECORATE.rsqdual: "LD mode (round 3)"), which go to the gun's RSLD_Jammed state
// (no shot, no sound, the hand works as in Ready). Never given without LegenDoom (the handler calls no effect then).
//
// Out of LD mode nothing here runs (the foundation calls no effect hook). Never a LegenDoom class name as a literal.

class RSLD_G5Hand play
{
	// the cadence
	State last;
	int lastTics;
	double acc;
	bool cycOn;
	int cycPull;
	// the gun's own cycle, measured: tics between two pulls of this hand while the trigger stayed down
	int prevPull, baseCyc;
	// edge of the trigger
	bool pressPrev;
	// tics the cadence took off this hand's cycle since the last pull (negative: added), for the proof line
	int saved;
	// effect scratch (one effect owns a hand's state: one effect per slot)
	int n1, n2, n3, tic1, tic2;
	bool f1, f2, f3;
	double v1;
	Weapon w;

	void Note(PSprite psp)
	{
		last = psp ? psp.CurState : null;
		lastTics = psp ? psp.Tics : 0;
	}

	void Reset()
	{
		last = null; lastTics = 0; acc = 0; cycOn = false;
	}
}

class RSLD_G5Effect : RSLD_Effect
{
	RSLD_G5Hand handSt[MAXPLAYERS * 2];

	RSLD_G5Hand HS(int pn, int hand)
	{
		int k = pn * 2 + hand;
		if (k < 0 || k >= MAXPLAYERS * 2) k = 0;
		if (!handSt[k]) handSt[k] = new("RSLD_G5Hand");
		return handSt[k];
	}
	RSLD_G5Hand HSs(RSLD_Shot s) { return HS(s.pn, s.hand); }
	RSLD_G5Hand HSc(RSLD_Held c) { return HS(c.pn, c.hand); }

	// the cycle of our gun measured from two pulls in a row with the trigger held (0 = not yet known)
	void Measure(RSLD_Shot s)
	{
		let h = HSs(s);
		if (h.prevPull > 0 && s.tic - h.prevPull > 0 && s.tic - h.prevPull <= 70)
			h.baseCyc = s.tic - h.prevPull;
		h.prevPull = s.tic;
	}
}

class RSLD_G5 play
{
	const MAXSTEP = 4;		// extra weapon states a tic (x5 at most on a gun of 1-tic frames)
	const CYCLE_MAX = 105;	// a cycle longer than 3 s is not a trigger cycle

	static PSprite Psp(PlayerPawn mo, int hand)
	{
		if (!mo || !mo.player) return null;
		return mo.player.FindPSprite(hand == RSLD.OFF ? PSP_OFFHANDWEAPON : PSP_WEAPON);
	}

	// a hand action has the gun: the hand pumps or loads (RSP), the break action is open (RSB), the magazine is out (RSR)
	static bool HandBusy(PlayerPawn mo)
	{
		if (!mo || !mo.player) return false;
		int pn = mo.PlayerNumber();
		if (RSP_Handler.Busy(pn) || RSB_Handler.Busy(pn)) return true;
		let r = RSR_ReloadHandler.StateOf(mo);
		return r && r.phase != RSR.IDLE;
	}

	// the hand is LOADING shells (not a pump wait): a burst never fires into a reload
	static bool Loading(PlayerPawn mo)
	{
		if (!mo || !mo.player) return false;
		let p = RSP_Handler.Peek(mo);
		if (p && p.mode == RSP.LOAD) return true;
		if (RSB_Handler.Busy(mo.PlayerNumber())) return true;
		let r = RSR_ReloadHandler.StateOf(mo);
		return r && r.phase != RSR.IDLE;
	}

	// BD22 / BD22 VR states that are never part of the trigger cycle (each label's own sequence, where the gun has it)
	static bool InStop(Weapon w, State st)
	{
		if (!w || !st) return true;
		static const string STOPLABELS[] =
		{
			"Ready", "Ready2", "Ready3", "ReadyToFire", "ReadyToFireAgain", "Steady",
			"Select", "SelectAnimation", "SelectAnimationEmpty", "FirstSelectAnimation", "SelectDual", "SelectDualEmpty",
			"Deselect", "DeselectEmpty", "DeselectContinue", "DeselectInstant",
			"Reload", "Reload2", "ReloadNormally", "Unload", "NoAmmo", "Inspect", "ContinueInspect", "DoKick", "TossGrenade",
			"Sprinting", "StartSprint", "StopSprint", "RSLD_Jammed",
			"RSP_Load", "RSP_Load2", "RSP_VRIns", "RSP_LoadWait", "RSP_P1Wait", "RSP_P2Wait", "RSP_P3Wait", "RSP_Feed"
		};
		for (int i = 0; i < STOPLABELS.Size(); i++)
		{
			State b = w.FindStateByString(STOPLABELS[i], true);
			if (b && Actor.InStateSequence(st, b)) return true;
		}
		return false;
	}

	static bool InReady(Weapon w, State st)
	{
		if (!w || !st) return false;
		static const string R[] = { "Ready", "Ready2", "Ready3", "ReadyToFire", "ReadyToFireAgain", "Steady" };
		for (int i = 0; i < R.Size(); i++)
		{
			State b = w.FindStateByString(R[i], true);
			if (b && Actor.InStateSequence(st, b)) return true;
		}
		return false;
	}

	// the hand's primary trigger is down (main: BT_ATTACK only, not alt fire; off: BT_OFFHANDATTACK)
	static bool Pressed(PlayerPawn mo, int hand)
	{
		if (!mo || !mo.player) return false;
		return (mo.player.cmd.buttons & (hand == RSLD.OFF ? BT_OFFHANDATTACK : BT_ATTACK)) != 0;
	}

	// what the gun's next shot comes out of: the magazine (Ammo2), or the reserve for a gun without one / BD22's
	// "no reload" play (Purist, NoReloading). -1: no ammo item (it never runs dry)
	static int Loaded(Weapon w, PlayerPawn mo)
	{
		if (!w) return 0;
		bool noMag = !w.Ammo2 || w.Ammo2 == w.Ammo1 || RSLD.Has(mo, "IsPlayingAsPurist") > 0 || RSLD.Has(mo, "NoReloading") > 0;
		Inventory a = noMag ? w.Ammo1 : w.Ammo2;
		if (!a) return -1;
		return a.Amount;
	}

	static bool CanShoot(Weapon w, PlayerPawn mo)
	{
		int n = Loaded(w, mo);
		return n < 0 || n > 0;
	}

	// LegenDoom's normal pistol cycle (prefire + NormalFireEnd, less the A_Refire frame): 14 tics
	static double BaseCycle()
	{
		return RSLD.Num("Base", "pi_pre") + RSLD.Num("Base", "pi_end") - RSLD.Num("Base", "pi_rf");
	}

	// ---- the cadence: see the head of this file
	static void Cadence(RSLD_G5Hand h, RSLD_Held c, double speed)
	{
		let psp = Psp(c.mo, c.hand);
		if (!psp || !psp.CurState || psp.Caller != c.weapon) { h.Reset(); return; }
		let hh = RSLD.H();
		int lp = hh ? hh.LastPull(c.pn, c.hand) : -1000;
		if (lp != h.cycPull && level.maptime - lp <= 1 && lp > 0) { h.cycOn = true; h.cycPull = lp; h.acc = 0; }
		if (h.cycOn && (level.maptime - h.cycPull > CYCLE_MAX || HandBusy(c.mo) || InStop(c.weapon, psp.CurState)))
			h.cycOn = false;
		if (!h.cycOn || speed <= 0 || abs(speed - 1.0) < 0.001)
		{
			h.acc = 0;
			h.Note(psp);
			return;
		}
		if (speed > 1)
		{
			h.acc = min(h.acc + speed - 1.0, double(MAXSTEP));
			int steps = 0, guard = 0;
			while (h.acc >= 1.0 && steps < MAXSTEP && guard++ < 64)
			{
				if (psp.Tics > 1) { psp.Tics--; h.acc -= 1.0; h.saved++; continue; }
				if (psp.Tics != 1) break;
				State nx = psp.CurState.NextState;
				if (!nx || InStop(c.weapon, nx) || HandBusy(c.mo)) break;
				psp.SetState(nx);
				h.acc -= 1.0;
				h.saved++;
				steps++;
				psp = Psp(c.mo, c.hand);
				if (!psp || !psp.CurState || psp.Caller != c.weapon || InStop(c.weapon, psp.CurState)) { h.cycOn = false; break; }
			}
		}
		else
		{
			bool fresh = (psp.CurState != h.last || psp.Tics >= h.lastTics) && psp.Tics >= 1 && psp.Tics <= psp.CurState.Tics;
			if (fresh)
			{
				double want = psp.Tics / speed + h.acc;
				int nt = max(1, int(want));
				h.acc = want - nt;
				h.saved -= nt - psp.Tics;
				psp.Tics = nt;
			}
		}
		if (psp) h.Note(psp);
	}

	// ---- the trigger hold: the hand's Fire / Hold states go to RSLD_Jammed while the token is on. Asked for every tic
	// (WhileHeld): a hold nobody renews runs out by itself one tic later (RSLD_G5Token), so a gun put away, a dropped
	// legendary or a level change never leaves a trigger held.
	static void Block(PlayerPawn mo, int hand, bool on)
	{
		if (!mo) return;
		class<Inventory> tok = "RSLD_G5BlockMain";
		if (hand == RSLD.OFF) tok = "RSLD_G5BlockOff";
		let it = RSLD_G5Token(mo.FindInventory(tok));
		if (on)
		{
			if (!it) { mo.GiveInventory(tok, 1); it = RSLD_G5Token(mo.FindInventory(tok)); }
			if (it) { it.Amount = 1; it.refreshed = level.maptime; }
		}
		else if (it) it.Amount = 0;
	}

	// shot events of this hand in this tic so far: the pull's pellets (synchronous with the gun's A_FireBullets) and
	// the player's fresh projectiles near him (WorldThingSpawned comes a tic later), BD22's helpers left out
	static int ShotCount(PlayerPawn mo, int hand)
	{
		int n = 0;
		let hh = RSLD.H();
		if (hh)
		{
			let s = hh.cur[mo.PlayerNumber() * 2 + hand];
			if (s && s.lastTic == level.maptime) n += s.pellets;
		}
		let it = BlockThingsIterator.Create(mo, 160);
		while (it.Next())
		{
			let a = it.thing;
			if (a && a.bMISSILE && a.target == mo && a.GetAge() == 0 && !RSLD_Handler.Helper(a) && !RSLD_Handler.IsStrike(a)) n++;
		}
		return n;
	}

	// ---- start one more shot of the gun from its own Fire state (its own checks decide: ammo, jam, pump...):
	// true if the gun went into Fire
	static bool Shoot(PlayerPawn mo, int hand, Weapon w)
	{
		let psp = Psp(mo, hand);
		if (!psp || !w || psp.Caller != w) return false;
		State f = w.FindState("Fire", true);
		if (!f) return false;
		psp.SetState(f);
		return true;
	}

	// ...and run its states on in this same tic until the shot is out (no lead-in: LegenDoom's burst and Quickdraw shots
	// come without a second charge-up). Every state's own action runs, in order. True: a shot went out.
	static bool ShootNow(PlayerPawn mo, int hand, Weapon w, int maxSteps = 64)
	{
		int before = ShotCount(mo, hand);
		if (!Shoot(mo, hand, w)) return false;
		return StepToShot(mo, hand, w, before, maxSteps);
	}

	static bool StepToShot(PlayerPawn mo, int hand, Weapon w, int before, int maxSteps)
	{
		for (int k = 0; k < maxSteps; k++)
		{
			if (ShotCount(mo, hand) > before) return true;
			let psp = Psp(mo, hand);
			if (!psp || !psp.CurState || psp.Caller != w || InStop(w, psp.CurState) || psp.Tics < 0) return false;
			State nx = psp.CurState.NextState;
			if (!nx) return false;
			psp.SetState(nx);
		}
		return ShotCount(mo, hand) > before;
	}

	// the slot's BD22 fire sound (a replayed shot, Recursive): the gun's own A_PlaySound(..., 1) in its fire state
	static string FireSound(Weapon w, int slot)
	{
		if (w)
		{
			string cn = w.GetClassName();
			if (cn.IndexOf("Rifle") >= 0 && cn.IndexOf("Plasma") < 0) return "Rifle/Fire";
			if (cn.IndexOf("Revolver") >= 0) return "Revolver/Fire";
		}
		static const string S[] = { "", "", "Pistol/Fire", "Shotgun/Fire", "SSG/Fire", "Chaingun/Fire", "Rocket/Fire", "Plasma/Fire", "BFG/Fire" };
		return slot >= 0 && slot < S.Size() ? S[slot] : "";
	}
}

// the trigger hold tokens (see Block); never given without LegenDoom. Amount 1 = held; a hold not renewed for a tic
// drops to 0 by itself (the guns' hook reads CountInv > 0)
class RSLD_G5Token : Inventory
{
	int refreshed;
	Default { +INVENTORY.UNDROPPABLE +INVENTORY.UNTOSSABLE +INVENTORY.UNCLEARABLE +INVENTORY.QUIET +INVENTORY.KEEPDEPLETED Inventory.MaxAmount 1; }
	override void DoEffect()
	{
		Super.DoEffect();
		if (Amount > 0 && level.maptime - refreshed > 1) Amount = 0;
	}
}
class RSLD_G5BlockMain : RSLD_G5Token {}
class RSLD_G5BlockOff : RSLD_G5Token {}

// ---- for R3a's G3 effects (Accelerator, Overkill): their fire-state part, called from R3a's RSLD_Fx_Overkill
// (this file defines no RSLD_Fx_Overkill / RSLD_Fx_Accelerator: one class per effect).
// Overkill (LegenDoom RocketLauncher.dec FireOverkillAmmoCheck / FireOverkill / ReadyOverkill, EpicSpecialEffects.dec
// LDOverkillCooldown): a shot needs Overkill|ammo (5) rockets LOADED (owner Q7: the magazine) and takes all of them;
// then LegenDoom's own LDOverkillCooldown (92 tics) holds the trigger (ReadyOverkill: A_WeaponReady(WRF_NOFIRE)).
// Accelerator: LegenDoom's FireAccelerator prefire (Accelerator|rl_pre, 8 tics) is its NormalFire's (2 + 4 + 2 = 8):
// no cadence change; the instant hit is the missile rider's (G3).
class RSLD_G5Fire play
{
	// every tic the Overkill launcher is in a hand (WhileHeld): the trigger is held while LegenDoom's cooldown runs or
	// fewer than 5 rockets are loaded. True = held.
	static bool OverkillHeld(RSLD_Held c)
	{
		if (!c || !c.mo) return false;
		int need = int(RSLD.Num("Overkill", "ammo"));
		int n = RSLD_G5.Loaded(c.weapon, c.mo);
		bool cool = RSLD.Has(c.mo, "LDOverkillCooldown") > 0;
		bool hold = cool || (n >= 0 && n < need);
		RSLD_G5.Block(c.mo, c.hand, hold);
		return hold;
	}

	// the hand let go of the launcher (or the effect left it): call to release the hold
	static void OverkillRelease(PlayerPawn mo, int hand) { RSLD_G5.Block(mo, hand, false); }

	// AfterPull of an Overkill shot: the rest of the 5 rockets out of the magazine (the gun took its own 1) and
	// LegenDoom's own cooldown powerup
	static void OverkillPull(RSLD_Shot s)
	{
		if (!s || !s.mo) return;
		int need = int(RSLD.Num("Overkill", "ammo"));
		int took = s.magTaken > 0 ? s.magTaken : s.ammoTaken;
		if (need - took > 0) s.Take(need - took);
		RSLD.Give(s.mo, "LDOverkillCooldown");
		s.Log(String.Format("Overkill: %d rockets for the shot (LegenDoom FireOverkill), cooldown %d tics (LDOverkillCooldown)", need, int(RSLD.Num("Overkill", "cooldown"))));
	}
}
