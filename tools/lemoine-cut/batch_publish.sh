#!/usr/bin/env bash
# batch_publish.sh — cut several clips, one after another, surviving restarts.
#
#   bash batch_publish.sh <workdir> <jobs.tsv>
#
# jobs.tsv, one cut per line, TAB separated (blank lines and # comments ok):
#   id    source-file    flute-folder    title    [extra lemoine_publish flags]
#   1606  src/IMG_1606.MOV  Stellar Flute D  nervous system reset in D
#   1603  src/IMG_1603.MOV  Quena Red Band   andean quena meditation in G   -bw
#
# The flute column is passed as LEMOINE_FLUTE, so every cut is filed by the
# flute actually identified, never by what the title happens to say. Use "-"
# to let categories.py route by title instead.
#
# WHY SEQUENTIAL. All runs share <workdir>; two at once overwrite each other's
# scratch frames (2026-09-22: a parallel run deleted the outro frames mid-read
# and killed a cut). One at a time, always.
#
# WHY RESUMABLE. The cloud container is restarted without warning, sometimes
# several times an hour, killing whatever is running. A job counts as done
# once its log shows the video UPLOADED, so re-running this script after a
# restart skips finished cuts and never uploads a video twice. A run killed
# before upload leaves at most a partial local .mp4, which is deleted and
# redone. Progress goes to <workdir>/runner.txt; ALL_DONE is its last line.
#
# Wait on runner.txt, never on process names: a `pgrep -f` pattern matches
# the shell running the pgrep itself, and once matched a literal "(01)" as a
# regex group instead of a filename. Both mistakes have happened here.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=$1; JOBS=$2
[[ -d $W && -f $JOBS ]] || { echo "usage: $0 <workdir> <jobs.tsv>" >&2; exit 2; }
cd "$W"
echo "start $(date -u +%FT%TZ)" >> runner.txt

while IFS=$'\t' read -r id src flute title extra || [[ -n ${id:-} ]]; do
  [[ -z ${id// } || ${id:0:1} == "#" ]] && continue
  log="log_${id}.txt"
  if grep -aq "uploaded: .*_shorts.mp4\|uploaded: .*_reels.mp4" "$log" 2>/dev/null; then
    echo "skip $id (already uploaded)" >> runner.txt; continue
  fi
  # a previous run of this job died before upload: clear its partial output
  if [[ -f $log ]]; then
    slug=$(sed -n 's/.*slug: \([^ ]*\).*/\1/p' "$log" | head -1)
    [[ -n $slug ]] && rm -f ./*_"${slug}"_shorts.mp4 ./*_"${slug}"_reels.mp4
  fi
  # shellcheck disable=SC2086  # extra flags are meant to word-split
  if [[ $flute == "-" ]]; then
    LEMOINE_WORKDIR=$W bash "$HERE/lemoine_publish.sh" "$src" -T "$title" ${extra:-} > "$log" 2>&1
  else
    LEMOINE_WORKDIR=$W LEMOINE_FLUTE="$flute" bash "$HERE/lemoine_publish.sh" "$src" -T "$title" ${extra:-} > "$log" 2>&1
  fi
  rc=$?
  if grep -aq "uploaded: .*_shorts.mp4\|uploaded: .*_reels.mp4" "$log"; then st=ok; else st="FAILED (exit $rc, see $log)"; fi
  echo "$st $id" >> runner.txt
done < "$JOBS"
echo ALL_DONE >> runner.txt
