import React, { useState } from 'react';
import { Radar, Clock, Search, Home, Menu, X } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar = () => {
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const isActive = (path) => location.pathname === path;

    const navLinks = [
        { to: "/", icon: Home, label: "Hub" },
        { to: "/analyze", icon: Search, label: "Analyze" },
        { to: "/twins", icon: Radar, label: "Twins" },
        { to: "/alerts", icon: Clock, label: "Price Watch" },
    ];

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 px-4 py-4 md:px-8">
            <div className="max-w-7xl mx-auto backdrop-blur-xl bg-background/50 border border-white/5 rounded-2xl md:rounded-full px-6 py-3 flex justify-between items-center shadow-glass relative">

                {/* Logo */}
                <Link to="/" className="flex items-center gap-3 group relative z-20">
                    <div className="relative">
                        <Radar className="text-primary-glow group-hover:rotate-180 transition-transform duration-700" size={32} />
                        <div className="absolute inset-0 bg-primary-glow blur-lg opacity-40 group-hover:opacity-60 transition-opacity" />
                    </div>
                    <div className="flex flex-col">
                        <span className="font-display font-black text-xl tracking-wider leading-none">
                            DEAL<span className="text-primary-glow">DETECTIVE</span>
                        </span>
                        <span className="text-[0.6rem] text-muted tracking-[0.2em] font-mono">INTELLIGENT SAVINGS PROTOCOL</span>
                    </div>
                </Link>

                {/* Desktop Nav */}
                <div className="hidden md:flex items-center gap-1 bg-black/20 rounded-full p-1 border border-white/5">
                    {navLinks.map((link) => (
                        <Link
                            key={link.to}
                            to={link.to}
                            className={`relative px-5 py-2 rounded-full transition-all duration-300 flex items-center gap-2 group ${isActive(link.to) ? 'text-white' : 'text-muted hover:text-white'
                                }`}
                        >
                            {isActive(link.to) && (
                                <motion.div
                                    layoutId="navbar-indicator"
                                    className="absolute inset-0 bg-primary-glow/10 border border-primary-glow/20 rounded-full shadow-[0_0_15px_rgba(0,240,255,0.2)]"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                />
                            )}
                            <link.icon size={18} className={isActive(link.to) ? 'text-primary-glow' : 'group-hover:text-primary-glow transition-colors'} />
                            <span className="font-medium text-sm pt-0.5">{link.label}</span>
                        </Link>
                    ))}
                </div>

                {/* Mobile Menu Toggle */}
                <button
                    className="md:hidden text-white p-2 relative z-20"
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </button>

                {/* Mobile Nav Overlay */}
                <AnimatePresence>
                    {isMobileMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="absolute top-full left-0 right-0 mt-4 p-4 mx-4 bg-[#0a0a16]/95 backdrop-blur-2xl border border-white/10 rounded-2xl flex flex-col gap-2 md:hidden"
                        >
                            {navLinks.map((link) => (
                                <Link
                                    key={link.to}
                                    to={link.to}
                                    onClick={() => setIsMobileMenuOpen(false)}
                                    className={`flex items-center gap-3 p-4 rounded-xl transition-colors ${isActive(link.to)
                                            ? 'bg-primary-glow/10 text-primary-glow border border-primary-glow/20'
                                            : 'text-muted hover:bg-white/5 hover:text-white'
                                        }`}
                                >
                                    <link.icon size={20} />
                                    <span className="font-bold">{link.label}</span>
                                </Link>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </nav>
    );
};

export default Navbar;
