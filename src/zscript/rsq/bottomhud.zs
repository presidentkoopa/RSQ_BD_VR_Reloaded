// 2.0.5n THE VR ROW (owner 2026-11-24 17:38: "our RSQ GBOVR mod has some hud elements we want in bd22 weapons. the offhand
// ammo counter, the centered mugshot with health and armor to either side. i want that for our BD22 standalone, provided i
// can load gbovr after it without any issues").
//
// RSQ Gun Bonsai VR's bottom row (rsq/ui/skin_a_hud.zs DrawBottom, the owner's mockups), drawn by this pack on its own: an
// ammo counter per hand on that hand's side of the screen (reserve, magazine and the ammo icon; the off hand's magazine
// gold, the main hand's orange), and in the middle the face between health and armour. Its numbers, places and fonts are
// Gun Bonsai VR's, so the two look the same.
//
// IT IS A HUD TYPE: Brutal Doom's own HUD Type (bd_sbartype) gets a 6th value, "VR Row" (the default from 2.0.5n: a saved
// 1, ZDoom's, is moved to it once, rsq_hud_vrrow_ver). On 6 Brutal Doom's status bar draws nothing (it knows 1-4) and this
// row draws. WITH RSQ GUN BONSAI VR LOADED: its own row sets bd_sbartype to 5 while it draws (and puts back what was there
// when it stops, dispatch.zs Manage), so this row is off and only Gun Bonsai VR's draws: never two rows. Load order does
// not matter. Left-handed: as Gun Bonsai VR (RSQ Accessibility's Handedness, else QuestZDoom's Control Scheme).
// Code only, not run in the headset.
class RSQ_BottomHud : StaticEventHandler
{
	const ROW_TYPE = 6;
	ui double ox, oy, u, sw, sh;

	override void OnRegister()
	{
		let ver = CVar.FindCVar("rsq_hud_vrrow_ver");
		if (!ver || ver.GetInt() >= 1) return;
		let sb = CVar.FindCVar("bd_sbartype");
		if (sb && sb.GetInt() == 1) sb.SetInt(ROW_TYPE);
		ver.SetInt(1);
	}

	static clearscope bool LeftLayout()
	{
		CVar h = null;
		{ Name an = "RSQA_Menu"; class<Object> ac = an; if (ac) h = CVar.FindCVar("rsqa_handed"); }
		int v = h ? h.GetInt() : 0;
		if (v == 1) return false;
		if (v == 2) return true;
		let cs = CVar.FindCVar("vr_control_scheme");
		return cs && cs.GetInt() >= 10;
	}
	// a hand's counter on its own side: a right-hander's off hand left, a left-hander's main hand left
	static clearscope bool OnLeft(int hand) { return (hand == 1) != LeftLayout(); }

	override void RenderOverlay(RenderEvent e)
	{
		let sb = CVar.GetCVar("bd_sbartype", players[consoleplayer]);
		if (!sb || sb.GetInt() != ROW_TYPE) return;
		if (gamestate != GS_LEVEL || !playeringame[consoleplayer] || automapactive) return;
		let mo = players[consoleplayer].mo;
		if (!mo || mo.health <= 0) return;
		Frame();
		Font big = Font.GetFont("HUDFONT_DOOM");
		if (!big) big = BigFont;
		double wide = sw / u, H = sh / u;   // (not W: ZScript names ignore case, and w is the weapon)
		for (int s = 0; s <= 1; s++)
		{
			Weapon w = s == 1 ? players[consoleplayer].OffhandWeapon : players[consoleplayer].ReadyWeapon;
			if (!w) continue;
			int mag, res; TextureID icon;
			[mag, res, icon] = ReadAmmo(w);
			if (res < 0) continue;
			int mc = s == 1 ? Font.CR_GOLD : Font.CR_ORANGE;
			if (OnLeft(s))
			{
				double x = 39;
				double rw = Digits(big, 16, String.Format("%d", res), x, H - 78, Font.CR_GOLD, 0, 0.75);
				if (mag >= 0) Digits(big, 16, String.Format("%d", mag), x + rw + 6, H - 78, mc, 0);
				Picture(icon, x + rw / 2 - 13, H - 52, 26, 32);
			}
			else
			{
				double xr = wide - 39;
				double rw = Digits(big, 16, String.Format("%d", res), xr, H - 78, Font.CR_GOLD, 2, 0.75);
				if (mag >= 0) Digits(big, 16, String.Format("%d", mag), xr - rw - 6, H - 78, mc, 2);
				Picture(icon, xr - rw / 2 - 13, H - 52, 26, 32);
			}
		}
		double cx = wide / 2;
		TextureID face = StatusBar ? StatusBar.GetMugshot(5) : TexMan.CheckForTexture("STFST01", TexMan.Type_Any);
		Picture(face, cx - 17, H - 36, 34, 32);
		let nohp = CVar.GetCVar('rsq_hud_nohp', players[consoleplayer]);
		if (nohp && nohp.GetBool()) return;
		double hw = Digits(big, 24, String.Format("%d", mo.health), cx - 26, H - 33, Font.CR_UNTRANSLATED, 2);
		Picture(TexMan.CheckForTexture("MEDIA0", TexMan.Type_Any), cx - 26 - hw - 38, H - 34, 32, 29);
		let ba = BasicArmor(mo.FindInventory("BasicArmor"));
		if (ba && ba.Amount > 0)
		{
			TextureID arm = ba.Icon.IsValid() ? ba.Icon : TexMan.CheckForTexture("ARM1A0", TexMan.Type_Any);
			Picture(arm, cx + 26, H - 34, 34, 29);
			Digits(big, 24, String.Format("%d", ba.Amount), cx + 66, H - 33, Font.CR_UNTRANSLATED, 0);
		}
	}

	// Gun Bonsai VR's rule (data.zs ReadAmmo): with two pools the smaller one (by MaxAmount) is the magazine
	static ui int, int, TextureID ReadAmmo(Weapon w)
	{
		Inventory a1 = w.Ammo1, a2 = w.Ammo2;
		TextureID ic; ic.SetInvalid();
		if (a1 && a2 && a1 != a2)
		{
			Inventory m = a1.MaxAmount <= a2.MaxAmount ? a1 : a2;
			Inventory r = m == a1 ? a2 : a1;
			return m.Amount, r.Amount, r.Icon.IsValid() ? r.Icon : m.Icon;
		}
		if (a1) return -1, a1.Amount, a1.Icon;
		if (a2) return -1, a2.Amount, a2.Icon;
		return -1, -1, ic;
	}

	// Gun Bonsai VR's frame (draw.zs HudFrame): the screen less 4% each side, its units scaled x1.5 (its HUD Size default)
	ui void Frame()
	{
		double w = Screen.GetWidth(), h = Screen.GetHeight();
		double f = 0.04;
		ox = w * f; oy = h * f; sw = w * (1 - 2 * f); sh = h * (1 - 2 * f);
		u = min(sh / 540.0, sw / 660.0) * 1.5;
	}
	ui double Digits(Font f, double h, String s, double x, double y, int cr, int align, double alpha = 1.0)
	{
		double k = h / max(1, f.GetHeight()) * u;
		double w = f.StringWidth(s) * k / u;
		if (align == 2) x -= w; else if (align == 1) x -= w / 2;
		Screen.DrawText(f, cr, ox + x * u, oy + y * u, s, DTA_ScaleX, k, DTA_ScaleY, k, DTA_Alpha, alpha);
		return w;
	}
	// fitted in the box, its own shape kept, centred (draw.zs Picture)
	ui void Picture(TextureID tex, double x, double y, double w, double h)
	{
		if (!tex.IsValid()) return;
		Vector2 sz = TexMan.GetScaledSize(tex);
		if (sz.x <= 0 || sz.y <= 0) return;
		double k = min(w / sz.x, h / sz.y);
		double dw = sz.x * k, dh = sz.y * k;
		Screen.DrawTexture(tex, false, ox + (x + (w - dw) / 2) * u, oy + (y + (h - dh) / 2) * u,
			DTA_DestWidthF, dw * u, DTA_DestHeightF, dh * u, DTA_TopLeft, true);
	}
}
