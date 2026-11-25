#!/bin/bash
# Final renders of plot 84 from the current model3d.json, then the room-name overlays on the open-floor views.
SP=/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad
cd "$SP/villa84" || exit 1
OUT="$SP/villa84/out/r3d/final"
mkdir -p "$OUT"
for v in cut_B cut_G cut_F aerial_front street garden aerial_back terrace top aerial_side; do
  case "$v" in
    cut_*) S=40 ;;
    top) S=40 ;;
    *) S=48 ;;
  esac
  "$SP/bvenv/bin/python" scene84.py --data "$SP/villa84/out/model3d.json" --view "$v" --res 1600x1000 --samples "$S" --out "$OUT/$v.png" > "$OUT/$v.log" 2>&1
  echo "done $v $(date +%H:%M:%S)"
done
node label.js "$OUT/cut_B.png" "$OUT/cut_B.png.labels.json" "$OUT/cut_B_labelled.png" "קומת מרתף" "משרד אדריכלים, חניון, חלק משפחתי ומקלט משותף"
node label.js "$OUT/cut_G.png" "$OUT/cut_G.png.labels.json" "$OUT/cut_G_labelled.png" "קומת קרקע" "מבואה, מטבח, פינת אוכל, סלון, בריכה וספא"
node label.js "$OUT/cut_F.png" "$OUT/cut_F.png.labels.json" "$OUT/cut_F_labelled.png" "קומה א׳" "חדרי שינה, חדרי רחצה וממ״ד"
echo ALL_DONE
