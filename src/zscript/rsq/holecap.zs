// BD 2.0.5y: A CAP ON BULLET HOLES (owner 2026-11-25: "the angrier benellus fight choked my pc to a crawl").
// BD22's puffs leave a hole on the floor and the ceiling (FlatDecals.dec DetectFloorBullet / DetectCeilBullet) that lasts
// 2000 tics (57 s). A monster that sprays hundreds of bullets a volley (Benellus, Angrier) piled up 1,700 of them in two
// minutes on the rig. The newest HOLE_MAX stay; past that the oldest goes. Normal play never reaches it.
class RSQ_HoleCap : EventHandler
{
	const HOLE_MAX = 192;
	Array<Actor> holes;
	int head;

	override void WorldThingSpawned(WorldEvent e)
	{
		let a = e.thing;
		if (!a) return;
		Name n = a.GetClassName();
		if (n != 'DetectCeilBullet' && n != 'DetectFloorBullet') return;
		if (holes.Size() < HOLE_MAX) { holes.Push(a); return; }
		let old = holes[head];
		if (old) old.Destroy();
		holes[head] = a;
		head = (head + 1) % HOLE_MAX;
	}
}
