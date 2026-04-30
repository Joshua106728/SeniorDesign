/*
 * to_midi.c
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#include "to_midi.h"
#include <math.h>
#include <string.h>

static int write_var_length(uint8_t *buf, uint32_t value)
{
    uint8_t temp[4];
    int n = 0;
    temp[n++] = value & 0x7F;
    while (value > 0x7F) {
        value >>= 7;
        temp[n++] = (value & 0x7F) | 0x80;
    }
    for (int i = 0; i < n; i++) buf[i] = temp[n - 1 - i];
    return n;
}

static int seconds_to_ticks(float32_t seconds, float32_t bpm)
{
    float32_t spb = 60.0f / bpm;
    return (int)roundf(seconds / spb * (float32_t)TICKS_PER_BEAT);
}

static int write_note_on(uint8_t *buf, uint32_t delta, uint8_t note, uint8_t vel)
{
    int n = write_var_length(buf, delta);
    buf[n++] = 0x90;
    buf[n++] = note & 0x7F;
    buf[n++] = vel  & 0x7F;
    return n;
}

static int write_note_off(uint8_t *buf, uint32_t delta, uint8_t note, uint8_t vel)
{
    int n = write_var_length(buf, delta);
    buf[n++] = 0x80;
    buf[n++] = note & 0x7F;
    buf[n++] = vel  & 0x7F;
    return n;
}

int write_midi_file(const NoteEvent *events, int count,
                    float32_t bpm, uint8_t *buffer, int buffer_size)
{
    int pos = 0;

    /* Header: MThd */
    memcpy(&buffer[pos], "MThd", 4); pos += 4;
    buffer[pos++]=0; buffer[pos++]=0; buffer[pos++]=0; buffer[pos++]=6;
    buffer[pos++]=0; buffer[pos++]=0;  /* format 0 */
    buffer[pos++]=0; buffer[pos++]=1;  /* 1 track */
    buffer[pos++]=(uint8_t)(TICKS_PER_BEAT>>8);
    buffer[pos++]=(uint8_t)(TICKS_PER_BEAT&0xFF);

    /* Track: MTrk */
    memcpy(&buffer[pos], "MTrk", 4); pos += 4;
    int tl_pos = pos; pos += 4;       /* placeholder for length */
    int t_start = pos;

    /* Tempo meta event */
    uint32_t uspb = (uint32_t)(60000000.0f / bpm);
    buffer[pos++]=0x00; buffer[pos++]=0xFF; buffer[pos++]=0x51; buffer[pos++]=0x03;
    buffer[pos++]=(uint8_t)(uspb>>16);
    buffer[pos++]=(uint8_t)(uspb>>8);
    buffer[pos++]=(uint8_t)(uspb);

    /* Note / rest events */
    float32_t prev_note_end = 0.0f;
    for (int i = 0; i < count; i++) {
        if (events[i].type == EVENT_NOTE) {
            // Use the gap from previous note's end to this note's start
        	float32_t gap_sec = events[i].start - prev_note_end;
        	if (gap_sec < 0.0f) gap_sec = 0.0f;
            uint32_t delta = (uint32_t)seconds_to_ticks(gap_sec, bpm);
            uint32_t dur = (uint32_t)seconds_to_ticks(events[i].delta, bpm);
            uint8_t n = (uint8_t)events[i].midi_note;
            pos += write_note_on (&buffer[pos], delta, n, 64);
            pos += write_note_off(&buffer[pos], dur,   n, 64);
            prev_note_end = events[i].end;
        }
    }

    /* End of track */
    buffer[pos++]=0x00; buffer[pos++]=0xFF;
    buffer[pos++]=0x2F; buffer[pos++]=0x00;

    /* Fill in track length */
    uint32_t tl = (uint32_t)(pos - t_start);
    buffer[tl_pos+0]=(uint8_t)(tl>>24);
    buffer[tl_pos+1]=(uint8_t)(tl>>16);
    buffer[tl_pos+2]=(uint8_t)(tl>>8);
    buffer[tl_pos+3]=(uint8_t)(tl);

    return pos;
}
