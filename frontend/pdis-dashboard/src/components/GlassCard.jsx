import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({ children, title, className = "", delay = 0 }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: delay }}
            className={`glass-panel p-6 ${className}`}
            style={{
                padding: '24px',
                marginBottom: '20px',
                position: 'relative',
                overflow: 'hidden'
            }}
        >
            {/* Decorative Glow */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '1px',
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)'
            }} />

            {title && (
                <h3 style={{
                    fontSize: '1.25rem',
                    marginBottom: '1rem',
                    fontWeight: '600',
                    color: 'var(--accent)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                }}>
                    {title}
                </h3>
            )}
            {children}
        </motion.div>
    );
};

export default GlassCard;
