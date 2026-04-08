import pvporcupine
from pvrecorder import PvRecorder

# 1. Configuration
ACCESS_KEY = "mNwEnUGv3sxulTOrd9Fwe2TLsjwelJnyg2tBV5TNGji/41B1ErbhQw==" # Paste your AccessKey from the console here
KEYWORDS = ['jarvis']

try:
    # 2. Create the Porcupine instance
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=KEYWORDS
    )

    # 3. Create the Audio Recorder (Microphone)
    # We set the frame_length to match what Porcupine expects
    recorder = PvRecorder(frame_length=porcupine.frame_length)
    recorder.start()

    print(f"Listening for keywords: {KEYWORDS}...")
    print("Press Ctrl+C to stop.")

    # 4. Main Loop
    while True:
        # Get audio frame from microphone
        pcm = recorder.read()
        
        # Process the audio frame
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            # keyword_index matches the index in the KEYWORDS list
            print(f"Detected {KEYWORDS[keyword_index]}!")

except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Error: {e}")

finally:
    # 5. Cleanup resources
    if 'recorder' in locals():
        recorder.delete()
    if 'porcupine' in locals():
        porcupine.delete()