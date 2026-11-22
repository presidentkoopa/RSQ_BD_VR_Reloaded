// RS VR reload gesture (1.17 flick, owner) and THE RELOAD BUTTON (2.0.5e, owner 2026-11-22).
//
// WHERE IT RUNS (unchanged since 1.17 / 2.0.3x): with a GUN IN EACH HAND, each gun's gesture reloads THAT gun with
// BD22's own reload, and only that one. With one gun (off hand free or a fist) VR reloading (rsr) has the gun, except:
// a lone rifle's gesture loads its LAUNCHER only (the magazine stays the hand reload's); a lone SSG reloads itself
// (SSG.dec RSQ_FlickReload); an RSQ series off-hand item (saber, Zippo, ShieldSaw...) closes the hand reload, so then
// the main gun's gesture reloads it (2.0.3x). Purist: off (BD22 purist has no reloading). rsq_flick 0: no gesture.
//
// THE GESTURE (Reload Gesture, rsq_reload_gesture):
//   0 POINT OFF-SCREEN + TRIGGER (2.0.5e, the default; owner 2026-11-22: House of the Dead's "shoot off-screen to
//     reload", because the wrist flick hurts). Point the gun off-screen -- at least Off-Screen Angle (rsq_offscreen_deg,
//     60 by default) below where you look, or CONE_DEG off it (behind you) -- and pull THAT hand's trigger: that gun
//     reloads instead of firing. No speed, no wrist. Measured against the headset's own view, so a low shot at a
//     crawling enemy you are looking at is on screen and fires as always.
//     HOW THE SHOT IS STOPPED (no engine change): the engine fires from the weapon layers' tick (PlayerPawn.TickPSprites:
//     each layer ticks, then CheckWeaponFire), and BD22's ready loops also jump to Fire from the buttons themselves. So a
//     layer of our own, GATE_LAYER, sits BELOW every weapon layer (the layers tick in id order) and ticks first: with the
//     gun pointed off-screen and its trigger pressed this tic, it sends the gun into its Reload before the gun's own
//     tick can see the trigger. The gun is idle at that moment exactly when its ready flag is still set from its last
//     A_WeaponReady (the engine clears the flag on every state change). A press that finds the gun busy (a refire's
//     last frames) waits up to PRESS_TICS for it: a second layer, GATE_LATE, sits ABOVE every weapon layer and ticks
//     after them, just before the engine's own trigger check, so a gun that comes back to its ready loop with the
//     trigger still held goes into its Reload there instead of firing. A lone rifle's gesture loads its launcher:
//     the press fires nothing while it is held (RSQ_HotdStates Hold); with nothing to load it fires as always.
//   1 FLICK (old): snap the barrel down -- it drops FLICK_DEG within FLICK_TICS, ends DOWN_DEG below level, and re-arms
//     above REARM_DEG -- read from the barrel's elevation, which turning and walking do not change.
// Either way the gun must be in its ready loop (its hand's ready flag), so it never cuts into firing or a reload.
//
// THE RELOAD BUTTON (owner 2026-11-22: "as long as the button press is guaranteed to work"): QuestZDoom's Reload (any
// of BT_RELOAD, BT_MAINHANDRELOAD, BT_OFFHANDRELOAD) reloads EVERY hand that holds a gun, in one press, whatever the
// pose, gesture or option: a gun busy firing takes it as soon as it is ready again (the press waits BUTTON_TICS); a
// hand reload already under way on the main gun finishes by itself (rsr/vreload.zs RSR_State.autoDone: the magazine
// falls, the new one goes home, the handle racks, at the gun's own sounds); a main gun the hand reload takes (VR
// reloading on, one gun) starts it and finishes it the same way. A rifle's launcher that needs a round gets one
// (rsr/rsr_m203.zs RSM.FlickLoad: a rocket or a hand grenade by the Underbarrel Ammo row, RSQ Grenade's of your kind).
// The pump shotgun and the break-open guns held alone keep their own VR loading on the button as before
// (rsr_pump.zs InsertWanted puts a shell in on it).
class RSQ_Flick : EventHandler
{
	const FLICK_DEG = 45.0;		// degrees of drop...
	const FLICK_TICS = 4;		// ...within this many tics (about 400 degrees a second)
	const DOWN_DEG = -40.0;
	const REARM_DEG = -15.0;
	const HIST = 8;
	// 2.0.5e
	const GATE_LAYER = -24100;	// the House of the Dead gate (below every weapon layer: it ticks first)
	const GATE_LATE = 0x7FFF0000;	// ...and its second layer, above every weapon layer (it ticks last, before the trigger check)
	const CONE_DEG = 120.0;		// a gun this far off where you look is off-screen too (behind you)
	const HYST_DEG = 8.0;		// once off-screen, back on screen only this far inside the line (no flutter on it)
	const PRESS_TICS = 10;		// an off-screen press waits this long for a gun still busy (its refire's last frames)
	const BUTTON_TICS = 105;	// a Reload press waits this long (3 s) for a gun that is busy
	const BTN_MASK = BT_RELOAD | BT_MAINHANDRELOAD | BT_OFFHANDRELOAD;

	double el[MAXPLAYERS][2][HIST];
	int head[MAXPLAYERS][2];
	int count[MAXPLAYERS][2];
	bool armed[MAXPLAYERS][2];
	// 2.0.5e the gesture: per hand, from the last WorldTick (the gate reads them before the next tic's weapons)
	int role[MAXPLAYERS][2];		// 0 nothing, 1 the gesture reloads the gun, 2 it loads a lone rifle's launcher only
	bool offScr[MAXPLAYERS][2];		// the gun points off-screen
	bool gateTrig[MAXPLAYERS][2];	// that hand's trigger at the gate's last tic
	int pressLeft[MAXPLAYERS][2];	// an off-screen press still waiting for its gun, tics
	bool holding[MAXPLAYERS][2];	// the press loaded the launcher: the gun is held (RSQ_HotdStates Hold) until it is let go
	// 2.0.5e the Reload button
	bool btnPrev[MAXPLAYERS];
	int btnLeft[MAXPLAYERS][2];
	int btnAge[MAXPLAYERS][2];		// tics the press has waited for that hand
	bool rdyPrev[MAXPLAYERS][2];	// that hand's gun was in its ready loop at the last WorldTick
	int autoWatch[MAXPLAYERS];		// tics a hand reload starting on the main gun still finishes by itself

	// the hand-held things that are not guns: they have no magazine to reload
	static bool IsGun(Weapon w)
	{
		if (!w || w is 'RSQ_Hands')
			return false;
		static const Name notGuns[] = { 'Melee_Attacks', 'BrutalAxe', 'Chain_saw', 'DSweap', 'HandGrenades' };
		for (int i = 0; i < notGuns.Size(); i++)
		{
			class<Actor> c = notGuns[i];
			if (c && w is c)
				return false;
		}
		return w.FindState("Reload") != null;
	}

	// 2.0.3x (owner 11-05 01:12): "When the saber or Zippo or ShieldSaw is in the off hand, we need to be
	// able to flick reload our main-hand weapon." With one of the RSQ series' off-hand items there, the hand
	// reload is closed (vreload.zs Wanted: the off hand must be RSQ_Hands to hold the magazine), so the main
	// gun flicks into BD22's own Reload, which needs no off hand. Matched by class name, no dependency.
	static bool IsSeriesOffItem(Weapon w)
	{
		if (!w)
			return false;
		static const Name items[] = {
			'UBQS_SaberBase', 'UBQS_ForceHand',			// RSQ Saber: off-hand saber, Force hand
			'SSQ_ShieldSaw',					// RSQ ShieldSaw
			'RSQTR_ZippoWeapon', 'RSQTR_CigWeapon',			// RSQ Tactical Rig
			'RSQFF_Held', 'RSQFF_Torch',				// RSQ Flash & Flare
			'RSQWP_WhipWeapon', 'RSQGN_Grenade', 'RSQ_Glove'	// Whip, Grenade, Melee gloves in the off hand
		};
		for (int i = 0; i < items.Size(); i++)
		{
			class<Actor> c = items[i];
			if (c && w is c)
				return true;
		}
		return false;
	}

	// 2.0.5e: Reload Gesture (rsq_reload_gesture): 0 Point Off-Screen + Trigger, 1 Flick (old)
	static int Style(PlayerPawn mo)
	{
		return RSQ.PlayerInt(mo, 'rsq_reload_gesture', 0) == 1 ? 1 : 0;
	}

	static double OffDeg(PlayerPawn mo)
	{
		let cv = CVar.GetCVar('rsq_offscreen_deg', mo.player);
		return clamp(cv ? cv.GetFloat() : 60.0, 40.0, 85.0);
	}

	// the gun (unit direction d) points off-screen: Off-Screen Angle or more below where the headset looks, or CONE_DEG
	// or more off it. In VR the pawn's angle and pitch are the headset's. Once off-screen it stays so until HYST_DEG back.
	static bool OffScreen(PlayerPawn mo, Vector3 d, bool was)
	{
		double cp = cos(mo.pitch);
		Vector3 v = (cp * cos(mo.angle), cp * sin(mo.angle), -sin(mo.pitch));
		double below = -mo.pitch - asin(clamp(d.z, -1, 1));	// degrees the gun points under the view's own elevation
		double off = acos(clamp(d dot v, -1, 1));
		double slack = was ? HYST_DEG : 0;
		return below >= OffDeg(mo) - slack || off >= CONE_DEG - slack;
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n] || !players[n].mo)
				continue;
			let mo = players[n].mo;
			let p = mo.player;
			bool alive = p.playerstate == PST_LIVE && mo.health > 0;
			Button(mo, n, alive);
			bool live = RSVR_VRHand.InVR(mo) && alive
				&& RSQ.PlayerInt(mo, 'rsq_flick', 1) != 0 && mo.CountInv('IsPlayingAsPurist') == 0;
			bool hotd = live && Style(mo) == 0;
			GateLayer(mo, hotd);
			bool on = live && IsGun(p.OffhandWeapon);	// 1.21: a gun in the off hand gestures, whatever the main hand holds
			// 2026-10-23: with ONE rifle the whole flick was off, so "flick down to reload both
			// barrels" (1.30) only ever worked while dual wielding -- and a lone rifle is the
			// common case. A single rifle now flicks for its LAUNCHER ONLY: the magazine stays
			// the hand reload's, exactly as the header says, and the flick gets the M203.
			bool loneM203 = live && !on && RSM.IsAnyRifle(p.ReadyWeapon);
			// 2.0.2a (owner 20:09): "ssg should always flick down to reload even if we allow for our vr
			// reload". A lone SSG flicks too (SSG.dec RSQ_FlickReload); the hand reload is still there.
			bool loneSSG = live && !on && p.ReadyWeapon is 'SSG';
			// 2.0.3x: a series off-hand item (saber, Zippo, shield...) in the off hand: the main gun flicks
			bool offItem = live && !on && IsSeriesOffItem(p.OffhandWeapon) && IsGun(p.ReadyWeapon);
			double ps = mo.Level.pixelstretch;
			if (ps <= 0)
				ps = 1.2;
			for (int h = 0; h < 2; h++)
			{
				// the main gun gestures only when the off hand has a gun too (one gun alone: VR reload)
				bool run = on && (h != 0 || IsGun(p.ReadyWeapon)) || h == 0 && (loneSSG || offItem);
				bool m203Only = !run && h == 0 && loneM203;	// a lone rifle: the launcher only
				role[n][h] = run ? 1 : (m203Only ? 2 : 0);
				if (!run && !m203Only)
				{
					count[n][h] = 0;
					armed[n][h] = false;
					offScr[n][h] = false;
					continue;
				}
				Vector3 d = h == 0 ? RSVR_VRHand.HandDir(mo, 0, 0, ps) : RSVR_VRHand.OffDir(mo, 0, 0, ps);
				if (hotd)
				{
					// 2.0.5e: the gate (GATE_LAYER) does the rest, next tic, ahead of the gun
					offScr[n][h] = OffScreen(mo, d, offScr[n][h]);
					count[n][h] = 0;
					armed[n][h] = false;
					continue;
				}
				offScr[n][h] = false;
				double e = asin(clamp(d.z, -1, 1));
				head[n][h] = (head[n][h] + 1) % HIST;
				el[n][h][head[n][h]] = e;
				if (count[n][h] < HIST)
					count[n][h]++;
				if (e > REARM_DEG)
					armed[n][h] = true;
				if (!armed[n][h] || count[n][h] <= FLICK_TICS || e > DOWN_DEG)
					continue;
				double before = el[n][h][(head[n][h] - FLICK_TICS + HIST) % HIST];
				if (before - e < FLICK_DEG)
					continue;
				armed[n][h] = false;
				if (m203Only)
					RSM.FlickLoad(mo, false);	// the magazine stays the hand reload's
				else
					Reload(p, h);
			}
		}
	}

	// 2.0.5e: the gate's two layers on while the House of the Dead gesture is (they do nothing while no gun points off-screen)
	static void GateLayer(PlayerPawn mo, bool want)
	{
		let p = mo.player;
		if (!want)
		{
			if (p.FindPSprite(GATE_LAYER))
				p.SetPsprite(GATE_LAYER, null);
			if (p.FindPSprite(GATE_LATE))
				p.SetPsprite(GATE_LATE, null);
			return;
		}
		let g = mo.FindInventory('RSQ_HotdGate');
		if (!g)
		{
			mo.GiveInventory('RSQ_HotdGate', 1);
			g = mo.FindInventory('RSQ_HotdGate');
			if (!g)
				return;
		}
		GateOn(p, g, GATE_LAYER, g.FindState("Gate"));
		GateOn(p, g, GATE_LATE, g.FindState("GateLate"));
	}

	static void GateOn(PlayerInfo p, Inventory g, int id, State st)
	{
		let psp = p.FindPSprite(id);
		if (!st || psp && psp.Caller == g)
			return;
		p.SetPsprite(id, st, false, g);
		psp = p.FindPSprite(id);
		if (psp)
			psp.bAddWeapon = false;
	}

	// 2.0.5e THE GATE (RSQ_HotdGate's layers, every tic: late false at the start of the player's weapon tick, late true at
	// its end, just before the engine's trigger check; see the header)
	void Gate(PlayerPawn mo, bool late)
	{
		let p = mo.player;
		int n = mo.PlayerNumber();
		if (!p || n < 0 || n >= MAXPLAYERS)
			return;
		for (int h = 0; h < 2; h++)
		{
			bool trig = (p.cmd.buttons & (h == 0 ? BT_ATTACK : BT_OFFHANDATTACK)) != 0;
			Weapon w = h == 0 ? p.ReadyWeapon : p.OffhandWeapon;
			int layer = h == 0 ? PSP_WEAPON : PSP_OFFHANDWEAPON;
			int ready = h == 0 ? WF_WEAPONREADY : WF_OFFHANDREADY;
			if (!late)
			{
				bool press = trig && !gateTrig[n][h];
				gateTrig[n][h] = trig;
				// a press that loaded the launcher: the gun waits, firing nothing, until the trigger is let go
				if (holding[n][h])
				{
					let hp = p.FindPSprite(layer);
					let hs = GetDefaultByType('RSQ_HotdStates').FindState("Hold");
					if (!w || !hp || hp.Caller != w || hp.CurState != hs)
						holding[n][h] = false;
					else if (!trig || mo.health <= 0)
					{
						holding[n][h] = false;
						p.SetPsprite(layer, w.GetReadyState(), false, w);
					}
					continue;
				}
				if (press)
					pressLeft[n][h] = PRESS_TICS;
			}
			if (pressLeft[n][h] <= 0)
				continue;
			if (!trig || !offScr[n][h] || role[n][h] == 0 || !w || mo.health <= 0)
			{
				pressLeft[n][h] = 0;
				continue;
			}
			if (!late)
				pressLeft[n][h]--;
			if (role[n][h] == 2)
			{
				// a lone rifle: its launcher, when it needs a round and one is carried; else the shot goes as always
				if (!(p.WeaponState & ready))
					continue;
				pressLeft[n][h] = 0;
				if (!RSM.FlickLoad(mo, h != 0))
					continue;
				let hs = GetDefaultByType('RSQ_HotdStates').FindState("Hold");
				if (hs)
				{
					p.SetPsprite(layer, hs, false, w);
					holding[n][h] = true;
				}
				if (CVar.GetCVar('rsq_switch_log', p).GetInt() > 0)
					Console.Printf("RSQ off-screen t%d: %s hand %d loaded its launcher", level.maptime, w.GetClassName(), h);
				continue;
			}
			if (Reload(p, h))
			{
				pressLeft[n][h] = 0;
				if (CVar.GetCVar('rsq_switch_log', p).GetInt() > 0)
					Console.Printf("RSQ off-screen t%d: %s hand %d reloads%s", level.maptime, w.GetClassName(), h, late ? " (it was busy)" : "");
			}
		}
	}

	// 2.0.5e THE RELOAD BUTTON (see the header)
	void Button(PlayerPawn mo, int n, bool alive)
	{
		let p = mo.player;
		bool down = (p.cmd.buttons & BTN_MASK) != 0;
		bool press = down && !btnPrev[n];
		btnPrev[n] = down;
		if (!alive || mo.CountInv('IsPlayingAsPurist') > 0)
		{
			btnLeft[n][0] = btnLeft[n][1] = 0;
			autoWatch[n] = 0;
			rdyPrev[n][0] = rdyPrev[n][1] = false;
			return;
		}
		for (int h = 0; h < 2; h++)
		{
			if (press)
			{
				btnLeft[n][h] = BUTTON_TICS;
				btnAge[n][h] = 0;
			}
			if (btnLeft[n][h] > 0)
			{
				btnLeft[n][h]--;
				if (ButtonHand(mo, n, h, press))
					btnLeft[n][h] = 0;
				btnAge[n][h]++;
			}
		}
		// the press's hand reload on the main gun, however it started (BD22's own reload key, or ours): it finishes by itself
		if (autoWatch[n] > 0)
		{
			autoWatch[n]--;
			let rs = RSR_ReloadHandler.StateOf(mo);
			if (rs && rs.phase != RSR.IDLE && rs.weap && rs.weap == p.ReadyWeapon && !rs.autoDone)
			{
				rs.autoDone = true;
				autoWatch[n] = 0;
				if (CVar.GetCVar('rsq_switch_log', p).GetInt() > 0)
					Console.Printf("RSQ reload button t%d: the hand reload of %s finishes by itself", mo.Level.maptime, rs.weap.GetClassName());
			}
		}
		rdyPrev[n][0] = (p.WeaponState & WF_WEAPONREADY) != 0;
		rdyPrev[n][1] = (p.WeaponState & WF_OFFHANDREADY) != 0;
	}

	// One hand's share of a Reload press; true when it is done with it (the gun is reloading, or there is nothing there to
	// reload). BD22 already answers its reload key for the MAIN hand: its "Reloading" token, which the gun's ready loop
	// reads, and which waits there while the gun is busy. So the main hand takes BD22's path whenever BD22 gave it
	// (never a second reload after it), and ours when it did not (another of QuestZDoom's reload buttons); the OFF hand
	// has no path of BD22's (the off-hand copies never read the token), so it is always ours.
	bool ButtonHand(PlayerPawn mo, int n, int h, bool first)
	{
		let p = mo.player;
		Weapon w = h == 0 ? p.ReadyWeapon : p.OffhandWeapon;
		if (!IsGun(w))
			return true;
		bool log = CVar.GetCVar('rsq_switch_log', p).GetInt() > 0;
		// a rifle's launcher at once: it needs no ready gun
		if (first && RSM.IsAnyRifle(w) && RSM.FlickLoad(mo, h != 0) && log)
			Console.Printf("RSQ reload button t%d: hand %d launcher loaded", mo.Level.maptime, h);
		int ready = h == 0 ? WF_WEAPONREADY : WF_OFFHANDREADY;
		bool rdy = (p.WeaponState & ready) != 0;
		if (h == 0)
		{
			autoWatch[n] = BUTTON_TICS;		// a hand reload that starts from this press finishes by itself (Button)
			let rs = RSR_ReloadHandler.StateOf(mo);
			if (rs && rs.phase != RSR.IDLE && rs.weap == w)
				return true;			// under way already: Button finishes it
			if (mo.CountInv('Reloading') > 0)
				return true;			// BD22's own: the gun takes it from its ready loop
			bool trig = (p.cmd.buttons & BT_ATTACK) != 0;
			if (rdyPrev[n][h] && !rdy && !trig)
				return true;			// the gun went into its reload this tic (BD22's key)
			if (!rdy || btnAge[n][h] < 1)
				return false;			// busy, or a tic for BD22's own key to answer first
		}
		if (!Reload(p, h))
			return false;		// busy: the press waits for it
		if (log)
			Console.Printf("RSQ reload button t%d: %s hand %d reloads", mo.Level.maptime, w.GetClassName(), h);
		return true;
	}

	// that hand's gun into its own reload, from its ready loop; true when it went (2.0.5e: the result is new)
	static bool Reload(PlayerInfo p, int h)
	{
		Weapon w = h == 0 ? p.ReadyWeapon : p.OffhandWeapon;
		int ready = h == 0 ? WF_WEAPONREADY : WF_OFFHANDREADY;
		if (!w)
			return false;
		// 2.0.2a: an SSG (either hand, dual or alone) flicks into its own reload, SSG.dec RSQ_FlickReload,
		// from its ready loop OR while it waits open for the hand reload (RSB_Wait): an empty SSG sits there
		// (rig flick3: ready 0). The hand reload is closed first.
		State fl = w is 'SSG' ? w.FindState("RSQ_FlickReload") : null;
		if (fl)
		{
			let psp = p.GetPSprite(h == 0 ? PSP_WEAPON : PSP_OFFHANDWEAPON);
			bool open = psp && psp.CurState == w.FindState("RSB_Wait");
			if (!(p.WeaponState & ready) && !open)
				return false;
			let bs = p.mo ? RSB_Handler.StateOf(p.mo) : null;
			if (bs && bs.weap == w && bs.phase != RSB.IDLE)
				bs.Abort(p.mo);
			p.SetPsprite(h == 0 ? PSP_WEAPON : PSP_OFFHANDWEAPON, fl, false, w);
			if (CVar.GetCVar('rsq_switch_log', p).GetInt() > 0)
				Console.Printf("RSQ flick t%d: %s hand %d flick reload (%s)", level.maptime, w.GetClassName(), h, open ? "was open" : "was ready");
			return true;
		}
		if (!(p.WeaponState & ready))
			return false;
		State st = w.FindState("Reload");
		if (!st)
			return false;
		// 2.0.3x: RSQ Saber / ShieldSaw carry their own copy of this flick (UBQS_OffFlick, SSQ_OffFlick); if one
		// of them already entered the Reload this tic, don't restart it, and clear the ready flag after ours so
		// theirs (later this tic) sees the gun busy: one flick, one reload.
		let rp = p.GetPSprite(h == 0 ? PSP_WEAPON : PSP_OFFHANDWEAPON);
		if (rp && rp.CurState == st)
			return true;
		p.SetPsprite(h == 0 ? PSP_WEAPON : PSP_OFFHANDWEAPON, st, false, w);
		p.WeaponState &= ~ready;
		if (CVar.GetCVar('rsq_switch_log', p).GetInt() > 0)
			Console.Printf("RSQ flick t%d: %s hand %d flick reload (off hand %s)", level.maptime, w.GetClassName(), h,
				p.OffhandWeapon ? p.OffhandWeapon.GetClassName() : 'none');
		// 1.30 (owner: "flick down to reload both barrels"): a rifle's empty M203 loads with it
		if (RSM.IsAnyRifle(w) && p.mo)
			RSM.FlickLoad(p.mo, h != 0);
		return true;
	}
}

// 2.0.5e: the House of the Dead gate's layers (RSQ_Flick.GateLayer gives it; it stays in the inventory). Gate is below
// every weapon layer, so it ticks first in the player's weapon tick; GateLate is above them, so it ticks last, before
// the engine's trigger check (RSQ_Flick.Gate). A CustomInventory: its states are overlay states, and its action runs
// on the player.
class RSQ_HotdGate : CustomInventory
{
	Default
	{
		Inventory.MaxAmount 1;
		+INVENTORY.UNDROPPABLE
		+INVENTORY.UNTOSSABLE
		+INVENTORY.QUIET
	}

	action void A_RSQHotdGate(bool late)
	{
		let pmo = PlayerPawn(self);
		let h = RSQ_Flick(EventHandler.Find('RSQ_Flick'));
		if (h && pmo && pmo.player)
			h.Gate(pmo, late);
	}

	States
	{
	Gate:
		TNT1 A 1 A_RSQHotdGate(false);
		Loop;
	GateLate:
		TNT1 A 1 A_RSQHotdGate(true);
		Loop;
	}
}

// 2.0.5e: the state a gun's layer holds while an off-screen press that loaded the launcher is still held (RSQ_Flick.Gate):
// the gun as it is, doing nothing and firing nothing (no A_WeaponReady: its ready flag stays clear). The gate puts the
// gun back in its own Ready when the trigger is let go. A weapon's state, so a weapon's layer may show it (as
// RSR_PartStates); never given.
class RSQ_HotdStates : Weapon
{
	Default
	{
		+WEAPON.CHEATNOTWEAPON
		+WEAPON.NO_AUTO_SWITCH
		+WEAPON.NOAUTOSWITCHTO
		+INVENTORY.UNDROPPABLE
		Weapon.SelectionOrder 32002;
	}

	States
	{
	Hold:
		"####" "#" -1;
		Stop;
	}
}
