import struct
import json
import math
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pvporcupine
import pvcheetah
from dotenv import load_dotenv, find_dotenv
from voice.agent import VoiceAgent

load_dotenv(find_dotenv())

# Configuration
ACCESS_KEY = "mNwEnUGv3sxulTOrd9Fwe2TLsjwelJnyg2tBV5TNGji/41B1ErbhQw==" 
KEYWORDS = ['jarvis']
ENDPOINT_DURATION_SEC = 2

app = FastAPI(title="Voice Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Extract user_id from query params 
    user_id = websocket.query_params.get("user_id") or "test_user"
    print(f"🔗 WebSocket connected for User ID: {user_id}")
    
    porcupine = None
    cheetah = None
    agent = VoiceAgent() # Initialize Agent
    
    try:
        # Initialize PicoVoice Engines
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=KEYWORDS
        )
        cheetah = pvcheetah.create(
            access_key=ACCESS_KEY,
            endpoint_duration_sec=ENDPOINT_DURATION_SEC
        )
        
        print(f"Client connected. Frame length: {porcupine.frame_length}")
        
        # Buffer setup
        frame_length = porcupine.frame_length
        buffer = bytearray()
        transcript_buffer = ""
        is_listening = False 
        
        print("Starting receive loop...")
        while True:
            # Check for messages
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                print("Client disconnected (event received)")
                break
            
            if "text" in message and message["text"]:
                try:
                    msg_json = json.loads(message["text"])
                    if msg_json.get("type") == "manual_trigger":
                        print("Manual Trigger Received!")
                        is_listening = True
                        transcript_buffer = ""
                        await websocket.send_json({
                            "type": "status", 
                            "payload": "listening"
                        })
                        continue 
                except:
                    pass

            if "bytes" in message and message["bytes"]:
                buffer.extend(message["bytes"])
            
                # Process frames
                while len(buffer) >= (frame_length * 2):
                    frame_bytes = buffer[:frame_length * 2]
                    buffer = buffer[frame_length * 2:]
                    
                    pcm = struct.unpack_from("h" * frame_length, frame_bytes)
                    
                    if not is_listening:
                        # --- WAKE WORD DETECTION ---
                        keyword_index = porcupine.process(pcm)
                        if keyword_index >= 0:
                            print("Wake Word Detected!")
                            is_listening = True
                            transcript_buffer = "" 
                            await websocket.send_json({
                                "type": "status", 
                                "payload": "listening"
                            })
                    else:
                        # --- SPEECH TO TEXT ---
                        try:
                            partial_transcript, is_endpoint = cheetah.process(pcm)
                            if partial_transcript:
                                transcript_buffer += partial_transcript
                                print(f"TRANSCRIPT (Partial): {transcript_buffer}")
                                await websocket.send_json({
                                    "type": "transcript", 
                                    "payload": transcript_buffer,
                                    "is_final": False
                                })
                        except Exception as e:
                            print(f"Cheetah Error: {e}")
                            
                        if is_endpoint:
                            final_transcript = cheetah.flush()
                            transcript_buffer += final_transcript
                            print(f"TRANSCRIPT (Final): {transcript_buffer}")
                            
                            # 1. Send final text
                            await websocket.send_json({
                                "type": "transcript", 
                                "payload": transcript_buffer,
                                "is_final": True
                            })
                            
                            # 2. Process with Agent (Gemini + Deepgram)
                            print(f"Processing command with Agent: {transcript_buffer}")
                            await websocket.send_json({"type": "status", "payload": "thinking"}) # Optional UI state
                            
                            # Pass user_id to agent
                            agent_response = await agent.process(transcript_buffer, user_id=user_id)
                            
                            # 3. Send Agent Response (Audio + Text)
                            print(f"📤 Sending agent response:")
                            print(f"   Text: {agent_response.get('text', 'N/A')[:50]}...")
                            print(f"   Audio URL present: {agent_response.get('audio_url') is not None}")
                            if agent_response.get('audio_url'):
                                audio_preview = agent_response['audio_url'][:80] + "..."
                                print(f"   Audio URL preview: {audio_preview}")
                            
                            await websocket.send_json({
                                "type": "agent_response",
                                "payload": agent_response
                            })
                            
                            print("✅ Agent response sent.")
                            is_listening = False
                            await websocket.send_json({
                                "type": "status", 
                                "payload": "waiting"
                            })

    except WebSocketDisconnect:
        print("Client disconnected cleanly")
    except Exception as e:
        print(f"Unexpected Server Error: {e}")
    finally:
        if porcupine: porcupine.delete()
        if cheetah: cheetah.delete()
