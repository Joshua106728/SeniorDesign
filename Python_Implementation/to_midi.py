
from constants import *

def var_length_encoding(value):
    buffer = value & 0x7F
    bytes_out = []
    while value > 0x7F:
        value >>= 7
        buffer <<= 8
        buffer |= ((value & 0x7F) | 0x80)
    while True:
        bytes_out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes_out

def note_on(delta, note, velocity):
    return var_length_encoding(delta) + [0x90, note & 0x7F, velocity & 0x7F]

def note_off(delta, note, velocity):
    return var_length_encoding(delta) + [0x80, note & 0x7F, velocity & 0x7F]

def seconds_to_ticks(seconds, ticks_per_beat, bpm):
    sec_per_beat = 60.0 / bpm
    return int(round(seconds / sec_per_beat * ticks_per_beat))

def create_midi_notes(midi_notes):
    # write header (once 'start recording' is pressed during LCD countdown)
    ticks_per_beat = 96
    format_type = 0
    num_tracks = 1

    header = b"MThd"                            # 0-3 | 4D 54 68 64 | "MThd" in ASCII
    header += (6).to_bytes(4, byteorder='big')  # 4-7 | 00 00 00 06 | Header data size = 6 bytes
    header += format_type.to_bytes(2, byteorder='big') # 8-9 | 00 00 | Format = 0 (single track)
    header += num_tracks.to_bytes(2, byteorder='big')  # 10-11 | 00 01 | Number of tracks = 1
    header += ticks_per_beat.to_bytes(2, byteorder='big') # 12-13 | 00 60 | Ticks per beat = 96 (0x60 in hex)

    # write meta event format [delta_time] [0xFF] [meta_type] [length] [data...]
    track_data = []

    microseconds_per_beat = int(60_000_000 / BPM)
    tempo_bytes = list(microseconds_per_beat.to_bytes(3, byteorder='big'))
    track_data += [0x00]           # Delta time = 0 (happens immediately)
    track_data += [0xFF]           # Meta event marker
    track_data += [0x51]           # Meta type 0x51 = "Set Tempo"
    track_data += [0x03]           # Length = 3 bytes
    track_data += tempo_bytes      # Actual tempo data

    # write track data
    accumulated_gap_ticks = 0
    new_event = seconds_to_ticks(FRAME_TIME, ticks_per_beat, BPM)
    velocity = 64

    for i, event in enumerate(midi_notes):
        duration_ticks = seconds_to_ticks(event['delta'], ticks_per_beat, BPM)
        if event['type'] == 'note':
            midi_note = event['midi']

            # note on occurs after accumulated gap
            track_data += note_on(accumulated_gap_ticks, midi_note, velocity)

            # note off occurs after note duration
            track_data += note_off(duration_ticks, midi_note, velocity)

            accumulated_gap_ticks = 0
        elif event['type'] == 'rest':
            accumulated_gap_ticks += duration_ticks

    track_data += [0x00]           # Delta time = 0
    track_data += [0xFF]           # Meta event marker
    track_data += [0x2F]           # Meta type 0x2F = "End of Track"
    track_data += [0x00]           # Length = 0 (no data)

    # write track chunk
    chunk_id = b"MTrk"
    track_length = len(track_data)
    track_chunk = chunk_id + track_length.to_bytes(4, byteorder='big') + bytes(track_data)

    midi_file = header + track_chunk
    with open("output.mid", "wb") as f:
        f.write(midi_file)