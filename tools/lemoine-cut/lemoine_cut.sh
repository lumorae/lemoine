#!/usr/bin/env bash
# lemoine_cut.sh — cut a raw clip into a branded "lemoine cut":
#   optional trim, brand lower-third overlay (alpha .mov), hall reverb on audio,
#   loudness normalized, h264 + aac, faststart.
#
# Usage:
#   ./lemoine_cut.sh -i input.mov -o output.mp4 -l lower3-alpha.mov \
#       [-s start_sec] [-e end_sec] [-a] [-w wet_db] [-t lower3_start_sec]
#
#   -s/-e  trim window in seconds (defaults: full clip)
#   -a     auto-trim: detect leading/trailing silence and cut with 1s padding
#   -w     reverb wet level in dB relative to dry (default -12)
#   -t     when the lower third appears, seconds into the cut (default 0.8)
set -euo pipefail

IN="" OUT="" LOWER3="" START="" END="" AUTOTRIM=0 WET_DB=-12 L3_AT=0.8
while getopts "i:o:l:s:e:aw:t:" opt; do
  case $opt in
    i) IN=$OPTARG;; o) OUT=$OPTARG;; l) LOWER3=$OPTARG;;
    s) START=$OPTARG;; e) END=$OPTARG;; a) AUTOTRIM=1;;
    w) WET_DB=$OPTARG;; t) L3_AT=$OPTARG;;
    *) exit 2;;
  esac
done
[[ -n $IN && -n $OUT && -n $LOWER3 ]] || { echo "need -i -o -l" >&2; exit 2; }

HERE=$(cd "$(dirname "$0")" && pwd)
IR="$HERE/ir-hall.wav"
[[ -f $IR ]] || python3 "$HERE/make_ir.py" --out "$IR"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if [[ $AUTOTRIM == 1 && -z $START ]]; then
  # find first/last non-silent audio, pad by 1s
  SIL=$(ffmpeg -i "$IN" -af "silencedetect=noise=-35dB:d=0.6" -f null - 2>&1 | grep -E "silence_(start|end)" || true)
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  FIRST_END=$(echo "$SIL" | grep silence_end | head -1 | sed -E 's/.*silence_end: ([0-9.]+).*/\1/') || true
  LAST_START=$(echo "$SIL" | grep silence_start | tail -1 | sed -E 's/.*silence_start: ([0-9.]+).*/\1/') || true
  FIRST_SIL_START=$(echo "$SIL" | grep silence_start | head -1 | sed -E 's/.*silence_start: ([0-9.]+).*/\1/') || true
  START=0; END=$DUR
  # only trim head if the clip actually starts silent
  if [[ -n ${FIRST_SIL_START:-} ]] && python3 -c "exit(0 if float('$FIRST_SIL_START') < 0.5 else 1)"; then
    [[ -n ${FIRST_END:-} ]] && START=$(python3 -c "print(max(0, float('$FIRST_END') - 1.0))")
  fi
  # only trim tail if the last silence runs to the end of the clip
  if [[ -n ${LAST_START:-} ]] && python3 -c "exit(0 if float('$DUR') - float('$LAST_START') > 1.2 else 1)"; then
    END=$(python3 -c "print(min(float('$DUR'), float('$LAST_START') + 1.0))")
  fi
  echo "auto-trim: $START -> $END (of $DUR)"
fi

TRIM_IN=()
[[ -n $START ]] && TRIM_IN+=(-ss "$START")
[[ -n $END ]] && { E=$END; S=${START:-0}; TRIM_IN+=(-t "$(python3 -c "print(float('$E')-float('$S'))")"); }

# 1) extract trimmed audio, 2) convolution reverb in python
# iPhone clips carry an extra spatial-audio track ffmpeg can't decode — take a:0
ffmpeg -y -v error "${TRIM_IN[@]}" -i "$IN" -map 0:a:0 -vn -ac 2 -ar 48000 -c:a pcm_s16le "$WORK/dry.wav"
python3 "$HERE/reverb.py" --in "$WORK/dry.wav" --ir "$IR" --out "$WORK/wetmix.wav" --wet-db "$WET_DB"

# 3) video with lower third + processed audio, loudness normalized for social
# (frame 0 of the overlay is fully transparent, so pre-start extension is invisible)
FILTER_V="[1:v]setpts=PTS+${L3_AT}/TB[l3];\
[l3][0:v:0]scale2ref=w=iw:h=ih[l3s][base];\
[base][l3s]overlay=x=0:y=0:eof_action=pass:format=auto[vout]"

ffmpeg -y "${TRIM_IN[@]}" -i "$IN" -i "$LOWER3" -i "$WORK/wetmix.wav" \
  -filter_complex "$FILTER_V;[2:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart \
  "$OUT"
echo "done: $OUT"
