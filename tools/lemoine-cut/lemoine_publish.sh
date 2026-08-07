#!/usr/bin/env bash
# lemoine_publish.sh — one command from a Drive link to platform-ready cuts.
#
#   ./lemoine_publish.sh <drive-url-or-local-file> [-g brands|dontblend] [-T "title"] [-p reels|shorts|both]
#
# Produces, from one raw vertical clip:
#   <slug>-reels.mp4   Instagram Reels: intro + lower third + outro end-card,
#                      reverb, ring-out, silent-until-reveal audio
#   <slug>-shorts.mp4  YouTube Shorts: no intro/outro, raised lower third,
#                      breath-to-breath trim + ambience-matched loop seam
#
# Title defaults to the Drive file name (lowercased, dashes normalized).
# Tagline (-g) picks the Reels end-card; default: brands ("brands that don't
# blend in.") — override with -g brands. Uploads to the Drive Cut folder automatically when
# gdrive-sa.json is configured (see drive_upload.py).
# -p limits which platform cut(s) get rendered (default: both).
# Filenames are stamped with date+time (not just date) since the same flute
# often gets several clips cut on the same day, which used to collide.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
# restore the Drive key from a persistent env var if the file is missing
if [[ ! -f "$HERE/gdrive-sa.json" && -n ${GDRIVE_SA_JSON_B64:-} ]]; then
  echo "$GDRIVE_SA_JSON_B64" | base64 -d > "$HERE/gdrive-sa.json" 2>/dev/null || true
fi
SRC="" TAGLINE="dontblend" TITLE="" PLATFORM="both"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -g) TAGLINE=$2; shift 2;;
    -T) TITLE=$2; shift 2;;
    -p) PLATFORM=$2; shift 2;;
    *) SRC=$1; shift;;
  esac
done
[[ -n $SRC ]] || { echo "usage: $0 <drive-url-or-file> [-g brands|dontblend] [-T title] [-p reels|shorts|both]" >&2; exit 2; }
case "$PLATFORM" in reels|shorts|both) ;; *) echo "-p must be reels, shorts, or both" >&2; exit 2;; esac

WORKDIR=${LEMOINE_WORKDIR:-$(pwd)}
cd "$WORKDIR"

# 1) fetch the clip (Drive links must be link-shared: anyone with the link)
if [[ $SRC == http* ]]; then
  ID=$(echo "$SRC" | grep -oE '(file/d/|id=)[A-Za-z0-9_-]{20,}' | head -1 | sed -E 's/(file\/d\/|id=)//')
  [[ -n $ID ]] || { echo "could not parse a Drive file id from: $SRC" >&2; exit 2; }
  echo "downloading Drive file $ID ..."
  CA=${CURL_CA_BUNDLE:-/root/.ccr/ca-bundle.crt}
  curl -sSL ${CA:+--cacert "$CA"} -D /tmp/lp-headers.txt -o /tmp/lp-clip.bin \
    "https://drive.usercontent.google.com/download?id=${ID}&export=download&confirm=t"
  FNAME=$(grep -io 'filename="[^"]*"' /tmp/lp-headers.txt | tail -1 | sed 's/filename="//; s/"//')
  [[ -n $FNAME ]] || { echo "no filename in response — is the file link-shared?" >&2; exit 2; }
  file /tmp/lp-clip.bin | grep -qi 'iso media\|quicktime' || { echo "download is not a video — is the file link-shared?" >&2; exit 2; }
  mv /tmp/lp-clip.bin "$FNAME"
  SRC=$FNAME
fi

# 2) title from filename unless overridden: lowercase, em/long dashes -> en dash
BASE=$(basename "$SRC")
BASE="${BASE%.*}"
[[ -n $TITLE ]] || TITLE=$(python3 - "$BASE" <<'EOF'
import sys
t = sys.argv[1].replace("—", "–").replace(" - ", " – ")
print(t.lower().strip())
EOF
)
SLUG=$(python3 -c "import sys,re; print(re.sub(r'[^a-z0-9]+','-',sys.argv[1].lower()).strip('-'))" "$TITLE")
DATE=$(date +%Y-%m-%d)
STAMP=$(date +%Y-%m-%d_%H%M)   # date+time in the filename: same flute, same day, no collisions
export LEMOINE_DRIVE_SUBFOLDER="$(date +%Y-%m)/${DATE}"   # cuts auto-file into Cut/YYYY-MM/YYYY-MM-DD/
echo "title: [ $TITLE ]   slug: $SLUG   tagline: $TAGLINE   stamp: $STAMP   platform: $PLATFORM"

# 3) lower thirds for this title (standard + raised-for-Shorts)
python3 "$HERE/make_lower3.py" --text "$TITLE" --orientation vertical --outdir . >/dev/null
python3 "$HERE/make_lower3.py" --text "$TITLE" --orientation vertical-yt --outdir . >/dev/null
L3=$(ls -t lemoine-lower3-*-1080x1920-alpha.mov | head -1)
L3YT=$(ls -t lemoine-lower3-*-1080x1920-yt-alpha.mov | head -1)

# 4) brand overlays (cached; regenerate only when missing)
INTRO=lemoine-intro-pixel-1080x1920-alpha.mov
OUTRO=lemoine-outro-pixel-${TAGLINE}-1080x1920-alpha.mov
[[ -f $INTRO ]] || PYTHONPATH="$HERE" python3 "$HERE/make_intro.py" \
  --template "${LEMOINE_LOGO_TEMPLATE:-lemoine-outro-vertical-1080x1920-alpha-iphone.mov}" --outdir . >/dev/null
if [[ ! -f $OUTRO ]]; then
  EC=$([[ $TAGLINE == brands ]] && echo endcard-brands-that-dont-blend-in-1080x1920.png \
                                 || echo endcard-dont-blend-in-1080x1920.png)
  python3 "$HERE/make_outro.py" --endcard "$HERE/endcards/$EC" --name "$TAGLINE" --outdir . >/dev/null
fi

# 5) the requested platform cut(s)
if [[ $PLATFORM == reels || $PLATFORM == both ]]; then
  bash "$HERE/lemoine_cut.sh" -i "$SRC" -o "${STAMP}_${SLUG}_reels.mp4"  -l "$L3"   -I "$INTRO" -O "$OUTRO"
fi
if [[ $PLATFORM == shorts || $PLATFORM == both ]]; then
  bash "$HERE/lemoine_cut.sh" -i "$SRC" -o "${STAMP}_${SLUG}_shorts.mp4" -l "$L3YT"
fi

echo ""
echo "ready (also filed to Drive Cut/${LEMOINE_DRIVE_SUBFOLDER}/):"
if [[ $PLATFORM == reels || $PLATFORM == both ]]; then
  echo "  ${STAMP}_${SLUG}_reels.mp4   (instagram: intro + end-card '$TAGLINE')"
fi
if [[ $PLATFORM == shorts || $PLATFORM == both ]]; then
  echo "  ${STAMP}_${SLUG}_shorts.mp4  (youtube shorts: clean loop, raised lower third)"
fi
