
from pathlib import Path
import librosa
import numpy as np
from yin import yin

frame_length = 2048
hop_length = 512
sr = 44100

def freq_to_midi(f0):
    # MIDI note formula = 69 + 12log_2(f/440)
    midi_notes = 69 + 12 * np.log2(f0 / 440)
    return np.round(midi_notes).astype(int)

def encode_variable_length(value):
    """Encode an integer into MIDI variable-length quantity format."""
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
    return encode_variable_length(delta) + [0x90, note & 0x7F, velocity & 0x7F]

def note_off(delta, note, velocity):
    return encode_variable_length(delta) + [0x80, note & 0x7F, velocity & 0x7F]

def seconds_to_ticks(seconds, ticks_per_beat=96, bpm=120):
    sec_per_beat = 60.0 / bpm
    return int(round(seconds / sec_per_beat * ticks_per_beat))

def write_midi_file(write_midi, filename="output.mid"):
    ticks_per_beat = 96
    bpm = 120
    
    track_data = []

    for _, event in write_midi.items():
        note = int(event["note"])
        velocity = int(event["velocity"])
        duration_ticks = seconds_to_ticks(event["time"], ticks_per_beat, bpm)

        if event["on_off"] == 1 and velocity > 0:
            # note on at delta=0
            track_data += note_on(0, note, velocity)
            # note off after duration
            track_data += note_off(duration_ticks, note, 64)

    # end of track
    track_data += [0x00, 0xFF, 0x2F, 0x00]

    # track chunk
    track_chunk = b"MTrk" + len(track_data).to_bytes(4, "big") + bytes(track_data)

    # header chunk (Format 0, 1 track, ticks_per_beat resolution)
    header = b"MThd" + (6).to_bytes(4, "big")
    header += (0).to_bytes(2, "big")   # format type 0
    header += (1).to_bytes(2, "big")   # one track
    header += (ticks_per_beat).to_bytes(2, "big")

    # final file
    with open(filename, "wb") as f:
        f.write(header + track_chunk)

    print(f"MIDI file written to {filename}")

def main():
    filepath = Path("Python_Implementation\single\A4_2s.wav")
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
        "time": time_length
    }

    for x in range(1, len(notes)):
        # print(f"Index {x}: note: {notes[x]} | velocity: {velocity[x]}")
        if notes[x] == write_midi[counter]['note'] and abs(velocity[x] - write_midi[counter]["velocity"] < 5):
            # same note -> extend time duration
            write_midi[counter]["time"] += time_length
        else:
            # new note -> new entry
            counter += 1
            write_midi[counter] = {
                "note": notes[x],
                "on_off": 1 if velocity[x] > 0 else 0,
                "velocity": velocity[x],
                "time": time_length
            }

    for k, v in write_midi.items():
        print(f"{k}: {v}")

    # Write to MIDI file
    write_midi_file(write_midi, "A4.mid")

if __name__=='__main__':
    main()