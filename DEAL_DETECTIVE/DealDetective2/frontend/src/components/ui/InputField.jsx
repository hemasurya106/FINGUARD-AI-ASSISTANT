import React from 'react';
import { Search } from 'lucide-react';

const InputField = ({
    value,
    onChange,
    placeholder = 'Search...',
    icon: Icon = Search,
    className = '',
    ...props
}) => {
    return (
        <div className={`relative group ${className}`}>
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-muted group-focus-within:text-primary-glow transition-colors">
                <Icon size={20} />
            </div>
            <input
                type="text"
                value={value}
                onChange={onChange}
                className="
                    w-full pl-12 pr-4 py-4 rounded-xl
                    bg-white/5 border border-white/10
                    text-white placeholder-white/30
                    focus:outline-none focus:border-primary-glow/50 focus:bg-white/10
                    focus:shadow-[0_0_20px_rgba(0,240,255,0.2)]
                    transition-all duration-300
                    text-lg
                "
                placeholder={placeholder}
                {...props}
            />
            <div className="absolute inset-0 rounded-xl border border-transparent group-focus-within:border-primary-glow/30 pointer-events-none" />
        </div>
    );
};

export default InputField;
