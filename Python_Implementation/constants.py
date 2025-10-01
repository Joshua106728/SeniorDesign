
import librosa
import numpy as np

SEMITONES_IN_OCTAVE = 12
AUDIO_FILE = "single/jingle_bells.mp3"   # Path to your input file
PLOT_RESULTS = False                       # Whether to plot results
CORRECTION_METHOD = "scale"               # "closest" or "scale"
SCALE = "D:min"                           # Used only if CORRECTION_METHOD == "scale"
SR = 44100 ####### Change SR
fmin = librosa.note_to_hz('C2')
fmax = librosa.note_to_hz('C7')
frame_length = 1024
hop_length = frame_length // 2
win_length = frame_length // 2
trough_threshold = 0.1
# Calculate minimum and maximum periods
min_period = int(np.floor(SR / fmax))
max_period = min(int(np.ceil(SR / fmin)), frame_length - win_length - 1)