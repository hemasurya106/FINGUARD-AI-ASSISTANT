import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, ArrowRight, Radar } from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Button from '../components/ui/Button';
import '../components/ui/UiStyles.css';
import './Dashboard.css';
import axios from 'axios';

// Placeholder components to be built next
const LoadingView = () => <div className="loading-view">Scanning Neural Networks...</div>;
const ResultsView = ({ data }) => <div className="results-view">Results Loaded for {data?.title}</div>;

const Dashboard = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const handleAnalyze = async (e) => {
        e.preventDefault();
        if (!url) return;

        setLoading(true);
        setError(null);
        setData(null);

        try {
            // Create FormData
            const formData = new FormData();
            formData.append('url', url);

            // Call API
            const response = await axios.post('http://127.0.0.1:8002/analyze-input', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setData(response.data);
        } catch (err) {
            console.error(err);
            setError('Failed to analyze product. Please check the URL and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard-container">
            <Navbar />

            <main className="main-content">
                <AnimatePresence mode="wait">
                    {!data && !loading && (
                        <motion.div
                            key="hero"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="hero-section"
                        >
                            <h1 className="hero-title">
                                Decode <span className="text-gradient">Commerce</span> <br />
                                with AI Intelligence
                            </h1>
                            <p className="hero-subtitle">
                                Paste any product URL. We'll find the best deals, bust the jargon, and check the eco-score.
                            </p>

                            <form onSubmit={handleAnalyze} className="search-bar-container glass-card">
                                <Search className="search-icon" size={20} />
                                <input
                                    type="text"
                                    className="hero-input-transparent"
                                    placeholder="Paste Amazon, Flipkart, or Myntra URL..."
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                />
                                <Button type="submit" variant="primary">
                                    Analyze <ArrowRight size={18} />
                                </Button>
                            </form>

                            {error && <div className="error-message">{error}</div>}

                            <div className="features-grid">
                                <div className="feature-item">
                                    <Sparkles size={20} color="var(--primary-glow)" />
                                    <span>Jargon Buster</span>
                                </div>
                                <div className="feature-item">
                                    <Radar size={20} color="var(--secondary-glow)" />
                                    <span>Price Twins</span>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {loading && (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <LoadingView />
                        </motion.div>
                    )}

                    {data && (
                        <motion.div
                            key="results"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                        >
                            <ResultsView data={data} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
};

export default Dashboard;
