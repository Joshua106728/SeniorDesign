import numpy as np
from numpy.fft import rfft, irfft
from numpy.lib.stride_tricks import as_strided
from constants import frame_length, hop_length, SR, hop_length, win_length, max_period, min_period, trough_threshold

def yin(y: np.ndarray) -> np.ndarray:
    """
    Frame-by-frame YIN pitch tracker.

    Parameters
    ----------
    y : np.ndarray [shape=(n_samples,)]
        Audio signal

    Returns
    -------
    f0 : np.ndarray [shape=(n_frames,)]
        Estimated F0 in Hz per frame
    """
    # Extract frames manually
    n_frames = 1 + (len(y) - frame_length) // hop_length
    f0 = np.zeros(n_frames)
    velocity = np.zeros(n_frames)

    for i in range(n_frames):
        frame = y[i * hop_length : i * hop_length + frame_length]

        # === 1. Autocorrelation ===
        a = rfft(frame, frame_length)
        b = rfft(frame[win_length:0:-1], frame_length)
        acf = irfft(a * b, frame_length)[win_length:]
        acf[np.abs(acf) < 1e-6] = 0

        # === 2. Energy terms ===
        energy = np.cumsum(frame**2)
        energy = energy[win_length:] - energy[:-win_length]
        energy[np.abs(energy) < 1e-6] = 0

        # === 2.5 Velocity terms ===
        amplitude = np.sqrt(np.mean(frame**2)) # take RMS of frame
        maximum = np.max(np.abs(frame))
        vel = (amplitude / maximum * 127).astype(int)

        # === 3. Difference function ===
        diff = energy[0] + energy - 2 * acf

        # === 4. CMND (cumulative mean normalized difference) ===
        tau_range = np.arange(1, max_period + 1)
        cummean = np.cumsum(diff[1:max_period + 1]) / tau_range
        yin_vals = diff[min_period:max_period + 1] / (cummean[min_period - 1:max_period] + np.finfo(float).tiny)

        # === 5. Find local minima below threshold ===
        troughs = _find_troughs(yin_vals, trough_threshold)
        if len(troughs) > 0:
            tau = troughs[0] + min_period
        else:
            tau = np.argmin(yin_vals) + min_period

        # === 6. Parabolic interpolation ===
        shift = _parabolic_interp(yin_vals, tau - min_period)
        period = tau + shift

        # === 7. Convert to frequency ===
        f0[i] = SR / period
        velocity[i] = vel

    return f0, velocity


def _find_troughs(yin_vals, threshold):
    """Return indices of local minima below threshold."""
    troughs = []
    for i in range(1, len(yin_vals) - 1):
        if yin_vals[i] < yin_vals[i-1] and yin_vals[i] <= yin_vals[i+1]:
            if yin_vals[i] < threshold:
                troughs.append(i)
    return troughs


def _parabolic_interp(yin_vals, idx):
    """Parabolic interpolation to refine minimum index."""
    if idx <= 0 or idx >= len(yin_vals) - 1:
        return 0
    a = yin_vals[idx - 1]
    b = yin_vals[idx]
    c = yin_vals[idx + 1]
    denom = (a - 2*b + c)
    if np.abs(denom) < 1e-12:
        return 0
    return 0.5 * (a - c) / denom