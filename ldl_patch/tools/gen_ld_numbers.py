"""Generate the LD mode's LegenDoom numbers tables from LegenDoom 3.0 itself (never typed by hand).

  python3 -I ldl_patch/tools/gen_ld_numbers.py        (from anywhere)

Reads every rules file ldl_patch/tools/numbers/<name>.rules and writes src/zscript/rsld/numbers_<name>.zs
(class RSLD_Numbers_<name> : RSLD_NumberTable). Each row: "effect|key|value|<file>:<line>|<the source text>".
LegenDoom is read from $LD_PK3 (default /mnt/user-data/uploads/1f3eb79e-LegenDoom_3.0.pk3), unzipped in memory.

Rule lines (whitespace separated, '#' comments):
  <effect> <key> <file> <label> <call>[#n] <argindex>      the n-th <call> (default 1st) inside the state block
                                                           <label> (an 'Actor/Label' form scopes the label to
                                                           that actor), its argument <argindex> (0-based)
  <effect> <key> <file> <label> tics                       the sum of the state durations in that block
                                                           (frames x tics, e.g. 'CSHT AAAA 1' = 4)
  <effect> <key> <file> re "<regex>" [n]                   group 1 of the n-th match (default 1st) in the file
  <effect> <key> <file> prop <Actor> <Property>            the actor's property (e.g. Inventory.MaxAmount)
Every rule must resolve; the tool stops with the rule's line number if one does not.
"""
import os, re, sys, zipfile, shlex

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LD = os.environ.get('LD_PK3', '/mnt/user-data/uploads/1f3eb79e-LegenDoom_3.0.pk3')
OUTDIR = os.path.join(REPO, 'src', 'zscript', 'rsld')

z = zipfile.ZipFile(LD)
names = {n.lower(): n for n in z.namelist()}
cache = {}

def lines(f):
    if f not in cache:
        n = names.get(f.lower())
        if not n:
            raise SystemExit('no file %s in %s' % (f, LD))
        cache[f] = z.read(n).decode('latin-1').split('\n')
    return cache[f]

LABEL = re.compile(r'^\s*([A-Za-z_][\w.]*)\s*:\s*(//.*)?$')
ACTOR = re.compile(r'^\s*actor\s+(\w+)', re.I)

def block(f, label):
    """(start line index, [line indexes]) of the state block that starts at label (until the next label/actor)."""
    L = lines(f)
    actor = None
    if '/' in label:
        actor, label = label.split('/', 1)
    in_actor = actor is None
    for i, t in enumerate(L):
        m = ACTOR.match(t)
        if m:
            in_actor = actor is None or m.group(1).lower() == actor.lower()
            continue
        m = LABEL.match(t)
        if in_actor and m and m.group(1).lower() == label.lower():
            out = []
            for j in range(i + 1, len(L)):
                if LABEL.match(L[j]) or ACTOR.match(L[j]) or L[j].strip() == '}':
                    if out and (LABEL.match(L[j]) or ACTOR.match(L[j]) or L[j].strip() == '}'):
                        break
                    if not out and LABEL.match(L[j]):
                        continue	# stacked labels ("FireSerious:\n  FireSerious:")
                out.append(j)
            return i, out
    raise KeyError('label %s not found in %s' % (label, f))

def split_args(s):
    depth, cur, out = 0, '', []
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    out.append(cur.strip())
    return out

def call_args(text, call):
    m = re.search(r'\b' + re.escape(call) + r'\s*\(', text, re.I)
    if not m:
        return None
    i = m.end(); depth = 1; j = i
    while j < len(text) and depth:
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
        j += 1
    return split_args(text[i:j - 1])

def number(s):
    s = s.strip().strip('"')
    m = re.match(r'^-?\d+(\.\d+)?$', s)
    if not m:
        raise ValueError('not a plain number: %r' % s)
    return s

def resolve(rule):
    eff, key, f = rule[0], rule[1], rule[2]
    L = lines(f)
    if rule[3] == 're':	# over the whole file (so (?s) patterns can span lines); the line is where group 1 is
        rx = re.compile(rule[4], re.I | re.M)
        nth = int(rule[5]) if len(rule) > 5 else 1
        text = '\n'.join(L)
        for k, m in enumerate(rx.finditer(text), 1):
            if k == nth:
                ln = text.count('\n', 0, m.start(1))
                return number(m.group(1)), ln + 1, L[ln].strip()
        raise KeyError('regex %s: match %d not found in %s' % (rule[4], nth, f))
    if rule[3] == 'prop':	# <file> prop <Actor> <Property>: the actor's property value
        actor, prop = rule[4], rule[5]
        inside = False
        for i, t in enumerate(L):
            m = ACTOR.match(t)
            if m:
                inside = m.group(1).lower() == actor.lower()
                continue
            if inside:
                m = re.match(r'^\s*' + re.escape(prop) + r'\s+"?(-?[\d.]+)', t, re.I)
                if m:
                    return number(m.group(1)), i + 1, t.strip()
        raise KeyError('property %s of %s not found in %s' % (prop, actor, f))
    label, what = rule[3], rule[4]
    start, idx = block(f, label)
    if what == 'tics':
        tot = 0
        for i in idx:
            t = L[i].split('//')[0].strip()
            m = re.match(r'^("####"|\w{4})\s+("#+"|"?[A-Z\[\]\\#]+"?)\s+(-?\d+)', t)
            if m:
                frames = m.group(2).strip('"')
                tot += len(frames) * int(m.group(3))
        return str(tot), start + 1, '%s: %d state lines' % (label, len(idx))
    call, nth = (what.split('#') + ['1'])[:2]
    nth = int(nth); argi = int(rule[5])
    k = 0
    for i in idx:
        t = L[i].split('//')[0]
        a = call_args(t, call)
        if a is None:
            continue
        k += 1
        if k == nth:
            return number(a[argi]), i + 1, t.strip()
    raise KeyError('%s#%d not found in %s %s' % (call, nth, f, label))

def main():
    rdir = os.path.join(HERE, 'numbers')
    total = 0
    errors = []
    for fn in sorted(os.listdir(rdir)):
        if not fn.endswith('.rules'):
            continue
        group = fn[:-6]
        rows = []
        for ln, raw in enumerate(open(os.path.join(rdir, fn)), 1):
            raw = re.split(r'\s#\s', raw)[0]	# a trailing comment is ' # ...' (A_FireBullets#2 is not one)
            t = raw.strip()
            if not t or t.startswith('#'):
                continue
            rule = shlex.split(t, comments=False)
            try:
                v, line, src = resolve(rule)
            except Exception as e:
                errors.append('%s:%d: %s (%s)' % (fn, ln, e, t))
                continue
            src = src.replace('\\', '\\\\').replace('"', "'").replace('\t', ' ')
            rows.append('%s|%s|%s|%s:%d|%s' % (rule[0], rule[1], v, rule[2], line, src))
        cls = 'RSLD_Numbers_' + re.sub(r'\W', '_', group)
        out = ['// GENERATED by ldl_patch/tools/gen_ld_numbers.py from ldl_patch/tools/numbers/%s -- do not edit.' % fn,
               '// LegenDoom 3.0 numbers, each with the file:line it was read from.', '',
               'class %s : RSLD_NumberTable' % cls, '{', '\tstatic const string Rows[] =', '\t{']
        out.append(',\n'.join('\t\t"%s"' % r for r in rows))
        out += ['\t};', '\toverride int Count() { return Rows.Size(); }', '\toverride string Row(int i) { return Rows[i]; }', '}', '']
        p = os.path.join(OUTDIR, 'numbers_%s.zs' % group)
        open(p, 'w').write('\n'.join(out))
        print('%s: %d numbers -> %s' % (fn, len(rows), os.path.relpath(p, REPO)))
        total += len(rows)
    print('total', total)
    for e in errors:
        print('ERROR', e)
    if errors:
        sys.exit(1)

main()
