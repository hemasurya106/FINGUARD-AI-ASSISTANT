import React, { useState, useEffect } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "./firebase";
import Login from "./Login";
import Sidebar from "./layout/Sidebar";
import DailyView from "./views/DailyView";
import InsightsView from "./views/InsightsView";
import PlannerView from "./views/PlannerView";
import ChatView from "./views/ChatView";
import ProfileSetup from "./views/ProfileSetup";
import VoiceAssistant from "./VoiceAssistant";
import "./App.css";

import axios from 'axios';

function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [expenses, setExpenses] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);

      if (currentUser) {
        try {
          // Fetch today's expenses
          const today = new Date().toISOString().split('T')[0];
          const response = await axios.get(`http://127.0.0.1:8000/get-expenses?user_id=${currentUser.uid}&date=${today}`);
          setExpenses(response.data);

          // Also fetch profile if needed (optional)
          const profileRes = await axios.get(`http://127.0.0.1:8000/get-profile?user_id=${currentUser.uid}`);
          setUserProfile(profileRes.data);
        } catch (error) {
          console.error("Error fetching initial data:", error);
        }
      }

      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-dark)', color: 'var(--accent)' }}>
      INITIALIZING JARVIS...
    </div>
  );

  if (!user) {
    return <Login />;
  }

  // If user is logged in, but profile is not loaded yet
  if (userProfile === null) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-dark)', color: 'var(--accent)' }}>
        LOADING PROFILE...
      </div>
    );
  }

  // If user profile is empty, force onboarding
  if (Object.keys(userProfile).length === 0) {
    return <ProfileSetup userId={user.uid} onComplete={(data) => setUserProfile(data)} />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={() => auth.signOut()}
      />

      <main style={{ flex: 1, padding: '20px 40px', overflowY: 'auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '2rem' }}>Welcome back, <span style={{ color: 'var(--primary)' }}>Admin</span></h1>
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{new Date().toDateString()}</p>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(45deg, var(--primary), var(--accent))' }} />
        </header>

        {activeTab === 'dashboard' && (
          <DailyView
            userId={user.uid}
            expenses={expenses}
            setExpenses={setExpenses}
            userProfile={userProfile}
          />
        )}
        {activeTab === 'insights' && <InsightsView userId={user.uid} />}
        {activeTab === 'planner' && <PlannerView userId={user.uid} />}
        {activeTab === 'chat' && <ChatView userId={user.uid} />}
      </main>

      <VoiceAssistant userId={user.uid} />
    </div>
  );
}

export default App;
