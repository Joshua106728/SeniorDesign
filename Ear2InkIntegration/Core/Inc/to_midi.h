/*
 * to_midi.h
 *
 *  Created on: Apr 3, 2026
 *      Author: jhwjh
 */

#ifndef INC_TO_MIDI_H_
#define INC_TO_MIDI_H_

#include "constants.h"

int write_midi_file(const NoteEvent *events, int count,
                    float32_t bpm, uint8_t *buffer, int buffer_size);

#endif /* INC_TO_MIDI_H_ */
