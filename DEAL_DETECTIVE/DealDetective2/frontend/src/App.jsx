import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Analyze from './pages/Analyze';
import Twins from './pages/Twins';
import Alerts from './pages/Alerts';

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/twins" element={<Twins />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
