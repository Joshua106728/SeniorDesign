**Ear2Ink**

**Core Functionality**
* Specify the tempo using keypad inputs (communicated through I2C)
* Press the record button to start recording audio input
* Once recording, an LCD display will act as a visual metronome
* Hardware will filter the audio
* Pitch Estimation will be performed using the YIN algorithm
* Post-processing of the pitch estimation is done
* Contents are then written to a MIDI file
* Storage of the MIDI file in an SD card
* Press the stop button to stop recording audio input
* Use an external source to extract MIDI file from SD card and convert it into sheet music (can be saved, downloaded, printed, etc. by user)
  
**Installation**
1. Clone this repository:
```bash
git clone https://github.com/Joshua106728/SeniorDesign.git
```

2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

**Files**
* All high-level Python prototyping is done in Python_Implementation
    * yin.py - includes the YIN algorithm
    * constants.py - constants used in YIN algorithm
    * generate_tests.py - used to generate .wav audio files using sine wave frequency and duration inputs for testing
    * audio_to_midi.py - loads in the audio file, calls yin, does post processing, and writes to a MIDI file
    * view_midi.py - prints out the contents of a MIDI file
