
from pathlib import Path
import librosa
import numpy as np
from yin import yin
from mido import MidiFile, MidiTrack, Message, MetaMessage
from scipy.ndimage import median_filter

frame_length = 1024
hop_length = 512
sr = 44100

def f0_to_midi_note(f0):
    """Convert frequency (Hz) to MIDI note number."""
    if f0 <= 0 or np.isnan(f0):
        return None
    midi_note = 69 + 12 * np.log2(f0 / 440.0)
    return int(round(midi_note))

def smooth_f0(f0_array, kernel_size=5):
    """Apply median filter to smooth f0 and remove outliers."""
    # Replace invalid values with 0 for filtering
    f0_clean = np.where(np.isnan(f0_array) | (f0_array <= 0), 0, f0_array)
    smoothed = median_filter(f0_clean, size=kernel_size)
    # Restore invalid values
    smoothed = np.where(f0_clean == 0, 0, smoothed)
    return smoothed

def quantize_notes(midi_notes, min_duration=5):
    """
    Merge consecutive frames of the same note into sustained notes.
    
    Parameters:
    -----------
    midi_notes : array-like
        MIDI note numbers for each frame (None for silence)
    min_duration : int
        Minimum number of frames for a valid note
    
    Returns:
    --------
    list of tuples: (note, start_frame, duration_in_frames)
    """
    if len(midi_notes) == 0:
        return []
    
    notes = []
    current_note = midi_notes[0]
    start_frame = 0
    
    for i in range(1, len(midi_notes)):
        # If note changes or we hit silence
        if midi_notes[i] != current_note:
            # Save the previous note if it meets minimum duration
            duration = i - start_frame
            if current_note is not None and duration >= min_duration:
                notes.append((current_note, start_frame, duration))
            
            # Start new note
            current_note = midi_notes[i]
            start_frame = i
    
    # Handle final note
    duration = len(midi_notes) - start_frame
    if current_note is not None and duration >= min_duration:
        notes.append((current_note, start_frame, duration))
    
    return notes

def filter_pitch_outliers(f0_array, max_semitone_jump=7):
    """
    Remove implausible pitch jumps (likely octave errors).
    
    Parameters:
    -----------
    f0_array : array-like
        Fundamental frequencies
    max_semitone_jump : int
        Maximum allowed semitone jump between consecutive valid frames
    
    Returns:
    --------
    Filtered f0 array
    """
    filtered = f0_array.copy()
    
    # Find last valid f0
    last_valid_f0 = None
    for i in range(len(filtered)):
        if filtered[i] > 0 and not np.isnan(filtered[i]):
            if last_valid_f0 is not None:
                # Calculate semitone difference
                semitone_diff = abs(12 * np.log2(filtered[i] / last_valid_f0))
                
                # If jump is too large, mark as invalid
                if semitone_diff > max_semitone_jump:
                    filtered[i] = 0
                else:
                    last_valid_f0 = filtered[i]
            else:
                last_valid_f0 = filtered[i]
    
    return filtered

def create_midi_from_arrays(f0_array, velocity_array, hop_length=512, sr=44100, 
                            output_file='output.mid', tempo=120,
                            smooth_kernel=5, min_note_frames=3, max_pitch_jump=None,
                            min_velocity_threshold=0.1):
    """
    Create a MIDI file from fundamental frequency and velocity arrays.
    
    Parameters:
    -----------
    f0_array : array-like
        Fundamental frequencies in Hz for each frame
    velocity_array : array-like
        RMS velocities for each frame (should be normalized 0-1)
    hop_length : int
        Number of samples between frames (default: 512)
    sr : int
        Sample rate (default: 44100)
    output_file : str
        Output MIDI filename
    tempo : int
        Tempo in BPM (default: 120)
    smooth_kernel : int
        Kernel size for median filtering (default: 5)
    min_note_frames : int
        Minimum frames for a valid note (default: 3, ~35ms)
    max_pitch_jump : int or None
        Maximum semitone jump allowed. Set to None to disable outlier filtering.
        Use this for monophonic audio. For polyphonic, set to None. (default: None)
    min_velocity_threshold : float
        Minimum velocity to consider a note valid (default: 0.1)
    """
    
    print(f"Input stats:")
    print(f"  Total frames: {len(f0_array)}")
    print(f"  Valid f0 frames: {np.sum((f0_array > 0) & ~np.isnan(f0_array))}")
    print(f"  F0 range: {np.nanmin(f0_array[f0_array > 0]):.1f} - {np.nanmax(f0_array):.1f} Hz")
    print(f"  Velocity range: {np.min(velocity_array):.3f} - {np.max(velocity_array):.3f}")
    
    # Filter by velocity threshold first
    f0_array_filtered = f0_array.copy()
    f0_array_filtered[velocity_array < min_velocity_threshold] = 0
    print(f"  Frames after velocity filter: {np.sum((f0_array_filtered > 0) & ~np.isnan(f0_array_filtered))}")
    
    # Step 1: Filter outliers (octave errors) - optional
    if max_pitch_jump is not None:
        f0_filtered = filter_pitch_outliers(f0_array_filtered, max_pitch_jump)
        print(f"  Frames after pitch outlier filter: {np.sum((f0_filtered > 0) & ~np.isnan(f0_filtered))}")
    else:
        f0_filtered = f0_array_filtered
        print(f"  Pitch outlier filter: DISABLED (polyphonic mode)")
    
    # Step 2: Smooth f0 to reduce jitter
    f0_smooth = smooth_f0(f0_filtered, smooth_kernel)
    
    # Step 3: Convert to MIDI notes
    midi_notes = np.array([f0_to_midi_note(f0) for f0 in f0_smooth])
    valid_notes = np.sum(midi_notes != None)
    print(f"  Valid MIDI note frames: {valid_notes}")
    
    # Step 4: Quantize into sustained notes
    note_events = quantize_notes(midi_notes, min_note_frames)
    
    print(f"\nQuantized to {len(note_events)} notes")
    if len(note_events) > 0:
        print(f"Note duration range: {min(n[2] for n in note_events)} - {max(n[2] for n in note_events)} frames")
    
    # Calculate timing
    frame_duration = hop_length / sr
    ticks_per_beat = 480
    seconds_per_beat = 60.0 / tempo
    ticks_per_second = ticks_per_beat / seconds_per_beat
    ticks_per_frame = frame_duration * ticks_per_second
    
    # Create MIDI file
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Add tempo
    track.append(MetaMessage('set_tempo', tempo=int(60000000 / tempo), time=0))
    
    if len(note_events) == 0:
        print("\nWARNING: No notes generated! Check your f0 and velocity arrays.")
        print("This usually means:")
        print("  - f0 values are all 0, NaN, or negative")
        print("  - velocity values are below threshold")
        print("  - min_note_frames is too high")
        mid.save(output_file)
        return
    
    # Convert note events to MIDI messages
    current_tick = 0
    
    for note, start_frame, duration_frames in note_events:
        # Calculate absolute times
        note_on_tick = int(start_frame * ticks_per_frame)
        note_off_tick = int((start_frame + duration_frames) * ticks_per_frame)
        
        # Get average velocity for this note duration
        vel_start = int(start_frame)
        vel_end = int(min(start_frame + duration_frames, len(velocity_array)))
        avg_velocity = np.mean(velocity_array[vel_start:vel_end])
        midi_velocity = int(np.clip(avg_velocity * 107 + 20, 1, 127))
        
        # Note on
        delta_on = note_on_tick - current_tick
        track.append(Message('note_on', note=note, velocity=midi_velocity, time=delta_on))
        current_tick = note_on_tick
        
        # Note off
        delta_off = note_off_tick - current_tick
        track.append(Message('note_off', note=note, velocity=0, time=delta_off))
        current_tick = note_off_tick
    
    # Save MIDI file
    mid.save(output_file)
    print(f"MIDI file saved to {output_file}")
    print(f"Duration: {len(f0_array) * frame_duration:.2f} seconds")
    print(f"Ticks per frame: {ticks_per_frame:.2f}")
    
    # Print first few events for debugging
    print("\nFirst few MIDI events:")
    for i, msg in enumerate(track[:20]):
        print(msg)

def main():
    filepath = Path("Python_Implementation\single\clouds_trimmed.mp3")
    y, sr = librosa.load(str(filepath), sr=None, mono=True)

    # YIN Algorithm
    y = np.concatenate((np.zeros(frame_length - hop_length), y)) # pads so first point starts in the center
    f0, velocity = yin(y) # fundamental frequency of each frame
    velocity = velocity.astype(int)

    # Write to MIDI file
    # Create MIDI file
    create_midi_from_arrays(f0, velocity, 
                           hop_length=hop_length, sr=sr,
                           output_file='output.mid', tempo=120,
                           smooth_kernel=5, min_note_frames=3,
                           max_pitch_jump=None,  # Disable for polyphonic
                           min_velocity_threshold=0.05)

if __name__=='__main__':
    main()