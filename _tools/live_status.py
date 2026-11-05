"""Regenerate _summary/live-status.md from every LY-###/status.json (and prep/prep-status.json).

  python -I _tools/live_status.py
"""
import json, os, datetime, collections
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
board = {s['id']: s for s in json.load(open(os.path.join(W, 'taskboard.json'), encoding='utf-8'))['seats']}
rows, count = [], collections.Counter()
for sid in sorted(board):
    s = board[sid]
    st_path = os.path.join(W, sid, 'status.json'); pr_path = os.path.join(W, sid, 'prep', 'prep-status.json')
    if os.path.exists(st_path):
        st = json.load(open(st_path, encoding='utf-8')); status = st.get('status', '?'); note = (st.get('summary') or '')[:120]
    elif os.path.exists(pr_path):
        pr = json.load(open(pr_path, encoding='utf-8'))
        status = '准备完成·' + ('G后可开工' if pr.get('readyAfterG') else '缺输入'); note = ''
    else:
        status, note = '待输入', ''
    count[status.split('·')[0]] += 1
    rows.append(f"| {sid} | {s['title']} | {s['type']} | {status} | {note.replace('|', '/')} |")
now = datetime.datetime.now().astimezone().isoformat(timespec='minutes')
out = [f'# 任务池实时状态（自动生成，{now}）', '', '状态取自各席位 status.json；没有交付的席位显示准备阶段的结论。「交付完成/复用完成」的验收结论见各席目录与 _summary/gate-seats.md。', '',
       '汇总：' + '，'.join(f'{k} {v}' for k, v in count.most_common()), '', '| 席位 | 名称 | 类型 | 状态 | 摘要 |', '|---|---|---|---|---|'] + rows
open(os.path.join(W, '_summary', 'live-status.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(dict(count))
