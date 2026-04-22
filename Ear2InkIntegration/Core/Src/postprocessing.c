/*
 * postprocessing.c
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#include "postprocessing.h"
#include <math.h>

static float32_t median3(float32_t a, float32_t b, float32_t c)
{
    if (a > b) { float32_t t = a; a = b; b = t; }
    if (b > c) { float32_t t = b; b = c; c = t; }
    if (a > b) { float32_t t = a; a = b; b = t; }
    return b;
}

int8_t freq_to_midi(float32_t freq)
{
    return (int8_t)roundf(69.0f + 12.0f * log2f(freq / 440.0f));
}

static int create_note_event(NoteEvent *events, int idx, int max_events,
                      float32_t start, int frames, float32_t pitch_sum,
                      int pitch_count, float32_t end_time, int min_frames)
{
    if (start >= 0.0f && frames >= min_frames && idx < max_events) {
        float32_t avg_pitch = pitch_sum / (float32_t)pitch_count;
        events[idx].type      = EVENT_NOTE;
        events[idx].start     = start;
        events[idx].end       = end_time;
        events[idx].pitch     = avg_pitch;
        events[idx].midi_note = freq_to_midi(avg_pitch);
        events[idx].delta     = 0.0f;
        return 1;
    }
    return 0;
}

static int create_rest_event(NoteEvent *events, int idx, int max_events,
                      float32_t start, int frames, float32_t end_time,
                      int min_frames)
{
    if (start >= 0.0f && frames >= min_frames && idx < max_events) {
        events[idx].type      = EVENT_REST;
        events[idx].start     = start;
        events[idx].end       = end_time;
        events[idx].pitch     = 0.0f;
        events[idx].midi_note = -1;
        events[idx].delta     = 0.0f;
        return 1;
    }
    return 0;
}

int segment_notes(const float32_t *f0_array, const float32_t *time_array,
                  int num_frames, int min_frames, float32_t pitch_tolerance,
                  NoteEvent *events, int max_events)
{
    int ec = 0;  /* event count */

    float32_t fifo[3] = {0};
    int fifo_pos = 0, fifo_n = 0;

    float32_t ns = -1.0f;   /* note start */
    int nf = 0;             /* note frames */
    float32_t pa = 0.0f;    /* pitch accumulator */
    int pc = 0;             /* pitch count */

    float32_t rs = -1.0f;   /* rest start */
    int rf = 0;             /* rest frames */

    for (int i = 0; i < num_frames; i++) {
        float32_t f0 = f0_array[i];
        float32_t t  = time_array[i];

        fifo[fifo_pos % 3] = f0;
        fifo_pos++;
        fifo_n = (fifo_pos < 3) ? fifo_pos : 3;

        float32_t fm;
        if      (fifo_n == 1) fm = fifo[0];
        else if (fifo_n == 2) fm = (fifo[0] + fifo[1]) * 0.5f;
        else                  fm = median3(fifo[0], fifo[1], fifo[2]);

        if (isnan(fm)) {
            ec += create_note_event(events, ec, max_events, ns, nf, pa, pc, t, min_frames);
            ns = -1.0f; nf = 0; pa = 0.0f; pc = 0;
            ec += create_rest_event(events, ec, max_events, rs, rf, t, min_frames);
            rs = -1.0f; rf = 0;
        }
        else if (fm == 0.0f) {
            ec += create_note_event(events, ec, max_events, ns, nf, pa, pc, t, min_frames);
            ns = -1.0f; nf = 0; pa = 0.0f; pc = 0;
            if (rs < 0.0f) { rs = t; rf = 1; } else { rf++; }
        }
        else {
            ec += create_rest_event(events, ec, max_events, rs, rf, t, min_frames);
            rs = -1.0f; rf = 0;

            if (ns < 0.0f) {
                ns = t; nf = 1; pa = fm; pc = 1;
            } else {
                float32_t avg = pa / (float32_t)pc;
                float32_t cents = 1200.0f * log2f(fm / avg);
                if (fabsf(cents) < pitch_tolerance) {
                    nf++; pa += fm; pc++;
                } else {
                    ec += create_note_event(events, ec, max_events, ns, nf, pa, pc, t, min_frames);
                    ns = t; nf = 1; pa = fm; pc = 1;
                }
            }
        }
    }

    float32_t ft = (num_frames > 0) ? time_array[num_frames - 1] : 0.0f;
    ec += create_note_event(events, ec, max_events, ns, nf, pa, pc, ft, min_frames);
    ec += create_rest_event(events, ec, max_events, rs, rf, ft, min_frames);

    return ec;
}

void compensate_onset(NoteEvent *events, int count)
{
    float32_t offset = (float32_t)WAIT_ATTACK * FRAME_TIME;
    for (int i = 0; i < count; i++) {
        events[i].start -= offset;
        if (events[i].start < 0.0f) events[i].start = 0.0f;
    }
}

int snap_notes(NoteEvent *events, int count, float32_t bpm)
{
    float32_t grid = 15.0f / bpm;
    for (int i = 0; i < count; i++) {
        float32_t s = roundf(events[i].start / grid) * grid;
        float32_t e = roundf(events[i].end   / grid) * grid;
        if (e <= s) e = s + grid;
        events[i].start = s;
        events[i].end   = e;
        events[i].delta = e - s;
    }
    return count;
}
