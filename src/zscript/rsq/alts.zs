// 1.37 (owner): secondary fire on BD22's dead (zoom) buttons. Always (1.39): SMG full-auto / 3-round
// burst toggle. Behind their own options, default off (BD22 as it was): revolver slug shot, pump shotgun slug shot. The guns' states (Rifle-style RSA_ states in the .dec files) read
// the tokens below; this hands the options to them. Server options: they change what is fired.
class RSA_Opt_SMG : RSVR_Token {}
class RSA_Opt_Rev : RSVR_Token {}
class RSA_Opt_Slug : RSVR_Token {}
class RSA_Opt_Semi : RSVR_Token {}		// 1.41: the pistol is semi auto
class RSA_BurstSMG : RSVR_Token {}		// the SMG is on burst
class RSA_BurstCnt : RSVR_Token { Default { Inventory.MaxAmount 9; } }		// rounds of this burst, main hand
class RSA_BurstCntOff : RSVR_Token { Default { Inventory.MaxAmount 9; } }	// ...off hand
class RSA_Magnum : RSVR_Token {}		// the next revolver shot is a slug, main hand
class RSA_MagnumOff : RSVR_Token {}		// ...off hand
class RSA_Slug : RSVR_Token {}			// the next shotgun shot is a slug, main hand
class RSA_SlugOff : RSVR_Token {}
class RSA_Opt_RLLock : RSVR_Token {}	// 2.0.2a: the rocket launcher's lock-on alt fire is on
class RSA_Opt_ASlug : RSVR_Token {}	// 2.0.2a: the assault shotgun's slug alt fire is on
class RSA_ASlug : RSVR_Token {}		// the next assault shotgun shot is a slug, main hand
class RSA_ASlugOff : RSVR_Token {}	// ...off hand		// ...off hand

class RSA_Handler : EventHandler
{
	// LD mode's stand-down tokens, by name at run time (they are defined in a later ZScript lump, zscript/rsld)
	static bool AltDown(Actor mo)
	{
		if (!mo)
			return false;
		string a = "RSLD_AltDown", b = "RSLD_AltDownOff";
		class<Inventory> ca = a, cb = b;
		return (ca && mo.CountInv(ca) > 0) || (cb && mo.CountInv(cb) > 0);
	}

	override void WorldTick()
	{
		static const Name cv[] = { 'rsa_rev_slug', 'rsa_sg_slug', 'rsa_pistol_semi', 'rsa_asg_slug', 'rsa_rl_lock' };
		static const Name tok[] = { 'RSA_Opt_Rev', 'RSA_Opt_Slug', 'RSA_Opt_Semi', 'RSA_Opt_ASlug', 'RSA_Opt_RLLock' };
		// F11: every gun fires at BD22's own rate (semiauto.zs RSQ_TriggerHeld)
		for (int n = 0; n < MAXPLAYERS; n++)
			if (playeringame[n] && players[n].mo && players[n].mo.CountInv('RSQ_TriggerHeld') <= 0)
				players[n].mo.GiveInventory('RSQ_TriggerHeld', 1);
		for (int k = 0; k < cv.Size(); k++)
		{
			let c = CVar.FindCVar(cv[k]);
			bool on = c && c.GetBool();
			for (int n = 0; n < MAXPLAYERS; n++)
			{
				if (!playeringame[n] || !players[n].mo)
					continue;
				let mo = players[n].mo;
				bool give = on;
				// LD mode (round 3, owner Q12): the lock-on (k 4) and the slug alt (k 1) stand down while the gun carries
				// the legendary power that uses them (zscript/rsld/g6_ammo.zs gives RSLD_AltDown / RSLD_AltDownOff)
				if (give && (k == 1 || k == 4) && AltDown(mo))
					give = false;
				if (give && mo.CountInv(tok[k]) <= 0)
					mo.GiveInventory(tok[k], 1);
				else if (!give && mo.CountInv(tok[k]) > 0)
					mo.TakeInventory(tok[k], 1);
			}
		}
	}
}
