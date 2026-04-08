import React, { useState } from 'react';
import { Bell, ShieldCheck, Mail, AlertTriangle, CheckCircle, Zap } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import GlassCard from '../components/ui/GlassCard';
import InputField from '../components/ui/InputField';
import NeonButton from '../components/ui/NeonButton';

const Alerts = () => {
    const [email, setEmail] = useState('');
    const [targetPrice, setTargetPrice] = useState('');
    const [url, setUrl] = useState('');

    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const [message, setMessage] = useState('');

    const handleSubscribe = async (e) => {
        e.preventDefault();

        if (!url || !targetPrice || !email) {
            setStatus('error');
            setMessage('All fields are required to activate the sentinel.');
            return;
        }

        setStatus('loading');
        setMessage('');

        try {
            const response = await axios.post('http://127.0.0.1:8002/api/set-alert', {
                product_url: url,
                target_price: parseFloat(targetPrice),
                email: email
            });

            setStatus('success');
            setMessage(response.data.message || 'Sentinel successfully deployed. We are watching.');

            // Clear form
            setUrl('');
            setTargetPrice('');
            setEmail('');
        } catch (err) {
            console.error(err);
            setStatus('error');
            setMessage(err.response?.data?.detail || 'Failed to activate sentinel. Please check your inputs.');
        }
    };

    return (
        <div className="max-w-4xl mx-auto w-full">
            <div className="text-center mb-12">
                <h2 className="text-4xl font-black mb-4 flex justify-center items-center gap-3">
                    <ShieldCheck className="text-warning animate-pulse-slow" size={40} />
                    Price <span className="text-warning">Watchtower</span>
                </h2>
                <p className="text-muted text-lg">Deploy automated sentinels to track price fluctuations 24/7.</p>
            </div>

            <GlassCard className="p-10 max-w-2xl mx-auto relative overflow-hidden">
                {/* Status Messages */}
                <AnimatePresence>
                    {status === 'error' && (
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="bg-danger/10 border border-danger/30 text-danger p-4 rounded-xl mb-6 flex items-center gap-3"
                        >
                            <AlertTriangle size={20} />
                            <span className="font-bold">{message}</span>
                        </motion.div>
                    )}
                    {status === 'success' && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 z-20 bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center text-center p-8"
                        >
                            <div className="w-20 h-20 bg-success/20 rounded-full flex items-center justify-center text-success mb-6 animate-bounce">
                                <CheckCircle size={40} />
                            </div>
                            <h3 className="text-3xl font-black text-white mb-2">PROTOCOL ACTIVATED</h3>
                            <p className="text-gray-300 text-lg mb-8 max-w-sm">{message}</p>
                            <NeonButton onClick={() => setStatus('idle')} className="px-8">
                                Deploy Another Sentinel
                            </NeonButton>
                        </motion.div>
                    )}
                </AnimatePresence>

                <form onSubmit={handleSubscribe} className="space-y-8 relative z-10">
                    <div>
                        <label className="block text-xs font-bold uppercase tracking-widest text-muted mb-3 ml-1">Target Product</label>
                        <InputField
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Paste Product URL..."
                            icon={Bell}
                            disabled={status === 'loading'}
                        />
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-xs font-bold uppercase tracking-widest text-muted mb-3 ml-1">Target Price (₹)</label>
                            <InputField
                                value={targetPrice}
                                onChange={(e) => setTargetPrice(e.target.value)}
                                placeholder="e.g. 25000"
                                type="number"
                                icon={ShieldCheck}
                                disabled={status === 'loading'}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold uppercase tracking-widest text-muted mb-3 ml-1">Notification Channel</label>
                            <InputField
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                type="email"
                                icon={Mail}
                                disabled={status === 'loading'}
                            />
                        </div>
                    </div>

                    <div className="pt-4">
                        <NeonButton
                            className={`w-full justify-center text-lg py-4 bg-warning text-black hover:shadow-[0_0_30px_rgba(255,203,0,0.4)] ${status === 'loading' ? 'opacity-75 cursor-wait' : ''}`}
                            icon={status === 'loading' ? Zap : Bell}
                            disabled={status === 'loading'}
                        >
                            {status === 'loading' ? 'Establishing Connection...' : 'Activate Sentinel'}
                        </NeonButton>
                        <p className="text-center text-xs text-muted mt-4">
                            By activating, you agree to receive automated price alerts.
                        </p>
                    </div>
                </form>
            </GlassCard>
        </div>
    );
};

export default Alerts;
