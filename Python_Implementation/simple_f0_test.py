
import numpy as np
from scipy.io.wavfile import write

def generate_sine_wave(pitch_hz, duration_sec, sample_rate=44100, amplitude=0.5, filename="output.wav"):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    waveform = amplitude * np.sin(2 * np.pi * pitch_hz * t)

    # Scale to 16-bit PCM range
    waveform_int16 = np.int16(waveform * 32767)

    # Save to .wav
    write(filename, sample_rate, waveform_int16)

    return waveform

# Generate a 440 Hz (A4) sine wave lasting 2 seconds
generate_sine_wave(440.0, 2.0, filename="A4_2s.wav")

# Generate middle C (261.63 Hz) lasting 1.5 seconds
generate_sine_wave(261.63, 1.5, filename="C4_1_5s.wav")