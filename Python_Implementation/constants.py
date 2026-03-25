
SR = 44100 # sampling rate
FRAME_LENGTH = 4096 # samples in one frame
HOP_LENGTH = 2048 # sample interval between FFT processing
FRAME_TIME = HOP_LENGTH / SR # sample interval in sec between FFT processing
FREQ_LOWER = 80 # lowest possible guitar note
FREQ_UPPER = 700 # highest possible guitar note
MIN_PERIOD = 63 # sr / freq_upper (for CMND func)
MAX_PERIOD = 551 # sr / freq_lower (for CMND func)
SMOOTHING_WINDOW = 15 # smoothing window for spectral whiten function
NOTE_THRESHOLD = 0.1 # must be greater to be considered a note
NOTE_ONSET_THRESHOLD = 0.7 # rms difference to be considered a note onset event
WAIT_ATTACK = 6 # amt of frames skipped after note onset
TROUGH_THRESHOLD = 0.1 # to count as a trough in YIN algorithm


# Change based on audio file!!
BPM = 106 # tempo (will be set by HW in actual implementation)
AUDIO_FILE = "audio_files/guitar-single-notes.m4a" # path to audio file
PLOT_RESULTS = True # save graphs or not
target_frequencies = [82, 110, 147, 196, 247, 330] # expected note values
target_times = [0.23219955, 1.97369615, 4.01705215, 6.26938776, 7.94122449, 9.35764172] # note change timing from graphing
