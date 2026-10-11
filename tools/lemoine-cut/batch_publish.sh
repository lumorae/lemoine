#!/usr/bin/env bash
# batch_publish.sh — cut several clips, one after another, surviving restarts.
#
#   bash batch_publish.sh <workdir> <jobs.tsv>
#
# jobs.tsv, one cut per line, columns separated by a TAB character (shown
# here as <TAB>; spaces do not work). Blank lines and # comments are fine:
#   id<TAB>source-file<TAB>flute-folder<TAB>title[<TAB>extra lemoine_publish flags]
#   1606<TAB>src/IMG_1606.MOV<TAB>Stellar Flute D<TAB>nervous system reset in D
#   1603<TAB>src/IMG_1603.MOV<TAB>Quena Jayras<TAB>andean quena meditation in G<TAB>-bw
#
# The flute column is passed as LEMOINE_FLUTE, so every cut is filed by the
# flute actually identified, never by what the title happens to say. Use "-"
# to let categories.py route by title instead. Extra flags are split on
# spaces ("-bw -c"), so a flag value cannot contain a space.
#
# Run it in the background and let its exit be the signal; its last line in
# runner.txt is "ALL_DONE ok=.. skipped=.. partial=.. failed=..". It exits 0
# only when every job is complete.
#
# WHY SEQUENTIAL. All runs share <workdir>; two at once overwrite each other's
# scratch frames (2026-09-22: a parallel run deleted the outro frames mid-read
# and killed a cut). One at a time, always, and a lock (runner.lock) refuses a
# second runner on the same workdir while the first is alive. The kernel drops
# the lock when a runner is killed, so re-running after a restart just works.
#
# WHY THE JOBS ARE READ ON FD 3. ffmpeg reads keystrokes from stdin while it
# encodes. When the job list was stdin, the first job's ffmpeg ate the rest of
# it: a "c" opened ffmpeg's command prompt and swallowed the next line, so
# that job silently never ran, and a "q" ended an encode early with exit 0,
# so a SHORT cut was uploaded and counted as done. Jobs now come from fd 3 and
# every job runs with stdin from /dev/null (and every ffmpeg has -nostdin).
#
# WHY RESUMABLE. The cloud container is restarted without warning, killing
# whatever is running. A job counts as done only when its log ends with
# lemoine_publish.sh's PUBLISH_COMPLETE line, so re-running this script after
# a restart skips finished cuts and re-does the rest. A job killed AFTER a
# video reached Drive but before the rest of it did (the thumbnail, or the
# shorts cut of a -p both job) is reported as PARTIAL and left alone, because
# redoing it would upload a second copy of the video; finish it by hand.
#
# Each log starts with the job's own row. If the row has changed since (a new
# flute, a new title), the old log is kept as log_<id>.<n>.txt and the job is
# cut again, and runner.txt says the earlier cut is still on Drive to trash.
#
# Wait on the runner's exit or on runner.txt, never on process names: a
# `pgrep -f` pattern matches the shell running the pgrep itself, and once
# matched a literal "(01)" as a regex group instead of a filename.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
usage() { echo "usage: $0 <workdir> <jobs.tsv>" >&2; exit 2; }
[[ $# -eq 2 ]] || usage
# absolute paths BEFORE the cd: a relative jobs.tsv used to be looked up again
# from inside the workdir, not found, and reported as ALL_DONE with no jobs
W=$(realpath -e "$1" 2>/dev/null) && [[ -d $W ]] || usage
JOBS=$(realpath -e "$2" 2>/dev/null) && [[ -f $JOBS ]] || usage
cd "$W"

exec 9>"$W/runner.lock"
if ! flock -n 9; then
  echo "another batch_publish.sh is already running in $W; wait for it" >&2
  exit 3
fi
# lemoine_cut.sh scratch: nothing in it can be live while we hold the lock
export LEMOINE_TMP="$W/.tmp"
rm -rf "$LEMOINE_TMP"

echo "start $(date -u +%FT%TZ) $JOBS" >> runner.txt
ok=0 skipped=0 partial=0 failed=0

while IFS=$'\t' read -r -u 3 id src flute title extra || [[ -n ${id:-} ]]; do
  [[ -z ${id// } || ${id:0:1} == "#" ]] && continue
  row="$id"$'\t'"$src"$'\t'"$flute"$'\t'"$title"$'\t'"${extra:-}"
  log="log_${id}.txt"

  if [[ -f $log ]]; then
    first=$(head -n1 "$log")
    if [[ $first == job$'\t'* && $first != "job"$'\t'"$row" ]]; then
      n=1; while [[ -e log_${id}.$n.txt ]]; do n=$((n + 1)); done
      mv "$log" "log_${id}.$n.txt"
      if grep -aq "^uploaded: .*\.mp4" "log_${id}.$n.txt"; then
        echo "note $id: row changed; cutting again. The earlier cut is still on Drive (see log_${id}.$n.txt): trash it once the new one is verified" >> runner.txt
      else
        echo "note $id: row changed; cutting again (old log kept as log_${id}.$n.txt)" >> runner.txt
      fi
    elif grep -aq "^PUBLISH_COMPLETE" "$log"; then
      echo "skip $id (already complete)" >> runner.txt; skipped=$((skipped + 1)); continue
    elif [[ $first != job$'\t'* ]] && grep -aq "uploaded: .*_shorts.mp4\|uploaded: .*_reels.mp4" "$log"; then
      # a log from before PUBLISH_COMPLETE existed: its upload line is all we have
      echo "skip $id (already uploaded, older log)" >> runner.txt; skipped=$((skipped + 1)); continue
    elif grep -aq "^uploaded: .*\.mp4" "$log"; then
      echo "PARTIAL $id: a video is on Drive but the job did not finish ($(grep -a '^PUBLISH_INCOMPLETE' "$log" | tail -1 || true)); finish by hand, see $log" >> runner.txt
      partial=$((partial + 1)); continue
    else
      # died before anything reached Drive: clear only ITS partial output
      stamp=$(sed -n 's/.*  stamp: \([^ ]*\).*/\1/p' "$log" | head -1)
      slug=$(sed -n 's/.*  slug: \([^ ]*\).*/\1/p' "$log" | head -1)
      [[ -n $stamp && -n $slug ]] && rm -f "./${stamp}_${slug}_shorts.mp4" "./${stamp}_${slug}_reels.mp4"
    fi
  fi

  if [[ ! -f $src ]]; then
    printf 'job\t%s\nno such source file: %s\n' "$row" "$src" > "$log"
    echo "FAILED $id (no such source: $src)" >> runner.txt; failed=$((failed + 1)); continue
  fi
  {
    printf 'job\t%s\n' "$row"
    if [[ $flute == "-" ]]; then
      # shellcheck disable=SC2086  # extra flags are meant to word-split
      LEMOINE_WORKDIR=$W bash "$HERE/lemoine_publish.sh" "$src" -T "$title" ${extra:-} < /dev/null
    else
      # shellcheck disable=SC2086
      LEMOINE_WORKDIR=$W LEMOINE_FLUTE="$flute" bash "$HERE/lemoine_publish.sh" "$src" -T "$title" ${extra:-} < /dev/null
    fi
  } > "$log" 2>&1
  rc=$?
  if grep -aq "^PUBLISH_COMPLETE" "$log"; then
    echo "ok $id" >> runner.txt; ok=$((ok + 1))
  elif grep -aq "^uploaded: .*\.mp4" "$log"; then
    echo "PARTIAL $id: $(grep -a '^PUBLISH_INCOMPLETE' "$log" | tail -1 || echo "exit $rc"); see $log" >> runner.txt
    partial=$((partial + 1))
  else
    echo "FAILED $id (exit $rc, see $log)" >> runner.txt; failed=$((failed + 1))
  fi
done 3< "$JOBS"

echo "ALL_DONE ok=$ok skipped=$skipped partial=$partial failed=$failed" >> runner.txt
(( partial == 0 && failed == 0 ))
