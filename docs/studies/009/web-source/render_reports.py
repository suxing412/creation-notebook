from pathlib import Path
import html,re,shutil
R=Path(__file__).resolve().parents[1];D=R/'dist';out=D/'web-review';out.mkdir(parents=True,exist_ok=True)
for src in (R/'review').rglob('*'):
 if src.is_file() and src.suffix in ['.json','.md','.png','.jpg','.cjs']:
  p=out/src.relative_to(R/'review');p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
for name,title in [('reference-notes','网页对标与改进'),('reflection','网页复盘与验收边界')]:
 text=html.escape((R/'review'/f'{name}.md').read_text())
 text=re.sub(r'https://[^\s<]+',lambda m:'<a href="'+m.group(0)+'" rel="noreferrer">'+m.group(0)+'</a>',text)
 (out/f'{name}.html').write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · 009</title><link rel="stylesheet" href="../style.css"><main class="readable"><a href="../index.html">← 返回姿态工作台</a><h1>{title}</h1><pre>{text}</pre></main></html>')
print('web reports rendered')
