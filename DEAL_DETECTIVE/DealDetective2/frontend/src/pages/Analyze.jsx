import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, ArrowRight, Zap, Leaf, AlertTriangle, CheckCircle, Info, Radar } from 'lucide-react';
import axios from 'axios';
import GlassCard from '../components/ui/GlassCard';
import NeonButton from '../components/ui/NeonButton';
import InputField from '../components/ui/InputField';
import { Link } from 'react-router-dom';

const Analyze = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const handleAnalyze = async (e) => {
        e.preventDefault();
        if (!url) return;
        setLoading(true);
        setError(null);
        setData(null);

        try {
            const formData = new FormData();
            formData.append('url', url);
            const response = await axios.post('http://127.0.0.1:8002/analyze-input', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setData(response.data);
        } catch (err) {
            console.error(err);
            setError('Analysis Protocol Failed. Please verify the URL and retry.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto w-full">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
                <div className="text-center mb-10">
                    <h2 className="text-4xl md:text-5xl font-black mb-4">Product Analysis Protocol</h2>
                    <p className="text-muted text-lg">Input product URL to extract technical specifications and hidden metadata.</p>
                </div>

                <GlassCard className="p-4 max-w-3xl mx-auto">
                    <form onSubmit={handleAnalyze} className="flex flex-col md:flex-row gap-4 items-center">
                        <div className="flex-1 w-full">
                            <InputField
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste Amazon/Retailer URL here..."
                                autoFocus
                            />
                        </div>
                        <NeonButton type="submit" disabled={loading} icon={loading ? Zap : Search} className="w-full md:w-auto h-full px-8">
                            {loading ? 'Scanning...' : 'Analyze'}
                        </NeonButton>
                    </form>
                </GlassCard>

                {error && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 p-4 bg-danger/10 border border-danger/30 text-danger rounded-xl flex items-center justify-center gap-2 max-w-2xl mx-auto">
                        <AlertTriangle size={20} />
                        <span className="font-bold">{error}</span>
                    </motion.div>
                )}
            </motion.div>

            <AnimatePresence mode="wait">
                {data && (
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-8"
                    >
                        {/* Main Product Card */}
                        <GlassCard className="p-8">
                            <div className="flex flex-col md:flex-row gap-8">
                                {data.images && data.images[0] && (
                                    <div className="w-full md:w-1/3 bg-white rounded-xl p-6 flex items-center justify-center min-h-[300px]">
                                        <img src={data.images[0]} alt="Product" className="max-h-64 object-contain mix-blend-multiply" />
                                    </div>
                                )}
                                <div className="flex-1 space-y-6">
                                    <div>
                                        <h3 className="text-3xl font-bold mb-2 leading-tight">{data.title || 'Unknown Product'}</h3>
                                        <div className="flex flex-wrap items-center gap-4 mt-4">
                                            <div className="text-4xl font-black text-primary-glow tracking-tight text-glow">
                                                {data.currency} {data.price}
                                            </div>
                                            {data.original_price && (
                                                <div className="text-xl text-muted line-through decoration-danger/50">
                                                    {data.currency} {data.original_price}
                                                </div>
                                            )}
                                            {data.discount_percentage && (
                                                <span className="px-3 py-1 bg-success/20 text-success border border-success/30 rounded-lg font-bold text-sm tracking-wide uppercase">
                                                    -{data.discount_percentage}% Savings Detected
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                                        <div className="p-4 bg-white/5 rounded-xl">
                                            <div className="text-muted text-xs uppercase tracking-wider mb-1">Brand Tax</div>
                                            <div className="text-xl font-bold text-white">Estimated High</div>
                                        </div>
                                        <div className="p-4 bg-white/5 rounded-xl">
                                            <div className="text-muted text-xs uppercase tracking-wider mb-1">Tech Verify</div>
                                            <div className="text-xl font-bold text-primary-glow">Verified Spec</div>
                                        </div>
                                    </div>

                                    <div className="pt-4 flex gap-4">
                                        <Link to={`/twins?url=${encodeURIComponent(url)}`} className="w-full">
                                            <NeonButton variant="secondary" icon={Radar} className="w-full justify-center text-lg py-4">
                                                Initiate Twin Search
                                            </NeonButton>
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </GlassCard>

                        {/* Analysis Grid */}
                        <div className="grid md:grid-cols-2 gap-8">
                            {/* Jargon Buster */}
                            <GlassCard className="p-8 h-full">
                                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
                                    <div className="p-3 bg-primary-glow/20 rounded-lg text-primary-glow">
                                        <Sparkles size={24} />
                                    </div>
                                    <h4 className="text-2xl font-bold">Marketing Decoder</h4>
                                </div>

                                {data.ai_analysis?.jargon_buster?.length > 0 ? (
                                    <div className="space-y-4">
                                        {data.ai_analysis.jargon_buster.map((item, i) => (
                                            <div key={i} className="group p-4 bg-white/5 rounded-xl border border-white/5 hover:border-primary-glow/30 transition-colors">
                                                <div className="flex items-start gap-3">
                                                    <Info className="flex-shrink-0 text-primary-glow mt-1" size={16} />
                                                    <div>
                                                        <span className="block font-bold text-primary-accent mb-1">{item.term}</span>
                                                        <p className="text-sm text-gray-400 leading-relaxed">{item.simple_explanation}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 text-muted">
                                        <CheckCircle size={48} className="mx-auto mb-4 opacity-20" />
                                        <p>No complex jargon detected in listing.</p>
                                    </div>
                                )}
                            </GlassCard>

                            {/* Eco Analysis */}
                            <GlassCard className="p-8 h-full">
                                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
                                    <div className="p-3 bg-success/20 rounded-lg text-success">
                                        <Leaf size={24} />
                                    </div>
                                    <h4 className="text-2xl font-bold">Sustainability Score</h4>
                                </div>

                                {data.ai_analysis?.eco_analysis ? (
                                    <div className="flex flex-col items-center justify-center text-center py-6">
                                        <div className={`
                                            w-32 h-32 rounded-full border-4 flex items-center justify-center mb-6 shadow-neon
                                            ${data.ai_analysis.eco_analysis.badge === 'Green' ? 'border-success text-success bg-success/10 shadow-[0_0_30px_rgba(0,255,148,0.2)]' :
                                                data.ai_analysis.eco_analysis.badge === 'Yellow' ? 'border-warning text-warning bg-warning/10' :
                                                    'border-danger text-danger bg-danger/10'}
                                        `}>
                                            <span className="text-3xl font-black">{data.ai_analysis.eco_analysis.badge}</span>
                                        </div>

                                        <h5 className="text-xl font-bold mb-4">Environmental Impact Rating</h5>
                                        <p className="text-muted leading-relaxed max-w-sm px-4">
                                            {data.ai_analysis.eco_analysis.reasoning}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="text-center py-12 text-muted">
                                        <p>Insufficient data for environmental impact assessment.</p>
                                    </div>
                                )}
                            </GlassCard>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Analyze;
