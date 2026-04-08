import pvporcupine
import pvcheetah
from pvrecorder import PvRecorder
import time

# Configuration
ACCESS_KEY = "mNwEnUGv3sxulTOrd9Fwe2TLsjwelJnyg2tBV5TNGji/41B1ErbhQw==" 
KEYWORDS = ['jarvis']
ENDPOINT_DURATION_SEC = 2 # 2 seconds of silence to stop recording

def main():
    porcupine = None
    cheetah = None
    recorder = None

    try:
        # 1. Initialize Engines
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=KEYWORDS
        )
        
        cheetah = pvcheetah.create(
            access_key=ACCESS_KEY,
            endpoint_duration_sec=ENDPOINT_DURATION_SEC
        )

        # 2. Initialize Recorder
        # Ideally, both engines should use the same frame length. 
        # Usually 512. We check just in case.
        if porcupine.frame_length != cheetah.frame_length:
            print(f"Warning: Frame lengths differ! Porcupine: {porcupine.frame_length}, Cheetah: {cheetah.frame_length}")
        
        recorder = PvRecorder(frame_length=porcupine.frame_length)
        recorder.start()

        print("Assistant Started.")
        print(f"Waiting for wake word: {KEYWORDS}...")
        
        is_listening = False
        transcript_buffer = ""

        while True:
            # Read audio frame
            pcm = recorder.read()

            if not is_listening:
                # --- WAKE WORD MODE ---
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    print(f"\nWake word detected! Listening...")
                    is_listening = True
            else:
                # --- SPEECH TO TEXT MODE ---
                partial_transcript, is_endpoint = cheetah.process(pcm)
                
                if partial_transcript:
                    print(partial_transcript, end='', flush=True)
                    transcript_buffer += partial_transcript
                
                if is_endpoint:
                    final_chunk = cheetah.flush()
                    transcript_buffer += final_chunk
                    print(f"\nFinal: {transcript_buffer}")
                    print(f"\nWaiting for wake word: {KEYWORDS}...")
                    is_listening = False
                    transcript_buffer = "" # Reset for next turn

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if recorder: recorder.delete()
        if porcupine: porcupine.delete()
        if cheetah: cheetah.delete()

if __name__ == "__main__":
    main()
