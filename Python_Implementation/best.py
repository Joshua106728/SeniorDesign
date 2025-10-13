
from pathlib import Path
import librosa
import numpy as np
from yin import yin
from scipy.ndimage import median_filter

frame_length = 1024
hop_length = 512
sample_rate = 44100

def freq_to_midi(f0):
    # MIDI note formula = 69 + 12log_2(f/440)
    midi_notes = 69 + 12 * np.log2(f0 / 440)
    return np.round(midi_notes).astype(int)

def main():
    filepath = Path("twinkle_trim.wav")
    y, sr = librosa.load(str(filepath), sr=sample_rate, mono=True)

    # YIN Algorithm
    y = np.concatenate((np.zeros(frame_length - hop_length), y)) # pads so first point starts in the center
    f0, velocity = yin(y) # fundamental frequency of each frame
    f0_smooth = median_filter(f0, size=9)  # adjust window (in frames)

    # temp
    f0_smooth = f0_smooth.astype(int)
    velocity = velocity.astype(int)

    # declare MIDI dictionary
    write_midi = {}
    counter = 0
    time_length = hop_length / sr

    # first entry
    write_midi[counter] = {
        "note": f0_smooth[0],
        "on_off": 1 if velocity[0] > 0 else 0,
        "velocity": velocity[0],
        "time": time_length,
    }

    for x in range(1, len(f0_smooth)):
        # print(f"Index {x}: note: {notes[x]} | velocity: {velocity[x]}")
        if f0_smooth[x] == write_midi[counter]['note']: # and abs(velocity[x] - write_midi[counter]["velocity"] < 5):
            # same note -> extend time duration
            write_midi[counter]["time"] += time_length
        else:
            # new note -> new entry
            counter += 1
            write_midi[counter] = {
                "note": f0_smooth[x],
                "on_off": 1 if velocity[x] > 0 else 0,
                "velocity": velocity[x],
                "time": time_length,
            }

    for k, v in write_midi.items():
        print(f"{k}: {v}")

if __name__=='__main__':
    main()