import React, { useState } from "react";
import { auth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "./firebase";

function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isSignUp, setIsSignUp] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError(null);

        if (isSignUp) {
            createUserWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    console.log("Signed up:", userCredential.user);
                })
                .catch((error) => {
                    console.error("Signup failed:", error);
                    setError(error.message);
                });
        } else {
            signInWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    console.log("Signed in:", userCredential.user);
                })
                .catch((error) => {
                    console.error("Signin failed:", error);
                    setError("Invalid email or password.");
                });
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <div style={styles.logoCircle}>🧠</div>
                <h1 style={styles.title}>{isSignUp ? "Create Account" : "Welcome Back"}</h1>
                <p style={styles.subtitle}>
                    {isSignUp ? "Join PDIS to track your decisions" : "Sign in to your Personal Decision Intelligence System"}
                </p>

                <form onSubmit={handleSubmit} style={styles.form}>
                    <input
                        type="email"
                        placeholder="Email Address"
                        style={styles.input}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        style={styles.input}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />

                    {error && <p style={styles.error}>{error}</p>}

                    <button type="submit" style={styles.button}>
                        {isSignUp ? "Sign Up" : "Sign In"}
                    </button>
                </form>

                <p style={styles.footerText}>
                    {isSignUp ? "Already have an account?" : "Don't have an account?"}
                    <span
                        style={styles.link}
                        onClick={() => setIsSignUp(!isSignUp)}
                    >
                        {isSignUp ? " Sign In" : " Sign Up"}
                    </span>
                </p>
            </div>
        </div>
    );
}

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
        maxWidth: "400px",
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
        boxShadow: "0 0 20px rgba(0,0,0,0.1)"
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
        borderRadius: "50px",
        border: "none",
        background: "rgba(255, 255, 255, 0.2)",
        color: "white",
        fontSize: "1rem",
        outline: "none",
        transition: "background 0.3s ease",
    },
    button: {
        padding: "12px",
        borderRadius: "50px",
        border: "none",
        background: "#FF5A5F",
        color: "white",
        fontSize: "1.1rem",
        fontWeight: "600",
        cursor: "pointer",
        marginTop: "10px",
        transition: "all 0.3s ease",
        boxShadow: "0 4px 15px rgba(255, 90, 95, 0.4)",
    },
    error: {
        color: "#ff6b6b",
        fontSize: "0.9rem",
        margin: "0",
    },
    footerText: {
        marginTop: "20px",
        fontSize: "0.9rem",
        color: "rgba(255, 255, 255, 0.7)",
    },
    link: {
        color: "white",
        fontWeight: "bold",
        cursor: "pointer",
        marginLeft: "5px",
        textDecoration: "underline",
    }
};

export default Login;
