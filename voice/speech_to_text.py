import pvcheetah
from pvrecorder import PvRecorder

# 1. Configuration
ACCESS_KEY = "mNwEnUGv3sxulTOrd9Fwe2TLsjwelJnyg2tBV5TNGji/41B1ErbhQw==" 
ENDPOINT_DURATION_SEC = 2 # Wait 2 seconds of silence before considering the sentence "done"

try:
    # 2. Create the Cheetah instance (Streaming Speech-to-Text)
    cheetah = pvcheetah.create(access_key=ACCESS_KEY, endpoint_duration_sec=ENDPOINT_DURATION_SEC)

    # 3. Create the Audio Recorder
    recorder = PvRecorder(frame_length=cheetah.frame_length)
    recorder.start()

    print("Listening... (Start speaking now)")
    print("Press Ctrl+C to stop.")

    # 4. Main Loop
    while True:
        # Get audio frame from microphone
        partial_transcript, is_endpoint = cheetah.process(recorder.read())

        # Print partial results (what it thinks you are saying as you speak)
        if partial_transcript:
            print(partial_transcript, end='', flush=True)

        # If it detects a pause (endpoint), flush the rest of the text
        if is_endpoint:
            final_transcript = cheetah.flush()
            print(f"{final_transcript}\n") # New line for the next sentence

except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Error: {e}")

finally:
    # 5. Cleanup
    if 'recorder' in locals():
        recorder.delete()
    if 'cheetah' in locals():
        cheetah.delete()