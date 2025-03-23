import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';

/**
 * AuthGuard component to protect routes that require authentication
 * Optionally can require admin role
 */
const AuthGuard = ({ children, requireAdmin = false }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [hasRequiredRole, setHasRequiredRole] = useState(false);
  const location = useLocation();
  
  // API base URL from environment variable or default
  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8081/api';
  
  useEffect(() => {
    const checkAuth = async () => {
      // First check local storage
      const userJson = localStorage.getItem('user');
      if (!userJson) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }
      
      let user;
      try {
        user = JSON.parse(userJson);
      } catch (e) {
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }
      
      // Check role if required
      if (requireAdmin) {
        setHasRequiredRole(user.role === 'admin');
      } else {
        setHasRequiredRole(true);
      }
      
      // Verify with server
      try {
        const response = await axios.get(`${apiBaseUrl}/auth/status`, { withCredentials: true });
        setIsAuthenticated(response.data.authenticated);
      } catch (error) {
        console.error('Auth check error:', error);
        setIsAuthenticated(false);
        localStorage.removeItem('user');
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, [apiBaseUrl, requireAdmin]);
  
  if (isLoading) {
    return (
      <div className="auth-loading-container">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Verifying authentication...</p>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    // Not authenticated, redirect to login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  if (requireAdmin && !hasRequiredRole) {
    // Not admin, redirect to dashboard
    return <Navigate to="/dashboard" replace />;
  }
  
  // User is authenticated and has required role
  return children;
};

export default AuthGuard; 