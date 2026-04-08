import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Radar, ExternalLink, RefreshCw, Search, AlertTriangle, CheckCircle, Package, ArrowRight } from 'lucide-react';
import axios from 'axios';
import GlassCard from '../components/ui/GlassCard';
import NeonButton from '../components/ui/NeonButton';
import InputField from '../components/ui/InputField';
import { motion, AnimatePresence } from 'framer-motion';

const Twins = () => {
    const [searchParams] = useSearchParams();
    const initialUrl = searchParams.get('url') || '';

    const [url, setUrl] = useState(initialUrl);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    // Auto-start if URL coming from Analyze page
    useEffect(() => {
        if (initialUrl) {
            handleSearch(null, initialUrl);
        }
    }, [initialUrl]);

    const handleSearch = async (e, overrideUrl = null) => {
        if (e) e.preventDefault();
        const targetUrl = overrideUrl || url;
        if (!targetUrl) return;

        setLoading(true);
        setError(null);
        setData(null);

        try {
            const formData = new FormData();
            formData.append('url', targetUrl);

            const response = await axios.post('http://127.0.0.1:8002/api/find-twins', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setData(response.data);
        } catch (err) {
            console.error(err);
            setError('Twin detection failed. The target may have anti-bot protections active.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto w-full">
            <div className="text-center mb-10">
                <h2 className="text-4xl md:text-5xl font-black mb-4 flex items-center justify-center gap-4">
                    <Radar className="text-secondary-glow animate-spin-slow" size={48} />
                    Twins <span className="text-secondary-glow">Detector</span>
                </h2>
                <p className="text-muted text-lg">Identify matching OEM components across global marketplaces.</p>
            </div>

            <GlassCard className="p-8 max-w-3xl mx-auto mb-12">
                <form onSubmit={(e) => handleSearch(e)} className="flex flex-col md:flex-row gap-4 items-center">
                    <div className="flex-1 w-full">
                        <InputField
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Enter Product URL to Find Twins..."
                            icon={Search}
                            autoFocus
                        />
                    </div>
                    <NeonButton
                        type="submit"
                        variant="secondary"
                        disabled={loading}
                        icon={loading ? RefreshCw : Radar}
                        className={`w-full md:w-auto h-full px-8 ${loading ? 'opacity-80' : ''}`}
                    >
                        {loading ? 'Scanning...' : 'Find Twins'}
                    </NeonButton>
                </form>
            </GlassCard>

            {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-8 p-4 bg-danger/10 border border-danger/30 text-danger rounded-xl flex items-center justify-center gap-2 max-w-2xl mx-auto">
                    <AlertTriangle size={20} />
                    <span className="font-bold">{error}</span>
                </motion.div>
            )}

            <AnimatePresence>
                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="text-center py-20"
                    >
                        <div className="relative w-32 h-32 mx-auto mb-8">
                            <div className="absolute inset-0 border-4 border-secondary-glow/20 rounded-full animate-ping"></div>
                            <div className="absolute inset-0 border-4 border-t-secondary-glow rounded-full animate-spin"></div>
                            <Radar className="absolute inset-0 m-auto text-secondary-glow" size={40} />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">Scanning Global Databases</h3>
                        <p className="text-muted">Analyzing product fingerprints and searching for matches...</p>
                    </motion.div>
                )}

                {data && (
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-12"
                    >
                        {/* Direct Twins Section */}
                        <div>
                            <div className="flex items-center gap-3 mb-6">
                                <span className="bg-success/10 text-success p-2 rounded-lg">
                                    <CheckCircle size={24} />
                                </span>
                                <h3 className="text-2xl font-bold">Direct Matches Found</h3>
                                <span className="ml-auto bg-white/5 px-3 py-1 rounded-full text-sm font-mono text-muted">
                                    {data.candidates?.length || 0} Candidates
                                </span>
                            </div>

                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {data.candidates?.map((item, idx) => (
                                    <GlassCard key={idx} className="p-6 h-full flex flex-col group overflow-hidden" hoverEffect>
                                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-100 transition-opacity">
                                            <ExternalLink size={20} />
                                        </div>

                                        <div className="mb-4">
                                            <div className="text-xs font-bold uppercase tracking-wider text-muted mb-1">{item.source}</div>
                                            <h4 className="font-bold text-lg leading-tight line-clamp-2 min-h-[3rem] group-hover:text-primary-glow transition-colors">
                                                {item.title}
                                            </h4>
                                        </div>

                                        {item.price_hint && (
                                            <div className="text-2xl font-black text-success mb-4">
                                                {item.price_hint}
                                            </div>
                                        )}

                                        <div className="mt-auto pt-4 border-t border-white/5">
                                            <a
                                                href={item.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="block w-full"
                                            >
                                                <NeonButton variant="outline" className="w-full justify-center text-sm py-2">
                                                    View Deal <ArrowRight size={14} className="ml-1" />
                                                </NeonButton>
                                            </a>
                                        </div>
                                    </GlassCard>
                                ))}

                                {(!data.candidates || data.candidates.length === 0) && (
                                    <div className="col-span-full py-12 text-center text-muted italic border border-dashed border-white/10 rounded-xl">
                                        No exact matches found. Try refining the search.
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Alternatives Section */}
                        {data.alternatives?.length > 0 && (
                            <div>
                                <div className="flex items-center gap-3 mb-6">
                                    <span className="bg-warning/10 text-warning p-2 rounded-lg">
                                        <Package size={24} />
                                    </span>
                                    <h3 className="text-2xl font-bold">Alternatives Detected</h3>
                                </div>

                                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {data.alternatives.map((item, idx) => (
                                        <GlassCard key={idx} className="p-6 h-full flex flex-col border-warning/20">
                                            <div className="mb-4">
                                                <div className="text-xs font-bold uppercase tracking-wider text-warning mb-1">Alternative</div>
                                                <h4 className="font-bold text-lg leading-tight line-clamp-2">{item.title}</h4>
                                            </div>

                                            {item.reason && (
                                                <div className="bg-warning/5 border border-warning/10 p-3 rounded-lg text-sm text-gray-300 mb-4 flex-1">
                                                    <span className="text-warning font-bold mr-1">AI Note:</span>
                                                    {item.reason}
                                                </div>
                                            )}

                                            <div className="mt-4 pt-4 border-t border-white/5">
                                                <a href={item.link} target="_blank" rel="noopener noreferrer" className="block w-full">
                                                    <NeonButton variant="secondary" className="w-full justify-center text-sm py-2">
                                                        Check Price
                                                    </NeonButton>
                                                </a>
                                            </div>
                                        </GlassCard>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Twins;
