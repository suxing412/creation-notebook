#!/usr/bin/env python3
"""Render authored review Markdown into locally readable pages. No external services."""
from pathlib import Path
import html,re
R=Path(__file__).resolve().parents[1]
import argparse
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=R);a=p.parse_args();R=a.directory.resolve();WR=R/'web-review'
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

for f in WR.glob("*.md"):write(f,f.with_suffix(".html"))
if (R/"WEB-README.md").exists():write(R/"WEB-README.md",R/"WEB-README.html","index.html","style.css")
print("Rendered 008 authored web reports")
