
from pathlib import Path
import librosa
import numpy as np
from yin import yin

frame_length = 1024
hop_length = 512
sr = 44100

def freq_to_midi(f0):
    # MIDI note formula = 69 + 12log_2(f/440)
    midi_notes = 69 + 12 * np.log2(f0 / 440)
    return np.round(midi_notes).astype(int)

# refer to Week 7 project journal
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

def seconds_to_ticks(seconds, ticks_per_beat=96, bpm=120):
    sec_per_beat = 60.0 / bpm
    return int(round(seconds / sec_per_beat * ticks_per_beat))

def write_midi_file(write_midi, filename, time_length):
    ticks_per_beat = 96
    bpm = 120
    track_data = []

    # === Tempo Meta Event ===
    microsec_per_beat = int(60_000_000 / bpm)
    tempo_bytes = list(microsec_per_beat.to_bytes(3, byteorder='big'))
    track_data += [0x00, 0xFF, 0x51, 0x03] + tempo_bytes
    new_event = seconds_to_ticks(time_length, ticks_per_beat, bpm)

    for _, event in write_midi.items():
        note = int(event["note"])
        velocity = int(event["velocity"])
        duration = event["time"]

        # Convert seconds → ticks
        duration_ticks = seconds_to_ticks(duration, ticks_per_beat, bpm)

        if event["on_off"] == 1 and velocity > 0:
            # note_on after delta_ticks (gap since last note)
            track_data += note_on(new_event, note, velocity)
            # note_off after duration
            track_data += note_off(duration_ticks, note, 64)

    # end of track
    track_data += [0x00, 0xFF, 0x2F, 0x00]

    # build chunks
    track_chunk = b"MTrk" + len(track_data).to_bytes(4, "big") + bytes(track_data)
    header = (
        b"MThd" + (6).to_bytes(4, "big")
        + (0).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
        + (ticks_per_beat).to_bytes(2, "big")
    )

    with open(filename, "wb") as f:
        f.write(header + track_chunk)

    print(f"MIDI file written to {filename}")

def main():
    filepath = Path("Python_Implementation\single\clouds_for_today.mp3")
    y, sr = librosa.load(str(filepath), sr=None, mono=True)

    # YIN Algorithm
    y = np.concatenate((np.zeros(frame_length - hop_length), y)) # pads so first point starts in the center
    f0, velocity = yin(y) # fundamental frequency of each frame

    # Convert to MIDI
    time_length = hop_length / sr # we are 'hopping' from note to note
    notes = freq_to_midi(f0)
    velocity = velocity.astype(int)

    # declare MIDI dictionary
    write_midi = {}
    counter = 0

    # first entry
    write_midi[counter] = {
        "note": notes[0],
        "on_off": 1 if velocity[0] > 0 else 0,
        "velocity": velocity[0],
        "time": time_length,
    }

    for x in range(1, len(notes)):
        # print(f"Index {x}: note: {notes[x]} | velocity: {velocity[x]}")
        if notes[x] == write_midi[counter]['note']: # and abs(velocity[x] - write_midi[counter]["velocity"] < 5):
            # same note -> extend time duration
            write_midi[counter]["time"] += time_length
        else:
            # new note -> new entry
            counter += 1
            write_midi[counter] = {
                "note": notes[x],
                "on_off": 1 if velocity[x] > 0 else 0,
                "velocity": velocity[x],
                "time": time_length,
            }

    for k, v in write_midi.items():
        print(f"{k}: {v}")

    # Write to MIDI file
    write_midi_file(write_midi, "clouds.mid", time_length)

if __name__=='__main__':
    main()