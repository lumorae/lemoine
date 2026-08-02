#!/usr/bin/env bash
# lemoine_cut.sh — cut a raw clip into a branded "lemoine cut":
#   optional trim, HDR→SDR tone-map, brand lower-third overlay (alpha .mov),
#   hall reverb, loudness normalize, h264 + aac, faststart, BT.709 tagged.
#
# Usage:
#   ./lemoine_cut.sh -i input.mov -o output.mp4 -l lower3-alpha.mov \
#       [-s start_sec] [-e end_sec] [-a] [-w wet_db] [-t lower3_start_sec] \
#       [-k] [-q crf]
#
#   -s/-e  trim window in seconds (defaults: full clip)
#   -a     auto-trim: detect leading/trailing silence and cut with 1s padding
#   -w     reverb wet level in dB relative to dry (default -12)
#   -t     when the lower third appears, seconds into the cut (default 0.8)
#   -k     keep source resolution (default: deliver at 1080p for speed/size)
#   -q     x264 crf (default 19)
#   -O     pixel-explosion outro overlay (.mov with alpha); plays after the
#          footage on a frozen last frame while the last note rings out
#   -I     pixel-explosion intro overlay (.mov with alpha); plays at t=0
set -euo pipefail

IN="" OUT="" LOWER3="" START="" END="" AUTOTRIM=0 WET_DB=-12 L3_AT="" KEEP_RES=0 CRF=19 OUTRO="" INTRO=""
while getopts "i:o:l:s:e:aw:t:kq:O:I:" opt; do
  case $opt in
    i) IN=$OPTARG;; o) OUT=$OPTARG;; l) LOWER3=$OPTARG;;
    s) START=$OPTARG;; e) END=$OPTARG;; a) AUTOTRIM=1;;
    w) WET_DB=$OPTARG;; t) L3_AT=$OPTARG;; k) KEEP_RES=1;; q) CRF=$OPTARG;;
    O) OUTRO=$OPTARG;; I) INTRO=$OPTARG;;
    *) exit 2;;
  esac
done
[[ -n $IN && -n $OUT && -n $LOWER3 ]] || { echo "need -i -o -l" >&2; exit 2; }

HERE=$(cd "$(dirname "$0")" && pwd)
IR="$HERE/ir-hall.wav"
[[ -f $IR ]] || python3 "$HERE/make_ir.py" --out "$IR"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

read -r SRC_W SRC_H SRC_TRC < <(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,color_transfer -of csv=p=0 "$IN" | tr ',' ' ')

if [[ $AUTOTRIM == 1 && -z $START ]]; then
  # find first/last non-silent audio, pad by 1s (audio-only decode: fast)
  SIL=$(ffmpeg -i "$IN" -map 0:a:0 -vn -af "silencedetect=noise=-35dB:d=0.6" -f null - 2>&1 | grep -E "silence_(start|end)" || true)
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

CLIP_DUR=$(python3 -c "
s = float('${START:-0}' or 0)
e = '${END:-}'
print((float(e) if e else $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")) - s)")
OUTRO_DUR=0
[[ -n $OUTRO ]] && OUTRO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTRO")
INTRO_DUR=0
[[ -n $INTRO ]] && INTRO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$INTRO")
# lower third by default appears just as the intro finishes dissolving
[[ -z $L3_AT ]] && L3_AT=$(python3 -c "print(max(0.8, $INTRO_DUR - 2.5))")

# 1) extract trimmed audio (a:0 — iPhone spatial track is undecodable), reverb
#    padded by the outro length; with an outro the final note rings out over it
ffmpeg -y -v error "${TRIM_IN[@]}" -i "$IN" -map 0:a:0 -vn -ac 2 -ar 48000 -c:a pcm_s16le "$WORK/dry.wav"
RING=()
if [[ -n $OUTRO ]]; then
  [[ -f "$HERE/ir-ring.wav" ]] || python3 "$HERE/make_ir.py" --out "$HERE/ir-ring.wav" --t60 4.8
  RING=(--ring-ir "$HERE/ir-ring.wav")
fi
python3 "$HERE/reverb.py" --in "$WORK/dry.wav" --ir "$IR" --out "$WORK/wetmix.wav" --wet-db "$WET_DB" --pad-sec "$OUTRO_DUR" "${RING[@]}"

# 2) video chain: optional downscale, HDR→SDR tone-map, overlay in RGB so the
#    brand colors pass through exactly once into BT.709
if [[ $KEEP_RES == 1 ]]; then
  OUT_W=$SRC_W; OUT_H=$SRC_H
elif (( SRC_H >= SRC_W )); then
  OUT_W=1080; OUT_H=1920
else
  OUT_W=1920; OUT_H=1080
fi
(( SRC_W < OUT_W )) && { OUT_W=$SRC_W; OUT_H=$SRC_H; }

case "$SRC_TRC" in
  arib-std-b67|smpte2084)
    echo "tone-mapping HDR ($SRC_TRC) -> BT.709 SDR"
    TOSDR="zscale=w=${OUT_W}:h=${OUT_H}:f=lanczos:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgba"
    ;;
  *)
    TOSDR="scale=${OUT_W}:${OUT_H}:flags=lanczos,format=rgba"
    ;;
esac

# build the RGB compositing chain: footage (+freeze), lower3, outro, intro
EXTRA_IN=()
IDX=3
if [[ -n $OUTRO ]]; then
  FV="[0:v:0]${TOSDR},tpad=stop_mode=clone:stop_duration=${OUTRO_DUR}[sdr];"
else
  FV="[0:v:0]${TOSDR}[sdr];"
fi
FV+="[1:v]format=rgba,setpts=PTS+${L3_AT}/TB[l3];\
[l3][sdr]scale2ref=w=iw:h=ih[l3s][base];\
[base][l3s]overlay=x=0:y=0:eof_action=pass:format=auto[mid]"
CUR="mid"
if [[ -n $OUTRO ]]; then
  FV+=";[${IDX}:v]format=rgba,setpts=PTS+${CLIP_DUR}/TB[og];\
[og][${CUR}]scale2ref=w=iw:h=ih[ogs][c${IDX}];\
[c${IDX}][ogs]overlay=x=0:y=0:eof_action=pass:format=auto[o${IDX}]"
  CUR="o${IDX}"; EXTRA_IN+=(-i "$OUTRO"); IDX=$((IDX+1))
fi
if [[ -n $INTRO ]]; then
  FV+=";[${IDX}:v]format=rgba[ig];\
[ig][${CUR}]scale2ref=w=iw:h=ih[igs][c${IDX}];\
[c${IDX}][igs]overlay=x=0:y=0:eof_action=pass:format=auto[o${IDX}]"
  CUR="o${IDX}"; EXTRA_IN+=(-i "$INTRO"); IDX=$((IDX+1))
fi
FILTER_V="$FV;[${CUR}]zscale=m=bt709:r=tv,format=yuv420p[vout]"

TOTAL=$(python3 -c "print($CLIP_DUR + $OUTRO_DUR)")
FILTER_A="[2:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=$(python3 -c "print($TOTAL-0.6)"):d=0.6[aout]"

ffmpeg -y "${TRIM_IN[@]}" -i "$IN" -i "$LOWER3" -i "$WORK/wetmix.wav" "${EXTRA_IN[@]}" \
  -filter_complex "$FILTER_V;$FILTER_A" \
  -map "[vout]" -map "[aout]" -shortest \
  -c:v libx264 -preset fast -crf "$CRF" \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart \
  "$OUT"
echo "done: $OUT"

# auto-save to Drive when a service-account key is configured
if [[ -f "$HERE/gdrive-sa.json" || -n ${GDRIVE_SA_JSON:-} ]]; then
  python3 "$HERE/drive_upload.py" --file "$OUT" || echo "drive upload failed (kept local)"
fi
