
#include "preprocessing.h"
#include <math.h>

// FFT instances
static arm_rfft_fast_instance_f32 rfft_fwd;
static arm_rfft_fast_instance_f32 rfft_inv;

// Shared buffers
static float32_t fft_buf[FRAME_LENGTH];     // 16 KB — FFT scratch, then reused for autocorrelation
static float32_t magnitude[NUM_BINS];       // ~8 KB — magnitude, then reused for power spectrum
static float32_t whitened_buf[NUM_BINS];    // ~8 KB
static float32_t diff[MAX_PERIOD];          // ~2 KB

// Note Onset Detection
static float32_t prev_variance = 0.0f;
static int       attack_wait_counter = 0;
static float32_t frame_scratch[FRAME_LENGTH];

void preprocessing_init(void)
{
    arm_rfft_fast_init_f32(&rfft_fwd, FRAME_LENGTH);
    arm_rfft_fast_init_f32(&rfft_inv, FRAME_LENGTH);
}

static void spectral_whiten(const float32_t *frame, float32_t *whitened_mag)
{
    arm_copy_f32(frame, fft_buf, FRAME_LENGTH);
    arm_rfft_fast_f32(&rfft_fwd, fft_buf, fft_buf, 0); // output: [DC, Nyq, Re1, Im1, Re2, Im2, ...]

    // Extract magnitude
    magnitude[0] = 0.0f; // remove DC bias from the mic
    magnitude[NUM_BINS - 1] = fabsf(fft_buf[1]);   // Nyquist
    arm_cmplx_mag_f32(&fft_buf[2], &magnitude[1], HOP_LENGTH - 1);

    // Sliding window box-car smoothing + whitening
    float32_t sum = 0.0f;
    for (int j = 0; j <= SMOOTHING_WINDOW && j < NUM_BINS; j++) {
        sum += magnitude[j];
    }

    for (int i = 0; i < NUM_BINS; i++) {
    	// Add value entering window
        int right = i + SMOOTHING_WINDOW;
        if (right < NUM_BINS && i > 0) {
            sum += magnitude[right];
        }

        // Subtract value exiting window
        int left = i - SMOOTHING_WINDOW - 1;
        if (left >= 0) {
            sum -= magnitude[left];
        }

        float32_t avg = (sum / (float32_t)SMOOTHING_KERNEL) + 1e-6f;
        whitened_mag[i] = magnitude[i] / avg;
    }
}

static void compute_autocorrelation(const float32_t *whitened_mag)
{
	// Step 1: Autocorrelation
    arm_mult_f32(whitened_mag, whitened_mag, magnitude, NUM_BINS);

    fft_buf[0] = magnitude[0];              // DC
    fft_buf[1] = magnitude[NUM_BINS - 1];   // Nyquist
    for (int i = 1; i < HOP_LENGTH; i++) {
        fft_buf[2 * i]     = magnitude[i];  // Real
        fft_buf[2 * i + 1] = 0.0f;          // Imag = 0
    }

    arm_rfft_fast_f32(&rfft_inv, fft_buf, fft_buf, 1);
}

static float32_t yin_estimate(void)
{
    // Step 2: Difference Function
    float32_t r0 = fft_buf[0];
    for (int i = 0; i < MAX_PERIOD; i++) {
        diff[i] = 2.0f * (r0 - fft_buf[i + 1]);
    }

    // Step 3: CMND
    float32_t running_sum = 0.0f;
    for (int i = 0; i < MAX_PERIOD; i++) {
        running_sum += diff[i];
        float32_t tau_val = (float32_t)(i + 1);
        diff[i] = (running_sum > 0.0f) ? (diff[i] * tau_val / running_sum) : 1.0f;
    }

    // Step 4: Trough detection
    const int start = MIN_PERIOD - 1;
    const int slice_len = YIN_SLICE_LEN;

    int best_idx = -1;
    int glob_min_idx = 0;
    float32_t glob_min = 1e9f;

    for (int i = 0; i < slice_len; i++) {
        float32_t val = diff[start + i];

        if (val < TROUGH_THRESHOLD) {
            int is_min = 1;
            if (i > 0 && val > diff[start + i - 1]) is_min = 0;
            if (i < (slice_len - 1) && val > diff[start + i + 1]) is_min = 0;
            if (is_min) {
            	best_idx = i;
            	break;
            }
        }

        if (val < glob_min) {
            glob_min = val;
            glob_min_idx = i;
        }
    }

    if (best_idx < 0) best_idx = glob_min_idx;

    // Step 5: Parabolic interpolation (use diff[start + tau_rel])
    float32_t shift = 0.0f;
    if (best_idx > 0 && best_idx < slice_len - 1) {
        float32_t left   = diff[start + best_idx - 1];
        float32_t center = diff[start + best_idx];
        float32_t right  = diff[start + best_idx + 1];

        float32_t a = right + left - 2.0f * center;
        float32_t b = (right - left) / 2.0f;

        if (fabsf(a) > fabsf(b)) shift = -b / a;
    }

    float32_t tau_abs = (float32_t)(MIN_PERIOD + best_idx) + shift;
    return (float32_t)SR / tau_abs;
}

static float32_t hps_estimate(const float32_t *magnitude_spec, int n_harmonics)
{
    // Search range: convert Hz to bin indices
    // bin = freq * FRAME_LENGTH / SR
    int bin_min = (int)((float32_t)FREQ_LOWER * FRAME_LENGTH / SR);
    int bin_max = (int)((float32_t)FREQ_UPPER * FRAME_LENGTH / SR);

    // Safety clamp: highest bin we can reach for the Nth harmonic must be < NUM_BINS
    int max_bin_limit = (NUM_BINS - 1) / n_harmonics;
    if (bin_max > max_bin_limit) bin_max = max_bin_limit;

    float32_t best_val = 0.0f;
    int best_bin = bin_min;

    for (int k = bin_min; k <= bin_max; k++) {
        // Product of magnitudes at k, 2k, 3k, ..., n_harmonics*k
        float32_t prod = magnitude_spec[k];
        for (int h = 2; h <= n_harmonics; h++) {
            prod *= magnitude_spec[k * h];
        }

        if (prod > best_val) {
            best_val = prod;
            best_bin = k;
        }
    }

    // Convert bin back to frequency
    return (float32_t)best_bin * (float32_t)SR / (float32_t)FRAME_LENGTH;
}

float32_t preprocess_audio(const float32_t *frame)
{
	arm_copy_f32((float32_t *)frame, frame_scratch, FRAME_LENGTH);

	float32_t mean, variance;
	arm_mean_f32(frame_scratch, FRAME_LENGTH, &mean);
	arm_var_f32(frame_scratch, FRAME_LENGTH, &variance);

	float32_t f0_yin, f0_hps, f0;
	if (attack_wait_counter > 0) {
		f0 = -1;
		attack_wait_counter--;
	}
	else if (variance < SILENCE_THRESHOLD) {
		f0 = 0.0f;
	}
	else if (prev_variance > 1.0f && variance > prev_variance * NOTE_ONSET) {
		f0 = -1;
		attack_wait_counter = WAIT_ATTACK;
	}
	else {
		arm_offset_f32(frame_scratch, -mean, frame_scratch, FRAME_LENGTH);
		spectral_whiten(frame_scratch, whitened_buf);
		f0_hps = hps_estimate(magnitude, 4);
		compute_autocorrelation(whitened_buf);
		f0_yin = yin_estimate();

		if (f0_hps > 250) {
			f0 = f0_hps;
		}
		else {
			f0 = f0_yin;
		}
	}

	prev_variance = variance;
	return f0;
}
