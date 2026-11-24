#!/bin/bash
# Second pass: reframed basement cutaway and the three aerial views with the tuned exposure. Starts when the first batch has finished.
SP=/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad
cd "$SP/villa84" || exit 1
OUT="$SP/villa84/out/r3d/final2"
mkdir -p "$OUT"
until grep -q ALL_DONE "$SP/villa84/out/r3d/final/batch.log"; do sleep 5; done
for v in cut_B aerial_front aerial_back aerial_side; do
  case "$v" in
    cut_*) S=56 ;;
    *) S=72 ;;
  esac
  "$SP/bvenv/bin/python" scene84_p2.py --data "$SP/villa84/out/model3d_final.json" --view "$v" --res 1600x1000 --samples "$S" --out "$OUT/$v.png" > "$OUT/$v.log" 2>&1
  echo "done $v $(date +%H:%M:%S)"
done
echo PASS2_DONE
