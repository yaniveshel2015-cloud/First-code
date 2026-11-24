#!/bin/bash
# Third pass: views rendered before the path behind the pool deck was added. Starts when pass two has finished.
SP=/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad
cd "$SP/villa84" || exit 1
OUT="$SP/villa84/out/r3d/final2"
mkdir -p "$OUT"
until grep -q PASS2_DONE "$OUT/batch.log"; do sleep 5; done
for v in garden cut_G cut_F; do
  case "$v" in
    cut_*) S=56 ;;
    *) S=72 ;;
  esac
  "$SP/bvenv/bin/python" scene84_p2.py --data "$SP/villa84/out/model3d_final.json" --view "$v" --res 1600x1000 --samples "$S" --out "$OUT/$v.png" > "$OUT/$v.log" 2>&1
  echo "done $v $(date +%H:%M:%S)"
done
echo PASS3_DONE
