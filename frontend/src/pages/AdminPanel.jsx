import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/AdminPanel.css';

const AdminPanel = () => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // API base URL from environment variable or default
  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8081/api';
  
  useEffect(() => {
    fetchUsers();
  }, []);
  
  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${apiBaseUrl}/auth/admin/users`, { withCredentials: true });
      setUsers(response.data.users);
      setError('');
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to load users. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const promoteToAdmin = async (userId) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${apiBaseUrl}/auth/admin/promote/${userId}`, {}, { withCredentials: true });
      
      if (response.data.success) {
        setSuccessMessage(`User has been promoted to admin successfully!`);
        // Refresh user list
        fetchUsers();
      }
    } catch (error) {
      console.error('Error promoting user:', error);
      setError('Failed to promote user. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="admin-panel container-fluid py-4">
      <div className="row mb-4">
        <div className="col">
          <h1 className="h3">User Management</h1>
          <p className="text-muted">Manage users and their permissions</p>
        </div>
      </div>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
          <button type="button" className="btn-close float-end" onClick={() => setError('')}></button>
        </div>
      )}
      
      {successMessage && (
        <div className="alert alert-success" role="alert">
          {successMessage}
          <button type="button" className="btn-close float-end" onClick={() => setSuccessMessage('')}></button>
        </div>
      )}
      
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Users</h5>
          <button className="btn btn-sm btn-primary" onClick={fetchUsers} disabled={isLoading}>
            {isLoading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Loading...
              </>
            ) : 'Refresh'}
          </button>
        </div>
        <div className="card-body">
          {isLoading ? (
            <div className="text-center py-5">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Loading users...</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Created At</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length > 0 ? (
                    users.map(user => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.name}</td>
                        <td>{user.email}</td>
                        <td>
                          <span className={`badge ${user.role === 'admin' ? 'bg-primary' : 'bg-secondary'}`}>
                            {user.role}
                          </span>
                        </td>
                        <td>{new Date(user.created_at).toLocaleString()}</td>
                        <td>
                          {user.role !== 'admin' && (
                            <button 
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => promoteToAdmin(user.id)}
                              disabled={isLoading}
                            >
                              Promote to Admin
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="text-center">No users found</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel; 