import React from 'react';
import { motion } from 'framer-motion';

const NeonButton = ({
    children,
    variant = 'primary',
    icon: Icon,
    className = '',
    onClick,
    disabled = false,
    ...props
}) => {
    const variants = {
        primary: 'bg-primary-glow text-black shadow-[0_0_20px_rgba(0,240,255,0.4)] hover:shadow-[0_0_35px_rgba(0,240,255,0.6)] hover:bg-white',
        secondary: 'bg-secondary-glow text-white shadow-[0_0_20px_rgba(188,19,254,0.4)] hover:shadow-[0_0_35px_rgba(188,19,254,0.6)] hover:bg-white hover:text-secondary-glow',
        outline: 'bg-transparent border border-primary-glow/50 text-primary-glow hover:bg-primary-glow/10 hover:border-primary-glow hover:shadow-[0_0_20px_rgba(0,240,255,0.3)]'
    };

    return (
        <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`
                relative px-6 py-3 rounded-xl font-bold uppercase tracking-wider text-sm
                flex items-center justify-center gap-2 transition-all duration-300
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
                ${variants[variant] || variants.primary}
                ${className}
            `}
            onClick={onClick}
            disabled={disabled}
            {...props}
        >
            {Icon && <Icon size={18} className="relative z-10" />}
            <span className="relative z-10">{children}</span>

            {/* Internal Glow Effect for Primary/Secondary */}
            {variant !== 'outline' && (
                <div className="absolute inset-0 rounded-xl bg-white/20 blur opacity-0 hover:opacity-100 transition-opacity" />
            )}
        </motion.button>
    );
};

export default NeonButton;
