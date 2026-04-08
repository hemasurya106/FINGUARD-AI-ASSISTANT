import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, SpeakOptions
import asyncio

load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def text_to_speech():
    dg = DeepgramClient(API_KEY)

    text = "Hello Hemasurya. This is Deepgram text to speech."

    options = SpeakOptions(
        model="aura-asteria-en",   # natural English voice
        encoding="mp3"
    )

    response = await dg.speak.v("1").save(
        "output.mp3",
        {"text": text},
        options
    )

    print("✅ Audio saved as output.mp3")

asyncio.run(text_to_speech())
