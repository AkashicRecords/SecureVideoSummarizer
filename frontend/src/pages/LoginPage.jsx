import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import '../styles/LoginPage.css';

const LoginPage = () => {
  const [activeTab, setActiveTab] = useState('login');
  const [isLoading, setIsLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ 
    name: '', 
    email: '', 
    password: '', 
    confirmPassword: '' 
  });
  const [loginError, setLoginError] = useState('');
  const [registerError, setRegisterError] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get redirect path from location state or default to dashboard
  const from = location.state?.from?.pathname || '/dashboard';
  
  // API base URL from environment variable or default
  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8081/api';
  
  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginForm({ ...loginForm, [name]: value });
  };
  
  const handleRegisterChange = (e) => {
    const { name, value } = e.target;
    setRegisterForm({ ...registerForm, [name]: value });
  };
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${apiBaseUrl}/auth/login`, {
        email: loginForm.email,
        password: loginForm.password
      }, { withCredentials: true });
      
      if (response.data.success) {
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify(response.data.user));
        // Redirect to original destination or dashboard
        navigate(from, { replace: true });
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError(error.response?.data?.error || 'An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate passwords match
    if (registerForm.password !== registerForm.confirmPassword) {
      setRegisterError('Passwords do not match');
      return;
    }
    
    setRegisterError('');
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${apiBaseUrl}/auth/register`, {
        name: registerForm.name,
        email: registerForm.email,
        password: registerForm.password
      }, { withCredentials: true });
      
      if (response.data.success) {
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify(response.data.user));
        // Redirect to dashboard
        navigate('/dashboard', { replace: true });
      }
    } catch (error) {
      console.error('Registration error:', error);
      setRegisterError(error.response?.data?.error || 'An error occurred during registration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleGoogleLogin = () => {
    window.location.href = `${apiBaseUrl}/auth/login/google`;
  };
  
  return (
    <div className="login-page">
      <div className="container">
        <div className="row mb-4">
          <div className="col text-center">
            <h1 className="display-5">Secure Video Summarizer</h1>
            <p className="lead">Please log in to access the dashboard</p>
          </div>
        </div>
        <div className="row">
          <div className="col-md-8 col-lg-6 mx-auto">
            <div className="card">
              <div className="card-header">
                <ul className="nav nav-tabs card-header-tabs">
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'login' ? 'active' : ''}`} 
                      onClick={() => setActiveTab('login')}
                    >
                      Login
                    </button>
                  </li>
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'register' ? 'active' : ''}`} 
                      onClick={() => setActiveTab('register')}
                    >
                      Register
                    </button>
                  </li>
                </ul>
              </div>
              <div className="card-body">
                {activeTab === 'login' ? (
                  <form onSubmit={handleLogin}>
                    <div className="mb-3">
                      <label htmlFor="email" className="form-label">Email address</label>
                      <input 
                        type="email" 
                        className="form-control" 
                        id="email" 
                        name="email"
                        value={loginForm.email}
                        onChange={handleLoginChange}
                        required
                      />
                    </div>
                    <div className="mb-3">
                      <label htmlFor="password" className="form-label">Password</label>
                      <input 
                        type="password" 
                        className="form-control" 
                        id="password" 
                        name="password"
                        value={loginForm.password}
                        onChange={handleLoginChange}
                        required
                      />
                    </div>
                    <div className="d-grid gap-2">
                      <button type="submit" className="btn btn-primary" disabled={isLoading}>
                        {isLoading ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Logging in...
                          </>
                        ) : 'Login'}
                      </button>
                      <button type="button" className="btn btn-outline-dark" onClick={handleGoogleLogin}>
                        <i className="bi bi-google me-2"></i> Sign in with Google
                      </button>
                    </div>
                    {loginError && (
                      <div className="alert alert-danger mt-3">
                        {loginError}
                      </div>
                    )}
                  </form>
                ) : (
                  <form onSubmit={handleRegister}>
                    <div className="mb-3">
                      <label htmlFor="reg-name" className="form-label">Name</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        id="reg-name" 
                        name="name"
                        value={registerForm.name}
                        onChange={handleRegisterChange}
                      />
                    </div>
                    <div className="mb-3">
                      <label htmlFor="reg-email" className="form-label">Email address</label>
                      <input 
                        type="email" 
                        className="form-control" 
                        id="reg-email" 
                        name="email"
                        value={registerForm.email}
                        onChange={handleRegisterChange}
                        required
                      />
                    </div>
                    <div className="mb-3">
                      <label htmlFor="reg-password" className="form-label">Password</label>
                      <input 
                        type="password" 
                        className="form-control" 
                        id="reg-password" 
                        name="password"
                        value={registerForm.password}
                        onChange={handleRegisterChange}
                        required
                      />
                    </div>
                    <div className="mb-3">
                      <label htmlFor="reg-confirm-password" className="form-label">Confirm Password</label>
                      <input 
                        type="password" 
                        className="form-control" 
                        id="reg-confirm-password" 
                        name="confirmPassword"
                        value={registerForm.confirmPassword}
                        onChange={handleRegisterChange}
                        required
                      />
                      {registerForm.confirmPassword && registerForm.password !== registerForm.confirmPassword && (
                        <div className="text-danger mt-1">
                          Passwords do not match
                        </div>
                      )}
                    </div>
                    <div className="d-grid gap-2">
                      <button 
                        type="submit" 
                        className="btn btn-primary" 
                        disabled={isLoading || (registerForm.confirmPassword && registerForm.password !== registerForm.confirmPassword)}
                      >
                        {isLoading ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Registering...
                          </>
                        ) : 'Register'}
                      </button>
                      <button type="button" className="btn btn-outline-dark" onClick={handleGoogleLogin}>
                        <i className="bi bi-google me-2"></i> Sign up with Google
                      </button>
                    </div>
                    {registerError && (
                      <div className="alert alert-danger mt-3">
                        {registerError}
                      </div>
                    )}
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 