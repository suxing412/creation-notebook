#!/usr/bin/env bash
# LY-075 prep: reproduce the nine-room survey for all six mingtang GLBs (read-only on the lab repo).
# Usage: bash run_all.sh [lab_repo]   (default D:/GitHub/creation-notebook-lab)
set -euo pipefail
LAB=${1:-D:/GitHub/creation-notebook-lab}
F=$LAB/docs/library/models/m-luoyang-mingtang/files
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"; mkdir -p out
for v in A B; do
  fy=$([ $v = A ] && echo 1.2 || echo 0.9)
  for l in 0 1 2; do
    g=$F/mingtang-$v-LOD$l.glb
    sha256sum "$g"
    /d/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P raycast_columns.py -- "$g" "$HERE/out/$v$l-cols-0p05.npz" 0.05 | grep DONE
    python floor_map.py out/$v$l-cols-0p05.npz out/$v$l
    python section_obstacles.py "$g" out/$v$l-floor.npz out/$v$l-sect.npz $fy
    python rooms_reach.py out/$v$l-floor.npz out/$v$l-reach.json $v-LOD$l out/$v$l-sect.npz > out/$v$l-reach.log
  done
done
python posts.py $F/mingtang-A-LOD0.glb $F/mingtang-B-LOD0.glb $F/mingtang-A-LOD2.glb $F/mingtang-B-LOD2.glb $F/mingtang-A-LOD1.glb $F/mingtang-B-LOD1.glb > out/posts.log
grep -c "reached 9/9" out/*-reach.log
# acceptance checks T0-T9 / P1-P2 / N1-N3 per variant (exit 1 on any failure)
for v in A B; do
  python check_invariants.py --expect $v --reach out/${v}0-reach.json out/${v}1-reach.json out/${v}2-reach.json     --floor out/${v}0-floor.npz out/${v}1-floor.npz out/${v}2-floor.npz --posts out/posts.log     --glb $F/mingtang-$v-LOD0.glb $F/mingtang-$v-LOD1.glb $F/mingtang-$v-LOD2.glb --out out/check-$v.json | tail -1
done
# N5: B files judged against A expectations must FAIL
if python check_invariants.py --expect A --reach out/B0-reach.json out/B1-reach.json out/B2-reach.json     --floor out/B0-floor.npz out/B1-floor.npz out/B2-floor.npz --posts out/posts.log     --glb $F/mingtang-B-LOD0.glb $F/mingtang-B-LOD1.glb $F/mingtang-B-LOD2.glb --out out/neg-N5-B-as-A.json > /dev/null; then
  echo "N5 NOT REJECTED: checker broken"; exit 1; else echo "N5 rejected as expected"; fi
# N4: door-block injections on measurement copies (LOD0 of each variant)
mkdir -p out/neg
for v in A B; do python neg_door_block.py out/${v}0-floor.npz out/${v}0-sect.npz out/${v}0-reach.json out/neg ${v}0 | tail -1; done
# N6: vertical rays only -> report must say section null
python rooms_reach.py out/A0-floor.npz out/neg/A0-N6-vertical-only-reach.json A-LOD0-N6 - > /dev/null
python -c "import json,sys; d=json.load(open('out/neg/A0-N6-vertical-only-reach.json')); sys.exit(0 if d['section'] is None else 1)" && echo "N6 flagged vertical-only"
# per-item tables (section 4 format), every GLB
for v in A B; do for l in 0 1 2; do python make_item_table.py out/$v$l-reach.json out/check-$v.json out/posts.log mingtang-$v-LOD$l.glb out/items-$v$l.md > /dev/null; done; done
echo "items tables written"
