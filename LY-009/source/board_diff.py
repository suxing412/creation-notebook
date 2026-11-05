"""Compare two taskboard.v2.json snapshots (read-only).

python -I board_diff.py <old.json> <new.json>
Prints status changes, newly 可开工 seats, G state, and pause/lock reference changes as JSON.
"""
import json, sys

old = json.load(open(sys.argv[1], encoding='utf-8'))
new = json.load(open(sys.argv[2], encoding='utf-8'))
o = {s['id']: s for s in old['seats']}
n = {s['id']: s for s in new['seats']}
changes = []
for sid in sorted(set(o) | set(n)):
    a, b = o.get(sid), n.get(sid)
    if a is None or b is None:
        changes.append({'seat': sid, 'change': 'added' if a is None else 'removed'})
        continue
    if a['status'] != b['status'] or a['pauses'] != b['pauses'] or a['locks'] != b['locks']:
        changes.append({'seat': sid, 'status': [a['status'], b['status']],
                        'pauses': [a['pauses'], b['pauses']] if a['pauses'] != b['pauses'] else None,
                        'locks': [a['locks'], b['locks']] if a['locks'] != b['locks'] else None,
                        'evidence': (b.get('statusEvidence') or {}).get('statusFile')})
print(json.dumps({
    'old': old.get('generatedAt'), 'new': new.get('generatedAt'),
    'G': [old['G'], new['G']],
    'counts': [old['counts'], new['counts']],
    'newlyReady': [c['seat'] for c in changes if c.get('status') and c['status'][1] == '可开工' and c['status'][0] != '可开工'],
    'changes': changes,
}, ensure_ascii=False, indent=1))
