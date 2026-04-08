import React, { useState } from 'react';
import GlassCard from '../components/GlassCard';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, TrendingUp, Wallet, CheckCircle, Camera } from 'lucide-react';
import axios from 'axios';

const DailyView = ({ userId, expenses, setExpenses, userProfile }) => {
    const [newExpense, setNewExpense] = useState({ category: 'Food', amount: '', description: '', paymentMode: 'UPI' });
    const [isScanning, setIsScanning] = useState(false);
    const fileInputRef = React.useRef(null);

    const submitExpenseToBackend = async (expenseData) => {
        const payload = {
            user_id: userId,
            date: new Date().toISOString().split('T')[0],
            category: expenseData.category,
            amount: parseFloat(expenseData.amount),
            payment_mode: expenseData.paymentMode || 'UPI',
            day_type: new Date().getDay() % 6 === 0 ? "Weekend" : "Weekday"
        };

        try {
            const response = await axios.post('http://127.0.0.1:8000/add-expense', payload);
            setExpenses(prev => [...prev, payload]);
            setNewExpense({ category: 'Food', amount: '', description: '', paymentMode: 'UPI' });

            let alertMsg = `✅ Added ₹${payload.amount} for ${payload.category}`;
            if (response.data && response.data.goal_feedback) {
                alertMsg += `\n\n${response.data.goal_feedback}`;
            }
            alert(alertMsg);
        } catch (e) {
            console.error("Error adding expense:", e);
            alert("Failed to add expense.");
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setIsScanning(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://127.0.0.1:8000/scan-bill', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const { amount, category } = response.data;

            // Auto-Add Logic
            if (amount) {
                const scannedExpense = {
                    category: category || 'Food',
                    amount: amount,
                    paymentMode: 'UPI' // Default
                };
                await submitExpenseToBackend(scannedExpense);
            } else {
                alert("Could not extract amount from bill.");
            }

        } catch (error) {
            console.error("Error scanning bill:", error);
            alert("Failed to scan bill. Please try again.");
        } finally {
            setIsScanning(false);
        }
    };

    const addExpense = () => {
        if (!newExpense.amount) return;
        submitExpenseToBackend(newExpense);
    };

    const totalSpent = expenses.reduce((sum, item) => sum + (item.amount || 0), 0);
    const remaining = (userProfile?.target_daily_spend || 2000) - totalSpent;

    return (
        <div className="flex flex-col gap-6">
            {/* Top Stats Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
                <GlassCard delay={0.1}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{ padding: '12px', borderRadius: '12px', background: 'rgba(74, 144, 226, 0.2)', color: 'var(--primary)' }}>
                            <TrendingUp size={24} />
                        </div>
                        <div>
                            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Today's Spend</p>
                            <h2 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 'bold' }}>₹{totalSpent.toFixed(0)}</h2>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard delay={0.2}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{ padding: '12px', borderRadius: '12px', background: 'rgba(80, 227, 194, 0.2)', color: 'var(--accent)' }}>
                            <Wallet size={24} />
                        </div>
                        <div>
                            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Remaining Budget</p>
                            <h2 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 'bold', color: remaining < 0 ? 'var(--alert)' : 'white' }}>
                                ₹{remaining.toFixed(0)}
                            </h2>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard delay={0.3}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{ padding: '12px', borderRadius: '12px', background: 'rgba(255, 90, 95, 0.2)', color: 'var(--alert)' }}>
                            <CheckCircle size={24} />
                        </div>
                        <div>
                            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Balance</p>
                            <h2 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 'bold' }}>₹{userProfile?.current_balance?.toFixed(0) || 0}</h2>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Main Content Split */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
                {/* Recent Transactions List */}
                <GlassCard title="Recent Transactions" delay={0.4}>
                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        <AnimatePresence>
                            {expenses.length === 0 ? (
                                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '20px' }}>No expenses today.</p>
                            ) : (
                                expenses.map((exp, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        transition={{ delay: idx * 0.05 }}
                                        style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            padding: '16px',
                                            marginBottom: '10px',
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '12px',
                                            border: '1px solid rgba(255,255,255,0.05)'
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                                            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                                                {exp.category === 'Food' ? '🍔' : exp.category === 'Travel' ? '🚕' : '🛍️'}
                                            </div>
                                            <div>
                                                <p style={{ margin: 0, fontWeight: '600' }}>{exp.category}</p>
                                                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{exp.payment_mode || 'UPI'}</p>
                                            </div>
                                        </div>
                                        <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>-₹{exp.amount}</span>
                                    </motion.div>
                                ))
                            )}
                        </AnimatePresence>
                    </div>
                </GlassCard>

                {/* Quick Add Form */}
                <GlassCard title="Quick Add" delay={0.5}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        <input
                            type="number"
                            placeholder="Amount (₹)"
                            value={newExpense.amount}
                            onChange={e => setNewExpense({ ...newExpense, amount: e.target.value })}
                            style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px', outline: 'none' }}
                        />
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <select
                                value={newExpense.category}
                                onChange={e => setNewExpense({ ...newExpense, category: e.target.value })}
                                style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px', outline: 'none' }}
                            >
                                {['Food', 'Travel', 'Shopping', 'Entertainment', 'Bills'].map(c => <option key={c} value={c} style={{ background: '#1e293b', color: 'white' }}>{c}</option>)}
                            </select>
                            <select
                                value={newExpense.paymentMode}
                                onChange={e => setNewExpense({ ...newExpense, paymentMode: e.target.value })}
                                style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px', outline: 'none' }}
                            >
                                {['UPI', 'Card', 'Cash'].map(p => <option key={p} value={p} style={{ background: '#1e293b', color: 'white' }}>{p}</option>)}
                            </select>
                        </div>
                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: 'none' }}
                            onChange={handleFileUpload}
                            accept="image/*"
                        />
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <motion.button
                                whileHover={{ scale: 1.02, backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => fileInputRef.current.click()}
                                disabled={isScanning}
                                style={{
                                    flex: 1,
                                    padding: '12px',
                                    background: 'transparent',
                                    color: 'var(--text-primary)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 'bold',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px'
                                }}
                            >
                                <Camera size={18} /> {isScanning ? 'Scanning...' : 'Scan Bill'}
                            </motion.button>
                            <motion.button
                                whileHover={{ scale: 1.02, backgroundColor: '#4A90E2' }}
                                whileTap={{ scale: 0.98 }}
                                onClick={addExpense}
                                style={{
                                    flex: 2,
                                    padding: '12px',
                                    background: 'var(--primary)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 'bold',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px'
                                }}
                            >
                                <Plus size={18} /> Add
                            </motion.button>
                        </div>
                    </div>
                </GlassCard>
            </div>
        </div>
    );
};

export default DailyView;
