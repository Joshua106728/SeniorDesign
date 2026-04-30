/*
 * constants.h
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#ifndef INC_CONSTANTS_H_
#define INC_CONSTANTS_H_

#include "arm_math.h"
#include <stdint.h>

// Audio parameters
#define SR                  32000
#define FRAME_LENGTH        4096
#define HOP_LENGTH          2048
#define FRAME_TIME          ((float32_t)HOP_LENGTH / (float32_t)SR)

// I2S Mic parameters
#define MIC_BUF				HOP_LENGTH * 4 // 2 16-bit * 2 channel * double buffer
#define MIC_DOUBLE_BUF		MIC_BUF * 2

// Determine note
#define SILENCE_THRESHOLD	5.0e8f
#define NOTE_ONSET			4.0f
#define WAIT_ATTACK			4

// Frequency range
#define FREQ_LOWER          80
#define FREQ_UPPER          800
#define MIN_PERIOD          40      // SR / FREQ_UPPER
#define MAX_PERIOD          400     // SR / FREQ_LOWER

// Spectral whitening
#define SMOOTHING_WINDOW    15
#define SMOOTHING_KERNEL    31      // 2 * SMOOTHING_WINDOW + 1

// YIN
#define NUM_BINS            (HOP_LENGTH + 1)   // 2049
#define YIN_SLICE_LEN       (MAX_PERIOD - MIN_PERIOD + 1)  // 489
#define TROUGH_THRESHOLD    0.15f

// Postprocessing
#define BPM 				80
#define NOTE_DUR 			15.0f / (float32_t)BPM
#define MIN_FRAMES			3
#define MAX_FRAMES			850
#define PITCH_TOLERANCE		100

// MIDI
#define TICKS_PER_BEAT      96

// LED
#define BEAT_MS				750
#define FLASH_MS			150

// Note event types
#define EVENT_NOTE  0
#define EVENT_REST  1

typedef struct {
    uint8_t   type;
    float32_t start;
    float32_t end;
    float32_t pitch;
    int8_t    midi_note;
    float32_t delta;
} NoteEvent;

#endif /* INC_CONSTANTS_H_ */
