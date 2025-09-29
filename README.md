Description
Creating music is one of the most powerful forms of personal expression, yet this creativity is often stalled by the painstaking process of transcribing these ideas into sheet music. For aspiring producers and musicians, these hours spent can be frustrating and discouraging. A 2022 MIDiA Research study projects that nearly 200 million music creators will exist by 2030 [1]. Even if only 10% rely on acoustic instruments without MIDI functionality, that still represents 20 million individuals dedicating countless hours to transcription rather than doing what they enjoy: creating. Beyond composers, an even larger population of hobbyists could benefit from turning what they hear into accessible sheet music to play accurately. The time spent transcribing needs to be reclaimed and invested into what truly matters: a creative, artistic outflow.

We will develop a microcontroller-based device that automatically transcribes audio input into a MIDI file. This MIDI file will then be converted into sheet music and displayed externally. Our goal for an MVP will operate under these constraints:

Single-note detection (no chords)
Fixed time signature: 4/4
Predefined tempo
From the record button being pressed until the stop button, functionality includes:

Visual metronome on an LCD display with the tempo specified by the user on a keypad
Capture of single-note audio
Accurate determination of each note’s pitch and duration using FFTs
Storage of determined values in MIDI format into an SD card
We will then use an established external source to extract the MIDI file from the SD card and convert it into a sheet music file that can be saved, downloaded, and printed by the user.



[1] C. Koe, “Ai and casual music creation to lead ‘unprecedented expansion’ of music creator economy, per new report,” MusicTech, https://musictech.com/news/industry/music-creator-economy-report-key-drivers/ (accessed Sep. 25, 2025).
