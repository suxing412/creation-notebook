# LY-023 prep: list connected islands (world bbox, mats) of merged-mesh GLBs. Read-only; prints JSON lines to OUT.
import bpy, sys, json
argv=sys.argv[sys.argv.index('--')+1:]; GLB, ISL_OUT = argv[0], argv[1]
sys.argv=[sys.argv[0],'--']+['--glb',GLB,'--mode','loose','--out',ISL_OUT+'.unused']
src=open(__file__.replace('list_islands.py','measure_stall_feet.py'),encoding='utf-8').read()
src=src.split('# ---- classify')[0]
exec(compile(src,'measure_stall_feet_head','exec'))
rows=[]
for o in main_objs:
    for p in parts_of(o, True):
        (x0,y0,z0),(x1,y1,z1)=bbox(p)
        rows.append(dict(name=p['name'],mats=p['mats'],nf=len(p['faces']),min=r3([x0,y0,z0]),max=r3([x1,y1,z1])))
json.dump(rows,open(ISL_OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('ISLANDS',len(rows))
