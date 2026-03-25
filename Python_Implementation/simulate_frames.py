import librosa
import matplotlib.pyplot as plt
from pathlib import Path
from constants import *
from preprocessing import process_audio

"""
Note, if you are working with any audio file type that isn't .wav, you will need to install FFmpeg 
(audio backend librosa uses to process these types of files)
https://ffmpeg.org/download.html <-- can download here and add to your PATH
"""

audio, sr = librosa.load(AUDIO_FILE, sr=SR, mono=True) # load audio file (ignore warning)
frames = librosa.util.frame(audio, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH) # split into frames (what we'll see in HW)

# process data one frame at a time
frame_counter = 0 # initialize as a 16-bit unsigned int
f0_estimates = []
f0_times = []
note_onset = []
prev_energy = 0
note_attack = 0

for i in range(frames.shape[1]):
    frame_counter = i
    frame = frames[:, i]
    prev_energy, note_attack, f0_estimates, f0_times, note_onset = process_audio(frame, frame_counter, f0_estimates, f0_times, note_onset, prev_energy, note_attack)

# plot data
if PLOT_RESULTS:
    # Create audio_plots folder if it doesn't exist
    output_dir = Path('audio_plots')
    output_dir.mkdir(exist_ok=True)

    # PLOT 1: original waveform w/ target frequencies
    fig, ax1 = plt.subplots(figsize=(14, 6))

    audio_end_time = len(audio) / sr
    extended_target_times = list(target_times)
    extended_target_frequencies = list(target_frequencies)
    if extended_target_times and extended_target_frequencies:
        if extended_target_times[-1] < audio_end_time:
            extended_target_times.append(audio_end_time)
            extended_target_frequencies.append(extended_target_frequencies[-1])

    librosa.display.waveshow(y=audio, sr=sr, ax=ax1, color='blue', alpha=0.7)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(-0.25, 0.25)

    ax2 = ax1.twinx()
    ax2.step(extended_target_times, extended_target_frequencies, where='post', color='green', linestyle='--', linewidth=2, label='Target Frequencies')
    ax2.set_ylabel('Frequency (Hz)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.set_ylim(0, 800)

    plt.title('Original Waveform with Target Frequencies')
    ax1.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Save instead of showing
    output_path = output_dir / 'orig_waveform.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    # PLOT 2: Preprocessed Data
    fig, ax1 = plt.subplots(figsize=(14, 6))

    librosa.display.waveshow(y=audio, sr=sr, ax=ax1, color='blue', alpha=0.7, label='Original Waveform')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(-0.25, 0.25)

    ax2 = ax1.twinx()
    ax2.plot(f0_times, f0_estimates, color='red', linewidth=2, label='Pitch Estimation')
    ax2.set_ylabel('Fundamental Frequency (Hz)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.set_ylim(0, 800)
    ax2.step(extended_target_times, extended_target_frequencies, where='post', color='green', linestyle='--', linewidth=2, label='Target Frequencies')
    plt.title('YIN Pitch Estimations')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # note onsets
    ax1.vlines(note_onset, -0.25, 0.25, color='purple', linestyle='-')

    fig.legend(loc='upper right', bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    plt.tight_layout()

    # Save instead of showing
    output_path = output_dir / 'yin_estimate_testing.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
