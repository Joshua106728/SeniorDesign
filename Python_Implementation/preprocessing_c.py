"""
Fixed preprocessing pipeline: Spectral Whitening + YIN Pitch Detection
Uses CMSIS-DSP Python wrapper for MCU-portable operations.

Key fixes from original:
  1. Removed incorrect energy subtraction from YIN difference function
  2. Separated spectral_whiten and autocorrelation into clear stages
  3. Fixed smoothing window edge handling to match Colab np.convolve behavior
"""

import numpy as np
import cmsisdsp as dsp
from constants import *

# ─── CMSIS-DSP FFT instances (init once, reuse) ─────────────────────────────
rfft_forward = dsp.arm_rfft_fast_instance_f32()
rfft_inverse = dsp.arm_rfft_fast_instance_f32()
dsp.arm_rfft_fast_init_f32(rfft_forward, FRAME_LENGTH)
dsp.arm_rfft_fast_init_f32(rfft_inverse, FRAME_LENGTH)

EPS = np.float32(1e-6)
SMOOTHING_KERNEL_SIZE = SMOOTHING_WINDOW * 2 + 1  # 31


# ─── SPECTRAL WHITENING ─────────────────────────────────────────────────────
def spectral_whiten(frame):
    """
    Flatten the spectral envelope so that the autocorrelation has sharper
    peaks at the fundamental period.

    Input:  time-domain frame (float32[FRAME_LENGTH])
    Output: whitened magnitude spectrum (float32[HOP_LENGTH+1])
            (phase is discarded — we only need |X_whitened|^2 for autocorrelation)
    """
    # ---- FFT ----
    # CMSIS rfft format: [DC_real, Nyq_real, Re1, Im1, Re2, Im2, ...]
    spectrum = dsp.arm_rfft_fast_f32(rfft_forward, frame.astype(np.float32), 0)

    # ---- Extract magnitude ----
    num_bins = HOP_LENGTH + 1  # 2049
    magnitude = np.zeros(num_bins, dtype=np.float32)
    magnitude[0]  = abs(spectrum[0])   # DC  (purely real)
    magnitude[-1] = abs(spectrum[1])   # Nyquist (purely real)
    magnitude[1:-1] = dsp.arm_cmplx_mag_f32(spectrum[2:])  # complex bins

    # ---- Box-car moving average (matches np.convolve mode='same') ----
    # At edges, treat out-of-bounds bins as 0 (same as np.convolve zero-padding).
    # Always divide by full kernel size so edge behaviour matches Colab.
    whitened = np.zeros(num_bins, dtype=np.float32)
    for i in range(num_bins):
        lo = max(0, i - SMOOTHING_WINDOW)
        hi = min(num_bins, i + SMOOTHING_WINDOW + 1)
        # sum only existing bins, but divide by full kernel (zero-pad effect)
        avg = (np.float32(sum(magnitude[lo:hi])) / np.float32(SMOOTHING_KERNEL_SIZE)) + EPS
        whitened[i] = magnitude[i] / avg

    return whitened


# ─── AUTOCORRELATION VIA IFFT(|X|^2) ────────────────────────────────────────
def compute_autocorrelation(whitened_mag):
    """
    Wiener-Khinchin: autocorr(x_whitened) = IFFT( |X_whitened|^2 )

    Input:  whitened magnitude spectrum (float32[HOP_LENGTH+1])
    Output: autocorrelation array       (float32[FRAME_LENGTH])
    """
    # Square the magnitude → power spectrum
    power = dsp.arm_mult_f32(whitened_mag, whitened_mag.copy())

    # Pack into CMSIS interleaved rfft format for IFFT
    packed = np.zeros(FRAME_LENGTH, dtype=np.float32)
    packed[0] = power[0]    # DC
    packed[1] = power[-1]   # Nyquist
    for i in range(1, HOP_LENGTH):
        packed[2 * i]     = power[i]         # Real
        packed[2 * i + 1] = np.float32(0.0)  # Imag = 0 (power spectrum is real)

    # Inverse FFT → autocorrelation
    autocorr = dsp.arm_rfft_fast_f32(rfft_inverse, packed.astype(np.float32), 1)
    return autocorr


# ─── YIN ALGORITHM ───────────────────────────────────────────────────────────
def yin(autocorr):
    """
    YIN pitch estimator (de Cheveigné & Kawahara, 2002).

    Steps:
      1. Difference function        d(τ) = 2·(r(0) − r(τ))
      2. Cumulative mean normalised  d′(τ) = d(τ)·τ / Σ_{j=1}^{τ} d(j)
      3. Absolute-threshold trough search
      4. Parabolic interpolation

    Input:  autocorrelation array (from compute_autocorrelation)
    Output: estimated f0 in Hz (float32)
    """
    num_lags = MAX_PERIOD  # 551  (lags 1 … 551)

    # ── STEP 1: Difference function ──────────────────────────────────────
    # d(τ) = 2·( r(0) − r(τ) )   for τ = 1 … MAX_PERIOD
    #
    # NOTE: the original code subtracted a cumulative-energy array of the
    #       *original* frame here.  That is WRONG — the autocorrelation
    #       already encodes the energy of the *whitened* signal.
    r0 = np.float32(autocorr[0])
    diff = np.zeros(num_lags, dtype=np.float32)  # index i → lag (i+1)
    for i in range(num_lags):
        diff[i] = np.float32(2.0) * (r0 - np.float32(autocorr[i + 1]))

    # ── STEP 2: Cumulative Mean Normalised Difference (CMND) ────────────
    # d′(τ) = 1                          if τ = 0
    #        d(τ) · τ / Σ_{j=1}^τ d(j)  if τ ≥ 1
    cmnd = np.zeros(num_lags, dtype=np.float32)
    running_sum = np.float32(0.0)
    for i in range(num_lags):
        running_sum += diff[i]
        tau = np.float32(i + 1)               # actual lag
        if running_sum > np.float32(0.0):
            cmnd[i] = diff[i] * tau / running_sum
        else:
            cmnd[i] = np.float32(1.0)

    # ── STEP 3: Trough detection ────────────────────────────────────────
    # Search within [MIN_PERIOD, MAX_PERIOD) for the first local minimum
    # that falls below TROUGH_THRESHOLD.  Fall back to global minimum.
    start = MIN_PERIOD - 1   # index offset (lag MIN_PERIOD → index MIN_PERIOD-1)
    end   = MAX_PERIOD       # exclusive
    yin_slice = cmnd[start:end]  # length = MAX_PERIOD - MIN_PERIOD + 1 = 489

    best_idx = None
    global_min_val = np.float32(1e9)
    global_min_idx = 0

    for i in range(len(yin_slice)):
        val = yin_slice[i]

        # Track global minimum as fallback
        if val < global_min_val:
            global_min_val = val
            global_min_idx = i

        # Check threshold
        if val < TROUGH_THRESHOLD:
            # Verify local minimum (≤ both neighbours)
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

    # ── STEP 4: Parabolic interpolation ─────────────────────────────────
    shift = np.float32(0.0)
    if 0 < best_idx < len(yin_slice) - 1:
        left   = yin_slice[best_idx - 1]
        center = yin_slice[best_idx]
        right  = yin_slice[best_idx + 1]

        a = right + left - np.float32(2.0) * center
        b = (right - left) / np.float32(2.0)

        if abs(a) > abs(b):        # parabola is concave-up → valid
            shift = np.float32(-b / a)

    # Convert to frequency
    tau_absolute = np.float32(MIN_PERIOD + best_idx) + shift
    f0 = np.float32(SR) / tau_absolute

    return f0


# ─── MAIN PER-FRAME ENTRY POINT ─────────────────────────────────────────────
def preprocess_audio(frame, count, f0_estimates, f0_times, note_onset,
                  prev_energy, note_attack, debug=False):
    """
    Process one audio frame: energy gate → onset detection → pitch estimation.

    Returns (total_energy, note_attack, f0_estimates, f0_times, note_onset)
    """
    curr_time = count * FRAME_TIME
    f0_times.append(curr_time)

    # ── Energy ───────────────────────────────────────────────────────────
    frame_f32 = frame.astype(np.float32)
    frame_squared = dsp.arm_mult_f32(frame_f32, frame_f32.copy())
    total_energy = np.float32(sum(frame_squared))       # arm_dot_f32 in C
    diff_energy  = total_energy - prev_energy

    # ── State machine ────────────────────────────────────────────────────
    if note_attack > 0:
        # Still waiting for attack transient to settle
        f0_estimates.append(np.nan)
        note_attack -= 1

    elif total_energy < NOTE_THRESHOLD:
        # Silence / rest
        f0_estimates.append(0)
        note_attack = 0

    elif diff_energy > NOTE_ONSET_THRESHOLD:
        # New note onset detected — skip a few frames
        f0_estimates.append(np.nan)
        note_onset.append(curr_time)
        note_attack = WAIT_ATTACK

    else:
        # Steady-state → estimate pitch
        whitened  = spectral_whiten(frame_f32)
        autocorr  = compute_autocorrelation(whitened)
        f0        = yin(autocorr)
        f0_estimates.append(f0)
        note_attack = 0

    return total_energy, note_attack, f0_estimates, f0_times, note_onset