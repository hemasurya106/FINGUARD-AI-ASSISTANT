import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({ children, className = '', hoverEffect = false, ...props }) => {
    return (
        <motion.div
            whileHover={hoverEffect ? { scale: 1.02, y: -5 } : {}}
            className={`
                relative overflow-hidden
                bg-card backdrop-blur-xl border border-white/10 rounded-2xl
                shadow-glass
                ${hoverEffect ? 'hover:shadow-neon-blue hover:border-primary-glow/50 transition-all duration-300' : ''}
                ${className}
            `}
            {...props}
        >
            {/* Subtle Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-dim/10 to-transparent pointer-events-none" />

            {/* Content with z-index to sit above overlay */}
            <div className="relative z-10">
                {children}
            </div>
        </motion.div>
    );
};

export default GlassCard;
