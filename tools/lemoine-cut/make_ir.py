#!/usr/bin/env python3
"""Generate a stereo impulse response for flute-friendly hall reverb.

Exponentially decaying noise with faster high-frequency decay, sparse early
reflections, ~25ms pre-delay and decorrelated channels. Used by lemoine_cut.sh
via ffmpeg's afir convolution (tail only — the dry path is mixed separately).
"""
import argparse
import struct
import wave

import numpy as np


def make_ir(sr=48000, t60=2.3, predelay_ms=25.0, seed=432):
    rng = np.random.default_rng(seed)
    n = int(sr * (t60 * 1.25))
    t = np.arange(n) / sr

    out = []
    for ch in range(2):
        noise = rng.standard_normal(n)
        # frequency-dependent decay: filter the noise into bands, decay highs faster
        spectrum = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n, 1 / sr)
        ir = np.zeros(n)
        bands = [(0, 500, 1.15), (500, 2000, 1.0), (2000, 6000, 0.72), (6000, sr / 2, 0.45)]
        for lo, hi, mult in bands:
            m = (freqs >= lo) & (freqs < hi)
            s = np.zeros_like(spectrum)
            s[m] = spectrum[m]
            band = np.fft.irfft(s, n)
            decay = np.exp(-6.91 * t / (t60 * mult))
            ir += band * decay
        # sparse early reflections in the first 80ms
        for _ in range(8):
            d = int(sr * rng.uniform(0.008, 0.08))
            ir[d] += rng.uniform(0.05, 0.16) * (1 if rng.random() > 0.5 else -1)
        out.append(ir)

    ir = np.stack(out, axis=1)
    pre = np.zeros((int(sr * predelay_ms / 1000), 2))
    ir = np.concatenate([pre, ir])
    ir /= np.max(np.abs(ir)) * 1.05
    return (ir * 32767).astype(np.int16), sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ir-hall.wav")
    ap.add_argument("--t60", type=float, default=2.3)
    args = ap.parse_args()
    data, sr = make_ir(t60=args.t60)
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())
    print(args.out)


if __name__ == "__main__":
    main()
