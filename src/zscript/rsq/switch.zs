// 2.0.2a (owner 2026-10-28 19:47): "allow instant switching for all weapons, this raise / lower thing is
// rough on some". Option "Instant Weapon Switch" (rsq_instant_switch, default On).
//
// How: no weapon's code is skipped. When the engine starts putting a weapon away (DropWeapon), its
// Deselect frames, then the next weapon's Select frames, are run through in the SAME tic, each frame's
// action in order, exactly as if every frame's time had run out. It stops the moment the new weapon calls
// A_WeaponReady (WF_WEAPONREADY): it is ready to fire. The engine's own instant-switch flag
// (CF_INSTANTWEAPSWITCH) keeps the gun at the top, so A_Lower / A_Raise finish at once and the drawn gun
// never dips (in VR a lowered gun tilts down: hw_weapon.cpp pitch (y - WEAPONTOP) / -4).
// BOTH HANDS (2026-11-27, owner: "I had wanted instant-switch as a toggle option for BD weapons ... off hand can never
// instant switch?"). Until then this read only the main hand's flags against the one PendingWeapon both hands share, so
// an OFF-hand switch (RSQ Tactical Rig's off-hand draws, BD22 VR's own off-hand moves) made it drop the MAIN gun, step its
// Deselect up to 96 times and leave it at the bottom (tilted down in VR), while the off-hand gun skipped its Select. Now
// the switch is read per hand: a pending weapon flagged OFFHANDWEAPON is the off hand's, and that hand's own weapon,
// layer (PSP_OFFHANDWEAPON) and flags (WF_OFFHANDSWITCHOK / WF_OFFHANDREADY / WF_OFFHANDDISABLESWITCH) are used, as the
// engine's own per-hand switch does (player.zs DropWeapon(hand)). Off: BD22's own switch, as before.
class RSQ_Switch : EventHandler
{
	bool okPrev[MAXPLAYERS * 2];
	Weapon wPrev[MAXPLAYERS * 2];

	static Weapon HandWeapon(PlayerInfo p, int h) { return h ? p.OffhandWeapon : p.ReadyWeapon; }
	static int SwitchOk(int h) { return h ? WF_OFFHANDSWITCHOK : WF_WEAPONSWITCHOK; }
	static int Ready(int h) { return h ? WF_OFFHANDREADY : WF_WEAPONREADY; }
	static int NoSwitch(int h) { return h ? WF_OFFHANDDISABLESWITCH : WF_DISABLESWITCH; }
	static int Layer(int h) { return h ? PSP_OFFHANDWEAPON : PSP_WEAPON; }
	// the hand the one shared PendingWeapon is for (-1 none)
	static int PendingHand(PlayerInfo p)
	{
		if (p.PendingWeapon == WP_NOCHANGE || !p.PendingWeapon) return -1;
		return p.PendingWeapon.bOffhandWeapon ? 1 : 0;
	}

	override void WorldTick()
	{
		for (int n = 0; n < MAXPLAYERS; n++)
		{
			if (!playeringame[n])
				continue;
			let p = players[n];
			let mo = p.mo;
			if (!mo)
				continue;
			bool on = CVar.GetCVar('rsq_instant_switch', p).GetBool();
			if (on)
				p.cheats |= CF_INSTANTWEAPSWITCH;
			else
				p.cheats &= ~CF_INSTANTWEAPSWITCH;

			int ph = PendingHand(p);
			for (int h = 0; h < 2; h++)
			{
				int k = n * 2 + h;
				Weapon cur = HandWeapon(p, h);
				if (on && p.playerstate == PST_LIVE && mo.health > 0)
				{
					bool mine = ph == h;
					// the drop happened in this tic's player think: this hand allowed switching last tic, a weapon is
					// pending for THIS hand, and the hand's flag is gone now
					bool dropped = mine && okPrev[k] && cur && cur == wPrev[k] && !(p.WeaponState & SwitchOk(h));
					bool raised = cur && wPrev[k] && cur != wPrev[k];
					// or this hand is at a frame that allows switching and its weapon is pending: drop it now
					// (rig sw1: without this, half the switches ran the old weapon's lowering at full length)
					bool canDrop = mine && !dropped && !raised && cur && (p.WeaponState & SwitchOk(h)) && !(p.WeaponState & NoSwitch(h));
					if (canDrop)
					{
						mo.DropWeapon(h);
						dropped = true;
					}
					if (dropped || raised)
						Run(p, h, dropped);
				}
				okPrev[k] = (p.WeaponState & SwitchOk(h)) != 0;
				wPrev[k] = HandWeapon(p, h);
			}
			if (p.PendingWeapon != WP_NOCHANGE && CVar.GetCVar('rsq_switch_log', p).GetInt() > 1)
			{
				int lh = ph < 0 ? 0 : ph;
				let ps = p.GetPSprite(Layer(lh));
				Weapon hw = HandWeapon(p, lh);
				Console.Printf("RSQ switch t%d pending %s (%s hand) ready %s state %s tics %d ws %x", level.maptime,
					p.PendingWeapon ? p.PendingWeapon.GetClassName() : 'none', lh ? "off" : "main", hw ? hw.GetClassName() : 'none',
					(ps && ps.CurState && hw && hw.FindState('Ready')) ? ps.CurState.DistanceTo(hw.FindState('Ready')) .. "" : "-", ps ? ps.tics : -1, p.WeaponState);
			}
		}
	}

	static void Run(PlayerInfo p, int h, bool dropped)
	{
		Weapon from = HandWeapon(p, h);
		int steps = 0;
		p.WeaponState &= ~Ready(h);
		// the old weapon's Deselect frames, down to its A_Lower (which brings the new weapon up)
		if (dropped)
		{
			for (; steps < 96 && HandWeapon(p, h) == from; steps++)
			{
				let psp = p.GetPSprite(Layer(h));
				if (!psp || !psp.CurState)
					break;
				psp.y = WEAPONBOTTOM;	// any A_Lower here finishes now
				psp.SetState(psp.CurState.NextState);
			}
			if (HandWeapon(p, h) == from)
			{
				// (2026-11-27: the layer is put back at the top, so a weapon that never lowered is not left low)
				let back = p.GetPSprite(Layer(h));
				if (back) { back.y = WEAPONTOP; back.oldy = WEAPONTOP; }
				Log(p, h, from, null, steps, "the old weapon never lowered; left to the engine");
				return;
			}
		}
		// the new weapon's Select frames, up to its first ready call
		Weapon to = HandWeapon(p, h);
		int up = 0;
		// (2026-11-27: also stops on reaching the weapon's Ready state: a weapon whose Ready never sets this hand's ready flag
		// -- BD22 VR's off-hand empty hands, RSQ_Hands -- ran its Ready loop's actions up to 96 times in one tic)
		State rdy = to ? to.GetReadyState() : null;
		for (; up < 96 && HandWeapon(p, h) == to && !(p.WeaponState & Ready(h)); up++)
		{
			let psp = p.GetPSprite(Layer(h));
			if (!psp || !psp.CurState || (rdy && psp.CurState == rdy))
				break;
			psp.y = WEAPONTOP;
			psp.SetState(psp.CurState.NextState);
		}
		let psp = p.GetPSprite(Layer(h));
		if (psp)
		{
			psp.y = WEAPONTOP;
			psp.oldy = WEAPONTOP;
		}
		Log(p, h, from, to, steps, String.Format("ready after %d select frames%s", up,
			(p.WeaponState & Ready(h)) ? "" : " (not ready yet: left to the engine)"));
	}

	static void Log(PlayerInfo p, int h, Weapon from, Weapon to, int steps, String what)
	{
		if (CVar.FindCVar('rsq_switch_log') && CVar.FindCVar('rsq_switch_log').GetInt())
			Console.Printf("RSQ switch t%d (%s hand): %s -> %s: %d deselect frames, %s", level.maptime, h ? "off" : "main",
				from ? from.GetClassName() : 'none', to ? to.GetClassName() : 'none', steps, what);
	}
}
