import React, { useState } from "react";
import axios from "axios";

const ProfileSetup = ({ userId, onComplete }) => {
    const [income, setIncome] = useState("");
    const [fixedCosts, setFixedCosts] = useState("");
    const [targetDailySpend, setTargetDailySpend] = useState("");
    const [currentBalance, setCurrentBalance] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload = {
                user_id: userId,
                income: parseFloat(income) || 0,
                est_fixed_costs: parseFloat(fixedCosts) || 0,
                target_daily_spend: parseFloat(targetDailySpend) || 0,
                current_balance: parseFloat(currentBalance) || 0,
            };

            await axios.post("http://127.0.0.1:8000/update-profile", payload);
            alert("Profile setup complete! Welcome to PDIS.");
            onComplete(payload);
        } catch (err) {
            console.error("Profile Setup Error:", err);
            setError("Failed to save profile. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <div style={styles.logoCircle}>⚙️</div>
                <h1 style={styles.title}>Let's Get Started</h1>
                <p style={styles.subtitle}>Tell us about your finances so we can personalize your experience.</p>

                <form onSubmit={handleSubmit} style={styles.form}>
                    <input
                        type="number"
                        placeholder="Current Balance (₹)"
                        style={styles.input}
                        value={currentBalance}
                        onChange={(e) => setCurrentBalance(e.target.value)}
                        required
                    />
                    <input
                        type="number"
                        placeholder="Monthly Income (₹)"
                        style={styles.input}
                        value={income}
                        onChange={(e) => setIncome(e.target.value)}
                        required
                    />
                    <input
                        type="number"
                        placeholder="Est. Fixed Monthly Costs (Rent, EMI) (₹)"
                        style={styles.input}
                        value={fixedCosts}
                        onChange={(e) => setFixedCosts(e.target.value)}
                        required
                    />
                    <input
                        type="number"
                        placeholder="Target Daily Spend (₹)"
                        style={styles.input}
                        value={targetDailySpend}
                        onChange={(e) => setTargetDailySpend(e.target.value)}
                        required
                    />

                    {error && <p style={styles.error}>{error}</p>}

                    <button type="submit" style={styles.button} disabled={loading}>
                        {loading ? "Saving..." : "Start Using PDIS"}
                    </button>
                </form>
            </div>
        </div>
    );
};

const styles = {
    container: {
        height: "100vh",
        width: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
        fontFamily: "'Segoe UI', sans-serif",
    },
    card: {
        background: "rgba(255, 255, 255, 0.1)",
        backdropFilter: "blur(10px)",
        borderRadius: "20px",
        padding: "50px 40px",
        textAlign: "center",
        boxShadow: "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
        maxWidth: "450px",
        width: "90%",
        border: "1px solid rgba(255, 255, 255, 0.18)",
        color: "white",
    },
    logoCircle: {
        width: "80px",
        height: "80px",
        background: "rgba(255,255,255,0.2)",
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "3rem",
        margin: "0 auto 20px",
        boxShadow: "0 0 20px rgba(0,0,0,0.1)",
    },
    title: {
        fontSize: "2rem",
        margin: "0 0 10px",
        fontWeight: "600",
    },
    subtitle: {
        fontSize: "1rem",
        color: "rgba(255, 255, 255, 0.8)",
        margin: "0 0 30px",
    },
    form: {
        display: "flex",
        flexDirection: "column",
        gap: "15px",
    },
    input: {
        padding: "12px 20px",
        borderRadius: "12px",
        border: "1px solid rgba(255, 255, 255, 0.3)",
        background: "rgba(255, 255, 255, 0.2)",
        color: "white",
        fontSize: "1rem",
        outline: "none",
        transition: "background 0.3s ease",
    },
    button: {
        padding: "12px",
        borderRadius: "12px",
        border: "none",
        background: "#00b894",
        color: "white",
        fontSize: "1.1rem",
        fontWeight: "600",
        cursor: "pointer",
        marginTop: "10px",
        transition: "all 0.3s ease",
        boxShadow: "0 4px 15px rgba(0, 184, 148, 0.4)",
    },
    error: {
        color: "#ff6b6b",
        fontSize: "0.9rem",
        margin: "0",
    },
};

export default ProfileSetup;
