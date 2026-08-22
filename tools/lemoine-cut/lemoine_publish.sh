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
# Cuts are filed in Drive under Cut/<Flute>/ — see categories.py.
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
CLEAN_ARGS=()   # -c / -n fill this; stays empty for a clean studio recording
BW_ARGS=()      # -bw fills this; footage goes monochrome, overlays stay branded
while [[ $# -gt 0 ]]; do
  case "$1" in
    -g) TAGLINE=$2; shift 2;;
    -T) TITLE=$2; shift 2;;
    -p) PLATFORM=$2; shift 2;;
    -bw) BW_ARGS=(-B); shift;;                # monochrome footage, colour overlays
    -c) CLEAN_ARGS=(-C); shift;;              # noisy location recording
    -n) CLEAN_ARGS=(-C -n "$2"); shift 2;;    # ... with explicit denoise strength
    *) SRC=$1; shift;;
  esac
done
[[ -n $SRC ]] || { echo "usage: $0 <drive-url-or-file> [-g brands|dontblend] [-T title] [-p reels|shorts|both] [-c] [-n strength] [-bw]" >&2; exit 2; }
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

# 2) title from filename unless overridden: lowercase, em/long dashes -> en dash.
#    A trailing take marker — "(02)", "[2]", "take 2", "#2" — identifies which
#    take a clip is, so it belongs in the filename but never on screen; it is
#    split off here and re-attached to the slug below. A bare trailing number
#    is left alone: it's more likely part of the real title than a take.
BASE=$(basename "$SRC"); BASE="${BASE%.*}"
PARSED=$(python3 - "$BASE" "$TITLE" <<'EOF'
import re, sys
raw, override = sys.argv[1], sys.argv[2]
t = raw.replace("—", "–").replace(" - ", " – ").lower().strip()
m = re.search(r"[\s_-]*(?:\((?:take[\s_-]*)?#?(\d{1,2})\)"
              r"|\[(?:take[\s_-]*)?#?(\d{1,2})\]"
              r"|(?:take[\s_-]*|#)(\d{1,2}))\s*$", t)
take = ""
if m:
    take = next(g for g in m.groups() if g).zfill(2)
    t = t[:m.start()].strip(" –-_")

# A bracketed aside in the file name — "Ebonized Walnut Flute in A [San Diego]"
# — becomes a comma clause, because the lower third already draws its own
# "[ ... ]" around the whole title and a second pair nests badly on screen.
# This runs after the take split so a bracketed take like "[02]" is long gone.
t = re.sub(r"\s*\[\s*([^\]]+?)\s*\]", r", \1", t).strip(" ,")
t = re.sub(r"\s*,\s*", ", ", t)

# The musical key is capitalised on screen — "in Gm", "in A", "in F#" — but only
# the key letter itself: the mode stays lowercase ("Gm", not "GM" or "G Minor")
# and so does the "in".
#
# Earlier versions asked what SURROUNDS the key — first what follows it (end of
# title, then a comma, then any punctuation), then that it follows "in". Each
# new title shape found the gap the last fix left: "in A [San Diego]", then
# "in G melancholic", then "Double Drone, G", where a comma introduces the key
# and there is no "in" at all.
#
# So neither side is the signal — the letter is. B through G are never English
# words, so a standalone one anywhere in a title is a key, however it is
# introduced and whatever follows. "in bamboo", "in berlin" and "in cedar" are
# untouched because none of them contains a lone letter. "A" is the one
# exception, being also the article, so it alone must still be followed by
# punctuation or the end of the title; that keeps "in a church" lowercase.
KEY = re.compile(
    r"\b(?:"
    r"[b-g](?:#|b)?(?:\s*(?:m|min|minor|maj|major))?\b"
    r"|a(?:#|b)?(?:\s*(?:m|min|minor|maj|major))?\b(?=\s*$|\s*[^\sa-z0-9])"
    r")")
print(KEY.sub(lambda m: m.group(0)[0].upper() + m.group(0)[1:], override or t))
print(take)
EOF
)
TITLE=$(sed -n 1p <<<"$PARSED")
TAKE=$(sed -n 2p <<<"$PARSED")
SLUG=$(python3 -c "import sys,re; print(re.sub(r'[^a-z0-9]+','-',sys.argv[1].lower()).strip('-'))" "$TITLE")
SLUG="${SLUG}${TAKE:+-take${TAKE}}"
# the container clock runs UTC; dates/folders are filed on Johnny's local day
# (San Diego, Pacific) so a session after ~5pm PT doesn't get stamped tomorrow
export TZ="${LEMOINE_TZ:-America/Los_Angeles}"
DATE=$(date +%Y-%m-%d)
STAMP=$(date +%Y-%m-%d_%H%M)   # date+time in the filename: same flute, same day, no collisions
# Cuts file by flute, not by date: there are only so many flutes, and every take
# of one instrument belongs together. The date lives in the filename already.
export LEMOINE_DRIVE_SUBFOLDER="$(python3 - "$SLUG" "$TITLE" <<PYEOF
import sys
sys.path.insert(0, "$HERE")
from categories import folder_for
print(folder_for(sys.argv[1], sys.argv[2]))
PYEOF
)"
echo "title: [ $TITLE ]${TAKE:+   take: $TAKE}   slug: $SLUG   tagline: $TAGLINE   stamp: $STAMP   platform: $PLATFORM"
echo "flute: $LEMOINE_DRIVE_SUBFOLDER"
if [[ $LEMOINE_DRIVE_SUBFOLDER == Unsorted ]]; then
  echo "  ^ no flute in categories.py matches this title, so it is NOT being" >&2
  echo "    filed under an invented folder. Add it to FLUTES (or MAP) and" >&2
  echo "    re-run drive_migrate.py to put it where it belongs." >&2
fi

# 3) lower thirds for this title (standard + raised-for-Shorts)
python3 "$HERE/make_lower3.py" --text "$TITLE" --orientation vertical --outdir . >/dev/null
python3 "$HERE/make_lower3.py" --text "$TITLE" --orientation vertical-yt --outdir . >/dev/null
L3=$(ls -t lemoine-lower3-*-1080x1920-alpha.mov | head -1)
L3YT=$(ls -t lemoine-lower3-*-1080x1920-yt-alpha.mov | head -1)

# 4) brand overlays (cached; regenerate only when missing)
INTRO=lemoine-intro-pixel-1080x1920-alpha.mov
OUTRO=lemoine-outro-pixel-${TAGLINE}-1080x1920-alpha.mov
# the logo master ships with the repo; a stray copy in the workdir still wins so
# a one-off variant can be dropped in, but a fresh workdir no longer breaks
LOGO_MASTER=lemoine-outro-vertical-1080x1920-alpha-iphone.mov
[[ -f $LOGO_MASTER ]] || LOGO_MASTER="$HERE/brand-assets/lemoine-outro-vertical-1080x1920-alpha-iphone.mov"
[[ -f $INTRO ]] || PYTHONPATH="$HERE" python3 "$HERE/make_intro.py" \
  --template "${LEMOINE_LOGO_TEMPLATE:-$LOGO_MASTER}" --outdir . >/dev/null
if [[ ! -f $OUTRO ]]; then
  EC=$([[ $TAGLINE == brands ]] && echo endcard-brands-that-dont-blend-in-1080x1920.png \
                                 || echo endcard-dont-blend-in-1080x1920.png)
  python3 "$HERE/make_outro.py" --endcard "$HERE/endcards/$EC" --name "$TAGLINE" --outdir . >/dev/null
fi

# 5) the requested platform cut(s)
if [[ $PLATFORM == reels || $PLATFORM == both ]]; then
  bash "$HERE/lemoine_cut.sh" -i "$SRC" -o "${STAMP}_${SLUG}_reels.mp4"  -l "$L3"   -I "$INTRO" -O "$OUTRO" "${CLEAN_ARGS[@]}" "${BW_ARGS[@]}"
fi
if [[ $PLATFORM == shorts || $PLATFORM == both ]]; then
  bash "$HERE/lemoine_cut.sh" -i "$SRC" -o "${STAMP}_${SLUG}_shorts.mp4" -l "$L3YT" "${CLEAN_ARGS[@]}" "${BW_ARGS[@]}"
fi

# 6) refresh Cut/INDEX.md so the catalogue never drifts from what's on Drive
if [[ -f "$HERE/gdrive-sa.json" || -n ${GDRIVE_SA_JSON:-} ]]; then
  python3 "$HERE/drive_index.py" --out "$WORKDIR/INDEX.md" || echo "index rebuild failed (cuts are still uploaded)"
fi

echo ""
echo "ready (also filed to Drive Cut/${LEMOINE_DRIVE_SUBFOLDER}/):"
if [[ $PLATFORM == reels || $PLATFORM == both ]]; then
  echo "  ${STAMP}_${SLUG}_reels.mp4   (instagram: intro + end-card '$TAGLINE')"
fi
if [[ $PLATFORM == shorts || $PLATFORM == both ]]; then
  echo "  ${STAMP}_${SLUG}_shorts.mp4  (youtube shorts: clean loop, raised lower third)"
fi
