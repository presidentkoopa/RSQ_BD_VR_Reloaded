"""Parse LegenDoom 3.0's DECORATE (following #include from the root lump, as the engine does) and list:
  - every `replaces X` LegenDoom makes            -> parsed/ld_replaces.txt   (replacee replacement)
  - every per-slot effect token class it defines  -> parsed/ld_tokens.txt     (slot effect)
  - which effects each slot's RandomLegendary can roll, per rarity -> parsed/ld_rolls.txt (slot rarity effect)
Usage: python3 -I parse_ld.py <LegenDoom_3.0.pk3> <outdir>
Never ships; the patch's generated tables (src/zscript/rsldp/tables.zs) are built from these files by gen_tables.py.
"""
import re, sys, zipfile, os

pk3, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
z = zipfile.ZipFile(pk3)
names = {n.lower(): n for n in z.namelist()}

def read(name):
    return z.read(names[name.lower()]).decode('latin-1')

def strip_comments(t):
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return re.sub(r'//[^\n]*', '', t)

seen, order = set(), []
def walk(name):
    if name.lower() in seen:
        return
    seen.add(name.lower())
    txt = strip_comments(read(name))
    for line in txt.split('\n'):
        m = re.match(r'\s*#include\s+"([^"]+)"', line, re.I)
        if m:
            walk(m.group(1))
    order.append((name, txt))

walk('DECORATE')
SLOTS = ['Fists', 'Chainsaw', 'Pistol', 'Shotgun', 'SuperShotgun', 'Chaingun', 'RocketLauncher', 'PlasmaRifle', 'BFG9000']
rep, tokens, rolls = [], [], []
hdr = re.compile(r'^\s*actor\s+(\w+)\s*(?::\s*(\w+))?\s*(?:replaces\s+(\w+))?', re.I | re.M)
for name, txt in order:
    for m in hdr.finditer(txt):
        cls, parent, replacee = m.group(1), m.group(2), m.group(3)
        if replacee:
            rep.append((replacee, cls, name))
        t = re.match(r'LD(%s)Effect_(\w+)$' % '|'.join(SLOTS), cls)
        if t:
            tokens.append((t.group(1), t.group(2)))
    # RandomLegendary rolls: walk each LD<slot>RandomLegendary actor's states in order, tracking the rarity section
    for m in re.finditer(r'actor\s+LD(%s)RandomLegendary\b.*?\n\}' % '|'.join(SLOTS), txt, re.I | re.S):
        slot, body = m.group(1), m.group(0)
        rarity = None
        for line in body.split('\n'):
            s = re.match(r'\s*(Common|Uncommon|Rare|Epic)Effects\s*:', line)
            if s:
                rarity = s.group(1)
            g = re.search(r'A_GiveInventory\s*\(\s*"LD%sEffect_(\w+)"' % slot, line)
            if g and rarity:
                rolls.append((slot, rarity, g.group(1)))
# last definition of a replacee wins (DECORATE order), as in the engine
final = {}
for replacee, cls, src in rep:
    final[replacee.lower()] = (replacee, cls, src)
with open(os.path.join(out, 'ld_replaces.txt'), 'w') as f:
    for k in sorted(final):
        r, c, s = final[k]
        f.write('%s %s %s\n' % (r, c, s))
with open(os.path.join(out, 'ld_tokens.txt'), 'w') as f:
    for s, e in tokens:
        f.write('%s %s\n' % (s, e))
with open(os.path.join(out, 'ld_rolls.txt'), 'w') as f:
    for s, r, e in sorted(set(rolls)):
        f.write('%s %s %s\n' % (s, r, e))
print('lumps parsed: %d, replaces: %d (unique replacees %d), effect tokens: %d, rolls: %d' %
      (len(order), len(rep), len(final), len(tokens), len(set(rolls))))
