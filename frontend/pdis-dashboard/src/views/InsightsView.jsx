import React, { useEffect, useState } from 'react';
import GlassCard from '../components/GlassCard';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

const InsightsView = ({ userId }) => {
    const [data, setData] = useState([]);
    const [riskyDays, setRiskyDays] = useState([]);
    const [recommendations, setRecommendations] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const overview = await axios.get(`http://127.0.0.1:8000/overview?user_id=${userId}`);
                setData(overview.data);
                const risks = await axios.get(`http://127.0.0.1:8000/risky-days?user_id=${userId}`);
                setRiskyDays(risks.data);
                const recs = await axios.get(`http://127.0.0.1:8000/recommendations?user_id=${userId}`);
                // Taking the last 3 unique recommendations to show relevant recent advice
                setRecommendations(recs.data.slice(-3).reverse());
            } catch (e) { console.error(e); }
        };
        fetchData();
    }, [userId]);

    const chartData = {
        labels: data.map(d => d.date),
        datasets: [
            {
                label: 'Daily Spend (₹)',
                data: data.map(d => d.amount),
                borderColor: '#50E3C2',
                backgroundColor: 'rgba(80, 227, 194, 0.2)',
                tension: 0.4,
                borderWidth: 2,
                pointBackgroundColor: '#fff',
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'top', labels: { color: 'white' } },
            title: { display: false },
        },
        scales: {
            y: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#94a3b8' } },
            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <GlassCard title="Spending Trend" delay={0.1}>
                <div style={{ height: '300px' }}>
                    <Line options={chartOptions} data={chartData} />
                </div>
            </GlassCard>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <GlassCard title="High Risk Anomalies" delay={0.2}>
                    {riskyDays.length === 0 ? (
                        <p style={{ color: 'var(--text-secondary)' }}>No anomalies detected.</p>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {riskyDays.map((risk, idx) => (
                                <li key={idx} style={{ padding: '10px', borderBottom: '1px solid var(--border-color)', color: 'var(--alert)', fontSize: '0.9rem' }}>
                                    ⚠️ {risk.date}: {risk.recommendation}
                                </li>
                            ))}
                        </ul>
                    )}
                </GlassCard>

                <GlassCard title="AI Recommendations" delay={0.3}>
                    {recommendations.length === 0 ? (
                        <p style={{ color: 'var(--text-secondary)' }}>
                            Start adding more daily expenses to unlock personalized insights from our ML Engine.
                        </p>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {recommendations.map((rec, idx) => (
                                <li key={idx} style={{ marginBottom: '10px', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                                        <span>{rec.date}</span>
                                        {rec.cluster === 1 && <span style={{ color: 'var(--alert)' }}>High Spend</span>}
                                    </div>
                                    <p style={{ margin: 0, color: '#e2e8f0' }}>{rec.recommendation}</p>
                                </li>
                            ))}
                        </ul>
                    )}
                </GlassCard>
            </div>
        </div>
    );
};

export default InsightsView;
