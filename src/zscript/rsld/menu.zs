// LD mode: Brutal Doom's interface stays when LegenDoom 3.0 is loaded (owner 11-06 07:31 / 07:39: "I want the TITLEMAP
// to be vanilla Doom or BD's, and the interface to be vanilla Doom or BD's", "with a button for LD Options").
// LegenDoom's MENUDEF (loaded after BD22 VR) replaces ListMenu "MainMenu" (its LDM_* art) and the whole OptionMenu
// "OptionsMenu" (QuestZDoom's VR Options, Quick Menu, Info, and BD22 VR's "BD22 VR Weapons" row are gone with it).
// LegenDoom is not edited: at the first UI tic, only when LegenDoom is loaded, the two descriptors get the items of
// MENUDEF.rsld's copies (Brutal Doom v22's main menu + a "LegenDoom Options" button; QuestZDoom 17.3's options menu +
// BD22 VR's row + "LegenDoom Options" + "LegenDoom x BD22 VR"). Rows a later mod added to LegenDoom's options menu
// (Champions...) are kept at the end. Without LegenDoom nothing here runs.

class RSLD_Interface : StaticEventHandler
{
	ui bool done;

	// LegenDoom 3.0's own OptionsMenu rows (its MENUDEF): anything else in it was added by a mod loaded after it
	static const Name LDOwn[] = { 'LegenDoom', 'CustomizeControls', 'MouseOptions', 'JoystickOptions', 'PlayerMenu',
		'GameplayOptions', 'CompatibilityOptions', 'AutomapOptions', 'HUDOptions', 'MiscOptions', 'NetworkOptions',
		'SoundOptions', 'VideoOptions', 'VideoModeMenu', 'reset2defaults', 'reset2saved', 'menuconsole', 'None' };

	override void UiTick()
	{
		if (done) return;
		done = true;
		if (!RSLD.On()) return;
		int a = MainMenu(), b = Options(), c = Brutal();
		if (RSLD.Debug()) Console.Printf("RSLD interface: main menu %s, options menu %s (%d rows kept from later mods), Brutal menu row %s",
			a ? "BD22's" : "unchanged", b >= 0 ? "QuestZDoom's" : "unchanged", max(b, 0), c ? "added" : "not added");
	}

	ui static bool MainMenu()
	{
		let src = ListMenuDescriptor(MenuDescriptor.GetDescriptor('RSLD_BDMainMenu'));
		let dst = ListMenuDescriptor(MenuDescriptor.GetDescriptor('MainMenu'));
		if (!src || !dst) return false;
		dst.mItems.Copy(src.mItems);
		dst.mSelectedItem = src.mSelectedItem;
		dst.mSelectOfsX = src.mSelectOfsX; dst.mSelectOfsY = src.mSelectOfsY;
		dst.mSelector = src.mSelector;
		dst.mDisplayTop = src.mDisplayTop;
		dst.mXpos = src.mXpos; dst.mYpos = src.mYpos;
		dst.mWLeft = src.mWLeft; dst.mWRight = src.mWRight;
		dst.mLinespacing = src.mLinespacing;
		dst.mFont = src.mFont; dst.mFontColor = src.mFontColor; dst.mFontColor2 = src.mFontColor2;
		dst.mCenter = src.mCenter; dst.mCenterText = src.mCenterText;
		dst.mAnimatedTransition = src.mAnimatedTransition; dst.mAnimated = src.mAnimated;
		dst.mDontBlur = src.mDontBlur; dst.mDontDim = src.mDontDim;
		dst.mVirtWidth = src.mVirtWidth; dst.mVirtHeight = src.mVirtHeight;
		return true;
	}

	ui static bool HasAction(OptionMenuDescriptor d, Name a)
	{
		for (int i = 0; i < d.mItems.Size(); i++) { Name n; int p; [n, p] = d.mItems[i].GetAction(); if (n == a) return true; }
		return false;
	}

	ui static int Options()
	{
		let src = OptionMenuDescriptor(MenuDescriptor.GetDescriptor('RSLD_OptionsMenuBD'));
		let dst = OptionMenuDescriptor(MenuDescriptor.GetDescriptor('OptionsMenu'));
		if (!src || !dst) return -1;
		Array<OptionMenuItem> extra;
		for (int i = 0; i < dst.mItems.Size(); i++)
		{
			Name n; int p;
			[n, p] = dst.mItems[i].GetAction();
			bool own = false;
			for (int k = 0; k < RSLD_Interface.LDOwn.Size(); k++) if (RSLD_Interface.LDOwn[k] == n) own = true;
			if (!own && !HasAction(src, n)) extra.Push(dst.mItems[i]);
		}
		dst.mItems.Copy(src.mItems);
		dst.mTitle = src.mTitle;
		for (int i = 0; i < extra.Size(); i++) dst.mItems.Push(extra[i]);
		return extra.Size();
	}

	// the LD mode's page also under Brutal Doom's own options (BrutalMenu), as the patch had it
	ui static bool Brutal()
	{
		let d = OptionMenuDescriptor(MenuDescriptor.GetDescriptor('BrutalMenu'));
		if (!d || HasAction(d, 'RSLD_Options')) return false;
		d.mItems.Push(new("OptionMenuItemStaticText").Init(" "));
		d.mItems.Push(new("OptionMenuItemSubmenu").Init("LegenDoom x BD22 VR", 'RSLD_Options'));
		d.mItems.Push(new("OptionMenuItemSubmenu").Init("LegenDoom Options", 'LegenDoom'));
		return true;
	}
}
