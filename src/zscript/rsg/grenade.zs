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
//      2.0.3r (owner 2026-11-03: "I still haven't seen the face-mouth pin pull work in either BD or ours"), as RSQ
//      Grenade's Face() now: the MOUTH, not a 0.47 m ball round player.viewz (the pawn's fixed 1.45 m eye, 0.25 m
//      under a 1.70 m headset, past 0.47 m for a tall player with vr_height_adjust; the chest counted). The mouth is
//      RSQ Tactical Rig's cigarette zone from your real eyes (the headset, rsq/scope.zs's eye height): lips to under
//      the chin, the controller, the drawn grenade or its ring within rsg_mouth_r (0.15 m) of it. The squeeze is the
//      trigger OR alt fire there: QuestZDoom's default vr_secondary_button_mappings makes the main grip a shift key, so
//      a fist round the grenade (grip and trigger) sends alt fire, never fire. A wobble of up to FACE_SLACK tics out
//      of the zone does not restart the count.
// BD22's own HandGrenade projectile, its fuse token, its explosion and sounds.
// Out of VR, or rsg_vr 0, BD22's own canned throw is untouched.
class RSG_Handler : EventHandler
{
	RSG_State st[MAXPLAYERS];

	// 2.0.3r SHOOT THROWN GRENADES (owner 2026-11-03 19:43, RSQ Grenade's rule): a player's shot or projectile within
	// SHOT_R (12 map units, 0.35 m at 34 a metre; BD22's grenade is 4 units) of a thrown HandGrenade sets it off on the
	// spot, once it is SHOT_GRACE tics (0.17 s) out of the hand. "Shoot Thrown Grenades" (rsg_shoot, on) and "Only in
	// Slow Motion" (rsg_shoot_slowmo, off: RSQ SlowMo asked by name). Melee (a reach of 128 or less) never does; a
	// grenade in the hand is a weapon, not a thing, and cannot be hit. Shot in the air, its blast carries RSG_Skeet
	// (RSQ Score's Trap Shot asks RSQ Grenade's service, which reads it).
	// FASTER GRENADES IN SLOW MOTION (rsg_slowmo_fast, off): RSQ SlowMo slows a thrown grenade with the world; with this
	// on it runs rsg_slowmo_speed (0.5) of the way from the world's speed up to real speed.
	const SHOT_R = 12.0;		// the largest reach (0.35 m); "Shot Grenade Reach" (rsg_shot_r, 2.0.3t) only tightens it
	// 2.0.3t (owner 2026-11-03 20:30: "let me have a slider to tighten it some but I won't make it bigger"): rsg_shot_r
	// metres, 0.10 to 0.35, x vr_vunits_per_meter, never past SHOT_R
	static double ShotR()
	{
		let c = CVar.FindCVar('rsg_shot_r');
		double m = clamp(c ? c.GetFloat() : 0.35, 0.10, 0.35);
		double vu = RSR.Float('vr_vunits_per_meter', 34);
		return min(m * (vu > 0 ? vu : 34), SHOT_R);
	}
	const SHOT_GRACE = 6;
	Array<Actor> nades;			// thrown HandGrenades (any thrower; a player's are the shootable ones)
	Array<int> nadeTic;			// ...the tic each was spawned
	Array<double> nadeBoost;	// ...the slow-motion boost applied to it now (1 none)
	Array<int> nadeId;			// ...a serial (the same on every machine): a shot names the grenade, not a place
	Array<double> nadeLX, nadeLY, nadeLZ;	// ...where it was a tic ago (the swept projectile test)
	Array<Actor> missiles;		// other live missiles (projectiles are not in the blockmap)
	Array<double> missLX, missLY, missLZ;	// ...where each was a tic ago
	int nadeSerial;

	static bool IsNade(Actor a) { Name c = a.GetClassName(); return c == 'HandGrenade' || c == 'HandGrenadeAlt'; }

	static double WorldScale()
	{
		let it = ServiceIterator.Find("RSQSM_Service");
		let s = it.Next();
		return s ? clamp(s.GetInt("scale", "", 0, 0, null) / 1000.0, 0.01, 1.0) : 1.0;
	}
	static bool CvOn(Name n, bool d) { let c = CVar.FindCVar(n); return c ? c.GetInt() != 0 : d; }
	static bool CanShoot() { return CvOn('rsg_shoot', true) && (!CvOn('rsg_shoot_slowmo', false) || WorldScale() < 0.999); }

	override void WorldThingSpawned(WorldEvent e)
	{
		let a = e.Thing;
		if (!a || !a.bMissile) return;
		if (IsNade(a)) { nades.Push(a); nadeTic.Push(a.Level.maptime); nadeBoost.Push(1.0); nadeId.Push(++nadeSerial); nadeLX.Push(a.pos.x); nadeLY.Push(a.pos.y); nadeLZ.Push(a.pos.z); }
		else { missiles.Push(a); missLX.Push(a.pos.x); missLY.Push(a.pos.y); missLZ.Push(a.pos.z); }
	}

	void ShotTick()
	{
		double w = WorldScale();
		double want = 1.0;
		if (w < 0.9999 && CvOn('rsg_slowmo_fast', false) && CvOn('rsqsm_slow_own', true))
		{
			let k = CVar.FindCVar('rsg_slowmo_speed');
			want = (w + (1.0 - w) * clamp(k ? k.GetFloat() : 0.5, 0.0, 1.0)) / w;
		}
		bool open = CanShoot();
		for (int i = nades.Size() - 1; i >= 0; i--)
		{
			let g = nades[i];
			if (!g || g.bDestroyed)
			{
				DropNade(i);
				continue;
			}
			// slow motion: RSQ SlowMo scales the velocity and the gravity by its factor; the boost rides on top
			if (g.target && g.target.player && abs(want - nadeBoost[i]) > 0.0005)
			{
				double r = want / nadeBoost[i];
				g.vel *= r;
				g.Gravity *= r * r;
				if (RSR.Debug(g.target.player))
					Console.Printf("RSG slow t%d: world x%.2f, grenade x%.2f", g.Level.maptime, w, w * want);
				nadeBoost[i] = want;
			}
			if (!open || !g.target || !g.target.player || g.Level.maptime - nadeTic[i] < SHOT_GRACE) { SetNadeLast(i, g.pos); continue; }
			bool hit = false;
			for (int m = 0; m < missiles.Size(); m++)
			{
				let t = missiles[m];
				// (a missile that burst in this tic's movement still counts: it passed)
				if (!t || t.bDestroyed || t.bNoInteraction || !t.target || !t.target.player || IsNade(t)) continue;
				if (t.GetMissileDamage(0, 1) <= 0) continue;	// a trail, a tracer, smoke: decoration that hurts nothing
				// SWEPT (a scoping read: a fast shot passed through between two samples): the closest the two came over the
				// last tic, each from where it was a tic ago to where it is now (WorldTick runs before the thinkers, and the
				// engine has already reset Prev, so the handler keeps the last positions itself)
				Vector3 r0 = (missLX[m], missLY[m], missLZ[m]) - (nadeLX[i], nadeLY[i], nadeLZ[i]), r1 = t.pos - g.pos;
				r0.z += (t.height - g.height) * 0.5;
				r1.z += (t.height - g.height) * 0.5;
				Vector3 dr = r1 - r0;
				double ll = dr dot dr;
				double k = ll > 0 ? clamp(-(r0 dot dr) / ll, 0.0, 1.0) : 1.0;
				if ((r0 + dr * k).Length() > ShotR() + t.radius) continue;
				Shoot(i, String.Format("projectile %s", t.GetClassName()), t.target);
				hit = true;
				break;
			}
			if (!hit) SetNadeLast(i, g.pos);
		}
		for (int m = 0; m < missiles.Size(); m++) if (missiles[m]) { missLX[m] = missiles[m].pos.x; missLY[m] = missiles[m].pos.y; missLZ[m] = missiles[m].pos.z; }
		for (int m = missiles.Size() - 1; m >= 0; m--)
			if (!missiles[m] || missiles[m].bDestroyed || !missiles[m].bMissile) { missiles.Delete(m); missLX.Delete(m); missLY.Delete(m); missLZ.Delete(m); }
	}

	void DropNade(int i) { nades.Delete(i); nadeTic.Delete(i); nadeBoost.Delete(i); nadeId.Delete(i); nadeLX.Delete(i); nadeLY.Delete(i); nadeLZ.Delete(i); }
	void SetNadeLast(int i, Vector3 p) { nadeLX[i] = p.x; nadeLY[i] = p.y; nadeLZ[i] = p.z; }

	// it goes off where it is: BD22's own blast (its Explode state's FragGrenadeExplosion), credited to the player whose
	// shot set it off (2.0.3v, owner 2026-11-04: anyone can shoot any thrown grenade in co-op and the shooter gets the
	// kill; it was the thrower's), the thrower when no shooter is known
	void Shoot(int i, String how, Actor by = null)
	{
		let g = nades[i];
		if (!g || g.bDestroyed) return;
		bool air = g.pos.z > g.floorz + 2;
		let ex = Actor.Spawn('FragGrenadeExplosion', g.pos, ALLOW_REPLACE);
		if (ex)
		{
			ex.target = (by && by.player) ? by : g.target;
			if (air) ex.GiveInventory('RSG_Skeet', 1);
		}
		if (g.target && g.target.player && RSR.Debug(g.target.player))
			Console.Printf("RSG shot t%d: %s, %s, %d tics out of the hand", g.Level.maptime, how, air ? "in the air (skeet)" : "on the ground", g.Level.maptime - nadeTic[i]);
		g.Destroy();
		DropNade(i);
	}

	// a hitscan of the console player's: the ray of the hand that fired (only this machine knows the hands), sent as an
	// event naming the grenade. 2.0.3v (RSQ 0.99a bug 54): it tested both hands' rays, so a hand that only pointed could
	// set a grenade off. The shot says which hand: QuestZDoom 17.3's weapon attacks mark an off-hand one (A_FireBullets
	// LAF_ISOFFHAND, A_RailAttack RGF_ISOFFHAND; P_LineAttack starts it from OffhandPos for that flag), and this mod's
	// own re-fires keep it (rsq/muzzle.zs, rsq/playerrounds.zs). The railgun (A_RailAttack, BD's RailGun) does not call the hitscan hook on 4.14.3: its own hook, the same.
	override bool WorldRailgunPreFired(WorldEvent e) { ShotTest(e, 1); return false; }
	override bool WorldHitscanPreFired(WorldEvent e) { ShotTest(e, 0); return false; }
	void ShotTest(WorldEvent e, int rail)
	{
		let mo = PlayerPawn(e.Thing);
		if (!mo || !mo.player || mo.PlayerNumber() != consoleplayer || !CanShoot() || nades.Size() == 0) return;
		if (e.AttackDistance > 0 && e.AttackDistance <= 128) return;
		double dist = e.AttackDistance > 0 ? e.AttackDistance : 8192;
		double ps = mo.Level.pixelstretch > 0 ? mo.Level.pixelstretch : 1.2;
		Vector3 a0, d0;
		if (RSVR_VRHand.InVR(mo))
		{
			bool off = rail == 1 ? (e.RailParams.flags & RGF_ISOFFHAND) != 0 : (e.AttackLineFlags & LAF_ISOFFHAND) != 0;
			if (off) { a0 = RSVR_VRHand.OffPos(mo); d0 = RSVR_VRHand.OffDir(mo, 0, 0, ps); }
			else { a0 = RSVR_VRHand.HandPos(mo); d0 = RSVR_VRHand.HandDir(mo, 0, 0, ps); }
		}
		else
		{
			double ca = cos(e.AttackPitch);
			a0 = mo.pos + (0, 0, mo.height * 0.5 - mo.Floorclip + mo.AttackZOffset * mo.player.crouchfactor + e.AttackZ);
			d0 = (cos(e.AttackAngle) * ca, sin(e.AttackAngle) * ca, -sin(e.AttackPitch));
		}
		for (int i = 0; i < nades.Size(); i++)
		{
			let g = nades[i];
			if (!g || g.bDestroyed || !g.target || !g.target.player) continue;
			for (int r = 0; r < 1; r++)		// one ray, the firing hand's (a loop so a miss can `continue` to the next grenade)
			{
				Vector3 ra = a0;
				Vector3 rd = d0;
				Vector3 c = g.pos + (0, 0, g.height * 0.5) - ra;
				double along = c dot rd;
				if (along < 0 || along > dist) continue;
				double miss = (c - rd * along).Length();
				if (miss > ShotR())
				{
					if (miss < 2 * SHOT_R && RSR.Debug(mo.player)) Console.Printf("RSG shot missed t%d: %.1f units off its centre, reach %.1f", mo.Level.maptime, miss, ShotR());
					continue;
				}
				if (RSR.Debug(mo.player)) Console.Printf("RSG shot ray t%d: %.1f units off its centre, reach %.1f", mo.Level.maptime, miss, ShotR());
				if (mo.Level.maptime - nadeTic[i] < SHOT_GRACE)
				{
					if (RSR.Debug(mo.player)) Console.Printf("RSG shot ignored t%d: the grenade is %d tics out of the hand (grace %d)", mo.Level.maptime, mo.Level.maptime - nadeTic[i], SHOT_GRACE);
					continue;
				}
				EventHandler.SendNetworkEvent("rsg_shoot", nadeId[i], rail);
				return;
			}
		}
		return;
	}

	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.IsManual || e.Name != "rsg_shoot" || !CanShoot()) return;
		// the grenade by its serial, validated: still tracked, live, a player's
		for (int i = 0; i < nades.Size(); i++)
			if (nadeId[i] == e.Args[0] && nades[i] && !nades[i].bDestroyed && nades[i].target && nades[i].target.player) { Shoot(i, e.Args[1] == 1 ? "railgun" : "hitscan", (e.Player >= 0 && e.Player < MAXPLAYERS && playeringame[e.Player]) ? players[e.Player].mo : null); break; }
	}

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

	// 2.0.3y (owner, BUGS_1.0 item 21: "right now we stand down, i want option for them to stand down as well"):
	// with RSQ Grenade loaded (its RSQGN_Handler, found by a String at run time: nothing of it is named when this
	// compiles) and "Use RSQ Grenade Instead" (rsg_rsq_nade, off) or RSQ Grenade's own "Replace Brutal Doom's Grenade"
	// (rsqgn_replace_bd, read by name) on, BRUTAL DOOM'S GRENADE STANDS DOWN: its weapon (HandGrenades) is put away
	// out of the inventory, so no slot key, wheel card or the VR pin and throw reach it, and BD22's grenade key
	// (TossGrenade) throws nothing. Its GrenadeAmmo is left as it is. Turned off again (or RSQ Grenade gone), the
	// weapon comes back with no ammo of its own (RSG_StoodDown remembers it across levels).
	static bool StandDown()
	{
		String n = "RSQGN_Handler";
		class<Object> c = n;
		if (!c)
			return false;
		if (CvOn('rsg_rsq_nade', false))
			return true;
		let cv = CVar.FindCVar('rsqgn_replace_bd');
		return cv && cv.GetInt() != 0;
	}

	void StandTick(PlayerPawn mo, bool down)
	{
		let p = mo.player;
		Name wn = 'HandGrenades';
		class<Inventory> wc = wn;
		if (!wc || p.playerstate != PST_LIVE)
			return;
		let w = Weapon(mo.FindInventory(wc));
		if (down)
		{
			String tn = "TossGrenade";	// BD22's grenade key's token (DEFAULTWEAPON.dec TossGrenade): no throw; by name at run time
			class<Inventory> tc = tn;
			if (tc)
				mo.SetInventory(tc, 0);
			if (p.PendingWeapon == w && w)
				p.PendingWeapon = WP_NOCHANGE;
			if (!w)
				return;
			if (p.ReadyWeapon == w)
			{
				// put it away first (the fists), then out of the inventory
				if (p.PendingWeapon == WP_NOCHANGE)
				{
					Name fn = 'Melee_Attacks';
					class<Inventory> fc = fn;
					let f = fc ? Weapon(mo.FindInventory(fc)) : null;
					if (f)
						p.PendingWeapon = f;
					else
						p.mo.PickNewWeapon(null);
				}
				return;
			}
			if (p.OffhandWeapon == w)
				return;		// (QuestZDoom's switch hand put it there: wait for it to leave)
			mo.TakeInventory(wc, 1);
			mo.SetInventory('RSG_StoodDown', 1);
			if (RSR.PlayerInt(p, 'rsq_switch_log', 0) > 0)
				Console.Printf("RSG t%d: RSQ Grenade is loaded and replaces this grenade: BD22's HandGrenades put away", mo.Level.maptime);
			return;
		}
		if (mo.CountInv('RSG_StoodDown') > 0)
		{
			mo.SetInventory('RSG_StoodDown', 0);
			if (w)
				return;
			let pend = p.PendingWeapon;
			let g = Weapon(Actor.Spawn(wc, mo.pos, NO_REPLACE));
			if (g)
			{
				g.AmmoGive1 = 0;
				g.AmmoGive2 = 0;
				if (!g.CallTryPickup(mo))
					g.Destroy();
			}
			if (p.PendingWeapon != pend)
				p.PendingWeapon = pend;
		}
	}

	override void WorldTick()
	{
		ShotTick();
		bool down = StandDown();
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n] || !players[n].mo)
				continue;
			let mo = players[n].mo;
			StandTick(mo, down);
			if (!st[n])
				st[n] = new('RSG_State');
			if (!down)
				st[n].Tick(mo);
		}
	}
}

class RSG_State play
{
	const FUSE = 48;				// BD22: GrenadeTime 3, 16 tics a count
	const RING_GRAB = 12.0;			// cm round the ring the off hand can take it
	const PULL = 8.0;				// cm past that: the pin is out
	const HIST = 7;		// ONE THROW (RSQ 11-10): the series' 7 tics (was 6)
	const RING_F = 3.45;		// the ring's centre: nade.md3 as drawn in the FBX hand (MODELDEF.rsq RQNP, fit_nade.py), gun hand cm (F, L, U)
	const RING_L = 5.12;
	const RING_U = 5.06;
	const NADE_F = 2.77;		// the grenade body's centre as drawn (moved 4.0 cm by the FBX hand fit): the throw and the in-hand blast start here
	const NADE_L = 4.23;
	const NADE_U = -1.97;
	const MOUTH_AF = 0.04;		// 2.0.3r THE MOUTH (RSQ Tactical Rig cig.zs ZONE_*): lips 0.04 m forward of the eyes, 0.06 under
	const MOUTH_AD = 0.06;
	const MOUTH_BF = 0.08;		// ...to just under the chin, 0.08 forward, 0.19 under (the head's frame)
	const MOUTH_BD = 0.19;
	const FACE_SLACK = 4;		// tics out of the zone (or off the squeeze) a hold forgives

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
	int faceMiss;		// 2.0.3r: tics it has been away (or unsqueezed) during a hold
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
		bool alt = (mo.player.cmd.buttons & BT_ALTATTACK) != 0;	// 2.0.3r: a gripped squeeze (see the top, 4.)

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
			Face(mo, trig || alt, trig ? "trigger" : alt ? "alt" : "none");
			return;
		}
		faceTic = 0;
		faceMiss = 0;
		if (!trig && !alt)
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

	// 2.0.3p THE TEETH, RSQ Grenade's Face() (RSQ_UBQSeries Grenade/zscript/rsqgn/hand.zs): the grenade squeezed and
	// held at your mouth for a run of tics (rsg_face_hold, 12). 2.0.3r: at your MOUTH (see the top, 4.), measured from
	// your real eyes; once taken, a hand clear of the mouth by rsg_face_far (0.71 m) or a let-go squeeze re-arms it.
	// Only runs with the pin in.
	static double PFloat(PlayerInfo p, Name n, double d) { let c = CVar.GetCVar(n, p); return c ? c.GetFloat() : d; }

	// YOUR REAL EYES (rsq/scope.zs Eye, the way the renderer places them): the pawn's x, y; viewz plus the headset's
	// height less the pawn's view height (vr_crouch_use_button on, the default: viewz stays at the pawn's eye and the
	// headset's real height is added afterwards, hw_openxrdevice.cpp:219; the hands are placed from the controller's
	// real height, hw_openxrdevice.cpp:595 / gl_openvr.cpp GetHandTransform). No headset height read: viewz.
	Vector3 Eyes(PlayerPawn mo)
	{
		let p = mo.player;
		Vector3 e = (mo.pos.x, mo.pos.y, p.viewz);
		let cb = CVar.FindCVar('vr_crouch_use_button');
		if (mo.HmdPosition.y > 0.3 && (!cb || cb.GetBool()))
			e.z += (mo.HmdPosition.y + RSR.Float('vr_height_adjust', 0)) * geo.vu / geo.ps - RSVR_VRHand.StandEyeHeight(mo);	// 2.0.4g: never DOWN's scaled ViewHeight
		return e;
	}

	// metres forward along where you look and down, from the eyes, in the head's frame (yaw and pitch: the headset's)
	Vector3 FromEyes(PlayerPawn mo, double fwd, double down)
	{
		double hp = clamp(mo.pitch, -89, 89);
		double horiz = fwd * cos(hp) - down * sin(hp);
		double vert = -fwd * sin(hp) - down * cos(hp);
		return Eyes(mo) + (cos(mo.angle) * horiz * geo.vu, sin(mo.angle) * horiz * geo.vu, vert * geo.vu / geo.ps);
	}

	// room metres from pt to the segment a-b
	double SegDist(Vector3 pt, Vector3 a, Vector3 b)
	{
		Vector3 ab = b - a, ap = pt - a;
		ab = (ab.x, ab.y, ab.z * geo.ps) / geo.vu;
		ap = (ap.x, ap.y, ap.z * geo.ps) / geo.vu;
		double ll = ab dot ab;
		double t = ll > 0 ? clamp((ap dot ab) / ll, 0.0, 1.0) : 0.0;
		return (ap - ab * t).Length();
	}

	// metres from the mouth zone's line to the nearest of the controller, the drawn grenade and its ring
	double MouthDist(PlayerPawn mo)
	{
		if (!geo || geo.vu <= 0 || geo.ps <= 0)
			return 999;
		Vector3 a = FromEyes(mo, MOUTH_AF, MOUTH_AD), b = FromEyes(mo, MOUTH_BF, MOUTH_BD);
		Vector3 c = RSVR_VRHand.HandPos(mo);
		double d = SegDist(c, a, b);
		d = min(d, SegDist(c + geo.FromGun((NADE_F, NADE_L, NADE_U)), a, b));
		return min(d, SegDist(c + geo.FromGun((RING_F, RING_L, RING_U)), a, b));
	}

	void Face(PlayerPawn mo, bool squeeze, String by)
	{
		let p = mo.player;
		if (RSR.PlayerInt(p, 'rsg_face', 1) == 0)
		{
			faceTic = 0;
			faceMiss = 0;
			return;
		}
		double dist = MouthDist(mo);
		double reach = clamp(PFloat(p, 'rsg_mouth_r', 0.15), 0.03, 0.40);
		double far = PFloat(p, 'rsg_face_far', 0.71);
		int hold = clamp(int(PFloat(p, 'rsg_face_hold', 12)), 1, 70);
		bool atMouth = dist <= reach;
		if (!squeeze || dist > far)
			faceReady = true;
		if (squeeze && atMouth)
		{
			faceTic++;
			faceMiss = 0;
		}
		else if (faceTic > 0 && ++faceMiss > FACE_SLACK)
		{
			faceTic = 0;
			faceMiss = 0;
		}
		bool dbg = RSR.Debug(p);	// "Print each reload step" (rsr_debug)
		if (faceReady && faceTic >= hold)
		{
			faceReady = false;
			faceTic = 0;
			faceMiss = 0;
			armed = true;
			teethPin = true;
			mo.SetInventory('RSG_PinOut', 1);
			mo.A_StartSound("Grenade/Pin", CHAN_WEAPON, CHANF_OVERLAP);
			Buzz(mo);
			if (dbg)
				Console.Printf("RSG teeth t%d: squeezed by %s, %.2f m from the mouth (reach %.2f) for %d tics", mo.Level.maptime, by, dist, reach, hold);
		}
		else if (dbg && (squeeze || atMouth) && mo.Level.maptime % 5 == 0)
			Console.Printf("RSG face t%d mouth %.2f m (reach %.2f) squeeze %s held %d/%d ready %d", mo.Level.maptime, dist, reach, by, faceTic, hold, faceReady);
	}

	// the fastest step of the hand over the last tics, in the BODY'S frame (forward, left, up),
	// so the player's own walking and turning are already out of it.
	// ONE THROW (RSQ series, owner 11-10: "one throw for everything"): the series' one sampler, as in RSQ Grenade (hand.zs
	// Sample / Peak), RSQ Saber, RSQ ShieldSaw and this pack's axe: the fastest 2-TIC window over the last 7 tics (it was
	// the fastest single-tic step), the vertical squash (pixelstretch) taken out of the speed, and over a metre in two
	// tics no motion (a pose jump). Still map units a tic, so THROW_MIN (2.5 m/s) and the flight read it as before.
	Vector3 Swing(out double best)
	{
		best = 0;
		Vector3 vel = (0, 0, 0);
		double ps = level.pixelstretch > 0.1 ? level.pixelstretch : 1.2;
		double vu = geo.vu > 0 ? geo.vu : 34;
		for (int i = 0; i + 2 < count; i++)
		{
			int a = (head - i + HIST) % HIST, b = (head - i - 2 + HIST) % HIST;
			Vector3 v = (hx[a] - hx[b], hy[a] - hy[b], hz[a] - hz[b]) * 0.5;
			double rel = (v.x, v.y, v.z * ps).Length();
			if (rel / vu >= 0.5) continue;
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
class RSG_Skeet : Inventory {}	// 2.0.3r: on the blast of a grenade shot in the air (RSG_Handler.Shoot)
class RSG_StoodDown : RSVR_Token {}	// 2.0.3y: BD22's HandGrenades was put away for RSQ Grenade (RSG_Handler.StandTick)
