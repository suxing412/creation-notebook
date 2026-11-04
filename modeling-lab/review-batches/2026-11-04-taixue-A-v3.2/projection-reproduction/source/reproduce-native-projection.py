"""Reproduce the scene-only Taixue A native projection without changing input ZIPs.
Run with Blender 4.3.2: blender -b -t 2 -P this-script.py -- --source-zip SOURCE --projection-zip REFERENCE --output-dir NEW_DIRECTORY
"""
import argparse,hashlib,json,math,os,re,struct,sys,tempfile,zipfile
from pathlib import Path
import bpy

SOURCE_ZIP_SHA256='0f4fdd0ceada1793da6c81d400a9f940a69ce42202bd4725c9cd7d92f1d88815'
REFERENCE_ZIP_SHA256='83556f30e8e88c56f8578b84afba00fe81d4c611cadb23acd30d7e3cbf4e671d'
sha=lambda b:hashlib.sha256(b).hexdigest()

def simple(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return list(v)
    except TypeError:return str(v)

def signature():
    meshes=[]
    for o in sorted(bpy.data.objects,key=lambda o:o.name):
        if o.type!='MESH':continue
        m=o.data;h=hashlib.sha256();h.update(repr([list(r)for r in o.matrix_world]).encode())
        for v in m.vertices:h.update(struct.pack('<3f',*v.co))
        for p in m.polygons:
            h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));h.update(struct.pack('<I',p.material_index))
        for u in m.uv_layers:
            for d in u.data:h.update(struct.pack('<2f',*d.uv))
        meshes.append(dict(object=o.name,geometry_topology_uv_matrix_sha256=h.hexdigest(),materials=[x.name for x in m.materials],verts=len(m.vertices),faces=len(m.polygons)))
    materials=[]
    for m in sorted(bpy.data.materials,key=lambda m:m.name):
        nodes=[];links=[]
        if m.node_tree:
            for n in m.node_tree.nodes:
                nodes.append(dict(name=n.name,type=n.bl_idname,inputs=[(s.identifier,simple(s.default_value))for s in n.inputs if hasattr(s,'default_value')],image=n.image.name if hasattr(n,'image') and n.image else None,operation=getattr(n,'operation',None),uv_map=getattr(n,'uv_map',None)))
            links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier)for l in m.node_tree.links)
        materials.append(dict(name=m.name,nodes=nodes,links=links,diffuse=list(m.diffuse_color),metallic=m.metallic,roughness=m.roughness))
    return dict(meshes=meshes,materials=materials,packed_images={i.name:sha(i.packed_file.data)for i in bpy.data.images if i.packed_file})

def open_native(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.view_layer.update()
    return signature()

def extract_one(z,name,destination):
    p=destination/Path(name).name;p.write_bytes(z.read(name));return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-zip',required=True,type=Path);ap.add_argument('--projection-zip',required=True,type=Path);ap.add_argument('--output-dir',required=True,type=Path)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else [])
    if bpy.app.version!=(4,3,2):raise RuntimeError('Use the verified Blender 4.3.2 environment; other versions have not been certified.')
    src=args.source_zip.resolve();ref=args.projection_zip.resolve();out=args.output_dir.resolve()
    if sha(src.read_bytes())!=SOURCE_ZIP_SHA256 or sha(ref.read_bytes())!=REFERENCE_ZIP_SHA256:raise RuntimeError('Input ZIP SHA256 mismatch; no output written.')
    if out.exists() and any(out.iterdir()):raise RuntimeError('Output directory must be new or empty; existing files are never overwritten.')
    out.mkdir(parents=True,exist_ok=True);(out/'models').mkdir();records=[]
    with zipfile.ZipFile(src)as zs,zipfile.ZipFile(ref)as zr,tempfile.TemporaryDirectory(prefix='taixue-native-repro-')as temporary:
        if zs.testzip()is not None or zr.testzip()is not None:raise RuntimeError('Input ZIP CRC failure.')
        temp=Path(temporary);(temp/'source').mkdir();(temp/'reference').mkdir()
        for lod in range(3):
            name=f'models/taixue-A-LOD{lod}.blend';original=extract_one(zs,name,temp/'source');reference=extract_one(zr,name,temp/'reference');dest=out/name
            expected=open_native(reference)
            before=open_native(original)
            if before!=expected:raise RuntimeError(f'LOD{lod}: source and published reference differ beyond permitted metadata.')
            if bpy.data.libraries or bpy.data.texts:raise RuntimeError('Unexpected linked libraries or text blocks require review.')
            for image in bpy.data.images:
                if not image.packed_file:raise RuntimeError('Unexpected unpacked image requires review.')
                image.filepath='//textures/'+image.name
                for packed in image.packed_files:packed.filepath=image.filepath
            for scene in bpy.data.scenes:scene.render.filepath='//preview.png'
            # Save only scene datablocks and dependencies. No screens, workspaces,
            # window-manager or file-browser history are part of this library write.
            bpy.data.libraries.write(str(dest),set(bpy.data.scenes),path_remap='NONE',fake_user=False,compress=False)
            after=open_native(dest)
            if after!=before or after!=expected:raise RuntimeError(f'LOD{lod}: reproduced geometry/material/image mismatch.')
            obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
            if len(obs)!=(3 if lod==2 else 4) or not all(o.visible_get()and not o.hide_render for o in obs):raise RuntimeError('Reopened active scene is not the expected visible model.')
            raw=dest.read_bytes()
            if re.search(br'/(?:home|workspace|tmp)/[^\x00\r\n]+',raw):raise RuntimeError('Unexpected absolute environment path in native projection.')
            records.append(dict(LOD=lod,source_member=name,source_sha256=sha(zs.read(name)),published_member=name,published_sha256=sha(zr.read(name)),reproduced_member=name,reproduced_sha256=sha(raw),source_reference_reproduction_geometry_uv_matrix_material_image_equal=True,active_scene_mesh_count=len(obs),active_scene_visible=True,absolute_environment_path_scan='pass',geometry_signature=after['meshes'],material_signature_sha256=sha(json.dumps(after['materials'],sort_keys=True).encode()),packed_image_sha256=after['packed_images']))
    if sha(src.read_bytes())!=SOURCE_ZIP_SHA256 or sha(ref.read_bytes())!=REFERENCE_ZIP_SHA256:raise RuntimeError('Input changed during execution.')
    report=dict(status='pass',blender_version=bpy.app.version_string,script_sha256=sha(Path(__file__).read_bytes()),source_zip_sha256=SOURCE_ZIP_SHA256,published_projection_zip_sha256=REFERENCE_ZIP_SHA256,input_archives_unchanged=True,records=records,scope='Only native scene/UI metadata projection. No geometry repair, GLB export, image re-encoding, city placement or website mutation. Blender native bytes may vary between runs; geometry/topology/UV/matrices/material graphs/packed image bytes are checked exactly against both the original and published native files.')
    (out/'reproduction-result.json').write_text(json.dumps(report,indent=2));print('TAIXUE_NATIVE_REPRODUCTION_PASS',len(records))

if __name__=='__main__':main()
