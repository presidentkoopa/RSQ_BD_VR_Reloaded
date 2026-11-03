// RS VR grenade (2026-10-16). BD22's own hand grenade, worked by hand in VR:
//   1. the off hand takes the RING (off trigger, or grip) and pulls it away: the pin is out
//      (BD's own "Grenade/Pin"). Bring the hand back to the top and grab again: pin back in.
//   2. the main TRIGGER is your squeeze on the spoon. Let go of it while swinging: thrown,
//      at the speed and direction of the swing. Let go while still: the spoon flies off
//      (ping) and the fuse is lit in your hand -- cooking. Squeeze and let go again to throw.
//   3. cook too long (BD's fuse, 48 tics) and it goes off in the hand.
//   4. THE TEETH (2.0.3p, owner 2026-11-03: the pin pull standardised with RSQ Grenade, whose hand.zs Face() is
//      the standard and is copied here, numbers and all): squeeze the grenade's trigger and hold the grenade at
//      your face for a run of tics (rsg_face_hold, 12): the pin is out. Two radii, not one: once the pin is out
//      the hand has to have been clear of your face (rsg_face_far, 0.71 m) before it can take another; letting go
//      of the trigger re-arms it too. The squeeze at the face is only a squeeze: it neither cooks nor throws. As
//      in RSQ, the trigger is still your squeeze on the spoon once the pin is out, so letting go of it afterwards
//      is 2. above (a swing throws, still cooks). The off-hand ring (1.) is unchanged and works alongside.
// BD22's own HandGrenade projectile, its fuse token, its explosion and sounds.
// Out of VR, or rsg_vr 0, BD22's own canned throw is untouched.
class RSG_Handler : EventHandler
{
	RSG_State st[MAXPLAYERS];

	// 2026-10-23: rsr/vreload.zs InputProcess asks this before it decides what to do with the Use
	// key. A grenade in the hand wants the ring, so Use has to reach the grenade too. Reads the
	// field Step() set this tic, the way RSP_Handler.Busy and RSB_Handler.Busy do.
	clearscope static bool WantsGrab(int n)
	{
		let h = RSG_Handler(EventHandler.Find('RSG_Handler'));
		if (!h || n < 0 || n >= MAXPLAYERS)
			return false;
		let s = h.st[n];
		return s && s.wantGrab;
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
			st[n].Reset(players[n].mo);
		}
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n] || !players[n].mo)
				continue;
			let mo = players[n].mo;
			if (!st[n])
				st[n] = new('RSG_State');
			st[n].Tick(mo);
		}
	}
}

class RSG_State play
{
	const FUSE = 48;				// BD22: GrenadeTime 3, 16 tics a count
	const RING_GRAB = 12.0;			// cm round the ring the off hand can take it
	const PULL = 8.0;				// cm past that: the pin is out
	const HIST = 6;
	const RING_F = 3.45;		// the ring's centre: nade.md3 as drawn in the FBX hand (MODELDEF.rsq RQNP, fit_nade.py), gun hand cm (F, L, U)
	const RING_L = 5.12;
	const RING_U = 5.06;
	const NADE_F = 2.77;		// the grenade body's centre as drawn (moved 4.0 cm by the FBX hand fit): the throw and the in-hand blast start here
	const NADE_L = 4.23;
	const NADE_U = -1.97;

	RSR_State geo;
	bool wantGrab;		// 2026-10-23: a grenade is in hand and wants the off-hand grab (read from
						// ui by RSG_Handler.WantsGrab, as the other modules' Busy() are)
	bool armed;			// pin out
	bool ringHeld;
	bool ringKept;		// the pulled ring is still in the off hand (until its grab lets go)
	bool spoonOff;		// cooking
	int cookTic;
	bool trigPrev, grabPrev;
	int faceTic;		// 2.0.3p THE TEETH: tics the squeezed grenade has been at the face
	bool faceReady;		// ...and the teeth may take a pin (RSQ Grenade's far radius / trigger re-arm)
	bool teethPin;		// this pin came out by the teeth (no ring in the off hand)
	int gripPrevPresses;
	double hx[HIST], hy[HIST], hz[HIST];	// the hand in the BODY's frame: forward, left, up
	int head, count;

	static class<Actor> Cls(Name n) { class<Actor> c = n; return c; }

	static bool Wanted(PlayerPawn mo)
	{
		let w = mo.player.ReadyWeapon;
		if (!w || w.GetClassName() != 'HandGrenades' || !RSVR_VRHand.InVR(mo))
			return false;
		if (RSR.PlayerInt(mo.player, 'rsg_vr', 1) == 0)
			return false;
		class<Inventory> am = (class<Inventory>)(Cls('GrenadeAmmo'));
		return am && mo.CountInv(am) > 0;
	}

	void Reset(PlayerPawn mo)
	{
		armed = ringHeld = ringKept = spoonOff = teethPin = false;
		faceTic = 0;
		mo.SetInventory('RSG_PinOut', 0);
		mo.SetInventory('RSG_Spoon', 0);
	}

	void Buzz(PlayerPawn mo) { RSVR_Hand.Buzz(mo); }

	// the off hand shows the ring pinched in its fingers while it holds it (hands.zs RsgRing)
	void Tick(PlayerPawn mo)
	{
		// 1.12 (owner: "throwing all grenades makes both hands disappear forever"): BD22 keeps the
		// empty grenade out (its no-ammo jump never fires) and shows nothing. In VR, the last
		// grenade gone switches to the fists (an empty hand is a fist).
		let p = mo.player;
		let w = p ? p.ReadyWeapon : null;
		class<Inventory> am = (class<Inventory>)(Cls('GrenadeAmmo'));
		if (w && w.GetClassName() == 'HandGrenades' && am && mo.CountInv(am) <= 0 && !armed
			&& p.PendingWeapon == WP_NOCHANGE && RSVR_VRHand.InVR(mo))
			mo.A_SelectWeapon('Melee_Attacks');	// out of grenades: the hand becomes a fist
		Step(mo);
		mo.SetInventory('RSG_RingHand', RSG_VR_On(mo) && (ringHeld || ringKept) ? 1 : 0);
	}

	static bool RSG_VR_On(PlayerPawn mo) { return mo.CountInv('RSG_VR') > 0; }

	void Step(PlayerPawn mo)
	{
		bool want = Wanted(mo);
		wantGrab = want;
		mo.SetInventory('RSG_VR', want ? 1 : 0);
		if (!want)
		{
			if (armed && spoonOff)
				Boom(mo);			// switched or left VR with the fuse lit: it still goes off
			if (armed)
				Reset(mo);
			count = 0;
			faceTic = 0;
			faceReady = true;	// RSQ Grenade: a new hand on the grenade starts ready
			return;
		}
		if (!geo)
			geo = new('RSR_State');
		geo.Frames(mo);

		// The hand's path, for the throw. 2026-10-23: this kept the hand in WORLD space and took
		// the pawn's movement out a tic later -- the method rsq/fists.zs threw out in 1.5, because
		// a TURN swings the hand round the player and the controller's sample lands a tic apart
		// from the body's. Turning read as a throw and a real throw read weak. Measured in the
		// BODY'S OWN FRAME instead (forward, left, up), as the fists are: walking, strafing and
		// turning now move nothing.
		head = (head + 1) % HIST;
		Vector3 hp = RSVR_VRHand.HandPos(mo) - mo.pos;
		double bc = cos(mo.angle), bs = sin(mo.angle);
		hx[head] = hp.x * bc + hp.y * bs;
		hy[head] = -hp.x * bs + hp.y * bc;
		hz[head] = hp.z;
		count = min(count + 1, HIST);

		// the off hand's grab: whatever "Grab ammo with" is set to. 2026-10-23: this read
		// rsr_grab_buttons raw and never looked at netUse, so with the Use key chosen (1.17,
		// rsr_grab_with 2) the ring could not be taken at all -- the pin pull was simply dead.
		// RSR.GrabMask is the same rule the reload uses: the trigger only when it is the choice.
		// The grip is taken PLAIN here, without the reload's gripFree guard: that guard exists so a
		// grip press near a GUN does not fight the engine's two-hand steadying, and the ring sits
		// 7.6 cm from the gun hand -- well inside the 50 cm steadying range -- so the guard would
		// make the grip mode structurally unable to ever reach the ring. There is no gun to steady.
		// 2.0.2a (owner 2026-10-28 19:50): "pulling pin with grenade always has to be done with offhand
		// trigger". The ring is taken by the OFF-HAND TRIGGER only, whatever "Grab ammo with" is set to.
		bool grab = (mo.player.cmd.buttons & BT_OFFHANDATTACK) != 0;
		bool grabPress = grab && !grabPrev;
		grabPrev = grab;
		if (!grab)
			ringKept = false;
		bool trig = (mo.player.cmd.buttons & BT_ATTACK) != 0;
		bool trigUp = !trig && trigPrev;
		trigPrev = trig;

		double cap = RING_GRAB * RSR.Float('rsr_assist', 1.0);
		double d = (geo.offLocal - (RING_F, RING_L, RING_U)).Length();
		int now = mo.Level.maptime;

		if (!armed)
		{
			if (grabPress && d < cap)
			{
				ringHeld = true;
				Buzz(mo);
			}
			if (ringHeld && !grab)
				ringHeld = false;
			if (ringHeld && d > cap + PULL)
			{
				armed = true;
				ringHeld = false;
				ringKept = true;
				mo.SetInventory('RSG_PinOut', 1);
				mo.A_StartSound("Grenade/Pin", CHAN_WEAPON, CHANF_OVERLAP);
				Buzz(mo);
				return;
			}
			Face(mo, trig);
			return;
		}
		faceTic = 0;
		if (!trig)
			faceReady = true;

		if (!spoonOff)
		{
			if (grabPress && d < cap * 0.6)
			{
				Reset(mo);			// the pin back in
				mo.A_StartSound("Grenade/Pin", CHAN_WEAPON, CHANF_OVERLAP);
				Buzz(mo);
				return;
			}
			if (trigUp)
			{
				if (!Throw(mo, 0, true))
				{
					spoonOff = true;		// let go while still: the spoon flies, it is cooking
					cookTic = now;
					mo.SetInventory('RSG_Spoon', 1);
					mo.A_StartSound("weapons/shell", CHAN_AUTO, CHANF_OVERLAP);
					Buzz(mo);
				}
			}
			return;
		}

		int cooked = now - cookTic;
		// 2026-10-23: Level.maptime restarts at 0 on a level change, so a fuse lit before an
		// exit reads as a hugely negative cook, never reaches FUSE, and the live grenade sits
		// in the hand for good -- it can neither go off nor be re-pinned. Re-base the cook
		// rather than latch; the player keeps the grenade and loses only the burn.
		if (cooked < 0)
		{
			cookTic = now;
			cooked = 0;
		}
		if (cooked >= FUSE)
		{
			Boom(mo);
			return;
		}
		if (trigUp)
			Throw(mo, cooked, false);
	}

	// 2.0.3p THE TEETH, RSQ Grenade's Face() (RSQ_UBQSeries Grenade/zscript/rsqgn/hand.zs): the trigger squeezed
	// and the drawn grenade held at your face for a run of tics. The distance is from the drawn grenade's body centre
	// to your eyes (the pawn's x, y and the view height), in metres; RSQ's 0.47 / 0.71 m and 12 tics are the
	// defaults. Once taken, the far radius (or letting go of the trigger) re-arms it. Only runs with the pin in.
	static double PFloat(PlayerInfo p, Name n, double d) { let c = CVar.GetCVar(n, p); return c ? c.GetFloat() : d; }

	double FaceDist(PlayerPawn mo)
	{
		if (!geo)
			return 999;
		Vector3 v = DrawnNade(mo) - (mo.Pos.x, mo.Pos.y, mo.player.viewz);
		double vu = geo.vu > 0 ? geo.vu : 34;
		double ps = geo.ps > 0 ? geo.ps : 1.2;
		return (v.x, v.y, v.z * ps).Length() / vu;
	}

	void Face(PlayerPawn mo, bool trig)
	{
		let p = mo.player;
		if (RSR.PlayerInt(p, 'rsg_face', 1) == 0)
		{
			faceTic = 0;
			return;
		}
		double dist = FaceDist(mo);
		double near = PFloat(p, 'rsg_face_near', 0.47);
		double far = PFloat(p, 'rsg_face_far', 0.71);
		int hold = int(PFloat(p, 'rsg_face_hold', 12));
		if (!trig || dist > far)
			faceReady = true;
		if (trig && dist <= near)
			faceTic++;
		else
			faceTic = 0;
		if (faceReady && faceTic >= hold)
		{
			faceReady = false;
			faceTic = 0;
			armed = true;
			teethPin = true;
			mo.SetInventory('RSG_PinOut', 1);
			mo.A_StartSound("Grenade/Pin", CHAN_WEAPON, CHANF_OVERLAP);
			Buzz(mo);
		}
	}

	// the fastest step of the hand over the last tics, in the BODY'S frame (forward, left, up),
	// so the player's own walking and turning are already out of it
	Vector3 Swing(out double best)
	{
		best = 0;
		Vector3 vel = (0, 0, 0);
		for (int i = 0; i < count - 1; i++)
		{
			int a = (head - i + HIST) % HIST, b = (head - i - 1 + HIST) % HIST;
			Vector3 v = (hx[a] - hx[b], hy[a] - hy[b], hz[a] - hz[b]);
			double rel = v.Length();
			if (rel > best)
			{
				best = rel;
				vel = v;
			}
		}
		return vel;
	}

	bool Throw(PlayerPawn mo, int cooked, bool needSwing)
	{
		double best;
		Vector3 vel = Swing(best);
		double vu = geo.vu > 0 ? geo.vu : 34;
		if (needSwing && best < RSVR_Hand.THROW_MIN * vu / 35.0)
			return false;
		class<Actor> gc = Cls('HandGrenade');
		if (!gc)
			return false;
		// Swing() is in the body's frame: turn it back into the world before it is a direction.
		double bc = cos(mo.angle), bs = sin(mo.angle);
		Vector3 world = (vel.x * bc - vel.y * bs, vel.x * bs + vel.y * bc, vel.z);
		Vector3 dir = best > 0.01 ? world.Unit() : geo.F;
		// 2026-10-23: was clamp(best * 2.2, 3, 32). best is map units per TIC, so a brisk 2.5 m/s
		// throw is 2.43 units/tic and came out at speed 5 -- a dribble, and the ceiling of 32 was
		// unreachable at any human arm speed. Matched to the axe throw in rsvr/melee.zs, which
		// works: a floor you can feel, and a reachable top end.
		double spd = clamp(best * 3.0, 14, 42);
		let g = Actor.Spawn(gc, DrawnNade(mo), ALLOW_REPLACE);
		if (!g)
			return false;
		g.target = mo;
		g.angle = VectorAngle(dir.x, dir.y);
		g.pitch = -asin(clamp(dir.z, -1, 1));
		g.vel = dir * spd + mo.vel;
		class<Inventory> gt = (class<Inventory>)(Cls('GrenadeTime'));
		if (gt && cooked >= 16)
			g.GiveInventory(gt, cooked / 16);	// the fuse already burned in the hand
		mo.A_StartSound("Grenade/Toss", CHAN_WEAPON, CHANF_OVERLAP);
		if (!spoonOff)
			mo.A_StartSound("weapons/shell", CHAN_AUTO, CHANF_OVERLAP);
		Spent(mo);
		return true;
	}

	// the drawn grenade (its body centre) in the world: the controller plus the gun-hand offset (geo: this tic's frames)
	Vector3 DrawnNade(PlayerPawn mo)
	{
		Vector3 h = RSVR_VRHand.HandPos(mo);
		if (!geo)
			return h;
		return h + geo.FromGun((NADE_F, NADE_L, NADE_U));
	}

	void Boom(PlayerPawn mo)
	{
		class<Actor> ec = Cls('FragGrenadeExplosion');
		if (ec)
		{
			let e = Actor.Spawn(ec, DrawnNade(mo));
			if (e)
				e.target = mo;
		}
		Spent(mo);
	}

	void Spent(PlayerPawn mo)
	{
		class<Inventory> am = (class<Inventory>)(Cls('GrenadeAmmo'));
		if (am)
			mo.TakeInventory(am, 1);
		Reset(mo);
		mo.GiveInventory('RSG_Thrown', 1);
		Buzz(mo);
	}
}

class RSG_VR : RSVR_Token {}
class RSG_PinOut : RSVR_Token {}
class RSG_Spoon : RSVR_Token {}
class RSG_Thrown : RSVR_Token {}
class RSG_RingHand : RSVR_Token {}
