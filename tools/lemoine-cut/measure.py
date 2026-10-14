#!/usr/bin/env python3
"""Measure a flute recording: tuning, scale, lowest note, and how clean a cut opens.

    python3 measure.py pitch   clip.MOV [more ...]   # which flute? which key? low cut?
    python3 measure.py opening cut_shorts.mp4 [...]  # first note, room level, gap

pitch reports the best-fit A4 reference from TWO overlapping sweeps (424-448
and 436-460 Hz). A scale that fits a grid at one reference fits equally well
a semitone away, so a single sweep wider than a semitone finds two equal
minima and picks one arbitrarily; a sweep that lands on its own boundary is
the same trap (a flute was once read as "A424, lowest note F4" this way).
Any flute tuned below about A436 (the quenas, the Spanish Cedar) fits BOTH
sweeps equally, at its real reference and a semitone above it, and which
one wins is rounding noise: picking by fit error alone read the Spanish
Cedar's E as D#. So when the sweeps tie, the notes are printed against BOTH,
nearer-440 first. That is usually right, but not always: the Jayras sits
about 57 cents flat, past the halfway point, so its true reading (G A B)
comes second. Choose between the two with your eyes and the flute table in
CLAUDE.md; the lowest note in Hz never depends on either.

lowest sustained note (2nd percentile of steady frames) is what a low cut is
set from: about an octave below it, never above.

opening reports the time to the first note, the room level before it, and
the gap between room and playing. A cut that opens on boosted hiss shows a
gap near 0 dB; a healthy one is 25 dB or more.

Reads audio through ffmpeg, so .MOV/.mp4/.wav all work.
"""
import collections
import subprocess
import sys

import numpy as np

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def load(path, sr=44100):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-map", "0:a:0", "-vn",
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr


def steady_pitches(x, sr):
    hop, win = int(0.02 * sr), int(0.12 * sr)
    v = []
    for i in range((len(x) - win) // hop):
        s = x[i * hop:i * hop + win]
        s = s - s.mean()
        if np.sqrt(np.mean(s ** 2)) < 3e-3:
            continue
        w = s * np.hanning(len(s))
        n = 1 << (2 * len(w) - 1).bit_length()
        S = np.fft.rfft(w, n)
        ac = np.fft.irfft(S * np.conj(S), n)[:len(w)]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lo, hi = int(sr / 1400), int(sr / 150)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] < 0.85:          # not clearly periodic: breath, noise, reverb
            continue
        # A periodic signal also correlates at twice its period, and that peak
        # can win by a hair: a held G4 then reads as G3 for most of a second
        # (a Stellar take showed 0.76 s of "199 Hz" on a flute whose lowest
        # note is 296). So if half the lag correlates nearly as well, the
        # shorter period is the note. A real low note with a strong 2nd
        # harmonic is safe: its half-lag only reaches 0.9 when H2 is about
        # 13 dB louder than H1, which a flute's fundamental never is.
        h = k // 2
        if h - 2 >= lo:
            j = h - 2 + int(np.argmax(ac[h - 2:h + 3]))
            if ac[j] >= 0.9 * ac[k]:
                k = j
        if 0 < k < len(ac) - 1:
            a, b, c = ac[k - 1], ac[k], ac[k + 1]
            d = a - 2 * b + c
            if d:
                k = k + 0.5 * (a - c) / d
        if not np.isfinite(k) or k <= 0:   # flat peak can push k to zero
            continue
        v.append((i, sr / k))
    if len(v) < 5:
        return np.array([]), np.array([], dtype=int)
    idx = np.array([i for i, _ in v])
    f = np.array([p for _, p in v])
    # steady = under 25 cents peak-to-peak across five consecutive voiced frames
    keep = [j for j in range(2, len(f) - 2)
            if max(f[j - 2:j + 3]) / min(f[j - 2:j + 3]) < 2 ** (25 / 1200)]
    return f[keep], idx[keep]


def has_fundamental(x, sr, starts, f, max_frames=120):
    """Is there real energy AT f, or only at 2f and above?

    A double flute plays two notes at once. A drone with a melody note a
    fifth above it (F# under C#, a 2:3 ratio) makes a waveform that repeats
    every 1/(f/2) s, and an autocorrelation tracker reads that shared period
    as a note an octave under the drone: the Double F#'s takes read
    "lowest 182-184 Hz" with nothing at 185 Hz at all (37-40 dB under the
    366 Hz drone). A real note always has its own fundamental; a flute's is
    its strongest partial. So a candidate whose fundamental sits 15 dB or
    more under its octave is a composite period, not a note.
    """
    win, n = int(0.12 * sr), 1 << 14
    step = max(1, len(starts) // max_frames)
    acc = None
    for s0 in starts[::step]:
        seg = x[s0:s0 + win]
        if len(seg) < win:
            continue
        spec = np.abs(np.fft.rfft(seg * np.hanning(win), n))
        acc = spec if acc is None else acc + spec
    if acc is None:
        return True
    fr = np.fft.rfftfreq(n, 1 / sr)

    def peak(c):
        b = (fr > c * 0.97) & (fr < c * 1.03)
        return 20 * np.log10(acc[b].max() + 1e-12)
    return peak(f) > peak(2 * f) - 15


def fit(st, lo, hi):
    return min((float(np.abs(((1200 * np.log2(st / r) + 50) % 100) - 50).mean()), float(r))
               for r in np.arange(lo, hi, 0.1))


def pitch(path):
    x, sr = load(path)
    st, at = steady_pitches(x, sr)
    if len(st) < 50:
        print(f"{path}: only {len(st)} steady frames, too few to measure")
        return
    (e1, r1), (e2, r2) = fit(st, 424, 448), fit(st, 436, 460)
    ambiguous = abs(r1 - r2) > 1.0 and abs(e1 - e2) < 1.0
    refs = sorted([(e1, r1), (e2, r2)], key=lambda c: abs(np.log2(c[1] / 440.0)))
    err, ref = refs[0] if ambiguous else min((e1, r1), (e2, r2))
    m = np.round(69 + 12 * np.log2(st / ref)).astype(int)

    def notes(r):
        c = collections.Counter(NAMES[i % 12] for i in np.round(69 + 12 * np.log2(st / r)).astype(int))
        return "  ".join(f"{k} {100 * n / len(st):.0f}%" for k, n in c.most_common(7))
    # Lowest REAL note: the autocorrelation occasionally locks onto twice the
    # period and reports a pitch an octave low. Those frames are scattered, so
    # a plain percentile gets dragged down by them (a Stellar take read 199 Hz
    # against a true ~291). Count a note only when at least 2% of steady
    # frames agree on it, then take that note's median frequency.
    # A heavily held note can clear that bar with its octave errors alone (a
    # Stellar take held G4 long enough to show 44 frames of "G3"). An octave
    # error happens WHILE the note above is sounding, so its neighbouring
    # frames (within 0.1 s) are that higher note; a real low note sits among
    # frames of itself. A candidate whose neighbours are mostly its own octave
    # above is dropped. Counting frames alone could not separate the two
    # without also discarding a real low note that is simply played rarely.
    # It must ALSO be much rarer than that octave: a real low note that keeps
    # leaping to its octave has neighbours that are mostly the octave too
    # (a take alternating G4 and G5 once read "lowest 784 Hz", putting the
    # suggested low cut right on the real G4). The artefact is a sliver of the
    # note above it; a real note is not.
    support = collections.Counter(m)
    by_frame = dict(zip(at.tolist(), m.tolist()))

    def octave_error(k):
        near = [by_frame.get(i + o) for i in at[m == k] for o in range(-5, 6) if o]
        near = [n for n in near if n is not None and n != k]
        return (bool(near) and sum(n == k + 12 for n in near) >= 0.5 * len(near)
                and support[k] < 0.25 * support.get(k + 12, 0))

    real = sorted(k for k, n in support.items() if n >= 0.02 * len(m) and not octave_error(k))
    # and a note must have its own fundamental (see has_fundamental): the
    # shared period of two voices a fifth apart is not a note
    hop = int(0.02 * sr)
    real = [k for k in real if has_fundamental(x, sr, at[m == k] * hop, float(np.median(st[m == k])))]
    low = float(np.median(st[m == real[0]])) if real else float(np.percentile(st, 2))
    lm = 69 + 12 * np.log2(low / 440.0)
    print(f"{path}")
    if ambiguous:
        print(f"  {len(st)} steady frames; A4 {refs[0][1]:.1f} and {refs[1][1]:.1f} Hz fit equally "
              f"({err:.1f} cents avg error), a semitone apart, so the notes read either way:")
        for _, r in refs:
            print(f"    at A{r:.1f} ({1200 * np.log2(r / 440):+.0f}c): {notes(r)}")
    else:
        print(f"  {len(st)} steady frames; best-fit A4 {ref:.1f} Hz ({err:.1f} cents avg error)")
        print(f"  time on each note: {notes(ref)}")
    print(f"  lowest sustained {low:.0f} Hz (~{NAMES[round(lm) % 12]}{round(lm) // 12 - 1} vs A440)"
          f"  -> a low cut around {int(low / 2 // 10 * 10)} Hz would sit an octave under it")


def opening(path):
    x, sr = load(path, 48000)
    h = int(0.25 * sr)
    db = lambda s: 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12)  # noqa: E731
    L = np.array([db(x[i * h:(i + 1) * h]) for i in range(len(x) // h)])
    play = float(np.median(L[L >= np.percentile(L, 40)]))
    first = next((i for i, v in enumerate(L) if v > play - 10), 0) * 0.25
    if first < 1.1:
        # Opens on the note: there is no room before it to measure, and the
        # window would sit inside the playing and report a false "hiss".
        print(f"{path}\n  first note {first:.1f}s  room n/a (opens on the note)  playing {play:.1f} dB")
        return
    pre = x[int(0.6 * sr):int((first - 0.2) * sr)]   # after the 0.6 s fade-in
    room = db(pre)
    print(f"{path}\n  first note {first:.1f}s  room {room:.1f} dB  playing {play:.1f} dB  "
          f"gap {play - room:.1f} dB" + ("   <- hiss is near playing level" if play - room < 15 else ""))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("pitch", "opening"):
        sys.exit(__doc__)
    for p in sys.argv[2:]:
        (pitch if sys.argv[1] == "pitch" else opening)(p)
