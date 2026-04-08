/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#030014', // Deep space blue/black
                card: 'rgba(17, 25, 40, 0.75)',
                'card-hover': 'rgba(25, 35, 55, 0.85)',
                primary: {
                    DEFAULT: '#00F0FF', // Cyan Neon
                    glow: '#00F0FF',
                    accent: '#00C2FF',
                    dim: 'rgba(0, 240, 255, 0.1)'
                },
                secondary: {
                    DEFAULT: '#BC13FE', // Purple Neon
                    glow: '#BC13FE',
                    accent: '#8A2BE2',
                    dim: 'rgba(188, 19, 254, 0.1)'
                },
                success: '#00FF94',
                warning: '#FFCB00',
                danger: '#FF0055',
                muted: '#94A3B8',
                border: 'rgba(255, 255, 255, 0.1)',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'], // Tech feel
                display: ['Orbitron', 'sans-serif'], // Futuristic headers
            },
            boxShadow: {
                'neon-blue': '0 0 5px theme("colors.primary.DEFAULT"), 0 0 20px theme("colors.primary.dim")',
                'neon-purple': '0 0 5px theme("colors.secondary.DEFAULT"), 0 0 20px theme("colors.secondary.dim")',
                'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
            },
            backdropBlur: {
                xs: '2px',
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'grid-flow': 'gridFlow 20s linear infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-20px)' },
                },
                gridFlow: {
                    '0%': { backgroundPosition: '0 0' },
                    '100%': { backgroundPosition: '50px 50px' },
                }
            }
        },
    },
    plugins: [],
}
