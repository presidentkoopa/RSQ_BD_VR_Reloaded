"""Minimal FBX binary (7.x) reader. Pure python + numpy. Written for lane_c (no external code)."""
import struct, zlib, numpy as np

class Node:
    __slots__=("name","props","children")
    def __init__(s,name,props,children): s.name=name; s.props=props; s.children=children
    def find(s,name):
        for c in s.children:
            if c.name==name: return c
        return None
    def findall(s,name): return [c for c in s.children if c.name==name]
    def __repr__(s): return f"<{s.name} {s.props[:3]!r} n={len(s.children)}>"

_ARR={b'f':('<f',4),b'd':('<d',8),b'l':('<q',8),b'i':('<i',4),b'b':('<b',1)}
_NP={b'f':np.float32,b'd':np.float64,b'l':np.int64,b'i':np.int32,b'b':np.int8}

def _prop(buf,o):
    t=buf[o:o+1]; o+=1
    if t==b'Y': return struct.unpack_from('<h',buf,o)[0],o+2
    if t==b'C': return bool(buf[o]),o+1
    if t==b'I': return struct.unpack_from('<i',buf,o)[0],o+4
    if t==b'F': return struct.unpack_from('<f',buf,o)[0],o+4
    if t==b'D': return struct.unpack_from('<d',buf,o)[0],o+8
    if t==b'L': return struct.unpack_from('<q',buf,o)[0],o+8
    if t in (b'S',b'R'):
        n=struct.unpack_from('<I',buf,o)[0]; o+=4; d=bytes(buf[o:o+n]); o+=n
        return (d.decode('utf8','replace') if t==b'S' else d),o
    if t in _ARR:
        n,enc,cl=struct.unpack_from('<III',buf,o); o+=12
        raw=bytes(buf[o:o+cl]); o+=cl
        if enc==1: raw=zlib.decompress(raw)
        return np.frombuffer(raw,dtype=_NP[t],count=n).copy(),o
    raise ValueError(f"bad prop type {t} at {o}")

def _node(buf,o,v64):
    if v64:
        end,np_,pl=struct.unpack_from('<QQQ',buf,o); o+=24
    else:
        end,np_,pl=struct.unpack_from('<III',buf,o); o+=12
    nl=buf[o]; o+=1
    if end==0: return None,o
    name=bytes(buf[o:o+nl]).decode(); o+=nl
    props=[]
    for _ in range(np_):
        p,o=_prop(buf,o); props.append(p)
    ch=[]
    sentinel=25 if v64 else 13
    while o<end:
        if end-o==sentinel: o=end; break
        c,o=_node(buf,o,v64)
        if c is None: break
        ch.append(c)
    return Node(name,props,ch),end

def load(path):
    buf=open(path,'rb').read()
    assert buf[:20]==b'Kaydara FBX Binary  ', 'not binary FBX'
    ver=struct.unpack_from('<I',buf,23)[0]
    v64=ver>=7500
    o=27; top=[]
    while o<len(buf):
        n,o=_node(buf,o,v64)
        if n is None: break
        top.append(n)
    return ver,Node('ROOT',[],top)

def props70(node):
    """Properties70 -> dict name->(type, values)"""
    d={}
    p=node.find('Properties70') if node else None
    if p is None: return d
    for P in p.children:
        d[P.props[0]]=(P.props[1],P.props[4:])
    return d
