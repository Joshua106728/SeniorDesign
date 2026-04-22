/*
 * yin.h
 *
 *  Created on: Apr 20, 2026
 *      Author: jhwjh
 */

#ifndef YIN_H
#define YIN_H

#include "arm_math.h"

void yin_init(void);
float32_t yin_estimate_f0(const float32_t *frame);

/* ---- Debug snapshots ---------------------------------------------------- */
extern float32_t dbg_yin_autocorr_r0;
extern float32_t dbg_yin_glob_min;
extern int32_t   dbg_yin_best_idx;
extern float32_t dbg_yin_tau_abs;
extern float32_t dbg_yin_f0;

#endif /* YIN_H */
