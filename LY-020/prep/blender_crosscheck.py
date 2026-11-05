# LY-020 prep: Blender cross-check of the city wall GLBs (read-only inputs) + CPU Workbench close-ups of the measured gaps.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <lab_root> <out_dir>
# Writes <out_dir>/blender-crosscheck.json and <out_dir>/preview/*.png. Never writes into the lab repo.
import bpy, bmesh, sys, os, json, hashlib, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
CITY = LAB + '/docs/cities/luoyang/'
os.makedirs(OUT + '/preview', exist_ok=True)
WALLS = ['A/wall-00', 'A/wall-01', 'A/wall-02', 'A/wall-03', 'A/wall-04', 'A/wall-05', 'A/wall-06', 'A/wall-07',
         'direct/wall-08', 'direct/wall-09', 'A/wall-10', 'A/wall-11', 'direct/gate-body-only']
GROUND = [('network-ground-stitched', (0, 0, 0)), ('retained', (0, 0, 0)), ('south', (0, 0, 0)), ('D08', (580, 0, -960))]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
res = {'blender': bpy.app.version_string, 'walls': {}}


def imp(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o['ly020_tag'] = tag
    return new


for w in WALLS:
    p = CITY + 'assets/city-wall/' + w + '.glb'
    objs = imp(p, w)
    rec = {'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'objects': []}
    for o in objs:
        if o.type != 'MESH':
            continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        nonman = sum(1 for e in bm.edges if not e.is_manifold)
        lo = [min(v.co[i] for v in bm.verts) for i in range(3)]
        hi = [max(v.co[i] for v in bm.verts) for i in range(3)]
        rec['objects'].append({'name': o.name, 'verts_welded': len(bm.verts), 'faces': len(bm.faces), 'nonmanifold_edges_after_weld': nonman,
                               'volume_m3': round(bm.calc_volume(signed=True), 2),
                               'blender_bbox_min_ZupYfwd': [round(x, 3) for x in lo], 'blender_bbox_max_ZupYfwd': [round(x, 3) for x in hi]})
        bm.free()
    res['walls'][w] = rec

for g, pos in GROUND:
    objs = imp(CITY + 'assets/ground-atomic/' + g + '.glb', 'ground/' + g)
    for o in objs:
        if o.parent is None:
            # glTF (x, y, z) -> Blender (x, -z, y)
            o.location = Vector((o.location.x + pos[0], o.location.y - pos[2], o.location.z + pos[1]))

# colouring: walls earth, ground grey-green, gate body dark
def mat(name, rgba):
    m = bpy.data.materials.new(name); m.diffuse_color = rgba; return m
mw, mg, mb = mat('w', (0.72, 0.52, 0.33, 1)), mat('g', (0.55, 0.62, 0.5, 1)), mat('b', (0.25, 0.25, 0.3, 1))
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    t = o.get('ly020_tag', '')
    o.data.materials.clear(); o.data.materials.append(mg if t.startswith('ground') else mb if 'gate-body' in t else mw)

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_object_outline = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
world = bpy.data.worlds.new('w'); sc.world = world; world.color = (0.93, 0.93, 0.92)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.1; cd.clip_end = 20000


def shot(name, gx, gz, span, el=90, az=0, h=6):
    # target in glTF coords (x east, z = -north); Blender: (x, -z, y)
    tgt = Vector((gx, -gz, h / 2))
    cd.type = 'ORTHO'; cd.ortho_scale = span
    r = span * 2
    e, a = math.radians(el), math.radians(az)
    cam.location = tgt + Vector((r * math.cos(e) * math.sin(a), -r * math.cos(e) * math.cos(a), r * math.sin(e)))
    d = tgt - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = OUT + '/preview/' + name + '.png'
    bpy.ops.render.render(write_still=True)
    res.setdefault('previews', []).append({'file': 'preview/' + name + '.png', 'renderer': 'Blender Workbench (CPU, not GPU/browser)',
                                           'target_gltf_xz': [gx, gz], 'ortho_span_m': span, 'elevation_deg': el, 'azimuth_deg': az})

shot('shangdong-gap-top', 2482.8, -2597.0, 90)
shot('shangdong-gap-oblique', 2482.8, -2597.0, 90, el=35, az=200)
shot('guangyang-direct-top', 0.0, -489.8, 140)
shot('guangyang-jog-08-oblique', -2.0, -437.0, 30, el=30, az=240)
shot('shangxi-stub-top', -30.4, -2640.0, 60)
shot('ne-corner-miter-top', 2459.2, 30.6, 60)
json.dump(res, open(OUT + '/blender-crosscheck.json', 'w'), indent=1)
print('ok')
