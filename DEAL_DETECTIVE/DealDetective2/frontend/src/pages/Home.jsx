import React from 'react';
import { motion } from 'framer-motion';
import { Search, Radar, Bell, ArrowRight, Zap, Target, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import NeonButton from '../components/ui/NeonButton';

const Home = () => {
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.2
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] relative z-10 text-center">

            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="max-w-5xl mx-auto w-full"
            >
                {/* Hero Section */}
                <motion.div variants={itemVariants} className="mb-8">
                    <span className="inline-block py-1 px-3 rounded-full bg-primary-glow/10 border border-primary-glow/30 text-primary-glow text-xs font-mono mb-6 tracking-widest uppercase">
                        AI-Powered OEM Detection System
                    </span>
                    <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tighter leading-tight">
                        <span className="block text-white mb-2">UNMASK THE</span>
                        <span className="bg-gradient-to-r from-primary-glow via-white to-secondary-glow bg-clip-text text-transparent animate-pulse-slow">
                            TRUE PRICE
                        </span>
                    </h1>
                </motion.div>

                <motion.p variants={itemVariants} className="text-xl md:text-2xl text-muted max-w-2xl mx-auto mb-12 leading-relaxed font-light">
                    The ultimate tool for decoding marketing jargon. Find the <span className="text-white font-semibold">exact</span> same OEM product for
                    <span className="text-primary-glow font-bold mx-2">30-50% less</span>
                    using military-grade product analysis.
                </motion.p>

                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center mb-24">
                    <Link to="/analyze">
                        <NeonButton icon={Search} className="w-full sm:w-auto px-8 min-w-[200px]">
                            Start Analysis
                        </NeonButton>
                    </Link>
                    <Link to="/twins">
                        <NeonButton variant="secondary" icon={Radar} className="w-full sm:w-auto px-8 min-w-[200px]">
                            Launch Twin Finder
                        </NeonButton>
                    </Link>
                </motion.div>

                {/* Feature Cards */}
                <motion.div variants={itemVariants} className="grid md:grid-cols-3 gap-8 text-left">
                    <FeatureCard
                        to="/analyze"
                        icon={Zap}
                        title="Instant Analysis"
                        desc="Deep-scan any product URL. We strip away the marketing fluff to reveal raw specs."
                        color="primary"
                    />
                    <FeatureCard
                        to="/twins"
                        icon={Target}
                        title="Twin Detection"
                        desc="Locate the original OEM manufacturer and identical white-labeled alternatives."
                        color="secondary"
                    />
                    <FeatureCard
                        to="/alerts"
                        icon={ShieldCheck}
                        title="Price Sentinel"
                        desc="Set price thresholds. We watch 24/7 and notify you the second a deal drops."
                        color="success"
                    />
                </motion.div>
            </motion.div>
        </div>
    );
};

const FeatureCard = ({ to, icon: Icon, title, desc, color }) => {
    const colorClasses = {
        primary: 'text-primary-glow bg-primary-glow/10',
        secondary: 'text-secondary-glow bg-secondary-glow/10',
        success: 'text-success bg-success/10'
    };

    return (
        <Link to={to} className="block h-full">
            <GlassCard className="h-full p-8 group transition-all duration-300 hover:-translate-y-2" hoverEffect>
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 text-2xl ${colorClasses[color]} mb-6 transition-transform group-hover:scale-110`}>
                    <Icon size={28} />
                </div>
                <h3 className="text-2xl font-bold mb-3 text-white group-hover:text-glow transition-all">{title}</h3>
                <p className="text-muted leading-relaxed mb-8">{desc}</p>

                <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide opacity-60 group-hover:opacity-100 transition-opacity">
                    <span>Activate Protocol</span>
                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </div>
            </GlassCard>
        </Link>
    );
};

export default Home;
