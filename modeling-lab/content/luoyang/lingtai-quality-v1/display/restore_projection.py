#!/usr/bin/env python3
"""Restore a byte-identical source GLB from its public display projection.
Usage: python restore_projection.py PATH-TO-mapping.json OUTPUT.glb
"""
import sys,json,hashlib,struct
from pathlib import Path
mfile=Path(sys.argv[1]); m=json.loads(mfile.read_text()); root=mfile.parent
h=lambda b:hashlib.sha256(b).hexdigest()
binary=bytearray(m['originalBinBytes'])
for v in m['bufferViews']:
    data=(root/v['uri']).read_bytes()[v['offset']:v['offset']+v['bytes']]
    assert h(data)==v['sha256'],v['uri']
    binary[v['originalOffset']:v['originalOffset']+v['bytes']]=data
j=(root/m['originalJson']).read_bytes()
b=struct.pack('<III',0x46546c67,2,m['sourceBytes'])+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
assert len(b)==m['sourceBytes'] and h(b)==m['sourceSha256']
Path(sys.argv[2]).write_bytes(b)
print(m['sourceSha256'])
