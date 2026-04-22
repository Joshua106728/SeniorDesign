/*
 * postprocessing.h
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#ifndef INC_POSTPROCESSING_H_
#define INC_POSTPROCESSING_H_

#include "constants.h"

int segment_notes(const float32_t *f0_array, const float32_t *time_array,
                  int num_frames, int min_frames, float32_t pitch_tolerance,
                  NoteEvent *events, int max_events);

void compensate_onset(NoteEvent *events, int count);
int  snap_notes(NoteEvent *events, int count, float32_t bpm);
int8_t freq_to_midi(float32_t freq);

#endif /* INC_POSTPROCESSING_H_ */
