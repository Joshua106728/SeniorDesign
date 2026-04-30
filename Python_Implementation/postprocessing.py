
import numpy as np
from collections import deque
from constants import *

def frames_per_note_duration(bpm, frame_time):
    note_duration = 15.0 / bpm
    return note_duration // frame_time

def create_note_event(event, note_start, note_frames, note_pitch, curr_time, min_frames):
    if note_start is not None and note_frames >= min_frames:
        median_pitch = np.median(note_pitch)
        event.append({
            'type' : 'note',
            'start' : note_start,
            'end' : curr_time,
            'pitch' : median_pitch,
            'midi' : freq_to_midi(median_pitch)
        })
        return event, None, 0, []
    return event, note_start, note_frames, note_pitch

def create_rest_event(event, rest_start, rest_frames, curr_time, min_frames):
    if rest_start is not None and rest_frames >= min_frames:
        event.append({
            'type' : 'rest',
            'start' : rest_start,
            'end' : curr_time,
            'pitch' : 0,
            'midi' : -1
        })
        return event, None, 0
    return event, rest_start, rest_frames

def segment_notes(f0_estimates, times_f0, min_frames, pitch_tolerance=100):
    note_events = []
    note_start = None
    note_frames = 0
    note_pitch = []
    rest_start = None
    rest_frames = 0
    fifo_buffer = deque(maxlen=3)

    for i, (f0, time) in enumerate(zip(f0_estimates, times_f0)):
        fifo_buffer.append(f0)
        f0 = np.median(fifo_buffer)

        # skip nans = waiting guitar attack
        if np.isnan(f0):
            # end current note / rest
            note_events, note_start, note_frames, note_pitch = create_note_event(note_events, note_start, note_frames, note_pitch, time, min_frames)
            note_events, rest_start, rest_frames = create_rest_event(note_events, rest_start, rest_frames, time, min_frames)

        # f0 = 0 (rest)
        elif f0 == 0:
            # end current note
            note_events, note_start, note_frames, note_pitch = create_note_event(note_events, note_start, note_frames, note_pitch, time, min_frames)

            # continue rest
            if rest_start is None:
                rest_start = time
                rest_frames = 1
            else:
                rest_frames += 1

        # f0 != 0 (note)
        else:
            # end rest
            note_events, rest_start, rest_frames = create_rest_event(note_events, rest_start, rest_frames, time, min_frames)

            # continue / start note
            if note_start is None:
                note_start = time
                note_frames = 1
                note_pitch.append(f0)
            else:
                median_so_far = np.median(note_pitch)
                cents_diff = 1200 * np.log2(f0 / median_so_far)
                if abs(cents_diff) < pitch_tolerance:
                    note_frames += 1
                    note_pitch.append(f0)
                else:
                    note_events, note_start, note_frames, note_pitch = create_note_event(note_events, note_start, note_frames, note_pitch, time, min_frames)

    # Handle final note / rest
    note_events, note_start, note_frames, note_pitch = create_note_event(note_events, note_start, note_frames, note_pitch, time, min_frames)
    note_events, rest_start, rest_frames = create_rest_event(note_events, rest_start, rest_frames, time, min_frames)
    return note_events

def freq_to_midi(freq_hz):
    return int(round(69 + 12 * np.log2(freq_hz / 440.0)))

def snap_notes(events, bpm):
    note_duration = 15.0 / bpm
    notes = []

    for event in events:
        start = round(event['start'] / note_duration) * note_duration
        end = round(event['end'] / note_duration) * note_duration

        if end <= start:
            end = start + note_duration

        notes.append({
            **event,
            'start': start,
            'end': end,
            'delta' : end - start
        })

    return notes

def postprocess_audio(f0_estimates, times_f0):
    min_frames = frames_per_note_duration(BPM, FRAME_LENGTH)
    notes = segment_notes(f0_estimates, times_f0, min_frames)

    # Account for skipped onset frames
    for note in notes:
        note['start'] -= (6 * FRAME_TIME)
        note['start'] = max(0, note['start'])

    # Quantize to tempo grid
    midi_notes = snap_notes(notes, BPM)

    return midi_notes