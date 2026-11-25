// BD 2.0.6a: A ROW FOR A MOD THAT IS NOT LOADED IS NOT SHOWN (owner 2026-11-25: "why does it say rig pouch only when
// there is no tactical rig loaded?"). At the first UI tic, BD22 VR WEAPONS loses the rows whose mod is missing, looked
// up by a class of that mod by name: Rig Pouch Only (rsr_rig_pouch) needs RSQ Tactical Rig (RSQTR_RigService).
class RSQ_MenuTrim : StaticEventHandler
{
	ui bool done;
	override void UiTick()
	{
		if (done) return;
		done = true;
		static const Name CV[] = { 'rsr_rig_pouch' };
		static const String NEED[] = { "RSQTR_RigService" };
		let d = OptionMenuDescriptor(MenuDescriptor.GetDescriptor('RSQ_Options'));
		if (!d) return;
		for (int k = 0; k < CV.Size(); k++)
		{
			String n = NEED[k];
			class<Object> c = n;
			if (c) continue;
			for (int i = d.mItems.Size() - 1; i >= 0; i--)
			{
				Name a; int p;
				[a, p] = d.mItems[i].GetAction();
				if (a == CV[k]) d.mItems.Delete(i);
			}
		}
	}
}
