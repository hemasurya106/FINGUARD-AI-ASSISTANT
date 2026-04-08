import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';
import './VoiceAssistant.css';

const VoiceAssistant = ({ userId, onCommand }) => {
    const [isMicActive, setIsMicActive] = useState(false);
    const [isAssistantActive, setIsAssistantActive] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [agentResponse, setAgentResponse] = useState('');

    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const processorRef = useRef(null);
    const sourceRef = useRef(null);
    const audioRef = useRef(null);

    useEffect(() => {
        if (!userId) return;

        // Connect WebSocket
        const ws = new WebSocket(`ws://127.0.0.1:8001/ws/audio?user_id=${userId}`);
        wsRef.current = ws;

        ws.onopen = () => console.log('Connected to Jarvis Node');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'status') {
                if (data.payload === 'listening') {
                    setIsAssistantActive(true);
                    setAgentResponse('');
                    setTranscript("Listening...");
                } else if (data.payload === 'waiting') {
                    setTimeout(() => setIsAssistantActive(false), 3000);
                }
            } else if (data.type === 'transcript') {
                if (data.is_final) {
                    setTranscript(data.payload);
                    if (onCommand) {
                        onCommand(data.payload);
                    }
                }
            } else if (data.type === 'agent_response') {
                const responsePayload = data.payload;
                setAgentResponse(responsePayload.text);
                if (responsePayload.audio_url) {
                    playAudio(responsePayload.audio_url);
                }
            }
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) ws.close();
            stopStreaming();
        };
    }, [userId, onCommand]);

    const [playbackError, setPlaybackError] = useState(null);

    const playAudio = (url) => {
        if (audioRef.current) {
            console.log("Attempting to play audio, length:", url.length);
            audioRef.current.src = url;
            audioRef.current.play().catch(e => {
                console.error("Audio playback failed", e);
                setPlaybackError("Audio playback failed: " + e.message);
            });
        }
    };

    const toggleMic = async () => {
        if (isMicActive) {
            stopStreaming();
            setIsMicActive(false);
            setIsAssistantActive(false);
        } else {
            await startStreaming();
        }
    };

    const startStreaming = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Initialize AudioContext
            const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            sourceRef.current = source;

            // Use ScriptProcessor for raw PCM access (bufferSize: 4096, in:1, out:1)
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);

                // Convert Float32 to Int16
                const buffer = new ArrayBuffer(inputData.length * 2);
                const view = new DataView(buffer);
                for (let i = 0; i < inputData.length; i++) {
                    // Clamp and scale
                    let s = Math.max(-1, Math.min(1, inputData[i]));
                    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true); // true = little-endian
                }

                if (wsRef.current?.readyState === WebSocket.OPEN) {
                    wsRef.current.send(buffer);
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            setIsMicActive(true);
        } catch (err) {
            console.error('Mic Error:', err);
            alert("Could not access microphone.");
        }
    };

    const stopStreaming = () => {
        if (sourceRef.current) sourceRef.current.disconnect();
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current.onaudioprocess = null;
        }
        if (audioContextRef.current) audioContextRef.current.close();

        sourceRef.current = null;
        processorRef.current = null;
        audioContextRef.current = null;
    };

    const SILENT_WAV = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAAABmYWN0BAAAAAAAAABkYXRhAAAAAA==";

    const handleManualTrigger = () => {
        // Unlock Audio (Chrome/Safari Autoplay Policy)
        if (audioRef.current) {
            console.log("Unlocking audio...");
            const originalSrc = audioRef.current.src;
            audioRef.current.src = SILENT_WAV;
            audioRef.current.play().then(() => {
                console.log("Audio unlocked.");
                // We don't need to restore src immediately as the next play will set it
            }).catch(e => console.error("Unlock failed:", e));
        }

        if (!isMicActive) {
            toggleMic().then(() => {
                setIsAssistantActive(true);
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                    wsRef.current.send(JSON.stringify({ type: "manual_trigger" }));
                }
            });
        } else {
            setIsAssistantActive(true);
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: "manual_trigger" }));
            }
        }
    };

    return (
        <>
            <audio ref={audioRef} style={{ display: 'none' }} />

            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleManualTrigger}
                title={isMicActive ? "Jarvis is Listening" : "Activate Jarvis"}
                style={{
                    position: 'fixed',
                    bottom: '30px',
                    right: '30px',
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    background: isMicActive
                        ? (isAssistantActive ? 'linear-gradient(135deg, #00C6FF, #0072FF)' : 'rgba(30, 41, 59, 0.8)')
                        : 'var(--primary)',
                    border: isMicActive ? '2px solid #00C6FF' : 'none',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
                    color: 'white',
                    cursor: 'pointer',
                    zIndex: 100,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backdropFilter: 'blur(5px)'
                }}
            >
                {isMicActive ? <Mic size={28} /> : <MicOff size={28} />}
            </motion.button>

            <AnimatePresence>
                {isAssistantActive && (
                    <motion.div
                        className="siri-container"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <motion.div
                            className="agent-response-text"
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                        >
                            {agentResponse || transcript || "Listening..."}
                        </motion.div>
                        {playbackError && (
                            <div style={{ color: 'red', marginTop: '10px', fontSize: '12px', background: 'rgba(0,0,0,0.5)', padding: '5px' }}>
                                {playbackError}
                            </div>
                        )}
                        <div className="siri-orb" />
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default VoiceAssistant;
