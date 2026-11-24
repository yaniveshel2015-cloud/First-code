#!/bin/bash
# Final renders of the villa on plot 84 (frozen copies of the scene script and data).
SP=/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad
cd "$SP/villa84" || exit 1
OUT="$SP/villa84/out/r3d/final"
for v in cut_G cut_B cut_F aerial_front street garden aerial_back terrace top aerial_side; do
  case "$v" in
    cut_*) S=56 ;;
    top) S=48 ;;
    *) S=72 ;;
  esac
  if [ ! -f "$OUT/$v.png" ]; then
    "$SP/bvenv/bin/python" scene84_final.py --data "$SP/villa84/out/model3d_final.json" --view "$v" --res 1600x1000 --samples "$S" --out "$OUT/$v.png" > "$OUT/$v.log" 2>&1
  fi
  echo "done $v $(date +%H:%M:%S)"
done
echo ALL_DONE
