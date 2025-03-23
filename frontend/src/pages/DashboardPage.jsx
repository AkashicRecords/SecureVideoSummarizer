import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/DashboardPage.css';

const DashboardPage = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // API base URL from environment variable or default
  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8081/api';
  
  useEffect(() => {
    // Get user from localStorage
    const userJson = localStorage.getItem('user');
    if (userJson) {
      try {
        setUser(JSON.parse(userJson));
      } catch (e) {
        console.error('Error parsing user data from localStorage', e);
      }
    }
    
    // Verify auth status with server
    const checkAuthStatus = async () => {
      try {
        const response = await axios.get(`${apiBaseUrl}/auth/status`, { withCredentials: true });
        if (!response.data.authenticated) {
          // If server says not authenticated, clear local storage
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        // Handle network errors
        if (error.response?.status === 401) {
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuthStatus();
  }, [apiBaseUrl]);
  
  const handleLogout = async () => {
    try {
      await axios.get(`${apiBaseUrl}/auth/logout`, { withCredentials: true });
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Clear user from localStorage and redirect to login
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  };
  
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p>Loading dashboard...</p>
      </div>
    );
  }
  
  return (
    <div className="dashboard-container">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container-fluid">
          <a className="navbar-brand" href="/dashboard">Secure Video Summarizer</a>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link className="nav-link active" to="/dashboard">Dashboard</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/transcribe">Create Summary</Link>
              </li>
              {user && user.role === 'admin' && (
                <li className="nav-item">
                  <Link className="nav-link" to="/admin">Admin</Link>
                </li>
              )}
            </ul>
            <div className="d-flex align-items-center">
              {user && (
                <span className="text-light me-3">Hello, {user.name}</span>
              )}
              <button className="btn btn-outline-light" onClick={handleLogout}>Logout</button>
            </div>
          </div>
        </div>
      </nav>
      
      <div className="container mt-4">
        <div className="row">
          <div className="col-12">
            <h1 className="mb-4">Dashboard</h1>
            
            <div className="row">
              <div className="col-md-6 col-lg-4 mb-4">
                <div className="card h-100">
                  <div className="card-body">
                    <h5 className="card-title">Create Summary</h5>
                    <p className="card-text">Upload a video file to generate a secure summary.</p>
                    <Link to="/transcribe" className="btn btn-primary">Get Started</Link>
                  </div>
                </div>
              </div>
              
              <div className="col-md-6 col-lg-4 mb-4">
                <div className="card h-100">
                  <div className="card-body">
                    <h5 className="card-title">Recent Summaries</h5>
                    <p className="card-text">View your recently created video summaries.</p>
                    <Link to="/dashboard/history" className="btn btn-outline-primary">View History</Link>
                  </div>
                </div>
              </div>
              
              {user && user.role === 'admin' && (
                <div className="col-md-6 col-lg-4 mb-4">
                  <div className="card h-100">
                    <div className="card-body">
                      <h5 className="card-title">Admin Panel</h5>
                      <p className="card-text">Manage users and system settings.</p>
                      <Link to="/admin" className="btn btn-outline-primary">Go to Admin</Link>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; 