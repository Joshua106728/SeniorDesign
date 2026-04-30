
import numpy as np
from scipy.io.wavfile import write

def generate_sine_wave(pitch_hz, duration_sec, sample_rate=44100, amplitude=0.5):
    """Generate a sine wave for a given frequency and duration."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    waveform = amplitude * np.sin(2 * np.pi * pitch_hz * t)
    return waveform

def note_duration(note_type, tempo_bpm):
    """
    Convert note type (quarter, half, whole, etc.) into duration in seconds,
    based on tempo in beats per minute.
    """
    beat_duration = 60.0 / tempo_bpm  # seconds per beat
    durations = {
        "whole": 4 * beat_duration,
        "half": 2 * beat_duration,
        "quarter": beat_duration,
        "eighth": beat_duration / 2,
        "sixteenth": beat_duration / 4,
    }
    return durations.get(note_type.lower(), beat_duration)

def generate_song(notes, tempo_bpm=120, sample_rate=44100, amplitude=0.5, filename="song.wav"):
    """
    Generate a simple song from a list of (pitch, note_type) tuples.
    pitch can be a frequency in Hz or None for a rest.
    """
    song = np.array([], dtype=np.float32)

    for pitch, note_type in notes:
        dur = note_duration(note_type, tempo_bpm)
        waveform = generate_sine_wave(pitch, dur, sample_rate, amplitude)
        waveform_rest = np.zeros(int(sample_rate * 0.15)) # dur = sixteenth note
        song = np.concatenate((song, waveform, waveform_rest))

    # Scale to 16-bit PCM range
    waveform_int16 = np.int16(song / np.max(np.abs(song)) * 32767)

    write(filename, sample_rate, waveform_int16)
    print(f"✅ Song saved as {filename}")

# Example: "Twinkle Twinkle Little Star" (first few notes)
notes = [
    (261.63, "quarter"),  # C4
    (261.63, "quarter"),  # C4
    (392.00, "quarter"),  # G4
    (392.00, "quarter"),  # G4
    (440.00, "quarter"),  # A4
    (440.00, "quarter"),  # A4
    (392.00, "half"),     # G4
    (349.23, "quarter"),  # F4
    (349.23, "quarter"),  # F4
    (329.63, "quarter"),  # E4
    (329.63, "quarter"),  # E4
    (293.66, "quarter"),  # D4
    (293.66, "quarter"),  # D4
    (261.63, "half"),     # C4
    (392.00, "quarter"),  # G4
    (392.00, "quarter"),  # G4
    (349.23, "quarter"),  # F4
    (349.23, "quarter"),  # F4
    (329.63, "quarter"),  # E4
    (329.63, "quarter"),  # E4
    (293.66, "half"),     # D4
    (392.00, "quarter"),  # G4
    (392.00, "quarter"),  # G4
    (349.23, "quarter"),  # F4
    (349.23, "quarter"),  # F4
    (329.63, "quarter"),  # E4
    (329.63, "quarter"),  # E4
    (293.66, "half"),     # D4
    (261.63, "quarter"),  # C4
    (261.63, "quarter"),  # C4
    (392.00, "quarter"),  # G4
    (392.00, "quarter"),  # G4
    (440.00, "quarter"),  # A4
    (440.00, "quarter"),  # A4
    (392.00, "half"),     # G4
    (349.23, "quarter"),  # F4
    (349.23, "quarter"),  # F4
    (329.63, "quarter"),  # E4
    (329.63, "quarter"),  # E4
    (293.66, "quarter"),  # D4
    (293.66, "quarter"),  # D4
    (261.63, "half"),     # C4
]

generate_song(notes, tempo_bpm=100, filename="twinkle.wav")
