
import numpy as np
import cmsisdsp as dsp
from constants import *

rfft_forward = dsp.arm_rfft_fast_instance_f32()
rfft_inverse = dsp.arm_rfft_fast_instance_f32()
dsp.arm_rfft_fast_init_f32(rfft_forward, FRAME_LENGTH)
dsp.arm_rfft_fast_init_f32(rfft_inverse, FRAME_LENGTH)
eps = 1e-6

def spectral_whiten(frame):
    # take FFT
    spectrum = dsp.arm_rfft_fast_f32(rfft_forward, frame.astype(np.float32), 0) # DC, Nyq, RE1, IM1, RE1, IM1

    # take magnitude (fully real)
    magnitude = np.zeros(HOP_LENGTH+1, dtype=np.float32) # 2049
    magnitude[0] = abs(spectrum[0]) # DC
    magnitude[-1] = abs(spectrum[1]) # Nyquist
    magnitude[1:-1] = dsp.arm_cmplx_mag_f32(spectrum[2:]) # expects alternating RE | IM = 1 value

    # box car moving average (do leetcode version in C)
    whitened = dsp.arm_copy_f32(magnitude)
    for i in range(HOP_LENGTH+1):
        lo = max(0, i - SMOOTHING_WINDOW)
        hi = min(HOP_LENGTH+1, i + SMOOTHING_WINDOW + 1)
        avg = (sum(magnitude[lo:hi]) / (hi - lo) ) + eps
        whitened[i] /= avg
        
    return whitened

def yin(frame, energy):
    # STEP 1: Autocorrelation
    # find power spectrum
    frame_copy = dsp.arm_copy_f32(frame)
    powspec = dsp.arm_mult_f32(frame, frame_copy)

    # find autocorrelation
    powspec_formatted = np.zeros(FRAME_LENGTH, dtype=np.float32)
    powspec_formatted[0] = powspec[0] # DC
    powspec_formatted[1] = powspec[-1] # Nyquist
    for i in range(1, HOP_LENGTH):
        powspec_formatted[2*i] = powspec[i] # Real
        powspec_formatted[2*i+1] = 0.0 # Imaginary <-- can probably get rid of this
    
    autocorr = dsp.arm_rfft_fast_f32(rfft_inverse, powspec_formatted.astype(np.float32), 1) # 4096
    autocorr_slice = autocorr[1:MAX_PERIOD+1] # 551

    # STEP 2: Difference Function
    r0_arr = np.full(MAX_PERIOD, autocorr[0], dtype=np.float32)
    diff = dsp.arm_sub_f32(r0_arr, autocorr_slice) # 1-552 --> 0-551
    scaled_diff = dsp.arm_scale_f32(diff, np.float32(2.0))
    diff_vals = dsp.arm_sub_f32(scaled_diff, np.array(energy, dtype=np.float32))

    # STEP 3: CMND
    cum_mean = np.zeros(MAX_PERIOD, dtype=np.float32) # 1-552 --> 0-551
    total = 0
    for i in range(len(cum_mean)):
        total += diff_vals[i]
        cum_mean[i] = total / np.float32(i+1)
    
    yin_numerator = diff_vals[MIN_PERIOD-1:MAX_PERIOD]
    yin_denominator = cum_mean[MIN_PERIOD-1:MAX_PERIOD]
    yin_denominator_tiny = dsp.arm_offset_f32(yin_denominator, np.float32(1e-6))
    yin_frames = yin_numerator / yin_denominator_tiny

    # STEP 4: Trough Detection
    tau = None
    min = 1e9
    min_idx = None

    for i in range(len(yin_frames)):
        # look for first local minima
        if yin_frames[i] < TROUGH_THRESHOLD:
            if i == 0: # only rightside
                if yin_frames[i] < yin_frames[i+1]:
                    tau = i
                    break
            elif i == len(yin_frames) - 1: # only leftside
                if yin_frames[i] <= yin_frames[i-1]:
                    tau = i
                    break
            elif yin_frames[i] <= yin_frames[i-1] and yin_frames[i] <= yin_frames[i+1]:
                tau = i
                break
        
        # keep track of minimum val if no minima under trough threshold detected
        if yin_frames[i] < min:
            min = yin_frames[i]
            min_idx = i

    if tau is None:
        tau = min_idx
        
    # STEP 5: Parabolic Interpolation
    shift = 0
    if tau == 0 or tau == (len(yin_frames) - 1):
        shift = np.float32(0.0)
    else:
        left = yin_frames[tau - 1]
        center = yin_frames[tau]
        right = yin_frames[tau + 1]

        a = right + left - (2 * center) # a = x[1] + x[-1] - 2 * x[0]
        b = (right - left) / np.float32(2.0) # b = b = (x[1] - x[-1]) / 2
        
        if abs(b) >= abs(a):
            shift = np.float32(0.0)
        else:
            shift = (b * -1) / a
    
    # FINAL STEP
    tau_absolute = np.float32(MIN_PERIOD + tau) + shift
    f0 = np.float32(SR) / tau_absolute
    return f0

def process_audio(frame, count, f0_estimates, f0_times, note_onset, prev_energy, note_attack):
    curr_time = count * FRAME_TIME # X-bit int
    f0_times.append(curr_time)

    # calculate energy
    frame = frame.astype(np.float32) # not needed in C
    frame_copy = dsp.arm_copy_f32(frame)
    frame_squared = dsp.arm_mult_f32(frame, frame_copy)
    
    energy = []
    total_energy = 0
    for i in range(len(frame_squared)):
        total_energy += frame_squared[i]
        if i < MAX_PERIOD:
            energy.append(total_energy)
    diff_energy = total_energy - prev_energy

    if note_attack != 0:
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
        whitened_frame = spectral_whiten(frame)
        preprocessed_frame = yin(whitened_frame, energy)
        f0_estimates.append(preprocessed_frame)
        note_attack = 0
    return total_energy, note_attack, f0_estimates, f0_times, note_onset

    # In C, pass in array pointers + note_attack pointer and only need to return total_energy