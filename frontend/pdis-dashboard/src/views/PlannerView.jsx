import React, { useState } from 'react';
import GlassCard from '../components/GlassCard';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import axios from 'axios';

const PlannerView = ({ userId }) => {
    // Simulation State
    const [simAmount, setSimAmount] = useState('');
    const [simDate, setSimDate] = useState('');
    const [simResult, setSimResult] = useState(null);

    // Goal State
    const [goalCategory, setGoalCategory] = useState('Food');
    const [goalLimit, setGoalLimit] = useState('');

    const handleSimulate = async () => {
        if (!simAmount || !simDate) return;
        try {
            const resp = await axios.post('http://127.0.0.1:8000/simulate', {
                user_id: userId,
                amount: parseFloat(simAmount),
                target_date: simDate
            });
            setSimResult(resp.data);
        } catch (e) {
            console.error(e);
        }
    };

    const handleSetGoal = async () => {
        if (!goalLimit) return;
        try {
            await axios.post('http://127.0.0.1:8000/set-goal', {
                user_id: userId,
                category: goalCategory,
                limit_amount: parseFloat(goalLimit),
                period: "daily"
            });
            alert('Goal Set!');
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <GlassCard title="Purchase Simulator" delay={0.1}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Predict if you can afford a big purchase without breaking your bank.
                    </p>
                    <input
                        type="number"
                        placeholder="Amount (₹)"
                        className="modern-input"
                        value={simAmount}
                        onChange={e => setSimAmount(e.target.value)}
                        style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px' }}
                    />
                    <input
                        type="date"
                        className="modern-input"
                        value={simDate}
                        onChange={e => setSimDate(e.target.value)}
                        style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px' }}
                    />
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSimulate}
                        style={{ padding: '10px', background: 'var(--primary)', border: 'none', borderRadius: '8px', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        Run Simulation
                    </motion.button>

                    <AnimatePresence>
                        {simResult && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                style={{ marginTop: '10px', padding: '15px', background: simResult.safe ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 90, 95, 0.1)', borderRadius: '8px', borderLeft: `4px solid ${simResult.safe ? '#4CAF50' : '#FF5A5F'}` }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                                    {simResult.safe ? <ShieldCheck color="#4CAF50" /> : <AlertTriangle color="#FF5A5F" />}
                                    <strong style={{ color: simResult.safe ? '#4CAF50' : '#FF5A5F' }}>{simResult.safe ? "Safe to Buy" : "Risky"}</strong>
                                </div>
                                <p style={{ margin: 0, fontSize: '0.9rem' }}>{simResult.message}</p>
                                <p style={{ margin: '5px 0 0 0', fontSize: '0.8rem', opacity: 0.7 }}>Future Balance: ₹{simResult.future_balance?.toFixed(2)}</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </GlassCard>

            <GlassCard title="Budget Goals" delay={0.2}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Set daily limits to keep your spending in check.
                    </p>
                    <select
                        value={goalCategory}
                        onChange={e => setGoalCategory(e.target.value)}
                        style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px' }}
                    >
                        {['Food', 'Travel', 'Shopping', 'Entertainment', 'Bills'].map(c => <option key={c} value={c} style={{ color: 'black' }}>{c}</option>)}
                    </select>
                    <input
                        type="number"
                        placeholder="Daily Limit (₹)"
                        value={goalLimit}
                        onChange={e => setGoalLimit(e.target.value)}
                        style={{ padding: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px' }}
                    />
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSetGoal}
                        style={{ padding: '10px', background: 'var(--accent)', border: 'none', borderRadius: '8px', color: '#0f172a', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        Set Goal
                    </motion.button>
                </div>
            </GlassCard>
        </div>
    );
};

export default PlannerView;
