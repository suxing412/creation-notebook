import json,random,pathlib,hashlib,collections,math
P=pathlib.Path(__file__).parent; D=[(0,1),(1,0),(0,-1),(-1,0)] # N E S W in Blender XY
N=3;BASE={'straight':(0,2),'elbow':(0,1),'tee':(0,1,3),'end':(2,)};T={}
for name,ports in BASE.items():
 seen=set()
 for r in range(4):
  p=tuple(sorted((d+r)%4 for d in ports))
  if p not in seen:T[name+str(r)]={'kind':name,'rotationCW':r*90,'ports':p};seen.add(p)
def initial():
 dom=[]
 for y in range(N):
  for x in range(N):
   c=set(T)
   for d,(dx,dy) in enumerate(D):
    if not(0<=x+dx<N and 0<=y+dy<N):
     is_terminal=(x==1 and y==0 and d==2) or (x==1 and y==2 and d==0)
     c={t for t in c if (d in T[t]['ports'])==is_terminal}
   dom.append(c)
 return dom
def compatible(a,b,d):return (d in T[a]['ports'])==((d+2)%4 in T[b]['ports'])
def solve(seed,locks=None,budget=30000):
 dom=initial();rng=random.Random(seed);work=decisions=shrinks=removed=0;fail=None;status='solved'
 if locks:
  for i,t in locks.items():dom[i]&={t}
 while True:
  changed=True
  while changed:
   changed=False
   for i,A in enumerate(dom):
    if not A:status='contradiction';fail=[i%N,i//N];break
    for d,(dx,dy) in enumerate(D):
     x,y=i%N+dx,i//N+dy
     if not(0<=x<N and 0<=y<N):continue
     j=y*N+x;old=dom[j];keep={b for b in old if any(compatible(a,b,d) for a in A)};work+=1
     if work>budget:status='budget_exceeded';fail=[x,y];break
     if keep!=old:removed+=len(old)-len(keep);shrinks+=1;dom[j]=keep;changed=True
    if status!='solved':break
   if status!='solved':break
  if status!='solved':break
  remaining=[i for i,a in enumerate(dom) if len(a)>1]
  if not remaining:break
  size=min(len(dom[i]) for i in remaining);i=rng.choice([i for i in remaining if len(dom[i])==size]);dom[i]={rng.choice(sorted(dom[i]))};decisions+=1
 return {'seed':seed,'solver_status':status,'failure_position':fail,'work_units':work,'domain_contractions':shrinks,'removed_states':removed,'decisions':decisions,'layout':[next(iter(a)) if len(a)==1 else None for a in dom],'unresolved_domains':[sorted(a) for a in dom] if status!='solved' else None}
def validate(layout):
 errors=[];edges=[]
 if len(layout)!=9 or any(t not in T for t in layout):return {'valid':False,'errors':['incomplete']}
 for i,t in enumerate(layout):
  for d in T[t]['ports']:
   dx,dy=D[d];x,y=i%N+dx,i//N+dy
   if 0<=x<N and 0<=y<N:
    j=y*N+x
    if (d+2)%4 not in T[layout[j]]['ports']:errors.append(f'mismatch:{i}->{j}')
    elif i<j:edges.append([i,j])
   elif not ((i==1 and d==2) or (i==7 and d==0)):errors.append(f'boundary:{i}:{d}')
 if 2 not in T[layout[1]]['ports'] or 0 not in T[layout[7]]['ports']:errors.append('terminal_missing')
 adjacency={i:set() for i in range(9)}
 for i,j in edges:adjacency[i].add(j);adjacency[j].add(i)
 reached={1};queue=[1]
 while queue:
  for j in adjacency[queue.pop()]-reached:reached.add(j);queue.append(j)
 if 7 not in reached:errors.append('exit_unreachable')
 if len(reached)!=9:errors.append('isolated_component')
 deg=collections.Counter(len(a) for a in adjacency.values());invariant={'degree_histogram':dict(sorted(deg.items())),'edges':len(edges),'cycle_rank_if_connected':len(edges)-8}
 return {'valid':not errors,'errors':errors,'reachable_tiles':len(reached),'edges':edges,'topology_invariant':invariant,'topology_class':json.dumps(invariant,sort_keys=True)}
def socket_ok(a,b):return a['kind']==b['kind'] and abs(a['width']-b['width'])<1e-6 and abs(a['floor']-b['floor'])<1e-6 and a['normal']==[-v for v in b['normal']] and abs(a['clear_height']-b['clear_height'])<1e-6 and all(abs(x-y)<1e-6 for x,y in zip(a['position'],b['position']))
def main():
 rs=[]
 for seed in range(20):
  r=solve(seed);r['validation']=validate(r['layout']);r['status']='accepted' if r['validation']['valid'] and r['solver_status']=='solved' else ('global_validation_failed' if r['solver_status']=='solved' else r['solver_status']);rs.append(r)
 # Strong local contradiction with entirely interior shared edge: center N-only End vs north center E/W Straight (also boundary contradiction).
 bad=solve(0,{4:'end2',5:'end1'})
 assert 'end2' in initial()[4] and 'end1' in initial()[5]
 p={'kind':'P','width':1.6,'floor':.2,'normal':[1,0],'clear_height':2.2,'position':[2,0,.2]};q={'kind':'P','width':1.6,'floor':.3,'normal':[-1,0],'clear_height':2.2,'position':[2,0,.3]}
 broken=list(next(r for r in rs if r['status']=='accepted')['layout']);broken[4]='end0'
 tests={'contradiction_rejected':bad['solver_status']=='contradiction','height_mismatch_rejected':not socket_ok(p,q),'budget_rejected':solve(0,budget=1)['solver_status']=='budget_exceeded','broken_global_or_interface_detected':not validate(broken)['valid'],'deterministic':all(solve(r['seed'])['layout']==r['layout'] for r in rs),'propagation_occurs':all(r['removed_states']>0 for r in rs),'local_all_solved':all(r['solver_status']=='solved' and not any(e.startswith('mismatch') for e in r['validation']['errors']) for r in rs),'global_failure_demonstrated':any(r['status']=='global_validation_failed' for r in rs)}
 assert all(tests.values()),tests
 classes={}
 for r in rs:
  if r['status']=='accepted':classes.setdefault(r['validation']['topology_class'],r['seed'])
 summary={'counts':dict(collections.Counter(r['status'] for r in rs)),'nonisomorphic_graph_classes_lower_bound':len(classes),'selected_topology_seeds':list(classes.values())[:3],'tests':tests}
 for name,obj in [('states',T),('results',rs),('summary',summary),('negative-tests',{'locked_conflict':bad,'height_mismatch':[p,q],'broken_layout':broken,'broken_validation':validate(broken)}),('config',{'version':'passage-wfc-0.1','N':3,'seeds':list(range(20)),'budget':30000,'restart':False,'backtracking':False,'fixed_interior':False,'boundary':'one south entry and one north exit; other external ports closed','all_weights':1,'rng':'Python random.Random MT19937','python_version':__import__('platform').python_version()})]: (P/(name+'.json')).write_text(json.dumps(obj,indent=2))
 print(summary)
if __name__=='__main__':main()
