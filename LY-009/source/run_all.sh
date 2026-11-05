#!/bin/sh
# LY-009 full re-run (read-only on everything except LY-009/). Run from the workpacks root:
#   sh LY-009/source/run_all.sh D:/GitHub/creation-notebook-lab bce3211 <scratch dir> [<user original TASKPOOL copy>]
set -e
LAB="$1"; BASE="$2"; SCRATCH="$3"; ORIG="$4"
ME=LY-009
rm -rf $ME/source/__pycache__
python -I $ME/source/parse_taskpool.py TASKPOOL.md $ME/qa/taskpool.parsed.json
python -I $ME/source/check_whitelist.py --scan . $ME/qa/whitelist-scan.json || true   # FAIL is reported, not fatal (PZ-14)
python -I $ME/source/build_board.py . "$LAB" "$BASE" $ME
python -I $ME/source/make_handover_example.py . $ME "$LAB" "$BASE"
python -I $ME/source/check_board.py . "$LAB" "$BASE" $ME "$SCRATCH" $ORIG
python -I $ME/source/render_board.py $ME
rm -rf $ME/source/__pycache__
