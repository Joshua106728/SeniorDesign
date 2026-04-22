
#include "yin.h"
#include "constants.h"
#include <math.h>

/* ---- FFT instances ------------------------------------------------------ */
static arm_rfft_fast_instance_f32 rfft_forward;
static arm_rfft_fast_instance_f32 rfft_inverse;

/* ---- Working buffers (reused where possible) --------------------------- */
static float32_t spectrum[FRAME_LENGTH];    /* 16 KB — FFT output, then packed for IFFT */
static float32_t magnitude[NUM_BINS];       /* 8 KB — magnitude, reused as power */
static float32_t autocorr[FRAME_LENGTH];    /* 16 KB — IFFT output */
static float32_t diff[MAX_PERIOD];          /* ~2 KB — YIN difference */
static float32_t cmnd[MAX_PERIOD];          /* ~2 KB — cumulative mean normalized diff */


void yin_init(void)
{
    arm_rfft_fast_init_f32(&rfft_forward, FRAME_LENGTH);
    arm_rfft_fast_init_f32(&rfft_inverse, FRAME_LENGTH);
}


/* ─────────────────────────────────────────────────────────────────────────
 * Autocorrelation via Wiener-Khinchin:
 *   autocorr(x) = IFFT( |FFT(x)|^2 )
 * No spectral whitening — power spectrum used directly.
 * ───────────────────────────────────────────────────────────────────────── */
static void compute_autocorrelation(const float32_t *frame)
{
    /* FFT (copy first since arm_rfft_fast_f32 overwrites input) */
    arm_copy_f32((float32_t *)frame, spectrum, FRAME_LENGTH);
    arm_rfft_fast_f32(&rfft_forward, spectrum, spectrum, 0);
    /* Format: [DC, Nyquist, Re1, Im1, Re2, Im2, ...] */

    /* Magnitude — reused as power spectrum buffer */
    magnitude[0]            = fabsf(spectrum[0]);               /* DC */
    magnitude[NUM_BINS - 1] = fabsf(spectrum[1]);               /* Nyquist */
    arm_cmplx_mag_f32(&spectrum[2], &magnitude[1], HOP_LENGTH - 1);

    /* Square to get power spectrum */
    arm_mult_f32(magnitude, magnitude, magnitude, NUM_BINS);

    /* Repack into interleaved format for inverse FFT.
     * Reusing spectrum[] as scratch since we've extracted everything we need. */
    spectrum[0] = magnitude[0];
    spectrum[1] = magnitude[NUM_BINS - 1];
    for (int i = 1; i < HOP_LENGTH; i++) {
        spectrum[2 * i]     = magnitude[i];
        spectrum[2 * i + 1] = 0.0f;
    }

    arm_rfft_fast_f32(&rfft_inverse, spectrum, autocorr, 1);
}


/* ─────────────────────────────────────────────────────────────────────────
 * YIN algorithm — difference function, CMND, trough search, parabolic interp
 * ───────────────────────────────────────────────────────────────────────── */
static float32_t yin_core(void)
{
    const int num_lags = MAX_PERIOD;

    /* Step 1: Difference function
     *   d(tau) = 2 * (r(0) - r(tau))   for tau = 1..MAX_PERIOD
     *   diff[i] represents d(i+1) */
    float32_t r0 = autocorr[0];
    for (int i = 0; i < num_lags; i++) {
        diff[i] = 2.0f * (r0 - autocorr[i + 1]);
    }

    /* Step 2: Cumulative Mean Normalized Difference (CMND)
     *   d'(tau) = d(tau) * tau / sum_{j=1..tau} d(j) */
    float32_t running_sum = 0.0f;
    for (int i = 0; i < num_lags; i++) {
        running_sum += diff[i];
        float32_t tau = (float32_t)(i + 1);
        if (running_sum > 0.0f) {
            cmnd[i] = diff[i] * tau / running_sum;
        } else {
            cmnd[i] = 1.0f;
        }
    }

    /* Step 3: Trough detection in window [MIN_PERIOD, MAX_PERIOD]
     *   best_idx is RELATIVE to the slice (0..slice_len-1) */
    const int start = MIN_PERIOD - 1;
    const int slice_len = MAX_PERIOD - MIN_PERIOD + 1;

    int best_idx = -1;
    int global_min_idx = 0;
    float32_t global_min_val = 1e9f;

    for (int i = 0; i < slice_len; i++) {
        float32_t val = cmnd[start + i];

        if (val < global_min_val) {
            global_min_val = val;
            global_min_idx = i;
        }

        if (val < TROUGH_THRESHOLD) {
            int is_min = 1;
            if (i > 0 && val > cmnd[start + i - 1]) is_min = 0;
            if (i < slice_len - 1 && val > cmnd[start + i + 1]) is_min = 0;
            if (is_min) {
                best_idx = i;
                break;
            }
        }
    }

    if (best_idx < 0) {
        best_idx = global_min_idx;
    }

    /* Step 4: Parabolic interpolation around the chosen trough */
    float32_t shift = 0.0f;
    if (best_idx > 0 && best_idx < slice_len - 1) {
        float32_t left   = cmnd[start + best_idx - 1];
        float32_t center = cmnd[start + best_idx];
        float32_t right  = cmnd[start + best_idx + 1];

        float32_t a = right + left - 2.0f * center;
        float32_t b = (right - left) / 2.0f;

        if (fabsf(a) > fabsf(b)) {
            shift = -b / a;
        }
    }

    /* Convert lag to frequency */
    float32_t tau_absolute = (float32_t)(MIN_PERIOD + best_idx) + shift;
    float32_t f0 = (float32_t)SR / tau_absolute;

    return f0;
}


/* ─────────────────────────────────────────────────────────────────────────
 * Top-level entry point
 * ───────────────────────────────────────────────────────────────────────── */
float32_t yin_estimate_f0(const float32_t *frame)
{
    compute_autocorrelation(frame);
    return yin_core();
}
