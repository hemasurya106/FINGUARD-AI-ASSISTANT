import React from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, PieChart, Calendar, LogOut, MessageSquare, Target } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab, onLogout }) => {
    const menuItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { id: 'insights', icon: PieChart, label: 'Insights' },
        { id: 'planner', icon: Calendar, label: 'Planner' },
        { id: 'chat', icon: MessageSquare, label: 'Financial Chat' },
    ];

    const handleDealDetective = () => {
        // Placeholder for the external Deal Detective server
        window.open('http://localhost:5173', '_blank');
    };

    return (
        <motion.div
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="glass-panel"
            style={{
                width: '260px',
                height: 'calc(100vh - 40px)',
                margin: '20px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                position: 'sticky',
                top: '20px'
            }}
        >
            <div style={{ marginBottom: '40px', padding: '10px' }}>
                <h1 style={{
                    margin: 0,
                    fontSize: '1.5rem',
                    background: 'linear-gradient(45deg, #4A90E2, #50E3C2)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontWeight: 'bold'
                }}>
                    FIN GUARD
                </h1>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    AI Financial Sentinel
                </p>
            </div>

            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <motion.button
                            key={item.id}
                            whileHover={{ scale: 1.02, backgroundColor: 'rgba(255,255,255,0.1)' }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setActiveTab(item.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                padding: '12px 16px',
                                borderRadius: '12px',
                                border: 'none',
                                background: isActive ? 'rgba(80, 227, 194, 0.15)' : 'transparent',
                                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                                cursor: 'pointer',
                                textAlign: 'left',
                                fontSize: '0.95rem',
                                transition: 'all 0.2s',
                                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent'
                            }}
                        >
                            <Icon size={20} />
                            {item.label}
                        </motion.button>
                    );
                })}
            </nav>

            <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <motion.button
                    whileHover={{ scale: 1.02, backgroundColor: 'rgba(255,255,255,0.1)' }}
                    onClick={handleDealDetective}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '12px 16px',
                        width: '100%',
                        background: 'rgba(74, 144, 226, 0.1)',
                        border: '1px solid var(--primary)',
                        borderRadius: '12px',
                        color: 'var(--primary)',
                        cursor: 'pointer',
                        fontSize: '0.9rem',
                        textAlign: 'left'
                    }}
                >
                    <Target size={18} />
                    Launch Deal Detective ↗
                </motion.button>

                <motion.button
                    whileHover={{ scale: 1.02, color: '#FF5A5F' }}
                    onClick={onLogout}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '12px 16px',
                        width: '100%',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        fontSize: '0.9rem'
                    }}
                >
                    <LogOut size={18} />
                    Sign Out
                </motion.button>
            </div>
        </motion.div>
    );
};

export default Sidebar;
