# LY-022 prep: hash every input (worktree bytes + git HEAD blob) and record city loading. Read-only on lab repo.
import hashlib,json,subprocess,sys
LAB='D:/GitHub/creation-notebook-lab'
def wt(p): return hashlib.sha256(open(f'{LAB}/{p}','rb').read()).hexdigest()
def head(p):
    try: return hashlib.sha256(subprocess.run(['git','-C',LAB,'show',f'HEAD:{p}'],capture_output=True,check=True).stdout).hexdigest()
    except Exception: return None
def sz(p):
    import os; return os.path.getsize(f'{LAB}/{p}')
I=json.load(open(sys.argv[1],encoding='utf-8'))
for r in I['inputs']:
    p=r['path']
    if p.startswith('modeling-lab/') or p.startswith('docs/') or p.startswith('lab/'):
        r['bytes']=sz(p); r['sha256Worktree']=wt(p); r['sha256GitHEAD']=head(p); r['eolOnlyDiff']=r['sha256Worktree']!=r['sha256GitHEAD']
json.dump(I,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('OK',len(I['inputs']))
