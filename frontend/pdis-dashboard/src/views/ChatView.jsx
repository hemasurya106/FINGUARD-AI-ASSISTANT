import React, { useState, useEffect, useRef } from 'react';
import GlassCard from '../components/GlassCard';
import { Send, Bot, User, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const ChatView = ({ userId }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Hello! I am your AI Financial Assistant. Ask me to analyze your spending or check your budget.' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://127.0.0.1:8000/chat/analyze', {
                user_id: userId,
                question: userMsg.text
            });

            const aiMsg = {
                role: 'assistant',
                text: response.data.answer || "I couldn't analyze that right now."
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', text: "Error connecting to server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') handleSend();
    };

    return (
        <div style={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <GlassCard className="flex-1 overflow-hidden flex flex-col" delay={0.1}>
                <div
                    ref={scrollRef}
                    style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '10px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '15px',
                        maxHeight: '60vh'
                    }}
                >
                    <AnimatePresence>
                        {messages.map((msg, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={{
                                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '70%',
                                    display: 'flex',
                                    gap: '10px',
                                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
                                }}
                            >
                                <div style={{
                                    width: '32px', height: '32px', borderRadius: '50%',
                                    background: msg.role === 'user' ? 'var(--primary)' : 'var(--accent)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#0f172a'
                                }}>
                                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                                </div>
                                <div style={{
                                    padding: '12px 16px',
                                    borderRadius: '12px',
                                    background: msg.role === 'user' ? 'rgba(74, 144, 226, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                                    border: msg.role === 'user' ? '1px solid var(--primary)' : '1px solid rgba(255,255,255,0.1)',
                                    color: 'white',
                                    lineHeight: '1.5'
                                }}>
                                    {msg.text}
                                </div>
                            </motion.div>
                        ))}
                        {isLoading && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', gap: '10px' }}>
                                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Bot size={18} />
                                </div>
                                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                                    <Loader className="animate-spin" size={18} />
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Input Area */}
                <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                    <input
                        type="text"
                        className="modern-input"
                        placeholder="Ask about your finances..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        style={{
                            flex: 1,
                            padding: '15px',
                            borderRadius: '12px',
                            background: 'rgba(0,0,0,0.3)',
                            border: '1px solid var(--border-color)',
                            color: 'white',
                            outline: 'none'
                        }}
                    />
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSend}
                        style={{
                            padding: '0 20px',
                            borderRadius: '12px',
                            background: 'var(--primary)',
                            border: 'none',
                            color: 'white',
                            cursor: 'pointer'
                        }}
                    >
                        <Send size={20} />
                    </motion.button>
                </div>
            </GlassCard>
        </div>
    );
};

export default ChatView;
