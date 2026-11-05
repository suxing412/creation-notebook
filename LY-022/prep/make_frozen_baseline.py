# LY-022 prep: write frozen-baseline.json (fingerprints of every node in the chunk + well opening + PROVISIONAL ports).
# usage: blender -b --factory-startup --python-exit-code 1 -P make_frozen_baseline.py -- <chunk.glb> <chunk-well-hole.json> <out.json>
import bpy,sys,json,hashlib
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
def fp(o):
    M=o.matrix_world; vs=sorted({(round((M@v.co).x,4),round((M@v.co).z,4),round(-(M@v.co).y,4)) for v in o.data.vertices})
    return hashlib.sha256(json.dumps(vs).encode()).hexdigest()
F={o.name:fp(o) for o in bpy.data.objects if o.type=='MESH'}
h=json.load(open(a[1]))
CX,CZ=214.286,-1959.184
ports=[
 {'id':'P-route_public-N-edge-x[-20,20]','a':[CX-20,CZ+2.0],'b':[CX+20,CZ+2.0],'topY':0.21,'inward':[0,-1],'status':'PROVISIONAL selftest only'},
 {'id':'P-route_public-N-edge-full','a':[CX-22.7,CZ+2.0],'b':[CX+22.15,CZ+2.0],'topY':0.21,'inward':[0,-1],'status':'PROVISIONAL'},
 {'id':'P-route_public-S-edge-full','a':[CX-22.7,CZ-2.0],'b':[CX+22.15,CZ-2.0],'topY':0.21,'inward':[0,1],'status':'PROVISIONAL'},
 {'id':'P-route_east-W-edge-streetband','a':[CX+24.0,CZ-5.0],'b':[CX+24.0,CZ+5.0],'topY':0.21,'inward':[1,0],'status':'PROVISIONAL'}]
json.dump({'chunkSha256':hashlib.sha256(open(a[0],'rb').read()).hexdigest(),'fingerprintMethod':'sha256(json(sorted unique world verts glTF xyz rounded 1e-4))',
 'keptPrefixes':['route_','boundary','C_market_ground','C_MARKET_ENTRY','A_LOD0__'],'fingerprints':F,
 'wellOpening':{'centreGLTF':h['centreGLTF'],'rMax':h['rMax'],'clearance':0.05},
 'allowGroundOverlay':True,'allowGroundOverlayStatus':'PROVISIONAL for selftest; real rule from LY-006 (double-layer definition)',
 'provisionalPorts':ports},open(a[2],'w'),indent=1)
print('OK',len(F))
