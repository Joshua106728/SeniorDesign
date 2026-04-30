
import numpy as np
from constants import *

EPS = 1e-6
SMOOTHING_KERNEL_SIZE = SMOOTHING_WINDOW * 2 + 1  # 31


# ─── SPECTRAL WHITENING (pure Python) ───────────────────────────────────────
def spectral_whiten_ref(frame):
    """
    Reference spectral whitening using only np.fft.

    Returns whitened magnitude spectrum (float64[HOP_LENGTH+1]).
    """
    spectrum = np.fft.rfft(frame)             # complex, length N//2+1 = 2049
    magnitude = np.abs(spectrum).astype(np.float64)

    # Box-car smoothing (matches np.convolve with mode='same', zero-padded edges)
    kernel = np.ones(SMOOTHING_KERNEL_SIZE) / SMOOTHING_KERNEL_SIZE
    envelope = np.convolve(magnitude, kernel, mode='same')

    whitened = magnitude / (envelope + EPS)
    return whitened


# ─── AUTOCORRELATION (pure Python) ──────────────────────────────────────────
def compute_autocorrelation_ref(whitened_mag):
    """
    Autocorrelation via IFFT of power spectrum.
    autocorr = IFFT( |X_whitened|^2 )
    """
    power = whitened_mag ** 2
    # irfft expects the one-sided spectrum (length N//2+1) and returns N real values
    autocorr = np.fft.irfft(power, n=FRAME_LENGTH)
    return autocorr


# ─── YIN ALGORITHM (pure Python) ────────────────────────────────────────────
def yin_ref(autocorr, return_intermediates=False):
    """
    Pure Python YIN.  Set return_intermediates=True to get diff and cmnd
    arrays for debugging.

    Returns:
      f0 (float)                                if return_intermediates=False
      (f0, diff, cmnd, yin_slice, best_idx)     if return_intermediates=True
    """
    num_lags = MAX_PERIOD  # 551

    # STEP 1: Difference function
    r0 = autocorr[0]
    diff = np.zeros(num_lags, dtype=np.float64)
    for i in range(num_lags):
        diff[i] = 2.0 * (r0 - autocorr[i + 1])

    # STEP 2: CMND
    cmnd = np.ones(num_lags, dtype=np.float64)
    running_sum = 0.0
    for i in range(num_lags):
        running_sum += diff[i]
        tau = i + 1
        if running_sum > 0:
            cmnd[i] = diff[i] * tau / running_sum
        else:
            cmnd[i] = 1.0

    # STEP 3: Trough detection in [MIN_PERIOD, MAX_PERIOD)
    start = MIN_PERIOD - 1
    end = MAX_PERIOD
    yin_slice = cmnd[start:end]

    best_idx = None
    global_min_val = 1e9
    global_min_idx = 0

    for i in range(len(yin_slice)):
        val = yin_slice[i]
        if val < global_min_val:
            global_min_val = val
            global_min_idx = i

        if val < TROUGH_THRESHOLD:
            is_min = True
            if i > 0 and val > yin_slice[i - 1]:
                is_min = False
            if i < len(yin_slice) - 1 and val > yin_slice[i + 1]:
                is_min = False
            if is_min:
                best_idx = i
                break

    if best_idx is None:
        best_idx = global_min_idx

    # STEP 4: Parabolic interpolation
    shift = 0.0
    if 0 < best_idx < len(yin_slice) - 1:
        left   = yin_slice[best_idx - 1]
        center = yin_slice[best_idx]
        right  = yin_slice[best_idx + 1]
        a = right + left - 2 * center
        b = (right - left) / 2.0
        if abs(a) > abs(b):
            shift = -b / a

    tau_absolute = (MIN_PERIOD + best_idx) + shift
    f0 = SR / tau_absolute

    if return_intermediates:
        return f0, diff, cmnd, yin_slice, best_idx
    return f0


# ─── FULL PIPELINE (pure Python) ────────────────────────────────────────────
def process_audio_ref(frame, count, f0_estimates, f0_times, note_onset,
                      prev_energy, note_attack):
    """
    Pure Python per-frame processing.  Drop-in replacement for process_audio.
    """
    curr_time = count * FRAME_TIME
    f0_times.append(curr_time)

    frame = frame.astype(np.float64)
    total_energy = np.sum(frame ** 2)
    diff_energy = total_energy - prev_energy

    if note_attack > 0:
        f0_estimates.append(np.nan)
        note_attack -= 1
    elif total_energy < NOTE_THRESHOLD:
        f0_estimates.append(0)
        note_attack = 0
    elif diff_energy > NOTE_ONSET_THRESHOLD:
        f0_estimates.append(np.nan)
        note_onset.append(curr_time)
        note_attack = WAIT_ATTACK
    else:
        whitened = spectral_whiten_ref(frame)
        autocorr = compute_autocorrelation_ref(whitened)
        f0 = yin_ref(autocorr)
        f0_estimates.append(f0)
        note_attack = 0

    return total_energy, note_attack, f0_estimates, f0_times, note_onset


# ─── COMPARISON / DEBUG UTILITIES ────────────────────────────────────────────
def compare_stage(name, arr_cmsis, arr_ref, tol=1e-3):
    """Print max difference between CMSIS-DSP and reference arrays."""
    a = np.asarray(arr_cmsis, dtype=np.float64)
    b = np.asarray(arr_ref,   dtype=np.float64)
    min_len = min(len(a), len(b))
    diff = np.abs(a[:min_len] - b[:min_len])
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    status = "PASS" if max_diff < tol else "FAIL"
    print(f"  [{status}] {name:30s}  max_diff={max_diff:.6e}  mean_diff={mean_diff:.6e}")
    return max_diff < tol


def debug_frame(frame):
    """
    Run both CMSIS-DSP and pure-Python pipelines on a single frame,
    compare every intermediate stage.  Great for finding where things diverge.
    """
    from preprocessing import (
        spectral_whiten as sw_cmsis,
        compute_autocorrelation as ac_cmsis,
        yin as yin_cmsis,
    )

    print("=" * 70)
    print("Stage-by-stage comparison: CMSIS-DSP vs Pure Python")
    print("=" * 70)

    # Spectral whitening
    wh_c = sw_cmsis(frame)
    wh_r = spectral_whiten_ref(frame)
    compare_stage("spectral_whiten", wh_c, wh_r, tol=1e-2)

    # Autocorrelation
    ac_c = ac_cmsis(wh_c)
    ac_r = compute_autocorrelation_ref(wh_r)
    compare_stage("autocorrelation", ac_c, ac_r, tol=1e-1)

    # YIN internals
    f0_c = yin_cmsis(ac_c)
    f0_r, diff_r, cmnd_r, yin_slice_r, best_idx_r = yin_ref(ac_r, return_intermediates=True)

    print(f"\n  CMSIS f0 = {f0_c:.2f} Hz")
    print(f"  Ref   f0 = {f0_r:.2f} Hz")
    print(f"  Δ f0     = {abs(f0_c - f0_r):.2f} Hz")
    print("=" * 70)

    return f0_c, f0_r