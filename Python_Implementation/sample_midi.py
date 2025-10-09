
from mido import MidiFile

mid = MidiFile("Python_Implementation\single\clouds_trimmed.mid")
for i, track in enumerate(mid.tracks):
    print('Track {}: {}'.format(i, track.name))
    for msg in track:
        print(msg)