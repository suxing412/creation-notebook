"""AETHER 001 — original parametric reliquary. Blender 4.3+, no external assets."""
import bpy, math, os, json
from mathutils import Vector, Matrix
from math import sin, cos, pi
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS=os.path.join(ROOT,'dist','assets'); os.makedirs(ASSETS,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name, color, metal=0, rough=.4, emission=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if emission: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    return m
GOLD=mat('Champagne gold | brushed edges',(.64,.39,.14),.86,.24)
PALE=mat('Pale gold | inlaid tracery',(.92,.72,.37),.8,.2)
DARK=mat('Midnight ceramic',(.015,.033,.045),.48,.23)
TEAL=mat('Verdigris enamel',(.025,.27,.25),.5,.25)
LIGHT=mat('Aether phosphor',(.1,.9,.74),.15,.25,2)
CORE=mat('Faceted aquamarine',(.045,.53,.43),.48,.16)

def finish(o,name,m,smooth=True,bev=0):
    o.name=name; o.data.materials.append(m)
    if smooth and o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    if bev:
        b=o.modifiers.new('Soft manufactured edge','BEVEL'); b.width=bev;b.segments=3
        n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def mesh(name,verts,faces,m,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,name,m,smooth)

def lathe(name,profile,m,n=128):
    # Closed cross-sections need no end disks; axis tips use ONE vertex.
    closed=profile[0]==profile[-1]
    profile=profile[:-1] if closed else profile
    v=[];layers=[];f=[]
    for r,z in profile:
        if abs(r)<1e-9:
            layers.append([len(v)]);v.append((0,0,z))
        else:
            layers.append(list(range(len(v),len(v)+n)))
            v.extend((r*cos(2*pi*j/n),r*sin(2*pi*j/n),z) for j in range(n))
    for i in range(len(layers) if closed else len(layers)-1):
        a,b=layers[i],layers[(i+1)%len(layers)]
        for j in range(n):
            if len(a)==1:f.append((a[0],b[(j+1)%n],b[j]))
            elif len(b)==1:f.append((a[j],a[(j+1)%n],b[0]))
            else:f.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
    if not closed:
        if len(layers[0])>1:f.append(tuple(reversed(layers[0])))
        if len(layers[-1])>1:f.append(tuple(layers[-1]))
    return mesh(name,v,f,m)

def tube(name,coords,radius,m,sides=8, radii=None):
    closed=(Vector(coords[0])-Vector(coords[-1])).length<1e-8
    coords=coords[:-1] if closed else coords
    vs=[];fs=[];count=len(coords)
    for i,c in enumerate(coords):
        c=Vector(c)
        before=coords[(i-1)%count] if closed else coords[max(0,i-1)]
        after=coords[(i+1)%count] if closed else coords[min(i+1,count-1)]
        t=(Vector(after)-Vector(before)).normalized(); up=Vector((0,0,1))
        if abs(t.dot(up))>.95:up=Vector((0,1,0))
        u=t.cross(up).normalized(); w=t.cross(u).normalized();r=radius*(radii[i] if radii else 1)
        for j in range(sides):vs.append(c+r*(cos(j*2*pi/sides)*u+sin(j*2*pi/sides)*w))
    for i in range(count if closed else count-1):
        nxt=(i+1)%count
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,nxt*sides+(j+1)%sides,nxt*sides+j))
    if not closed:fs += [tuple(reversed(range(sides))),tuple((count-1)*sides+j for j in range(sides))]
    return mesh(name,vs,fs,m)

def ring(name,r,z,thick,m,rotation=None,n=192):
    pts=[Vector((r*cos(2*pi*i/n),r*sin(2*pi*i/n),0)) for i in range(n+1)]
    if rotation: pts=[rotation@p for p in pts]
    pts=[p+Vector((0,0,z)) for p in pts]
    return tube(name,pts,thick,m,10)

# One continuous turned pedestal, with stepped lips and recessed enamel bands.
lathe('Pedestal | turned basalt',[(.05,.03),(1.18,.03),(1.27,.10),(1.27,.19),(1.18,.26),(1.08,.28),(.99,.42),(.99,.51),(.85,.58),(.77,.67),(.75,.89),(.66,1.01),(.52,1.12),(.48,1.33)],DARK)
for r,z in [(1.24,.12),(1.18,.25),(.99,.47),(.76,.69),(.67,1.0),(.48,1.3)]:ring('Pedestal | gold turning',r,z,.018,PALE)
lathe('Pedestal | fluted crown',[(.48,1.18),(.59,1.22),(.61,1.33),(.55,1.40),(.44,1.44)],GOLD)
for i in range(48):
    a=i*2*pi/48
    pts=[(.78*cos(a),.78*sin(a),.61),(.94*cos(a),.94*sin(a),.53),(.98*cos(a),.98*sin(a),.47)]
    tube('Pedestal | radial engraving',pts,.007,PALE,6)
for i in range(16):
    a=i*2*pi/16
    tube('Pedestal | enamel flute',[(.76*cos(a),.76*sin(a),.72),(.75*cos(a),.75*sin(a),.86)],.021,TEAL,6)
# Sculpted gold cage: variable elliptical sweeps, six twisted rising leaves.
for k in range(6):
    v=[];f=[];points=[];n=80;sides=12
    for i in range(n+1):
        t=i/n; z=1.34+4.03*t; a=2*pi*k/6+.34*sin(pi*t)
        r=.5+1.04*sin(pi*t)**.9-.30*t
        center=Vector((r*cos(a),r*sin(a),z));points.append(center)
        tang=Vector((-sin(a),cos(a),0)); radial=Vector((cos(a),sin(a),0))
        width=(.055+.17*sin(pi*t)**1.4)*(1-.95*t**12)
        depth=(.045+.025*sin(pi*t))*(1-.90*t**15)
        for j in range(sides):
            b=j*2*pi/sides;v.append(center+tang*(cos(b)*width)+radial*(sin(b)*depth))
    for i in range(n):
        for j in range(sides):f.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    f += [tuple(reversed(range(sides))),tuple(n*sides+j for j in range(sides))]
    mesh(f'Petal_{k:02d} | sculpted gold blade',v,f,GOLD)
    # Thin raised enamel vein follows each curved blade without floating away.
    coords=[]
    for i in range(5,n-7):
        t=i/n;a=2*pi*k/6+.34*sin(pi*t);r=.5+1.04*sin(pi*t)**.9-.30*t+.068
        coords.append((r*cos(a),r*sin(a),1.34+4.03*t))
    tube(f'Petal_{k:02d} | enamel inlay',coords,.014,TEAL,6)
# Articulated equatorial collar, designed as a split dark band with fine gold lips.
lathe('Equatorial collar | enamel',[(1.45,2.88),(1.52,2.93),(1.52,3.08),(1.45,3.13),(1.43,3.08),(1.43,2.93),(1.45,2.88)],TEAL)
for z in [2.94,3.07]:ring('Equatorial collar | beaded edge',1.525,z,.019,PALE)
for i in range(36):
    a=i*2*pi/36
    tube('Collar | measured tick',[(1.54*cos(a),1.54*sin(a),2.97),(1.54*cos(a),1.54*sin(a),3.04 if i%3 else 3.08)],.008,PALE,6)
# Two oblique orbital scales intersect at plausible swivel connections.
for idx,(r,rx,ry) in enumerate([(1.92,.95,.3),(1.73,-.65,-.4)]):
    rot=Matrix.Rotation(rx,3,'X')@Matrix.Rotation(ry,3,'Y')
    ring(f'Orbit_{idx} | scale',r,3.11,.045,GOLD,rot)
    ring(f'Orbit_{idx} | phosphor track',r-.06,3.11,.009,LIGHT,rot)
    for i in range(60):
        a=i*2*pi/60;rr=r-.04
        p=rot@Vector((rr*cos(a),rr*sin(a),0))+Vector((0,0,3.11))
        tick_length=.035 if idx==1 and i==50 else (.10 if i%5==0 else .045) # Clearance from petal 05.
        q=rot@Vector(((rr-tick_length)*cos(a),(rr-tick_length)*sin(a),0))+Vector((0,0,3.11))
        tube(f'Orbit_{idx} | tick', [p,q],.007,PALE,5)
# Centerpiece: elongated faceted rhombohedral crystal with deliberately unequal tiers.
N=10;v=[(0,0,2.12)];f=[]
for rad,z,phase in [(.49,2.67,0),(.69,3.13,.1),(.44,3.67,0)]:
    for j in range(N):
        a=2*pi*j/N+phase;v.append((rad*cos(a),rad*sin(a),z))
v.append((0,0,4.23));top=len(v)-1
for j in range(N):
    f.append((0,1+(j+1)%N,1+j))
    f.append((1+2*N+j,1+2*N+(j+1)%N,top))
for i in range(2):
    for j in range(N):f.append((1+i*N+j,1+i*N+(j+1)%N,1+(i+1)*N+(j+1)%N,1+(i+1)*N+j))
mesh('Aether core | cut crystal',v,f,CORE,False)
# Internal glow visible through openings, with gold geometric wire cage.
for k in range(5):
    a=k*2*pi/5
    tube('Core | golden meridian',[(0,0,2.10),(.52*cos(a),.52*sin(a),2.67),(.72*cos(a+.1),.72*sin(a+.1),3.13),(.47*cos(a),.47*sin(a),3.67),(0,0,4.25)],.012,PALE,6)
ring('Core | levitation halo',.71,2.28,.018,LIGHT)
ring('Core | suspension halo',.53,4.08,.014,LIGHT)
# Slender pointed crown and suspended bottom needle.
lathe('Crown | carved finial',[(.0,5.29),(.20,5.29),(.26,5.38),(.23,5.48),(.12,5.57),(.105,5.75),(.0,6.12)],GOLD,64)
ring('Crown | turquoise seal',.22,5.42,.024,TEAL)
lathe('Core | lower needle',[(.0,1.58),(.09,1.91),(.15,2.01),(.08,2.13)],GOLD,48)
# A few fine chains establish construction logic between cage and orbital scale.
for k in range(3):
    a=k*2*pi/3
    tube('Suspension | fine cable',[(.54*cos(a),.54*sin(a),1.38),(.70*cos(a),.70*sin(a),1.91),(.73*cos(a),.73*sin(a),2.28)],.012,PALE,6)
# Export only the artifact. No cameras, ground or studio lights in the GLB.
bpy.ops.object.select_all(action='SELECT')
for o in bpy.context.selected_objects:
    if o.type=='MESH':
        bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
mesh_count=len([o for o in bpy.data.objects if o.type=='MESH']);triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ASSETS,'aether-reliquary.blend'))
# Preserve editable individual parts in .blend, then batch render meshes by material for mobile.
for material in [GOLD, PALE, DARK, TEAL, LIGHT, CORE]:
    bpy.ops.object.select_all(action='DESELECT')
    parts=[o for o in bpy.data.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==material]
    for o in parts:o.select_set(True)
    if parts:
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();parts[0].name='Batch | '+material.name
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(ASSETS,'aether-reliquary.glb'),export_format='GLB',use_selection=True,export_apply=True)
with open(os.path.join(ASSETS,'model-info.json'),'w') as f:json.dump({'sourceMeshObjects':mesh_count,'renderMeshes':6,'triangles':triangles,'generator':'Blender 4.3.2 / original Python mesh construction','height':6.12},f,indent=2)
# Offline studio preview for honest asset QA.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));finish(bpy.context.object,'Preview ground',mat('Studio slate',(.015,.024,.031),.1,.5))
def area(name,loc,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(5,-5,9),1400,(1,.8,.55),6);area('Cool fill',(-4,-1,6),1200,(.45,.8,1),5);area('Rim',(0,4,7),1800,(.3,1,.8),4)
bpy.ops.object.camera_add(location=(9,-13,8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.2;bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=False;s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.world.color=(.12,.12,.12);s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(ROOT,'evidence','blender-studio.png');s.view_settings.view_transform='AgX';bpy.ops.render.render(write_still=True)
print('MODEL_STATS',mesh_count,triangles)
