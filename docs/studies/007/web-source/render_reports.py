#!/usr/bin/env python3
"""Render authored review Markdown into locally readable pages. No external services."""
from pathlib import Path
import html,re
R=Path(__file__).resolve().parents[1]
WR=R/'web-review' if (R/'web-review').exists() else R/'review'
def inline(s):
 s=html.escape(s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'\[([^]]+)\]\(([^ )]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'(?<!["=])(https?://[^\s，；。<]+)',lambda m:'<a href="'+m.group(1)+'">'+m.group(1)+'</a>',s) if '<a ' not in s else s
 return s

def render(md):
 out=[];ul=False;pre=False;paragraph=[];table=[]
 def flush():
  if paragraph:out.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
 def flush_table():
  if not table:return
  rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in table]
  hashead=len(rows)>1 and all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in rows[1])
  out.append('<div class="report-table"><table>')
  if hashead:
   out.append('<thead><tr>'+''.join('<th scope="col">'+inline(x)+'</th>' for x in rows[0])+'</tr></thead>');rows=rows[2:]
  out.append('<tbody>')
  for row in rows:out.append('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+inline(x)+('</th>' if i==0 else '</td>') for i,x in enumerate(row))+'</tr>')
  out.append('</tbody></table></div>');table.clear()
 for line in md.splitlines():
  if not pre and line.startswith('|'):
   flush()
   if ul:out.append('</ul>');ul=False
   table.append(line);continue
  if table:flush_table()
  if line.startswith('```'):
   flush()
   if ul:out.append('</ul>');ul=False
   out.append('</code></pre>' if pre else '<pre><code>');pre=not pre;continue
  if pre:out.append(html.escape(line)+'\n');continue
  if line.startswith('#'):
   flush()
   if ul:out.append('</ul>');ul=False
   n=len(line)-len(line.lstrip('#'));out.append(f'<h{min(n,6)}>'+inline(line[n:].strip())+f'</h{min(n,6)}>')
  elif re.match(r'^(- |\d+\. )',line):
   flush()
   if not ul:out.append('<ul>');ul=True
   out.append('<li>'+inline(re.sub(r'^(- |\d+\. )','',line))+'</li>')
  elif not line.strip():
   flush()
   if ul:out.append('</ul>');ul=False
  else:paragraph.append(line)
 flush();flush_table()
 if ul:out.append('</ul>')
 return ''.join(out)

def write(mdpath,outpath,back='../index.html',css='../style.css'):
 md=mdpath.read_text();title=md.splitlines()[0].lstrip('# ')
 outpath.write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="stylesheet" href="{css}"></head><body class="report-page"><a href="{back}">← 返回观察笔记</a><main>{render(md)}</main><p><a href="{mdpath.name}">Markdown原文</a></p></body></html>')

for f in WR.glob('*.md'):write(f,f.with_suffix('.html'))
if (R/'WEB-README.md').exists():write(R/'WEB-README.md',R/'WEB-README.html','index.html','style.css')
figures=[]
for name,label in [('v1-desktop.jpg','首版结构占位：未接模型，不可作为产物。'),('v2-desktop.jpg','真实候选布局：修复图片固有尺寸造成的裁切，尚未冻结。'),('final-desktop.jpg','最终模型接入后的完整首屏。')]:
 if (WR/name).exists():figures.append(f'<figure><img src="web-review/{name}" alt="{label}" width="1173" height="751" loading="lazy"><figcaption>{label}</figcaption></figure>')
case='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>007 · 网页前后与复盘</title><link rel="stylesheet" href="style.css"></head><body class="report-page"><a href="index.html">← 返回观察笔记</a><main><p class="eyebrow">WEB DESIGN / ORISON 007</p><h1>让空处成为阅读的主角。</h1><p>不是模型查看器换肤，而是一次从真实投影进入形体的观察：正面看见内空，侧面看见遮挡，最后回到闭合与几何证据。</p>'+''.join(figures)+'<h2>判断与证据分开</h2><ul><li><a href="web-review/reference-notes.html">真实外部网页后评审</a> — 日期、实际观察、推断、采用与不采用。</li><li><a href="web-review/design-review.html">设计评审与修订</a> — 保留首版与实际发现。</li><li><a href="web-review/browser-qa.html">原生浏览器局部验收</a> — 不借模拟结论冒称GPU/真机。</li><li><a href="web-review/reflection.html">本轮复盘</a> — 留给下一轮的方法。</li></ul></main></body></html>'
(R/'design-case.html').write_text(case)
print('Rendered 007 web review pages')
