#!/usr/bin/env python3
"""Convolution reverb: mix dry signal with IR-convolved wet tail.

Reads/writes 16/32-bit PCM WAV. Wet level is relative to dry in dB.
(ffmpeg's afir is broken in some distro builds, so we convolve ourselves.)
"""
import argparse
import wave

import numpy as np


def read_wav(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    dtype = {2: np.int16, 4: np.int32}[sw]
    a = np.frombuffer(raw, dtype=dtype).reshape(-1, ch).astype(np.float64)
    a /= float(np.iinfo(dtype).max)
    return a, sr


def write_wav(path, a, sr):
    a = np.clip(a, -1.0, 1.0)
    with wave.open(path, "wb") as w:
        w.setnchannels(a.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def fftconvolve(x, h):
    n = len(x) + len(h) - 1
    nfft = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--ir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wet-db", type=float, default=-12.0,
                    help="wet level relative to dry RMS (default -12)")
    ap.add_argument("--pad-sec", type=float, default=0.0,
                    help="silence appended so the reverb tail rings out (e.g. outro length)")
    args = ap.parse_args()

    dry, sr = read_wav(args.inp)
    ir, sr_ir = read_wav(args.ir)
    if sr_ir != sr:
        raise SystemExit(f"sample rate mismatch: audio {sr} vs IR {sr_ir}")
    if dry.shape[1] == 1:
        dry = np.repeat(dry, 2, axis=1)
    if args.pad_sec > 0:
        dry = np.concatenate([dry, np.zeros((int(sr * args.pad_sec), 2))])

    n = len(dry)
    wet = np.zeros((n, 2))
    for c in range(2):
        wet[:, c] = fftconvolve(dry[:, c], ir[:, min(c, ir.shape[1] - 1)])[:n]

    # scale wet so its RMS sits wet_db below the dry RMS, then sum
    rms = lambda s: np.sqrt(np.mean(s ** 2)) + 1e-12
    wet *= (rms(dry) / rms(wet)) * (10 ** (args.wet_db / 20))
    mix = dry + wet

    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    write_wav(args.out, mix, sr)
    print(f"reverb: dry_rms={20*np.log10(rms(dry)):.1f}dB "
          f"wet_rms={20*np.log10(rms(wet)):.1f}dB peak={peak:.3f}")


if __name__ == "__main__":
    main()
