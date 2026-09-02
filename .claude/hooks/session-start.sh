#!/bin/bash
# Rebuild everything lemoine-cut needs, on every fresh container.
#
# WHY THIS EXISTS
# ---------------
# Sessions run in a disposable cloud container. When the platform rebuilds it,
# anything not committed to git is gone. On 2026-09-01 that took out ffmpeg,
# numpy/scipy/soundfile/Pillow, and the Drive service-account key all at once —
# so a routine "cut these two clips" turned into a diagnosis, three installs,
# and two finished videos that could not be filed anywhere.
#
# Committed to the repo, this script survives every rebuild and puts the
# machine back the way the pipeline expects it.
#
# THE ONE PIECE IT CANNOT DO ALONE
# --------------------------------
# gdrive-sa.json is a credential. It must never be committed — anyone with
# read access to the repo would get write access to the Drive. So it cannot
# live in git, and this script restores it from an environment variable
# instead. Set GDRIVE_SA_JSON_B64 once in the Claude Code environment settings
# (base64 of the key file) and Drive uploads survive every rebuild from then on.
#
# Without that variable the cuts still render — they just stay local, and
# lemoine_publish.sh now says LOCAL ONLY rather than claiming otherwise.
set -euo pipefail

# Local machines already have all of this; only the remote container needs it.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

HERE="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CUT="$HERE/tools/lemoine-cut"

# 1) ffmpeg — the pipeline is ffmpeg from end to end, so nothing works without it
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "session-start: installing ffmpeg"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg
fi

# 2) python packages — reverb.py and the overlay builders need these
if ! python3 -c "import numpy, scipy, soundfile, PIL" >/dev/null 2>&1; then
  echo "session-start: installing python dependencies"
  pip install -q --root-user-action=ignore -r "$CUT/requirements.txt"
fi

# 3) the Drive key, from the environment rather than from git
if [ ! -f "$CUT/gdrive-sa.json" ] && [ -n "${GDRIVE_SA_JSON_B64:-}" ]; then
  if echo "$GDRIVE_SA_JSON_B64" | base64 -d > "$CUT/gdrive-sa.json" 2>/dev/null \
     && python3 -c "import json,sys; json.load(open('$CUT/gdrive-sa.json'))" 2>/dev/null; then
    chmod 600 "$CUT/gdrive-sa.json"
    echo "session-start: restored gdrive-sa.json from GDRIVE_SA_JSON_B64"
  else
    # A half-written key is worse than none: drive_upload.py would fail with a
    # JSON error instead of the clear "no key" path.
    rm -f "$CUT/gdrive-sa.json"
    echo "session-start: GDRIVE_SA_JSON_B64 is set but did not decode to valid JSON" >&2
  fi
fi

# 4) say plainly whether Drive is connected, so a broken upload is never a surprise
if [ -f "$CUT/gdrive-sa.json" ]; then
  echo "session-start: ready — Drive connected, cuts will be filed automatically"
else
  echo "session-start: ready — NO DRIVE KEY. Cuts will render but stay local."
  echo "               Set GDRIVE_SA_JSON_B64 in the environment settings:"
  echo "               base64 -w0 gdrive-sa.json"
fi
