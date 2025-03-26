import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Pages
import LoginPage from './pages/LoginPage';
import TranscriptionPage from './pages/TranscriptionPage';
import AdminPanel from './pages/AdminPanel';
import DashboardPage from './pages/DashboardPage';
import Documentation from './pages/Documentation';

// Components
import AuthGuard from './components/AuthGuard';

// CSS
import './styles/App.css';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/docs" element={<Documentation />} />
        
        {/* Protected routes */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route 
          path="/dashboard" 
          element={
            <AuthGuard>
              <DashboardPage />
            </AuthGuard>
          } 
        />
        <Route 
          path="/transcribe" 
          element={
            <AuthGuard>
              <TranscriptionPage />
            </AuthGuard>
          }
        />
        <Route 
          path="/admin" 
          element={
            <AuthGuard requireAdmin={true}>
              <AdminPanel />
            </AuthGuard>
          }
        />
        
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App; 