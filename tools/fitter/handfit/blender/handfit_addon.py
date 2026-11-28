"""Handfit: fit the FBX hand to a gun in Blender, export what the pack reads. (RS_ModelSwapper, 2026-11-08; step 1)

STATUS: written, not verified -- this file was authored where Blender cannot run. The first run is the acceptance test
(test_brutalpistol.py), on the owner's machine.

What it does (sidebar panel "Handfit" in the 3D view, or the functions below from a script):
  Load card     a cards/<set>/<gun>/ folder: the labelled MD3 at its idle frame as a mesh, the card's grip line,
                trigger, support feature, muzzle and magazine well as empties. Placed in the CONTROLLER frame
                (F = +X, L = +Y, U = +Z, centimetres) by the gun's MODELDEF numbers (Scale, Offset, ZOffset,
                AngleOffset, PitchOffset, RollOffset) through the same chain QZD 17.3 draws with
                (models.cpp RenderHUDModel; tools/handfit/core/hands_tool/gunplace.py). Blender's scene IS the
                controller frame, so 1 Blender unit = 1 cm in the player's hand.
  Import hand   hand_final.fbx (both rigs). The take's animation is dropped: poses come from the library.
  Apply pose    a pose_library.json entry (29 BD22 2.0.1 holds, the FBX take's 5 poses, each side) onto the rig: every
                joint's frame relative to HANDPALM_joint, mapped to Blender's bones through one conversion solved from
                the rest pose (no axis convention typed). Seats the hand where that hold put it (hand_place), or on
                the controller grip for a seed pose.
  Export        the posed hand as an MD3 frame in hook-0 / rot-0 convention (the frame IS where the hand is drawn,
                as BD22 2.0.1's fbx_b1_R.md3), a MODELDEF snippet (the gun's six numbers read back from where the gun
                object is -- move the GUN to the hand, the one method -- and the hand FrameIndex lines), a
                <Class>.handfit.json record (pose joints, placement, report), and a one-line report.
Not in step 1: finger snapping (IK to the trigger face, shrinkwrap to the grip), the support hand workflow, textures.
"""
bl_info = {"name": "Handfit (RS_ModelSwapper)", "author": "presidentkoopa", "version": (0, 1, 0), "blender": (4, 0, 0),
           "location": "3D View > Sidebar > Handfit", "category": "Rigging"}

import os, re, json, math, struct, itertools
try:
    import bpy, bmesh
    from mathutils import Matrix, Vector, Euler
    from mathutils.kdtree import KDTree
    IN_BLENDER = True
except ImportError:  # imported outside Blender (tests of the pure parts)
    IN_BLENDER = False

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DEFAULT_LIB = os.path.join(HERE, 'pose_library.json')
DEFAULT_FBX = os.path.join(REPO, 'tools', 'handfit', 'core', 'fbx_hand', 'hand_final.fbx')
WS = 1.02                                   # vr_weaponScale the kit measured everything with
HAND_PL = dict(scale=(-1.0, 1.0, 1.0), off=(0.0, -24.0, -10.0))   # RSQ_GunSide: 1.92's hand placement (hook.PL)
K_OFF = (0.0, 5.0, 30.0)                    # RenderHUDModel's fixed offset (hudrender.to_local)
JOINTS_SKIP = ()


# ----------------------------------------------------------------------------------------------- pure math (no bpy)
def rot_x(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return [[1, 0, 0], [0, c, -s], [0, s, c]]
def rot_y(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
def rot_z(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]
def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(a, v):
    return [sum(a[i][k] * v[k] for k in range(3)) for i in range(3)]
def tr(a):
    return [[a[j][i] for j in range(3)] for i in range(3)]
SWAP_YZ = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]                 # md3 (x,y,z) -> GL (x,z,y)
P_FLU = [[0, 0, -1], [-1, 0, 0], [0, 1, 0]]                 # GL local (x right, y up, z back) -> (F, L, U)


def gun_chain(scale, off, zoff, ang=0.0, pit=0.0, rol=0.0, ws=WS):
    """The 3x3 + translation that takes a gun MD3 vertex (model units) to the controller frame in cm (F, L, U):
    gunplace.to_local_ao followed by gunview.to_fl. scale = MODELDEF Scale (xs, ys, zs), off = Offset (xo, yo),
    zoff = ZOffset; AngleOffset / PitchOffset / RollOffset in degrees."""
    xs, ys, zs = scale; xo, yo = off; zo = zoff
    A = mm(mm(rot_y(-ang), rot_z(pit)), rot_x(-rol))
    L = mm(rot_y(90), mm(A, [[ws * SWAP_YZ[i][j] for j in range(3)] for i in range(3)]))
    D = [[xs, 0, 0], [0, zs, 0], [0, 0, ys]]
    L = mm(D, L)
    t = [xo + K_OFF[0], zo + K_OFF[1], yo + K_OFF[2]]
    L = mm(P_FLU, L); t = mv(P_FLU, t)
    return L, t


def gun_numbers_from_world(Lw, tw, scale, ws=WS):
    """Inverse of gun_chain for a KNOWN Scale: the world linear part + translation of the gun object (FLU cm) ->
    (Offset x, Offset y, ZOffset, AngleOffset, PitchOffset, RollOffset). Exact when the object was only moved."""
    xs, ys, zs = scale
    Dinv = [[1 / xs, 0, 0], [0, 1 / zs, 0], [0, 0, 1 / ys]]
    A = mm(mm(mm(tr(rot_y(90)), Dinv), mm(tr(P_FLU), Lw)), [[SWAP_YZ[i][j] / ws for j in range(3)] for i in range(3)])
    # A = Ry(-ang) Rz(pit) Rx(-rol): extrinsic X, Z, Y
    e = Matrix([A[0], A[1], A[2]]).to_euler('XZY')
    ang, pit, rol = -math.degrees(e.y), math.degrees(e.z), -math.degrees(e.x)
    o = mv(tr(P_FLU), tw)
    xo, zo, yo = o[0] - K_OFF[0], o[1] - K_OFF[1], o[2] - K_OFF[2]
    return dict(Offset=[round(xo, 3), round(yo, 3)], ZOffset=round(zo, 3), AngleOffset=round(ang, 3), PitchOffset=round(pit, 3), RollOffset=round(rol, 3))


def flu_to_md3(X):
    """hook.flu_to_md3: controller-frame cm -> md3 vertex units for a hand drawn with HAND_PL (hook 0, rot 0)."""
    S = [-1.0, 1.0, 1.0]
    OFF = [HAND_PL['off'][0] + K_OFF[0], HAND_PL['off'][2] + K_OFF[1], HAND_PL['off'][1] + K_OFF[2]]  # (xo, zo, yo) + k
    out = []
    for x in X:
        loc = mv(tr(P_FLU), [x[0] / 100.0, x[1] / 100.0, x[2] / 100.0])
        p = [loc[i] * 100.0 - OFF[i] for i in range(3)]
        p = [p[i] * S[i] for i in range(3)]
        r = [-p[2] / WS, p[1] / WS, p[0] / WS]
        out.append([r[0], r[2], r[1]])
    return out


def parse_card(path):
    """The lines the add-on draws: grip line, trigger, support feature, muzzle, mag_well, model name, idle frame."""
    c = dict(points={})
    for line in open(path, encoding='utf-8', errors='replace'):
        body = line.split('#', 1)[0].rstrip(); s = body.strip()
        if not s: continue
        if s.startswith('model '):
            c['model'] = s.split()[1]; m = re.search(r'idle_frame\s+(\d+)', s); c['idle'] = int(m.group(1)) if m else 0
        elif s.startswith('weapon '): c['weapon'] = s.split()[1]
        elif s.startswith('archetype '): c['archetype'] = s.split()[1]
        elif s.startswith('grip '):
            v = re.findall(r'\[([^\]]*)\]', s)
            if len(v) >= 2: c['points']['grip_top'] = [float(x) for x in v[0].split(',')]; c['points']['grip_bottom'] = [float(x) for x in v[1].split(',')]
            if len(v) >= 3: c['points']['trigger'] = [float(x) for x in v[2].split(',')]
        elif s.startswith('support '):
            v = re.findall(r'\[([^\]]*)\]', s)
            if v: c['points']['support'] = [float(x) for x in v[0].split(',')]
        elif s.startswith('muzzle '):
            v = re.findall(r'\[([^\]]*)\]', s)
            if v: c['points']['muzzle'] = [float(x) for x in v[0].split(',')]
        elif s.startswith('mag_well '):
            v = re.findall(r'\[([^\]]*)\]', s)
            if v: c['points']['mag_well'] = [float(x) for x in v[0].split(',')]
            if len(v) > 1: c['points']['mag_mouth'] = [float(x) for x in v[1].split(',')]
    return c


def read_md3(path):
    """surfaces of an MD3: name, tris, st, xyz per frame (model units), skins"""
    d = open(path, 'rb').read()
    ident, ver, name, flags, nframes, ntags, nsurf, nskins, ofs_frames, ofs_tags, ofs_surf, ofs_eof = struct.unpack_from('<4si64s9i', d, 0)
    surfs = []; o = ofs_surf
    for _ in range(nsurf):
        sid, sname, sflags, snf, nsh, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end = struct.unpack_from('<4s64s10i', d, o)
        tris = list(struct.unpack_from('<%di' % (nt * 3), d, o + o_tri)); tris = [tris[i:i + 3] for i in range(0, len(tris), 3)]
        st = list(struct.unpack_from('<%df' % (nv * 2), d, o + o_st)); st = [st[i:i + 2] for i in range(0, len(st), 2)]
        xyz = []
        for f in range(snf):
            raw = struct.unpack_from('<%dh' % (nv * 4), d, o + o_xyz + f * nv * 8)
            xyz.append([[raw[4 * i] / 64.0, raw[4 * i + 1] / 64.0, raw[4 * i + 2] / 64.0] for i in range(nv)])
        skins = [struct.unpack_from('<64s', d, o + o_sh + 68 * k)[0].split(b'\0')[0].decode(errors='replace') for k in range(nsh)]
        surfs.append(dict(name=sname.split(b'\0')[0].decode(errors='replace'), tris=tris, st=st, xyz=xyz, skins=skins))
        o += o_end
    return dict(name=name.split(b'\0')[0].decode(errors='replace'), nframes=nframes, surfs=surfs)


def enc_normal(n):
    l = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) + 1e-12; n = [n[0] / l, n[1] / l, n[2] / l]
    lat = int(round(math.degrees(math.acos(max(-1, min(1, n[2])))) * 255 / 360)) & 255
    lng = int(round(math.degrees(math.atan2(n[1], n[0])) * 255 / 360)) & 255
    return (lat << 8) | lng


def write_md3(path, frames, tris, uv, skin, surf_name='hand', frame_names=None, model_name='rsq_fbxhand'):
    """md3write.write: one surface, N vertex frames. frames: list of [nv][3] (md3 units); uv: [nv][2] (t already flipped)."""
    nf = len(frames); nv = len(frames[0]); nt = len(tris)
    assert nv <= 4096 and nt <= 8192, (nv, nt)
    for X in frames:
        assert max(abs(c) for v in X for c in v) * 64 < 32767, 'vertex out of md3 range'
    tri_b = b''.join(struct.pack('<3i', *t) for t in tris); st_b = b''.join(struct.pack('<2f', *s) for s in uv)
    sh_b = struct.pack('<64si', skin.encode()[:63], 0)
    xyzn = b''
    for X in frames:
        N = [[0.0, 0.0, 0.0] for _ in range(nv)]
        for a, b, c in tris:
            u = [X[b][i] - X[a][i] for i in range(3)]; w = [X[c][i] - X[a][i] for i in range(3)]
            fn = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
            for k in (a, b, c):
                for i in range(3): N[k][i] += fn[i]
        for v, n in zip(X, N):
            xyzn += struct.pack('<4h', int(round(v[0] * 64)), int(round(v[1] * 64)), int(round(v[2] * 64)), enc_normal(n) - (65536 if enc_normal(n) > 32767 else 0))
    o_tri = 108; o_sh = o_tri + len(tri_b); o_st = o_sh + len(sh_b); o_xyz = o_st + len(st_b); o_end = o_xyz + len(xyzn)
    surf = struct.pack('<4s64siiiiiiiiii', b'IDP3', surf_name.encode()[:63], 0, nf, 1, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end) + tri_b + sh_b + st_b + xyzn
    fr = b''
    for i, X in enumerate(frames):
        mn = [min(v[k] for v in X) for k in range(3)]; mx = [max(v[k] for v in X) for k in range(3)]
        c = [(mn[k] + mx[k]) / 2 for k in range(3)]; r = math.sqrt(sum((mx[k] - c[k]) ** 2 for k in range(3)))
        nm = (frame_names[i] if frame_names else 'f%d' % i).encode()[:15]
        fr += struct.pack('<3f3f3ff16s', *mn, *mx, 0, 0, 0, r, nm)
    o_fr = 108; o_tag = o_fr + len(fr); o_surf = o_tag; o_eof = o_surf + len(surf)
    hdr = struct.pack('<4si64siiiiiiiii', b'IDP3', 15, model_name.encode()[:63], 0, nf, 0, 1, 0, o_fr, o_tag, o_surf, o_eof)
    open(path, 'wb').write(hdr + fr + surf)


def signed_perms():
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            M = [[0.0] * 3 for _ in range(3)]
            for i in range(3): M[i][perm[i]] = float(sg[i])
            yield M


# ----------------------------------------------------------------------------------------------- Blender side
def load_library(path=DEFAULT_LIB):
    return json.load(open(path))


def M4(rows):
    return Matrix([list(r) for r in rows])


def _armature_for_mesh(mesh_obj):
    for m in mesh_obj.modifiers:
        if m.type == 'ARMATURE' and m.object: return m.object
    p = mesh_obj.parent
    return p if p and p.type == 'ARMATURE' else None


class HandRig:
    """The imported FBX hand of one side: its armature, mesh, and the conversion between the library's joint frames
    (relative to HANDPALM_joint, FBX units) and Blender's bones (armature space), solved from the rest pose."""
    def __init__(self, lib, side, arm, mesh):
        self.lib, self.side, self.arm, self.mesh = lib, side, arm, mesh
        self.joints = lib['joints'][side]; bind = lib['bind'][side]
        missing = [j for j in self.joints if j not in arm.data.bones]
        if missing: raise RuntimeError('armature %s lacks joints %s' % (arm.name, missing))
        A = {j: arm.data.bones[j].matrix_local.copy() for j in self.joints}        # rest, armature space
        Lb = {j: M4(bind[j]) for j in self.joints}                                   # bind, palm-relative, FBX units
        palm = 'HANDPALM_joint'; Ap_inv = A[palm].inverted()
        # unit scale the importer applied (FBX cm -> Blender units): palm->INDEX_BASE distance
        def dist(M, N): return (M.to_translation() - N.to_translation()).length
        self.s_y = dist(A[palm], A['INDEX_BASE_joint']) / max(dist(Lb[palm], Lb['INDEX_BASE_joint']), 1e-9)
        # the one bone-axis correction K (a signed permutation): palm^-1 A_j  ==  K^-1 L_j K  (scaled)
        best = None
        for K in signed_perms():
            Km = M4([K[0] + [0], K[1] + [0], K[2] + [0], [0, 0, 0, 1]]); Ki = Km.inverted()
            err = 0.0
            for j in self.joints:
                rel = Ap_inv @ A[j]; tgt = Ki @ Lb[j] @ Km
                for r in range(3):
                    for c in range(3): err += abs(rel[r][c] - tgt[r][c])
                    err += abs(rel[r][3] / self.s_y - tgt[r][3])
            if best is None or err < best[0]: best = (err, Km)
        self.K_err, self.K = best
        self.A_rest = A

    def palm_to_armature(self):
        """4x4: palm frame (FBX units) -> armature space"""
        S = Matrix.Scale(self.s_y, 4)
        return self.A_rest['HANDPALM_joint'] @ self.K.inverted() @ S

    def apply_pose(self, joints):
        """joints: {name: 4x4 palm-relative (library entry)}. Sets every pose bone's armature-space matrix."""
        arm = self.arm
        if arm.animation_data: arm.animation_data_clear()
        if self.mesh.animation_data: self.mesh.animation_data_clear()
        P2A = self.palm_to_armature(); Ki = self.K.inverted(); K = self.K
        # bone_j (armature) = P2A @ L_j @ K  with the scale folded: positions scale, axes do not
        for j in self.joints:   # library order is parent before child
            Lj = M4(joints[j]); pb = arm.pose.bones[j]
            pb.matrix = P2A @ Lj @ K @ Matrix.Scale(1.0 / self.s_y, 4)   # undo the scale on the bone axes
            bpy.context.view_layer.update()

    def place(self, rotvec, t_cm, hand_scale):
        """armature world = T(t) R(rotvec) (hand_scale) palm^-1: the mesh lands in the controller frame, cm (solve.hand_X)"""
        ang = math.sqrt(sum(v * v for v in rotvec))
        R = Matrix.Rotation(ang, 4, Vector(rotvec).normalized()) if ang > 1e-12 else Matrix.Identity(4)
        W = Matrix.Translation(Vector(t_cm)) @ R @ Matrix.Scale(hand_scale, 4) @ self.palm_to_armature().inverted()
        self.arm.matrix_world = W
        if self.mesh.parent != self.arm: self.mesh.matrix_world = W @ self.mesh.matrix_world
        bpy.context.view_layer.update()

    def world_mesh(self):
        """(verts world, loops uv per corner, triangles as (vert idx triplets, uv triplets)) of the posed, skinned mesh"""
        dg = bpy.context.evaluated_depsgraph_get(); ev = self.mesh.evaluated_get(dg); me = ev.to_mesh()
        try:
            me.calc_loop_triangles()
            Wm = ev.matrix_world
            V = [Wm @ v.co for v in me.vertices]
            uv_layer = me.uv_layers.active.data if me.uv_layers.active else None
            tris = []
            for lt in me.loop_triangles:
                uvs = [tuple(uv_layer[l].uv) if uv_layer else (0.0, 0.0) for l in lt.loops]
                tris.append((tuple(lt.vertices), uvs))
            return V, tris
        finally:
            ev.to_mesh_clear()

    def palm_verts(self):
        """posed, skinned mesh in the palm frame (FBX units): what the library's reference clouds are in"""
        V, _ = self.world_mesh()
        Wi = (self.arm.matrix_world @ self.palm_to_armature()).inverted()
        return [Wi @ v for v in V]


def import_hand(fbx=DEFAULT_FBX):
    """-> {'R': (armature, mesh), 'L': (armature, mesh)}. Hand_Low is the right rig, Hand_Low1 the left (handmodel.py)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx, use_anim=False, automatic_bone_orientation=False, ignore_leaf_bones=False, use_custom_normals=False)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = sorted([o for o in new if o.type == 'MESH' and o.name.startswith('Hand_Low')], key=lambda o: o.name)
    if len(meshes) < 2: raise RuntimeError('expected two Hand_Low meshes, got %s' % [o.name for o in meshes])
    out = {}
    for side, mesh in zip('RL', meshes):
        arm = _armature_for_mesh(mesh)
        if arm is None: raise RuntimeError('no armature deforms %s' % mesh.name)
        out[side] = (arm, mesh)
    # the controllers (NURBS curves, nulls) are not needed: hide them
    for o in new:
        if o.type in ('CURVE', 'EMPTY'): o.hide_set(True)
    return out


def import_gun(card_folder, lib=None, scale=(-1.0, 1.0, 1.0), gun_move=None):
    """the card's labelled MD3 at its idle frame, placed in the controller frame; the card's points as empties"""
    cards = [f for f in os.listdir(card_folder) if f.endswith('.card') and not f.endswith('.blend.card')]
    if not cards: raise RuntimeError('no .card in %s' % card_folder)
    card = parse_card(os.path.join(card_folder, cards[0]))
    md3 = read_md3(os.path.join(card_folder, card['model']))
    gm = gun_move or {}
    L, t = gun_chain(scale, (gm.get('Offset_x', 0.0), gm.get('Offset_y', 0.0)), gm.get('ZOffset', 0.0), gm.get('AngleOffset', 0.0), gm.get('PitchOffset', 0.0), gm.get('RollOffset', 0.0))
    W = M4([L[0] + [t[0]], L[1] + [t[1]], L[2] + [t[2]], [0, 0, 0, 1]])
    coll = bpy.data.collections.get('Handfit') or bpy.data.collections.new('Handfit')
    if coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
    objs = []
    f = min(card.get('idle', 0), md3['nframes'] - 1)
    for s in md3['surfs']:
        me = bpy.data.meshes.new('%s_%s' % (card.get('weapon', 'gun'), s['name']))
        me.from_pydata([Vector(v) for v in s['xyz'][f]], [], s['tris'])
        uv = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                st = s['st'][me.loops[li].vertex_index]; uv.data[li].uv = (st[0], 1.0 - st[1])
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = W; coll.objects.link(ob); objs.append(ob)
        ob['handfit_role'] = 'gun'; ob['handfit_surface'] = s['name']
    for name, p in card['points'].items():
        e = bpy.data.objects.new('card_%s' % name, None); e.empty_display_type = 'SPHERE'; e.empty_display_size = 0.6
        e.matrix_world = W @ Matrix.Translation(Vector(p)); coll.objects.link(e); e['handfit_role'] = 'card_point'
        if objs: e.parent = objs[0]; e.matrix_parent_inverse = objs[0].matrix_world.inverted()
    if objs:
        objs[0]['handfit_scale'] = list(scale); objs[0]['handfit_card'] = card_folder; objs[0]['handfit_weapon'] = card.get('weapon', '')
    return objs, card


def gun_numbers(gun_obj):
    """read the six MODELDEF numbers back from where the gun object sits now (the gun moved to the hand)"""
    W = gun_obj.matrix_world; sc = list(gun_obj.get('handfit_scale', (-1.0, 1.0, 1.0)))
    Lw = [[W[i][j] for j in range(3)] for i in range(3)]; tw = [W[i][3] for i in range(3)]
    return gun_numbers_from_world(Lw, tw, sc)


def export_hand(rig, out_dir, cls, frames, skin='fbx_hand.png'):
    """frames: list of (name, joints) poses to bake, in order. Writes <cls>_hand_<side>.md3 and returns the report."""
    os.makedirs(out_dir, exist_ok=True)
    baked = []; names = []; tri_idx = None; uv_out = None
    for name, joints in frames:
        rig.apply_pose(joints)
        V, tris = rig.world_mesh()
        key = {}; verts = []; uvs = []; T = []
        for vidx, uvt in tris:
            row = []
            for k in range(3):
                kk = (vidx[k], (round(uvt[k][0], 6), round(uvt[k][1], 6)))
                if kk not in key: key[kk] = len(verts); verts.append(V[vidx[k]]); uvs.append(uvt[k])
                row.append(key[kk])
            T.append(row)
        X = flu_to_md3([[v.x, v.y, v.z] for v in verts])
        if tri_idx is None: tri_idx, uv_out = T, [(u[0], 1.0 - u[1]) for u in uvs]
        elif T != tri_idx: raise RuntimeError('frame %s has a different vertex split from the first frame' % name)
        baked.append(X); names.append(name[:15])
    path = os.path.join(out_dir, '%s_hand_%s.md3' % (cls, rig.side))
    write_md3(path, baked, tri_idx, uv_out, skin, frame_names=names)
    return dict(md3=path, frames=names, verts=len(baked[0]), tris=len(tri_idx))


def report_line(rig, lib, pose_key):
    """the one line the agent reads: index pad to trigger empty, penetration estimate against the gun (nearest point)"""
    out = {}
    V, _ = rig.world_mesh()
    lm = lib['controller_grip'][rig.side]['landmarks']
    trig = bpy.data.objects.get('card_trigger')
    if trig and 'pad_I' in lm and lm['pad_I'] < len(V):
        out['index_pad_to_trigger_cm'] = round((V[lm['pad_I']] - trig.matrix_world.translation).length, 3)
    guns = [o for o in bpy.data.objects if o.get('handfit_role') == 'gun']
    if guns:
        kd = KDTree(sum(len(o.data.vertices) for o in guns))
        i = 0
        for o in guns:
            for v in o.data.vertices: kd.insert(o.matrix_world @ v.co, i); i += 1
        kd.balance()
        pads = [lm[k] for k in ('pad_I', 'pad_M', 'pad_R', 'pad_P', 'pad_T') if k in lm and lm[k] < len(V)]
        out['pads_to_gun_cm'] = [round(kd.find(V[p])[2], 3) for p in pads]
    return '%s %s %s' % (pose_key, rig.side, json.dumps(out))


def apply_library_pose(rigs, lib, key, seat=True):
    ent = lib['poses'][key]; side = ent['side']; arm, mesh = rigs[side]
    rig = HandRig(lib, side, arm, mesh); rig.apply_pose(ent['joints'])
    if seat:
        hp = ent.get('hand_place') or dict(rotvec=lib['controller_grip'][side]['rotvec'], t_cm=lib['controller_grip'][side]['t_cm'])
        rig.place(hp['rotvec'], hp['t_cm'], lib['hand_scale'])
    return rig


# ----------------------------------------------------------------------------------------------- UI
if IN_BLENDER:
    def _pose_items(self, context):
        try:
            lib = load_library(context.scene.handfit_library)
            return [(k, k, v.get('source', '')) for k, v in lib['poses'].items()]
        except Exception as e:
            return [('none', 'no library: %s' % e, '')]

    class HANDFIT_OT_load_card(bpy.types.Operator):
        bl_idname = 'handfit.load_card'; bl_label = 'Load card'
        def execute(self, context):
            sc = context.scene; lib = load_library(sc.handfit_library)
            gm = lib['poses'].get(sc.handfit_pose, {}).get('gun_move') if sc.handfit_pose else None
            scale = tuple(sc.handfit_gun_scale)
            objs, card = import_gun(bpy.path.abspath(sc.handfit_card), lib, scale, gm)
            self.report({'INFO'}, 'loaded %s (%d surfaces, %d card points)' % (card.get('weapon'), len(objs), len(card['points'])))
            return {'FINISHED'}

    class HANDFIT_OT_import_hand(bpy.types.Operator):
        bl_idname = 'handfit.import_hand'; bl_label = 'Import hand'
        def execute(self, context):
            rigs = import_hand(bpy.path.abspath(context.scene.handfit_fbx))
            context.scene['handfit_rigs'] = {s: [a.name, m.name] for s, (a, m) in rigs.items()}
            self.report({'INFO'}, 'hands: %s' % {s: a.name for s, (a, m) in rigs.items()})
            return {'FINISHED'}

    def _rigs(context):
        d = context.scene.get('handfit_rigs')
        if not d: raise RuntimeError('import the hand first')
        return {s: (bpy.data.objects[v[0]], bpy.data.objects[v[1]]) for s, v in d.items()}

    class HANDFIT_OT_apply_pose(bpy.types.Operator):
        bl_idname = 'handfit.apply_pose'; bl_label = 'Apply pose'
        def execute(self, context):
            sc = context.scene; lib = load_library(sc.handfit_library)
            rig = apply_library_pose(_rigs(context), lib, sc.handfit_pose, seat=sc.handfit_seat)
            self.report({'INFO'}, 'K error %.4f, unit scale %.4f; %s' % (rig.K_err, rig.s_y, report_line(rig, lib, sc.handfit_pose)))
            return {'FINISHED'}

    class HANDFIT_OT_export(bpy.types.Operator):
        bl_idname = 'handfit.export'; bl_label = 'Export'
        def execute(self, context):
            sc = context.scene; lib = load_library(sc.handfit_library); rigs = _rigs(context)
            ent = lib['poses'][sc.handfit_pose]; side = ent['side']; arm, mesh = rigs[side]
            rig = HandRig(lib, side, arm, mesh)
            cls = sc.handfit_class or sc.handfit_pose.split(':')[-1]
            # the pose as it is NOW in the scene (the user may have moved bones): read it back palm-relative
            P2A_inv = (rig.palm_to_armature()).inverted()
            joints_now = {j: [list(r) for r in (P2A_inv @ arm.pose.bones[j].matrix @ Matrix.Scale(rig.s_y, 4) @ rig.K.inverted())] for j in rig.joints}
            frames = [('%s_trg' % cls[:11], joints_now)]
            if ent.get('squeeze'): frames.append(('%s_sqz' % cls[:11], ent['squeeze']))
            out_dir = bpy.path.abspath(sc.handfit_out)
            rep = export_hand(rig, out_dir, cls, frames)
            guns = [o for o in bpy.data.objects if o.get('handfit_role') == 'gun']
            gn = gun_numbers(guns[0]) if guns else None
            snippet = []
            if gn:
                snippet += ['// %s: the gun moved to the hand (Handfit, Blender). Scale as the set has it.' % cls,
                            '   Scale %s' % ' '.join('%.3f' % v for v in guns[0].get('handfit_scale', (-1, 1, 1))),
                            '   Offset %.3f %.3f' % tuple(gn['Offset']), '   ZOffset %.3f' % gn['ZOffset'],
                            '   AngleOffset %.3f' % gn['AngleOffset'], '   PitchOffset %.3f' % gn['PitchOffset'], '   RollOffset %.3f' % gn['RollOffset'], '']
            snippet += ['// hand frames in %s (hook 0, rot 0: the frame is where the hand is drawn)' % os.path.basename(rep['md3']),
                        'Model RSQ_GunSide', '{', '\tPath "models/rsq/fbx"', '\tModel 0 "%s"' % os.path.basename(rep['md3']), '\tSkin 0 "fbx_hand.png"',
                        '\tScale -1.0 1.0 1.0', '\tOffset 0.0 -24.0 -10.0']
            snippet += ['\tFrameIndex RQXX %s 0 %d\t// %s' % (chr(65 + i), i, n) for i, n in enumerate(rep['frames'])] + ['}']
            open(os.path.join(out_dir, '%s.modeldef.txt' % cls), 'w').write('\n'.join(snippet) + '\n')
            record = dict(cls=cls, side=side, pose=sc.handfit_pose, joints=joints_now, gun_move=gn, hand_world=[list(r) for r in arm.matrix_world], md3=rep, report=report_line(rig, lib, sc.handfit_pose))
            json.dump(record, open(os.path.join(out_dir, '%s.handfit.json' % cls), 'w'), indent=1)
            self.report({'INFO'}, record['report'])
            return {'FINISHED'}

    class HANDFIT_PT_panel(bpy.types.Panel):
        bl_label = 'Handfit'; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'Handfit'
        def draw(self, context):
            sc = context.scene; l = self.layout
            l.prop(sc, 'handfit_library'); l.prop(sc, 'handfit_fbx')
            l.separator(); l.prop(sc, 'handfit_card'); l.prop(sc, 'handfit_gun_scale'); l.operator('handfit.load_card')
            l.separator(); l.operator('handfit.import_hand'); l.prop(sc, 'handfit_pose'); l.prop(sc, 'handfit_seat'); l.operator('handfit.apply_pose')
            l.separator(); l.prop(sc, 'handfit_class'); l.prop(sc, 'handfit_out'); l.operator('handfit.export')

    CLASSES = (HANDFIT_OT_load_card, HANDFIT_OT_import_hand, HANDFIT_OT_apply_pose, HANDFIT_OT_export, HANDFIT_PT_panel)

    def register():
        for c in CLASSES: bpy.utils.register_class(c)
        S = bpy.types.Scene
        S.handfit_library = bpy.props.StringProperty(name='Pose library', subtype='FILE_PATH', default=DEFAULT_LIB)
        S.handfit_fbx = bpy.props.StringProperty(name='FBX hand', subtype='FILE_PATH', default=DEFAULT_FBX)
        S.handfit_card = bpy.props.StringProperty(name='Card folder', subtype='DIR_PATH', default=os.path.join(REPO, 'cards', 'bd21', 'pistol'))
        S.handfit_gun_scale = bpy.props.FloatVectorProperty(name='Gun MODELDEF Scale', size=3, default=(-1.0, 1.0, 1.0))
        S.handfit_pose = bpy.props.EnumProperty(name='Pose', items=_pose_items)
        S.handfit_seat = bpy.props.BoolProperty(name='Seat the hand where the hold put it', default=True)
        S.handfit_class = bpy.props.StringProperty(name='Weapon class', default='')
        S.handfit_out = bpy.props.StringProperty(name='Output folder', subtype='DIR_PATH', default=os.path.join(REPO, 'work', 'handfit'))

    def unregister():
        for c in reversed(CLASSES): bpy.utils.unregister_class(c)
        for p in ('handfit_library', 'handfit_fbx', 'handfit_card', 'handfit_gun_scale', 'handfit_pose', 'handfit_seat', 'handfit_class', 'handfit_out'):
            delattr(bpy.types.Scene, p)

    if __name__ == '__main__':
        register()
