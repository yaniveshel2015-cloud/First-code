#!/bin/bash
# Final renders with the utility pillars on the street front.
SP=/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad
cd "$SP/villa84" || exit 1
OUT="$SP/villa84/out/r3d/final4"
mkdir -p "$OUT"
for v in street cut_B cut_G aerial_front cut_F top aerial_side aerial_back; do
  case "$v" in
    cut_*) S=56 ;;
    top) S=48 ;;
    *) S=72 ;;
  esac
  "$SP/bvenv/bin/python" scene84_p4.py --data "$SP/villa84/out/model3d_final.json" --view "$v" --res 1600x1000 --samples "$S" --out "$OUT/$v.png" > "$OUT/$v.log" 2>&1
  echo "done $v $(date +%H:%M:%S)"
done
echo PASS4_DONE
