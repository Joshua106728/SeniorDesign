
from pathlib import Path
import librosa
import numpy as np
from yin import yin

frame_length = 2048
hop_length = 512

def freq_to_midi(f0):
    # MIDI note formula = 69 + 12log_2(f/440)
    midi_notes = 69 + 12 * np.log2(f0 / 440)
    return np.round(midi_notes).astype(int)

def main():
    filepath = Path("Python_Implementation\single\A4_2s.wav")
    y, sr = librosa.load(str(filepath), sr=None, mono=True)
    y = np.concatenate((np.zeros(frame_length - hop_length), y)) # pads so first point starts in the center
    f0, velocity = yin(y) # fundamental frequency of each frame
    notes = freq_to_midi(f0)

    print(len(velocity))
    for i in range(len(velocity)):
        print(velocity[i])


if __name__=='__main__':
    main()